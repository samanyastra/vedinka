from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings

from celery import shared_task

from .backends.outlook import OutlookBackend
from .models import MailTemplates, OutBounds
from apps.common.utils import get_object_or_none


@shared_task(bind=True)
def send_email(status, template_name: str, subject: str, *to_mail, **context):
    """should not be called directly only call via send_email.delay"""

    mail_template = get_object_or_none(MailTemplates, template_name=template_name)
    print(mail_template)

    if mail_template is None:
        raise ValueError("Invalid mail template given")
   
    subject = subject
    from_mail = settings.DEFAULT_FROM_MAIL
    template_string = mail_template.get_template_string() 

    template = Template(template_string)
    mail_body = template.render(Context(context))

    msg = OutlookBackend(subject, message_body=mail_body, sender=from_mail, to=[*to_mail])
    msg.send()

    mail_obj = OutBounds.objects.create( 
        mail_template=mail_template,
        to_mail=to_mail,
        body=mail_body
    )
    mail_obj.save()
    return True


# @shared_task(bind=True)
def send_email_with_attachment(status, template_name, subject, *to_mail, **context):

    mail_template = MailTemplates.objects.get(template_name=template_name)

    subject = subject
    to_mail = to_mail
    template_string = mail_template.get_template_string() 
    template = Template(template_string)
    mail_body = template.render(Context(context))
    from_mail = settings.DEFAULT_FROM_MAIL

    msg = EmailMultiAlternatives(subject,
                                 mail_body,
                                 from_mail,
                                 to_mail,
                                 )
    msg.attach_alternative(mail_body, "text/html")
    msg.send()

    mail_obj = OutBounds.objects.create(
        mail_template=mail_template,
        to_mail=to_mail,
        body=mail_body
    )
    mail_obj.save()
    return True
