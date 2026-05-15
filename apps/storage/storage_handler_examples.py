"""
StorageHandler Usage Examples and Integration Guide

The StorageHandler provides a unified interface for file operations
across all backends (Local, Azure, S3).
"""

from django.http import FileResponse, JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from apps.storage.storage_handler import StorageHandler, StorageOperationError, FileNotFoundError


# ============================================================================
# BASIC USAGE
# ============================================================================

def basic_example():
    """Basic file operations example."""
    
    # Initialize handler (defaults to 'default' storage for media files)
    handler = StorageHandler()
    
    # Upload a file
    with open('/path/to/document.pdf', 'rb') as f:
        file_info = handler.upload_file('documents/document.pdf', f)
        print(f"Uploaded: {file_info.name} ({file_info.size} bytes)")
        print(f"URL: {file_info.url}")
    
    # Get file info
    file_info = handler.get_file('documents/document.pdf')
    print(f"File: {file_info.to_dict()}")
    
    # Check if file exists
    exists = handler.file_exists('documents/document.pdf')
    print(f"Exists: {exists}")
    
    # Download file
    content = handler.download_file('documents/document.pdf')
    print(f"Downloaded {len(content)} bytes")
    
    # Delete file
    deleted = handler.delete_file('documents/document.pdf')
    print(f"Deleted: {deleted}")


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def file_operations_example():
    """File operations: copy, move, search."""
    
    handler = StorageHandler()
    
    # Copy file
    file_info = handler.copy_file('documents/file1.pdf', 'backups/file1.pdf')
    print(f"Copied to: {file_info.url}")
    
    # Move file
    file_info = handler.move_file('documents/file1.pdf', 'archive/file1.pdf')
    print(f"Moved to: {file_info.url}")
    
    # List all files in a folder
    files = handler.list_files('documents/')
    for file_info in files:
        print(f"{file_info.name}: {file_info.size} bytes, {file_info.url}")
    
    # Search for files
    pdf_files = handler.search_files('*.pdf')
    print(f"Found {len(pdf_files)} PDF files")


# ============================================================================
# REST API VIEWS
# ============================================================================

class FileUploadView(View):
    """Handle file uploads (works with any backend)."""
    
    def post(self, request):
        try:
            file_obj = request.FILES.get('file')
            if not file_obj:
                return JsonResponse({'error': 'No file provided'}, status=400)
            
            # Use storage handler
            handler = StorageHandler()
            
            # Generate file path
            file_path = f"uploads/{file_obj.name}"
            
            # Upload
            file_info = handler.upload_file(file_path, file_obj)
            
            return JsonResponse({
                'status': 'success',
                'file': file_info.to_dict(),
            })
        
        except StorageOperationError as e:
            return JsonResponse({'error': str(e)}, status=400)


class FileDownloadView(View):
    """Download/get file (works with any backend)."""
    
    def get(self, request, file_path):
        try:
            handler = StorageHandler()
            
            # Option 1: Return file URL (redirect to cloud storage)
            file_info = handler.get_file(file_path)
            return JsonResponse({'url': file_info.url})
            
            # Option 2: Stream file content (for local/private files)
            # content = handler.download_file(file_path)
            # return FileResponse(BytesIO(content), as_attachment=True)
        
        except FileNotFoundError:
            return JsonResponse({'error': 'File not found'}, status=404)
        except StorageOperationError as e:
            return JsonResponse({'error': str(e)}, status=400)


class FileDeleteView(View):
    """Delete file (works with any backend)."""
    
    def delete(self, request, file_path):
        try:
            handler = StorageHandler()
            deleted = handler.delete_file(file_path)
            
            if deleted:
                return JsonResponse({'status': 'success', 'deleted': True})
            else:
                return JsonResponse({'error': 'File not found'}, status=404)
        
        except StorageOperationError as e:
            return JsonResponse({'error': str(e)}, status=400)


class FileListView(View):
    """List files in a folder (works with any backend)."""
    
    def get(self, request):
        try:
            folder = request.GET.get('folder', '')
            
            handler = StorageHandler()
            files = handler.list_files(folder)
            
            return JsonResponse({
                'folder': folder,
                'count': len(files),
                'files': [f.to_dict() for f in files],
            })
        
        except StorageOperationError as e:
            return JsonResponse({'error': str(e)}, status=400)


class FileMoveView(View):
    """Move/rename file (works with any backend)."""
    
    def post(self, request):
        try:
            source = request.POST.get('source')
            dest = request.POST.get('destination')
            
            if not source or not dest:
                return JsonResponse({'error': 'source and destination required'}, status=400)
            
            handler = StorageHandler()
            file_info = handler.move_file(source, dest)
            
            return JsonResponse({'status': 'success', 'file': file_info.to_dict()})
        
        except StorageOperationError as e:
            return JsonResponse({'error': str(e)}, status=400)


# ============================================================================
# DRF API VIEWS (REST Framework)
# ============================================================================

