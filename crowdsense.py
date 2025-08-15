import os
import requests
import tweepy
from dotenv import load_dotenv
from collections import deque
from datetime import datetime, timedelta

load_dotenv()

# Twitter API setup
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
client = tweepy.Client(bearer_token=bearer_token)

# Keywords & time window
KEYWORDS = ["earthquake", "flood", "landslide", "fire"]
TWEET_WINDOW_MIN = 5
THRESHOLD = 10  # tweets in time window to trigger alert

tweet_times = deque()

def fetch_tweets():
    global tweet_times
    for kw in KEYWORDS:
        query = f"{kw} -is:retweet lang:en"
        tweets = client.search_recent_tweets(query=query, max_results=10)
        if tweets.data:
            for t in tweets.data:
                tweet_times.append(datetime.utcnow())
                print(f"[{kw.upper()}] {t.text[:80]}...")
    # Remove old tweets from the deque
    cutoff = datetime.utcnow() - timedelta(minutes=TWEET_WINDOW_MIN)
    while tweet_times and tweet_times[0] < cutoff:
        tweet_times.popleft()

    # Trigger alert if threshold exceeded
    if len(tweet_times) >= THRESHOLD:
        print("🚨 ALERT: Possible disaster detected!")
        tweet_times.clear()

if __name__ == "__main__":
    while True:
        fetch_tweets()
