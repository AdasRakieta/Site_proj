"""
Background scheduler for SmartHome tasks
Runs periodic tasks like city cache updates
"""
import logging
import schedule
import time
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    """Background task scheduler for periodic jobs"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting background scheduler...")
        
        # Background tasks can be added here in the future
        # Example: schedule.every().monday.at("22:00").do(self._some_task)
        
        self.running = True
        self.thread = threading.Thread(target=self._run_schedule, daemon=True)
        self.thread.start()
        
        logger.info("Background scheduler started successfully")
    
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        schedule.clear()
        logger.info("Background scheduler stopped")
    
    def _run_schedule(self):
        """Run the scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

# Global scheduler instance
scheduler = BackgroundScheduler()
