from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from apps.finance.models import Charge, BillLedger
from apps.finance.bill_serializers import ChargeSerializer, BillLedgerSerializer
from apps.auth.permissions import IsSuperUserOrAdmin


@extend_schema(
    tags=['Admin - Charges'],
    summary='List all charges',
    description='Retrieve list of all charges with their configurations',
    responses={200: ChargeSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsSuperUserOrAdmin])
def list_charges(request):
    """Get all charges"""
    charges = Charge.objects.all()
    serializer = ChargeSerializer(charges, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=['Admin - Charges'],
    summary='Create new charge',
    description='Create a new charge configuration (platform fee, GST, shipping, etc)',
    request=ChargeSerializer,
    responses={201: ChargeSerializer},
)
@api_view(['POST'])
@permission_classes([IsSuperUserOrAdmin])
def create_charge(request):
    """Create a new charge"""
    serializer = ChargeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin - Charges'],
    summary='Update charge',
    description='Update an existing charge configuration',
    request=ChargeSerializer,
    responses={200: ChargeSerializer},
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsSuperUserOrAdmin])
def update_charge(request, charge_id):
    """Update a charge"""
    try:
        charge = Charge.objects.get(id=charge_id)
    except Charge.DoesNotExist:
        return Response(
            {'error': 'Charge not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ChargeSerializer(charge, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Admin - Charges'],
    summary='Delete charge',
    description='Delete a charge configuration',
    responses={204: None},
)
@api_view(['DELETE'])
@permission_classes([IsSuperUserOrAdmin])
def delete_charge(request, charge_id):
    """Delete a charge"""
    try:
        charge = Charge.objects.get(id=charge_id)
        charge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Charge.DoesNotExist:
        return Response(
            {'error': 'Charge not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['Admin - Bill Ledger'],
    summary='List bill ledger entries',
    description='View all bill breakdown ledger entries with audit trail',
    responses={200: BillLedgerSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsSuperUserOrAdmin])
def list_bill_ledger(request):
    """Get all bill ledger entries"""
    ledger_entries = BillLedger.objects.all().select_related('user')
    
    # Optional filters
    transaction_type = request.query_params.get('transaction_type')
    user_id = request.query_params.get('user_id')
    
    if transaction_type:
        ledger_entries = ledger_entries.filter(transaction_type=transaction_type)
    if user_id:
        ledger_entries = ledger_entries.filter(user_id=user_id)
    
    serializer = BillLedgerSerializer(ledger_entries, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=['Admin - Bill Ledger'],
    summary='Get bill ledger entry',
    description='View a specific bill breakdown ledger entry',
    responses={200: BillLedgerSerializer},
)
@api_view(['GET'])
@permission_classes([IsSuperUserOrAdmin])
def get_bill_ledger_entry(request, ledger_id):
    """Get a specific bill ledger entry"""
    try:
        entry = BillLedger.objects.get(id=ledger_id)
        serializer = BillLedgerSerializer(entry)
        return Response(serializer.data)
    except BillLedger.DoesNotExist:
        return Response(
            {'error': 'Bill ledger entry not found'},
            status=status.HTTP_404_NOT_FOUND
        )
