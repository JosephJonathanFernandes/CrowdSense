#!/usr/bin/env python3
"""
CrowdSense - Enhanced Real-time Disaster Detection System
Main entry point for the application
"""

import sys
import os
import argparse

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logging_config import setup_logging, get_logger
from core.database import init_database
from core.crowdsense_enhanced import initialize_system
from core.scheduler import start_crowdsense_scheduler

logger = get_logger('main')


def run_web_app(simulation_mode: bool = False):
    """Run the web dashboard application"""
    logger.info(f"Starting CrowdSense web dashboard (simulation: {simulation_mode})...")
    
    # Import appropriate app module
    if simulation_mode:
        from web.hackathon_app.app_simulation import app, start_background_tasks
    else:
        from web.hackathon_app.app import app, start_background_tasks
    
    # Start background tasks
    start_background_tasks()
    
    # Run the web application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )


def run_background_only(simulation_mode: bool = False):
    """Run only the background monitoring system"""
    logger.info(f"Starting CrowdSense background monitoring (simulation: {simulation_mode})...")
    
    # Initialize the appropriate system
    if simulation_mode:
        from simulation.crowdsense_simulation import initialize_system as init_sim
        init_sim()
    else:
        initialize_system()
    
    # Start the scheduler
    scheduler = start_crowdsense_scheduler()
    
    try:
        # Keep the main thread alive
        import time
        while True:
            time.sleep(60)
            
            # Log scheduler status periodically
            status = scheduler.get_task_status()
            logger.info("Scheduler status", scheduler_status=status)
            
    except KeyboardInterrupt:
        logger.info("Shutting down CrowdSense...")
        scheduler.stop()
        sys.exit(0)


def run_single_analysis():
    """Run a single analysis cycle for testing"""
    logger.info("Running single analysis cycle...")
    
    # Initialize the system
    initialize_system()
    
    # Import and run analysis
    from core.crowdsense_enhanced import fetch_and_analyze_tweets
    
    results = fetch_and_analyze_tweets()
    
    print("\n" + "="*50)
    print("ANALYSIS RESULTS")
    print("="*50)
    print(f"Keywords processed: {results['keywords_processed']}")
    print(f"Total tweets: {results['total_tweets']}")
    print(f"Anomalies detected: {results['anomalies_detected']}")
    print(f"Alerts sent: {results['alerts_sent']}")
    print(f"Errors: {results['errors']}")
    print("="*50)
    
    # Show dashboard data
    from core.crowdsense_enhanced import get_dashboard_data
    dashboard = get_dashboard_data()
    
    print(f"\nSystem status: {dashboard['status']}")
    print(f"Recent tweets: {len(dashboard['tweets'])}")
    print(f"Recent alerts: {len(dashboard['alerts'])}")
    
    if dashboard['stats']:
        stats = dashboard['stats']
        print(f"\nSystem Statistics:")
        print(f"  Total alerts: {stats.get('total_alerts', 0)}")
        print(f"  Total tweets: {stats.get('total_tweets', 0)}")
        print(f"  Alerts (24h): {stats.get('alerts_24h', 0)}")
        print(f"  Tweets (1h): {stats.get('tweets_1h', 0)}")


def test_components():
    """Test individual components"""
    logger.info("Testing CrowdSense components...")
    
    print("Initializing database...")
    init_database()
    print("✅ Database initialized")
    
    print("\nTesting location extraction...")
    from core.location_extraction import extract_location_from_tweet
    
    test_tweet = "Major earthquake hits San Francisco, emergency services responding"
    location_result = extract_location_from_tweet(test_tweet)
    print(f"✅ Location extraction: {location_result}")
    
    print("\nTesting anomaly detection...")
    from core.anomaly_detection import AnomalyDetector
    
    detector = AnomalyDetector()
    z_score, ewma, is_anomaly = detector.update_history("earthquake", 10)
    print(f"✅ Anomaly detection: z_score={z_score:.2f}, ewma={ewma:.2f}, anomaly={is_anomaly}")
    
    print("\nTesting database operations...")
    from core.database import save_alert, get_recent_alerts
    
    alert_id = save_alert("test", "Test alert message", 5)
    alerts = get_recent_alerts(1)
    print(f"✅ Database operations: alert_id={alert_id}, alerts_count={len(alerts)}")
    
    print("\n🎉 All components tested successfully!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='CrowdSense - Real-time Disaster Detection System')
    parser.add_argument('mode', choices=['web', 'background', 'single', 'test', 'simulation'], 
                       help='Run mode: web (dashboard), background (monitoring only), single (one analysis), test (component tests), simulation (web with simulation)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    parser.add_argument('--no-db-logging', action='store_true',
                       help='Disable database logging')
    parser.add_argument('--simulation', action='store_true',
                       help='Enable simulation mode for testing')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, enable_db_logging=not args.no_db_logging)
    
    try:
        if args.mode == 'web':
            run_web_app(simulation_mode=args.simulation)
        elif args.mode == 'simulation':
            run_web_app(simulation_mode=True)
        elif args.mode == 'background':
            run_background_only(simulation_mode=args.simulation)
        elif args.mode == 'single':
            run_single_analysis()
        elif args.mode == 'test':
            test_components()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
