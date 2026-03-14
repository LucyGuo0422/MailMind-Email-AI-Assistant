import base64
import logging
from email.mime.text import MIMEText
from tools.gmail_reader import _get_service
from graph.state import EmailState

logger = logging.getLogger(__name__)


def save_draft_node(state: EmailState) -> EmailState:
    email = state["current_email"]

    if not email.get("human_approved"):
        return state

    body = email.get("edited_reply") or email.get("draft_reply", "")
    service = _get_service()

    message = MIMEText(body)
    message["to"] = email["sender"]
    message["subject"] = f"Re: {email['subject']}"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()

    draft_id = draft.get("id", "unknown")
    email["send_status"] = f"draft_saved:{draft_id}"
    state["history"].append(email)
    logger.info(f"Draft saved for {email['email_id']}: {draft_id}")
    print(f"\nDraft saved to Gmail. (draft ID: {draft_id})")

    return state
