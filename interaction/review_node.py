import logging
from graph.state import EmailState

logger = logging.getLogger(__name__)


def human_review_node(state: EmailState) -> EmailState:
    from agents.response_agent import _draft_reply

    email = state["current_email"]

    while True:
        print(f"\n--- DRAFT REPLY ---\n{email['draft_reply']}\n")
        choice = input("[A]pprove / [E]dit / [R]eject (regenerate)? ").strip().lower()

        if choice == "a":
            email["human_approved"] = True
            logger.info(f"Human review for {email['email_id']}: approved")
            return state
        elif choice == "e":
            email["edited_reply"] = input("Enter your edited reply:\n")
            email["human_approved"] = True
            logger.info(f"Human review for {email['email_id']}: edited")
            return state
        else:
            print("Regenerating draft...")
            logger.info(f"Human review for {email['email_id']}: rejected, regenerating")
            try:
                email["draft_reply"] = _draft_reply(email, state["user_name"])
            except Exception as e:
                logger.warning(f"Regeneration error: {e}")
