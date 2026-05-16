"""
Decorators for API documentation using drf-spectacular.
Provides clean, reusable decorators for documenting endpoints.
"""
from typing import Type, List, Optional
from functools import wraps
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import serializers, status
from apps.common.response_serializers import (
    SuccessResponseSerializer,
    ErrorResponseSerializer,
    ValidationErrorResponseSerializer,
)


def document_api_view(
    operation_id: str,
    summary: str,
    description: str,
    request_serializer: Optional[Type[serializers.Serializer]] = None,
    response_serializer: Optional[Type[serializers.Serializer]] = None,
    status_code: int = status.HTTP_200_OK,
    tags: Optional[List[str]] = None,
    auth_required: bool = True,
):
    """
    Decorator to document API views with Swagger/OpenAPI schema.
    
    Args:
        operation_id: Unique operation identifier
        summary: Short description of the endpoint
        description: Detailed description of the endpoint
        request_serializer: Serializer for request body
        response_serializer: Serializer for response body
        status_code: HTTP status code for success response
        tags: List of tags for grouping in Swagger UI
        auth_required: Whether authentication is required
        
    Returns:
        Decorated function with Swagger documentation
    """
    def decorator(func):
        # Use provided response serializer or default to SuccessResponseSerializer
        response_ser = response_serializer or SuccessResponseSerializer
        
        # Build responses dict
        responses = {
            status_code: OpenApiResponse(
                response=response_ser,
                description='Success response'
            )
        }
        
        # Add error responses
        responses[status.HTTP_400_BAD_REQUEST] = OpenApiResponse(
            response=ValidationErrorResponseSerializer,
            description='Bad request - validation error'
        )
        
        if auth_required:
            responses[status.HTTP_401_UNAUTHORIZED] = OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Unauthorized - authentication required'
            )
            responses[status.HTTP_403_FORBIDDEN] = OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Forbidden - insufficient permissions'
            )
        
        responses[status.HTTP_500_INTERNAL_SERVER_ERROR] = OpenApiResponse(
            response=ErrorResponseSerializer,
            description='Internal server error'
        )
        
        # Apply extend_schema decorator
        schema_decorator = extend_schema(
            operation_id=operation_id,
            summary=summary,
            description=description,
            request=request_serializer,
            responses=responses,
            tags=tags or ['Default'],
            auth=None if not auth_required else ['Bearer'],
        )
        
        return schema_decorator(func)
    
    return decorator


def document_list_endpoint(
    operation_id: str,
    summary: str,
    description: str,
    response_serializer: Type[serializers.Serializer],
    tags: Optional[List[str]] = None,
):
    """
    Decorator for documenting list/retrieve endpoints.
    
    Args:
        operation_id: Unique operation identifier
        summary: Short description
        description: Detailed description
        response_serializer: Serializer for response
        tags: List of tags for grouping
        
    Returns:
        Decorated function with Swagger documentation
    """
    return extend_schema(
        operation_id=operation_id,
        summary=summary,
        description=description,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=response_serializer,
                description='Success response'
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Unauthorized'
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Forbidden'
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Not found'
            ),
        },
        tags=tags or ['Default'],
        auth=['Bearer'],
    )


def document_create_endpoint(
    operation_id: str,
    summary: str,
    description: str,
    request_serializer: Type[serializers.Serializer],
    response_serializer: Type[serializers.Serializer],
    tags: Optional[List[str]] = None,
):
    """
    Decorator for documenting create endpoints.
    
    Args:
        operation_id: Unique operation identifier
        summary: Short description
        description: Detailed description
        request_serializer: Serializer for request
        response_serializer: Serializer for response
        tags: List of tags for grouping
        
    Returns:
        Decorated function with Swagger documentation
    """
    return extend_schema(
        operation_id=operation_id,
        summary=summary,
        description=description,
        request=request_serializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=response_serializer,
                description='Resource created successfully'
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description='Validation error'
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Unauthorized'
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Forbidden'
            ),
        },
        tags=tags or ['Default'],
        auth=None,
    )


def document_update_endpoint(
    operation_id: str,
    summary: str,
    description: str,
    request_serializer: Type[serializers.Serializer],
    response_serializer: Type[serializers.Serializer],
    tags: Optional[List[str]] = None,
    partial: bool = False,
):
    """
    Decorator for documenting update/patch endpoints.
    
    Args:
        operation_id: Unique operation identifier
        summary: Short description
        description: Detailed description
        request_serializer: Serializer for request
        response_serializer: Serializer for response
        tags: List of tags for grouping
        partial: Whether partial updates are allowed
        
    Returns:
        Decorated function with Swagger documentation
    """
    return extend_schema(
        operation_id=operation_id,
        summary=summary,
        description=description,
        request=request_serializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=response_serializer,
                description='Resource updated successfully'
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description='Validation error'
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Unauthorized'
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Forbidden'
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Not found'
            ),
        },
        tags=tags or ['Default'],
        auth=['Bearer'],
    )


def document_delete_endpoint(
    operation_id: str,
    summary: str,
    description: str,
    tags: Optional[List[str]] = None,
):
    """
    Decorator for documenting delete endpoints.
    
    Args:
        operation_id: Unique operation identifier
        summary: Short description
        description: Detailed description
        tags: List of tags for grouping
        
    Returns:
        Decorated function with Swagger documentation
    """
    return extend_schema(
        operation_id=operation_id,
        summary=summary,
        description=description,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description='Resource deleted successfully'
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Unauthorized'
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Forbidden'
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Not found'
            ),
        },
        tags=tags or ['Default'],
        auth=['Bearer'],
    )
