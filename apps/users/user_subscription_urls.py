"""
URL routing for user subscription endpoints.
"""
from django.urls import path
from apps.users.user_subscription_views import (
    get_my_subscription,
    view_all_subscriptions,
    create_subscription_order,
    verify_payment_for_subscription,
    generate_invoice,
)

urlpatterns = [
    path('my/', get_my_subscription, name='get_my_subscription'),
    path('get-all-to-buy/', view_all_subscriptions, name='view_all_subscriptions'),
    path('create-buy-order/', create_subscription_order, name='create_subscription_order'),
    path('verify-payment-for-subscription/', verify_payment_for_subscription, name='verify_payment_for_subscription'),
    path('generate-invoice/', generate_invoice, name='generate_invoice'),
]
