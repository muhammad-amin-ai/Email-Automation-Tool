"""
Dynamic email personalization engine.

Responsible for:
  1. Building the variable context for a given (user, contact) pair —
     including graceful, multi-step fallbacks so a variable is *always*
     resolvable even when the underlying profile/contact data is thin.
  2. Rendering `{{ variable }}` tokens in a subject/body into real values.
  3. Normalizing loose, AI- or human-written `[bracket]` placeholders onto
     the same `{{variable}}` system, via both exact phrasing and fuzzy
     keyword matching.
  4. Validating that no unresolved placeholders remain before an email is
     allowed to send.

This intentionally stays a plain string-substitution engine (no Jinja/etc.)
to match the existing `_replace_variables` behaviour in campaign_service and
keep the change minimal and dependency-free.
"""
import html
import re
from datetime import datetime
from typing import Dict, List, Optional

from app.core.config import settings
from app.models.contact import Contact
from app.models.user import User

# Variables that MUST resolve to a non-empty value before we allow a send.
# (Most other variables now have safe fallback defaults baked into
# build_context, so this set stays intentionally small.)
REQUIRED_VARIABLES = {"recipient_name"}

_VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
_UNRESOLVED_BRACE_PATTERN = re.compile(r"\{\{\s*[a-zA-Z0-9_]*\s*\}\}")
_UNRESOLVED_BRACKET_PATTERN = re.compile(r"\[\s*[^\[\]{}]{0,120}?\s*\]")

# Context keys whose values are pre-built, already-safe HTML fragments
# (e.g. contain literal "<br>" tags). render() must NOT html-escape these —
# they're escaped piece-by-piece when assembled in build_context() instead.
_RAW_HTML_KEYS = {"contact_block"}

# ---------------------------------------------------------------------------
# 1. Legacy / exact bracket placeholders
# ---------------------------------------------------------------------------
# Older, hand-written templates (or a model that ignores instructions) may
# contain static "[bracket]" placeholders. These get mapped onto the same
# {{variable}} tokens so such templates keep working without manual edits.
_LEGACY_PLACEHOLDER_MAP = {
    r"\[\s*(?:recipient|subscriber|customer)'?s?\s+(?:full\s+)?name\s*\]": "{{recipient_name}}",
    r"\[\s*first\s*name\s*\]": "{{first_name}}",
    r"\[\s*last\s*name\s*\]": "{{last_name}}",
    r"\[\s*date\s*\]": "{{date}}",
    r"\[\s*(?:today'?s?\s+date|current\s+date)\s*\]": "{{date}}",
    r"\[\s*insert (?:a )?link or button to view\s*\]": "{{subscription_url}}",
    r"\[\s*insert\s+(?:your\s+)?contact\s+(?:information|info|details)(?:\s+here)?\s*\]": "{{contact_block}}",
    r"\[\s*your\s+name\s*\]": "{{sender_name}}",
    r"\[\s*your\s+(?:position|title|role|designation)\s*\]": "{{sender_title}}",
    r"\[\s*your\s+company(?:'s)?\s*(?:\/\s*agency)?\s*(?:name)?\s*\]": "{{company_name}}",
    r"\[\s*your\s+email(?:\s+address)?\s*\]": "{{sender_email}}",
    r"\[\s*your\s+phone(?:\s+number)?\s*\]": "{{sender_phone}}",
    # Common AI-generated / generic bracket placeholders
    r"\[\s*company\s*(?:\/\s*agency)?\s*name\s*\]": "{{company_name}}",
    r"\[\s*(?:company|agency|organi[sz]ation)\s*\]": "{{company_name}}",
    r"\[\s*contact\s+(?:information|info|details)(?:\s+here)?\s*\]": "{{contact_block}}",
    r"\[\s*contact\s+(?:number|phone)\s*\]": "{{sender_phone}}",
    r"\[\s*(?:email|email\s+address)\s*\]": "{{sender_email}}",
    r"\[\s*website\s*(?:url|address|link)?\s*\]": "{{website_url}}",
    r"\[\s*(?:phone|phone\s+number|telephone)\s*\]": "{{sender_phone}}",
    r"\[\s*(?:sender|from)\s+name\s*\]": "{{sender_name}}",
    r"\[\s*(?:position|title|role|designation)\s*\]": "{{sender_title}}",
    r"\[\s*name\s*\]": "{{sender_name}}",
    r"\[\s*unsubscribe\s*(?:link|url)?\s*\]": "{{subscription_url}}",
    r"\[\s*(?:manage|update)\s+(?:my\s+)?(?:subscription|preferences)\s*\]": "{{subscription_url}}",
    r"\[\s*(?:subscription|plan)\s*(?:plan|name)?\s*\]": "{{subscription_plan}}",
    r"\[\s*billing\s*cycle\s*\]": "{{billing_cycle}}",
}

