"""
Asynchronous mail manager for Site_proj
Provides non-blocking email sending capabilities
"""
import asyncio
import aiosmtplib
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from queue import Queue
import logging

logger = logging.getLogger(__name__)


class AsyncMailManager:
    """
    Asynchronous mail manager that handles email sending in background
    """
    
    def __init__(self, mail_manager):
        """
        Initialize with existing mail_manager configuration
        """
        self.mail_manager = mail_manager
        self.config = mail_manager.config
        self.smtp_config = mail_manager.smtp_config
        self.mail_queue = Queue()
        self.worker_thread = None
        self.stop_worker = False
        self.start_worker()
    
    def start_worker(self):
        """Start the background worker thread"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_worker = False
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Async mail worker started")
    
    def stop(self):
        """Stop the background worker"""
        self.stop_worker = True
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
    
    def _worker_loop(self):
        """Background worker loop to process mail queue"""
        while not self.stop_worker:
            try:
                # Check for new mail tasks
                if not self.mail_queue.empty():
                    mail_task = self.mail_queue.get(timeout=1.0)
                    self._process_mail_task(mail_task)
                else:
                    # Sleep briefly if no tasks
                    threading.Event().wait(0.1)
            except Exception as e:
                logger.error(f"Error in mail worker: {e}")
                threading.Event().wait(1.0)  # Wait longer on error
    
    def _process_mail_task(self, mail_task):
        """Process a single mail task"""
        try:
            task_type = mail_task.get('type')
            
            if task_type == 'verification':
                self._send_verification_email_sync(
                    mail_task['email'], 
                    mail_task['code']
                )
            elif task_type == 'security_alert':
                self._send_security_alert_sync(
                    mail_task['event_type'],
                    mail_task['details']
                )
            elif task_type == 'failed_login_alert':
                self._send_failed_login_alert_sync(
                    mail_task['username'],
                    mail_task['ip_address']
                )
            
            logger.info(f"Processed mail task: {task_type}")
            
        except Exception as e:
            logger.error(f"Failed to process mail task: {e}")
    
    def send_verification_email_async(self, email, code):
        """
        Queue verification email to be sent asynchronously
        """
        mail_task = {
            'type': 'verification',
            'email': email,
            'code': code,
            'timestamp': datetime.now()
        }
        self.mail_queue.put(mail_task)
        logger.info(f"Queued verification email for {email}")
        return True  # Return immediately, email will be sent in background
    
    def send_security_alert_async(self, event_type, details):
        """
        Queue security alert to be sent asynchronously
        """
        mail_task = {
            'type': 'security_alert',
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now()
        }
        self.mail_queue.put(mail_task)
        logger.info(f"Queued security alert: {event_type}")
        return True
    
    def track_and_alert_failed_login_async(self, username, ip_address):
        """
        Queue failed login alert to be sent asynchronously
        """
        mail_task = {
            'type': 'failed_login_alert',
            'username': username,
            'ip_address': ip_address,
            'timestamp': datetime.now()
        }
        self.mail_queue.put(mail_task)
        logger.info(f"Queued failed login alert for {username} from {ip_address}")
        return True
    
    def _send_verification_email_sync(self, email, code):
        """
        Send verification email synchronously (used by worker)
        """
        try:
            # Use the original mail_manager method but with better error handling
            return self.mail_manager.send_verification_email(email, code)
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False
    
    def _send_security_alert_sync(self, event_type, details):
        """
        Send security alert synchronously (used by worker)
        """
        try:
            return self.mail_manager.send_security_alert(event_type, details)
        except Exception as e:
            logger.error(f"Failed to send security alert {event_type}: {e}")
            return False
    
    def _send_failed_login_alert_sync(self, username, ip_address):
        """
        Send failed login alert synchronously (used by worker)
        """
        try:
            return self.mail_manager.track_and_alert_failed_login(username, ip_address)
        except Exception as e:
            logger.error(f"Failed to send failed login alert for {username}: {e}")
            return False
    
    # Fallback methods for immediate sending when needed
    def send_verification_email(self, email, code):
        """Fallback to immediate sending if needed"""
        return self.mail_manager.send_verification_email(email, code)
    
    def send_security_alert(self, event_type, details):
        """Fallback to immediate sending if needed"""
        return self.mail_manager.send_security_alert(event_type, details)
    
    def track_and_alert_failed_login(self, username, ip_address):
        """Fallback to immediate sending if needed"""
        return self.mail_manager.track_and_alert_failed_login(username, ip_address)
    
    def get_queue_size(self):
        """Get the current size of the mail queue"""
        return self.mail_queue.qsize()


class BackgroundTaskManager:
    """
    Manager for running background tasks asynchronously
    """
    
    def __init__(self):
        self.tasks = []
        self.executor = None
        self.stop_tasks = False
    
    def add_task(self, func, *args, **kwargs):
        """Add a task to be executed in background"""
        task = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'created_at': datetime.now()
        }
        self.tasks.append(task)
    
    def start_background_processing(self):
        """Start processing background tasks"""
        import concurrent.futures
        
        if self.executor is None:
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        
        def process_tasks():
            while not self.stop_tasks:
                if self.tasks:
                    task = self.tasks.pop(0)
                    try:
                        self.executor.submit(task['func'], *task['args'], **task['kwargs'])
                    except Exception as e:
                        logger.error(f"Error submitting background task: {e}")
                threading.Event().wait(0.5)
        
        threading.Thread(target=process_tasks, daemon=True).start()
    
    def stop(self):
        """Stop background task processing"""
        self.stop_tasks = True
        if self.executor:
            self.executor.shutdown(wait=True)