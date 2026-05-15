# Storage Configuration Guide

This document explains how to configure and use the flexible storage backend system in Vedinka.

## Overview

The storage system is designed to support multiple backends:
- **Local** (default): Local filesystem storage
- **Azure**: Azure Blob Storage
- **S3**: AWS S3 Storage

Switch between backends by setting the `STORAGE_BACKEND` environment variable.

## Backends

### 1. Local Storage (Default)

Stores files on the local filesystem. Best for development.

**Environment Variables:**
```bash
STORAGE_BACKEND=local
STATIC_ROOT=/path/to/static
MEDIA_ROOT=/path/to/media
```

**Defaults:**
- `STATIC_ROOT`: `{BASE_DIR}/staticfiles`
- `MEDIA_ROOT`: `{BASE_DIR}/media`
- `STATIC_URL`: `/static/`
- `MEDIA_URL`: `/media/`

**Setup:**
```bash
# No additional setup needed. Files are stored locally.
```

---

### 2. Azure Blob Storage

Cloud-based storage using Microsoft Azure.

**Environment Variables:**
```bash
STORAGE_BACKEND=azure
AZURE_ACCOUNT_NAME=myaccount
AZURE_ACCOUNT_KEY=your-account-key
# OR use connection string instead of account key:
AZURE_CONNECTION_STRING=DefaultEndpointProtocol=https;AccountName=...

# Optional (defaults to 'static' and 'media')
AZURE_CONTAINER_STATIC=static
AZURE_CONTAINER_MEDIA=media
```

**Setup:**

1. **Create Azure Storage Account:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new Storage Account
   - Copy the account name and key (or full connection string)

2. **Create Containers:**
   ```bash
   az storage container create --name static --account-name myaccount
   az storage container create --name media --account-name myaccount
   ```
   Or use Azure Portal UI to create containers.

3. **Update `.env`:**
   ```bash
   STORAGE_BACKEND=azure
   AZURE_ACCOUNT_NAME=myaccount
   AZURE_ACCOUNT_KEY=your-key-here
   AZURE_CONTAINER_STATIC=static
   AZURE_CONTAINER_MEDIA=media
   ```

4. **URLs Generated:**
   - `STATIC_URL`: `https://myaccount.blob.core.windows.net/static/`
   - `MEDIA_URL`: `https://myaccount.blob.core.windows.net/media/`

**Requirements:**
```bash
pip install django-storages[azure]
```

---

### 3. AWS S3 Storage

Cloud-based storage using Amazon Web Services S3.

**Environment Variables:**
```bash
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=my-app-bucket
AWS_S3_REGION_NAME=us-east-1
# Optional:
AWS_S3_CUSTOM_DOMAIN=cdn.example.com
AWS_S3_OBJECT_PARAMETERS={"CacheControl":"max-age=86400"}
```

**Setup:**

