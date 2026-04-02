```python
def home_required(self, f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user_id = session.get('user_id')
        home_id = session.get('current_home_id')
        if not home_id:
            return redirect(url_for('select_home'))
        if not self.multi_db.user_belongs_to_home(user_id, home_id):
            return redirect(url_for('select_home'))
        return f(*args, **kwargs)
    return decorated_function
```
