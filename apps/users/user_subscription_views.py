"""
User subscription management views.
User-facing endpoints for viewing and purchasing subscriptions.
Uses TransactionHandler from finance app for payment processing.
"""
from typing import Dict, Any
from datetime import datetime, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.users.models import SubscriptionType, UserSubscription, SubscriptionOrder, UserProfile
from apps.users.user_subscription_serializers import (
    AvailableSubscriptionSerializer,
    UserSubscriptionDetailSerializer,
    CreateSubscriptionOrderSerializer,
    VerifyPaymentSerializer,
    SubscriptionOrderResponseSerializer,
    RazorpayCheckoutResponseSerializer,
)
from apps.common.response_serializers import SuccessResponseSerializer
from apps.constants.errors import en as errors
from apps.constants.messages import en as msgs
from apps.common.utils import get_object_or_none
from drf_spectacular.utils import extend_schema
from apps.finance.transaction_handler import TransactionHandler


@extend_schema(
    operation_id='get_my_subscription',
    summary='Get my subscription',
    description='Retrieve current active subscription of authenticated user',
    responses={200: UserSubscriptionDetailSerializer},
    tags=['User Subscriptions'],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_subscription(request: Request) -> Response:
    """Get user's current active subscription."""
    try:
        user_profile = request.user.profile
        subscription = UserSubscription.objects.filter(
            user=user_profile,
            valid_till__gt=datetime.now()
        ).first()
        
        if not subscription:
            raise ValidationError({"error": errors.NO_ACTIVE_SUBSCRIPTION}, code=404)
        
        serializer = UserSubscriptionDetailSerializer(subscription)
        return Response(serializer.data)
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)


@extend_schema(
    operation_id='view_all_subscriptions',
    summary='View all available subscriptions',
    description='Get all available subscription types with current purchase status',
    responses={200: AvailableSubscriptionSerializer(many=True)},
    tags=['User Subscriptions'],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_all_subscriptions(request: Request) -> Response:
    """Get all available subscriptions with purchase status."""
    try:
        subscriptions = SubscriptionType.objects.all()
        serializer = AvailableSubscriptionSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)


@extend_schema(
    operation_id='create_subscription_order',
    summary='Create subscription order',
    description='Create Razorpay order for subscription purchase',
    request=CreateSubscriptionOrderSerializer,
    responses={201: RazorpayCheckoutResponseSerializer},
    tags=['User Subscriptions'],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_subscription_order(request: Request) -> Response:
    """Create subscription order using TransactionHandler."""
    try:
        serializer = CreateSubscriptionOrderSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors, code=400)
        
        subscription_type = SubscriptionType.objects.get(
            id=serializer.validated_data['subscription_type_id']
        )
        user_profile = request.user.profile
        
        # Use TransactionHandler to create order
        handler = TransactionHandler(
            user_id=request.user.id,
            transaction_amount=float(subscription_type.cost)
        )
        
        # Create remote Razorpay order
        remote_order = handler.create_remote_transaction()
        
        # Create local SubscriptionOrder record
        order = SubscriptionOrder.objects.create(
            user=user_profile,
            subscription_type=subscription_type,
            razorpay_order_id=remote_order['id'],
            amount=subscription_type.cost,
            currency=subscription_type.currency,
            payment_status='pending'
        )
        order.save()
        res = handler.make_user_prefill_information()
        
        # response_serializer = SubscriptionOrderResponseSerializer(order)
        return Response(res, status=status.HTTP_201_CREATED)
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)


