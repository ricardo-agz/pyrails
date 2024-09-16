import os
import abc
import requests
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
import boto3


class EmailProvider(abc.ABC):
    @abc.abstractmethod
    def send_email(self, source: str, recipients: list[str], subject: str, body: str):
        pass


class MailgunProvider(EmailProvider):
    def __init__(self, domain: str = None, api_key: str = None):
        self.domain = domain or os.getenv("MAILGUN_DOMAIN")
        self.api_key = api_key or os.getenv("MAILGUN_API_KEY")

    def send_email(self, source: str, recipients: list[str], subject: str, body: str):
        requests.post(
            f"https://api.mailgun.net/v3/{self.domain}/messages",
            auth=("api", self.api_key),
            data={
                "from": source,
                "to": recipients,
                "subject": subject,
                "html": body,
            },
        )


class AWSESProvider(EmailProvider):
    def __init__(self, region_name: str = "us-west-2"):
        self.client = boto3.client("ses", region_name=region_name)

    def send_email(self, source: str, recipients: List[str], subject: str, body: str):
        self.client.send_email(
            Source=source,
            Destination={"ToAddresses": recipients},
            Message={"Subject": {"Data": subject}, "Body": {"Html": {"Data": body}}},
        )


class EmailSender:
    def __init__(
        self,
        provider: EmailProvider = None,
        templates_dir: str | None = None,
    ):
        if provider is None:
            if os.getenv("MAILGUN_DOMAIN") and os.getenv("MAILGUN_API_KEY"):
                provider = MailgunProvider()
            elif os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
                provider = AWSESProvider()
            else:
                raise ValueError("No email provider configured")

        self.provider = provider

        # Update the templates directory to use an absolute path
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.templates_dir = templates_dir or os.path.join(base_path, "templates")

        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    @staticmethod
    def _apply_base_styling(body: str) -> str:
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background-color: #f4f4f4;
                    color: #333;
                    line-height: 1.6;
                }}
                .email-content {{
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 5px;
                    max-width: 600px;
                    margin: 0 auto;
                }}
            </style>
        </head>
        <body>
            <div class="email-content">
                {body}
            </div>
        </body>
        </html>
        """

    def send_email(
        self,
        source: str,
        recipients: List[str],
        subject: str,
        template_name: Optional[str] = None,
        context: Optional[dict] = None,
        body: Optional[str] = None,
        styled: bool = True,
    ):
        if not template_name and not body:
            raise ValueError("Either a template_name or a body must be provided")

        if template_name and context is not None:
            body = self._render_template(template_name, context)

        if styled:
            body = self._apply_base_styling(body)

        self.provider.send_email(source, recipients, subject, body)

    def _render_template(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(context)


# Usage example:
if __name__ == "__main__":
    # For Mailgun
    mailgun_provider = MailgunProvider(
        domain=os.getenv("MAILGUN_DOMAIN"), api_key=os.getenv("MAILGUN_API_KEY")
    )
    mailgun_sender = EmailSender(provider=mailgun_provider)

    # For AWS SES
    ses_provider = AWSESProvider(region_name="us-west-2")
    ses_sender = EmailSender(provider=ses_provider)

    # Using Mailgun
    mailgun_sender.send_email(
        source="sender@example.com",
        recipients=["recipient@example.com"],
        subject="Test Email",
        body="This is a test email sent using Mailgun.",
    )

    # Using AWS SES
    ses_sender.send_email(
        source="sender@example.com",
        recipients=["recipient@example.com"],
        subject="Test Email",
        body="This is a test email sent using AWS SES.",
    )
