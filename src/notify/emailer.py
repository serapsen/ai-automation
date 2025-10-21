import os
import smtplib
import mimetypes
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.utils.logger import get_logger

logger = get_logger("notify.emailer")


def _split_list(val: Optional[str]) -> List[str]:
    if not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


def render_email_template(template_name: str, context: dict) -> Optional[str]:
    try:
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
            enable_async=False,
        )
        tpl = env.get_template(template_name)
        return tpl.render(**context)
    except Exception as e:
        logger.error("email template render failed: %s", e)
        return None


def send_email(subject: str, body_text: str, to_addrs: Optional[List[str]] = None, cc_addrs: Optional[List[str]] = None, body_html: Optional[str] = None, attachments: Optional[list] = None) -> bool:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_addr = os.getenv("SMTP_FROM")
    if to_addrs is None:
        to_addrs = _split_list(os.getenv("SMTP_TO"))
    if cc_addrs is None:
        cc_addrs = _split_list(os.getenv("SMTP_CC"))

    if not host or not from_addr or not to_addrs:
        logger.info("SMTP not configured (missing host/from/to); skipping email send")
        return False

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    if cc_addrs:
        msg["Cc"] = ", ".join(cc_addrs)

    has_inline = any(bool(getattr(a, "get", None) and a.get("cid")) or (isinstance(a, dict) and a.get("cid")) for a in (attachments or []))

    if has_inline:
        related = MIMEMultipart("related")
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body_text or "", "plain", _charset="utf-8"))
        if body_html:
            alt.attach(MIMEText(body_html, "html", _charset="utf-8"))
        related.attach(alt)
        msg.attach(related)
        inline_parent = related
    else:
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body_text or "", "plain", _charset="utf-8"))
        if body_html:
            alt.attach(MIMEText(body_html, "html", _charset="utf-8"))
        msg.attach(alt)
        inline_parent = msg

    for att in (attachments or []):
        if not isinstance(att, dict):
            continue
        path = att.get("path")
        if not path or not os.path.isfile(path):
            continue
        mime = att.get("mime")
        cid = att.get("cid")
        if not mime:
            mime, _ = mimetypes.guess_type(path)
        main_type, sub_type = (mime.split("/", 1) if mime else ("application", "octet-stream"))
        with open(path, "rb") as fp:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(fp.read())
            encoders.encode_base64(part)
        filename = os.path.basename(path)
        part.add_header("Content-Disposition", f"attachment; filename=\"{filename}\"")
        if cid:
            part.add_header("Content-ID", f"<{cid}>")
            inline_parent.attach(part)
        else:
            msg.attach(part)

    recipients = list(dict.fromkeys((to_addrs or []) + (cc_addrs or [])))

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            if os.getenv("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes"): 
                try:
                    server.starttls()
                    server.ehlo()
                except Exception:
                    pass
            if user and password:
                server.login(user, password)
            server.sendmail(from_addr, recipients, msg.as_string())
        logger.info("email sent to %s (cc=%s)", ", ".join(to_addrs), ", ".join(cc_addrs or []))
        return True
    except Exception as e:
        logger.error("email send failed: %s", e)
        return False
