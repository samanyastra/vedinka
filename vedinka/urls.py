from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/",
        include(
            [
                path("auth/", include("apps.auth.urls")),
                path("users/", include("apps.users.urls")),
                path("messaging/", include("apps.messaging.urls")),
                # subscriptions
                path("subscriptions/", include("apps.users.subscription_urls")),
                path("user-subscriptions/", include("apps.users.user_subscription_urls")),
                # content
                path("content/", include("apps.content.urls")),
                path("author/", include("apps.content.author_urls")),
                path("schema/", SpectacularAPIView.as_view(), name="schema"),
                path(
                    "swagger-ui/",
                    SpectacularSwaggerView.as_view(url_name="schema"),
                    name="swagger-ui",
                ),
                path(
                    "redoc/",
                    SpectacularRedocView.as_view(url_name="schema"),
                    name="redoc",
                ),
            ]
        ),
    ),
]
