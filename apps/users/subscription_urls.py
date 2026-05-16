"""
URL configuration for subscription management endpoints.
All endpoints require admin authentication.
"""

from django.urls import path

from apps.users.subscription_views import (
    # Subscription Type endpoints
    list_subscription_types,
    get_subscription_type,
    create_subscription_type,
    update_subscription_type,
    delete_subscription_type,
    # User Subscription endpoints
    list_user_subscriptions,
    get_user_subscription,
    assign_subscription_to_user,
    update_user_subscription,
    delete_user_subscription,
)

urlpatterns = [
    # Subscription Type endpoints
    path(
        "subscription-types/", list_subscription_types, name="list_subscription_types"
    ),
    path(
        "subscription-types/<uuid:subscription_id>/",
        get_subscription_type,
        name="get_subscription_type",
    ),
    path(
        "subscription-types/create/",
        create_subscription_type,
        name="create_subscription_type",
    ),
    path(
        "subscription-types/<uuid:subscription_id>/update/",
        update_subscription_type,
        name="update_subscription_type",
    ),
    path(
        "subscription-types/<uuid:subscription_id>/delete/",
        delete_subscription_type,
        name="delete_subscription_type",
    ),
    # User Subscription endpoints
    path(
        "user-subscriptions/", list_user_subscriptions, name="list_user_subscriptions"
    ),
    path(
        "user-subscriptions/<uuid:subscription_id>/",
        get_user_subscription,
        name="get_user_subscription",
    ),
    path(
        "user-subscriptions/assign/",
        assign_subscription_to_user,
        name="assign_subscription_to_user",
    ),
    path(
        "user-subscriptions/<uuid:subscription_id>/update/",
        update_user_subscription,
        name="update_user_subscription",
    ),
    path(
        "user-subscriptions/<uuid:subscription_id>/delete/",
        delete_user_subscription,
        name="delete_user_subscription",
    ),
]
