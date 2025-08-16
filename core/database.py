import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_PATH = "crowdsense.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize the SQLite database with required tables"""
    with get_db_connection() as conn:
        # Create alerts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                message TEXT NOT NULL,
                tweet_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sms_sid TEXT,
                news_articles TEXT  -- JSON string of news articles
            )
        """)
        
        # Create tweets table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_id TEXT UNIQUE,
                keyword TEXT NOT NULL,
                user_screen_name TEXT,
                text TEXT NOT NULL,
                sentiment REAL,
                location TEXT,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tweet_created_at TIMESTAMP
            )
        """)
        
        # Create tweet_metrics table for anomaly detection
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tweet_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                count INTEGER NOT NULL,
                window_start TIMESTAMP NOT NULL,
                window_end TIMESTAMP NOT NULL,
                z_score REAL,
                ewma_value REAL,
                is_anomaly BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create system_logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                module TEXT NOT NULL,
                message TEXT NOT NULL,
                extra_data TEXT,  -- JSON string for additional data
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")


def save_alert(keyword: str, message: str, tweet_count: int, sms_sid: str = None, 
               news_articles: List[Dict] = None) -> int:
    """Save an alert to the database"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO alerts (keyword, message, tweet_count, sms_sid, news_articles)
            VALUES (?, ?, ?, ?, ?)
        """, (
            keyword, 
            message, 
            tweet_count, 
            sms_sid, 
            json.dumps(news_articles) if news_articles else None
        ))
        conn.commit()
        alert_id = cursor.lastrowid
        logger.info(f"Alert saved with ID: {alert_id}")
        return alert_id


def save_tweet(tweet_data: Dict[str, Any]) -> bool:
    """Save a tweet to the database"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO tweets 
                (tweet_id, keyword, user_screen_name, text, sentiment, location, 
                 latitude, longitude, tweet_created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tweet_data.get('id'),
                tweet_data.get('keyword'),
                tweet_data.get('user_screen_name'),
                tweet_data.get('text'),
                tweet_data.get('sentiment'),
                tweet_data.get('location'),
                tweet_data.get('latitude'),
                tweet_data.get('longitude'),
                tweet_data.get('created_at')
            ))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error saving tweet: {e}")
        return False


def save_tweet_metrics(keyword: str, count: int, window_start: datetime, 
                      window_end: datetime, z_score: float = None, 
                      ewma_value: float = None, is_anomaly: bool = False) -> int:
    """Save tweet metrics for anomaly detection"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO tweet_metrics 
            (keyword, count, window_start, window_end, z_score, ewma_value, is_anomaly)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (keyword, count, window_start, window_end, z_score, ewma_value, is_anomaly))
        conn.commit()
        return cursor.lastrowid


def get_recent_alerts(limit: int = 10) -> List[Dict]:
    """Get recent alerts from the database"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM alerts 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_recent_tweets(limit: int = 50) -> List[Dict]:
    """Get recent tweets from the database"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM tweets 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_tweets_with_location(limit: int = 100) -> List[Dict]:
    """Get tweets that have location data for map visualization"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM tweets 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_tweet_metrics_history(keyword: str, hours: int = 24) -> List[Dict]:
    """Get tweet metrics history for a keyword"""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM tweet_metrics 
            WHERE keyword = ? AND created_at > datetime('now', '-{} hours')
            ORDER BY created_at DESC
        """.format(hours), (keyword,))
        return [dict(row) for row in cursor.fetchall()]


def log_to_database(level: str, module: str, message: str, extra_data: Dict = None):
    """Log messages to the database"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO system_logs (level, module, message, extra_data)
                VALUES (?, ?, ?, ?)
            """, (
                level, 
                module, 
                message, 
                json.dumps(extra_data) if extra_data else None
            ))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging to database: {e}")


def get_system_stats() -> Dict[str, Any]:
    """Get system statistics"""
    with get_db_connection() as conn:
        stats = {}
        
        # Total alerts
        cursor = conn.execute("SELECT COUNT(*) as count FROM alerts")
        stats['total_alerts'] = cursor.fetchone()['count']
        
        # Total tweets
        cursor = conn.execute("SELECT COUNT(*) as count FROM tweets")
        stats['total_tweets'] = cursor.fetchone()['count']
        
        # Alerts in last 24 hours
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM alerts 
            WHERE created_at > datetime('now', '-24 hours')
        """)
        stats['alerts_24h'] = cursor.fetchone()['count']
        
        # Tweets in last hour
        cursor = conn.execute("""
            SELECT COUNT(*) as count FROM tweets 
            WHERE created_at > datetime('now', '-1 hour')
        """)
        stats['tweets_1h'] = cursor.fetchone()['count']
        
        return stats


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")
