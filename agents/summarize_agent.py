import logging
from config import client, FILTER_MODEL
from graph.state import EmailState

logger = logging.getLogger(__name__)

PROMPT = """Summarize the following email in 2-3 sentences. Be concise and factual.

Email: {body}"""


def summarize_node(state: EmailState) -> EmailState:
    for email in state["emails"]:
        if email["category"] in ("spam", "promotional"):
            email["summary"] = None
            continue

        prompt = PROMPT.format(body=email["body"])
        try:
            response = client.chat.completions.create(
                model=FILTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            email["summary"] = response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Summarize error for {email['email_id']}: {e}")
            email["summary"] = ""

        logger.info(f"Email {email['email_id']} summarized")

    return state
