"""
Flexible storage configuration for multiple backends (Azure, S3, Local).

This module provides configurable storage backends for Django.
Set the STORAGE_BACKEND environment variable to one of:
- 'local' (default): Local filesystem storage
- 'azure': Azure Blob Storage
- 's3': AWS S3 Storage

Environment variables required for each backend:

Azure:
  - AZURE_ACCOUNT_NAME: Azure storage account name
  - AZURE_ACCOUNT_KEY: Azure storage account key
  - AZURE_CONNECTION_STRING: Full Azure connection string
  - AZURE_CONTAINER_STATIC: Container for static files (default: 'static')
  - AZURE_CONTAINER_MEDIA: Container for media files (default: 'media')

S3:
  - AWS_ACCESS_KEY_ID: AWS access key (from IAM user restricted to this app)
  - AWS_SECRET_ACCESS_KEY: AWS secret key (from IAM user restricted to this app)
  - AWS_STORAGE_BUCKET_NAME: S3 bucket name
  - AWS_S3_REGION_NAME: AWS region (default: 'us-east-1')
  - AWS_S3_CUSTOM_DOMAIN: Custom domain for URLs (optional)
  - AWS_S3_OBJECT_PARAMETERS: JSON string with additional S3 options (optional)
  - APP_ID: Application identifier for S3 access logging (e.g., 'vedinka-app')
  - APP_VERSION: Application version for tracking (e.g., '1.0.0')
  - APP_ENVIRONMENT: Deployment environment (e.g., 'production', 'staging', 'development')

Local:
  - STATIC_ROOT: Local path for static files
  - MEDIA_ROOT: Local path for media files
"""

import os
import json
from pathlib import Path
import environ

# Initialize environ
env = environ.Env()

# Determine active storage backend
STORAGE_BACKEND = env('STORAGE_BACKEND', default='local').lower()


def get_local_storage_config(base_dir):
    """Configure local filesystem storage."""
    return {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        }
    }


def get_azure_storage_config():
    """Configure Azure Blob Storage."""
    azure_account_name = env('AZURE_ACCOUNT_NAME', default='')
    azure_account_key = env('AZURE_ACCOUNT_KEY', default='')
    azure_connection_string = env('AZURE_CONNECTION_STRING', default='')
    azure_container_static = env('AZURE_CONTAINER_STATIC', default='static')
    azure_container_media = env('AZURE_CONTAINER_MEDIA', default='media')

    if not (azure_account_name and (azure_account_key or azure_connection_string)):
        raise ValueError(
            "Azure storage requires AZURE_ACCOUNT_NAME and either "
            "AZURE_ACCOUNT_KEY or AZURE_CONNECTION_STRING"
        )

    return {
        'default': {
            'BACKEND': 'storages.backends.azure_storage.AzureStorage',
            'OPTIONS': {
                'azure_container': azure_container_media,
                'account_name': azure_account_name,
                'account_key': azure_account_key,
                'connection_string': azure_connection_string,
            },
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.azure_storage.AzureStorage',
            'OPTIONS': {
                'azure_container': azure_container_static,
                'account_name': azure_account_name,
                'account_key': azure_account_key,
                'connection_string': azure_connection_string,
            },
        },
    }


