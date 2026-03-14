"""Airbnb guest assistant powered by Claude."""

import os
import anthropic
from global_faq import GLOBAL_FAQ, COMPLAINT_KEYWORDS


def fetch_apartment_info(sheet_link: str, email_account: str) -> dict:
    """Fetch apartment info from Google Sheets (optional)."""
    if not sheet_link:
        return {}
    try:
        from sheets_client import fetch_apartment_info as _fetch
        return _fetch(sheet_link, email_account)
    except Exception:
        return {}


def build_system_prompt(apartment_info: dict) -> str:
    """Build the system prompt with apartment-specific information."""
    apartment_section = ""
    if apartment_info:
        apartment_section = f"""
## Apartment Information
- **Name/Property**: {apartment_info.get('name', 'N/A')}
- **Address**: {apartment_info.get('address', 'N/A')}
- **WiFi Network**: {apartment_info.get('wifi_name', 'N/A')}
- **WiFi Password**: {apartment_info.get('wifi_password', 'N/A')}
- **Check-in Instructions**: {apartment_info.get('check_in', 'N/A')}
- **Check-out Instructions**: {apartment_info.get('check_out', 'N/A')}
- **Parking**: {apartment_info.get('parking', 'N/A')}
- **Appliance Instructions**: {apartment_info.get('appliance_instructions', 'N/A')}
- **Additional Notes**: {apartment_info.get('notes', 'N/A')}
"""
    else:
        apartment_section = "\n## Apartment Information\nNo specific apartment information available for this account.\n"

    faq_section = "\n## Global FAQ (applies to all properties)\n"
    for key, faq in GLOBAL_FAQ.items():
        faq_section += f"- **{key.replace('_', ' ').title()}**: {faq['answer']}\n"

    return f"""You are a friendly and professional Airbnb guest assistant.

Your role is to help guests with questions about their stay. Follow these rules:

1. Answer questions politely, clearly, and briefly in a natural tone.
2. Use the apartment-specific information below when answering property-specific questions.
3. Use the Global FAQ for questions that apply to all properties.
4. If you are unsure about something, respond exactly with: "I will check this for you and get back to you."
5. CRITICAL: If the guest is reporting a complaint, a problem, damage, malfunction, or any urgent issue with the property, respond ONLY with the exact text: ALERT_HOST
6. Do NOT add any explanation or apology when responding ALERT_HOST — just output that exact text.
{apartment_section}
{faq_section}"""


def is_complaint(message: str) -> bool:
    """Quick pre-check: does the message contain complaint keywords?"""
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in COMPLAINT_KEYWORDS)


def process_guest_message(
    guest_message: str,
    source_email: str,
    sheet_link: str = "",
) -> str:
    """
    Process a guest message and return an appropriate response.

    Returns:
        - "ALERT_HOST" if the message is a complaint or urgent issue
        - A polite reply otherwise
    """
    # Fast path: keyword-based complaint detection before calling the API
    if is_complaint(guest_message):
        return "ALERT_HOST"

    # Fetch apartment info from Google Sheets
    apartment_info = fetch_apartment_info(sheet_link, source_email)

    # Build prompt and call Claude
    system_prompt = build_system_prompt(apartment_info)

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "enabled", "budget_tokens": 1024},
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Source email account: {source_email}\n\n"
                    f"Guest message:\n{guest_message}"
                ),
            }
        ],
    )

    reply = next(
        (block.text for block in response.content if block.type == "text"), ""
    ).strip()

    # Final safety check: if Claude determined it's a complaint, honour that
    if reply.upper() == "ALERT_HOST":
        return "ALERT_HOST"

    return reply
