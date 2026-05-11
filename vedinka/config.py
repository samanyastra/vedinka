"""
Centralized configuration loader for Django settings.
This module handles loading environment variables and determining which settings file to use.
"""
import environ
from pathlib import Path


# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / '.env')

# Determine which settings module to use
ENVIRONMENT = env('ENVIRONMENT', default='dev')
SETTINGS_MODULE = 'vedinka.vedinka_settings_prod' if ENVIRONMENT == 'prod' else 'vedinka.settings'


