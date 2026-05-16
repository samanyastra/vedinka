from django.urls import include, path

from apps.auth.viewsets import TokenTypesViewset
from rest_framework.routers import DefaultRouter
from apps.auth.views import (forgot_password, register_user, 
                             login,
                             refresh,
                             logout,
                             activate_user,
                             forgot_password, 
                             resend_activation_link
                             )

router = DefaultRouter()
router.register(r'token-types', TokenTypesViewset)


urlpatterns = [
    path("register", register_user, name="register_user"),
    path("login", login, name="login"),
    path("refresh_auth", refresh, name="refresh"),
    path("logout", logout, name="logout"),
    path("activate", activate_user, name="activate user"),
    path('resend-activation-mail', resend_activation_link, name="resend acitvation link"),
    path("forgot-password", forgot_password, name="forgot_password"),
    path('', include(router.urls)),
]