# MailMind

A multi-agent email assistant built with LangGraph that reads your Gmail, classifies and summarizes emails using AI, and saves approved draft replies — without ever sending automatically.

## Features

- **Multi-agent pipeline** — separate agents for filtering, summarizing, and drafting replies
- **You choose what to reply to** — presents a summary of all fetched emails and lets you select one
- **Human-in-the-loop** — approve, edit, or regenerate every draft before it's saved
- **Draft-only mode** — never auto-sends; approved replies are saved to Gmail Drafts
- **Swappable models** — all LLMs configured via `.env`, routed through OpenRouter

## Architecture

```
filter → summarize → select → generate_reply → human_review → save_draft
```

| Stage | What happens |
|---|---|
| `filter` | Classifies all fetched emails into `action-required`, `informational`, `promotional`, or `spam` |
| `summarize` | Summarizes all non-spam/promo emails |
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
mkdir -p logs
```

### 2. Configure environment

Fill in `.env` with your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-...
GMAIL_MAX_FETCH=10
DEFAULT_FILTER_MODEL=mistralai/mistral-7b-instruct
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
# Fetch emails from Gmail (default 10)
python main.py

# Fetch a specific number
python main.py --fetch 5

# Run with local test emails (no Gmail needed)
python main.py --test
```

Example session:

```
Your name (used as email signature): Alex

Fetching 5 emails...

===========================================================================
  #    CATEGORY    SUBJECT                                        SENDER
===========================================================================
  1    [ACTION]    Contract renewal — need your signature by Fri  john.smith@acme.com
        → John needs your signature on updated contract terms by Friday EOD.
  2    [INFO]      This week in AI: GPT-5 rumors, open source...  newsletter@techdigest.io
        → A newsletter covering recent AI and open source developments.
  3    [PROMO]     🔥 48-hour flash sale — 40% off everything!    deals@shopify-store.com
  4    [SPAM]      URGENT: Confidential business proposal          nigerian.prince99@freemail.xyz
===========================================================================

Which email do you want to reply to? (enter number): 1

--- DRAFT REPLY ---
Hi John, thank you for the reminder...

[A]pprove / [E]dit / [R]eject (regenerate)?
```

- **A** — saves the draft to Gmail as-is
- **E** — lets you type your own reply before saving
- **R** — regenerates the draft (loops until you approve)

## Testing without Gmail

To run the pipeline without Gmail OAuth, use the `--test` flag. This loads emails from `test_emails.json` instead:

```bash
python main.py --test
```

`test_emails.json` contains four sample emails covering all categories (action-required, informational, promotional, spam). Edit the file to add your own test cases.

## Project Structure

```
MailMind/
├── main.py                  # Entry point
├── config.py                # API keys and model config
├── test_emails.json         # Sample emails for local testing
├── graph/
│   ├── state.py             # EmailState TypedDict
│   └── graph.py             # LangGraph StateGraph
├── agents/                  # LLM-powered nodes
│   ├── filter_agent.py      # Classifies emails into 4 categories
│   ├── summarize_agent.py   # Generates summary
│   └── response_agent.py    # Drafts reply
├── interaction/             # Human-in-the-loop CLI nodes
│   ├── select_node.py       # Displays email list, captures user selection
│   └── review_node.py       # Approve / edit / reject draft
├── tools/
│   ├── gmail_reader.py      # OAuth + fetch emails
│   └── gmail_sender.py      # Save approved reply to Gmail Drafts
├── credentials/             # OAuth credentials (gitignored)
└── logs/                    # Runtime logs (gitignored)
```

## Models

| Agent | Model (via .env) | Purpose |
|---|---|---|
| Filter | `DEFAULT_FILTER_MODEL` | Classify email category |
| Summarize | `DEFAULT_FILTER_MODEL` | Generate summary |
| Response | `DEFAULT_RESPONSE_MODEL` | Draft reply |

Prompts live directly in each agent file alongside the code that uses them.
