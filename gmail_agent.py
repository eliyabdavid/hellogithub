"""
Airbnb Guest Assistant — Fully Automated Gmail Agent

Runs in a loop:
1. Checks all Gmail inboxes for new guest messages
2. Generates AI replies using Claude
3. Sends replies automatically (or alerts the host for complaints)
4. Marks processed messages as read
"""

import os
import time
import base64
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from assistant import process_guest_message

# ── Configuration ────────────────────────────────────────────────────────────

SHEET_LINK = os.getenv("SHEET_LINK", "")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL", "60"))  # check every 60s
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")          # host email for ALERT_HOST notices
GMAIL_CREDENTIALS_FILE = "gmail_credentials.json"  # OAuth client credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Add Gmail accounts here: ("display name", "email@gmail.com")
ACCOUNTS = []
_raw = os.getenv("GMAIL_ACCOUNTS", "")
if _raw:
    for entry in _raw.split(","):
        parts = entry.strip().split("|")
        if len(parts) == 2:
            ACCOUNTS.append((parts[0].strip(), parts[1].strip()))
        elif len(parts) == 1 and parts[0]:
            ACCOUNTS.append(("Host", parts[0].strip()))

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Gmail helpers ─────────────────────────────────────────────────────────────

def get_service(account_email: str, token_file: str):
    """Authenticate and return a Gmail service for one account."""
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Missing {GMAIL_CREDENTIALS_FILE}. "
                    "Download it from Google Cloud Console → APIs & Services → Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, SCOPES)
            log.info(f"Opening browser to authorize: {account_email}")
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def decode_body(payload: dict) -> str:
    """Extract plain-text body from a Gmail message payload."""
    def _decode(data: str) -> str:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return _decode(data)
        # Fallback: first part
        data = payload["parts"][0].get("body", {}).get("data", "")
        return _decode(data) if data else ""
    else:
        data = payload.get("body", {}).get("data", "")
        return _decode(data) if data else ""


def get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch_unread(service) -> list[dict]:
    """Return list of unread inbox messages."""
    result = service.users().messages().list(
        userId="me", labelIds=["UNREAD", "INBOX"], maxResults=20
    ).execute()
    msgs = []
    for m in result.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=m["id"], format="full"
        ).execute()
        headers = msg["payload"].get("headers", [])
        msgs.append({
            "id": m["id"],
            "from": get_header(headers, "From"),
            "subject": get_header(headers, "Subject"),
            "body": decode_body(msg["payload"]).strip(),
            "thread_id": msg.get("threadId"),
        })
    return msgs


def send_reply(service, original: dict, reply_text: str, account_email: str):
    """Send a reply to a guest message."""
    msg = MIMEMultipart()
    msg["To"] = original["from"]
    msg["From"] = account_email
    msg["Subject"] = "Re: " + original["subject"]
    msg["In-Reply-To"] = original.get("message_id", "")
    msg["References"] = original.get("message_id", "")
    msg.attach(MIMEText(reply_text, "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": original["thread_id"]}
    ).execute()


def send_alert(service, original: dict, account_email: str):
    """Forward a complaint to the host's alert email."""
    target = ALERT_EMAIL or account_email
    msg = MIMEMultipart()
    msg["To"] = target
    msg["From"] = account_email
    msg["Subject"] = f"🚨 GUEST COMPLAINT — {original['subject']}"
    body = (
        f"A guest message requires your attention:\n\n"
        f"From: {original['from']}\n"
        f"Subject: {original['subject']}\n\n"
        f"Message:\n{original['body']}"
    )
    msg.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()


def mark_read(service, msg_id: str):
    """Mark a message as read."""
    service.users().messages().modify(
        userId="me", id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ── Main loop ─────────────────────────────────────────────────────────────────

def run():
    if not ACCOUNTS:
        log.error(
            "No Gmail accounts configured.\n"
            "Set GMAIL_ACCOUNTS in your .env file, e.g.:\n"
            "  GMAIL_ACCOUNTS=host1@gmail.com,host2@gmail.com"
        )
        return

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set. Add it to your .env file.")
        return

    log.info(f"Starting Airbnb Guest Assistant — monitoring {len(ACCOUNTS)} account(s)")
    log.info(f"Checking every {POLL_INTERVAL_SECONDS} seconds...")

    # Authenticate all accounts upfront
    services = {}
    for idx, (name, email) in enumerate(ACCOUNTS, start=1):
        token_file = f"token_{idx}.json"
        log.info(f"Authenticating: {email}")
        services[email] = (name, get_service(email, token_file))

    log.info("✅ All accounts authenticated. Agent is running.\n")

    while True:
        for account_email, (display_name, service) in services.items():
            try:
                messages = fetch_unread(service)
                if messages:
                    log.info(f"[{account_email}] {len(messages)} unread message(s)")

                for msg in messages:
                    log.info(f"  → From: {msg['from']} | Subject: {msg['subject']}")

                    # Skip emails sent by own monitored accounts (prevents forwarding loops)
                    sender = msg["from"].lower()
                    own_emails = [e.lower() for _, e in ACCOUNTS]
                    if any(e in sender for e in own_emails):
                        log.info("  ⏭ Skipping — sent by a monitored account (loop prevention)")
                        mark_read(service, msg["id"])
                        continue

                    # Skip already-forwarded complaint alerts
                    if msg["subject"].startswith("🚨 GUEST COMPLAINT"):
                        log.info("  ⏭ Skipping — already-forwarded complaint alert")
                        mark_read(service, msg["id"])
                        continue

                    response = process_guest_message(
                        guest_message=msg["body"],
                        source_email=account_email,
                        sheet_link=SHEET_LINK,
                    )

                    if response == "ALERT_HOST":
                        log.warning(f"  ⚠️  ALERT_HOST — forwarding complaint to host")
                        send_alert(service, msg, account_email)
                    else:
                        log.info(f"  ✉️  Sending reply...")
                        send_reply(service, msg, response, account_email)

                    mark_read(service, msg["id"])
                    log.info(f"  ✅ Done\n")

            except Exception as e:
                log.error(f"[{account_email}] Error: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
