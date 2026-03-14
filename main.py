import argparse
from tools.gmail_reader import fetch_emails
from graph.graph import build_graph


def main():
    parser = argparse.ArgumentParser(description="MailMind — Email AI Assistant")
    parser.add_argument("--fetch", type=int, default=10, help="Number of emails to fetch")
    args = parser.parse_args()

    user_name = input("Your name (used as email signature): ").strip()

    print(f"\nFetching {args.fetch} unread emails...")
    emails = fetch_emails(max_results=args.fetch)

    if not emails:
        print("No unread emails found.")
        return

    graph = build_graph()
    graph.invoke({
        "emails": emails,
        "history": [],
        "current_email": {},
        "user_name": user_name,
    })


if __name__ == "__main__":
    main()
