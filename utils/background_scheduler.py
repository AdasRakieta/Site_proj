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
        
        # Schedule city cache update every Monday at 22:00
        schedule.every().monday.at("22:00").do(self._update_city_cache)
        
        # Check if we need to run initial update (if cache is empty)
        self._check_initial_update()
        
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
    
    def _update_city_cache(self):
        """Update city cache - scheduled task"""
        try:
            logger.info("=" * 50)
            logger.info("Scheduled city cache update starting...")
            logger.info(f"Time: {datetime.now()}")
            logger.info("=" * 50)
            
            from utils.city_cache_updater import CityCacheUpdater
            updater = CityCacheUpdater()
            success = updater.update_city_cache()
            
            if success:
                status = updater.get_cache_status()
                logger.info(f"City cache updated successfully! Cities: {status.get('cities_count', 0)}")
            else:
                logger.error("City cache update failed!")
            
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Error in scheduled city cache update: {e}", exc_info=True)
    
    def _check_initial_update(self):
        """Check if we need to run initial city cache update"""
        try:
            from utils.city_cache_updater import CityCacheUpdater
            updater = CityCacheUpdater()
            status = updater.get_cache_status()
            
            if not status or status.get('cities_count', 0) == 0:
                logger.info("City cache is empty, running initial update...")
                self._update_city_cache()
            else:
                logger.info(f"City cache already populated with {status.get('cities_count', 0)} cities")
                logger.info(f"Last updated: {status.get('last_updated')}")
        
        except Exception as e:
            logger.error(f"Error checking initial cache status: {e}")

# Global scheduler instance
scheduler = BackgroundScheduler()
