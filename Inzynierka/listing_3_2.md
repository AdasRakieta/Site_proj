```python
def _broadcast_device_update(self, home_id, device_data):
    broadcast_count = 0
    # Pobierz użytkowników gospodarstwa
    users = self.multi_db.get_home_users(str(home_id))
    for user in users:
        user_id = user.get('id')
        # Mapowanie user_id -> aktywne session_id Socket.IO
        session_id = self._get_user_session_id(user_id)
        if session_id:
            # Emituj tylko do konkretnej sesji, nie globalnie
            self.socketio.emit('device_updated', device_data, room=session_id)
            broadcast_count += 1
    logger.info(f"Broadcast device_updated to {broadcast_count} clients for home {home_id}")
```

Listing 3.2: Fragment metody `_broadcast_device_update` z `routes.py`.
