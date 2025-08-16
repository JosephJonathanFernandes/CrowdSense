import random
import time
from collections import deque
from datetime import datetime, timedelta

# Keywords & time window
KEYWORDS = ["earthquake", "flood", "landslide", "fire"]
TWEET_WINDOW_MIN = 5
THRESHOLD = 10  # tweets in time window to trigger alert

tweet_times = deque()

# Mock tweet generator
def generate_mock_tweets():
    # Randomly decide if tweets appear
    for _ in range(random.randint(0, 5)):
        kw = random.choice(KEYWORDS)
        tweet_text = f"Breaking: {kw} reported in region XYZ!"
        tweet_times.append(datetime.utcnow())
        print(f"[{kw.upper()}] {tweet_text}")

def fetch_tweets():
    global tweet_times
    generate_mock_tweets()

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
        time.sleep(2)  # simulate API delay
