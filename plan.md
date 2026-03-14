# Email AI Assistant — Engineering Plan
> Multi-agent email processing pipeline using LangGraph + OpenRouter + Gmail API

---

## 1. Project Overview

A local-first, multi-agent email assistant that ingests Gmail messages, classifies them, summarizes content, drafts replies, and supports human-in-the-loop review before saving to Gmail Drafts. Triggered manually via CLI. Orchestrated as a LangGraph `StateGraph` with conditional routing between agents.

**Runtime flow summary:**
```
python main.py --fetch 10
```
Fetches up to N unread emails, runs each through the full graph pipeline sequentially, logs results, and saves approved drafts to Gmail.

---

## 2. Repository Structure

```
email-agent/
├── main.py                  # Entry point
├── config.py                # API keys, constants, env loading
├── graph/
│   ├── __init__.py
│   ├── state.py             # EmailState TypedDict definition
│   └── graph.py             # Conditional edge logic + StateGraph assembly + compilation
├── agents/
│   ├── __init__.py
│   ├── filter_agent.py      # Classification agent
│   ├── summarize_agent.py   # Summarization agent
│   └── response_agent.py    # Draft response agent
├── tools/
│   ├── __init__.py
│   ├── gmail_reader.py      # Fetch emails via Gmail API
│   └── gmail_sender.py      # Send/create drafts via Gmail API
├── human_review/
│   ├── __init__.py
│   └── review_cli.py        # CLI interface for human review
├── prompts/
│   ├── filter_prompt.txt
│   ├── summarize_prompt.txt
│   └── response_prompt.txt
├── logs/
│   └── app.log
├── credentials/
│   └── .gitkeep             # Store OAuth credentials here (gitignored)
├── .env                     # API keys (gitignored)
├── .gitignore
├── requirements.txt
└── plan.md
```

---

## 3. Shared State Schema

```python
# graph/state.py
from typing import TypedDict, Optional, Literal

class EmailState(TypedDict):
    # Ingestion
    email_id: str
    sender: str
    subject: str
    body: str
    received_at: str

    # Filter Agent output
    category: Optional[Literal["action-required", "informational", "promotional", "spam"]]

    # Summarize Agent output
    summary: Optional[str]

    # Response Agent output
    draft_reply: Optional[str]

    # Human Review
    human_approved: Optional[bool]
    edited_reply: Optional[str]

    # Control flow
    skip_response: bool       # True for spam/promotional
    send_status: Optional[str]

    # Logging / metadata
    processing_log: list[str]
```

---

## 4. Agent Designs

### 4.1 Filter Agent
- **Input**: `subject`, `body`, `sender`
- **Output**: `category`
- **Model**: OpenRouter (fast/cheap — e.g. `mistralai/mistral-7b-instruct`)
- **Logic**: Structured output prompt asking for one of 4 categories + brief reason. Parse JSON response.
- **Prompt template** (`prompts/filter_prompt.txt`):
  ```
  Classify the following email into exactly one category:
  - action-required
  - informational
  - promotional
  - spam

  Respond in JSON: {"category": "...", "reason": "..."}

  Subject: {subject}
  Body: {body}
  ```

### 4.2 Summarize Agent
- **Input**: `body`, `category`
- **Output**: `summary` (2–3 sentences)
- **Model**: OpenRouter (e.g. `mistralai/mistral-7b-instruct` or `openai/gpt-4o-mini`)
- **Skip condition**: category is `spam` — return empty summary, log skip.
- **Prompt template** (`prompts/summarize_prompt.txt`):
  ```
  Summarize the following email in 2-3 sentences. Be concise and factual.

  Email: {body}
  ```

### 4.3 Response Agent
- **Input**: `subject`, `summary`, `sender`, `category`
- **Output**: `draft_reply`
- **Model**: OpenRouter (better model recommended — e.g. `openai/gpt-4o-mini` or `anthropic/claude-haiku`)
- **Skip condition**: category is `spam` or `promotional` — set `skip_response = True`.
- **Prompt template** (`prompts/response_prompt.txt`):
  ```
  You are a professional email assistant. Draft a polite, concise reply.

  Original email summary: {summary}
  Sender: {sender}
  Subject: {subject}
  Category: {category}

  Write only the reply body. Do not include subject line or metadata.
  ```

---

## 5. LangGraph State Graph

### 5.1 Nodes

| Node Name        | Function                          |
| ---------------- | --------------------------------- |
| `ingest`         | Fetch email from Gmail API        |
| `filter`         | Classify email category           |
| `summarize`      | Generate 2–3 sentence summary     |
| `generate_reply` | Draft response                    |
| `human_review`   | CLI prompt for review/edit        |
| `send_email`     | Send approved draft via Gmail API |
| `skip`           | Log and exit for spam/promo       |

### 5.2 Graph Topology

```
ingest
  └──► filter
          ├── [spam / promotional] ──────────────────────────────► skip (END)
          ├── [informational] ──► summarize ──────────────────────► END (summary logged, no reply)
          └── [action-required]
                  └──► summarize
                            └──► generate_reply
                                      └──► human_review
                                                ├── [approved] ──► save_draft ──► END
                                                └── [rejected / edited] ──► generate_reply (retry)
```

### 5.3 Conditional Edge Logic + Graph Builder (`graph/graph.py`)

