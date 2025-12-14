# 7. Bezpieczeństwo — szczegółowa analiza i zalecenia

7.1 Model zagrożeń (STRIDE odwołania)
- Spoofing (podszywanie się): ryzyko kradzieży sesji lub tokenów autoryzacyjnych.
- Tampering (manipulacja): nieautoryzowane modyfikacje stanów urządzeń lub automatyzacji.
- Repudiation (zaprzeczenie): brak logów operacji użytkowników utrudnia audyt.
- Information disclosure: wyciek danych użytkowników lub kluczy.
- Denial of Service: ataki przeciążeniowe na Socket.IO lub DB.
- Elevation of Privilege: eskalacja uprawnień w modelu ról.

7.2 Zaimplementowane środki i ich uzasadnienie
- Sesje i ciasteczka: `SESSION_COOKIE_HTTPONLY` i `SESSION_COOKIE_SAMESITE='Lax'` — redukuje ryzyko XSS/CSRF przy niektórych scenariuszach (plik: `app_db.py`).

```python
self.app.config.update({
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SECURE': bool(is_production),
})
```

- Hasła i uwierzytelnianie: użycie `werkzeug.security.generate_password_hash` i `check_password_hash` w warstwie DB/management.
- Parametryzowane zapytania: cała warstwa DB (`psycopg2`) używa parametrów zamiast formatowania stringów, co chroni przed SQL injection (zob. `_execute_query` w `utils/smart_home_db_manager.py`).
- Uprawnienia per-home: każda operacja w `RoutesManager` sprawdza role/permissions przez `auth_manager` przed wykonaniem zmian.
- Logowanie i audyt: `DatabaseManagementLogger` rejestruje ważne operacje administracyjne i automatyzacje (umożliwia repudiation auditing).

7.3 Dodatkowe rekomendacje (do wdrożenia)
- Wdrożyć CSRF protection dla endpointów formularzy (Flask-WTF lub tokeny ręczne) oraz ograniczyć HTTP methods dla endpointów modyfikujących.
- Zabezpieczyć endpointy API przez rate-limiting (Flask-Limiter) aby zmniejszyć ryzyko DoS na Socket.IO.
- Uwierzytelnianie dwuskładnikowe (2FA) dla ról owner/admin.
- Szyfrowanie wrażliwych danych w spoczynku (np. invitation tokens) i rotacja sekretów w systemie (Vault).
