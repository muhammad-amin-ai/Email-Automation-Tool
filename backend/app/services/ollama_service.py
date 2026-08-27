import logging
import httpx
from typing import Optional

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableException, BadRequestException
from app.services import template_engine


logger = logging.getLogger(__name__)

# Instruction appended to every AI-drafting system prompt so the model
# outputs our actual template variables instead of ambiguous bracket text
# like "[Your Name]" or "[Subscriber's Name]" that can't be reliably
# auto-detected later. The model should leave these tokens EXACTLY as-is —
# they get resolved by app.services.template_engine right before sending.
VARIABLE_SYSTEM_INSTRUCTION = (
    "\n\nIMPORTANT — use these exact placeholder tokens wherever the "
    "corresponding info belongs, and do NOT invent bracket-style text like "
    "'[Your Name]' or '[Subscriber's Name]' instead:\n"
    "{{recipient_name}} - the recipient's name\n"
    "{{sender_name}} - the sender's name\n"
    "{{sender_title}} - the sender's job title\n"
    "{{company_name}} - the sender's company/agency name\n"
    "{{sender_phone}} - the sender's phone number\n"
    "{{sender_email}} - the sender's email address\n"
    "{{subscription_plan}} - the recipient's subscription plan name\n"
    "{{billing_cycle}} - the recipient's billing cycle\n"
    "{{subscription_status}} - the recipient's subscription status\n"
    "{{subscription_url}} - the link to view subscription details\n"
    "{{date}} - today's date\n"
    "Write these tokens literally, with the double curly braces, exactly as "
    "shown above — do not translate, rename, or reformat them."
)


class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    async def _call_ollama(self, prompt: str, system: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
        except httpx.ConnectError:
            raise ServiceUnavailableException(
                "AI service is not reachable. Please ensure Ollama is running."
            )
        except httpx.TimeoutException:
            raise ServiceUnavailableException("AI service timed out. Please try again.")
        except Exception as e:
            logger.error(f"Ollama connection error: {e}")
            raise ServiceUnavailableException("AI service is unavailable.")

        if response.status_code != 200:
            logger.error(
                f"Ollama returned status {response.status_code}: {response.text}"
            )
            if response.status_code == 404:
                raise ServiceUnavailableException(
                    f"AI model '{self.model}' not found. Please run: ollama pull {self.model}"
                )
            raise ServiceUnavailableException("AI service returned an error.")

        try:
            data = response.json()
            text = (data.get("response") or "").strip()
            if not text:
                raise BadRequestException("AI returned an empty response.")
            return text
        except BadRequestException:
            raise
        except Exception as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            raise ServiceUnavailableException("Invalid response from AI service.")

    async def generate_email(
        self,
        purpose: str,
        recipient: Optional[str] = None,
        tone: str = "professional",
        additional_instructions: Optional[str] = None,
    ) -> dict:
        system = (
            "You are an expert email copywriter. Create clear, engaging, and professional emails. "
            "Always return the email in a structured format with a SUBJECT line and BODY."
            + VARIABLE_SYSTEM_INSTRUCTION
        )
        parts = [f"Purpose: {purpose}"]
        if recipient:
            parts.append(f"Recipient: {recipient}")
        parts.append(f"Tone: {tone}")
        if additional_instructions:
            parts.append(f"Additional instructions: {additional_instructions}")

        parts.append(
            "\nReturn the response in this exact format:\n"
            "SUBJECT: <subject line>\n"
            "BODY:\n<email body content>"
        )
        prompt = "\n".join(parts)
        text = await self._call_ollama(prompt, system=system)
        result = self._parse_email_response(text)
        return self._normalize_variables(result)

    async def generate_subject(
        self, email_body: str, context: Optional[str] = None
    ) -> dict:
        system = (
            "You are an expert email marketing copywriter. "
            "Generate compelling email subject lines that improve open rates."
        )
        parts = [f"Email body:\n{email_body}"]
        if context:
            parts.append(f"Context: {context}")

        parts.append(
            "\nReturn 1 primary subject line and 2 alternatives in this exact format:\n"
            "PRIMARY: <primary subject>\n"
            "ALT1: <alternative 1>\n"
            "ALT2: <alternative 2>"
        )
        prompt = "\n".join(parts)
        text = await self._call_ollama(prompt, system=system)
        return self._parse_subject_response(text)

    async def personalize_email(
        self,
        template_subject: str,
        template_body: str,
        contact_first_name: Optional[str] = None,
        contact_last_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        extra_context: Optional[str] = None,
    ) -> dict:
        system = (
            "You are an email personalization assistant. "
            "Take a template email and personalize it for a specific recipient "
            "while preserving the original message and intent."
            + VARIABLE_SYSTEM_INSTRUCTION
        )

        parts = [
            f"Template subject: {template_subject}",
            f"Template body:\n{template_body}",
        ]
        if contact_first_name or contact_last_name:
            name = " ".join(filter(None, [contact_first_name, contact_last_name]))
            parts.append(f"Recipient name: {name}")
        if contact_email:
            parts.append(f"Recipient email: {contact_email}")
        if extra_context:
            parts.append(f"Extra context: {extra_context}")

        parts.append(
            "\nReturn the personalized email in this exact format:\n"
            "SUBJECT: <personalized subject>\n"
            "BODY:\n<personalized body>"
        )
        prompt = "\n".join(parts)
        text = await self._call_ollama(prompt, system=system)
        result = self._parse_email_response(text)
        return self._normalize_variables(result)

    @staticmethod
    def _normalize_variables(result: dict) -> dict:
        """Safety net: even though the system prompt instructs the model to
        use {{variable}} tokens, models occasionally still emit bracket-style
        text (e.g. "[Your Name]"). Run it through the same legacy-placeholder
        migration used for hand-written templates so known variants still
        resolve correctly at send time."""
        return {
            "subject": template_engine.migrate_legacy_placeholders(
                result.get("subject", "")
            ),
            "body": template_engine.migrate_legacy_placeholders(
                result.get("body", "")
            ),
        }

    @staticmethod
    def _parse_email_response(text: str) -> dict:
        subject = ""
        body_lines = []
        body_started = False

        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.upper().startswith("SUBJECT:"):
                subject = stripped[len("SUBJECT:"):].strip()
            elif stripped.upper().startswith("BODY:"):
                body_started = True
            elif body_started:
                body_lines.append(line)

        body = "\n".join(body_lines).strip()

        if not subject:
            for line in text.split("\n"):
                if line.strip():
                    subject = line.strip()
                    break
        if not body:
            body = text

        return {"subject": subject, "body": body}

    @staticmethod
    def _parse_subject_response(text: str) -> dict:
        subject = ""
        alternatives = []
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.upper().startswith("PRIMARY:"):
                subject = stripped[len("PRIMARY:"):].strip()
            elif stripped.upper().startswith("ALT"):
                colon = stripped.find(":")
                if colon != -1:
                    alternatives.append(stripped[colon + 1:].strip())

        if not subject and alternatives:
            subject = alternatives.pop(0)
        if not subject:
            subject = text.split("\n")[0].strip() if text else ""

        return {"subject": subject, "alternatives": alternatives}


ollama_service = OllamaService()