@api_view(['POST'])
def upload_file_api(request):
    """Upload file via REST API."""
    try:
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        handler = StorageHandler()
        file_path = f"uploads/{file_obj.name}"
        file_info = handler.upload_file(file_path, file_obj)
        
        return Response({
            'status': 'success',
            'file': file_info.to_dict(),
        }, status=status.HTTP_201_CREATED)
    
    except StorageOperationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_file_api(request, file_path):
    """Get file info via REST API."""
    try:
        handler = StorageHandler()
        file_info = handler.get_file(file_path)
        return Response(file_info.to_dict())
    
    except FileNotFoundError:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    except StorageOperationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_files_api(request):
    """List files in folder via REST API."""
    try:
        folder = request.query_params.get('folder', '')
        handler = StorageHandler()
        files = handler.list_files(folder)
        
        return Response({
            'folder': folder,
            'count': len(files),
            'files': [f.to_dict() for f in files],
        })
    
    except StorageOperationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_file_api(request, file_path):
    """Delete file via REST API."""
    try:
        handler = StorageHandler()
        deleted = handler.delete_file(file_path)
        
        if deleted:
            return Response({'status': 'success', 'deleted': True})
        else:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except StorageOperationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def copy_file_api(request):
    """Copy file via REST API."""
    try:
        source = request.data.get('source')
        dest = request.data.get('destination')
        
        if not source or not dest:
            return Response(
                {'error': 'source and destination required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        handler = StorageHandler()
        file_info = handler.copy_file(source, dest)
        
        return Response({'status': 'success', 'file': file_info.to_dict()})
    
    except StorageOperationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def move_file_api(request):
    """Move file via REST API."""
    try:
        source = request.data.get('source')
        dest = request.data.get('destination')
        
        if not source or not dest:
            return Response(
                {'error': 'source and destination required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        handler = StorageHandler()
        file_info = handler.move_file(source, dest)
        
        return Response({'status': 'success', 'file': file_info.to_dict()})
    
    except StorageOperationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def search_files_api(request):
    """Search for files via REST API."""
    try:
        pattern = request.query_params.get('pattern', '*')
        handler = StorageHandler()
        files = handler.search_files(pattern)
        
        return Response({
            'pattern': pattern,
            'count': len(files),
            'files': [f.to_dict() for f in files],
        })
    
    except StorageOperationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# URL CONFIGURATION EXAMPLE
# ============================================================================

"""
Add to apps/storage/urls.py:

from django.urls import path
from . import views_examples

urlpatterns = [
    # REST API endpoints
    path('api/upload/', views_examples.upload_file_api, name='upload-file'),
    path('api/files/<path:file_path>/', views_examples.get_file_api, name='get-file'),
    path('api/files/<path:file_path>/delete/', views_examples.delete_file_api, name='delete-file'),
    path('api/files/list/', views_examples.list_files_api, name='list-files'),
    path('api/files/copy/', views_examples.copy_file_api, name='copy-file'),
    path('api/files/move/', views_examples.move_file_api, name='move-file'),
    path('api/files/search/', views_examples.search_files_api, name='search-files'),
]
"""


# ============================================================================
# BACKEND-SPECIFIC FEATURES
# ============================================================================

def backend_specific_example():
    """Examples of backend-specific operations."""
    
    handler = StorageHandler()
    
    # Get backend name
    print(f"Using backend: {handler.backend_name}")
    
    # Get file size
    size = handler.get_file_size('documents/file.pdf')
    print(f"File size: {size} bytes")
    
    # Get public URL
    url = handler.get_file_url('documents/file.pdf')
    print(f"Public URL: {url}")
    
    # Get metadata (backend-specific)
    metadata = handler.get_file_metadata('documents/file.pdf')
    print(f"Metadata: {metadata}")
    
    # S3 specific: metadata in object
    # Metadata: {'app-id': 'vedinka-app', 'app-version': '1.0.0', ...}
    
    # Azure specific: blob properties
    # metadata['metadata']: custom blob metadata
    
    # Local specific: filesystem stats
    # metadata['created'], metadata['modified']


# ============================================================================
# ERROR HANDLING
# ============================================================================

def error_handling_example():
    """How to handle errors properly."""
    
    from apps.storage.storage_handler import (
        StorageHandler,
        StorageOperationError,
        FileNotFoundError as StorageFileNotFoundError,
    )
    
    handler = StorageHandler()
    
    try:
        handler.download_file('nonexistent.pdf')
    except StorageFileNotFoundError as e:
        print(f"File not found: {e}")
    except StorageOperationError as e:
        print(f"Storage error: {e}")
    
    # Safe operations with defaults
    try:
        file_info = handler.get_file('optional-file.pdf')
    except StorageFileNotFoundError:
        file_info = None
    
    if file_info:
        print(f"File exists: {file_info.url}")
    else:
        print("File doesn't exist")
