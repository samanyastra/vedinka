from datetime import timedelta
from .settings import *
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / '.env')

# Override default settings for production below

# DB Configuration
DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db_prod.sqlite3',
    # }
     'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}


# Production-specific overrides below
# DEBUG = False  # Enable in production
# ALLOWED_HOSTS = ['yourdomain.com']

OUTLOOK_CLIENT_ID=env("OUTLOOK_CLIENT_ID", default='')
OUTLOOK_CLIENT_SECRET=env("OUTLOOK_CLIENT_SECRET", default='')
OUTLOOK_TENANT_ID=env("OUTLOOK_TENANT_ID", default='')


DOMAIN_ADDRESS = "http://localhost:5173/"