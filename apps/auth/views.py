from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from datetime import date
from typing import Dict, Any

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from apps.auth.serializers import (
    RegisterSerializer,
    LoginSerialzier,
    ResetPasswordSerializer,
)
from apps.auth.models import ActivationTokens, TokenTypes
from apps.auth.utils import create_activation_link, validate_activation_token
from apps.common.serializers import EmailSerializer
from apps.common.response_serializers import (
    UserIdResponseSerializer,
    LoginResponseSerializer,
    RefreshResponseSerializer,
    LogoutResponseSerializer,
    ActivationResponseSerializer,
    ResendActivationResponseSerializer,
    SuccessResponseSerializer,
)
from apps.common.utils import (
    set_response_cookie,
    delete_response_cookie,
    get_object_or_none,
)
from apps.auth.backend import (
    create_activation_token,
    get_tokens_for_user,
    validate_refresh_token,
    blacklist_token,
)
from apps.constants.errors import en as errors
from apps.constants.messages import en as msgs
from apps.constants.application import (FORGOT_PASSWORD_TEMPLATE_NAME,
                                        ACTIVATION_EMAIL_TEMPLATE_NAME,
                                        RETRIVE_PASSWORD_DB_CODE)
from apps.messaging.smtp import send_email
from apps.users.models import UserProfile
from apps.content.models import Book
from apps.auth.permissions import IsSuperUserOrAdmin
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

User = get_user_model()


@extend_schema(
    operation_id='register_user',
    summary='Register new user',
    description='Create a new user account with email, password, and basic information',
    request=RegisterSerializer,
    responses={200: UserIdResponseSerializer},
    tags=['Authentication'],
)
@api_view(["POST"])
def register_user(request: Request) -> Response:
    user_data = RegisterSerializer(data=request.data)

    if not user_data.is_valid():
        raise ValidationError(user_data.errors, code=400)

    user = user_data.save()
    return Response({"id": user.id})


@extend_schema(
    operation_id='login_user',
    summary='User login',
    description='Authenticate user with email and password. Returns access token and sets refresh token in cookie.',
    request=LoginSerialzier,
    responses={200: LoginResponseSerializer},
    tags=['Authentication'],
)
@api_view(["POST"])
def login(request: Request) -> Response:
    user = LoginSerialzier(data=request.data)

    if not user.is_valid():
        raise ValidationError(user.errors, code=400)
    user = User.objects.get(email=user.data.get("email"))
    tokens = get_tokens_for_user(user=user)
    access, refresh = tokens["access"], tokens["refresh"]
    role = user.profile.role.name if user.profile and user.profile.role else None

    res = Response({"user": user.id, "role": role, "vedinka_access": access})
    set_response_cookie(response=res, key="vedinka_refresh", value=refresh)
    return res


@extend_schema(
    operation_id='refresh_token',
    summary='Refresh access token',
    description='Generate new access token using refresh token from cookie',
    responses={200: RefreshResponseSerializer},
    tags=['Authentication'],
)
@api_view(["GET"])
def refresh(request: Request) -> Response:
    refresh_token = request.COOKIES.get("vedinka_refresh")
    if not refresh_token:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)

    try:
        new_tokens = validate_refresh_token(refresh_token)

        refresh_obj = RefreshToken(refresh_token)
        user_id = refresh_obj.get("user_id")
        user = User.objects.get(id=user_id)

        blacklist_token(refresh_token)

        access = new_tokens["access"]
        refresh = new_tokens["refresh"]
        role = user.profile.role.name if user.profile and user.profile.role else None

        res = Response({"user": user.id, "role": role, "vedinka_access": access})
        set_response_cookie(response=res, key="vedinka_refresh", value=refresh)

        return res
    except ObjectDoesNotExist:
        raise ValidationError(errors.USER_404_ERROR, code=400)
    except AuthenticationFailed:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)
    except Exception as e:
        raise ValidationError(str(e), code=400)


@extend_schema(
    operation_id='logout_user',
    summary='User logout',
    description='Logout user by blacklisting refresh token',
    request=None,
    responses={200: LogoutResponseSerializer},
    tags=['Authentication'],
)
@api_view(["POST"])
def logout(request: Request) -> Response:
    """Logout user by blacklisting refresh token and deleting cookie."""
    refresh_token = request.COOKIES.get("vedinka_refresh")
    if not refresh_token:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)
    try:
        blacklist_token(refresh_token)
        res = Response({"status": "success", "message": msgs.LOGOUT_SUCCESS})
        delete_response_cookie(response=res, key="vedinka_refresh")

        return res
    except Exception as e:
        raise ValidationError(str(e), code=400)


