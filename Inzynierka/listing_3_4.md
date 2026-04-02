```python
@self.app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-CSRFToken')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

    # SECURITY: Add security headers (MEDIUM FIX)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.socket.io; "
        "script-src-elem 'self' 'unsafe-inline' https://unpkg.com https://cdn.socket.io; "
        "style-src 'self' 'unsafe-inline' https://unpkg.com; "
        "style-src-elem 'self' 'unsafe-inline' https://unpkg.com; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https://unpkg.com; "
        "frame-ancestors 'none';"
    )
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if is_production:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    return response
```

Listing 3.4: Fragment `app_db.py` — konfiguracja nagłówków bezpieczeństwa (CSP + X- headers).
