import os
import requests
import time
import json
from datetime import datetime, timedelta, timezone
from collections import deque, defaultdict
from twilio.rest import Client

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ---------------- CONFIG ----------------
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
MY_PHONE = os.getenv("MY_PHONE")

# disaster keywords to monitor
DISASTER_KEYWORDS = [
    "earthquake",
    "flood",
    "cyclone",
    "tsunami",
    "landslide",
    "fire",
    "storm",
]

# IMPROVED SETTINGS FOR RATE LIMITING
WINDOW = timedelta(minutes=15)  # Longer window
THRESHOLD = 2  # Lower threshold
ALERT_COOLDOWN = timedelta(minutes=30)
API_RETRY_DELAY = 900  # 15 minutes for 429 errors
CYCLE_DELAY = 120  # 2 minutes between cycles

# Use separate tracking for each keyword
tweet_times = defaultdict(deque)
last_alert_time = defaultdict(lambda: None)
api_retry_time = None
current_keyword_index = 0  # Rotate through keywords

# ---------------- TWILIO SETUP ----------------
twilio_client = Client(TWILIO_SID, TWILIO_AUTH)


def send_sms_alert(message: str):
    """Send SMS using Twilio"""
    try:
        message_obj = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=MY_PHONE,
        )
        print(f"✅ SMS Sent! SID: {message_obj.sid}")
        return True
    except Exception as e:
        print(f"❌ SMS Failed: {e}")
        return False


