from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
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
from apps.messaging.smtp import send_email

User = get_user_model()


@api_view(["POST"])
def register_user(request):
    user_data = RegisterSerializer(data=request.data)

    if not user_data.is_valid():
        raise ValidationError(user_data.errors, code=400)

    user = user_data.save()
    return Response({"id": user.id})


@api_view(["POST"])
def login(request):
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


@api_view(["GET"])
def refresh(request):
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


@api_view(["POST"])
def logout(request):
    """Logout user by blacklisting refresh token and deleting cookie."""
    refresh_token = request.COOKIES.get("vedinka_refresh")
    if not refresh_token:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)
    try:
        blacklist_token(refresh_token)
        res = Response({"status": "success", "message": "Logged out successfully"})
        delete_response_cookie(response=res, key="vedinka_refresh")

        return res
    except Exception as e:
        raise ValidationError(str(e), code=400)


@api_view(["GET"])
def resend_activation_link(request):
    pass


@api_view(["GET"])
def activate_user(request):
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
    return Response({"status": True})


@api_view(["GET"])
def forgot_password(request):
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

    token = create_activation_token(user, "retrive_creds")
    reset_link = create_activation_link(token, "retrive")
    send_email.delay(
        "forgot_password",
        msgs.FORGOT_PASSWORD_SUBJECT,
        user.email,
        reset_link=reset_link,
    )
    return Response({"status": True})


@api_view(["GET"])
def reset_password(request):

    serializer = ResetPasswordSerializer(data=request.GET)

    if not serializer.is_valid():
        raise ValidationError({"error": errors.INVALID_DETAILS}, code=400)

    validated_data = serializer.data
    email = validated_data.get("email")
    token = validated_data.get("token")

    User = get_user_model()
    user = User.objects.get(email=email)
    token_obj = validate_activation_token(
        token=token, token_type_str="retrive", user=user
    )
    

