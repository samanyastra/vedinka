from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

from apps.constants.messages import en as messages
from apps.auth.backend import create_activation_token
from apps.auth.utils import create_activation_link

from apps.messaging.smtp import send_email

User = get_user_model()
logger = logging.getLogger(__name__)


def handle_new_user(user):
    """
    Hook called when a new user is created.

    Implement any post-create logic here: create profile, send welcome
    email, assign default groups, etc. Keep this function small and
    idempotent.
    """
    token = create_activation_token(user, "activate_user")
    activation_link = create_activation_link(token, "hint")

    send_email.delay(
        "activation_mail",
        messages.ACTIVATION_MAIL_SUBJECT,
        user.email,
        activation_link=activation_link,
    )
    logger.info(f"New user created: id={user.pk}, \
                username={getattr(user, 'username', None)}")


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Call `handle_new_user` only when a User is created."""
    if not created:
        return
    try:
        handle_new_user(instance)
    except Exception as e:
        print(f"Exception in signal: {e}")
        logger.exception("Error in user_post_save handler")
