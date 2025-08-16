#!/usr/bin/env python3
"""
CrowdSense - Production Real-time Disaster Detection System
Main production version using real APIs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.crowdsense_enhanced import (
    initialize_system, 
    fetch_and_analyze_tweets,
    get_dashboard_data
)
from utils.logging_config import setup_logging, get_logger

logger = get_logger('crowdsense.main')


def main_production():
    """Run the production disaster detection system"""
    setup_logging('INFO', enable_db_logging=True)
    logger.info("Starting CrowdSense Production System...")
    
    # Initialize the system
    initialize_system()
    
    # Run analysis
    results = fetch_and_analyze_tweets()
    
    print("\n" + "="*50)
    print("📊 PRODUCTION ANALYSIS RESULTS")
    print("="*50)
    print(f"Keywords processed: {results['keywords_processed']}")
    print(f"Total tweets: {results['total_tweets']}")
    print(f"Anomalies detected: {results['anomalies_detected']}")
    print(f"Alerts sent: {results['alerts_sent']}")
    print(f"Errors: {results['errors']}")
    print("="*50)
    
    return results


if __name__ == "__main__":
    main_production()
