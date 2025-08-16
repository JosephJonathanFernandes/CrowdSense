import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Dict, Any
import signal
from utils.logging_config import get_logger, metrics

logger = get_logger('scheduler')


class BackgroundScheduler:
    """Background task scheduler to replace while True loops"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        self.tasks = {}
        self.task_stats = {}
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def add_task(self, name: str, func: Callable, interval_minutes: int = 1, 
                 run_immediately: bool = False):
        """
        Add a scheduled task
        
        Args:
            name: Unique name for the task
            func: Function to execute
            interval_minutes: Interval in minutes between executions
            run_immediately: Whether to run the task immediately on start
        """
        # Store task info
        self.tasks[name] = {
            'func': func,
            'interval_minutes': interval_minutes,
            'run_immediately': run_immediately,
            'last_run': None,
            'next_run': None,
            'run_count': 0,
            'error_count': 0
        }
        
        # Schedule the task
        job = schedule.every(interval_minutes).minutes.do(self._run_task, name)
        
        # Store job reference for potential cancellation
        self.tasks[name]['job'] = job
        
        logger.info(f"Task '{name}' scheduled to run every {interval_minutes} minutes",
                   task_name=name, interval=interval_minutes)
        
        # Run immediately if requested
        if run_immediately:
            self._run_task(name)
    
    def _run_task(self, task_name: str):
        """Execute a scheduled task with error handling and metrics"""
        if task_name not in self.tasks:
            logger.error(f"Task '{task_name}' not found", task_name=task_name)
            return
            
        task_info = self.tasks[task_name]
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Starting task: {task_name}", task_name=task_name)
            
            # Execute the task function
            result = task_info['func']()
            
            # Update task statistics
            task_info['last_run'] = start_time
            task_info['run_count'] += 1
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Task '{task_name}' completed successfully",
                       task_name=task_name, 
                       execution_time=execution_time,
                       run_count=task_info['run_count'])
            
            # Store execution stats
            if task_name not in self.task_stats:
                self.task_stats[task_name] = []
            
            self.task_stats[task_name].append({
                'start_time': start_time,
                'execution_time': execution_time,
                'success': True,
                'result': result
            })
            
            # Keep only last 100 runs
            self.task_stats[task_name] = self.task_stats[task_name][-100:]
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            task_info['error_count'] += 1
            
            logger.error(f"Task '{task_name}' failed",
                        task_name=task_name,
                        error=str(e),
                        execution_time=execution_time,
                        error_count=task_info['error_count'])
            
            # Store error stats
            if task_name not in self.task_stats:
                self.task_stats[task_name] = []
                
            self.task_stats[task_name].append({
                'start_time': start_time,
                'execution_time': execution_time,
                'success': False,
                'error': str(e)
            })
    
    def start(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        
        def run_scheduler():
            logger.info("Background scheduler started")
            while self.running:
                try:
                    schedule.run_pending()
                    time.sleep(1)  # Check every second
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(5)  # Wait a bit before retrying
                    
            logger.info("Background scheduler stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Background scheduler initialized with {} tasks".format(len(self.tasks)))
    
    def stop(self):
        """Stop the background scheduler"""
        logger.info("Stopping background scheduler...")
        self.running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=10)
            
        logger.info("Background scheduler stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all scheduled tasks"""
        status = {}
        
        for task_name, task_info in self.tasks.items():
            recent_stats = self.task_stats.get(task_name, [])
            recent_runs = recent_stats[-10:]  # Last 10 runs
            
            # Calculate success rate
            if recent_runs:
                successful_runs = sum(1 for run in recent_runs if run['success'])
                success_rate = successful_runs / len(recent_runs) * 100
                avg_execution_time = sum(run['execution_time'] for run in recent_runs) / len(recent_runs)
            else:
                success_rate = 0
                avg_execution_time = 0
            
            status[task_name] = {
                'interval_minutes': task_info['interval_minutes'],
                'last_run': task_info['last_run'].isoformat() if task_info['last_run'] else None,
                'run_count': task_info['run_count'],
                'error_count': task_info['error_count'],
                'success_rate': round(success_rate, 2),
                'avg_execution_time': round(avg_execution_time, 3),
                'recent_runs': len(recent_runs)
            }
        
        return status
    
    def remove_task(self, task_name: str):
        """Remove a scheduled task"""
        if task_name in self.tasks:
            # Cancel the scheduled job
            schedule.cancel_job(self.tasks[task_name]['job'])
            
            # Remove from tracking
            del self.tasks[task_name]
            if task_name in self.task_stats:
                del self.task_stats[task_name]
                
            logger.info(f"Task '{task_name}' removed from scheduler", task_name=task_name)
        else:
            logger.warning(f"Task '{task_name}' not found for removal", task_name=task_name)


# Global scheduler instance
scheduler = BackgroundScheduler()


def start_crowdsense_scheduler():
    """Start the CrowdSense background scheduler with all tasks"""
    from core.crowdsense_enhanced import fetch_and_analyze_tweets
    
    # Add the main tweet fetching task
    scheduler.add_task(
        name="fetch_tweets",
        func=fetch_and_analyze_tweets,
        interval_minutes=1,  # Run every minute
        run_immediately=True
    )
    
    # Add metrics logging task
    def log_metrics():
        metrics.log_metrics()
        return "Metrics logged"
    
    scheduler.add_task(
        name="log_metrics",
        func=log_metrics,
        interval_minutes=15,  # Log metrics every 15 minutes
        run_immediately=False
    )
    
    # Add database cleanup task
    def cleanup_old_data():
        """Clean up old data from database"""
        try:
            from core.database import get_db_connection
            with get_db_connection() as conn:
                # Delete tweets older than 7 days
                conn.execute("""
                    DELETE FROM tweets 
                    WHERE created_at < datetime('now', '-7 days')
                """)
                
                # Delete tweet metrics older than 30 days
                conn.execute("""
                    DELETE FROM tweet_metrics 
                    WHERE created_at < datetime('now', '-30 days')
                """)
                
                # Delete system logs older than 30 days
                conn.execute("""
                    DELETE FROM system_logs 
                    WHERE created_at < datetime('now', '-30 days')
                """)
                
                conn.commit()
                return "Database cleanup completed"
        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return f"Database cleanup failed: {e}"
    
    scheduler.add_task(
        name="database_cleanup",
        func=cleanup_old_data,
        interval_minutes=60 * 24,  # Run daily
        run_immediately=False
    )
    
    # Start the scheduler
    scheduler.start()
    
    logger.info("CrowdSense scheduler started with all tasks")
    return scheduler


if __name__ == "__main__":
    # Test the scheduler
    def test_task():
        print(f"Test task executed at {datetime.now()}")
        return "Test completed"
    
    scheduler.add_task("test", test_task, interval_minutes=1, run_immediately=True)
    scheduler.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(10)
            print("Scheduler status:", scheduler.get_task_status())
    except KeyboardInterrupt:
        scheduler.stop()
