import os
import requests
import time
from datetime import datetime, timedelta
from collections import deque
from twilio.rest import Client

# ---------------- CONFIG ----------------
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

# disaster keywords to monitor
DISASTER_KEYWORDS = ["earthquake", "flood", "cyclone", "tsunami", "landslide", "fire", "storm"]

# thresholds & cooldown
WINDOW = timedelta(minutes=5)
THRESHOLD = 5
ALERT_COOLDOWN = timedelta(minutes=15)

tweet_times = deque()
last_alert_time = None

# ---------------- TWILIO SETUP ----------------
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)

def send_sms_alert(message: str):
    """Send SMS using Twilio"""
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=MY_PHONE
        )
        print("✅ SMS Sent!")
    except Exception as e:
        print(f"❌ SMS Failed: {e}")

# ---------------- NEWS CHECK ----------------
def check_news(keyword):
    """Check related news to reduce false alarms"""
    try:
        url = f"https://newsapi.org/v2/everything?q={keyword}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        return res.get("articles", [])[:3]
    except:
        return []

# ---------------- TWITTER FETCH ----------------
def fetch_tweets():
    global last_alert_time
    for kw in DISASTER_KEYWORDS:
        url = f"https://api.twitter.com/2/tweets/search/recent?query={kw}&max_results=10"
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
        response = requests.get(url, headers=headers).json()

        if "data" in response:
            for tweet in response["data"]:
                tweet_times.append(datetime.utcnow())

        # Clean old tweets
        while tweet_times and datetime.utcnow() - tweet_times[0] > WINDOW:
            tweet_times.popleft()

        # Alert condition
        if len(tweet_times) >= THRESHOLD:
            if last_alert_time is None or datetime.utcnow() - last_alert_time > ALERT_COOLDOWN:
                last_alert_time = datetime.utcnow()

                alert_msg = f"🚨 ALERT: Surge in '{kw}' tweets detected!"
                print(alert_msg)

                # Add related news links
                articles = check_news(kw)
                if articles:
                    news_links = "\n".join([a["url"] for a in articles])
                    alert_msg += f"\nTop News:\n{news_links}"

                # Send SMS
                send_sms_alert(alert_msg)

                # Reset window
                tweet_times.clear()

# ---------------- MAIN LOOP ----------------
if __name__ == "__main__":
    print("🌐 Real-Time Disaster Alert System Started...")
    while True:
        fetch_tweets()
        time.sleep(60)  # check every 1 minute
