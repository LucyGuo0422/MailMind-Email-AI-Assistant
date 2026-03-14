import logging
from graph.state import EmailState

logger = logging.getLogger(__name__)

CATEGORY_LABEL = {
    "action-required": "[ACTION]",
    "informational":   "[INFO]  ",
    "promotional":     "[PROMO] ",
    "spam":            "[SPAM]  ",
}


def select_node(state: EmailState) -> EmailState:
    emails = state["emails"]

    print("\n" + "="*65)
    print(f"  {'#':<4} {'CATEGORY':<10}  SUBJECT")
    print("="*65)
    for i, email in enumerate(emails, start=1):
        label = CATEGORY_LABEL.get(email.get("category", ""), "[?]     ")
        print(f"  {i:<4} {label}  {email['subject'][:45]}")
        if email.get("summary"):
            print(f"        → {email['summary'][:80]}")
    print("="*65)

    while True:
        raw = input("\nWhich email do you want to reply to? (enter number): ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(emails)):
            print(f"Please enter a number between 1 and {len(emails)}.")
            continue

        selected = emails[int(raw) - 1]
        if selected["category"] in ("spam", "promotional"):
            print(f"That email is {selected['category']} — no reply needed. Pick another.")
            continue

        state["current_email"] = selected
        logger.info(f"User selected email {selected['email_id']} for reply")
        return state
