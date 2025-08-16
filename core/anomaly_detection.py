import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from core.database import get_tweet_metrics_history, save_tweet_metrics

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Smart anomaly detection using Z-score and EWMA"""
    
    def __init__(self, window_size: int = 10, ewma_alpha: float = 0.3, 
                 z_threshold: float = 2.0):
        """
        Initialize anomaly detector
        
        Args:
            window_size: Number of historical windows to consider for Z-score
            ewma_alpha: Smoothing factor for EWMA (0-1)
            z_threshold: Z-score threshold for anomaly detection
        """
        self.window_size = window_size
        self.ewma_alpha = ewma_alpha
        self.z_threshold = z_threshold
        
        # Historical data for each keyword
        self.keyword_history: Dict[str, deque] = {}
        self.keyword_ewma: Dict[str, float] = {}
        
    def update_history(self, keyword: str, count: int) -> Tuple[float, float, bool]:
        """
        Update historical data and detect anomalies
        
        Args:
            keyword: The keyword being monitored
            count: Current count of tweets for this keyword
            
        Returns:
            Tuple of (z_score, ewma_value, is_anomaly)
        """
        # Initialize history for new keywords
        if keyword not in self.keyword_history:
            self.keyword_history[keyword] = deque(maxlen=self.window_size)
            self.keyword_ewma[keyword] = count
            
        # Add current count to history
        self.keyword_history[keyword].append(count)
        
        # Calculate Z-score
        z_score = self._calculate_z_score(keyword, count)
        
        # Update EWMA
        if keyword in self.keyword_ewma:
            self.keyword_ewma[keyword] = (
                self.ewma_alpha * count + 
                (1 - self.ewma_alpha) * self.keyword_ewma[keyword]
            )
        else:
            self.keyword_ewma[keyword] = count
            
        ewma_value = self.keyword_ewma[keyword]
        
        # Detect anomaly using both Z-score and EWMA
        is_anomaly = self._is_anomaly(z_score, count, ewma_value)
        
        logger.info(f"Keyword: {keyword}, Count: {count}, Z-score: {z_score:.2f}, "
                   f"EWMA: {ewma_value:.2f}, Anomaly: {is_anomaly}")
        
        return z_score, ewma_value, is_anomaly
    
    def _calculate_z_score(self, keyword: str, current_count: int) -> float:
        """Calculate Z-score for current count"""
        history = list(self.keyword_history[keyword])
        
        if len(history) < 2:
            return 0.0
            
        # Use historical data excluding current count
        historical_data = history[:-1] if len(history) > 1 else history
        
        if len(historical_data) == 0:
            return 0.0
            
        mean = np.mean(historical_data)
        std = np.std(historical_data)
        
        # Avoid division by zero
        if std == 0:
            return 0.0
            
        z_score = (current_count - mean) / std
        return float(z_score)
    
    def _is_anomaly(self, z_score: float, current_count: int, ewma_value: float) -> bool:
        """
        Determine if current measurement is an anomaly
        
        Uses combined approach:
        1. Z-score exceeds threshold
        2. Current count significantly exceeds EWMA
        """
        # Z-score based detection
        z_anomaly = abs(z_score) > self.z_threshold
        
        # EWMA based detection (current count is 50% higher than EWMA)
        ewma_anomaly = current_count > ewma_value * 1.5 and ewma_value > 0
        
        # Require both conditions for stronger signal
        return z_anomaly and ewma_anomaly
    
    def load_historical_data(self, keyword: str, hours: int = 24):
        """Load historical data from database"""
        try:
            history = get_tweet_metrics_history(keyword, hours)
            
            if not history:
                return
                
            # Load historical counts
            counts = [record['count'] for record in history[-self.window_size:]]
            self.keyword_history[keyword] = deque(counts, maxlen=self.window_size)
            
            # Initialize EWMA with most recent value or average
            if history:
                recent_counts = [record['count'] for record in history[-5:]]
                self.keyword_ewma[keyword] = np.mean(recent_counts)
                
            logger.info(f"Loaded {len(counts)} historical data points for {keyword}")
            
        except Exception as e:
            logger.error(f"Error loading historical data for {keyword}: {e}")


class AdaptiveThresholdDetector:
    """Alternative detector using adaptive thresholds"""
    
    def __init__(self, base_threshold: int = 5, adaptation_rate: float = 0.1):
        """
        Initialize adaptive threshold detector
        
        Args:
            base_threshold: Starting threshold value
            adaptation_rate: Rate at which threshold adapts
        """
        self.base_threshold = base_threshold
        self.adaptation_rate = adaptation_rate
        self.keyword_thresholds: Dict[str, float] = {}
        self.keyword_averages: Dict[str, float] = {}
        
    def update_threshold(self, keyword: str, count: int) -> Tuple[float, bool]:
        """
        Update adaptive threshold and check for anomaly
        
        Args:
            keyword: The keyword being monitored
            count: Current count of tweets
            
        Returns:
            Tuple of (current_threshold, is_anomaly)
        """
        # Initialize threshold for new keywords
        if keyword not in self.keyword_thresholds:
            self.keyword_thresholds[keyword] = float(self.base_threshold)
            self.keyword_averages[keyword] = float(count)
            
        # Update running average
        if keyword in self.keyword_averages:
            self.keyword_averages[keyword] = (
                self.adaptation_rate * count + 
                (1 - self.adaptation_rate) * self.keyword_averages[keyword]
            )
        
        # Adapt threshold based on recent average
        avg = self.keyword_averages[keyword]
        self.keyword_thresholds[keyword] = max(
            self.base_threshold,
            avg * 2.0  # Threshold is 2x the running average
        )
        
        current_threshold = self.keyword_thresholds[keyword]
        is_anomaly = count >= current_threshold
        
        logger.info(f"Adaptive - Keyword: {keyword}, Count: {count}, "
                   f"Threshold: {current_threshold:.2f}, Anomaly: {is_anomaly}")
        
        return current_threshold, is_anomaly


def create_anomaly_detector(method: str = "zscore") -> AnomalyDetector:
    """Factory function to create anomaly detector"""
    if method == "zscore":
        return AnomalyDetector(
            window_size=15,    # Look at last 15 windows
            ewma_alpha=0.3,    # Moderate smoothing
            z_threshold=2.5    # 2.5 standard deviations
        )
    elif method == "adaptive":
        return AdaptiveThresholdDetector(
            base_threshold=5,
            adaptation_rate=0.15
        )
    else:
        raise ValueError(f"Unknown anomaly detection method: {method}")


if __name__ == "__main__":
    # Test the anomaly detector
    detector = AnomalyDetector()
    
    # Simulate tweet counts
    test_data = [2, 3, 1, 4, 2, 3, 15, 2, 1, 3]  # 15 is an anomaly
    
    for i, count in enumerate(test_data):
        z_score, ewma, is_anomaly = detector.update_history("test", count)
        print(f"Time {i}: Count={count}, Z-score={z_score:.2f}, "
              f"EWMA={ewma:.2f}, Anomaly={is_anomaly}")
