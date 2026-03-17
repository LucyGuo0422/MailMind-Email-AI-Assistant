import json
import logging
import argparse
from tools.gmail_reader import fetch_emails
from graph.graph import build_graph

logging.basicConfig(level=logging.WARNING)


def main():
    parser = argparse.ArgumentParser(description="MailMind — Email AI Assistant")
    parser.add_argument("--fetch", type=int, default=10, help="Number of emails to fetch")
    parser.add_argument("--test", action="store_true", help="Run with test_emails.json instead of Gmail")
    args = parser.parse_args()

    user_name = input("Your name (used as email signature): ").strip()

    if args.test:
        with open("test_emails.json") as f:
            emails = json.load(f)
    else:
        print(f"\nFetching {args.fetch} emails...")
        emails = fetch_emails(max_results=args.fetch)
        if not emails:
            print("No emails found.")
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
