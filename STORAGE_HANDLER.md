# StorageHandler - Universal File Storage API

A unified, backend-agnostic file storage interface that works seamlessly with **Local**, **Azure Blob Storage**, and **AWS S3** backends.

## Overview

`StorageHandler` abstracts away backend differences and provides a consistent API for:
- ✅ Upload files
- ✅ Download files  
- ✅ Delete files
- ✅ List files
- ✅ Search files
- ✅ Copy/Move files
- ✅ Get file metadata
- ✅ Auto-detect backend

**Single line initialization:**
```python
handler = StorageHandler()
```

Works with **any** configured backend (Local/Azure/S3) — no code changes needed.

---

## Installation

Already installed in `apps/storage/storage_handler.py`. Import:

```python
from apps.storage.storage_handler import StorageHandler, StorageOperationError, FileNotFoundError
```

---

## Quick Start

### Upload File
```python
from apps.storage.storage_handler import StorageHandler

handler = StorageHandler()

# Upload from file object
with open('document.pdf', 'rb') as f:
    file_info = handler.upload_file('documents/document.pdf', f)
    
print(f"URL: {file_info.url}")
print(f"Size: {file_info.size} bytes")
```

### Download File
```python
content = handler.download_file('documents/document.pdf')
# content is bytes
```

### Delete File
```python
deleted = handler.delete_file('documents/document.pdf')
# Returns True if deleted, False if not found
```

### List Files
```python
files = handler.list_files('documents/')
for file_info in files:
    print(f"{file_info.name}: {file_info.url}")
```

### Search Files
```python
pdf_files = handler.search_files('*.pdf')
print(f"Found {len(pdf_files)} PDFs")
```

---

## API Reference

### Initialization

```python
handler = StorageHandler(storage_type='default')
```

**Parameters:**
- `storage_type`: `'default'` for media files (default), or `'staticfiles'` for static files

**Attributes:**
- `handler.storage_type`: Current storage type
- `handler.backend_name`: Detected backend ('local', 'azure', or 's3')

---

### Upload

```python
file_info = handler.upload_file(
    file_path: str,
    file_content: Union[BinaryIO, bytes],
    overwrite: bool = True,
    metadata: Optional[Dict[str, str]] = None
) -> StorageFileInfo
```

**Parameters:**
- `file_path`: Path/name in storage (e.g., `'documents/report.pdf'`)
- `file_content`: File object or raw bytes
- `overwrite`: Whether to replace if exists
- `metadata`: Optional metadata dict (S3 only)

**Returns:** `StorageFileInfo` object with file details

**Raises:** `StorageOperationError` on failure

**Example:**
```python
# From file object
with open('report.pdf', 'rb') as f:
    file_info = handler.upload_file('reports/q1-2025.pdf', f)

# From bytes
file_info = handler.upload_file('data.json', b'{"key": "value"}')
```

---

### Download

```python
content = handler.download_file(file_path: str) -> bytes
```

**Returns:** File content as bytes

**Raises:** `FileNotFoundError` if not found, `StorageOperationError` on other errors

**Example:**
```python
try:
    content = handler.download_file('documents/report.pdf')
    with open('local_copy.pdf', 'wb') as f:
        f.write(content)
except FileNotFoundError:
    print("File not found")
```

---

### Delete

```python
deleted = handler.delete_file(file_path: str) -> bool
```

**Returns:** `True` if deleted, `False` if file didn't exist

**Raises:** `StorageOperationError` on errors

**Example:**
```python
if handler.delete_file('documents/old.pdf'):
    print("Deleted successfully")
else:
    print("File not found")
```

---

### Get File Info

```python
file_info = handler.get_file(file_path: str) -> StorageFileInfo
```

**Returns:** `StorageFileInfo` with metadata

**Raises:** `FileNotFoundError` if not found

**StorageFileInfo attributes:**
- `name`: File path
- `size`: Size in bytes
- `url`: Public URL
- `created_at`: Creation timestamp
- `modified_at`: Last modified timestamp
- `storage_backend`: Backend name
- `metadata`: Backend-specific metadata dict

**Example:**
```python
file_info = handler.get_file('documents/report.pdf')
print(f"Name: {file_info.name}")
print(f"Size: {file_info.size} bytes")
print(f"URL: {file_info.url}")
print(f"Backend: {file_info.storage_backend}")
print(f"Dict: {file_info.to_dict()}")  # For JSON serialization
```

---

### List Files

```python
files = handler.list_files(folder_path: str = '') -> List[StorageFileInfo]
```

**Parameters:**
- `folder_path`: Folder/prefix to list (empty = root)

**Returns:** List of `StorageFileInfo` objects

**Raises:** `StorageOperationError` on errors

