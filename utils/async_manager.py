"""
Async Operations Manager for Site_proj

This file provides asynchronous operation capabilities for the smart home application.
It handles email sending, background tasks, and other non-blocking operations to
improve user experience and application responsiveness.

Features:
- Asynchronous email sending with queue-based processing
- Background task management for non-critical operations
- Thread-safe queue operations
- Graceful degradation to synchronous operations on failure
- Comprehensive error handling and logging

Email Operations:
- Verification emails are sent asynchronously to avoid blocking UI
- Security alerts are queued for background processing  
- Failed login notifications are handled in background
- All email operations fallback to synchronous mode if needed

Background Tasks:
- Non-critical operations are queued for background processing
- Thread pool executor for concurrent task execution
- Automatic task retry on failure
- Clean shutdown handling

Usage:
    Email operations are automatically asynchronous when using AsyncMailManager.
    Background tasks can be added to BackgroundTaskManager for deferred execution.
    
Dependencies:
    - Standard library threading and queue modules
    - Email configuration from existing MailManager
"""
import threading
import logging
from queue import Queue, Empty
from datetime import datetime
from typing import Optional, Callable, Any, Dict
import time

logger = logging.getLogger(__name__)


class AsyncMailManager:
    """
    Asynchronous mail manager that handles email sending in background threads
    
    This class wraps the existing MailManager to provide non-blocking email
    operations. All emails are queued and processed by a background worker thread.
    The original MailManager functionality is preserved 1:1 while adding
    asynchronous capabilities.
    
    Features:
    - Queue-based email processing
    - Background worker thread
    - Automatic fallback to synchronous operations
    - Thread-safe operations
    - Comprehensive error handling
    """
    
    def __init__(self, mail_manager):
        """
        Initialize with existing mail_manager configuration
        
        Args:
            mail_manager: Existing MailManager instance with SMTP configuration
        """
        self.mail_manager = mail_manager
        self.config = mail_manager.config
        self.smtp_config = mail_manager.smtp_config
        
        # Queue for email tasks
        self.mail_queue = Queue()
        
        # Worker thread management
        self.worker_thread = None
        self.stop_worker = False
        self.worker_active = False
        
        # Statistics
        self.emails_processed = 0
        self.emails_failed = 0
        
        # Start the background worker
        self.start_worker()
        logger.info("AsyncMailManager initialized")
    
    def start_worker(self):
        """Start the background worker thread"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.stop_worker = False
            self.worker_thread = threading.Thread(
                target=self._worker_loop, 
                daemon=True,
                name="AsyncMailWorker"
            )
            self.worker_thread.start()
            logger.info("Async mail worker started")
    
    def stop(self):
        """
        Stop the background worker gracefully
        Waits for current operations to complete
        """
        logger.info("Stopping async mail worker")
        self.stop_worker = True
        
        # Wait for worker to finish current tasks
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
            if self.worker_thread.is_alive():
                logger.warning("Worker thread did not stop gracefully")
            else:
                logger.info("Worker thread stopped successfully")
    
    def _worker_loop(self):
        """
        Background worker loop to process mail queue
        
        Continuously processes email tasks from the queue until
        stop_worker is set to True.
        """
        self.worker_active = True
        logger.info("Mail worker loop started")
        
        while not self.stop_worker:
            try:
                # Check for new mail tasks with timeout
                try:
                    mail_task = self.mail_queue.get(timeout=1.0)
                    self._process_mail_task(mail_task)
                    self.mail_queue.task_done()
                except Empty:
                    # No tasks in queue, continue loop
                    continue
                    
            except Exception as e:
                logger.error(f"Error in mail worker loop: {e}")
                # Sleep on error to prevent tight error loops
                time.sleep(1.0)
        
        self.worker_active = False
        logger.info("Mail worker loop stopped")
    
    def _process_mail_task(self, mail_task: Dict[str, Any]):
        """
        Process a single mail task
        
        Args:
            mail_task: Dictionary containing task type and parameters
        """
        try:
            task_type = mail_task.get('type')
            timestamp = mail_task.get('timestamp', datetime.now())
            
            logger.debug(f"Processing mail task: {task_type} from {timestamp}")
            
            success = False
            if task_type == 'verification':
                success = self._send_verification_email_sync(
                    mail_task['email'], 
                    mail_task['code']
                )
            elif task_type == 'security_alert':
                success = self._send_security_alert_sync(
                    mail_task['event_type'],
                    mail_task['details']
                )
            elif task_type == 'failed_login_alert':
                success = self._send_failed_login_alert_sync(
                    mail_task['username'],
                    mail_task['ip_address']
                )
            elif task_type == 'password_reset':
                success = self._send_password_reset_email_sync(
                    mail_task['email'],
                    mail_task['code']
                )
            else:
                logger.warning(f"Unknown mail task type: {task_type}")
                return
            
            if success:
                self.emails_processed += 1
                logger.info(f"Successfully processed mail task: {task_type}")
            else:
                self.emails_failed += 1
                logger.error(f"Failed to process mail task: {task_type}")
                
        except Exception as e:
            self.emails_failed += 1
            logger.error(f"Exception processing mail task: {e}")
    
    def _queue_mail_task(self, task_type: str, **kwargs) -> bool:
        """
        Queue a mail task for background processing
        
        Args:
            task_type: Type of email task
            **kwargs: Task-specific parameters
            
        Returns:
            True if task was queued successfully
        """
        try:
            mail_task = {
                'type': task_type,
                'timestamp': datetime.now(),
                **kwargs
            }
            self.mail_queue.put(mail_task)
            logger.debug(f"Queued mail task: {task_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue mail task {task_type}: {e}")
            return False
    
    # === ASYNC EMAIL METHODS ===
    
    def send_verification_email_async(self, email: str, code: str) -> bool:
        """
        Queue verification email to be sent asynchronously
        
        Args:
            email: Recipient email address
            code: Verification code
            
        Returns:
            True if email was queued successfully
        """
        return self._queue_mail_task('verification', email=email, code=code)
    
    def send_security_alert_async(self, event_type: str, details: str) -> bool:
        """
        Queue security alert to be sent asynchronously
        
        Args:
            event_type: Type of security event
            details: Event details
            
        Returns:
            True if alert was queued successfully
        """
        return self._queue_mail_task('security_alert', event_type=event_type, details=details)
    
    def track_and_alert_failed_login_async(self, username: str, ip_address: str) -> bool:
        """
        Queue failed login alert to be sent asynchronously
        
        Args:
            username: Username that failed login
            ip_address: IP address of failed attempt
            
        Returns:
            True if alert was queued successfully
        """
        return self._queue_mail_task('failed_login_alert', username=username, ip_address=ip_address)
    
    def send_password_reset_email_async(self, email: str, code: str) -> bool:
        """
        Queue password reset email to be sent asynchronously
        
        Args:
            email: Recipient email address
            code: Password reset verification code
            
        Returns:
            True if email was queued successfully
        """
        return self._queue_mail_task('password_reset', email=email, code=code)
    
    # === SYNC EMAIL METHODS (Internal) ===
    
    def _send_verification_email_sync(self, email: str, code: str) -> bool:
        """
        Send verification email synchronously (used by worker)
        
        Args:
            email: Recipient email address
            code: Verification code
            
        Returns:
            True if email was sent successfully
        """
        try:
            return self.mail_manager.send_verification_email(email, code)
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {e}")
            return False
    
    def _send_security_alert_sync(self, event_type: str, details: str) -> bool:
        """
        Send security alert synchronously (used by worker)
        
        Args:
            event_type: Type of security event
            details: Event details
            
        Returns:
            True if alert was sent successfully
        """
        try:
            return self.mail_manager.send_security_alert(event_type, details)
        except Exception as e:
            logger.error(f"Failed to send security alert {event_type}: {e}")
            return False
    
    def _send_failed_login_alert_sync(self, username: str, ip_address: str) -> bool:
        """
        Send failed login alert synchronously (used by worker)
        
        Args:
            username: Username that failed login
            ip_address: IP address of failed attempt
            
        Returns:
            True if alert was sent successfully
        """
        try:
            return self.mail_manager.track_and_alert_failed_login(username, ip_address)
        except Exception as e:
            logger.error(f"Failed to send failed login alert for {username}: {e}")
            return False

    def _send_password_reset_email_sync(self, email: str, code: str) -> bool:
        """
        Send password reset email synchronously (used by worker)
        
        Args:
            email: Recipient email address
            code: Password reset verification code
            
        Returns:
            True if email was sent successfully
        """
        try:
            return self.mail_manager.send_password_reset_email(email, code)
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            return False
    
    # === FALLBACK METHODS ===
    
    def send_verification_email(self, email: str, code: str) -> bool:
        """
        Fallback to immediate/synchronous sending if needed
        
        This method provides compatibility with the original MailManager API
        for cases where immediate sending is required.
        """
        logger.debug(f"Sending verification email synchronously to {email}")
        return self.mail_manager.send_verification_email(email, code)
    
    def send_security_alert(self, event_type: str, details: str) -> bool:
        """Fallback to immediate sending if needed"""
        logger.debug(f"Sending security alert synchronously: {event_type}")
        return self.mail_manager.send_security_alert(event_type, details)
    
    def track_and_alert_failed_login(self, username: str, ip_address: str) -> bool:
        """Fallback to immediate sending if needed"""
        logger.debug(f"Sending failed login alert synchronously for {username}")
        return self.mail_manager.track_and_alert_failed_login(username, ip_address)
    
    # === STATUS METHODS ===
    
    def get_queue_size(self) -> int:
        """Get the current size of the mail queue"""
        return self.mail_queue.qsize()
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get email processing statistics
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'emails_processed': self.emails_processed,
            'emails_failed': self.emails_failed,
            'queue_size': self.get_queue_size(),
            'worker_active': self.worker_active
        }
    
    def is_healthy(self) -> bool:
        """
        Check if the async mail manager is healthy
        
        Returns:
            True if worker is active and responsive
        """
        return (
            self.worker_thread is not None and 
            self.worker_thread.is_alive() and 
            self.worker_active and
            not self.stop_worker
        )


class BackgroundTaskManager:
    """
    Manager for running background tasks asynchronously
    
    This class provides a way to execute non-critical tasks in the background
    without blocking the main application flow. Tasks are executed in a
    thread pool for concurrent processing.
    
    Features:
    - Thread pool executor for concurrent task execution
    - Task queue management
    - Error handling and retry logic
    - Clean shutdown handling
    - Task statistics and monitoring
    """
    
    def __init__(self, max_workers: int = 2):
        """
        Initialize background task manager
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self.tasks = []
        self.executor = None
        self.stop_tasks = False
        self.processor_thread = None
        
        # Statistics
        self.tasks_processed = 0
        self.tasks_failed = 0
        
        logger.info(f"BackgroundTaskManager initialized with {max_workers} workers")
    
    def add_task(self, func: Callable, *args, **kwargs):
        """
        Add a task to be executed in background
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        task = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'created_at': datetime.now(),
            'retries': 0
        }
        self.tasks.append(task)
        logger.debug(f"Added background task: {func.__name__}")
    
    def start_background_processing(self):
        """
        Start processing background tasks
        
        Creates a thread pool executor and starts the task processor thread
        """
        if self.processor_thread is None or not self.processor_thread.is_alive():
            import concurrent.futures
            
            if self.executor is None:
                self.executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.max_workers,
                    thread_name_prefix="BackgroundTask"
                )
            
            self.stop_tasks = False
            self.processor_thread = threading.Thread(
                target=self._process_tasks_loop,
                daemon=True,
                name="BackgroundTaskProcessor"
            )
            self.processor_thread.start()
            logger.info("Background task processing started")
    
    def _process_tasks_loop(self):
        """
        Main loop for processing background tasks
        
        Continuously processes tasks from the queue until stop_tasks is set
        """
        logger.info("Background task processor loop started")
        
        while not self.stop_tasks:
            try:
                if self.tasks:
                    task = self.tasks.pop(0)
                    self._submit_task(task)
                else:
                    # No tasks, sleep briefly
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error in background task processor: {e}")
                time.sleep(1.0)
        
        logger.info("Background task processor loop stopped")
    
    def _submit_task(self, task: Dict[str, Any]):
        """
        Submit a task to the thread pool executor
        
        Args:
            task: Task dictionary with function and parameters
        """
        try:
            future = self.executor.submit(
                self._execute_task, 
                task['func'], 
                *task['args'], 
                **task['kwargs']
            )
            
            # Add callback to handle task completion
            future.add_done_callback(lambda f: self._task_completed(f, task))
            
        except Exception as e:
            logger.error(f"Error submitting background task: {e}")
            self.tasks_failed += 1
    
    def _execute_task(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a single task
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        try:
            logger.debug(f"Executing background task: {func.__name__}")
            result = func(*args, **kwargs)
            logger.debug(f"Background task completed: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Background task failed: {func.__name__}: {e}")
            raise
    
    def _task_completed(self, future, task: Dict[str, Any]):
        """
        Handle task completion
        
        Args:
            future: Completed future object
            task: Original task dictionary
        """
        try:
            # Check if task completed successfully
            result = future.result()
            self.tasks_processed += 1
            
        except Exception as e:
            self.tasks_failed += 1
            logger.error(f"Background task failed: {task['func'].__name__}: {e}")
            
            # Optionally implement retry logic here
            task['retries'] += 1
            if task['retries'] < 3:  # Max 3 retries
                logger.info(f"Retrying task: {task['func'].__name__} (attempt {task['retries'] + 1})")
                self.tasks.append(task)
    
    def stop(self):
        """
        Stop background task processing gracefully
        
        Shuts down the thread pool and waits for tasks to complete
        """
        logger.info("Stopping background task manager")
        self.stop_tasks = True
        
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5.0)
        
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Background task executor shut down")
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get task processing statistics
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'tasks_processed': self.tasks_processed,
            'tasks_failed': self.tasks_failed,
            'pending_tasks': len(self.tasks),
            'max_workers': self.max_workers
        }
    
    def is_healthy(self) -> bool:
        """
        Check if the background task manager is healthy
        
        Returns:
            True if processor is active and responsive
        """
        return (
            self.processor_thread is not None and
            self.processor_thread.is_alive() and
            not self.stop_tasks and
            self.executor is not None
        )