"""Email delivery via Resend.

Drop-in replacement for the old SMTP-based ``send_email``.  The public
function signatures are deliberately identical so every existing call site
(``admin/service.py``) keeps working without changes beyond the import path
(which hasn't changed — it's still ``app.core.email``).

New additions:
    * ``send_html_email`` — for rich HTML content.
    * ``send_template_email`` — renders a Jinja2 template from the
      ``email_templates/`` directory, then sends as HTML.

All sends are best-effort: a failure is logged and returns ``False``, never
raising into the caller.  This matches the original contract and ensures that
notification delivery can never block or crash the request it's attached to.
"""
import logging
from pathlib import Path
from typing import Optional

import resend
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from app.config import settings

logger = logging.getLogger("app.email")

# ---------------------------------------------------------------------------
# SDK initialisation
# ---------------------------------------------------------------------------

resend.api_key = settings.RESEND_API_KEY

# ---------------------------------------------------------------------------
# Template engine
# ---------------------------------------------------------------------------

_TEMPLATE_DIR = Path(__file__).resolve().parent / "email_templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send a plain-text email via Resend.

    Returns ``True`` on success, ``False`` on any failure.
    Signature is identical to the old SMTP version for backward compat.
    """
    try:
        params: resend.Emails.SendParams = {
            "from": settings.EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
        result = resend.Emails.send(params)
        logger.info("Email sent to %s (id=%s)", to_email, result.get("id") if isinstance(result, dict) else getattr(result, "id", "unknown"))
        return True
    except Exception:
        logger.exception("Failed to send email to %s via Resend", to_email)
        return False


def send_html_email(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
    """Send an HTML email via Resend.

    An optional plain-text fallback can be provided for clients that don't
    render HTML.
    """
    try:
        params: resend.Emails.SendParams = {
            "from": settings.EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        if text_body:
            params["text"] = text_body
        result = resend.Emails.send(params)
        logger.info("HTML email sent to %s (id=%s)", to_email, result.get("id") if isinstance(result, dict) else getattr(result, "id", "unknown"))
        return True
    except Exception:
        logger.exception("Failed to send HTML email to %s via Resend", to_email)
        return False


def send_template_email(to_email: str, template_name: str, context: dict, subject: Optional[str] = None) -> bool:
    """Render a Jinja2 template and send as HTML via Resend.

    Parameters
    ----------
    to_email:
        Recipient address.
    template_name:
        Filename inside ``email_templates/`` (e.g. ``"welcome.html"``).
    context:
        Template variables.  ``project_name`` is injected automatically.
    subject:
        Email subject line.  Falls back to ``context["subject"]`` or the
        template_name.
    """
    try:
        template = _jinja_env.get_template(template_name)
    except TemplateNotFound:
        logger.error("Email template '%s' not found in %s", template_name, _TEMPLATE_DIR)
        return False

    ctx = {"project_name": settings.PROJECT_NAME, **context}
    html_body = template.render(ctx)
    email_subject = subject or ctx.get("subject", template_name.replace(".html", "").replace("_", " ").title())

    return send_html_email(to_email, email_subject, html_body)
