"""
URL routing for user subscription endpoints.
"""
from django.urls import path
from apps.users.user_subscription_views import (
    get_my_subscription,
    view_all_subscriptions,
    create_subscription_order,
    verify_payment,
    generate_invoice,
)

urlpatterns = [
    path('my-subscription/', get_my_subscription, name='get_my_subscription'),
    path('available-subscriptions/', view_all_subscriptions, name='view_all_subscriptions'),
    path('create-order/', create_subscription_order, name='create_subscription_order'),
    path('verify-payment/', verify_payment, name='verify_payment'),
    path('generate-invoice/', generate_invoice, name='generate_invoice'),
]
