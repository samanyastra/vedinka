from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def handle_new_user(user):
    """
    Hook called when a new user is created.

    Implement any post-create logic here: create profile, send welcome
    email, assign default groups, etc. Keep this function small and
    idempotent.
    """
    # Example: log the creation (caller can extend this function)
    logger.info(f"New user created: id={user.pk}, username={getattr(user, 'username', None)}")


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Call `handle_new_user` only when a User is created."""
    if not created:
        return
    try:
        handle_new_user(instance)
    except Exception:
        # Protect the save flow from signal errors
        logger.exception("Error in user_post_save handler")
