import re
import logging
from config import client, RESPONSE_MODEL
from graph.state import EmailState

logger = logging.getLogger(__name__)

PROMPT = """You are a professional email assistant. Draft a polite, concise reply.

Original email summary: {summary}
Sender: {sender}
Recipient name (person you are replying to): {recipient_name}
Subject: {subject}
Category: {category}

Sign off the email with the name: {user_name}

Write only the reply body. Do not include subject line or metadata."""


def _parse_recipient_name(sender: str) -> str:
    match = re.match(r'^"?([^"<]+)"?\s*<', sender)
    if match:
        return match.group(1).strip().split()[0]
    return "there"


def _draft_reply(email: dict, user_name: str) -> str:
    prompt = PROMPT.format(
        summary=email.get("summary", ""),
        sender=email["sender"],
        recipient_name=_parse_recipient_name(email["sender"]),
        subject=email["subject"],
        category=email["category"],
        user_name=user_name,
    )
    response = client.chat.completions.create(
        model=RESPONSE_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def response_node(state: EmailState) -> EmailState:
    email = state["current_email"]
    try:
        email["draft_reply"] = _draft_reply(email, state["user_name"])
    except Exception as e:
        logger.warning(f"Response agent error: {e}")
        email["draft_reply"] = ""

    logger.info(f"Draft reply generated for {email['email_id']}")
    return state
