from __future__ import absolute_import
import os
from celery import Celery
from .config import SETTINGS_MODULE

os.environ.setdefault('DJANGO_SETTINGS_MODULE', SETTINGS_MODULE)
app = Celery('vedinka',)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
