from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
from typing import List

# Support running as module or script
try:
    from .auth import get_gmail_service
    from .config import (
        DEFAULT_DATA_PATH,
        DEFAULT_TEMPLATE_PATH,
        DEFAULT_HTML_TEMPLATE_PATH,
        DEFAULT_DELAY_SECONDS,
        DEFAULT_TRACKING_PIXEL,
        MAX_RECIPIENTS_GUARD,
    )
    from .mailer import build_message, send_message
    from .template_engine import render_template
    from .utils import setup_logging, load_recipients, prompt_yes_no, load_sent_history
except ImportError:  # pragma: no cover
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.append(str(_Path(__file__).resolve().parent))
    from auth import get_gmail_service
    from config import (
        DEFAULT_DATA_PATH,
        DEFAULT_TEMPLATE_PATH,
        DEFAULT_HTML_TEMPLATE_PATH,
        DEFAULT_DELAY_SECONDS,
        DEFAULT_TRACKING_PIXEL,
        MAX_RECIPIENTS_GUARD,
    )
    from mailer import build_message, send_message
    from template_engine import render_template
    from utils import setup_logging, load_recipients, prompt_yes_no, load_sent_history

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Secure bulk Gmail sender (OAuth2)")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="CSV or JSON file with recipients")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH, help="Plain text template path")
    parser.add_argument("--html-template", type=Path, default=None, help="HTML template path (optional)")
    parser.add_argument("--subject", required=True, help="Email subject (supports {{placeholders}})")
    parser.add_argument("--attachments", type=Path, nargs="*", help="File attachments")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS, help="Delay between sends (seconds)")
    parser.add_argument("--dry-run", action="store_true", help="Render only, do not send")
    parser.add_argument("--tracking-pixel", action="store_true", default=DEFAULT_TRACKING_PIXEL, help="Append 1x1 tracking pixel to HTML body")
    parser.add_argument("--resume", action="store_true", help="Skip emails already logged as sent")
    return parser.parse_args()


def load_template(path: Path, fallback: str) -> str:
    if path and path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


def main() -> None:
    args = parse_args()
    setup_logging()

    recipients, invalid, duplicates = load_recipients(args.data)
    logger.info(
        "Loaded %s recipients (%s invalid, %s duplicates skipped)",
        len(recipients),
        len(invalid),
        len(duplicates),
    )

    if MAX_RECIPIENTS_GUARD and len(recipients) > MAX_RECIPIENTS_GUARD:
        logger.error("Recipient count %s exceeds guard %s; aborting.", len(recipients), MAX_RECIPIENTS_GUARD)
        sys.exit(1)

    sent_history = load_sent_history() if args.resume else set()
    if sent_history:
        before = len(recipients)
        recipients = [row for row in recipients if row.get("email") not in sent_history]
        logger.info("Resume enabled: skipping %s already-sent emails", before - len(recipients))

    if not recipients:
        logger.warning("No recipients to process after filtering; exiting.")
        return

    text_template = load_template(args.template, "Hi {{first_name}},\nThis is a sample message.\n")
    html_template = None
    if args.html_template:
        html_template = load_template(args.html_template, "")

    total = len(recipients)
    if not prompt_yes_no(f"You are about to send {total} emails. Continue?"):
        logger.info("User aborted.")
        return

    service = get_gmail_service()
    user_id = "me"

    sent = 0
    failed = 0
    skipped = len(invalid) + len(duplicates)

    for idx, row in enumerate(recipients, start=1):
        email = row.get("email")
        subject, missing_subject = render_template(args.subject, row)
        body_text, missing_text = render_template(text_template, row)
        body_html = None
        missing_html = set()
        if html_template:
            body_html, missing_html = render_template(html_template, row)

        for missing_key in (missing_subject | missing_text | missing_html):
            logger.warning("Missing placeholder '%s' for %s", missing_key, email)

        message_body = build_message(
            sender="me",
            to=email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            attachments=args.attachments,
            tracking_pixel=args.tracking_pixel,
        )

        if args.dry_run:
            logger.info("[Dry Run] Prepared message for %s", email)
            sent += 1
            continue

        success = send_message(service, user_id, message_body, delay_seconds=args.delay)
        if success:
            logger.info("SENT %s (%s/%s)", email, idx, total)
            sent += 1
        else:
            logger.error("FAILED %s (%s/%s)", email, idx, total)
            failed += 1

    logger.info("Summary -> Total Sent: %s | Failed: %s | Skipped: %s", sent, failed, skipped)


if __name__ == "__main__":
    main()
