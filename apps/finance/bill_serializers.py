from rest_framework import serializers
from apps.finance.models import Charge, BillLine, BillLedger


class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = [
            'id',
            'name',
            'description',
            'amount_type',
            'amount',
            'is_active',
            'apply_to_order',
            'apply_to_subscription',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class BillLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLine
        fields = [
            'id',
            'name',
            'amount_type',
            'base_amount',
            'calculated_amount',
        ]
        read_only_fields = ['id']


class BillLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLedger
        fields = [
            'id',
            'user',
            'transaction_type',
            'reference_id',
            'subtotal',
            'breakdown_json',
            'total_charges',
            'final_amount',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'breakdown_json',
            'total_charges',
            'final_amount',
            'created_at',
        ]


class BillBreakdownResponseSerializer(serializers.Serializer):
    """Response serializer for bill breakdown calculations"""
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    charges = serializers.ListField(child=serializers.DictField())
    total_charges = serializers.DecimalField(max_digits=12, decimal_places=2)
    final_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(default='INR')
