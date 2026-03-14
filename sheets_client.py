"""Google Sheets client for fetching apartment information."""

import os
from typing import Optional
import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_sheets_client() -> Optional[gspread.Client]:
    """Initialize and return a Google Sheets client."""
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    if not os.path.exists(credentials_path):
        return None
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    return gspread.authorize(creds)


def fetch_apartment_info(sheet_link: str, email_account: str) -> dict:
    """
    Fetch apartment info from Google Sheet based on the source email account.

    Returns a dict with apartment details or empty dict if unavailable.
    """
    client = get_sheets_client()
    if not client or not sheet_link:
        return {}

    try:
        sheet = client.open_by_url(sheet_link)
        worksheet = sheet.get_worksheet(0)
        records = worksheet.get_all_records()

        # Match apartment by email account
        for record in records:
            record_email = str(record.get("Email Account", "")).strip().lower()
            if record_email == email_account.strip().lower():
                return {
                    "name": record.get("Name", ""),
                    "address": record.get("Address", ""),
                    "wifi_name": record.get("WiFi Name", ""),
                    "wifi_password": record.get("WiFi Password", ""),
                    "check_in": record.get("Check-in Instructions", ""),
                    "check_out": record.get("Check-out Instructions", ""),
                    "parking": record.get("Parking", ""),
                    "appliance_instructions": record.get("Appliance Instructions", ""),
                    "notes": record.get("Notes", ""),
                    "email_account": record.get("Email Account", ""),
                }
    except Exception:
        pass

    return {}
