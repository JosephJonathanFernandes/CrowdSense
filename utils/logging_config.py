import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from core.database import log_to_database


class DatabaseHandler(logging.Handler):
    """Custom logging handler that logs to database"""
    
    def emit(self, record):
        """Emit a log record to the database"""
        try:
            # Extract extra data from the record
            extra_data = {}
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                              'pathname', 'filename', 'module', 'lineno', 
                              'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process',
                              'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    extra_data[key] = value
            
            # Log to database
            log_to_database(
                level=record.levelname,
                module=record.module,
                message=record.getMessage(),
                extra_data=extra_data if extra_data else None
            )
        except Exception:
            # Avoid infinite recursion if database logging fails
            pass


class MetricsCollector:
    """Collect and track application metrics"""
    
    def __init__(self):
        self.metrics = {
            'tweets_processed': 0,
            'alerts_sent': 0,
            'anomalies_detected': 0,
            'api_requests': 0,
            'errors': 0,
            'locations_extracted': 0,
            'geocoding_requests': 0,
            'start_time': datetime.utcnow()
        }
        self.logger = logging.getLogger('metrics')
    
    def increment(self, metric_name: str, value: int = 1):
        """Increment a metric counter"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
            self.logger.debug(f"Metric {metric_name} incremented by {value} to {self.metrics[metric_name]}")
    
    def set_metric(self, metric_name: str, value: Any):
        """Set a metric value"""
        self.metrics[metric_name] = value
        self.logger.debug(f"Metric {metric_name} set to {value}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all current metrics"""
        # Calculate uptime
        uptime = datetime.utcnow() - self.metrics['start_time']
        runtime_metrics = {
            **self.metrics,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0]  # Remove microseconds
        }
        return runtime_metrics
    
    def log_metrics(self):
        """Log current metrics"""
        metrics = self.get_metrics()
        self.logger.info("Current metrics", extra={'metrics': metrics})
    
    def reset_counters(self):
        """Reset counter metrics (keep start_time)"""
        start_time = self.metrics['start_time']
        self.metrics = {
            'tweets_processed': 0,
            'alerts_sent': 0,
            'anomalies_detected': 0,
            'api_requests': 0,
            'errors': 0,
            'locations_extracted': 0,
            'geocoding_requests': 0,
            'start_time': start_time
        }


# Global metrics collector instance
metrics = MetricsCollector()


def setup_logging(level: str = 'INFO', enable_db_logging: bool = True):
    """
    Setup structured logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_db_logging: Whether to enable database logging
    """
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('crowdsense.log')
        ]
    )
    
    # Add database handler if enabled
    if enable_db_logging:
        db_handler = DatabaseHandler()
        db_handler.setLevel(logging.WARNING)  # Only log warnings and errors to DB
        logging.getLogger().addHandler(db_handler)
    
    # Set up specific loggers
    loggers = {
        'crowdsense': logging.INFO,
        'anomaly_detection': logging.INFO,
        'location_extraction': logging.INFO,
        'database': logging.INFO,
        'metrics': logging.INFO,
        'scheduler': logging.INFO
    }
    
    for logger_name, logger_level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logging.info("Structured logging initialized")


class ContextLogger:
    """Logger with context information"""
    
    def __init__(self, name: str, context: Dict[str, Any] = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context"""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
        metrics.increment('errors')
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)
        metrics.increment('errors')


def get_logger(name: str, context: Dict[str, Any] = None) -> ContextLogger:
    """Get a context logger instance"""
    return ContextLogger(name, context)


def log_tweet_processed(keyword: str, tweet_count: int):
    """Log tweet processing metrics"""
    logger = get_logger('crowdsense.tweets')
    logger.info(f"Processed tweets for keyword: {keyword}", 
                keyword=keyword, tweet_count=tweet_count)
    metrics.increment('tweets_processed', tweet_count)


def log_alert_sent(keyword: str, message: str, sms_sid: str = None):
    """Log alert sending"""
    logger = get_logger('crowdsense.alerts')
    logger.info(f"Alert sent for keyword: {keyword}", 
                keyword=keyword, sms_sid=sms_sid, message_length=len(message))
    metrics.increment('alerts_sent')


def log_anomaly_detected(keyword: str, z_score: float, tweet_count: int):
    """Log anomaly detection"""
    logger = get_logger('crowdsense.anomaly')
    logger.warning(f"Anomaly detected for keyword: {keyword}",
                   keyword=keyword, z_score=z_score, tweet_count=tweet_count)
    metrics.increment('anomalies_detected')


def log_location_extracted(location: str, latitude: float = None, longitude: float = None):
    """Log location extraction"""
    logger = get_logger('crowdsense.location')
    logger.info(f"Location extracted: {location}",
                location=location, latitude=latitude, longitude=longitude)
    metrics.increment('locations_extracted')


def log_api_request(api_name: str, status_code: int = None, response_time: float = None):
    """Log API requests"""
    logger = get_logger('crowdsense.api')
    logger.debug(f"API request to {api_name}",
                 api_name=api_name, status_code=status_code, response_time=response_time)
    metrics.increment('api_requests')


def log_error(module: str, error: Exception, context: Dict[str, Any] = None):
    """Log errors with context"""
    logger = get_logger(f'crowdsense.{module}')
    error_context = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        **(context or {})
    }
    logger.error(f"Error in {module}: {error}", **error_context)


if __name__ == "__main__":
    # Test logging setup
    setup_logging('DEBUG')
    
    logger = get_logger('test', {'component': 'test_module'})
    logger.info("Test log message")
    logger.error("Test error message", error_code=500)
    
    # Test metrics
    metrics.increment('tweets_processed', 5)
    metrics.increment('alerts_sent')
    print("Current metrics:", metrics.get_metrics())
