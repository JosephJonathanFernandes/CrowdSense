"""
Enhanced CrowdSense with Simulation Support
Modified version that uses simulated data instead of real APIs for testing
"""

import time
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Any, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import TWITTER_BEARER_TOKEN, NEWS_API_KEY
from utils.alert import send_alert
from core.database import (
    init_database, save_alert, save_tweet, save_tweet_metrics, 
    get_recent_alerts, get_recent_tweets, get_system_stats
)
from core.anomaly_detection import AnomalyDetector
from core.location_extraction import extract_location_from_tweet
from utils.logging_config import (
    setup_logging, get_logger, metrics, 
    log_tweet_processed, log_alert_sent, log_anomaly_detected,
    log_location_extracted, log_api_request, log_error
)
from simulation.simulation import get_simulated_twitter_data, disaster_simulator

# ---------------- CONFIG ----------------
# Disaster keywords to monitor
DISASTER_KEYWORDS = ["earthquake", "flood", "cyclone", "tsunami", "landslide", "fire", "storm", "hurricane", "tornado"]

# Time window for analysis
WINDOW = timedelta(minutes=5)
ALERT_COOLDOWN = timedelta(minutes=15)

# Global state
tweet_buffers = {keyword: deque() for keyword in DISASTER_KEYWORDS}
last_alert_times = {keyword: None for keyword in DISASTER_KEYWORDS}
anomaly_detector = AnomalyDetector(window_size=15, ewma_alpha=0.3, z_threshold=2.0)  # Lower threshold for simulation

# Simulation mode flag
SIMULATION_MODE = True  # Set to True for simulation, False for real APIs

# Initialize logging
setup_logging('INFO', enable_db_logging=True)
logger = get_logger('crowdsense.simulation')


def build_retry_session() -> requests.Session:
    """Build HTTP session with retry logic"""
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


http = build_retry_session()


def check_news(keyword: str) -> List[Dict[str, Any]]:
    """Check related news - simulated or real based on mode"""
    if SIMULATION_MODE:
        # Return simulated news articles
        return [
            {
                "title": f"Breaking: {keyword.title()} emergency response activated",
                "url": f"https://news.example.com/{keyword}-emergency",
                "source": {"name": "Emergency News Network"}
            },
            {
                "title": f"Local authorities issue {keyword} safety guidelines",
                "url": f"https://safety.example.com/{keyword}-guidelines",
                "source": {"name": "Safety Alert System"}
            }
        ]
    
    # Real news API (original code)
    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not configured")
        return []
        
    try:
        start_time = time.time()
        url = f"https://newsapi.org/v2/everything?q={keyword}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        
        response = http.get(url, timeout=10)
        response_time = time.time() - start_time
        
        log_api_request('newsapi', response.status_code, response_time)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])[:3]
            logger.debug(f"Retrieved {len(articles)} news articles for '{keyword}'",
                        keyword=keyword, article_count=len(articles))
            return articles
        else:
            logger.warning(f"News API returned status {response.status_code}",
                          keyword=keyword, status_code=response.status_code)
            return []
            
    except Exception as e:
        log_error('news_api', e, {'keyword': keyword})
        return []


