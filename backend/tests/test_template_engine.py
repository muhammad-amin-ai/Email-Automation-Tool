import pytest

from app.core.config import settings
from app.services import template_engine
from app.models.user import User
from app.models.contact import Contact


def _make_user(**overrides) -> User:
    defaults = dict(
        email="abdullah@abddigital.com",
        sender_name="Abdullah Amin",
        sender_title="Director",
        company_name="ABD Digital Agency",
        sender_phone="0908797998",
    )
    defaults.update(overrides)
    return User(**defaults)


def _make_contact(**overrides) -> Contact:
    defaults = dict(
        email="ahmed@example.com",
        first_name="Ahmed",
        last_name=None,
        status="active",
        subscription_plan="Pro",
        subscription_billing_cycle="monthly",
        subscription_status="active",
    )
    defaults.update(overrides)
    return Contact(**defaults)


def test_build_context_fills_all_variables(monkeypatch):
    # DEFAULT_SENDER_EMAIL (from .env) intentionally overrides user.email in
    # build_context — clear it here so this test verifies the per-user
    # fallback path instead of whatever happens to be in the local .env.
    monkeypatch.setattr(settings, "DEFAULT_SENDER_EMAIL", "")

    context = template_engine.build_context(_make_user(), _make_contact())

    assert context["recipient_name"] == "Ahmed"
    assert context["sender_name"] == "Abdullah Amin"
    assert context["sender_title"] == "Director"
    assert context["company_name"] == "ABD Digital Agency"
    assert context["sender_phone"] == "0908797998"
    assert context["sender_email"] == "abdullah@abddigital.com"
    assert context["subscription_plan"] == "Pro"
    assert context["billing_cycle"] == "monthly"
    assert context["subscription_status"] == "active"
    assert context["subscription_url"].startswith("http")
    assert context["date"]  # non-empty, formatted date


def test_default_sender_email_overrides_user_email(monkeypatch):
    # When DEFAULT_SENDER_EMAIL is set in config/.env, it should win over
    # the logged-in user's own email (e.g. a dev/test login account).
    monkeypatch.setattr(settings, "DEFAULT_SENDER_EMAIL", "contact@company.com")
    context = template_engine.build_context(_make_user(), _make_contact())
    assert context["sender_email"] == "contact@company.com"


def test_recipient_name_falls_back_to_email_derived_name_when_missing():
    # No first/last name on file -> derive "Ahmed" from ahmed@example.com
    context = template_engine.build_context(
        _make_user(), _make_contact(first_name=None, last_name=None)
    )
    assert context["recipient_name"] == "Ahmed"


def test_recipient_name_falls_back_to_generic_when_nothing_available():
    # No name AND no usable email local-part -> generic fallback
    context = template_engine.build_context(
        _make_user(),
        _make_contact(first_name=None, last_name=None, email="123@example.com"),
    )
    assert context["recipient_name"] == "there"


def test_sender_name_falls_back_to_generic_when_profile_incomplete(monkeypatch):
    monkeypatch.setattr(settings, "DEFAULT_SENDER_NAME", "")
    context = template_engine.build_context(
        _make_user(sender_name=None), _make_contact()
    )
    assert context["sender_name"] == "Our Team"


def test_contact_block_omits_blank_fields_gracefully():
    context = template_engine.build_context(
        _make_user(sender_title=None, sender_phone=None), _make_contact()
    )
    block = context["contact_block"]
    assert "Abdullah Amin" in block
    assert "<br>" in block
    # No dangling ", " where title/phone would have been
    assert ",  " not in block and ", <br>" not in block


def test_ai_written_bracket_variants_are_migrated():
    # Exact wording an AI model wrote that the old exact-match map missed.
    text = (
        "Dear {{recipient_name}},\n"
        "Please visit our [subscription_url] to view your plan.\n"
        "Best regards,\n"
        "{{sender_name}} - {{sender_title}} - [Company/Agency Name]\n"
        "[Insert Contact Information Here]"
    )
    context = template_engine.build_context(_make_user(), _make_contact())
    rendered = template_engine.render_and_validate(text, context)
    assert template_engine.find_unresolved_placeholders(rendered) == []
    assert "ABD Digital Agency" in rendered


