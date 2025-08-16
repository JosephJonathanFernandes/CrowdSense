import os
import requests
import time
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from twilio.rest import Client
import re

# from tweets_mock_generator import fetch_tweets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------- CONFIG ----------------
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

# disaster keywords to monitor with location context
DISASTER_KEYWORDS = [
    "earthquake",
    "flood", 
    "cyclone",
    "tsunami",
    "landslide",
    "fire",
    "storm",
]

# Location keywords to look for in tweets
LOCATION_KEYWORDS = [
    "city", "region", "state", "country", "area", "zone", 
    "district", "province", "county", "village", "town"
]

# thresholds & cooldown
WINDOW = timedelta(minutes=5)
THRESHOLD = 5
ALERT_COOLDOWN = timedelta(minutes=15)
API_RETRY_DELAY = 60  # seconds to wait after 429 error

# Use separate deques for each keyword to track individually
tweet_times = defaultdict(deque)
last_alert_time = defaultdict(lambda: None)
api_retry_time = None

# ---------------- TWILIO SETUP ----------------
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)


def send_sms_alert(message: str):
    """Send SMS using Twilio"""
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=MY_PHONE,
        )
        print(f"Message SID: {message.sid}")
        print(f"Status: {message.status}")
    except Exception as e:
        print(f"❌ SMS Failed: {e}")


# ---------------- NEWS CHECK ----------------
# ---------------- NEWS CHECK ----------------
def extract_location_from_tweets(tweets_data, keyword):
    """Extract location information from tweets"""
    locations = []
    for tweet in tweets_data:
        text = tweet.get('text', '').lower()
        
        # Look for common location patterns
        location_patterns = [
            r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "in California", "in New York"
            r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "at Mumbai", "at Tokyo"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:earthquake|flood|fire|storm)',  # "California earthquake"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            locations.extend(matches)
    
    # Return most common location
    if locations:
        from collections import Counter
        most_common = Counter(locations).most_common(1)
        return most_common[0][0] if most_common else None
    return None

def check_news(keyword, location=None):
    """Check related news with better query including location"""
    try:
        # Create a more specific query
        if location:
            query = f'"{keyword}" AND "{location}"'
            print(f"📰 Searching news for: {query}")
        else:
            query = f'"{keyword}" disaster OR emergency'
            print(f"📰 Searching news for: {query}")
            
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=3"
        res = requests.get(url).json()
        
        articles = res.get("articles", [])
        if articles:
            print(f"✅ Found {len(articles)} relevant news articles")
            # Filter articles that actually mention the keyword
            relevant_articles = []
            for article in articles:
                title_text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
                if keyword.lower() in title_text:
                    relevant_articles.append(article)
            return relevant_articles
        else:
            print("❌ No relevant news articles found")
            return []
            
    except Exception as e:
        print(f"❌ News API error: {e}")
        return []


# ---------------- TWITTER FETCH ----------------
def fetch_tweets():
    global last_alert_time
    print(f"🔍 Starting tweet fetch cycle at {datetime.utcnow().strftime('%H:%M:%S')}")

    for kw in DISASTER_KEYWORDS:
        print(f"📡 Searching for keyword: '{kw}'")
        url = f"https://api.x.com/2/tweets/search/recent?query={kw}&max_results=10"
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

        try:
            response = requests.get(url, headers=headers)
            print(f"🌐 API Response Status: {response.status_code}")
            response_data = response.json()

            if "data" in response_data:
                tweet_count = len(response_data["data"])
                print(f"✅ Found {tweet_count} tweets for '{kw}'")
                for tweet in response_data["data"]:
                    tweet_times.append(datetime.utcnow())
            else:
                print(f"❌ No tweets found for '{kw}' - Response: {response_data}")

        except Exception as e:
            print(f"🚨 Error fetching tweets for '{kw}': {e}")
            continue

        # Clean old tweets
        old_count = len(tweet_times)
        while tweet_times and datetime.utcnow() - tweet_times[0] > WINDOW:
            tweet_times.popleft()
        cleaned_count = old_count - len(tweet_times)
        if cleaned_count > 0:
            print(f"🧹 Cleaned {cleaned_count} old tweets from window")

        print(
            f"📊 Current tweet count in {WINDOW.total_seconds()/60:.0f}-min window: {len(tweet_times)}"
        )

        # Alert condition
        if len(tweet_times) >= THRESHOLD:
            print(f"⚠️  Threshold reached! ({len(tweet_times)} >= {THRESHOLD})")
            if (
                last_alert_time is None
                or datetime.utcnow() - last_alert_time > ALERT_COOLDOWN
            ):
                print("🚨 Triggering alert...")
                last_alert_time = datetime.utcnow()

                alert_msg = f"🚨 ALERT: Surge in '{kw}' tweets detected!"
                print(alert_msg)

                # Add related news links
                print("📰 Checking related news...")
                articles = check_news(kw)
                if articles:
                    print(f"✅ Found {len(articles)} related news articles")
                    news_links = "\n".join([a["url"] for a in articles])
                    alert_msg += f"\nTop News:\n{news_links}"
                else:
                    print("❌ No related news found")

                # Send SMS
                print("📱 Sending SMS alert...")
                send_sms_alert(alert_msg)

                # Reset window
                tweet_times.clear()
                print("🔄 Tweet window reset after alert")
            else:
                cooldown_remaining = ALERT_COOLDOWN - (
                    datetime.utcnow() - last_alert_time
                )
                print(
                    f"⏱️  Alert in cooldown. {cooldown_remaining.total_seconds()/60:.1f} minutes remaining"
                )
        else:
            print(f"✅ No alert needed ({len(tweet_times)} < {THRESHOLD})")

    print("=" * 50)


# ---------------- MAIN LOOP ----------------
if __name__ == "__main__":
    print("🌐 Real-Time Disaster Alert System Started...")
    while True:
        fetch_tweets()
        time.sleep(60)  # check every 1 minute
