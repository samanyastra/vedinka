from django.urls import path, include

from apps.users.views import (
    get_user_profile,
    complete_user_profile,
    update_user_profile,
)

urlpatterns = [
    path("profile/", get_user_profile, name="get_user_profile"),
    path("profile/complete/", complete_user_profile, name="complete_user_profile"),
    path("profile/update/", update_user_profile, name="update_user_profile"),
    path("subscriptions/", include("apps.users.user_subscription_urls")),
]
