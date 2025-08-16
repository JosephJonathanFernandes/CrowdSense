import os
from functools import lru_cache

from dotenv import load_dotenv
from twilio.rest import Client


# Load environment variables from a .env file if present
load_dotenv()


# Public configuration values
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")


def require(value: str, name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=1)
def get_twilio_client() -> Client:
    account_sid = require(TWILIO_SID, "TWILIO_SID")
    auth_token = require(TWILIO_AUTH_TOKEN, "TWILIO_AUTH_TOKEN")
    return Client(account_sid, auth_token)
