"""
Common utility functions for the application.
"""
import secrets
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.conf import settings

from decimal import Decimal



def create_rand_string(length=20):
    """Generate a URL-safe random string of the requested length."""
    if length <= 0:
        return ''

    token = secrets.token_urlsafe(length)
    return token[:length]


def get_object_or_none(model_class, *args, **kwargs):
    try:
        return model_class.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None
    except MultipleObjectsReturned:
        return model_class.objects.filter(**kwargs).latest('created_at')
    

def get_percentage(value: Decimal, percentage: Decimal) -> Decimal:
    percentage = Decimal(percentage)
    value = Decimal(value)
    return (value/100)*percentage


def make_str_ready_for_var(value: str) -> str:
    return str(value).lower().replace(" ","_")


def set_response_cookie(response, key, value, **options):
    """
    Set a cookie on the response object following Django and HTTP standards.
    
    This is a wrapper around Django's HttpResponse.set_cookie() method
    with secure defaults and flexibility for customization.
    
    Args:
        response: Django HttpResponse object
        key (str): Cookie name
        value (str): Cookie value
        **options: Optional cookie parameters
            - max_age (int): Max age in seconds. Default: 3600 (1 hour)
            - expires (datetime): Expiration datetime. Default: None
            - path (str): Cookie path. Default: '/'
            - domain (str): Cookie domain. Default: None
            - secure (bool): HTTPS only. Default: not settings.DEBUG (True in production)
            - httponly (bool): Block JavaScript access. Default: True
            - samesite (str): SameSite policy ('Strict', 'Lax', 'None'). Default: 'Lax'
    
    Returns:
        HttpResponse: The response object with cookie set
        
    Example:
        response = Response({'status': 'success'})
        set_response_cookie(response, 'access_token', token_value, max_age=3600)
        return response
    """
    
    # Default cookie settings with security standards
    cookie_settings = {
        'max_age': options.get('max_age', 3600),  # 1 hour default
        'path': options.get('path', '/'),
        'domain': options.get('domain', None),
        'secure': options.get('secure', not settings.DEBUG),  # Only HTTPS in production
        'httponly': options.get('httponly', True),  # Prevent JavaScript access
        'samesite': options.get('samesite', 'Lax'),  # CSRF protection
    }
    
    # Override with user-provided options
    cookie_settings.update({k: v for k, v in options.items() 
                           if k in ['max_age', 'expires', 'path', 'domain', 'secure', 'httponly', 'samesite']})

    response.set_cookie(
        key=key,
        value=value,
        **cookie_settings
    )
    
    return response


def set_response_cookies(response, cookies_dict, **default_options):
    """
    Set multiple cookies on the response object with default options.
    
    Args:
        response: Django HttpResponse object
        cookies_dict (dict): Dictionary of cookie key-value pairs
        **default_options: Default options applied to all cookies
            (can be overridden per cookie)
    
    Returns:
        HttpResponse: The response object with all cookies set
        
    Example:
        response = Response({'status': 'success'})
        cookies = {
            'access_token': access_token_value,
            'refresh_token': refresh_token_value,
        }
        set_response_cookies(response, cookies, max_age=3600)
        return response
    """
    for cookie_key, cookie_value in cookies_dict.items():
        set_response_cookie(response, cookie_key, cookie_value, **default_options)
    
    return response


def delete_response_cookie(response, key, path='/', domain=None):
    """
    Delete a cookie from the response object.
    
    Args:
        response: Django HttpResponse object
        key (str): Cookie name to delete
        path (str): Cookie path. Default: '/'
        domain (str): Cookie domain. Default: None
    
    Returns:
        HttpResponse: The response object with cookie deleted
        
    Example:
        response = Response({'status': 'logged_out'})
        delete_response_cookie(response, 'access_token')
        return response
    """
    response.delete_cookie(
        key=key,
        path=path,
        domain=domain
    )
    
    return response
