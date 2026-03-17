from config import client, FILTER_MODEL
from graph.state import EmailState

PROMPT = """Summarize this email in 1-2 sentences. Focus on: what is the main point of the email and any deadline or action needed.

Email: {body}"""


def summarize_node(state: EmailState) -> EmailState:
    for email in state["emails"]:
        if email["category"] in ("spam", "promotional"):
            email["summary"] = None
            continue

        prompt = PROMPT.format(body=email["body"])
        response = client.chat.completions.create(
            model=FILTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        email["summary"] = response.choices[0].message.content.strip()

    return state
