from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

from apps.constants.errors import en as errors


User = get_user_model()

def get_tokens_for_user(user):
    """
    Generate access and refresh tokens for a user.
    
    Args:
        user: The user object
        
    Returns:
        dict: Contains 'refresh' and 'access' tokens
        
    Raises:
        AuthenticationFailed: If user is not active
    """
    if not user.is_active:
        raise AuthenticationFailed({"error": errors.USER_INACTIVE})

    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def validate_refresh_token(refresh_token_str):
    """
    Validate a refresh token and generate new token pair if valid.
    
    Args:
        refresh_token_str (str): The refresh token string to validate
        
    Returns:
        dict: Contains 'refresh' and 'access' tokens
        
    Raises:
        AuthenticationFailed: If token is invalid, expired, or blacklisted
    """
    if not refresh_token_str:
        raise AuthenticationFailed({"error": errors.EMPTY_REFRESH_TOKEN_ERROR})
    try:
        refresh = RefreshToken(refresh_token_str)
        user_id = refresh.get('user_id')
        
        if not user_id:
            raise AuthenticationFailed({"error": errors.USER_404_ERROR})
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed({"error": errors.USER_404_ERROR})

        return get_tokens_for_user(user)
        
    except Exception as e:
        if isinstance(e, AuthenticationFailed):
            raise
        raise AuthenticationFailed({"error": errors.INVALID_REFRESH_TOKEN})


def blacklist_token(refresh_token):
    """
    Blacklist a refresh token using simplejwt's built-in blacklist.
    The token blacklist is managed by rest_framework_simplejwt.token_blacklist app.
    
    Args:
        refresh_token (str or RefreshToken): The refresh token to blacklist
        
    Returns:
        dict: Contains the blacklisted token info
        
    Raises:
        AuthenticationFailed: If token is invalid
    """
    try:
        # Convert string to RefreshToken object if needed
        if isinstance(refresh_token, str):
            token = RefreshToken(refresh_token)
        else:
            token = refresh_token
        
        # Blacklist the token (simplejwt handles this)
        token.blacklist()
        
        return {
            'status': 'success',
            'message': 'Token blacklisted successfully'
        }
    except Exception as e:
        raise AuthenticationFailed(f"Failed to blacklist token: {str(e)}")