1. **Create S3 Bucket:**
   - Go to [AWS S3 Console](https://s3.console.aws.amazon.com)
   - Create a new bucket (e.g., `my-app-bucket`)
   - Note the region

2. **Create IAM User with S3 Permissions:**
   - Go to [AWS IAM Console](https://console.aws.amazon.com/iam)
   - Create a new user
   - Attach policy: `AmazonS3FullAccess` (or create custom policy)
   - Generate access keys

3. **Configure Bucket Policy (if needed):**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::my-app-bucket/*"
       }
     ]
   }
   ```

4. **Update `.env`:**
   ```bash
   STORAGE_BACKEND=s3
   AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_STORAGE_BUCKET_NAME=my-app-bucket
   AWS_S3_REGION_NAME=us-east-1
   ```

5. **Optional: CloudFront CDN:**
   ```bash
   AWS_S3_CUSTOM_DOMAIN=d12345.cloudfront.net
   ```

6. **URLs Generated (without custom domain):**
   - `STATIC_URL`: `https://my-app-bucket.s3.us-east-1.amazonaws.com/static/`
   - `MEDIA_URL`: `https://my-app-bucket.s3.us-east-1.amazonaws.com/media/`

7. **URLs Generated (with custom domain):**
   - `STATIC_URL`: `https://cdn.example.com/static/`
   - `MEDIA_URL`: `https://cdn.example.com/media/`

**Requirements:**
```bash
pip install django-storages[s3]
```

---

## Configuration Files

### `vedinka/storage_config.py`

Core storage configuration module. Contains:
- `get_local_storage_config(base_dir)` - Local storage setup
- `get_azure_storage_config()` - Azure setup
- `get_s3_storage_config()` - S3 setup
- `get_storage_config(base_dir)` - Dispatcher (returns config for active backend)
- `get_static_and_media_urls(base_dir)` - URL configuration
- `get_static_and_media_roots(base_dir)` - Root paths for local storage

### `vedinka/settings.py`

Imports and uses storage configuration:
```python
from vedinka.storage_config import (
    get_storage_config,
    get_static_and_media_urls,
    get_static_and_media_roots,
    STORAGE_BACKEND,
)

STORAGES = get_storage_config(BASE_DIR)
STATIC_URL, MEDIA_URL = get_static_and_media_urls(BASE_DIR)
```

### `.env` (or `.env.example`)

Environment variables for all backends.

---

## Switching Between Backends

### From Local to Azure

1. Update `.env`:
   ```bash
   STORAGE_BACKEND=azure
   AZURE_ACCOUNT_NAME=myaccount
   AZURE_ACCOUNT_KEY=key-here
   ```

2. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. Restart the application.

### From Local to S3

1. Update `.env`:
   ```bash
   STORAGE_BACKEND=s3
   AWS_ACCESS_KEY_ID=key-here
   AWS_SECRET_ACCESS_KEY=secret-here
   AWS_STORAGE_BUCKET_NAME=bucket-name
   ```

2. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

3. Restart the application.

---

## Advanced Configuration

### S3 with Additional Options

Pass additional S3 parameters as a JSON string:

```bash
AWS_S3_OBJECT_PARAMETERS='{"CacheControl":"max-age=86400","ACL":"public-read"}'
```

Parsed options:
- `CacheControl`: HTTP cache headers
- `ACL`: Access control list (e.g., "public-read", "private")
- `Metadata`: Custom metadata
- `ServerSideEncryption`: Encryption type (e.g., "AES256")

### Azure with Connection String

Instead of separate account name and key, use the full connection string:

```bash
STORAGE_BACKEND=azure
AZURE_CONNECTION_STRING=DefaultEndpointProtocol=https;AccountName=myaccount;AccountKey=key==;EndpointSuffix=core.windows.net
```

---

## Troubleshooting

### "Storage backend not configured"
- Check `STORAGE_BACKEND` is set in `.env`
- Ensure required environment variables for the chosen backend are present

### "Access denied" (Azure/S3)
- Verify credentials are correct
- Check IAM permissions (for S3)
- Verify container/bucket access policies

### Files not uploading
- Ensure storage package is installed: `pip install django-storages[backend]`
- Check file permissions and ownership
- Review Django logs for specific errors

### URLs returning 404
- For local storage: ensure `STATIC_ROOT` and `MEDIA_ROOT` directories exist
- For cloud storage: verify bucket/container is public or has proper CORS configuration
- Check `STATIC_URL` and `MEDIA_URL` configuration

---

## Performance Tips

### Local Storage
- Use for development only
- Consider using a CDN for static files in production

### Azure
- Use container-level SAS tokens for temporary access
- Consider lifecycle policies for archival
- Enable CDN through Azure CDN service

### S3
- Use CloudFront CDN for better performance
- Enable S3 Transfer Acceleration for faster uploads
- Use multipart upload for large files
- Configure S3 object lifecycle policies

---

## Security Considerations

1. **Credentials**: Never commit credentials to version control. Use `.env` files only locally.
2. **IAM Permissions**: Use least privilege principle. Grant only necessary S3/Azure permissions.
3. **Public Access**: Carefully configure which files should be publicly accessible.
4. **CORS**: For cross-origin file access, configure CORS policies properly.
5. **Encryption**: Use server-side encryption for sensitive files.

---

## Example: Complete Multi-Environment Setup

**Development (.env.local):**
```bash
STORAGE_BACKEND=local
```

**Staging (.env.staging):**
```bash
STORAGE_BACKEND=azure
AZURE_ACCOUNT_NAME=staging-account
AZURE_ACCOUNT_KEY=staging-key
```

**Production (.env.prod):**
```bash
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=prod-key
AWS_SECRET_ACCESS_KEY=prod-secret
AWS_STORAGE_BUCKET_NAME=prod-bucket
AWS_S3_CUSTOM_DOMAIN=cdn.vedinka.com
```

Load the appropriate `.env` file based on environment:
```bash
# Development
export ENV=local && python manage.py runserver

# Staging
export ENV=staging && gunicorn vedinka.wsgi

# Production
export ENV=prod && gunicorn vedinka.wsgi
```
