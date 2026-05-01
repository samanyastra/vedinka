import requests
from django.conf import settings
from apps.messaging.backends import EmailBackend

class OutlookBackend(EmailBackend):

    def __init__(self, subject, message_body, sender, to, cc=[], bcc=[], attachements=[]):

        self.client_id = settings.OUTLOOK_CLIENT_ID
        self.client_secret = settings.OUTLOOK_CLIENT_SECRET
        self.tenant_id = settings.OUTLOOK_TENANT_ID

        self.default_from_url = "https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"
        self.token_url = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        
        self.subject = subject
        self.sender = sender
        self.to = to
        self.cc = cc
        self.bcc = bcc
        self.message_body = message_body
        self.attachements = attachements
        super().__init__()

    
    def get_auth_token(self) -> str | None:
        payload = {
        "client_id": self.client_id,
        "client_secret": self.client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
        }
        response = requests.post(self.token_url.format(tenant_id=self.tenant_id), data=payload)
    
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print("Error fetching token:", response.json())
            return None

    def format_receipients_list(self, receipients):
        """formats regular list of receipients to outlook supported format"""

        formatted_receipeients = []
        for receipient in receipients:
            obj = {"emailAddress": {"address": receipient}}
            formatted_receipeients.append(obj)
        return formatted_receipeients
    
    def convert_attachemtns(self):
        """this is not tested or completed"""
        attachments = []
        for attachment in self.attachements:
            attachments.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": attachment.name,
                "contentBytes": attachment.read()
            })
    

    def prepare_email(self):
        """takes to, cc, and bcc converts to graph api requirements"""
        to = self.format_receipients_list(self.to)
        cc = self.format_receipients_list(self.cc)
        email_data = {
            "message": {
                "subject": self.subject,
                "body": {
                    "contentType": "HTML",
                    "content": self.message_body
                },
                "toRecipients": to,
                "ccRecipients": cc,
            }
        }
        self.email_data = email_data
        return self.email_data

    def send(self):
        access_token = self.get_auth_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        if access_token:
            self.prepare_email()
            response = requests.post(self.default_from_url.format(sender_email=self.sender), headers=headers, json=self.email_data)

            if response.status_code == 202:
                print("Email sent successfully!")
            else:
                print("Error sending email:", response.json())