def fetch_tweets_for_keyword(keyword: str) -> List[Dict[str, Any]]:
    """Fetch tweets for a specific keyword - simulated or real based on mode"""
    
    if SIMULATION_MODE:
        # Use simulated Twitter data
        try:
            start_time = time.time()
            data = get_simulated_twitter_data(keyword)
            response_time = time.time() - start_time
            
            log_api_request('twitter_simulation', 200, response_time)
            
            if "data" not in data:
                logger.debug(f"No simulated tweets for keyword '{keyword}'", keyword=keyword)
                return []
                
            tweets = []
            for tweet_data in data["data"]:
                # Extract location information
                location_info = extract_location_from_tweet(tweet_data.get('text', ''))
                
                if location_info['primary_location']:
                    log_location_extracted(
                        location_info['primary_location'],
                        location_info['latitude'],
                        location_info['longitude']
                    )
                
                # Prepare tweet data for storage
                tweet_record = {
                    'id': tweet_data.get('id'),
                    'keyword': keyword,
                    'user_screen_name': tweet_data.get('author_id'),
                    'text': tweet_data.get('text'),
                    'sentiment': None,
                    'location': location_info['primary_location'],
                    'latitude': location_info['latitude'],
                    'longitude': location_info['longitude'],
                    'created_at': tweet_data.get('created_at'),
                    'tweet_created_at': tweet_data.get('created_at')
                }
                
                # Save to database
                if save_tweet(tweet_record):
                    tweets.append(tweet_record)
                
            logger.info(f"Processed {len(tweets)} simulated tweets for keyword '{keyword}'",
                       keyword=keyword, tweet_count=len(tweets))
            
            return tweets
            
        except Exception as e:
            log_error('twitter_simulation', e, {'keyword': keyword})
            return []
    
    # Real Twitter API (original code)
    if not TWITTER_BEARER_TOKEN:
        logger.error("TWITTER_BEARER_TOKEN not configured")
        return []

    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}

    try:
        start_time = time.time()
        url = f"https://api.twitter.com/2/tweets/search/recent?query={keyword}&max_results=10&tweet.fields=created_at,author_id,public_metrics"
        
        response = http.get(url, headers=headers, timeout=10)
        response_time = time.time() - start_time
        
        log_api_request('twitter', response.status_code, response_time)
        
        if response.status_code != 200:
            logger.error(f"Twitter API error for '{keyword}': {response.status_code}",
                        keyword=keyword, status_code=response.status_code)
            return []
            
        data = response.json()
        
        if "data" not in data:
            logger.debug(f"No tweets found for keyword '{keyword}'", keyword=keyword)
            return []
            
        tweets = []
        for tweet_data in data["data"]:
            # Extract location information
            location_info = extract_location_from_tweet(tweet_data.get('text', ''))
            
            if location_info['primary_location']:
                log_location_extracted(
                    location_info['primary_location'],
                    location_info['latitude'],
                    location_info['longitude']
                )
            
            # Prepare tweet data for storage
            tweet_record = {
                'id': tweet_data.get('id'),
                'keyword': keyword,
                'user_screen_name': tweet_data.get('author_id'),
                'text': tweet_data.get('text'),
                'sentiment': None,
                'location': location_info['primary_location'],
                'latitude': location_info['latitude'],
                'longitude': location_info['longitude'],
                'created_at': tweet_data.get('created_at'),
                'tweet_created_at': tweet_data.get('created_at')
            }
            
            # Save to database
            if save_tweet(tweet_record):
                tweets.append(tweet_record)
            
        logger.debug(f"Processed {len(tweets)} tweets for keyword '{keyword}'",
                    keyword=keyword, tweet_count=len(tweets))
        
        return tweets
        
    except Exception as e:
        log_error('twitter_api', e, {'keyword': keyword})
        return []


def analyze_tweet_anomaly(keyword: str, tweet_count: int) -> Tuple[float, float, bool]:
    """Analyze tweet count for anomalies using smart detection"""
    try:
        # Load historical data for this keyword if not already loaded
        if keyword not in anomaly_detector.keyword_history or not anomaly_detector.keyword_history[keyword]:
            anomaly_detector.load_historical_data(keyword, hours=24)
        
        # Update anomaly detector and get results
        z_score, ewma_value, is_anomaly = anomaly_detector.update_history(keyword, tweet_count)
        
        # Save metrics to database
        window_start = datetime.utcnow() - WINDOW
        window_end = datetime.utcnow()
        
        save_tweet_metrics(
            keyword=keyword,
            count=tweet_count,
            window_start=window_start,
            window_end=window_end,
            z_score=z_score,
            ewma_value=ewma_value,
            is_anomaly=is_anomaly
        )
        
        if is_anomaly:
            log_anomaly_detected(keyword, z_score, tweet_count)
            
        return z_score, ewma_value, is_anomaly
        
    except Exception as e:
        log_error('anomaly_detection', e, {'keyword': keyword, 'tweet_count': tweet_count})
        return 0.0, 0.0, False


