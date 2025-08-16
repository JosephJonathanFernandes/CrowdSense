import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY")

def fetch_disaster_news(query="earthquake"):
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "articles" in data:
        for article in data["articles"][:5]:  # limit to 5
            print(f"📰 {article['title']} - {article['source']['name']}")
    else:
        print("⚠️ Error fetching news:", data)

if __name__ == "__main__":
    fetch_disaster_news("flood")
