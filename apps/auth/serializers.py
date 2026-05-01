from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password as dj_validate_pwd

from rest_framework import serializers
from apps.common.utils import get_object_or_none
from rest_framework.serializers import (ModelSerializer,
                                        Serializer)

User = get_user_model()

from apps.constants.errors import en as errors


class RegisterSerializer(Serializer):

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=25)
    last_name = serializers.CharField(max_length=25)
    password = serializers.CharField(max_length=25)
    confirm_password = serializers.CharField(max_length=25)

    def validate(self, attrs):
        pwd = attrs.get('password', '').strip()
        conf_pwd = attrs.get('confirm_password', '').strip()
        
        if pwd != conf_pwd:
            raise serializers.ValidationError(errors.PASSWORD_MISMATCH_ERROR, code=400)
        return super().validate(attrs)

    def validate_password(self, value):
        pwd = value.strip()
        if 16 < len(pwd) < 8:
            raise serializers.ValidationError({"error": errors.PASSWORD_LENGTH_ERROR}, code=400)
        try:
            dj_validate_pwd(value)
        except Exception as e:
            print(e)
            raise serializers.ValidationError({"error": errors.PASSWORD_VALIDATION_ERROR}, code=400)
        return value
    
    def validate_email(self, email):
        user = User.objects.filter(email=email)
        if user.exists():
            raise serializers.ValidationError({"error": errors.USER_EXISTS_ERROR}, code=400)
        return email

    def create(self, validated_data) -> User:
        validated_data.pop('confirm_password', None)
        pwd =  validated_data.get('password')
        validated_data['username'] = validated_data.get('email').strip().lower()
        validated_data['email'] = validated_data.get('email').strip().lower()

        new_user = User(**validated_data)
        new_user.set_password(pwd)
        new_user.save()
        return new_user

    def save(self, **kwargs) -> User:
        return self.create(self.validated_data)

class LoginSerialzier(Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=16)

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        pwd = attrs.get('password').strip()
        user = get_object_or_none(User, email=email)
        if user is None:
            raise serializers.ValidationError({"error": errors.USER_404_ERROR}, code=400)
        elif not user.is_active:
            raise serializers.ValidationError({"error": errors.USER_INACTIVE}, code=400)
        pwd_check = user.check_password(pwd)
        if not pwd_check:
            raise serializers.ValidationError({"error": errors.INVALID_DETAILS}, code=400)
        return super().validate(attrs)