def test_placeholder_company_name_is_not_used(monkeypatch):
    # Regression: a duplicated .env key (or an unedited starter value) once
    # overrode the real DEFAULT_COMPANY_NAME with the literal text
    # "Your Company", which then got emailed to real customers. That filler
    # text must now be skipped, falling through to the next real value.
    monkeypatch.setattr(settings, "DEFAULT_COMPANY_NAME", "Your Company")
    context = template_engine.build_context(
        _make_user(company_name=None), _make_contact()
    )
    assert context["company_name"] != "Your Company"
    assert context["company_name"] == ""


def test_placeholder_phone_is_not_used(monkeypatch):
    monkeypatch.setattr(settings, "DEFAULT_SENDER_PHONE", "+1234567890")
    context = template_engine.build_context(
        _make_user(sender_phone=None), _make_contact()
    )
    assert context["sender_phone"] != "+1234567890"


def test_placeholder_website_url_is_not_used(monkeypatch):
    monkeypatch.setattr(settings, "DEFAULT_WEBSITE_URL", "https://yourwebsite.com")
    context = template_engine.build_context(_make_user(), _make_contact())
    assert "yourwebsite.com" not in context["website_url"]


def test_real_company_name_is_still_used(monkeypatch):
    # Make sure the placeholder guard doesn't accidentally reject genuine
    # business names that merely contain a common word.
    monkeypatch.setattr(settings, "DEFAULT_COMPANY_NAME", "")
    context = template_engine.build_context(
        _make_user(company_name="Company One Solutions"), _make_contact()
    )
    assert context["company_name"] == "Company One Solutions"


def test_render_replaces_known_variables():
    context = template_engine.build_context(_make_user(), _make_contact())
    text = "Dear {{recipient_name}}, your {{subscription_plan}} plan is active."
    rendered = template_engine.render(text, context)
    assert rendered == "Dear Ahmed, your Pro plan is active."


def test_render_escapes_html_by_default():
    context = template_engine.build_context(
        _make_user(), _make_contact(first_name="<script>alert(1)</script>")
    )
    rendered = template_engine.render("Hi {{recipient_name}}", context)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_legacy_bracket_placeholders_are_migrated():
    context = template_engine.build_context(_make_user(), _make_contact())
    text = (
        "Dear [Recipient's Name],\n"
        "Best regards,\n"
        "[insert your contact information]\n"
        "[Date]"
    )
    rendered = template_engine.render(text, context)
    assert "[Recipient's Name]" not in rendered
    assert "Ahmed" in rendered
    assert "Abdullah Amin" in rendered
    assert "[Date]" not in rendered


def test_find_unresolved_placeholders_detects_leftovers():
    text = "Hi {{recipient_name}}, contact us at [demo@example.com]"
    context = {"recipient_name": "Ahmed"}
    rendered = template_engine.render(text, context)
    unresolved = template_engine.find_unresolved_placeholders(rendered)
    assert "[demo@example.com]" in unresolved


def test_render_and_validate_raises_on_unresolved_variable():
    # sender_name intentionally missing from context -> stays unresolved
    context = {"recipient_name": "Ahmed"}
    text = "Dear {{recipient_name}}, from {{sender_name}}"
    with pytest.raises(ValueError, match="unresolved placeholder"):
        template_engine.render_and_validate(text, context)


def test_render_and_validate_raises_when_required_variable_missing():
    context = template_engine.build_context(_make_user(), _make_contact())
    context["recipient_name"] = ""  # simulate missing required data
    with pytest.raises(ValueError, match="required variable"):
        template_engine.render_and_validate("Hi {{recipient_name}}", context)


def test_render_and_validate_passes_for_fully_resolved_email():
    context = template_engine.build_context(_make_user(), _make_contact())
    text = (
        "Dear {{recipient_name}},<br>"
        "Your {{subscription_plan}} subscription has been successfully "
        "activated.<br>"
        "Best regards,<br>{{sender_name}}<br>{{sender_title}}, "
        "{{company_name}}<br>{{sender_phone}}<br>{{sender_email}}<br>{{date}}"
    )
    rendered = template_engine.render_and_validate(text, context)
    assert template_engine.find_unresolved_placeholders(rendered) == []
    assert "Ahmed" in rendered
    assert "Pro" in rendered