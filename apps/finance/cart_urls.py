"""
URL routing for cart endpoints.
"""
from django.urls import path
from apps.finance.cart_views import (
    get_user_cart,
    add_to_cart,
    remove_from_cart,
    clear_cart,
)

urlpatterns = [
    path('cart/', get_user_cart, name='get_user_cart'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/remove/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),
]