def should_send_alert(keyword: str) -> bool:
    """Check if we should send an alert based on cooldown period"""
    if keyword not in last_alert_times:
        return True
        
    last_alert = last_alert_times[keyword]
    if last_alert is None:
        return True
        
    return datetime.utcnow() - last_alert > ALERT_COOLDOWN


def fetch_and_analyze_tweets() -> Dict[str, Any]:
    """Main function to fetch and analyze tweets for all keywords"""
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'keywords_processed': 0,
        'total_tweets': 0,
        'anomalies_detected': 0,
        'alerts_sent': 0,
        'errors': 0,
        'simulation_mode': SIMULATION_MODE
    }
    
    try:
        logger.info(f"Starting tweet fetch and analysis cycle (simulation: {SIMULATION_MODE})")
        
        for keyword in DISASTER_KEYWORDS:
            try:
                # Fetch tweets for this keyword
                tweets = fetch_tweets_for_keyword(keyword)
                tweet_count = len(tweets)
                
                # Update tweet buffer
                current_time = datetime.utcnow()
                tweet_buffers[keyword].extend([current_time] * tweet_count)
                
                # Clean old tweets from buffer
                cutoff = current_time - WINDOW
                while tweet_buffers[keyword] and tweet_buffers[keyword][0] < cutoff:
                    tweet_buffers[keyword].popleft()
                
                # Get current count in window
                window_count = len(tweet_buffers[keyword])
                
                # Analyze for anomalies
                z_score, ewma_value, is_anomaly = analyze_tweet_anomaly(keyword, window_count)
                
                # Log tweet processing
                log_tweet_processed(keyword, tweet_count)
                
                # Update results
                results['keywords_processed'] += 1
                results['total_tweets'] += tweet_count
                
                if is_anomaly:
                    results['anomalies_detected'] += 1
                    
                    # Check if we should send an alert
                    if should_send_alert(keyword):
                        try:
                            # Create short, simple alert message
                            mode_text = "SIMULATION" if SIMULATION_MODE else "REAL"
                            
                            # Add location info if available from recent tweets
                            location_text = ""
                            if tweets:
                                locations = [t.get('location') for t in tweets if t.get('location')]
                                if locations:
                                    unique_locations = list(set(locations))
                                    location_text = f" in {unique_locations[0]}" if unique_locations else ""
                            
                            alert_msg = f"{keyword.title()} activity detected{location_text}. {mode_text.lower()} alert."
                            
                            # Get related news (but don't include in SMS)
                            articles = check_news(keyword)
                            
                            # Send SMS alert (with delay to prevent spam filtering)
                            import time
                            time.sleep(2)  # 2 second delay between alerts
                            sms_sid = send_alert(alert_msg)
                            
                            # Save alert to database
                            alert_id = save_alert(
                                keyword=keyword,
                                message=alert_msg,
                                tweet_count=window_count,
                                sms_sid=sms_sid,
                                news_articles=articles
                            )
                            
                            # Update state
                            last_alert_times[keyword] = current_time
                            results['alerts_sent'] += 1
                            
                            # Clear buffer after alert
                            tweet_buffers[keyword].clear()
                            
                            log_alert_sent(keyword, alert_msg, sms_sid)
                            
                            logger.info(f"Alert sent for keyword '{keyword}' (simulation: {SIMULATION_MODE})",
                                       keyword=keyword, alert_id=alert_id, z_score=z_score)
                            
                        except Exception as e:
                            log_error('alert_sending', e, {'keyword': keyword})
                            results['errors'] += 1
                            
                logger.debug(f"Keyword '{keyword}' analysis complete",
                           keyword=keyword, 
                           tweet_count=tweet_count, 
                           window_count=window_count,
                           z_score=z_score,
                           is_anomaly=is_anomaly)
                           
            except Exception as e:
                log_error('keyword_processing', e, {'keyword': keyword})
                results['errors'] += 1
        
        # Update global metrics
        metrics.increment('tweets_processed', results['total_tweets'])
        metrics.increment('anomalies_detected', results['anomalies_detected'])
        metrics.increment('alerts_sent', results['alerts_sent'])
        
        logger.info("Tweet analysis cycle completed",
                   **{k: v for k, v in results.items() if k != 'timestamp'})
        
        return results
        
    except Exception as e:
        log_error('main_loop', e)
        results['errors'] += 1
        return results


