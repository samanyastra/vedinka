"""
URL configuration for finance app endpoints.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('apps.finance.cart_urls')),
    path('', include('apps.finance.bill_urls')),
]
