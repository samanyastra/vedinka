from datetime import timedelta
from .settings import *
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / '.env')

# Override default settings for production below

# DB Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_prod.sqlite3',
    }
}


# Production-specific overrides below
# DEBUG = False  # Enable in production
# ALLOWED_HOSTS = ['yourdomain.com']

OUTLOOK_CLIENT_ID=env("OUTLOOK_CLIENT_ID", '')
OUTLOOK_CLIENT_SECRET=env("OUTLOOK_CLIENT_SECRET", '')
OUTLOOK_TENANT_ID=env("OUTLOOK_TENANT_ID", '')