**Example:**
```python
# List all in root
all_files = handler.list_files()

# List in specific folder
docs = handler.list_files('documents/')

# Display
for file_info in docs:
    print(f"{file_info.name} ({file_info.size} bytes)")
```

---

### Search Files

```python
files = handler.search_files(pattern: str) -> List[StorageFileInfo]
```

**Parameters:**
- `pattern`: Glob pattern (e.g., `'*.pdf'`, `'reports/*.xlsx'`)

**Returns:** List of matching `StorageFileInfo` objects

**Raises:** `StorageOperationError` on errors

**Example:**
```python
# Find all PDFs
pdfs = handler.search_files('*.pdf')

# Find in specific folder
reports = handler.search_files('reports/*.xlsx')

# Complex patterns
data = handler.search_files('2025-*.json')
```

---

### Copy File

```python
file_info = handler.copy_file(
    source_path: str,
    dest_path: str,
    overwrite: bool = True
) -> StorageFileInfo
```

**Parameters:**
- `source_path`: Source file path
- `dest_path`: Destination path
- `overwrite`: Replace if exists

**Returns:** `StorageFileInfo` for copied file

**Example:**
```python
file_info = handler.copy_file('documents/original.pdf', 'backups/original.pdf')
print(f"Copied to: {file_info.url}")
```

---

### Move File

```python
file_info = handler.move_file(
    source_path: str,
    dest_path: str,
    overwrite: bool = True
) -> StorageFileInfo
```

**Performs copy then delete (atomic within storage limits)**

**Example:**
```python
file_info = handler.move_file('documents/report.pdf', 'archive/report.pdf')
```

---

### Utility Methods

```python
# Check if file exists
exists = handler.file_exists(file_path: str) -> bool

# Get file size
size = handler.get_file_size(file_path: str) -> int

# Get public URL
url = handler.get_file_url(file_path: str) -> str

# Get metadata (backend-specific)
metadata = handler.get_file_metadata(file_path: str) -> Dict[str, Any]
```

**Examples:**
```python
if handler.file_exists('document.pdf'):
    size = handler.get_file_size('document.pdf')
    url = handler.get_file_url('document.pdf')
    meta = handler.get_file_metadata('document.pdf')
```

---

## StorageFileInfo Object

Represents metadata about a stored file.

**Attributes:**
```python
file_info.name              # File path in storage
file_info.size              # Size in bytes
file_info.created_at        # Creation datetime
file_info.modified_at       # Last modified datetime
file_info.url               # Public/accessible URL
file_info.storage_backend   # 'local', 'azure', or 's3'
file_info.metadata          # Dict of backend-specific metadata
```

**Methods:**
```python
# Convert to dict (for JSON serialization)
data = file_info.to_dict()
# {'name': '...', 'size': 123, 'url': '...', ...}

# String representation
print(file_info)
# <StorageFileInfo name=... size=... url=...>
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── StorageOperationError
│   ├── FileNotFoundError
│   └── (other operation failures)
```

**Exception Classes:**

```python
from apps.storage.storage_handler import (
    StorageOperationError,    # Base exception
    FileNotFoundError,        # File not found
)
```

### Error Handling Pattern

```python
try:
    file_info = handler.get_file('document.pdf')
except FileNotFoundError:
    print("File doesn't exist")
except StorageOperationError as e:
    print(f"Storage error: {e}")
```

### Safe Operations

```python
# Graceful fallback
def get_file_safe(file_path):
    try:
        return handler.get_file(file_path)
    except FileNotFoundError:
        return None

file_info = get_file_safe('optional.pdf')
if file_info:
    print(f"URL: {file_info.url}")
```

---

## Backend-Specific Information

### Local Filesystem

**Backend Detection:**
```python
handler.backend_name  # 'local'
```

**Metadata:**
```python
meta = handler.get_file_metadata('file.pdf')
# {'created': '2025-01-15T10:30:00', 'modified': '2025-01-15T10:30:00'}
```

**Best For:**
- Development
- Testing
- Small deployments

---

### Azure Blob Storage

**Backend Detection:**
```python
handler.backend_name  # 'azure'
```

**Metadata:**
```python
meta = handler.get_file_metadata('file.pdf')
# {
#   'size': 102400,
#   'content_type': 'application/pdf',
#   'last_modified': '2025-01-15T10:30:00Z',
#   'metadata': {'app-id': 'vedinka-app', ...}
# }
```

**URLs:**
```python
file_info.url
# https://account.blob.core.windows.net/container/path/file.pdf
```

**Best For:**
- Microsoft Azure deployments
- Enterprise Microsoft integration

---

### AWS S3

**Backend Detection:**
```python
handler.backend_name  # 's3'
```

