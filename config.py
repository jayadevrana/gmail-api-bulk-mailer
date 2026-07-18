"""Configuration constants for the bulk mailer."""
from pathlib import Path
import os

# OAuth scope required for sending mail via Gmail API
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

BASE_DIR = Path(__file__).resolve().parent
TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"
LOG_DIR = BASE_DIR / "logs"
DEFAULT_DATA_PATH = BASE_DIR / "emails.csv"
DEFAULT_TEMPLATE_PATH = BASE_DIR / "email_template.txt"
DEFAULT_HTML_TEMPLATE_PATH = BASE_DIR / "email_template.html"
DEFAULT_DELAY_SECONDS = float(os.getenv("BULK_MAILER_DELAY", 1.0))
MAX_RETRIES = int(os.getenv("BULK_MAILER_MAX_RETRIES", 3))
BACKOFF_FACTOR = float(os.getenv("BULK_MAILER_BACKOFF", 2.0))
REQUEST_TIMEOUT = int(os.getenv("BULK_MAILER_TIMEOUT", 30))

# Used for resume logic: we read success.log to skip already-sent addresses
SUCCESS_LOG_PATH = LOG_DIR / "success.log"
ERROR_LOG_PATH = LOG_DIR / "error.log"

# Tracking pixel default (set to False to avoid surprises)
DEFAULT_TRACKING_PIXEL = False

# Maximum rows allowed to avoid accidental blasts; set to 0 to disable guard
MAX_RECIPIENTS_GUARD = int(os.getenv("BULK_MAILER_MAX_RECIPIENTS", 0))