# Any `{{variable}}` name the engine actually knows how to resolve (kept in
# sync with build_context's keys). If the model writes the raw variable name
# inside brackets (e.g. "[subscription_url]", "[company_name]") instead of
# the double-curly form, we recognize it directly.
_KNOWN_VARIABLE_NAMES = {
    "recipient_name", "first_name", "last_name", "email", "full_name",
    "sender_name", "sender_title", "company_name", "sender_phone",
    "sender_email", "subscription_plan", "billing_cycle",
    "subscription_status", "subscription_url", "website_url", "date",
    "contact_block",
}

# ---------------------------------------------------------------------------
# 2. Fuzzy keyword fallback
# ---------------------------------------------------------------------------
# For bracket text that survives the exact-pattern pass above (i.e. the
# model phrased it differently than anything we anticipated), look for a
# keyword anywhere inside it and map to the closest known variable. Order
# matters — more specific / multi-word keywords are checked before looser
# single-word ones so e.g. "contact information" doesn't get caught by a
# generic "name" rule first.
_FUZZY_KEYWORD_MAP = [
    (("contact info", "contact information", "contact details"), "{{contact_block}}"),
    (("subscription url", "subscription link", "subscription details",
      "view subscription", "manage subscription", "manage preferences",
      "billing url", "billing link", "update payment"), "{{subscription_url}}"),
    (("unsubscribe",), "{{subscription_url}}"),
    (("plan name", "subscription plan", "your plan"), "{{subscription_plan}}"),
    (("billing cycle", "billing frequency"), "{{billing_cycle}}"),
    (("company", "agency", "organisation", "organization", "business name"), "{{company_name}}"),
    (("phone", "telephone", "mobile", "contact number"), "{{sender_phone}}"),
    (("email address", "email"), "{{sender_email}}"),
    (("position", "title", "role", "designation"), "{{sender_title}}"),
    (("first name",), "{{first_name}}"),
    (("last name",), "{{last_name}}"),
    (("recipient", "subscriber", "customer name", "customer"), "{{recipient_name}}"),
    (("your name", "sender name", "from name"), "{{sender_name}}"),
    (("date",), "{{date}}"),
    (("website",), "{{website_url}}"),
]


def _fuzzy_bracket_replacement(bracket_text: str) -> Optional[str]:
    """Best-effort mapping for a `[...]` placeholder the exact pattern map
    didn't catch. Returns a `{{variable}}` string, or None if nothing
    reasonably matches (left as-is, still caught later by
    find_unresolved_placeholders so it never silently disappears)."""
    inner = bracket_text.strip("[] \t\r\n")
    if not inner:
        return None

    # Raw variable name in brackets, e.g. "[subscription_url]", "[Company_Name]"
    normalized_key = re.sub(r"[^a-z0-9]+", "_", inner.lower()).strip("_")
    if normalized_key in _KNOWN_VARIABLE_NAMES:
        return "{{" + normalized_key + "}}"

    lowered = inner.lower()
    for keywords, replacement in _FUZZY_KEYWORD_MAP:
        if any(keyword in lowered for keyword in keywords):
            return replacement
    return None


