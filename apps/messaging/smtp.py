from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context

# from celery import shared_task

from .backends import EmailBackend
from .models import MailTemplates, OutBounds
from apps.common.utils import get_object_or_none


# @shared_task(bind=True)
def send_email(status, template_name, subject, *to_mail, **context):
    """should not be called directly only call via send_email.delay"""

    mail_template = get_object_or_none(MailTemplates, name=template_name)

    if mail_template is None:
        raise ValueError("Invalid mail template given")
   
    subject = subject
    # TODO work around need to be done to get from email from settings itself.
    from_mail = mail_template.from_mail
    to_mail = to_mail
    template_string = mail_template.template_name 

    template = Template(template_string)
    mail_body = template.render(Context(context))

    msg = EmailBackend(subject, mail_body, from_mail, to_mail)
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

    mail_template = MailTemplates.objects.get(name=template_name)

    subject = subject
    from_mail = from_mail
    to_mail = to_mail
    template_string = mail_template.template 
    template = Template(template_string)
    mail_body = template.render(Context(context))

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
