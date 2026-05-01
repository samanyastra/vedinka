from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from apps.auth.backend import (get_tokens_for_user,
                               validate_refresh_token,
                               blacklist_token)
from apps.auth.serializers import (RegisterSerializer, 
                                   LoginSerialzier)
from apps.common.utils import set_response_cookie, delete_response_cookie
from apps.constants.errors import en as errors


User = get_user_model()


@api_view(['POST'])
def register_user(request):
    user_data = RegisterSerializer(data=request.data)

    if not user_data.is_valid():
        raise ValidationError(user_data.errors, code=400)
    
    user = user_data.save()
    return Response({"id": user.id})


@api_view(['POST'])
def login(request):
    user = LoginSerialzier(data=request.data)

    if not user.is_valid():
        raise ValidationError(user.errors, code=400)
    user = User.objects.get(email=user.data.get("email"))
    tokens = get_tokens_for_user(user=user)
    access, refresh = tokens['access'], tokens['refresh']

    res = Response({ "user": user.id, "vedinka_access": access})
    set_response_cookie(response=res, key="vedinka_refresh", value=refresh)
    return res


@api_view(['GET'])
def refresh(request):
    refresh_token = request.COOKIES.get('vedinka_refresh')
    if not refresh_token:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)

    try:
        new_tokens = validate_refresh_token(refresh_token)
        
        refresh_obj = RefreshToken(refresh_token)
        user_id = refresh_obj.get('user_id')
        user = User.objects.get(id=user_id)
        
        blacklist_token(refresh_token)
        
        access = new_tokens['access']
        refresh = new_tokens['refresh']
        
        res = Response({"user": user.id, "vedinka_access": access})
        set_response_cookie(response=res, key="vedinka_refresh", value=refresh)
        
        return res
    except ObjectDoesNotExist:
        raise ValidationError(errors.USER_404_ERROR, code=400)
    except AuthenticationFailed:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)
    except Exception as e:
        raise ValidationError(str(e), code=400)


@api_view(['POST'])
def logout(request):
    """Logout user by blacklisting refresh token and deleting cookie."""
    refresh_token = request.COOKIES.get('vedinka_refresh')
    if not refresh_token:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)
    try:
        blacklist_token(refresh_token)
        res = Response({"status": "success", "message": "Logged out successfully"})
        delete_response_cookie(response=res, key="vedinka_refresh")

        return res
    except Exception as e:
        raise ValidationError(str(e), code=400)