def get_dashboard_data() -> Dict[str, Any]:
    """Get data for the web dashboard"""
    try:
        # Get recent data from database
        recent_alerts = get_recent_alerts(limit=10)
        recent_tweets = get_recent_tweets(limit=20)
        system_stats = get_system_stats()
        
        # Determine system status
        recent_anomalies = sum(1 for alert in recent_alerts 
                             if alert['created_at'] > (datetime.utcnow() - timedelta(hours=1)).isoformat())
        
        status = "ALERT" if recent_anomalies > 0 else "SAFE"
        
        # Format tweets for display
        formatted_tweets = []
        for tweet in recent_tweets[:10]:  # Limit to 10 for display
            formatted_tweets.append({
                'user': tweet.get('user_screen_name', 'Unknown'),
                'text': tweet.get('text', '')[:100] + ('...' if len(tweet.get('text', '')) > 100 else ''),
                'sentiment': 'Neutral',  # Could add sentiment analysis
                'location': tweet.get('location'),
                'latitude': tweet.get('latitude'),
                'longitude': tweet.get('longitude'),
                'created_at': tweet.get('created_at')
            })
        
        # Format alerts as news
        formatted_news = []
        for alert in recent_alerts[:5]:
            headline = f"Alert: {alert['keyword'].title()} activity detected"
            if alert.get('news_articles'):
                try:
                    import json
                    articles = json.loads(alert['news_articles'])
                    if articles:
                        headline = articles[0].get('title', headline)
                except:
                    pass
            formatted_news.append({'headline': headline})
        
        return {
            'status': status,
            'tweets': formatted_tweets,
            'news': formatted_news,
            'alerts': recent_alerts,
            'stats': system_stats,
            'metrics': metrics.get_metrics(),
            'simulation_mode': SIMULATION_MODE,
            'active_scenarios': disaster_simulator.active_scenarios,
            'last_updated': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_error('dashboard_data', e)
        return {
            'status': 'ERROR',
            'tweets': [],
            'news': [],
            'alerts': [],
            'stats': {},
            'metrics': {},
            'simulation_mode': SIMULATION_MODE,
            'last_updated': datetime.utcnow().isoformat(),
            'error': str(e)
        }


def initialize_system():
    """Initialize the CrowdSense system"""
    logger.info(f"Initializing CrowdSense system (simulation mode: {SIMULATION_MODE})...")
    
    # Initialize database
    init_database()
    logger.info("Database initialized")
    
    # Load historical data for anomaly detection
    for keyword in DISASTER_KEYWORDS:
        anomaly_detector.load_historical_data(keyword, hours=48)
    
    logger.info("Historical data loaded for anomaly detection")
    
    if SIMULATION_MODE:
        # Start simulation mode
        from simulation.simulation import start_simulation_mode
        start_simulation_mode()
        logger.info("Simulation mode activated - ready for disaster scenarios")
    
    logger.info("CrowdSense system initialization complete")


if __name__ == "__main__":
    # Initialize system
    initialize_system()
    
    # Run analysis once for testing
    print("Running single analysis cycle...")
    results = fetch_and_analyze_tweets()
    print(f"Results: {results}")
    
    # Get dashboard data
    print("\nDashboard data:")
    dashboard_data = get_dashboard_data()
    print(f"Status: {dashboard_data['status']}")
    print(f"Tweets: {len(dashboard_data['tweets'])}")
    print(f"Alerts: {len(dashboard_data['alerts'])}")
    print(f"Simulation mode: {dashboard_data['simulation_mode']}")
