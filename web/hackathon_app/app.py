import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, render_template, jsonify
from core.crowdsense_enhanced import get_dashboard_data, initialize_system
from core.database import get_tweets_with_location, get_recent_alerts, get_system_stats
from core.scheduler import scheduler
import threading

app = Flask(__name__)

# Initialize the system when the app starts
initialize_system()

@app.route("/")
def index():
    """Render the main dashboard"""
    try:
        data = get_dashboard_data()
        return render_template("index1.html", data=data)
    except Exception as e:
        # Fallback to basic data in case of error
        error_data = {
            "status": "ERROR",
            "tweets": [],
            "news": [],
            "error": str(e)
        }
        return render_template("index.html", data=error_data)

@app.route("/api/data")
def api_data():
    """API endpoint for live dashboard data"""
    return jsonify(get_dashboard_data())

@app.route("/api/map-data")
def map_data():
    """API endpoint for map visualization data"""
    try:
        tweets_with_location = get_tweets_with_location(limit=100)
        
        # Format data for map
        map_points = []
        for tweet in tweets_with_location:
            if tweet['latitude'] and tweet['longitude']:
                map_points.append({
                    'lat': float(tweet['latitude']),
                    'lng': float(tweet['longitude']),
                    'location': tweet['location'],
                    'text': tweet['text'][:100] + ('...' if len(tweet['text']) > 100 else ''),
                    'keyword': tweet['keyword'],
                    'created_at': tweet['created_at']
                })
        
        return jsonify({
            'points': map_points,
            'count': len(map_points)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'points': [], 'count': 0})

@app.route("/api/stats")
def stats():
    """API endpoint for system statistics"""
    try:
        return jsonify(get_system_stats())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route("/api/alerts")
def alerts():
    """API endpoint for recent alerts"""
    try:
        recent_alerts = get_recent_alerts(limit=20)
        return jsonify(recent_alerts)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route("/api/scheduler-status")
def scheduler_status():
    """API endpoint for scheduler status"""
    try:
        return jsonify(scheduler.get_task_status())
    except Exception as e:
        return jsonify({'error': str(e)})

def start_background_tasks():
    """Start background tasks in a separate thread"""
    from core.scheduler import start_crowdsense_scheduler
    
    def run_scheduler():
        start_crowdsense_scheduler()
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

if __name__ == "__main__":
    # Start background tasks
    start_background_tasks()
    
    # Run Flask app
    app.run(debug=True, threaded=True)
