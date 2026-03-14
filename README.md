# MailMind

A multi-agent email assistant built with LangGraph that reads your Gmail, classifies and summarizes emails using AI, and saves approved draft replies — without ever sending automatically.

## Features

- **Multi-agent pipeline** — separate agents for filtering, summarizing, and drafting replies
- **You choose what to reply to** — presents a summary of all fetched emails and lets you select one
- **Human-in-the-loop** — approve, edit, or regenerate every draft before it's saved
- **Draft-only mode** — never auto-sends; approved replies are saved to Gmail Drafts
- **Swappable models** — all LLMs configured via `.env`, routed through OpenRouter

## Overview

1. **Ingest** — fetches N unread emails from Gmail and extracts sender, subject, body, and date.
2. **Filter** — classifies each email into `action-required`, `informational`, `promotional`, or `spam` using an LLM.
3. **Summarize** — generates a 2–3 sentence summary for each non-spam/promo email using an LLM.
4. **Select** — displays all emails with their category and summary, and asks you to pick one to reply to.
5. **Generate Reply** — drafts a polite, concise reply for the selected email using an LLM.
6. **Human Review** — shows the draft and lets you approve, edit, or reject (regenerates until you approve).
7. **Save Draft** — saves the approved reply to your Gmail Drafts folder, never sends automatically.

---

## Architecture

```
filter → summarize → select → generate_reply → human_review → save_draft
```

| Stage | What happens |
|---|---|
| `filter` | Classifies all fetched emails (action-required / informational / promotional / spam) |
| `summarize` | Summarizes all non-spam/promo emails in 2–3 sentences |
| `select` | Displays the full list with categories and summaries; you pick one to reply to |
| `generate_reply` | AI drafts a reply for the selected email |
| `human_review` | You approve, edit, or reject (regenerates) until satisfied |
| `save_draft` | Saves the approved reply to Gmail Drafts |

### State

```python
class EmailState(TypedDict):
    emails: list[dict]    # all fetched emails, enriched by filter + summarize
    history: list[dict]   # emails that have been replied to this session
    current_email: dict   # the single email currently being drafted and reviewed
    user_name: str        # your name, used as the reply signature
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Fill in `.env` with your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-...
GMAIL_MAX_FETCH=10
DEFAULT_FILTER_MODEL=openai/gpt-4o-mini
DEFAULT_RESPONSE_MODEL=openai/gpt-4o-mini
```

### 3. Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and enable the Gmail API
2. Create OAuth 2.0 credentials (Desktop app) and download `credentials.json`
3. Place `credentials.json` in the `credentials/` directory
4. On first run, a browser window will open for OAuth authorization — the token is cached as `credentials/token.json`

Required OAuth scopes:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.compose`

## Usage

```bash
# Fetch 10 unread emails (default)
python main.py

# Fetch a specific number
python main.py --fetch 5
```

Example session:

```
Your name (used as email signature): Alex

Fetching 5 unread emails...

=================================================================
  #    CATEGORY    SUBJECT
=================================================================
  1    [ACTION]    Contract renewal — need your signature by Fri
        → John needs your signature on updated contract terms...
  2    [INFO]      This week in AI: GPT-5 rumors, open source...
        → A newsletter covering recent AI developments...
  3    [PROMO]     🔥 48-hour flash sale — 40% off everything!
  4    [SPAM]      URGENT: Confidential business proposal
=================================================================

Which email do you want to reply to? (enter number): 1

--- DRAFT REPLY ---
Hi John, thank you for the reminder...

[A]pprove / [E]dit / [R]eject (regenerate)?
```

- **A** — saves the draft to Gmail as-is
- **E** — lets you type your own reply before saving
- **R** — regenerates the draft (loops until you approve)

## Project Structure

```
MailMind/
├── main.py                  # Entry point
├── config.py                # API keys, model config, logging setup
├── test_pipeline.py         # Run the pipeline with test_emails.json (no Gmail needed)
├── test_emails.json         # Sample emails for local testing
├── graph/
│   ├── state.py             # EmailState TypedDict
│   └── graph.py             # LangGraph StateGraph
├── agents/                  # LLM-powered nodes (each contains its own prompt)
│   ├── filter_agent.py      # Classifies emails into 4 categories
│   ├── summarize_agent.py   # Generates 2–3 sentence summary
│   └── response_agent.py    # Drafts reply
├── interaction/             # Human-in-the-loop CLI nodes (no LLM)
│   ├── select_node.py       # Displays email list, captures user selection
│   └── review_node.py       # Approve / edit / reject draft
├── tools/
│   ├── gmail_reader.py      # OAuth + fetch unread emails
│   └── gmail_sender.py      # Save approved reply to Gmail Drafts
├── logs/                    # app.log output
└── credentials/             # OAuth credentials (gitignored)
```

## Models

| Agent | Model (via .env) | Purpose |
|---|---|---|
| Filter | `DEFAULT_FILTER_MODEL` | Classify email category |
| Summarize | `DEFAULT_FILTER_MODEL` | 2–3 sentence summary |
| Response | `DEFAULT_RESPONSE_MODEL` | Draft reply |

Prompts live directly in each agent file alongside the code that uses them.

## Logs

Pipeline activity is logged to `logs/app.log` and stdout, including email IDs, classification decisions, and draft IDs.