@extend_schema(
    operation_id='verify_payment_for_subscription',
    summary='Verify subscription payment',
    description='Verify Razorpay payment and activate subscription',
    request=VerifyPaymentSerializer,
    responses={200: SuccessResponseSerializer},
    tags=['User Subscriptions'],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_payment_for_subscription(request: Request) -> Response:
    """Verify Razorpay payment and activate subscription using TransactionHandler."""
    try:
        serializer = VerifyPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors, code=400)
        
        checkout_data = serializer.validated_data
        
        # Get the order from Razorpay order ID
        order = get_object_or_none(
            SubscriptionOrder,
            razorpay_order_id=checkout_data['razorpay_order_id']
        )
        
        if not order:
            raise ValidationError({"error": errors.ORDER_NOT_FOUND}, code=404)
        
        # Verify user ownership
        if order.user != request.user.profile:
            raise ValidationError({"error": errors.UNAUTHORIZED_ORDER_ACCESS}, code=403)
        
        # Use TransactionHandler to verify payment
        handler = TransactionHandler(
            user_id=request.user.id,
            transaction_amount=float(order.amount)
        )
        
        # Verify signature
        if not handler.verify_transaction(checkout_data):
            raise ValidationError({"error": errors.INVALID_PAYMENT_SIGNATURE}, code=400)
        
        # Complete transaction
        payment = handler.complete_transaction()
        
        # Update order status
        order.payment_status = 'completed'
        order.razorpay_payment_id = checkout_data['razorpay_payment_id']
        order.razorpay_signature = checkout_data['razorpay_signature']
        order.save()
        
        # Create user subscription
        valid_till = datetime.now() + timedelta(days=order.subscription_type.duration_in_days)
        subscription = UserSubscription.objects.create(
            user=order.user,
            subscription_type=order.subscription_type,
            valid_till=valid_till
        )
        
        # Send confirmation email with invoice
        _send_invoice_email(order, valid_till)
        
        return Response({
            "status": True,
            "message": "Payment verified and subscription activated"
        })
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)


@extend_schema(
    operation_id='generate_invoice',
    summary='Generate invoice',
    description='Generate and send invoice for subscription purchase',
    responses={200: SuccessResponseSerializer},
    tags=['User Subscriptions'],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def generate_invoice(request: Request) -> Response:
    """Generate and send invoice for subscription."""
    try:
        order_id = request.GET.get('order_id')
        if not order_id:
            raise ValidationError({"error": errors.INVALID_ORDER_ID}, code=400)
        
        order = get_object_or_none(SubscriptionOrder, id=order_id)
        if not order:
            raise ValidationError({"error": errors.ORDER_NOT_FOUND}, code=404)
        
        # Verify order belongs to current user
        if order.user != request.user.profile:
            raise ValidationError({"error": errors.UNAUTHORIZED_ORDER_ACCESS}, code=403)
        
        # Get subscription details
        subscription = UserSubscription.objects.filter(
            user=order.user,
            subscription_type=order.subscription_type
        ).order_by('-created_at').first()
        
        valid_till = subscription.valid_till if subscription else (
            order.created_at + timedelta(days=order.subscription_type.duration_in_days)
        )
        
        # Send invoice email
        _send_invoice_email(order, valid_till)
        
        return Response({
            "status": True,
            "message": "Invoice generated and sent to email"
        })
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)


def _send_invoice_email(order: SubscriptionOrder, valid_till: datetime) -> None:
    """Helper function to send invoice email."""
    from django.template.loader import render_to_string
    from apps.messaging.smtp import send_email
    from decimal import Decimal
    
    # Calculate platform charges (2% of product amount)
    platform_charges = order.amount * Decimal('0.02')
    total_amount = order.amount + platform_charges
    
    # Prepare invoice context
    invoice_context = {
        'invoice_id': str(order.id)[:8].upper(),
        'invoice_date': order.created_at.strftime('%d %b, %Y'),
        'customer_name': order.user.user.get_full_name() or order.user.user.username,
        'customer_email': order.user.user.email,
        'product_name': order.subscription_type.name,
        'product_amount': f"{order.amount:.2f}",
        'duration_days': order.subscription_type.duration_in_days,
        'platform_charges': f"{platform_charges:.2f}",
        'total_amount': f"{total_amount:.2f}",
        'payment_method': 'Razorpay',
        'transaction_id': order.razorpay_payment_id or 'N/A',
        'valid_till': valid_till.strftime('%d %b, %Y'),
    }
    
    # Render HTML template
    html_message = render_to_string(
        'subscription_invoice.html',
        invoice_context
    )
    
    # Send invoice email
    send_email.delay(
        'subscription_invoice',
        f'Invoice for {order.subscription_type.name} Subscription',
        order.user.user.email,
        html_message=html_message,
    )
