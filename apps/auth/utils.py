from django.conf import settings
from django.contrib.auth import get_user_model


from apps.auth.models import ActivationTokens, TokenTypes
from apps.common.utils import get_object_or_none


def validate_activation_token(token, token_type_str, user):

    token_type_obj = get_object_or_none(TokenTypes, token_type=token_type_str)

    if token_type_obj is None:
        raise TokenTypes.DoesNotExist
    token_obj = get_object_or_none(ActivationTokens, user=user, token=token)
    if token_obj is None:
        raise ActivationTokens.DoesNotExist
    return token_obj


def create_activation_link(token, key):
    domain_address = settings.DOMAIN_ADDRESS.rstrip("/")
    return f"{domain_address}/auth/activate?{key}={token}"
