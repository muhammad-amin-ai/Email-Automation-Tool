import logging
import httpx
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException, BadRequestException


logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.email_from = settings.EMAIL_FROM
        self.email_from_name = settings.EMAIL_FROM_NAME
        self.base_url = "https://api.brevo.com/v3"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.email_from)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ServiceUnavailableException(
                "Email service is not configured. Please set BREVO_API_KEY and EMAIL_FROM."
            )

        if not to_email or not subject:
            raise BadRequestException("Recipient email and subject are required.")

        url = f"{self.base_url}/smtp/email"
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "accept": "application/json",
        }

        payload = {
            "sender": {"name": self.email_from_name, "email": self.email_from},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
        }
        if text_body:
            payload["textContent"] = text_body

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
        except httpx.ConnectError:
            raise ServiceUnavailableException("Could not connect to email provider.")
        except httpx.TimeoutException:
            raise ServiceUnavailableException("Email provider timed out.")
        except Exception as e:
            logger.error(f"Brevo connection error: {e}")
            raise ServiceUnavailableException("Email provider is unavailable.")

        if response.status_code in (200, 201, 202):
            try:
                data = response.json()
                return {"id": data.get("messageId"), "raw": data}
            except Exception:
                return {"id": None, "raw": {}}

        try:
            err = response.json()
            err_msg = err.get("message") or err.get("error") or "Email send failed"
        except Exception:
            err_msg = response.text or "Email send failed"

        logger.error(f"Brevo error {response.status_code}: {err_msg}")

        if response.status_code == 401:
            raise ServiceUnavailableException("Email provider rejected the API key.")
        if response.status_code == 400:
            raise BadRequestException(f"Invalid email payload: {err_msg}")

        raise ServiceUnavailableException(f"Email provider error: {err_msg}")


email_service = EmailService()