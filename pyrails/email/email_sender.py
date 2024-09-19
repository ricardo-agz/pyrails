import importlib.util
import os
import abc
from pathlib import Path
import requests
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pyrails.logger import logger
import httpx


# Try to import boto3, set a flag if it fails
try:
    import boto3

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    import aioboto3

    AIOBOTO3_AVAILABLE = True
except ImportError:
    AIOBOTO3_AVAILABLE = False


class EmailProvider(abc.ABC):
    @abc.abstractmethod
    def send_email(self, source: str, recipients: List[str], subject: str, body: str):
        """
        Synchronously send an email.
        """
        pass

    @abc.abstractmethod
    async def send_email_async(
        self, source: str, recipients: List[str], subject: str, body: str
    ):
        """
        Asynchronously send an email.
        """
        pass


class MailgunProvider(EmailProvider):
    def __init__(self, domain: str = None, api_key: str = None):
        self.domain = domain or os.getenv("MAILGUN_DOMAIN")
        self.api_key = api_key or os.getenv("MAILGUN_API_KEY")

    def send_email(self, source: str, recipients: list[str], subject: str, body: str):
        response = requests.post(
            f"https://api.mailgun.net/v3/{self.domain}/messages",
            auth=("api", self.api_key),
            data={
                "from": source,
                "to": recipients,
                "subject": subject,
                "html": body,
            },
        )
        if response.status_code != 200:
            logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
            response.raise_for_status()
        logger.info(f"Email sent via Mailgun to {recipients} with subject '{subject}'.")

    async def send_email_async(
        self, source: str, recipients: List[str], subject: str, body: str
    ):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.mailgun.net/v3/{self.domain}/messages",
                auth=("api", self.api_key),
                data={
                    "from": source,
                    "to": recipients,
                    "subject": subject,
                    "html": body,
                },
            )
            if response.status_code != 200:
                logger.error(
                    f"Mailgun API async error: {response.status_code} - {response.text}"
                )
                response.raise_for_status()
            logger.info(
                f"Email sent via Mailgun (async) to {recipients} with subject '{subject}'."
            )


class AWSESProvider(EmailProvider):
    def __init__(self, region_name: str = "us-west-2"):
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for AWSESProvider but is not installed."
            )
        self.region_name = region_name
        self.client = boto3.client("ses", region_name=region_name)

    def send_email(self, source: str, recipients: List[str], subject: str, body: str):
        try:
            response = self.client.send_email(
                Source=source,
                Destination={"ToAddresses": recipients},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Data": body}},
                },
            )
            logger.info(
                f"Email sent via AWS SES to {recipients} with subject '{subject}'. Message ID: {response['MessageId']}"
            )
        except Exception as e:
            logger.error(f"AWS SES error: {e}")
            raise

    async def send_email_async(
        self, source: str, recipients: List[str], subject: str, body: str
    ):
        if not AIOBOTO3_AVAILABLE:
            raise ImportError(
                "aioboto3 is required for async AWSESProvider but is not installed."
            )
        session = aioboto3.Session()
        async with session.client("ses", region_name=self.region_name) as client:
            try:
                response = await client.send_email(
                    Source=source,
                    Destination={"ToAddresses": recipients},
                    Message={
                        "Subject": {"Data": subject},
                        "Body": {"Html": {"Data": body}},
                    },
                )
                logger.info(
                    f"Email sent via AWS SES (async) to {recipients} with subject '{subject}'. Message ID: {response['MessageId']}"
                )
            except Exception as e:
                logger.error(f"AWS SES async error: {e}")
                raise


def _get_application_root() -> Path:
    """
    Determines the root directory of the user's application.

    :return: Path object representing the application root.
    """
    try:
        # Attempt to get the path of the main module
        main_spec = importlib.util.find_spec("__main__")
        if main_spec and main_spec.origin:
            return Path(main_spec.origin).resolve().parent
    except Exception as e:
        logger.warning(f"Failed to determine application root: {e}")

    # Fallback to current working directory
    return Path.cwd()


