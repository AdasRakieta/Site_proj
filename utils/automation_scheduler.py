"""
Automation Scheduler - handles time-based automation triggers
"""
import logging
from datetime import datetime, time as dt_time
from threading import Thread
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AutomationScheduler:
    """Handles time-based automation execution"""
    
    def __init__(self, multi_db, automation_executor):
        """
        Initialize AutomationScheduler
        
        Args:
            multi_db: MultiHomeDBManager instance
            automation_executor: AutomationExecutor instance
        """
        self.multi_db = multi_db
        self.automation_executor = automation_executor
        self.running = False
        self.scheduler_thread = None
        logger.info("[SCHEDULER] AutomationScheduler initialized")
    
    def start(self):
        """Start the scheduler background thread"""
        if self.running:
            logger.warning("[SCHEDULER] Already running")
            return
        
        self.running = True
        self.scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("[SCHEDULER] Started time-based automation scheduler")
    
    def stop(self):
        """Stop the scheduler background thread"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("[SCHEDULER] Stopped automation scheduler")
    
    def _scheduler_loop(self):
        """Main scheduler loop - runs every minute"""
        last_minute = -1
        
        while self.running:
            try:
                now = datetime.now()
                current_minute = now.minute
                
                # Only process once per minute
                if current_minute != last_minute:
                    last_minute = current_minute
                    self._check_time_automations(now)
                
                # Sleep for 60 seconds before next check
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"[SCHEDULER] Error in scheduler loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait a minute before retrying on error
    
    def _check_time_automations(self, now: datetime):
        """
        Check and execute time-based automations
        
        Args:
            now: Current datetime
        """
        if not self.multi_db:
            return
        
        # Skip if in JSON fallback mode (no database available)
        if hasattr(self.multi_db, 'json_fallback_mode') and self.multi_db.json_fallback_mode:
            return
        
        try:
            # Get all enabled automations from all homes (use home_automations table)
            with self.multi_db.get_cursor() as cursor:
                if not cursor:  # Safety check for None cursor
                    return
                    
                cursor.execute("""
                    SELECT a.id, a.home_id, a.name, a.trigger_config, a.actions_config, a.enabled
                    FROM home_automations a
                    WHERE a.enabled = true
                    AND a.trigger_config->>'type' = 'time'
                """)
                automations = cursor.fetchall()
            
            current_time = now.strftime('%H:%M')
            # Map weekday to 3-letter abbreviation used in frontend (mon, tue, wed, etc.)
            weekday_map = {
                'monday': 'mon',
                'tuesday': 'tue', 
                'wednesday': 'wed',
                'thursday': 'thu',
                'friday': 'fri',
                'saturday': 'sat',
                'sunday': 'sun'
            }
            current_weekday_full = now.strftime('%A').lower()  # monday, tuesday, etc.
            current_weekday = weekday_map.get(current_weekday_full, current_weekday_full)
            
            logger.debug(f"[SCHEDULER] Checking {len(automations)} time-based automations at {current_time} ({current_weekday})")
            
            for automation in automations:
                try:
                    automation_dict = {
                        'id': automation[0],
                        'home_id': automation[1],
                        'name': automation[2],
                        'trigger_config': automation[3],
                        'actions_config': automation[4],
                        'enabled': automation[5]
                    }
                    
                    trigger = automation_dict.get('trigger_config', {})
                    if not trigger:
                        continue
                    
                    # Check if time matches
                    trigger_time = trigger.get('time', '')
                    if trigger_time != current_time:
                        logger.debug(f"[SCHEDULER] ⏭ Automation '{automation_dict['name']}' - time mismatch: {trigger_time} != {current_time}")
                        continue
                    
                    # Check if day matches
                    trigger_days = trigger.get('days', [])
                    if trigger_days and current_weekday not in trigger_days:
                        logger.info(f"[SCHEDULER] ⏭ Skipping automation '{automation_dict['name']}' - day mismatch: {current_weekday} not in {trigger_days}")
                        continue
                    
                    # Execute automation
                    logger.info(f"[SCHEDULER] ✓ Executing time-based automation: {automation_dict['name']} at {current_time} on {current_weekday}")
                    
                    # Get a user from this home to use for execution context
                    user_id = self._get_home_user(automation_dict['home_id'])
                    if not user_id:
                        logger.warning(f"[SCHEDULER] No user found for home {automation_dict['home_id']}, skipping automation")
                        continue
                    
                    result = self.automation_executor._execute_automation(
                        automation=automation_dict,
                        home_id=automation_dict['home_id'],
                        user_id=user_id,
                        trigger_data={
                            'trigger_type': 'time',
                            'time': current_time,
                            'weekday': current_weekday
                        }
                    )
                    
                    logger.info(f"[SCHEDULER] Automation '{automation_dict['name']}' result: {result['status']}")
                    
                except Exception as automation_error:
                    logger.error(f"[SCHEDULER] Error executing automation: {automation_error}")
                    import traceback
                    traceback.print_exc()
            
        except Exception as e:
            logger.error(f"[SCHEDULER] Error checking time automations: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_home_user(self, home_id: str) -> Optional[str]:
        """
        Get any user ID that has access to this home
        
        Args:
            home_id: Home UUID
            
        Returns:
            User UUID or None
        """
        try:
            with self.multi_db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT user_id
                    FROM user_homes
                    WHERE home_id = %s
                    LIMIT 1
                """, (home_id,))
                result = cursor.fetchone()
                return str(result[0]) if result else None
        except Exception as e:
            logger.error(f"[SCHEDULER] Error getting home user: {e}")
            return None
