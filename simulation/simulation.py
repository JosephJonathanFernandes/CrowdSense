"""
Twitter API and Disaster Simulation for CrowdSense
Simulates realistic disaster scenarios to test the full system including SMS alerts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from utils.logging_config import get_logger

logger = get_logger('simulation')

# Realistic disaster scenarios with locations
DISASTER_SCENARIOS = {
    "earthquake": [
        {"location": "San Francisco", "lat": 37.7749, "lng": -122.4194, "severity": "major"},
        {"location": "Los Angeles", "lat": 34.0522, "lng": -118.2437, "severity": "moderate"},
        {"location": "Tokyo", "lat": 35.6762, "lng": 139.6503, "severity": "severe"},
        {"location": "Istanbul", "lat": 41.0082, "lng": 28.9784, "severity": "major"},
        {"location": "Mexico City", "lat": 19.4326, "lng": -99.1332, "severity": "moderate"},
    ],
    "flood": [
        {"location": "Houston", "lat": 29.7604, "lng": -95.3698, "severity": "severe"},
        {"location": "Mumbai", "lat": 19.0760, "lng": 72.8777, "severity": "major"},
        {"location": "New Orleans", "lat": 29.9511, "lng": -90.0715, "severity": "moderate"},
        {"location": "Bangkok", "lat": 13.7563, "lng": 100.5018, "severity": "major"},
        {"location": "Venice", "lat": 45.4408, "lng": 12.3155, "severity": "moderate"},
    ],
    "fire": [
        {"location": "California", "lat": 36.7783, "lng": -119.4179, "severity": "severe"},
        {"location": "Australia", "lat": -25.2744, "lng": 133.7751, "severity": "major"},
        {"location": "Oregon", "lat": 44.9519, "lng": -123.0307, "severity": "moderate"},
        {"location": "Greece", "lat": 39.0742, "lng": 21.8243, "severity": "major"},
        {"location": "Brazil", "lat": -14.2350, "lng": -51.9253, "severity": "severe"},
    ],
    "storm": [
        {"location": "Miami", "lat": 25.7617, "lng": -80.1918, "severity": "major"},
        {"location": "Philippines", "lat": 12.8797, "lng": 121.7740, "severity": "severe"},
        {"location": "New York", "lat": 40.7128, "lng": -74.0060, "severity": "moderate"},
        {"location": "Caribbean", "lat": 21.4691, "lng": -78.6569, "severity": "major"},
        {"location": "Gulf Coast", "lat": 29.2520, "lng": -89.4012, "severity": "severe"},
    ],
    "tsunami": [
        {"location": "Pacific Coast", "lat": 35.0000, "lng": -120.0000, "severity": "severe"},
        {"location": "Japan", "lat": 36.2048, "lng": 138.2529, "severity": "major"},
        {"location": "Indonesia", "lat": -0.7893, "lng": 113.9213, "severity": "severe"},
        {"location": "Chile", "lat": -35.6751, "lng": -71.5430, "severity": "moderate"},
        {"location": "Alaska", "lat": 61.2181, "lng": -149.9003, "severity": "major"},
    ]
}

# Tweet templates for realistic content
TWEET_TEMPLATES = {
    "earthquake": [
        "🚨 BREAKING: {severity} earthquake hits {location}! Buildings shaking, people evacuating #earthquake",
        "Magnitude {magnitude} earthquake reported in {location}. Stay safe everyone! #earthquake #emergency",
        "Just felt a strong earthquake in {location}. Power is out in several areas #earthquake",
        "Emergency services responding to earthquake in {location}. Avoid damaged buildings #earthquake",
        "URGENT: Earthquake aftershocks continue in {location}. Seek shelter immediately #earthquake"
    ],
    "flood": [
        "🌊 FLOOD WARNING: {location} experiencing severe flooding! Roads impassable #flood #emergency",
        "Water levels rising rapidly in {location}. Evacuations underway #flood",
        "Flash flood emergency in {location}! Avoid low-lying areas #flood #safety",
        "Rescue operations ongoing in flood-hit {location}. Many stranded #flood",
        "URGENT: Dam overflow causes major flooding in {location} #flood #evacuation"
    ],
    "fire": [
        "🔥 WILDFIRE ALERT: Large fire spreading rapidly near {location}! #wildfire #evacuation",
        "Evacuations ordered as fire approaches {location}. Smoke visible for miles #fire",
        "Emergency crews battling massive blaze in {location} #wildfire #emergency",
        "Fire danger extreme in {location}. Red flag warning issued #fire #safety",
        "BREAKING: Multiple structures destroyed by fire in {location} #wildfire"
    ],
    "storm": [
        "⛈️ SEVERE STORM: {location} hit by powerful storm! Winds {wind_speed}mph #storm",
        "Tornado warning issued for {location}. Take shelter immediately! #tornado #storm",
        "Hurricane {name} makes landfall near {location}. Category {category} #hurricane",
        "Damaging winds and hail reported in {location} #storm #severeweather",
        "Power outages widespread in {location} due to severe storms #storm"
    ],
    "tsunami": [
        "🌊 TSUNAMI WARNING: Wave heights up to {height}ft expected in {location}! #tsunami",
        "Evacuate coastal areas of {location} immediately! Tsunami waves incoming #tsunami",
        "All-clear tsunami warning lifted for {location} after evacuation #tsunami",
        "Tsunami advisory in effect for {location}. Stay away from beaches #tsunami",
        "Emergency: Large tsunami waves observed approaching {location} #tsunami"
    ]
}


class DisasterSimulator:
    """Simulate realistic disaster scenarios for testing"""
    
    def __init__(self):
        self.active_scenarios = {}
        self.simulation_mode = False
        
    def start_simulation(self):
        """Start simulation mode"""
        self.simulation_mode = True
        logger.info("Disaster simulation mode activated")
        
    def stop_simulation(self):
        """Stop simulation mode"""
        self.simulation_mode = False
        self.active_scenarios.clear()
        logger.info("Disaster simulation mode deactivated")
        
    def trigger_disaster_scenario(self, disaster_type: str, severity: str = "random") -> Dict[str, Any]:
        """
        Trigger a specific disaster scenario
        
        Args:
            disaster_type: Type of disaster (earthquake, flood, fire, storm, tsunami)
            severity: Severity level (low, moderate, major, severe) or "random"
            
        Returns:
            Dictionary with scenario details
        """
        if disaster_type not in DISASTER_SCENARIOS:
            raise ValueError(f"Unknown disaster type: {disaster_type}")
            
        # Select random location for this disaster type
        scenario = random.choice(DISASTER_SCENARIOS[disaster_type])
        
        # Override severity if specified
        if severity != "random":
            scenario["severity"] = severity
            
        # Generate additional realistic details
        scenario.update({
            "disaster_type": disaster_type,
            "start_time": datetime.utcnow(),
            "magnitude": self._generate_magnitude(disaster_type, scenario["severity"]),
            "wind_speed": random.randint(70, 150) if disaster_type == "storm" else None,
            "height": random.randint(5, 30) if disaster_type == "tsunami" else None,
            "name": self._generate_storm_name() if disaster_type in ["storm", "hurricane"] else None,
            "category": random.randint(1, 5) if disaster_type == "storm" else None
        })
        
        # Store active scenario
        scenario_id = f"{disaster_type}_{int(time.time())}"
        self.active_scenarios[scenario_id] = scenario
        
        logger.info(f"Triggered {disaster_type} scenario in {scenario['location']}", 
                   scenario=scenario)
        
        return scenario
        
    def _generate_magnitude(self, disaster_type: str, severity: str) -> float:
        """Generate realistic magnitude based on disaster type and severity"""
        if disaster_type == "earthquake":
            severity_ranges = {
                "moderate": (4.0, 5.5),
                "major": (5.5, 7.0),
                "severe": (7.0, 9.0)
            }
            min_mag, max_mag = severity_ranges.get(severity, (5.0, 6.5))
            return round(random.uniform(min_mag, max_mag), 1)
        return 0.0
        
    def _generate_storm_name(self) -> str:
        """Generate random storm name"""
        names = ["Alex", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta", 
                "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi"]
        return random.choice(names)
        
    def generate_disaster_tweets(self, disaster_type: str, scenario: Dict[str, Any], count: int = 15) -> List[Dict[str, Any]]:
        """
        Generate realistic tweets for a disaster scenario
        
        Args:
            disaster_type: Type of disaster
            scenario: Scenario details
            count: Number of tweets to generate
            
        Returns:
            List of tweet data
        """
        tweets = []
        templates = TWEET_TEMPLATES.get(disaster_type, [])
        
        if not templates:
            return tweets
            
        for i in range(count):
            template = random.choice(templates)
            
            # Fill in template variables
            tweet_text = template.format(
                location=scenario["location"],
                severity=scenario["severity"],
                magnitude=scenario.get("magnitude", ""),
                wind_speed=scenario.get("wind_speed", ""),
                height=scenario.get("height", ""),
                name=scenario.get("name", ""),
                category=scenario.get("category", "")
            )
            
            # Generate tweet data
            tweet = {
                "id": f"sim_{disaster_type}_{i}_{int(time.time())}",
                "text": tweet_text,
                "keyword": disaster_type,
                "user_screen_name": f"user_{random.randint(1000, 9999)}",
                "created_at": (datetime.utcnow() - timedelta(minutes=random.randint(0, 30))).isoformat(),
                "location": scenario["location"],
                "latitude": scenario["lat"],
                "longitude": scenario["lng"],
                "sentiment": random.choice(["Negative", "Neutral"]) # Disasters are rarely positive
            }
            
            tweets.append(tweet)
            
        logger.info(f"Generated {len(tweets)} simulated tweets for {disaster_type} in {scenario['location']}")
        return tweets


class TwitterAPISimulator:
    """Simulate Twitter API responses"""
    
    def __init__(self, disaster_simulator: DisasterSimulator):
        self.disaster_simulator = disaster_simulator
        self.baseline_tweet_counts = {keyword: random.randint(1, 3) for keyword in DISASTER_SCENARIOS.keys()}
        
    def simulate_twitter_response(self, keyword: str) -> Dict[str, Any]:
        """
        Simulate Twitter API response for a keyword
        
        Args:
            keyword: Disaster keyword to search for
            
        Returns:
            Simulated Twitter API response
        """
        if not self.disaster_simulator.simulation_mode:
            # Return minimal baseline data when not in simulation mode
            return {"data": []}
            
        # Check if there's an active scenario for this keyword
        active_scenario = None
        for scenario in self.disaster_simulator.active_scenarios.values():
            if scenario["disaster_type"] == keyword:
                active_scenario = scenario
                break
                
        if active_scenario:
            # Generate high volume of tweets for active disaster
            tweet_count = random.randint(10, 25)  # High count to trigger anomaly
            tweets = self.disaster_simulator.generate_disaster_tweets(keyword, active_scenario, tweet_count)
        else:
            # Generate baseline normal activity
            tweet_count = self.baseline_tweet_counts.get(keyword, 2)
            tweets = self._generate_baseline_tweets(keyword, tweet_count)
            
        # Format as Twitter API response
        response = {
            "data": [
                {
                    "id": tweet["id"],
                    "text": tweet["text"],
                    "created_at": tweet["created_at"],
                    "author_id": tweet["user_screen_name"]
                }
                for tweet in tweets
            ]
        }
        
        logger.debug(f"Simulated Twitter API response for '{keyword}': {len(tweets)} tweets")
        return response
        
    def _generate_baseline_tweets(self, keyword: str, count: int) -> List[Dict[str, Any]]:
        """Generate baseline (non-disaster) tweets"""
        baseline_templates = {
            "earthquake": ["Earthquake preparedness drill today", "Reading about earthquake safety"],
            "flood": ["River levels normal today", "Flood insurance important to have"],
            "fire": ["Fire safety tips for summer", "Beautiful sunset looks like fire"],
            "storm": ["Nice thunderstorm last night", "Storm clouds gathering"],
            "tsunami": ["Tsunami documentary was interesting", "Beach waves look big today"]
        }
        
        tweets = []
        templates = baseline_templates.get(keyword, [f"Thinking about {keyword} safety"])
        
        for i in range(count):
            template = random.choice(templates) if templates else f"Normal day, no {keyword}"
            
            tweet = {
                "id": f"baseline_{keyword}_{i}_{int(time.time())}",
                "text": template,
                "keyword": keyword,
                "user_screen_name": f"user_{random.randint(1000, 9999)}",
                "created_at": datetime.utcnow().isoformat(),
                "location": None,
                "latitude": None,
                "longitude": None,
                "sentiment": "Neutral"
            }
            tweets.append(tweet)
            
        return tweets


# Global simulator instances
disaster_simulator = DisasterSimulator()
twitter_simulator = TwitterAPISimulator(disaster_simulator)


def simulate_disaster_scenario(disaster_type: str, severity: str = "major") -> Dict[str, Any]:
    """
    Public function to trigger a disaster scenario
    
    Args:
        disaster_type: Type of disaster (earthquake, flood, fire, storm, tsunami)
        severity: Severity level (moderate, major, severe)
        
    Returns:
        Scenario details
    """
    if not disaster_simulator.simulation_mode:
        disaster_simulator.start_simulation()
        
    return disaster_simulator.trigger_disaster_scenario(disaster_type, severity)


def get_simulated_twitter_data(keyword: str) -> Dict[str, Any]:
    """
    Get simulated Twitter data for a keyword
    
    Args:
        keyword: Disaster keyword
        
    Returns:
        Simulated Twitter API response
    """
    return twitter_simulator.simulate_twitter_response(keyword)


def start_simulation_mode():
    """Start disaster simulation mode"""
    disaster_simulator.start_simulation()


def stop_simulation_mode():
    """Stop disaster simulation mode"""
    disaster_simulator.stop_simulation()


def get_active_scenarios() -> Dict[str, Any]:
    """Get currently active disaster scenarios"""
    return disaster_simulator.active_scenarios


if __name__ == "__main__":
    # Test the simulation
    print("🧪 Testing Disaster Simulation")
    print("=" * 40)
    
    # Start simulation
    start_simulation_mode()
    
    # Trigger earthquake scenario
    scenario = simulate_disaster_scenario("earthquake", "major")
    print(f"Triggered scenario: {scenario}")
    
    # Generate tweets
    tweets_response = get_simulated_twitter_data("earthquake")
    print(f"Generated {len(tweets_response['data'])} tweets")
    
    # Show sample tweets
    for i, tweet in enumerate(tweets_response['data'][:3]):
        print(f"Tweet {i+1}: {tweet['text']}")
        
    print("\n✅ Simulation test complete!")
