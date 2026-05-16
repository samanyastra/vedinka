from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from apps.auth.models import ActivationTokens, TokenTypes
from apps.common.utils import get_object_or_none
from apps.constants.errors import en as errors


def validate_activation_token(token: str, token_type_str: str, user):
    """Validate activation token and check if it's expired.
    
    Args:
        token: The activation token string
        token_type_str: Type of token (e.g., 'activate', 'retrive')
        user: User object
        
    Returns:
        ActivationTokens object if valid
        
    Raises:
        TokenTypes.DoesNotExist: If token type not found
        ActivationTokens.DoesNotExist: If token not found or is expired
        ValidationError: If token is expired
    """
    token_type_obj = get_object_or_none(TokenTypes, token_type=token_type_str)

    if token_type_obj is None:
        raise TokenTypes.DoesNotExist
    
    # Filter by is_expired=False to exclude expired tokens
    token_obj = get_object_or_none(ActivationTokens, user=user, token=token, is_expired=False)
    if token_obj is None:
        raise ActivationTokens.DoesNotExist
    
    return token_obj


def create_activation_link(token: str, key: str, path: str="activate") -> str:
    """Create activation link with token.
    
    Args:
        token: The activation token
        key: Query parameter key name
        
    Returns:
        Full activation link URL
    """
    domain_address = settings.DOMAIN_ADDRESS.rstrip("/")
    return f"{domain_address}/auth/{path}?{key}={token}"
