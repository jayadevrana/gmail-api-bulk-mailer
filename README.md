# Gmail API Bulk Mailer

Secure bulk email sender using the Gmail API with OAuth2 (no passwords) — personalized templates, CSV recipients, retries, and resume support, built for Python 3.11.

## Features

- OAuth2 Installed App flow — authorize once in the browser, no passwords or app-specific passwords stored.
- Personalized mail-merge with `{{placeholder}}` substitution across subject, plain-text, and HTML bodies.
- CSV or JSON recipient sources with automatic email validation and duplicate skipping.
- Plain-text and HTML multipart messages, plus optional file attachments.
- Automatic retries with exponential backoff and rate limiting on Gmail API errors (403/429/500/503).
- Resume mode that skips addresses already logged as sent, plus a recipient-count guard to prevent accidental blasts.
- Dry-run mode to render and preview messages without sending, with success/error logging.

## Stack

- Python 3.11+
- Gmail API via `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`
- `pandas` for recipient parsing, `python-dotenv` for configuration

## Getting started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create an OAuth client ID (Desktop app) in the Google Cloud Console, enable the Gmail API, and save the downloaded `credentials.json` into the project folder.
3. Prepare your recipients in `emails.csv` (must include an `email` column; any other columns become template placeholders).
4. Run it:
   ```bash
   python -m bulk_mailer.main --subject "Hello {{first_name}}"
   ```
   The first run opens a browser to authorize; a `token.json` is then saved for reuse.

Useful flags: `--html-template`, `--attachments`, `--delay`, `--dry-run`, `--resume`, `--tracking-pixel`.

## Notes

- `credentials.json` and `token.json` are secrets — they are gitignored and must never be committed.
- Always test with `--dry-run` before a real send, and respect Gmail sending limits and anti-spam / consent requirements for your recipients.

## Author

Built by [Jayadev Rana](https://jayadevrana.in) — @bluealgocapital · [YouTube](https://www.youtube.com/@jayadevrana3657) · [GitHub](https://github.com/jayadevrana)
