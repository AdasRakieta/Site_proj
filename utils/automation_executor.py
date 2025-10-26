"""
Automation Executor - handles execution of automation triggers and actions
"""
import logging
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Any
import uuid

logger = logging.getLogger(__name__)


class AutomationExecutor:
    """Handles automation execution logic"""
    
    def __init__(self, multi_db, socketio=None):
        """
        Initialize AutomationExecutor
        
        Args:
            multi_db: MultiHomeDBManager instance
            socketio: Flask-SocketIO instance for real-time updates
        """
        self.multi_db = multi_db
        self.socketio = socketio
    
    def process_device_trigger(self, device_id: str, room_name: str, device_name: str,
                               new_state: bool, home_id: str, user_id: str) -> List[Dict]:
        """
        Process automations triggered by device state change
        
        Args:
            device_id: UUID of the device
            room_name: Name of the room
            device_name: Name of the device
            new_state: New state of the device (True/False for on/off)
            home_id: UUID of the home
            user_id: UUID of the user triggering the change
            
        Returns:
            List of execution results
        """
        logger.info(f"[AUTOMATION] process_device_trigger called: device_id={device_id}, room={room_name}, name={device_name}, state={new_state}, home_id={home_id}")
        
        if not self.multi_db or not home_id:
            logger.warning(f"[AUTOMATION] Skipping trigger - multi_db={self.multi_db is not None}, home_id={home_id}")
            return []
        
        try:
            # Get automations for this home
            automations = self.multi_db.get_home_automations(home_id, user_id)
            logger.info(f"[AUTOMATION] Found {len(automations)} total automations for home {home_id}")
            
            device_key = f"{room_name}_{device_name}"
            logger.info(f"[AUTOMATION] Looking for device trigger with key: '{device_key}'")
            
            results = []
            for automation in automations:
                logger.info(f"[AUTOMATION] Checking automation: {automation.get('name')} (enabled={automation.get('enabled')})")
                if not automation.get('enabled', False):
                    logger.info(f"[AUTOMATION] ⏭ Skipping disabled automation: {automation.get('name')}")
                    continue
                
                trigger = automation.get('trigger', {}) or automation.get('trigger_config', {})
                if not trigger or trigger.get('type') != 'device':
                    logger.debug(f"[AUTOMATION] Skipping automation '{automation.get('name')}' - wrong trigger type: {trigger.get('type') if trigger else 'None'}")
                    continue
                
                # Check if trigger matches this device
                trigger_device = trigger.get('device')
                logger.debug(f"[AUTOMATION] Automation '{automation.get('name')}' trigger device: '{trigger_device}' vs '{device_key}'")
                
                if trigger_device != device_key:
                    logger.debug(f"[AUTOMATION] Device mismatch: '{trigger_device}' != '{device_key}'")
                    continue
                
                # Check if state matches trigger condition
                trigger_state = trigger.get('state', 'on')
                device_on = new_state is True
                
                logger.debug(f"[AUTOMATION] Checking state: trigger_state={trigger_state}, device_on={device_on}")
                
                should_execute = False
                if trigger_state == 'on' and device_on:
                    should_execute = True
                elif trigger_state == 'off' and not device_on:
                    should_execute = True
                elif trigger_state == 'toggle':
                    should_execute = True
                
                if should_execute:
                    logger.info(f"[AUTOMATION] ✓ Executing automation: {automation.get('name')}")
                    result = self._execute_automation(automation, home_id, user_id, {
                        'trigger_type': 'device',
                        'device_id': device_id,
                        'device_key': device_key,
                        'new_state': new_state
                    })
                    results.append(result)
                else:
                    logger.debug(f"[AUTOMATION] State condition not met for '{automation.get('name')}'")
            
            logger.info(f"[AUTOMATION] Executed {len(results)} automations")
            return results
            
        except Exception as e:
            logger.error(f"Error processing device trigger: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def process_sensor_trigger(self, sensor_id: str, sensor_name: str, room_name: str,
                               sensor_type: str, value: float, home_id: str, user_id: str) -> List[Dict]:
        """
        Process automations triggered by sensor value changes
        
        Args:
            sensor_id: UUID of the sensor
            sensor_name: Name of the sensor
            room_name: Name of the room
            sensor_type: Type of sensor (temperature, humidity, etc.)
            value: Current sensor value
            home_id: UUID of the home
            user_id: UUID of the user
            
        Returns:
            List of execution results
        """
        if not self.multi_db or not home_id:
            return []
        
        try:
            # Get automations for this home
            automations = self.multi_db.get_home_automations(home_id, user_id)
            sensor_key = f"{room_name}_{sensor_name}"
            
            results = []
            for automation in automations:
                if not automation.get('enabled', False):
                    continue
                
                trigger = automation.get('trigger', {}) or automation.get('trigger_config', {})
                if not trigger or trigger.get('type') != 'sensor':
                    continue
                
                # Check if trigger matches this sensor
                if trigger.get('sensor') != sensor_key:
                    continue
                
                # Check if value crosses threshold
                condition = trigger.get('condition', 'above')  # above, below, equals
                threshold = trigger.get('value')
                
                if threshold is None:
                    continue
                
                try:
                    threshold = float(threshold)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid threshold value in automation: {threshold}")
                    continue
                
                should_execute = False
                if condition == 'above' and value > threshold:
                    should_execute = True
                elif condition == 'below' and value < threshold:
                    should_execute = True
                elif condition == 'equals' and abs(value - threshold) < 0.01:  # Float comparison tolerance
                    should_execute = True
                
                if should_execute:
                    result = self._execute_automation(automation, home_id, user_id, {
                        'trigger_type': 'sensor',
                        'sensor_id': sensor_id,
                        'sensor_key': sensor_key,
                        'sensor_type': sensor_type,
                        'value': value,
                        'threshold': threshold,
                        'condition': condition
                    })
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing sensor trigger: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _execute_automation(self, automation: Dict, home_id: str, user_id: str,
                           trigger_data: Dict) -> Dict:
        """
        Execute automation actions
        
        Args:
            automation: Automation configuration
            home_id: UUID of the home
            user_id: UUID of the user
            trigger_data: Data about what triggered the automation
            
        Returns:
            Execution result
        """
        automation_id = automation.get('id')
        automation_name = automation.get('name', 'Unknown')
        
        start_time = datetime.now()
        actions_executed = []
        errors = []
        
        try:
            actions = automation.get('actions', []) or automation.get('actions_config', [])
            
            for action in actions:
                action_type = action.get('type')
                
                try:
                    if action_type == 'device':
                        self._execute_device_action(action, home_id, user_id)
                    elif action_type == 'thermostat_control':
                        self._execute_thermostat_control_action(action, home_id, user_id)
                    elif action_type == 'set_temperature':
                        self._execute_temperature_action(action, home_id, user_id)
                    elif action_type == 'notification':
                        self._execute_notification_action(action, home_id, user_id)
                    
                    actions_executed.append({
                        'type': action_type,
                        'status': 'success',
                        'action': action
                    })
                except Exception as action_error:
                    error_msg = str(action_error)
                    logger.error(f"Error executing action {action_type}: {error_msg}")
                    errors.append(error_msg)
                    actions_executed.append({
                        'type': action_type,
                        'status': 'error',
                        'error': error_msg,
                        'action': action
                    })
            
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Log execution to database
            execution_status = 'error' if errors else 'success'
            error_message = '; '.join(errors) if errors else None
            
            if automation_id:
                self._log_execution(
                    automation_id=automation_id,
                    execution_status=execution_status,
                    trigger_data=trigger_data,
                    actions_executed=actions_executed,
                    error_message=error_message,
                    execution_time_ms=execution_time_ms
                )
            
            return {
                'automation_id': automation_id,
                'automation_name': automation_name,
                'status': execution_status,
                'actions_executed': len(actions_executed),
                'errors': errors,
                'execution_time_ms': execution_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error executing automation {automation_name}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'automation_id': automation_id,
                'automation_name': automation_name,
                'status': 'error',
                'errors': [str(e)],
                'actions_executed': 0
            }
    
    def _execute_device_action(self, action: Dict, home_id: str, user_id: str):
        """Execute device control action (on/off/toggle)"""
        device_key = action.get('device')  # format: room_name
        target_state = action.get('state')  # 'on', 'off', or 'toggle'
        
        if not device_key or not target_state:
            raise ValueError("Missing device or state in action")
        
        # Parse device key (room_name)
        parts = device_key.split('_', 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid device key format: {device_key}")
        
        room_name, device_name = parts
        
        # Find device in database
        devices = self.multi_db.get_home_devices(home_id, user_id, device_type='button')
        device = None
        for d in devices:
            if d['room_name'] == room_name and d['name'] == device_name:
                device = d
                break
        
        if not device:
            raise ValueError(f"Device not found: {device_key}")
        
        # Determine new state
        current_state = device.get('state', False)
        if target_state == 'on':
            new_state = True
        elif target_state == 'off':
            new_state = False
        elif target_state == 'toggle':
            new_state = not current_state
        else:
            raise ValueError(f"Invalid target state: {target_state}")
        
        # Update device state
        device_id = device['id']
        self.multi_db.update_device(device_id, user_id, state=new_state)
        
        # Emit WebSocket updates if available - broadcast to all clients in the home
        if self.socketio:
            # Update button state for all clients - include room_id for proper switch matching
            self.socketio.emit('update_button', {
                'room': room_name,
                'room_id': str(device.get('room_id', '')),  # Add room_id for UUID-based switch IDs
                'name': device_name,
                'state': new_state,
                'device_id': device_id
            })
            
            # Sync button states (for lights page and other views)
            self.socketio.emit('sync_button_states', {
                f"{room_name}_{device_name}": new_state
            })
            
            logger.info(f"[AUTOMATION] Emitted WebSocket update for {device_key}")
        
        logger.info(f"[AUTOMATION] Set {device_key} to {new_state}")
    
    def _execute_thermostat_control_action(self, action: Dict, home_id: str, user_id: str):
        """Execute thermostat on/off/toggle control action"""
        device_key = action.get('device')  # format: room_name_devicename
        target_state = action.get('state')  # 'on', 'off', or 'toggle'
        
        if not device_key or not target_state:
            raise ValueError("Missing device or state in thermostat_control action")
        
        # Parse device key (room_name_devicename)
        parts = device_key.split('_', 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid thermostat key format: {device_key}")
        
        room_name, device_name = parts
        
        # Find thermostat in database
        devices = self.multi_db.get_home_devices(home_id, user_id, device_type='temperature_control')
        device = None
        for d in devices:
            if d['room_name'] == room_name and d['name'] == device_name:
                device = d
                break
        
        if not device:
            raise ValueError(f"Thermostat not found: {device_key}")
        
        # Determine new state
        current_state = device.get('state', False)
        if target_state == 'on':
            new_state = True
        elif target_state == 'off':
            new_state = False
        elif target_state == 'toggle':
            new_state = not current_state
        else:
            raise ValueError(f"Invalid target state: {target_state}")
        
        # Update thermostat state
        device_id = device['id']
        self.multi_db.update_device(device_id, user_id, state=bool(new_state))
        
        # Emit WebSocket updates if available - broadcast to all clients in the home
        if self.socketio:
            # Convert Decimal to float for JSON serialization
            current_temp = device.get('temperature')
            temp_value = float(current_temp) if current_temp is not None else None
            
            # Update thermostat state for all clients - include room_id for proper element matching
            self.socketio.emit('update_temperature', {
                'room': room_name,
                'room_id': str(device.get('room_id', '')),
                'name': device_name,
                'state': new_state,
                'device_id': device_id,
                'temperature': temp_value  # Convert Decimal to float
            })
            
            # Sync temperature states (for temperature page and other views)
            self.socketio.emit('sync_temperature', {
                f"{room_name}_{device_name}": {
                    'state': new_state,
                    'temperature': temp_value  # Convert Decimal to float
                }
            })
            
            logger.info(f"[AUTOMATION] Emitted WebSocket update for thermostat {device_key}")
        
        logger.info(f"[AUTOMATION] Set thermostat {device_key} to {new_state}")
    
    def _execute_temperature_action(self, action: Dict, home_id: str, user_id: str):
        """Execute temperature control action"""
        thermostat_key = action.get('thermostat')  # format: room_name
        target_temp = action.get('temperature')
        
        if not thermostat_key or target_temp is None:
            raise ValueError("Missing thermostat or temperature in action")
        
        # Parse thermostat key
        parts = thermostat_key.split('_', 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid thermostat key format: {thermostat_key}")
        
        room_name, device_name = parts
        
        # Find thermostat in database
        devices = self.multi_db.get_home_devices(home_id, user_id, device_type='temperature_control')
        device = None
        for d in devices:
            if d['room_name'] == room_name and d['name'] == device_name:
                device = d
                break
        
        if not device:
            raise ValueError(f"Thermostat not found: {thermostat_key}")
        
        # Update temperature
        device_id = device['id']
        self.multi_db.update_device(device_id, user_id, temperature=float(target_temp))
        
        # Emit WebSocket updates if available - broadcast to all clients
        if self.socketio:
            # Update temperature for all views
            self.socketio.emit('update_temperature', {
                'room': room_name,
                'name': device_name,
                'temperature': float(target_temp),
                'device_id': device_id
            })
            
            # Sync temperature (for compatibility with different pages)
            self.socketio.emit('sync_temperature', {
                'name': device_name,
                'temperature': float(target_temp)
            })
            
            logger.info(f"[AUTOMATION] Emitted WebSocket temperature update for {thermostat_key}")
        
        logger.info(f"[AUTOMATION] Set {thermostat_key} temperature to {target_temp}°C")
    
    def _execute_notification_action(self, action: Dict, home_id: str, user_id: str):
        """Execute notification action"""
        message = action.get('message')
        
        if not message:
            raise ValueError("Missing message in notification action")
        
        # Emit notification via WebSocket if available
        if self.socketio:
            self.socketio.emit('automation_notification', {
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        
        logger.info(f"[AUTOMATION] Notification: {message}")
    
    def _log_execution(self, automation_id: str, execution_status: str,
                      trigger_data: Dict, actions_executed: List[Dict],
                      error_message: Optional[str], execution_time_ms: int):
        """Log automation execution to database"""
        try:
            import json
            with self.multi_db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO automation_executions 
                    (automation_id, execution_status, trigger_data, actions_executed, 
                     error_message, execution_time_ms, executed_at)
                    VALUES (%s, %s, %s::jsonb, %s::jsonb, %s, %s, %s)
                """, (
                    automation_id,
                    execution_status,
                    json.dumps(trigger_data),  # Convert dict to JSON string
                    json.dumps(actions_executed),  # Convert list to JSON string
                    error_message,
                    execution_time_ms,
                    datetime.now()
                ))
                
                # Update automation statistics (use home_automations table)
                cursor.execute("""
                    UPDATE home_automations
                    SET execution_count = execution_count + 1,
                        last_executed = %s,
                        error_count = CASE WHEN %s = 'error' THEN error_count + 1 ELSE error_count END,
                        last_error = CASE WHEN %s = 'error' THEN %s ELSE last_error END,
                        last_error_time = CASE WHEN %s = 'error' THEN %s ELSE last_error_time END
                    WHERE id = %s
                """, (
                    datetime.now(),
                    execution_status,
                    execution_status,
                    error_message,
                    execution_status,
                    datetime.now() if execution_status == 'error' else None,
                    automation_id
                ))
        except Exception as e:
            logger.error(f"Error logging automation execution: {e}")