def migrate_legacy_placeholders(text: str) -> str:
    """Rewrite known static `[bracket]` placeholders to `{{variables}}`.

    Two passes:
      1. Exact known phrasings (`_LEGACY_PLACEHOLDER_MAP`) for backward
         compatibility with older hand-written templates.
      2. A fuzzy keyword fallback for anything phrased differently (e.g.
         "[Insert Contact Information Here]", "[Company/Agency Name]",
         "[subscription_url]") — these get mapped by keyword rather than
         exact wording, so wording drift from an AI writer doesn't cause a
         failed send.

    Bracket text with no recognizable keyword at all (e.g. a literal
    person's name someone typed in brackets) is left untouched — it will
    still be caught by find_unresolved_placeholders() so it never sends
    silently with a leftover placeholder.
    """
    if not text:
        return text
    result = text
    for pattern, replacement in _LEGACY_PLACEHOLDER_MAP.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    def _fuzzy_replace(match: "re.Match") -> str:
        replacement = _fuzzy_bracket_replacement(match.group(0))
        return replacement if replacement is not None else match.group(0)

    result = _UNRESOLVED_BRACKET_PATTERN.sub(_fuzzy_replace, result)
    return result


# ---------------------------------------------------------------------------
# 3. Context building — every value has a graceful fallback chain so a
#    variable is (almost) never truly empty.
# ---------------------------------------------------------------------------
def _derive_name_from_email(email: Optional[str]) -> str:
    """Last-resort recipient name: turn 'ahmed.khan99@x.com' into 'Ahmed
    Khan'. Used only when the contact has no first/last name on file."""
    if not email or "@" not in email:
        return ""
    local = email.split("@", 1)[0]
    local = re.sub(r"[._\-+0-9]+", " ", local).strip()
    if not local:
        return ""
    return " ".join(part.capitalize() for part in local.split() if part)


def _first_non_empty(*values: Optional[str]) -> str:
    for v in values:
        if v and str(v).strip():
            return str(v).strip()
    return ""


# ---------------------------------------------------------------------------
# Placeholder-value guard
# ---------------------------------------------------------------------------
# Extra safety net: even *real* config data (a .env value, a user's saved
# profile field) can accidentally be leftover placeholder/example text
# rather than a genuine value — e.g. a duplicated .env key silently
# overriding the real one with "Your Company", or a copy-pasted starter
# value like "+1234567890" / "yourwebsite.com" that never got edited. If
# such a value slipped through, it would otherwise render as a normal,
# "resolved" variable and get emailed straight to a real customer without
# ever tripping find_unresolved_placeholders(). To catch that, any value
# that matches one of these known filler patterns is treated as if it were
# never set, so the fallback chain continues to the next tier instead.
_PLACEHOLDER_TEXT_PATTERNS = [
    r"^your\s+(company|company'?s?\s+name|business|agency|organi[sz]ation)$",
    r"^(company|business|agency)\s+name$",
    r"^your\s+name$",
    r"^your\s+(title|position|role|designation)$",
    r"^your\s+(phone|phone\s+number|telephone)$",
    r"^your\s+email(\s+address)?$",
    r"^(n/?a|tbd|todo|xxx+|placeholder|sample|example|test)$",
    r"^example\.(com|org|net)$",
    r"^test@example\.(com|org|net)$",
]
_PLACEHOLDER_URL_SNIPPETS = ("yourwebsite.", "example.com", "yourcompany.", "yoursite.")
_PLACEHOLDER_PHONE_PATTERN = re.compile(r"^\+?1?[\s\-]?2345?6?7?8?9?0?$")


def _looks_like_placeholder(value: str) -> bool:
    """True if `value` looks like leftover template/example filler rather
    than real data someone actually entered."""
    if not value:
        return False
    normalized = value.strip().lower()
    for pattern in _PLACEHOLDER_TEXT_PATTERNS:
        if re.match(pattern, normalized):
            return True
    if any(snippet in normalized for snippet in _PLACEHOLDER_URL_SNIPPETS):
        return True
    digits_only = re.sub(r"[^\d]", "", value)
    if digits_only in {"1234567890", "0000000000", "1111111111"}:
        return True
    return False