**Metadata:**
```python
meta = handler.get_file_metadata('file.pdf')
# {
#   'size': 102400,
#   'content_type': 'application/pdf',
#   'last_modified': '2025-01-15T10:30:00Z',
#   'metadata': {'app-id': 'vedinka-app', 'app-version': '1.0.0'},
#   'etag': '"abc123"'
# }
```

**URLs:**
```python
# Without custom domain
file_info.url
# https://bucket.s3.us-east-1.amazonaws.com/path/file.pdf

# With CloudFront
file_info.url
# https://cdn.vedinka.com/path/file.pdf
```

**Best For:**
- AWS deployments
- Global CDN via CloudFront
- Large-scale applications

---

## REST API Integration

### Upload API
```python
@api_view(['POST'])
def upload_file(request):
    handler = StorageHandler()
    file_obj = request.FILES['file']
    file_info = handler.upload_file(f'uploads/{file_obj.name}', file_obj)
    return Response(file_info.to_dict())
```

### List API
```python
@api_view(['GET'])
def list_files(request):
    folder = request.query_params.get('folder', '')
    handler = StorageHandler()
    files = handler.list_files(folder)
    return Response({
        'count': len(files),
        'files': [f.to_dict() for f in files]
    })
```

### Download API
```python
@api_view(['GET'])
def get_file(request, file_path):
    handler = StorageHandler()
    file_info = handler.get_file(file_path)
    return Response(file_info.to_dict())
```

See `storage_handler_examples.py` for complete REST framework implementations.

---

## Common Patterns

### Save Uploaded File

```python
handler = StorageHandler()
uploaded_file = request.FILES['document']
file_info = handler.upload_file(
    file_path=f'user-{request.user.id}/{uploaded_file.name}',
    file_content=uploaded_file
)
# Store file_info.url in database
```

### Download and Serve

```python
from django.http import FileResponse
from io import BytesIO

handler = StorageHandler()
content = handler.download_file('documents/report.pdf')
return FileResponse(BytesIO(content), as_attachment=True)
```

### Organize by Date

```python
from datetime import datetime

handler = StorageHandler()
today = datetime.now().strftime('%Y/%m/%d')
file_info = handler.upload_file(
    file_path=f'logs/{today}/activity.log',
    file_content=log_content
)
```

### Backup Files

```python
handler = StorageHandler()
for file_path in important_files:
    handler.copy_file(
        file_path,
        f'backups/{file_path}'
    )
```

### Clean Up Old Files

```python
handler = StorageHandler()
old_files = handler.search_files('temp/*.tmp')
for file_info in old_files:
    handler.delete_file(file_info.name)
```

---

## Performance Considerations

### Bulk Operations

For many files, batch operations when possible:

```python
# Less efficient - many individual operations
for file in files:
    handler.upload_file(...)

# More efficient - use list operations
files_to_upload = handler.list_files('staging/')
# Process as batch
```

### Streaming Large Files

For large files, consider streaming instead of loading into memory:

```python
# S3: Use presigned URLs for direct browser upload
url = handler.get_file_url('large-file.iso')
# Client uploads directly to S3

# Azure: Similar - use SAS URLs
```

### Caching

Cache file metadata to avoid repeated lookups:

```python
from django.views.decorators.cache import cache_page

@cache_page(60)
def get_files_list(request):
    handler = StorageHandler()
    return Response(handler.list_files('documents/'))
```

---

## Troubleshooting

### "File not found" when it exists

**Causes:**
- Path mismatch (case-sensitive on some backends)
- Wrong storage type (default vs staticfiles)
- Different backend than expected

**Solution:**
```python
# List to verify path
files = handler.list_files()
for f in files:
    if 'myfile' in f.name.lower():
        print(f"Found: {f.name}")
```

### Permission errors

**Cause:** IAM/access credentials insufficient

**Solution:**
- Verify AWS/Azure credentials and permissions
- Check bucket/container policies
- Ensure IAM user has required S3 permissions

### Backend not detected

**Cause:** Storage not configured

**Solution:**
```python
from django.conf import settings
print(settings.STORAGES)  # Verify configuration
```

---

## Security Best Practices

1. **Access Control:**
   - Use IAM roles/policies to restrict access
   - Never expose credentials in code

2. **File Validation:**
   ```python
   # Validate file type
   if not file_obj.name.endswith('.pdf'):
       raise ValidationError("Only PDFs allowed")
   ```

3. **Path Traversal Prevention:**
   ```python
   # Safe path handling
   import os
   safe_path = os.path.normpath(user_path)
   if '..' in safe_path:
       raise ValidationError("Invalid path")
   ```

4. **Encryption:**
   - Enable server-side encryption on S3/Azure
   - Use HTTPS for all file transfers

---

## Examples

See `storage_handler_examples.py` for:
- Basic usage
- File operations
- REST API views
- DRF integration
- Error handling
- Backend-specific examples
