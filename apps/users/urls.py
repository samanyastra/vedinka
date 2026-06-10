from django.urls import path, include

from apps.users.views import (
    get_user_profile,
    complete_user_profile,
    update_user_profile,
    get_bank_details,
    add_or_update_bank_details,
)

urlpatterns = [
    path("profile/", get_user_profile, name="get_user_profile"),
    path("profile/complete/", complete_user_profile, name="complete_user_profile"),
    path("profile/update/", update_user_profile, name="update_user_profile"),
    path("bank-details/", get_bank_details, name="get_bank_details"),
    path("bank-details/add/", add_or_update_bank_details, name="add_or_update_bank_details"),
]
