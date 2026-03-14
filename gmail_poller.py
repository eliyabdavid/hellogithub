"""Gmail polling integration for reading guest messages."""

import base64
import os
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# The 4 Gmail accounts to monitor (configure via environment or config file)
GMAIL_ACCOUNTS = [
    os.getenv("GMAIL_ACCOUNT_1", ""),
    os.getenv("GMAIL_ACCOUNT_2", ""),
    os.getenv("GMAIL_ACCOUNT_3", ""),
    os.getenv("GMAIL_ACCOUNT_4", ""),
]


def get_gmail_service(token_path: str, credentials_path: str = "gmail_credentials.json"):
    """Build and return a Gmail API service for a given account token."""
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def decode_message_body(payload: dict) -> str:
    """Decode a Gmail message payload body to plain text."""
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return body


def fetch_unread_messages(service, account_email: str) -> list[dict]:
    """
    Fetch unread messages from Gmail for the given account.

    Returns a list of dicts with keys: message_id, subject, sender, body, source_email.
    """
    messages_out = []
    result = service.users().messages().list(
        userId="me", labelIds=["UNREAD", "INBOX"], maxResults=50
    ).execute()

    message_ids = [m["id"] for m in result.get("messages", [])]

    for msg_id in message_ids:
        msg = service.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        body = decode_message_body(msg["payload"])

        messages_out.append({
            "message_id": msg_id,
            "subject": headers.get("Subject", ""),
            "sender": headers.get("From", ""),
            "body": body.strip(),
            "source_email": account_email,
        })

    return messages_out


def get_all_unread_messages() -> list[dict]:
    """
    Poll all configured Gmail accounts and return unread guest messages.

    Each account needs a corresponding token file: token_1.json, token_2.json, etc.
    """
    all_messages = []
    for idx, account_email in enumerate(GMAIL_ACCOUNTS, start=1):
        if not account_email:
            continue
        token_path = f"token_{idx}.json"
        try:
            service = get_gmail_service(token_path)
            messages = fetch_unread_messages(service, account_email)
            all_messages.extend(messages)
        except Exception as exc:
            print(f"[WARN] Could not fetch messages for account {account_email}: {exc}")

    return all_messages
