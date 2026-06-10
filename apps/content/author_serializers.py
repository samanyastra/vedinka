from rest_framework import serializers
from apps.content.serializers import TagSerializer, GenreSerializer, LanguageSerializer
from apps.users.models import BankDetail


class BankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetail
        fields = ['id', 'account_holder_name', 'account_number', 'ifsc_code', 'bank_name', 'branch_name', 'account_type', 'is_verified']
        read_only_fields = ['id', 'is_verified']