def _first_real_value(*values: Optional[str]) -> str:
    """Like _first_non_empty, but also skips values that look like
    leftover placeholder/example text (see _looks_like_placeholder)."""
    for v in values:
        if v and str(v).strip() and not _looks_like_placeholder(str(v)):
            return str(v).strip()
    return ""


def _build_contact_block(
    sender_name: str, sender_title: str, company_name: str,
    sender_phone: str, sender_email: str, escape_html: bool = True,
) -> str:
    """Assemble a 'signature block' from whichever sender fields actually
    have a value — never leaves dangling commas/blank lines for fields the
    user hasn't filled in on their profile. Values are escaped individually
    here (not by render()) since the joined result contains literal <br>
    HTML that must NOT itself be escaped."""
    esc = (lambda s: html.escape(s)) if escape_html else (lambda s: s)
    lines = []
    if sender_name:
        lines.append(esc(sender_name))
    role_bits = ", ".join(esc(b) for b in (sender_title, company_name) if b)
    if role_bits:
        lines.append(role_bits)
    if sender_phone:
        lines.append(esc(sender_phone))
    if sender_email:
        lines.append(esc(sender_email))
    return "<br>".join(lines)


def build_context(
    user: User, contact: Contact, extra: Optional[Dict[str, str]] = None,
    escape_html: bool = True,
) -> Dict[str, str]:
    """Build the full variable -> value mapping for one recipient.

    Every field follows a fallback chain (contact/user data -> app-level
    default from settings -> a sensible generic default) so templates never
    end up sending with a blank name, blank sender line, etc.
    """
    # --- Recipient name: contact profile -> derived from email -> generic ---
    recipient_name = _first_non_empty(
        " ".join(filter(None, [contact.first_name, contact.last_name])).strip(),
        _derive_name_from_email(getattr(contact, "email", None)),
        "there",
    )

    # --- Sender identity: user profile -> app defaults -> generic fallback ---
    # (_first_real_value also skips leftover placeholder/example text, e.g.
    # a duplicated .env key or an unedited "[Your Company]"-style value.)
    sender_name = _first_real_value(
        user.sender_name, settings.DEFAULT_SENDER_NAME, "Our Team",
    )
    company_name = _first_real_value(
        user.company_name, settings.DEFAULT_COMPANY_NAME,
    )
    sender_title = _first_real_value(
        user.sender_title, settings.DEFAULT_SENDER_TITLE,
    )
    sender_phone = _first_real_value(
        user.sender_phone, settings.DEFAULT_SENDER_PHONE,
    )
    sender_email = _first_real_value(
        settings.DEFAULT_SENDER_EMAIL, user.email,
    )

    subscription_url = f"{settings.FRONTEND_URL.rstrip('/')}/subscription"

    context = {
        "recipient_name": recipient_name,
        "first_name": _first_non_empty(contact.first_name, recipient_name.split(" ")[0]),
        "last_name": contact.last_name or "",
        "email": contact.email or "",
        "full_name": recipient_name,
        "sender_name": sender_name,
        "sender_title": sender_title,
        "company_name": company_name,
        "sender_phone": sender_phone,
        "sender_email": sender_email,
        "subscription_plan": contact.subscription_plan or "",
        "billing_cycle": contact.subscription_billing_cycle or "",
        "subscription_status": contact.subscription_status or "",
        "subscription_url": subscription_url,
        "website_url": _first_real_value(
            getattr(user, "website_url", None), settings.DEFAULT_WEBSITE_URL
        ),
        "date": datetime.utcnow().strftime("%d %B %Y"),
    }
    # Computed signature block — built from the already-resolved fields
    # above so it's consistent with whatever {{sender_name}} etc. resolve to.
    context["contact_block"] = _build_contact_block(
        sender_name, sender_title, company_name, sender_phone, sender_email,
        escape_html=escape_html,
    )
    if extra:
        context.update({k: str(v) for k, v in extra.items()})
    return context


