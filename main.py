"""
Airbnb Guest Assistant — Entry Point

Processes guest messages from Gmail accounts and returns
appropriate replies or ALERT_HOST for complaints/urgent issues.
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

from assistant import process_guest_message


load_dotenv()


def run_single(guest_message: str, source_email: str, sheet_link: str = "") -> str:
    """Process a single guest message and print the response."""
    response = process_guest_message(
        guest_message=guest_message,
        source_email=source_email,
        sheet_link=sheet_link,
    )
    return response


def run_from_gmail(sheet_link: str = "") -> None:
    """
    Poll all configured Gmail accounts, process unread messages, and print responses.

    Each response is printed as JSON: {message_id, source_email, response}.
    """
    from gmail_poller import get_all_unread_messages

    messages = get_all_unread_messages()
    if not messages:
        print("No unread messages found.")
        return

    for msg in messages:
        response = process_guest_message(
            guest_message=msg["body"],
            source_email=msg["source_email"],
            sheet_link=sheet_link,
        )
        result = {
            "message_id": msg["message_id"],
            "source_email": msg["source_email"],
            "sender": msg["sender"],
            "subject": msg["subject"],
            "response": response,
        }
        print(json.dumps(result, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Airbnb Guest Assistant — powered by Claude"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Single message mode
    single_parser = subparsers.add_parser(
        "reply", help="Process a single guest message"
    )
    single_parser.add_argument("--message", required=True, help="Guest message text")
    single_parser.add_argument(
        "--email", required=True, help="Source Gmail account (e.g. host1@gmail.com)"
    )
    single_parser.add_argument(
        "--sheet",
        default=os.getenv("SHEET_LINK", ""),
        help="Google Sheet URL with apartment info",
    )

    # Gmail polling mode
    poll_parser = subparsers.add_parser(
        "poll", help="Poll Gmail accounts for new guest messages"
    )
    poll_parser.add_argument(
        "--sheet",
        default=os.getenv("SHEET_LINK", ""),
        help="Google Sheet URL with apartment info",
    )

    args = parser.parse_args()

    if args.command == "reply":
        response = run_single(
            guest_message=args.message,
            source_email=args.email,
            sheet_link=args.sheet,
        )
        print(response)

    elif args.command == "poll":
        run_from_gmail(sheet_link=args.sheet)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
