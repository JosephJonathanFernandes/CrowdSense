# 🌍 CrowdSense Enhanced – AI-Powered Real-Time Disaster Detection System

CrowdSense Enhanced is an **AI-powered early warning system** that detects potential disasters in real time by analyzing live tweets, news feeds, and sensor data. It uses **machine learning, anomaly detection, and NLP** to identify unusual spikes in disaster-related chatter and sends instant alerts to users and authorities.

This enhanced version includes **realistic disaster simulation**, **advanced anomaly detection**, **database-backed metrics**, and a **full-featured web dashboard**.

---

## ✨ Features

### 🔹 Core Capabilities

* Real-time Twitter keyword monitoring (via Tweepy API)
* NLP-based classification of disaster-related tweets (NLTK, spaCy, scikit-learn)
* NewsAPI verification to reduce false positives
* Threshold-based and anomaly-based alerting
* Optional SMS notifications via Twilio

### 🔹 New Enhancements

1. **Live Data Integration**

   * Web dashboard connected to backend (`/api/data`, `/api/map-data`)
   * Auto-refresh every 5 minutes & manual refresh button

2. **SQLite Database Storage**

   * Tables for alerts, tweets, metrics, and logs
   * Historical data storage & trend analysis
   * Automated cleanup of old data

3. **Smart Anomaly Detection**

   * Z-score + EWMA-based detection
   * Historical data learning (past 24–48 hrs)
   * Adaptive thresholds

4. **Location Extraction & Map Visualization**

   * spaCy NER + OpenStreetMap geocoding
   * Interactive map (Leaflet.js) with tweet markers
   * Location-based filtering

5. **Background Task Scheduler**

   * Proper scheduling with `schedule` library
   * Multi-task execution & monitoring
   * Graceful shutdown + retry logic

6. **Structured Logging & Metrics**

   * Real-time metrics (tweets processed, alerts sent, errors)
   * Performance monitoring (API latency, execution times)
   * Structured contextual logging

7. **Disaster Simulation System (🆕)**

   * Trigger realistic disaster scenarios (earthquake, flood, fire, storm, tsunami)
   * Severity levels: moderate, major, severe
   * Realistic tweet generation + SMS alerts
   * Interactive simulation controls on web dashboard

---

## ⚙️ Tech Stack

* **Backend:** Python (Flask)
* **APIs:** Tweepy (Twitter API), Twilio (SMS), NewsAPI, OpenStreetMap (geocoding)
* **ML/NLP:** scikit-learn, NLTK, spaCy
* **Database:** SQLite (default) / PostgreSQL (optional)
* **Frontend:** HTML, CSS, JavaScript, Leaflet.js / Google Maps

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Setup Environment Variables

Create a `.env` file:

```env
TWITTER_BEARER_TOKEN=your_twitter_token  # Optional in simulation mode
NEWS_API_KEY=your_news_api_key           # Optional in simulation mode
TWILIO_SID=your_twilio_sid               # Required for SMS alerts
TWILIO_AUTH_TOKEN=your_twilio_token      # Required for SMS alerts
TWILIO_PHONE=your_twilio_phone           # Required for SMS alerts
MY_PHONE=your_phone_number               # Required for SMS alerts
```

### 3. Run the System

#### 🧪 Simulation Mode (Recommended)

```bash
python simulate.py earthquake
python simulate.py flood --severity severe
python simulate.py -i   # Interactive
python main.py simulation
```

* Dashboard: [http://localhost:5000](http://localhost:5000)
* Click disaster buttons to trigger scenarios
* Receive real SMS alerts!

#### 🌐 Production Mode (Live APIs)

```bash
python crowdsense.py
python main.py web
```

* Dashboard: [http://localhost:5000](http://localhost:5000)

#### Background Monitoring

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

---

## 📊 Dashboard Features

* Real-time **status indicator** (SAFE / ALERT / ERROR)
* Live **tweet feed** with location badges
* **Interactive global map** with disaster markers
* **System metrics:** processed tweets, alerts, errors
* **Recent alerts + verified news integration**
* **Sentiment analysis charts**

---

## 🔧 Configuration

### Anomaly Detection (in `anomaly_detection.py`)

```python
detector = AnomalyDetector(
    window_size=15,
    ewma_alpha=0.3,
    z_threshold=2.5
)
```

### Scheduler (in `scheduler.py`)

```python
scheduler.add_task(
    name="fetch_tweets",
    func=fetch_and_analyze_tweets,
    interval_minutes=1,
    run_immediately=True
)
```

### Database

* Default: `crowdsense.db` (SQLite)
* Auto-cleanup: Tweets >7 days, Logs >30 days

---

## 📈 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │  Background      │    │    Database     │
│  - Live Data    │◄───┤  Scheduler       ├───►│  - Alerts       │
│  - Map Visual   │    │  - Tweet Fetch   │    │  - Tweets       │
│  - Analytics    │    │  - Anomaly Det   │    │  - Metrics      │
└─────────────────┘    │  - Logging       │    │  - Logs         │
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  External APIs   │
                       │  - Twitter API   │
                       │  - News API      │
                       │  - Geocoding     │
                       │  - Twilio SMS    │
                       └──────────────────┘
```

---

## 🧪 Testing

```bash
python location_extraction.py   # Test NER + geocoding
python anomaly_detection.py     # Test anomaly detection
python database.py              # Test DB operations
python scheduler.py             # Test scheduler
```

---

## 📋 Monitoring & Maintenance

* Logs: `crowdsense.log` + DB logs (`system_logs` table)
* Auto-cleanup of old tweets/logs
* Metrics available via `/api/stats`
* Backup: Copy `crowdsense.db`

---

## 🔒 Security

* All secrets in `.env`
* API rate limiting + retry logic
* Sanitized tweet input before DB storage
* Structured error handling and logging

---

## 🤝 Contributing

1. Add new disaster keywords in `DISASTER_KEYWORDS` (in `crowdsense_enhanced.py`)
2. Extend anomaly detection by creating new detectors
3. Add new API endpoints in `hackathon_app/app.py`
4. Update database schema (`database.py`) for new features

---

## 📝 License

This enhanced version maintains the same license as the original CrowdSense project.

---

✅ **Production-ready system with full monitoring, logging, simulation, and anomaly detection.**


