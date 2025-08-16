import spacy
import re
from typing import Dict, List, Tuple, Optional
import logging
import requests
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

# Load spaCy model for NER
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("SpaCy model loaded successfully")
except OSError:
    logger.error("SpaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None


class LocationExtractor:
    """Extract and geocode locations from tweet text"""
    
    def __init__(self):
        self.geocoding_cache = {}
        self.rate_limit_delay = 1  # Delay between geocoding requests
        self.last_request_time = 0
        
    def extract_locations_from_text(self, text: str) -> List[str]:
        """
        Extract location entities from text using NER
        
        Args:
            text: Tweet text to analyze
            
        Returns:
            List of location strings found in the text
        """
        if not nlp:
            return self._extract_locations_regex(text)
            
        try:
            doc = nlp(text)
            locations = []
            
            # Extract named entities of type GPE (Geopolitical entity), LOC (Location)
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:
                    location = ent.text.strip()
                    if len(location) > 2:  # Filter out very short matches
                        locations.append(location)
                        
            # Remove duplicates while preserving order
            seen = set()
            unique_locations = []
            for loc in locations:
                if loc.lower() not in seen:
                    seen.add(loc.lower())
                    unique_locations.append(loc)
                    
            logger.debug(f"Extracted locations from '{text[:50]}...': {unique_locations}")
            return unique_locations
            
        except Exception as e:
            logger.error(f"Error in NER location extraction: {e}")
            return self._extract_locations_regex(text)
    
    def _extract_locations_regex(self, text: str) -> List[str]:
        """
        Fallback regex-based location extraction
        
        Args:
            text: Tweet text to analyze
            
        Returns:
            List of potential location strings
        """
        # Common location patterns
        patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:City|Town|District|State|Province|County))\b',
            r'\b(?:in|at|from|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+)\b',  # City, State pattern
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    locations.extend([m.strip() for m in match if m.strip()])
                else:
                    locations.append(match.strip())
        
        # Filter common non-location words
        filter_words = {'Twitter', 'Facebook', 'Instagram', 'News', 'Today', 'Now', 'Live'}
        locations = [loc for loc in locations if loc not in filter_words and len(loc) > 2]
        
        return list(set(locations))  # Remove duplicates
    
    @lru_cache(maxsize=1000)
    def geocode_location(self, location: str) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude for a location string
        
        Args:
            location: Location name to geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        if location in self.geocoding_cache:
            return self.geocoding_cache[location]
            
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_request_time < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay)
        
        try:
            # Using OpenStreetMap Nominatim API (free)
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': location,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'CrowdSense-DisasterAlert/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    coordinates = (lat, lon)
                    
                    # Cache the result
                    self.geocoding_cache[location] = coordinates
                    logger.debug(f"Geocoded {location} -> {coordinates}")
                    return coordinates
                    
        except Exception as e:
            logger.error(f"Error geocoding location '{location}': {e}")
            
        # Cache negative results to avoid repeated requests
        self.geocoding_cache[location] = None
        return None
    
    def extract_and_geocode(self, text: str) -> Dict[str, any]:
        """
        Extract locations from text and geocode the most likely one
        
        Args:
            text: Tweet text to analyze
            
        Returns:
            Dictionary with location info
        """
        locations = self.extract_locations_from_text(text)
        
        result = {
            'locations_found': locations,
            'primary_location': None,
            'latitude': None,
            'longitude': None
        }
        
        if not locations:
            return result
            
        # Try to geocode the first (most prominent) location
        primary_location = locations[0]
        coordinates = self.geocode_location(primary_location)
        
        if coordinates:
            result.update({
                'primary_location': primary_location,
                'latitude': coordinates[0],
                'longitude': coordinates[1]
            })
        else:
            # Try other locations if first one fails
            for location in locations[1:]:
                coordinates = self.geocode_location(location)
                if coordinates:
                    result.update({
                        'primary_location': location,
                        'latitude': coordinates[0],
                        'longitude': coordinates[1]
                    })
                    break
                    
        return result


# Global instance
location_extractor = LocationExtractor()


def extract_location_from_tweet(tweet_text: str) -> Dict[str, any]:
    """
    Convenience function to extract location from tweet text
    
    Args:
        tweet_text: The text content of the tweet
        
    Returns:
        Dictionary with location extraction results
    """
    return location_extractor.extract_and_geocode(tweet_text)


def get_sample_locations() -> List[Dict[str, any]]:
    """Get sample location data for testing"""
    return [
        {
            'text': 'Heavy flooding in Mumbai, Maharashtra causing major disruptions',
            'latitude': 19.0760, 
            'longitude': 72.8777,
            'location': 'Mumbai'
        },
        {
            'text': 'Earthquake reported in San Francisco Bay Area',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'location': 'San Francisco'
        },
        {
            'text': 'Severe storm warning for Houston, Texas',
            'latitude': 29.7604,
            'longitude': -95.3698,
            'location': 'Houston'
        },
        {
            'text': 'Wildfire evacuation orders in Los Angeles County',
            'latitude': 34.0522,
            'longitude': -118.2437,
            'location': 'Los Angeles'
        },
        {
            'text': 'Tsunami alert issued for coastal areas of Tokyo',
            'latitude': 35.6762,
            'longitude': 139.6503,
            'location': 'Tokyo'
        }
    ]


if __name__ == "__main__":
    # Test the location extractor
    extractor = LocationExtractor()
    
    test_tweets = [
        "Breaking: Major earthquake hits San Francisco, buildings swaying downtown",
        "Flooding reported in Mumbai's Bandra area, trains suspended",
        "Wildfire spreads near Los Angeles, evacuation orders issued",
        "Storm warning for Houston, Texas - stay indoors",
        "Heavy rains causing waterlogging in Delhi NCR region"
    ]
    
    for tweet in test_tweets:
        print(f"\nTweet: {tweet}")
        result = extractor.extract_and_geocode(tweet)
        print(f"Result: {result}")
