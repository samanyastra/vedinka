# Storage Backend Setup - Quick Start

## Overview

The Vedinka application now supports flexible storage backends for static and media files:

| Backend | Best For | Cloud | Complexity |
|---------|----------|-------|-----------|
| **Local** | Development | ❌ | ⭐ |
| **Azure** | Production (Microsoft) | ✅ | ⭐⭐⭐ |
| **S3** | Production (AWS) | ✅ | ⭐⭐⭐ |

---

## Quick Start

### 1. Local Storage (Default - No Setup Needed)

Already configured for development. Files stored locally.

```bash
STORAGE_BACKEND=local
```

**URLs:**
- Static: `http://localhost:8000/static/`
- Media: `http://localhost:8000/media/`

---

### 2. Azure Blob Storage

#### Prerequisites
```bash
pip install django-storages[azure]
```

#### Setup in `.env`
```bash
STORAGE_BACKEND=azure
AZURE_ACCOUNT_NAME=myaccount
AZURE_ACCOUNT_KEY=your-key-here
AZURE_CONTAINER_STATIC=static
AZURE_CONTAINER_MEDIA=media
```

#### Create Containers
```bash
az storage container create --name static --account-name myaccount
az storage container create --name media --account-name myaccount
```

#### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

**URLs Generated:**
- Static: `https://myaccount.blob.core.windows.net/static/`
- Media: `https://myaccount.blob.core.windows.net/media/`

---

### 3. AWS S3

#### Prerequisites
```bash
pip install django-storages[s3]
```

#### Setup in `.env`
```bash
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=my-bucket
AWS_S3_REGION_NAME=us-east-1
```

#### With CloudFront CDN (Optional)
```bash
AWS_S3_CUSTOM_DOMAIN=d123.cloudfront.net
```

#### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

**URLs Generated:**
- Without CDN: `https://my-bucket.s3.us-east-1.amazonaws.com/`
- With CDN: `https://d123.cloudfront.net/`

---

## Environment File Examples

### Development
```bash
# .env
STORAGE_BACKEND=local
```

### Staging (Azure)
```bash
# .env
STORAGE_BACKEND=azure
AZURE_ACCOUNT_NAME=vedinka-staging
AZURE_ACCOUNT_KEY=...
```

### Production (S3 + CloudFront)
```bash
# .env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=vedinka-prod
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=cdn.vedinka.com
```

---

## Switching Backends

1. Update `STORAGE_BACKEND` in `.env`
2. Install required package (if needed)
3. Set environment variables for the new backend
4. Collect static files: `python manage.py collectstatic --noinput`
5. Restart application

---

## Files Reference

- **Configuration**: `vedinka/storage_config.py`
- **Settings Integration**: `vedinka/settings.py` (lines with STORAGES, STATIC_URL, MEDIA_URL)
- **Documentation**: `STORAGE_CONFIG.md` (detailed guide)
- **Environment Template**: `.env.example`

---

## Common Commands

```bash
# Collect static files to storage backend
python manage.py collectstatic --noinput

# Check current configuration
python manage.py shell
>>> from django.conf import settings
>>> print(settings.STORAGES)
>>> print(settings.STATIC_URL)
```

---

## Troubleshooting

**Import Error in settings.py?**
- Ensure `vedinka/storage_config.py` exists
- Check syntax: `python3 -m py_compile vedinka/storage_config.py`

**Azure "Access Denied"?**
- Verify AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY
- Check container permissions

**S3 "Access Denied"?**
- Verify AWS credentials are correct
- Ensure IAM user has S3 permissions

**Files not showing up?**
- Run `python manage.py collectstatic --noinput`
- Verify URLs are correct in templates

---

## Full Documentation

See [STORAGE_CONFIG.md](STORAGE_CONFIG.md) for complete setup instructions and advanced configuration.