@extend_schema(
    operation_id='activate_user',
    summary='Activate user account',
    description='Activate user account using activation token from email',
    parameters=[
        OpenApiParameter(
            name='hint',
            description='Activation token from email',
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: ActivationResponseSerializer},
    tags=['Authentication'],
)
@api_view(["GET"])
def activate_user(request: Request) -> Response:
    token = request.GET.get("hint", "").strip()

    if not token:
        raise ValidationError({"error": errors.INVALID_VERIFICAITON_LINK}, code=400)

    token_type, _ = TokenTypes.objects.get_or_create(
        type_code="activate_user", token_type="activate"
    )
    token_obj = get_object_or_none(ActivationTokens, token=token, token_type=token_type)
    if token_obj is None:
        raise ValidationError({"error": errors.INVALID_VERIFICAITON_LINK}, code=400)

    user = token_obj.user
    if user.is_active:
        raise ValidationError({"error": errors.USER_ALREADY_ACTIVATED}, code=400)

    user.is_active = True
    profile = UserProfile.objects.get(user=user)
    profile.is_email_verified = True
    profile.save()
    user.save()
    
    # Mark token as expired after successful activation
    token_obj.is_expired = True
    token_obj.is_activated = True
    token_obj.save()
    
    return Response({"status": True})


@extend_schema(
    operation_id='resend_activation_link',
    summary='Resend activation link',
    description='Resend activation link to user email if not already activated',
    parameters=[
        OpenApiParameter(
            name='email',
            description='User email address',
            required=True,
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: ResendActivationResponseSerializer},
    tags=['Authentication'],
)
@api_view(["GET"])
def resend_activation_link(request: Request) -> Response:
    email = request.GET.get("email")
    s = EmailSerializer(data={"email": email})
    if not s.is_valid():
        raise ValidationError({"error": errors.INVALID_EMAIL})
    
    user = get_object_or_none(User, email=email)
    if user is None:
        raise ValidationError({"error": errors.USER_404_ERROR})
    
    if user.is_active:
        raise ValidationError({"error": errors.USER_ALREADY_ACTIVATED}, code=400)
    
    token_type, _ = TokenTypes.objects.get_or_create(
        type_code="activate_user", token_type="activate"
    )
    
    token_obj = get_object_or_none(ActivationTokens, user=user, token_type=token_type)
    if token_obj:
        token_obj.delete()
    
    token = create_activation_token(user, "activate_user")
    activation_link = create_activation_link(token, "hint")
    send_email.delay(
        ACTIVATION_EMAIL_TEMPLATE_NAME,
        msgs.ACTIVATION_MAIL_SUBJECT,
        user.email,
        activation_link=activation_link,
    )
    return Response({"status": True, "message": msgs.ACTIVATION_LINK_SENT})


@extend_schema(
    operation_id='forgot_password',
    summary='Request password reset',
    description='Send password reset link to user email',
    parameters=[
        OpenApiParameter(
            name='email',
            description='User email address',
            required=True,
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.QUERY,
        )
    ],
    responses={200: SuccessResponseSerializer},
    tags=['Authentication'],
)
@api_view(["GET"])
def forgot_password(request: Request) -> Response:
    email = request.GET.get("email")
    s = EmailSerializer(data={"email": email})
    if not s.is_valid():
        raise ValidationError({"error": errors.INVALID_EMAIL})

    User = get_user_model()
    user = get_object_or_none(User, email=email)

    if user is None:
        raise ValidationError({"error": errors.USER_404_ERROR})

    if not user.is_active:
        raise ValidationError({"error": errors.USER_INACTIVE})

    token = create_activation_token(user, RETRIVE_PASSWORD_DB_CODE)
    reset_link = create_activation_link(token, "retrive", path="reset-password")
    send_email.delay(
       FORGOT_PASSWORD_TEMPLATE_NAME,
        msgs.FORGOT_PASSWORD_SUBJECT,
        user.email,
        reset_link=reset_link,
    )
    return Response({"status": True, 'message': msgs.PASSWORD_RESET_MAIL_SENT_SUCCESS})


@extend_schema(
    operation_id='reset_password',
    summary='Reset user password',
    description='Reset password using token from email',
    request=ResetPasswordSerializer,
    responses={200: SuccessResponseSerializer},
    tags=['Authentication'],
)
@api_view(["POST"])
def reset_password(request: Request) -> Response:

    serializer = ResetPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)

    validated_data = serializer.data
    email = validated_data.get("email", '')
    token = validated_data.get("token", '')

    User = get_user_model()
    user = User.objects.get(email=email)
    token_obj = validate_activation_token(
        token=token, token_type_str="retrive", user=user
    )
    
    user.set_password(validated_data.get('password'))
    user.save()
    
    # Mark token as expired after successful password reset
    token_obj.is_expired = True
    token_obj.save()
    
    return Response({"status": True, "message": msgs.PASSWORD_SAVED})


@extend_schema(
    operation_id='admin_stats_overview',
    summary='Admin statistics overview',
    description='Get overall platform statistics - total users, users joined today, total books, books uploaded today. Admin only.',
    responses={200: {
        'type': 'object',
        'properties': {
            'total_users': {'type': 'integer'},
            'users_joined_today': {'type': 'integer'},
            'total_books': {'type': 'integer'},
            'books_uploaded_today': {'type': 'integer'},
        }
    }},
    tags=['Admin - Statistics'],
)
@api_view(["GET"])
@permission_classes([IsSuperUserOrAdmin])
def admin_stats_overview(request: Request) -> Response:
    """Get admin statistics overview."""
    try:
        today = date.today()
        
        # Total users count
        total_users = User.objects.filter(is_active=True).count()
        
        # Users joined today
        users_joined_today = User.objects.filter(
            is_active=True,
            date_joined__date=today
        ).count()
        
        # Total books count
        total_books = Book.objects.count()
        
        # Books uploaded today
        books_uploaded_today = Book.objects.filter(
            created_at__date=today
        ).count()
        
        return Response({
            'total_users': total_users,
            'users_joined_today': users_joined_today,
            'total_books': total_books,
            'books_uploaded_today': books_uploaded_today,
        })
    except Exception as e:
        raise ValidationError({"error": str(e)}, code=400)

