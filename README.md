# CrowdSense Enhanced - Real-time Disaster Detection System

## 🌟 New Features Added

This enhanced version of CrowdSense includes all the requested improvements plus **realistic disaster simulation**:

### ✅ 1. Live Data Integration
- **Web dashboard now connects to live backend data** from `crowdsense_enhanced.py`
- Real-time API endpoints for dashboard updates (`/api/data`, `/api/map-data`, etc.)
- Auto-refresh functionality every 5 minutes
- Manual refresh button for immediate updates

### ✅ 2. SQLite Database Storage
- **Complete database schema** with tables for alerts, tweets, metrics, and logs
- **Historical data storage** for trend analysis
- **Automated cleanup** of old data (tweets >7 days, logs >30 days)
- **Database-backed metrics** and statistics

### ✅ 3. Smart Anomaly Detection
- **Z-score based detection** with configurable thresholds
- **EWMA (Exponentially Weighted Moving Average)** for trend analysis
- **Combined anomaly scoring** requiring both statistical measures
- **Historical data learning** from past 24-48 hours
- **Adaptive thresholds** as alternative detection method

### ✅ 4. Location Extraction & Map Visualization
- **Named Entity Recognition (NER)** using spaCy for location extraction
- **Geocoding integration** with OpenStreetMap Nominatim API
- **Interactive map** using Leaflet with tweet location markers
- **Location-based filtering** and visualization
- **Fallback regex patterns** when NER is unavailable

### ✅ 5. Background Task Scheduler
- **Replaced while True loop** with proper `schedule` library
- **Multi-task scheduling** with different intervals
- **Task monitoring** and health checks
- **Graceful shutdown** handling
- **Error recovery** and retry logic

### ✅ 6. Structured Logging & Metrics
- **Comprehensive logging system** with database integration
- **Real-time metrics collection** (tweets processed, alerts sent, errors)
- **Performance monitoring** (API response times, execution times)
- **Log levels and filtering** (DEBUG, INFO, WARNING, ERROR)
- **Contextual logging** with structured data

### 🆕 7. Disaster Simulation System
- **Realistic disaster scenarios** with authentic tweet generation
- **Interactive web controls** to trigger disasters instantly
- **Real SMS alerts** sent to your phone during simulation
- **Multiple disaster types**: earthquake, flood, fire, storm, tsunami
- **Severity levels**: moderate, major, severe
- **Geographic diversity** with real locations and coordinates
- **Command-line tools** for automated testing

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Set Environment Variables
Create a `.env` file with:
```env
TWITTER_BEARER_TOKEN=your_twitter_token  # Optional for simulation mode
NEWS_API_KEY=your_news_api_key           # Optional for simulation mode
TWILIO_SID=your_twilio_sid               # Required for SMS alerts
TWILIO_AUTH_TOKEN=your_twilio_token      # Required for SMS alerts
TWILIO_PHONE=your_twilio_phone           # Required for SMS alerts
MY_PHONE=your_phone_number               # Required for SMS alerts
```

### 3. Run the System

#### 🧪 Simulation Mode (Recommended for Testing)
```bash
# Quick simulation
python simulate.py earthquake
python simulate.py flood --severity severe

# Interactive simulation with full options
python simulate.py -i

# Web dashboard with simulation
python main.py simulation
```
- Access dashboard at: http://localhost:5000
- Click disaster buttons to trigger scenarios
- Receive real SMS alerts on your phone!

#### 🌐 Production Mode (Real APIs)
```bash
# Production disaster detection
python crowdsense.py

# Web dashboard with real data
python main.py web
```
Access dashboard at: http://localhost:5000

#### Background Monitoring Only
```bash
python main.py background
```

#### Single Analysis (Testing)
```bash
python main.py single
```

#### Component Testing
```bash
python main.py test
```

## 📊 Dashboard Features

### Main Dashboard
- **Real-time status indicator** (SAFE/ALERT/ERROR)
- **System metrics** showing total alerts, tweets, and recent activity
- **Live tweet feed** with location badges
- **Recent alerts and news** integration
- **Interactive sentiment analysis** charts

### Map Visualization
- **Global map** showing tweet locations
- **Clickable markers** with tweet details
- **Auto-zoom** to fit all current markers
- **Real-time updates** every 5 minutes

### API Endpoints
- `/api/data` - Main dashboard data
- `/api/map-data` - Location data for map
- `/api/stats` - System statistics
- `/api/alerts` - Recent alerts
- `/api/scheduler-status` - Background task status

## 🔧 Configuration

### Anomaly Detection Settings
```python
# In anomaly_detection.py
detector = AnomalyDetector(
    window_size=15,      # Historical windows to consider
    ewma_alpha=0.3,      # EWMA smoothing factor
    z_threshold=2.5      # Z-score threshold for anomaly
)
```

### Scheduler Settings
```python
# In scheduler.py
scheduler.add_task(
    name="fetch_tweets",
    func=fetch_and_analyze_tweets,
    interval_minutes=1,  # Run every minute
    run_immediately=True
)
```

### Database Settings
- **SQLite database**: `crowdsense.db`
- **Auto-cleanup**: Configurable retention periods
- **Connection pooling**: Context managers for safe access

## 📈 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │  Background      │    │    Database     │
│                 │    │  Scheduler       │    │                 │
│  - Live Data    │◄───┤                  ├───►│  - Alerts       │
│  - Map Visual   │    │  - Tweet Fetch   │    │  - Tweets       │
│  - Analytics    │    │  - Anomaly Det   │    │  - Metrics      │
└─────────────────┘    │  - Logging       │    │  - Logs         │
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  External APIs   │
                       │                  │
                       │  - Twitter API   │
                       │  - News API      │
                       │  - Geocoding     │
                       │  - Twilio SMS    │
                       └──────────────────┘
```

## 🧪 Testing

### Component Tests
```bash
python main.py test
```

### Manual Testing
```bash
# Test location extraction
python location_extraction.py

# Test anomaly detection
python anomaly_detection.py

# Test database operations
python database.py

# Test scheduler
python scheduler.py
```

## 📋 Monitoring & Maintenance

### Log Files
- **Application logs**: `crowdsense.log`
- **Database logs**: Stored in `system_logs` table
- **Metrics**: Available via `/api/stats` endpoint

### Database Maintenance
- **Automatic cleanup**: Runs daily via scheduler
- **Manual cleanup**: Database functions available
- **Backup**: SQLite file can be copied for backup

### Performance Monitoring
- **Task execution times**: Tracked per scheduler task
- **API response times**: Logged for external API calls
- **Error rates**: Monitored and alerted

## 🔒 Security Considerations

- **Environment variables**: All sensitive data in `.env` file
- **Rate limiting**: Built into API requests with retry logic
- **Input validation**: Tweet data sanitized before database storage
- **Error handling**: Comprehensive error catching and logging

## 🤝 Contributing

1. Each module is self-contained and testable
2. Add new disaster keywords to `DISASTER_KEYWORDS` in `crowdsense_enhanced.py`
3. Extend anomaly detection by implementing new detector classes
4. Add new API endpoints in `hackathon_app/app.py`
5. Update database schema in `database.py` for new data types

## 📝 License

This enhanced version maintains the same license as the original CrowdSense project.

---

**Note**: This enhanced system is production-ready with proper error handling, logging, and monitoring. All requested features have been implemented and tested.
