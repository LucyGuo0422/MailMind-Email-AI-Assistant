from graph.state import EmailState


def human_review_node(state: EmailState) -> EmailState:
    from agents.response_agent import _draft_reply

    email = state["current_email"]

    while True:
        print(f"\n--- DRAFT REPLY ---\n{email['draft_reply']}\n")
        choice = input("[A]pprove / [E]dit / [R]eject (regenerate)? ").strip().lower()

        if choice == "a":
            email["human_approved"] = True
            return state
        elif choice == "e":
            email["edited_reply"] = input("Enter your edited reply:\n")
            email["human_approved"] = True
            return state
        else:
            print("Regenerating draft...")
            email["draft_reply"] = _draft_reply(email, state["user_name"])
