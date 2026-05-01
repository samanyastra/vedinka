from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'apps.users'
    verbose_name = "Users"

    def ready(self):
        # Import signal handlers to ensure they are registered
        try:
            import apps.users.signals  # noqa: F401
        except Exception:
            # Avoid raising on import errors during migrations or testing
            pass
