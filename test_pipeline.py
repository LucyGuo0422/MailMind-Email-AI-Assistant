import json
from graph.graph import build_graph


def main():
    with open("test_emails.json") as f:
        emails = json.load(f)

    user_name = input("Your name (used as email signature): ").strip()

    graph = build_graph()
    graph.invoke({
        "emails": emails,
        "history": [],
        "current_email": {},
        "user_name": user_name,
    })


if __name__ == "__main__":
    main()
