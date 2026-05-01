from django.urls import path

from apps.auth.views import register_user, login, refresh, logout


urlpatterns = [
    path("register", register_user, name="register_user"),
    path("login", login, name="login"),
    path("refresh_auth", refresh, name="refresh"),
    path("logout", logout, name="logout"),
]