class EmailSender:
    DEFAULT_TEMPLATES_SUBDIR = "templates/email"

    def __init__(
        self,
        provider: Optional[EmailProvider] = None,
        templates_dir: Optional[str] = None,
    ):
        """
        Initialize the EmailSender.

        :param provider: An instance of EmailProvider. If None, defaults to Mailgun or AWS SES based on environment variables.
        :param templates_dir: Optional path to the templates directory. If None, searches for 'templates/emails' in the application root.
        :raises ValueError: If no provider is configured or templates directory is not found.
        """
        self.provider = self._initialize_provider(provider)
        self.templates_dir = self._determine_templates_dir(templates_dir)
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    @staticmethod
    def _initialize_provider(provider: Optional[EmailProvider]) -> EmailProvider:
        if provider:
            logger.debug("Using provided EmailProvider.")
            return provider

        # Determine provider based on environment variables
        mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        if mailgun_domain and mailgun_api_key:
            logger.info("Configuring MailgunProvider based on environment variables.")
            return MailgunProvider()
        elif aws_access_key and aws_secret_key:
            logger.info("Configuring AWSESProvider based on environment variables.")
            return AWSESProvider()
        else:
            logger.error(
                "No email provider configured. Please set Mailgun or AWS SES environment variables."
            )
            raise ValueError(
                "No email provider configured. Please set Mailgun or AWS SES environment variables."
            )

    def _determine_templates_dir(self, templates_dir: Optional[str]) -> str:
        """
        Determine the templates directory using Path.cwd().
        """
        if templates_dir:
            resolved_dir = Path(templates_dir).resolve()
            if not resolved_dir.is_dir():
                logger.error(
                    f"The specified templates directory does not exist: {resolved_dir}"
                )
                raise FileNotFoundError(
                    f"The specified templates directory does not exist: {resolved_dir}"
                )
            logger.info(f"Using custom templates directory: {resolved_dir}")
            return str(resolved_dir)

        # Use the current working directory as the application root
        app_root = Path.cwd()
        default_templates_dir = app_root / self.DEFAULT_TEMPLATES_SUBDIR

        if default_templates_dir.is_dir():
            logger.info(f"Using default templates directory: {default_templates_dir}")
            return str(default_templates_dir)
        else:
            logger.error(
                f"Default templates directory '{default_templates_dir}' not found. "
                "Please ensure 'templates/email' exists in your application or specify a 'templates_dir'."
            )
            raise FileNotFoundError(
                f"Default templates directory '{default_templates_dir}' not found. "
                "Please ensure 'templates/email' exists in your application or specify a 'templates_dir'."
            )

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
        recipients: list[str],
        subject: str,
        template_name: Optional[str] = None,
        context: Optional[dict[str, any]] = None,
        body: Optional[str] = None,
        styled: bool = True,
    ):
        """
        Synchronously send an email.

        :param source: Sender's email address.
        :param recipients: List of recipient email addresses.
        :param subject: Subject of the email.
        :param template_name: Name of the Jinja2 template to render.
        :param context: Context dictionary for template rendering.
        :param body: Raw HTML body of the email. Overrides template if provided.
        :param styled: Whether to apply base styling to the email.
        :raises ValueError: If neither template_name nor body is provided.
        """
        if not template_name and not body:
            raise ValueError("Either a template_name or a body must be provided")

        if template_name:
            try:
                body = self._render_template(template_name, context or {})
            except TemplateNotFound:
                logger.error(
                    f"Template '{template_name}' not found in '{self.templates_dir}'."
                )
                raise
            except Exception as e:
                logger.error(f"Error rendering template '{template_name}': {e}")
                raise

        if styled:
            body = self._apply_base_styling(body)

        self.provider.send_email(source, recipients, subject, body)

    async def send_email_async(
        self,
        source: str,
        recipients: List[str],
        subject: str,
        template_name: Optional[str] = None,
        context: Optional[dict[str, any]] = None,
        body: Optional[str] = None,
        styled: bool = True,
    ):
        """
        Asynchronously send an email.

        :param source: Sender's email address.
        :param recipients: List of recipient email addresses.
        :param subject: Subject of the email.
        :param template_name: Name of the Jinja2 template to render.
        :param context: Context dictionary for template rendering.
        :param body: Raw HTML body of the email. Overrides template if provided.
        :param styled: Whether to apply base styling to the email.
        :raises ValueError: If neither template_name nor body is provided.
        """
        if not template_name and not body:
            raise ValueError("Either a template_name or a body must be provided")

        if template_name:
            try:
                body = self._render_template(template_name, context or {})
            except TemplateNotFound:
                logger.error(
                    f"Template '{template_name}' not found in '{self.templates_dir}'."
                )
                raise
            except Exception as e:
                logger.error(f"Error rendering template '{template_name}': {e}")
                raise

        if styled:
            body = self._apply_base_styling(body)

        await self.provider.send_email_async(source, recipients, subject, body)

    def _render_template(self, template_name: str, context: dict[str, any]) -> str:
        """
        Render a Jinja2 template with the given context.

        :param template_name: Name of the template file.
        :param context: Context dictionary for rendering.
        :return: Rendered HTML as a string.
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(context)
        except TemplateNotFound:
            logger.error(
                f"Template '{template_name}' not found in '{self.templates_dir}'."
            )
            raise
        except Exception as e:
            logger.error(f"Error rendering template '{template_name}': {e}")
            raise


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
