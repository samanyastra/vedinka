from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
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
from apps.constants.application import FORGOT_PASSWORD_TEMPLATE_NAME
from apps.messaging.smtp import send_email
from apps.users.models import UserProfile
from vedinka.schema_decorators import document_api_view, document_create_endpoint

User = get_user_model()


@document_create_endpoint(
    operation_id='register_user',
    summary='Register new user',
    description='Create a new user account with email, password, and basic information',
    request_serializer=RegisterSerializer,
    response_serializer=UserIdResponseSerializer,
    tags=['Authentication'],
)
@api_view(["POST"])
def register_user(request: Request) -> Response:
    user_data = RegisterSerializer(data=request.data)

    if not user_data.is_valid():
        raise ValidationError(user_data.errors, code=400)

    user = user_data.save()
    return Response({"id": user.id})


@document_api_view(
    operation_id='login_user',
    summary='User login',
    description='Authenticate user with email and password. Returns access token and sets refresh token in cookie.',
    request_serializer=LoginSerialzier,
    response_serializer=LoginResponseSerializer,
    tags=['Authentication'],
    auth_required=False,
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


@document_api_view(
    operation_id='refresh_token',
    summary='Refresh access token',
    description='Generate new access token using refresh token from cookie',
    response_serializer=RefreshResponseSerializer,
    tags=['Authentication'],
    auth_required=False,
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


@document_api_view(
    operation_id='logout_user',
    summary='User logout',
    description='Logout user by blacklisting refresh token',
    response_serializer=LogoutResponseSerializer,
    tags=['Authentication'],
    auth_required=False,
)
@api_view(["POST"])
def logout(request: Request) -> Response:
    """Logout user by blacklisting refresh token and deleting cookie."""
    refresh_token = request.COOKIES.get("vedinka_refresh")
    if not refresh_token:
        raise ValidationError(errors.REFRESH_TOKEN_NOT_FOUND_ERROR, code=400)
    try:
        blacklist_token(refresh_token)
        res = Response({"status": "success", "message": msgs.LOGOUNT_SUCCESS})
        delete_response_cookie(response=res, key="vedinka_refresh")

        return res
    except Exception as e:
        raise ValidationError(str(e), code=400)


@document_api_view(
    operation_id='activate_user',
    summary='Activate user account',
    description='Activate user account using activation token from email',
    response_serializer=ActivationResponseSerializer,
    tags=['Authentication'],
    auth_required=False,
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
    return Response({"status": True})


@document_api_view(
    operation_id='resend_activation_link',
    summary='Resend activation link',
    description='Resend activation link to user email if not already activated',
    response_serializer=ResendActivationResponseSerializer,
    tags=['Authentication'],
    auth_required=False,
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
        "activation_email",
        msgs.ACTIVATION_MAIL_SUBJECT,
        user.email,
        activation_link=activation_link,
    )
    return Response({"status": True, "message": msgs.ACTIVATION_LINK_SENT})


@document_api_view(
    operation_id='forgot_password',
    summary='Request password reset',
    description='Send password reset link to user email',
    response_serializer=SuccessResponseSerializer,
    tags=['Authentication'],
    auth_required=False,
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

    token = create_activation_token(user, "retrive_creds")
    reset_link = create_activation_link(token, "retrive")
    send_email.delay(
       FORGOT_PASSWORD_TEMPLATE_NAME,
        msgs.FORGOT_PASSWORD_SUBJECT,
        user.email,
        reset_link=reset_link,
    )
    return Response({"status": True})


@document_api_view(
    operation_id='reset_password',
    summary='Reset user password',
    description='Reset password using token from email',
    request_serializer=ResetPasswordSerializer,
    response_serializer=SuccessResponseSerializer,
    tags=['Authentication'],
    auth_required=False,
)
@api_view(["POST"])
def reset_password(request: Request) -> Response:

    serializer = ResetPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        raise ValidationError(serializer.errors, code=400)

    validated_data = serializer.data
    email = validated_data.get("email")
    token = validated_data.get("token")

    User = get_user_model()
    user = User.objects.get(email=email)
    try: 
        token_obj = validate_activation_token(
            token=token, token_type_str="retrive", user=user
        )
    except ActivationTokens.DoesNotExist as e:
        raise ValidationError({"error": errors.INVALID_VERIFICAITON_LINK}, code=400)
    
    user.set_password(validated_data.get('password'))
    user.save()
    return Response({"status": True, "message": msgs.PASSWORD_SAVED})