```python
from langgraph.graph import StateGraph, END
from graph.state import EmailState
from agents.filter_agent import filter_node
from agents.summarize_agent import summarize_node
from agents.response_agent import response_node
from human_review.review_cli import human_review_node
from tools.gmail_sender import save_draft_node
from graph.state import skip_node

# --- Conditional edge functions ---

def route_after_filter(state: EmailState) -> str:
    if state["category"] in ("spam", "promotional"):
        return "skip"
    return "summarize"  # both informational and action-required go to summarize

def route_after_summarize(state: EmailState) -> str:
    if state["category"] == "informational":
        return END  # summary only, no reply needed
    return "generate_reply"

def route_after_review(state: EmailState) -> str:
    if state["human_approved"]:
        return "save_draft"
    return "generate_reply"  # regenerate on rejection

# --- Graph assembly ---

def build_graph():
    g = StateGraph(EmailState)

    g.add_node("ingest", ingest_node)
    g.add_node("filter", filter_node)
    g.add_node("summarize", summarize_node)
    g.add_node("generate_reply", response_node)
    g.add_node("human_review", human_review_node)
    g.add_node("save_draft", save_draft_node)
    g.add_node("skip", skip_node)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "filter")
    g.add_conditional_edges("filter", route_after_filter)
    g.add_conditional_edges("summarize", route_after_summarize)
    g.add_edge("generate_reply", "human_review")
    g.add_conditional_edges("human_review", route_after_review)
    g.add_edge("save_draft", END)
    g.add_edge("skip", END)

    return g.compile()
```

---

## 6. Gmail API Integration

### 6.1 Setup
1. Enable Gmail API at [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials → download `credentials.json` → place in `credentials/`
3. Required scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.compose`

### 6.2 Reader (`tools/gmail_reader.py`)
- Authenticate with `google-auth-oauthlib`
- List unread messages from INBOX (configurable max count via `config.py`)
- Decode `payload.parts` for email body (handle both `text/plain` and `text/html`)
- Return structured dict matching `EmailState` fields

### 6.3 Draft Saver (`tools/gmail_sender.py`)
- Compose MIME message from `edited_reply` (or `draft_reply` if not edited)
- Use `users.drafts.create` — always saves to Gmail Drafts folder, never sends automatically
- Log the resulting draft ID for traceability
- User sends manually from Gmail if they choose to

---

## 7. OpenRouter LLM Integration

```python
# config.py
from openai import OpenAI  # OpenRouter is OpenAI-compatible

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)
```

Recommended model routing per agent:

| Agent     | Model                           | Reason                     |
| --------- | ------------------------------- | -------------------------- |
| Filter    | `mistralai/mistral-7b-instruct` | Fast, cheap classification |
| Summarize | `mistralai/mistral-7b-instruct` | Adequate for summarization |
| Response  | `openai/gpt-4o-mini`            | Better tone/quality        |

Override all models via `.env` for flexibility.

---

## 8. Human Review (CLI)

```python
# human_review/review_cli.py
def human_review_node(state: EmailState) -> EmailState:
    print(f"\n--- DRAFT REPLY ---\n{state['draft_reply']}\n")
    choice = input("[A]pprove / [E]dit / [R]eject? ").strip().lower()

    if choice == "a":
        state["human_approved"] = True
    elif choice == "e":
        state["edited_reply"] = input("Enter your edited reply:\n")
        state["human_approved"] = True
    else:  # reject → triggers regeneration
        state["human_approved"] = False

    return state
```

---

## 9. Logging

```python
# config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
```

Log at each node: email ID, category decision, summary length, draft generation, human action, send status.

---

## 10. Environment & Dependencies

### `.env`
```
OPENROUTER_API_KEY=sk-or-...
GMAIL_MAX_FETCH=10
DEFAULT_FILTER_MODEL=mistralai/mistral-7b-instruct
DEFAULT_RESPONSE_MODEL=openai/gpt-4o-mini
```

### Entry Point (`main.py`)

```python
# main.py
import argparse
from tools.gmail_reader import fetch_emails
from graph.graph_builder import build_graph

def main():
    parser = argparse.ArgumentParser(description="Email AI Assistant")
    parser.add_argument("--fetch", type=int, default=10, help="Number of emails to process")
    args = parser.parse_args()

    graph = build_graph()
    emails = fetch_emails(max_results=args.fetch)

    for email in emails:
        print(f"\nProcessing: {email['subject']}")
        result = graph.invoke(email)
        print(f"  → Category: {result['category']} | Status: {result['send_status']}")

if __name__ == "__main__":
    main()
```


```
langgraph>=0.2
langchain-core>=0.3
openai>=1.0           # OpenRouter uses OpenAI-compatible client
google-api-python-client
google-auth-oauthlib
google-auth-httplib2
python-dotenv
```

---

## 11. Build Order (Recommended)

| Phase | Task                                          |
| ----- | --------------------------------------------- |
| 1     | Gmail OAuth setup + `gmail_reader.py`         |
| 2     | `config.py` + OpenRouter client + `.env`      |
| 3     | `state.py` + `graph_builder.py` skeleton      |
| 4     | `filter_agent.py` + unit test with mock email |
| 5     | `summarize_agent.py`                          |
| 6     | `response_agent.py`                           |
| 7     | `human_review/review_cli.py`                  |
| 8     | `gmail_sender.py` (draft mode first)          |
| 9     | Wire full graph + conditional edges           |
| 10    | End-to-end test + logging validation          |

---

## 12. Key Risks & Mitigations

| Risk                                | Mitigation                                                              |
| ----------------------------------- | ----------------------------------------------------------------------- |
| Gmail OAuth token expiry            | Store + refresh `token.json` automatically                              |
| LLM returns malformed JSON (filter) | Wrap in try/except, fallback to `"informational"`                       |
| Accidental email sends              | Default to draft mode; require explicit config flag to enable live send |
| Rate limits (OpenRouter)            | Add retry with exponential backoff                                      |
| Email body encoding issues          | Handle `base64url` decode + charset normalization in reader             |