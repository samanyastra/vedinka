from django.urls import include, path

from apps.auth.viewsets import TokenTypesViewset
from rest_framework.routers import DefaultRouter
from apps.auth.views import (
    register_user,
    login,
    refresh,
    logout,
    activate_user,
    resend_activation_link,
    forgot_password,
    reset_password,
)

router = DefaultRouter()
router.register(r'token-types', TokenTypesViewset)


urlpatterns = [
    path("register", register_user, name="register_user"),
    path("login", login, name="login"),
    path("refresh_auth", refresh, name="refresh"),
    path("logout", logout, name="logout"),
    path("activate", activate_user, name="activate_user"),
    path("resend-activation-mail", resend_activation_link, name="resend_activation_link"),
    path("forgot-password", forgot_password, name="forgot_password"),
    path("reset-password", reset_password, name="reset_password"),
    path('', include(router.urls)),
]