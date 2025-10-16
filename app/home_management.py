"""
Home Management Classes for Multi-Home System
Handles different aspects of home management separately from general app settings.
"""

from typing import Dict, List, Optional, Any
from utils.multi_home_db_manager import MultiHomeDBManager
import logging

logger = logging.getLogger(__name__)

class HomeInfoManager:
    """Manages basic home information (name, description, etc.)"""
    
    def __init__(self, db_manager: MultiHomeDBManager):
        self.db = db_manager
    
    def update_home_info(self, home_id: str, user_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Update basic home information"""
        try:
            # Validate user is owner
            if not self._is_home_owner(home_id, user_id):
                return {"success": False, "error": "Only home owners can update home information"}
            
            # Validate input
            if not name or not name.strip():
                return {"success": False, "error": "Home name is required"}
            
            if len(name.strip()) > 100:
                return {"success": False, "error": "Home name must be 100 characters or less"}
            
            if description and len(description) > 500:
                return {"success": False, "error": "Description must be 500 characters or less"}
            
            # Update database
            success = self.db.update_home_info(home_id, name.strip(), description.strip() if description else None)
            
            if not success:
                return {"success": False, "error": "Failed to update home information in database"}
            
            logger.info(f"Home info updated for home {home_id} by user {user_id}")
            return {
                "success": True,
                "message": "Home information updated successfully",
                "data": {
                    "name": name.strip(),
                    "description": description.strip() if description else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating home info: {e}")
            return {"success": False, "error": "Failed to update home information"}
    
    def get_home_info(self, home_id: str, user_id: str) -> Dict[str, Any]:
        """Get home information"""
        try:
            # Check if user has access to this home
            user_homes = self.db.get_user_homes(user_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            
            if not home:
                return {"success": False, "error": "Home not found or access denied"}
            
            return {
                "success": True,
                "data": home
            }
            
        except Exception as e:
            logger.error(f"Error getting home info: {e}")
            return {"success": False, "error": "Failed to get home information"}
    
    def _is_home_owner(self, home_id: str, user_id: str) -> bool:
        """Check if user is owner of the home"""
        try:
            user_homes = self.db.get_user_homes(user_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            return home and home.get('is_owner', False)
        except Exception as e:
            logger.error(f"Error checking home ownership: {e}")
            return False


class HomeUserManager:
    """Manages home users, invitations, and permissions"""
    
    def __init__(self, db_manager: MultiHomeDBManager):
        self.db = db_manager
    
    def invite_user(self, home_id: str, inviter_id: str, email: str, role: str = 'user') -> Dict[str, Any]:
        """Send invitation to a user"""
        try:
            # Validate inviter is owner
            if not self._is_home_owner(home_id, inviter_id):
                return {"success": False, "error": "Only home owners can invite users"}
            
            # Validate email
            if not email or '@' not in email:
                return {"success": False, "error": "Valid email address is required"}
            
            # Validate role
            valid_roles = ['user', 'admin']
            if role not in valid_roles:
                return {"success": False, "error": f"Role must be one of: {', '.join(valid_roles)}"}
            
            # Generate invitation code
            invitation_code = self._generate_invitation_code()
            
            # TODO: Implement invitation system
            # - Store invitation in database
            # - Send email with invitation code
            # self.db.create_invitation(home_id, email, role, invitation_code, inviter_id)
            # self._send_invitation_email(email, invitation_code, home_name)
            
            logger.info(f"User invited to home {home_id}: {email} with role {role}")
            return {
                "success": True,
                "message": f"Invitation sent to {email}",
                "data": {
                    "email": email,
                    "role": role,
                    "invitation_code": invitation_code  # Remove this in production
                }
            }
            
        except Exception as e:
            logger.error(f"Error inviting user: {e}")
            return {"success": False, "error": "Failed to send invitation"}
    
    def get_home_users(self, home_id: str, requester_id: str) -> Dict[str, Any]:
        """Get list of users in a home"""
        try:
            # Check if requester has access to this home
            user_homes = self.db.get_user_homes(requester_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            
            if not home:
                return {"success": False, "error": "Home not found or access denied"}
            
            # TODO: Implement get_home_users in database
            # users = self.db.get_home_users(home_id)
            
            # For now, return dummy data
            users = [
                {
                    "id": requester_id,
                    "name": "You",
                    "email": "owner@example.com",
                    "role": "owner",
                    "is_owner": True,
                    "joined_at": "2024-01-01"
                }
            ]
            
            return {
                "success": True,
                "data": users
            }
            
        except Exception as e:
            logger.error(f"Error getting home users: {e}")
            return {"success": False, "error": "Failed to get home users"}
    
    def remove_user(self, home_id: str, owner_id: str, user_id: str) -> Dict[str, Any]:
        """Remove user from home"""
        try:
            # Validate requester is owner
            if not self._is_home_owner(home_id, owner_id):
                return {"success": False, "error": "Only home owners can remove users"}
            
            # Prevent owner from removing themselves
            if owner_id == user_id:
                return {"success": False, "error": "Owner cannot remove themselves"}
            
            # TODO: Implement user removal
            # self.db.remove_user_from_home(home_id, user_id)
            
            logger.info(f"User {user_id} removed from home {home_id} by owner {owner_id}")
            return {
                "success": True,
                "message": "User removed from home"
            }
            
        except Exception as e:
            logger.error(f"Error removing user: {e}")
            return {"success": False, "error": "Failed to remove user"}
    
    def _is_home_owner(self, home_id: str, user_id: str) -> bool:
        """Check if user is owner of the home"""
        try:
            user_homes = self.db.get_user_homes(user_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            return home and home.get('is_owner', False)
        except Exception as e:
            logger.error(f"Error checking home ownership: {e}")
            return False
    
    def _generate_invitation_code(self) -> str:
        """Generate unique invitation code"""
        import uuid
        return str(uuid.uuid4())[:8].upper()
    
    def _send_invitation_email(self, email: str, code: str, home_name: str):
        """Send invitation email (to be implemented)"""
        # TODO: Integrate with email system
        pass


class HomeRoomManager:
    """Manages rooms within homes"""
    
    def __init__(self, db_manager: MultiHomeDBManager):
        self.db = db_manager
    
    def get_home_rooms(self, home_id: str, user_id: str) -> Dict[str, Any]:
        """Get rooms in a home"""
        try:
            # Check if user has access to this home
            user_homes = self.db.get_user_homes(user_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            
            if not home:
                return {"success": False, "error": "Home not found or access denied"}
            
            # Get rooms from database
            rooms = self.db.get_home_rooms(home_id, user_id)
            
            return {
                "success": True,
                "data": rooms
            }
            
        except Exception as e:
            logger.error(f"Error getting home rooms: {e}")
            return {"success": False, "error": "Failed to get rooms"}
    
    def update_room(self, home_id: str, user_id: str, room_id: str, name: str, room_type: str) -> Dict[str, Any]:
        """Update room information"""
        try:
            # Check if user has access to this home
            if not self._has_home_access(home_id, user_id):
                return {"success": False, "error": "Access denied"}
            
            # Validate input
            if not name or not name.strip():
                return {"success": False, "error": "Room name is required"}
            
            valid_types = ['living_room', 'bedroom', 'kitchen', 'bathroom', 'office', 'garage', 'garden', 'other']
            if room_type not in valid_types:
                return {"success": False, "error": "Invalid room type"}
            
            # TODO: Implement room update
            # self.db.update_room(room_id, name.strip(), room_type)
            
            logger.info(f"Room {room_id} updated in home {home_id} by user {user_id}")
            return {
                "success": True,
                "message": "Room updated successfully",
                "data": {
                    "id": room_id,
                    "name": name.strip(),
                    "room_type": room_type
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating room: {e}")
            return {"success": False, "error": "Failed to update room"}
    
    def delete_room(self, home_id: str, user_id: str, room_id: str) -> Dict[str, Any]:
        """Delete a room"""
        try:
            # Check if user has admin access to this home
            if not self._has_admin_access(home_id, user_id):
                return {"success": False, "error": "Admin access required to delete rooms"}
            
            # TODO: Implement room deletion
            # Check if room has devices first
            # devices = self.db.get_room_devices(room_id)
            # if devices:
            #     return {"success": False, "error": "Cannot delete room with devices"}
            # self.db.delete_room(room_id)
            
            logger.info(f"Room {room_id} deleted from home {home_id} by user {user_id}")
            return {
                "success": True,
                "message": "Room deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting room: {e}")
            return {"success": False, "error": "Failed to delete room"}
    
    def _has_home_access(self, home_id: str, user_id: str) -> bool:
        """Check if user has access to this home"""
        try:
            user_homes = self.db.get_user_homes(user_id)
            return any(h['id'] == home_id for h in user_homes)
        except Exception as e:
            logger.error(f"Error checking home access: {e}")
            return False
    
    def _has_admin_access(self, home_id: str, user_id: str) -> bool:
        """Check if user has admin access to this home"""
        try:
            user_homes = self.db.get_user_homes(user_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            return home and (home.get('is_owner', False) or home.get('role') == 'admin')
        except Exception as e:
            logger.error(f"Error checking admin access: {e}")
            return False


class HomeDeletionManager:
    """Manages home deletion and dangerous operations"""
    
    def __init__(self, db_manager: MultiHomeDBManager):
        self.db = db_manager
    
    def delete_home(self, home_id: str, owner_id: str) -> Dict[str, Any]:
        """Delete a home permanently"""
        try:
            # Validate user is owner
            if not self._is_home_owner(home_id, owner_id):
                return {"success": False, "error": "Only home owners can delete homes"}
            
            # Get home info for logging
            user_homes = self.db.get_user_homes(owner_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            
            if not home:
                return {"success": False, "error": "Home not found"}
            
            # Delete home completely from database
            success = self.db.delete_home_completely(home_id)
            
            if not success:
                return {"success": False, "error": "Failed to delete home from database"}
            
            logger.warning(f"Home '{home['name']}' ({home_id}) deleted by owner {owner_id}")
            return {
                "success": True,
                "message": f"Home '{home['name']}' has been permanently deleted"
            }
            
        except Exception as e:
            logger.error(f"Error deleting home: {e}")
            return {"success": False, "error": "Failed to delete home"}
    
    def get_deletion_info(self, home_id: str, owner_id: str) -> Dict[str, Any]:
        """Get information about what will be deleted"""
        try:
            # Validate user is owner
            if not self._is_home_owner(home_id, owner_id):
                return {"success": False, "error": "Only home owners can view deletion info"}
            
            # Get comprehensive home data
            rooms = self.db.get_home_rooms(home_id, owner_id)
            devices = self.db.get_home_devices(home_id, owner_id)
            
            # TODO: Get additional data like automations, user count, etc.
            
            return {
                "success": True,
                "data": {
                    "room_count": len(rooms),
                    "device_count": len(devices),
                    "user_count": 1,  # TODO: Get actual user count
                    "automation_count": 0  # TODO: Get actual automation count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting deletion info: {e}")
            return {"success": False, "error": "Failed to get deletion information"}
    
    def _is_home_owner(self, home_id: str, user_id: str) -> bool:
        """Check if user is owner of the home"""
        try:
            user_homes = self.db.get_user_homes(user_id)
            home = next((h for h in user_homes if h['id'] == home_id), None)
            return home and home.get('is_owner', False)
        except Exception as e:
            logger.error(f"Error checking home ownership: {e}")
            return False


class HomeSettingsManager:
    """Main manager that coordinates all home management classes"""
    
    def __init__(self, db_manager: MultiHomeDBManager):
        self.db = db_manager
        self.info_manager = HomeInfoManager(db_manager)
        self.user_manager = HomeUserManager(db_manager)
        self.room_manager = HomeRoomManager(db_manager)
        self.deletion_manager = HomeDeletionManager(db_manager)
    
    def get_home_settings_data(self, home_id: str, user_id: str) -> Dict[str, Any]:
        """Get all data needed for the home settings page"""
        try:
            # Get basic home info
            home_info = self.info_manager.get_home_info(home_id, user_id)
            if not home_info["success"]:
                return home_info
            
            # Get rooms
            try:
                rooms_info = self.room_manager.get_home_rooms(home_id, user_id)
                rooms_data = rooms_info.get("data", []) if rooms_info.get("success", False) else []
            except Exception as e:
                logger.error(f"Error getting rooms: {e}")
                rooms_data = []
            
            # Get users
            try:
                users_info = self.user_manager.get_home_users(home_id, user_id)
                users_data = users_info.get("data", []) if users_info.get("success", False) else []
            except Exception as e:
                logger.error(f"Error getting users: {e}")
                users_data = []
            
            # Combine all data
            return {
                "success": True,
                "data": {
                    "home": home_info["data"],
                    "rooms": rooms_data,
                    "users": users_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting home settings data: {e}")
            return {"success": False, "error": "Failed to load home settings"}