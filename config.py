import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

FILTER_MODEL = os.getenv("DEFAULT_FILTER_MODEL", "mistralai/mistral-7b-instruct")
RESPONSE_MODEL = os.getenv("DEFAULT_RESPONSE_MODEL", "openai/gpt-4o-mini")
GMAIL_MAX_FETCH = int(os.getenv("GMAIL_MAX_FETCH", "10"))

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler(),
    ],
)
