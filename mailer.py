"""Email creation and sending utilities."""
from __future__ import annotations

import base64
import logging
import mimetypes
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Iterable, Optional, Dict

from googleapiclient.errors import HttpError

from .config import MAX_RETRIES, BACKOFF_FACTOR, DEFAULT_DELAY_SECONDS
from .template_engine import inject_tracking_pixel

logger = logging.getLogger(__name__)


def build_message(
    sender: str,
    to: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachments: Optional[Iterable[Path]] = None,
    tracking_pixel: bool = False,
) -> Dict[str, str]:
    """Create a raw message ready for Gmail API."""
    if body_html and tracking_pixel:
        body_html = inject_tracking_pixel(body_html)

    if body_html:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body_text, "plain"))
        message.attach(MIMEText(body_html, "html"))
    else:
        message = MIMEMultipart()
        message.attach(MIMEText(body_text, "plain"))

    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    if attachments:
        for path in attachments:
            path = Path(path)
            if not path.exists():
                logger.warning("Attachment not found: %s", path)
                continue
            content_type, encoding = mimetypes.guess_type(path)
            if content_type is None or encoding is not None:
                content_type = "application/octet-stream"
            main_type, sub_type = content_type.split("/", 1)
            with path.open("rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=path.name)
            message.attach(part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_message(service, user_id: str, message_body: Dict[str, str], delay_seconds: float = DEFAULT_DELAY_SECONDS) -> bool:
    """Send message with retries and rate limiting. Returns True on success."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            service.users().messages().send(userId=user_id, body=message_body).execute()
            time.sleep(delay_seconds)
            return True
        except HttpError as err:
            status = getattr(err, "status_code", None) or getattr(getattr(err, "resp", None), "status", None)
            logger.warning("Attempt %s failed: %s", attempt, err)
            if status in (403, 429, 500, 503):
                sleep_for = delay_seconds * (BACKOFF_FACTOR ** (attempt - 1))
                time.sleep(sleep_for)
                continue
            return False
        except Exception as exc:  # noqa: BLE001
            logger.exception("Attempt %s failed due to unexpected error", attempt)
            sleep_for = delay_seconds * (BACKOFF_FACTOR ** (attempt - 1))
            time.sleep(sleep_for)
            continue
    return False