def render(text: str, context: Dict[str, str], escape_html: bool = True) -> str:
    """Replace `{{ variable }}` tokens in `text` with values from `context`.

    Unknown variables are left as-is (so validate() can catch them rather
    than silently dropping content). Values are HTML-escaped by default to
    prevent injection via contact/user-supplied data (name, company, etc.)
    — except keys in `_RAW_HTML_KEYS` (like `contact_block`), which are
    pre-built, already-escaped HTML fragments.
    """
    if not text:
        return text

    text = migrate_legacy_placeholders(text)

    def _replace(match: "re.Match") -> str:
        key = match.group(1)
        if key not in context:
            return match.group(0)
        value = context[key]
        if not escape_html or key in _RAW_HTML_KEYS:
            return value
        return html.escape(value)

    return _VAR_PATTERN.sub(_replace, text)


# ---------------------------------------------------------------------------
# 4. Plain-text -> HTML formatting for sending.
# ---------------------------------------------------------------------------
# Templates in this tool are authored as plain text (e.g. "Dear {{recipient_name}},
# \n\nBody text...\n\nBest regards,"). Sent as-is inside an HTML email, browsers/
# email clients collapse all whitespace/newlines into a single run-on paragraph
# (this is what produced the unformatted email in the field report). We detect
# whether the text already contains real HTML block markup and, if not, convert
# blank-line-separated paragraphs to <p> and single line breaks to <br>.
_HTML_BLOCK_TAG_PATTERN = re.compile(
    r"<(p|br|div|table|ul|ol|li|h[1-6])\b", re.IGNORECASE
)


def looks_like_html(text: str) -> bool:
    """True if `text` already contains real HTML block-level markup, meaning
    it should be left alone rather than re-formatted from plain text."""
    return bool(text) and bool(_HTML_BLOCK_TAG_PATTERN.search(text))


def plain_text_to_html(text: str) -> str:
    """Convert a plain-text email body (blank-line-separated paragraphs,
    single newlines within a paragraph) into HTML that preserves that
    formatting when rendered by an email client.

    No-op (returned unchanged) if `text` already looks like HTML, so
    hand-written HTML templates aren't double-wrapped or mangled.
    """
    if not text:
        return text
    if looks_like_html(text):
        return text

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"\n\s*\n", normalized.strip())
    html_paragraphs = [
        "<p>" + p.strip().replace("\n", "<br>") + "</p>"
        for p in paragraphs
        if p.strip()
    ]
    return "\n".join(html_paragraphs)


def find_unresolved_placeholders(text: str) -> List[str]:
    """Return any leftover `{{ ... }}` or `[ ... ]` placeholders in `text`."""
    if not text:
        return []
    found = set()
    found.update(_UNRESOLVED_BRACE_PATTERN.findall(text))
    found.update(_UNRESOLVED_BRACKET_PATTERN.findall(text))
    return sorted(found)


def render_and_validate(
    text: str, context: Dict[str, str], escape_html: bool = True
) -> str:
    """Render `text`, then raise if unresolved placeholders remain.

    Raises ValueError with a clear, actionable message — callers (e.g.
    campaign_service) should catch this and turn it into a failed job /
    BadRequestException rather than sending a half-rendered email.
    """
    rendered = render(text, context, escape_html=escape_html)
    unresolved = find_unresolved_placeholders(rendered)
    if unresolved:
        raise ValueError(
            "Email not sent: unresolved placeholder(s) remain: "
            + ", ".join(unresolved)
        )
    missing_required = [
        var for var in REQUIRED_VARIABLES if not context.get(var)
    ]
    if missing_required:
        raise ValueError(
            "Email not sent: required variable(s) missing: "
            + ", ".join(missing_required)
        )
    return rendered