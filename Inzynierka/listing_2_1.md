```python
def _broadcast_device_update(self, home_id, device_data):
    broadcast_count = 0
    # 1) pobranie listy użytkowników gospodarstwa
    users = self.multi_db.get_home_users(str(home_id))
    # 2) iteracja przez użytkowników i mapowanie user_id -> session_id
    for user in users:
        user_id = user.get('id')
        session_id = self._get_user_session_id(user_id)
        # 3) emit do konkretnej sesji Socket.IO (izolacja gospodarstwa)
        if session_id:
            self.socketio.emit('device_updated', device_data, room=session_id)
            broadcast_count += 1
    # 4) logging liczby klientów, do których wysłano broadcast
    logger.info(f"Broadcast device_updated to {broadcast_count} clients for home {home_id}")
```

Listing 2.1: Fragment metody `_broadcast_device_update` z `routes.py` (ok. 15 linii).
