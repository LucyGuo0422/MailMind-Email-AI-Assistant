import json
import logging
from config import client, FILTER_MODEL
from graph.state import EmailState

logger = logging.getLogger(__name__)

PROMPT = """Classify the following email into exactly one category:
- action-required
- informational
- promotional
- spam

Respond in JSON: {{"category": "...", "reason": "..."}}

Sender: {sender}
Subject: {subject}
Body: {body}"""


def filter_node(state: EmailState) -> EmailState:
    for email in state["emails"]:
        prompt = PROMPT.format(
            subject=email["subject"],
            body=email["body"],
            sender=email["sender"],
        )
        try:
            response = client.chat.completions.create(
                model=FILTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw.strip())
            category = data["category"]
        except Exception as e:
            logger.warning(f"Filter error for {email['email_id']}: {e} — defaulting to informational")
            category = "informational"

        email["category"] = category
        logger.info(f"Email {email['email_id']} classified as {category}")

    return state