def get_s3_storage_config():
    """Configure AWS S3 Storage with app-specific identification.
    
    This configuration restricts S3 access to a specific IAM user/role and
    tags all operations with the application ID for audit and access control.
    
    Security Setup:
    1. Create IAM user 'vedinka-app' with S3-only permissions
    2. Restrict bucket policy to allow access only from this IAM user
    3. Set APP_ID to identify this app in CloudTrail logs
    4. Rotate credentials every 90 days
    
    Reference: .env.example for all required variables
    """
    access_key = env('AWS_ACCESS_KEY_ID', default='')
    secret_key = env('AWS_SECRET_ACCESS_KEY', default='')
    bucket_name = env('AWS_STORAGE_BUCKET_NAME', default='')
    region_name = env('AWS_S3_REGION_NAME', default='us-east-1')
    custom_domain = env('AWS_S3_CUSTOM_DOMAIN', default='')
    object_params_str = env('AWS_S3_OBJECT_PARAMETERS', default='{}')
    
    # App identification for access control and audit logging
    app_id = env('APP_ID', default='vedinka-app')
    app_version = env('APP_VERSION', default='1.0.0')
    app_environment = env('APP_ENVIRONMENT', default='development')

    if not (access_key and secret_key and bucket_name):
        raise ValueError(
            "S3 storage requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, "
            "and AWS_STORAGE_BUCKET_NAME. "
            "Use IAM user credentials restricted to this app only."
        )

    # Parse additional S3 object parameters from JSON string
    try:
        object_params = json.loads(object_params_str)
    except json.JSONDecodeError:
        object_params = {}

    s3_options = {
        'access_key': access_key,
        'secret_key': secret_key,
        'bucket_name': bucket_name,
        'region_name': region_name,
    }
    
    # Add app identification headers for CloudTrail logging and access control
    # This helps identify which app is making S3 requests in audit logs
    s3_options['config'] = {
        'user_agent_extra': f'{app_id}/{app_version} ({app_environment})'
    }
    
    # Add app metadata to all uploaded objects for tracking
    if 'Metadata' not in object_params:
        object_params['Metadata'] = {
            'app-id': app_id,
            'app-version': app_version,
            'app-environment': app_environment,
            'uploaded-by': 'vedinka-storage',
        }

    if custom_domain:
        s3_options['custom_domain'] = custom_domain

    s3_options.update(object_params)

    return {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': s3_options,
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.s3boto3.S3StaticStorage',
            'OPTIONS': s3_options,
        },
    }


def get_storage_config(base_dir):
    """
    Get the appropriate storage configuration based on STORAGE_BACKEND.

    Args:
        base_dir: Django BASE_DIR (Path object)

    Returns:
        Dictionary with 'default' and 'staticfiles' storage backends
    """
    if STORAGE_BACKEND == 'azure':
        return get_azure_storage_config()
    elif STORAGE_BACKEND == 's3':
        return get_s3_storage_config()
    else:  # default to 'local'
        return get_local_storage_config(base_dir)


def get_static_and_media_urls(base_dir):
    """
    Get static and media URLs based on the storage backend.

    Args:
        base_dir: Django BASE_DIR (Path object)

    Returns:
        Tuple of (STATIC_URL, MEDIA_URL) or None for local
    """
    if STORAGE_BACKEND == 'azure':
        azure_account_name = env('AZURE_ACCOUNT_NAME', default='')
        azure_container_static = env('AZURE_CONTAINER_STATIC', default='static')
        azure_container_media = env('AZURE_CONTAINER_MEDIA', default='media')

        static_url = f"https://{azure_account_name}.blob.core.windows.net/{azure_container_static}/"
        media_url = f"https://{azure_account_name}.blob.core.windows.net/{azure_container_media}/"

        return static_url, media_url

    elif STORAGE_BACKEND == 's3':
        custom_domain = env('AWS_S3_CUSTOM_DOMAIN', default='')
        bucket_name = env('AWS_STORAGE_BUCKET_NAME', default='')
        region_name = env('AWS_S3_REGION_NAME', default='us-east-1')

        if custom_domain:
            static_url = f"https://{custom_domain}/static/"
            media_url = f"https://{custom_domain}/media/"
        else:
            static_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/static/"
            media_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/media/"

        return static_url, media_url

    else:  # local
        return '/static/', '/media/'


def get_static_and_media_roots(base_dir):
    """
    Get static and media root paths for local storage.

    Args:
        base_dir: Django BASE_DIR (Path object)

    Returns:
        Tuple of (STATIC_ROOT, MEDIA_ROOT) for local storage, or None for cloud
    """
    if STORAGE_BACKEND == 'local':
        static_root = env('STATIC_ROOT', default=str(base_dir / 'staticfiles'))
        media_root = env('MEDIA_ROOT', default=str(base_dir / 'media'))
        return static_root, media_root
    return None, None
