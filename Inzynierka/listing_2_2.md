```python
def cache_json_response(self, timeout=None):
    if timeout is None:
        timeout = self.get_timeout('api_response')

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = (session or {}).get('user_id', 'anonymous')
            req_args = getattr(getattr(request, 'args', None), 'to_dict', lambda: {})()
            req_args_str = '&'.join(f"{k}={v}" for k, v in sorted(req_args.items()))
            cache_key = f"api_{f.__name__}_{user_id}_{getattr(request, 'method','')}_{args}_{req_args_str}"

            cached_response = self.cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_response

            response = f(*args, **kwargs)
            # Cache only successful GET responses
            if getattr(request, 'method', None) == 'GET' and getattr(response, 'status_code', None) == 200:
                self.cache.set(cache_key, response, timeout=timeout)
                logger.debug(f"Cached response for {cache_key}")
            return response
        return decorated_function
    return decorator
```

Listing 2.2: Fragment z `utils/cache_manager.py` pokazujący dekorator cache'ujący odpowiedzi JSON i mechanizm sprawdzania cache (miss/hit) oraz zapisu w cache.