# ---------------- GROQ AI INTEGRATION ----------------
def call_groq_ai(prompt, max_tokens=500):
    """Call Groq AI API with better error handling"""
    try:
        if not GROQ_API_KEY:
            print("❌ GROQ_API_KEY not found in environment variables")
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        print(f"🌐 Making Groq API call...")
        print(f"   Model: {data['model']}")
        print(f"   Max tokens: {max_tokens}")
        print(f"   Prompt length: {len(prompt)} characters")

        response = requests.post(url, headers=headers, json=data, timeout=30)

        print(f"🌐 Groq API Response: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            usage = result.get("usage", {})
            print(f"✅ Groq API Success!")
            print(f"   Response length: {len(content)} characters")
            print(f"   Tokens used: {usage.get('total_tokens', 'unknown')}")
            return content
        elif response.status_code == 401:
            print("❌ Groq API Authentication failed - check API key")
            print(f"   API key starts with: {GROQ_API_KEY[:10]}...")
            return None
        elif response.status_code == 429:
            print("❌ Groq API rate limit exceeded")
            return None
        elif response.status_code == 400:
            print("❌ Groq API bad request")
            print(f"   Error details: {response.text}")
            return None
        else:
            print(f"❌ Groq API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print("❌ Groq API timeout (30s)")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Groq API connection error - check internet")
        return None
    except Exception as e:
        print(f"❌ Groq API unexpected error: {e}")
        return None


def analyze_tweets_with_ai(tweets_data, keyword):
    """Use AI to analyze tweets and generate search queries"""
    if not tweets_data:
        print("❌ No tweets provided for analysis")
        return [], None

    print(f"📱 TWEETS BEING ANALYZED ({len(tweets_data)} total):")
    for i, tweet in enumerate(tweets_data[:5], 1):
        tweet_text = tweet.get("text", "")
        print(f"   {i}. {tweet_text}")

    tweets_text = "\n".join([f"- {tweet.get('text', '')}" for tweet in tweets_data[:8]])
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    prompt = f"""Current DateTime: {current_time}

Analyze these tweets about '{keyword}':
{tweets_text}

Tasks:
1. Extract the most likely location (city, state, country) from tweets
2. Generate 2-3 specific news search queries to verify this disaster
3. Assess if this appears genuine

Respond ONLY in JSON format:
{{
    "location": "specific location or null",
    "search_queries": ["query1", "query2", "query3"],
    "is_genuine": true/false,
    "confidence": "high/medium/low",
    "reasoning": "brief explanation"
}}"""

    print(f"🤖 Sending to Groq AI...")
    print(f"📝 PROMPT BEING SENT:")
    print(f"{prompt}")
    print("=" * 40)

    ai_response = call_groq_ai(prompt, max_tokens=300)

    print(f"🧠 AI RESPONSE RECEIVED:")
    if ai_response:
        print(f"✅ Response length: {len(ai_response)} characters")
        print(f"📄 Full response:")
        print(f"{ai_response}")
        print("=" * 40)
    else:
        print("❌ No response received from Groq AI")
        return [], None

    if ai_response:
        try:
            # Try to clean the response in case there's extra text
            response_cleaned = ai_response.strip()

            # Look for JSON within the response
            if "{" in response_cleaned and "}" in response_cleaned:
                start = response_cleaned.find("{")
                end = response_cleaned.rfind("}") + 1
                json_part = response_cleaned[start:end]
                print(f"🔍 Extracted JSON part: {json_part}")

                analysis = json.loads(json_part)

                print(f"📊 PARSED ANALYSIS:")
                print(f"   Location: {analysis.get('location')}")
                print(f"   Genuine: {analysis.get('is_genuine')}")
                print(f"   Confidence: {analysis.get('confidence')}")
                print(f"   Reasoning: {analysis.get('reasoning')}")
                print(f"   Search Queries: {analysis.get('search_queries')}")

                search_queries = analysis.get("search_queries", [])
                if not search_queries or len(search_queries) == 0:
                    print("❌ AI returned empty search queries")
                    return [], None

                return search_queries, analysis.get("location")
            else:
                print("❌ No JSON found in AI response")
                return [], None

        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Raw response that failed to parse: '{ai_response}'")

            # Try to manually extract some search queries as fallback
            if keyword in ai_response.lower():
                fallback_queries = [
                    f"{keyword} news today",
                    f"{keyword} disaster alert",
                    f"breaking {keyword} emergency",
                ]
                print(f"🔄 Using fallback search queries: {fallback_queries}")
                return fallback_queries, None
            else:
                return [], None

    return [], None


def fetch_news_with_queries(search_queries):
    """Fetch news using AI-generated search queries"""
    all_articles = []

    for i, query in enumerate(search_queries[:3], 1):
        try:
            print(f"📰 NEWS SEARCH #{i}: '{query}'")
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=3&language=en"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])

                if articles:
                    print(f"   ✅ Found {len(articles)} articles:")
                    for j, article in enumerate(articles, 1):
                        title = article.get("title", "No title")[:70]
                        source = article.get("source", {}).get("name", "Unknown")
                        url_link = article.get("url", "")
                        print(f"      {j}. [{source}] {title}")
                        print(f"         {url_link}")
                    all_articles.extend(articles)
                else:
                    print(f"   ❌ No articles found")
            else:
                print(f"❌ News API error: {response.status_code}")

        except Exception as e:
            print(f"❌ News fetch error: {e}")

    print(f"📊 TOTAL ARTICLES: {len(all_articles)}")
    return all_articles


def validate_news_with_ai(tweets_data, news_articles, keyword, location):
    """Use AI to validate if news confirms the disaster"""
    if not news_articles:
        return False, "No news found for validation", []

    tweets_text = "\n".join([f"- {tweet.get('text', '')}" for tweet in tweets_data[:5]])
    news_text = "\n".join(
        [
            f"- [{article.get('source', {}).get('name', 'Unknown')}] {article.get('title', '')}: {article.get('description', '')}"
            for article in news_articles[:5]
        ]
    )

    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    prompt = f"""Current DateTime: {current_time}

TWEETS about '{keyword}':
{tweets_text}

NEWS ARTICLES:
{news_text}

Validate if news confirms the disaster. Consider:
1. Same disaster type and location?
2. Recent (within 24 hours)?
3. Credible sources?
4. Actual ongoing/recent event?

Respond ONLY in JSON:
{{
    "is_validated": true/false,
    "confidence": "high/medium/low", 
    "summary": "Brief alert summary max 80 words",
    "news_urls": ["url1", "url2"]
}}"""

    print(f"🤖 Validating with AI...")
    ai_response = call_groq_ai(prompt, max_tokens=400)

    print(f"🧠 VALIDATION RESPONSE:")
    print(f"{ai_response}")

    if ai_response:
        try:
            # Clean the response and extract JSON like we do in analyze_tweets_with_ai
            response_cleaned = ai_response.strip()

            # Look for JSON within the response
            if "{" in response_cleaned and "}" in response_cleaned:
                start = response_cleaned.find("{")
                end = response_cleaned.rfind("}") + 1
                json_part = response_cleaned[start:end]
                print(f"🔍 Extracted JSON part: {json_part}")

                validation = json.loads(json_part)
                is_valid = validation.get("is_validated", False)
                summary = validation.get("summary", "Disaster detected")
                news_urls = validation.get("news_urls", [])
                confidence = validation.get("confidence", "unknown")

                print(f"🔍 VALIDATION RESULT:")
                print(f"   Valid: {'✅ YES' if is_valid else '❌ NO'}")
                print(f"   Confidence: {confidence}")
                print(f"   Summary: {summary}")

                return is_valid, summary, news_urls
            else:
                print("❌ No JSON found in validation response")
                return False, "No JSON in AI response", []

        except json.JSONDecodeError as e:
            print(f"❌ Validation JSON Error: {e}")
            print(f"Failed to parse: '{ai_response}'")
            return False, "AI validation failed", []

    return False, "AI unavailable", []


def create_sms_alert(summary, news_urls, keyword, location):
    """Create SMS alert within 160 character limit"""
    alert_msg = f"🚨 {keyword.upper()}"
    if location:
        alert_msg += f" - {location}"

    alert_msg += f"\n\n{summary}"

    # Add news links if space allows
    for url in news_urls[:2]:
        test_msg = alert_msg + f"\n{url}"
        if len(test_msg) <= 1500:  # SMS limit with margin
            alert_msg = test_msg
        else:
            break

    return alert_msg


# ---------------- IMPROVED TWITTER FETCH ----------------
def fetch_tweets():
    global api_retry_time, current_keyword_index

    # Check if we're in API cooldown
    if api_retry_time and datetime.now(timezone.utc) < api_retry_time:
        remaining = (api_retry_time - datetime.now(timezone.utc)).total_seconds()
        print(f"⏱️  API cooldown: {remaining/60:.1f} minutes remaining")
        return

    current_time = datetime.now(timezone.utc)
    print(f"🔍 AI Tweet Analysis - {current_time.strftime('%H:%M:%S')}")

    # Process ONE keyword per cycle to avoid rate limits
    kw = DISASTER_KEYWORDS[current_keyword_index]
    print(f"📡 Keyword #{current_keyword_index + 1}/{len(DISASTER_KEYWORDS)}: '{kw}'")
    current_keyword_index = (current_keyword_index + 1) % len(DISASTER_KEYWORDS)

    # Better Twitter query
    query = f'"{kw}" -is:retweet -is:reply lang:en'
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=10&tweet.fields=created_at"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    try:
        print(f"🌐 API Call: {query}")
        response = requests.get(url, headers=headers)
        print(f"🌐 Status: {response.status_code}")

        if response.status_code == 429:
            print("🚫 RATE LIMITED - 15min cooldown")
            api_retry_time = current_time + timedelta(seconds=API_RETRY_DELAY)
            return
        elif response.status_code == 401:
            print("❌ AUTH FAILED - Check bearer token")
            return
        elif response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(response.text[:200])
            return

        response_data = response.json()

        if "data" in response_data:
            tweets_data = response_data["data"]
            print(f"✅ Found {len(tweets_data)} tweets")

            # Add to tracking
            for _ in tweets_data:
                tweet_times[kw].append(current_time)
        else:
            print(f"ℹ️  No tweets found")
            tweets_data = []

    except Exception as e:
        print(f"🚨 Network error: {e}")
        return

    # Clean old tweets
    old_count = len(tweet_times[kw])
    while tweet_times[kw] and current_time - tweet_times[kw][0] > WINDOW:
        tweet_times[kw].popleft()
    cleaned_count = old_count - len(tweet_times[kw])

    if cleaned_count > 0:
        print(f"🧹 Cleaned {cleaned_count} old tweets")

    current_count = len(tweet_times[kw])
    print(
        f"📊 Window: {current_count}/{THRESHOLD} tweets in {WINDOW.total_seconds()/60:.0f}min"
    )

    # Check for alert condition
    if current_count >= THRESHOLD:
        print(f"⚠️  THRESHOLD REACHED! ({current_count} >= {THRESHOLD})")

        if (
            last_alert_time[kw] is None
            or current_time - last_alert_time[kw] > ALERT_COOLDOWN
        ):

            if not tweets_data:
                print("❌ No recent tweets for analysis")
                return

            print(f"🚨 STARTING AI ANALYSIS...")
            last_alert_time[kw] = current_time

            # AI Analysis Pipeline
            search_queries, ai_location = analyze_tweets_with_ai(tweets_data, kw)

            if not search_queries:
                print("❌ AI couldn't generate search queries")
                return

            news_articles = fetch_news_with_queries(search_queries)
            is_validated, summary, news_urls = validate_news_with_ai(
                tweets_data, news_articles, kw, ai_location
            )

            if is_validated:
                print("✅ AI VALIDATED DISASTER!")
                alert_msg = create_sms_alert(summary, news_urls, kw, ai_location)

                print(f"📱 SMS ({len(alert_msg)} chars):")
                print(f"'{alert_msg}'")

                if send_sms_alert(alert_msg):
                    print("✅ Alert sent!")

                tweet_times[kw].clear()
                print("🔄 Window reset")
            else:
                print("❌ AI rejected - not a valid disaster")
                print(f"   Reason: {summary}")
        else:
            cooldown = ALERT_COOLDOWN - (current_time - last_alert_time[kw])
            print(f"⏱️  Cooldown: {cooldown.total_seconds()/60:.1f}min remaining")
    else:
        needed = THRESHOLD - current_count
        print(f"✅ Need {needed} more tweets for alert")

    print("=" * 60)


# ---------------- MAIN LOOP ----------------
if __name__ == "__main__":
    print("🤖 AI-Powered CrowdSense v2.0")
    print(f"📊 Keywords: {DISASTER_KEYWORDS}")
    print(f"⚡ Threshold: {THRESHOLD} tweets per {WINDOW.total_seconds()/60:.0f}min")
    print(f"🔕 Cooldown: {ALERT_COOLDOWN.total_seconds()/60:.0f}min")
    print(f"⏱️  Cycle delay: {CYCLE_DELAY}s (better for rate limits)")
    print("=" * 60)

    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n🔄 CYCLE #{cycle}")
            fetch_tweets()
            print(f"😴 Waiting {CYCLE_DELAY}s...")
            time.sleep(CYCLE_DELAY)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            break
        except Exception as e:
            print(f"💥 Error: {e}")
            time.sleep(30)
