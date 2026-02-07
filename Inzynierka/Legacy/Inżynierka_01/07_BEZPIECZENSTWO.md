# Rozdział 7: Bezpieczeństwo systemu

Celem rozdziału jest przedstawienie modelu zagrożeń, zastosowanych mechanizmów bezpieczeństwa oraz weryfikacji zgodności z dobrymi praktykami (OWASP Top 10). Opis odnosi się do konkretnej implementacji systemu SmartHome Multi-Home.

## 7.1. Model zagrożeń (STRIDE)

| Kategoria | Przykład w systemie | Mitigacja |
|---|---|---|
| Spoofing | Podszycie się pod użytkownika | bcrypt + salt, sesje HTTP-Only, rotacja tokenów, rate limiting logowania |
| Tampering | Modyfikacja żądań POST/PUT | CSRF tokens, walidacja danych, parametryzacja SQL |
| Repudiation | Zaprzeczenie wykonania akcji | Logi zarządzania (who/when/what), identyfikacja użytkownika |
| Information Disclosure | Wycieki danych członków domu | RBAC per-home, maskowanie danych, HTTPS |
| Denial of Service | Zalew żądań / socket flood | Limit połączeń, timeouts, buffering Nginx, retry/backoff |
| Elevation of Privilege | Nadanie admina bez autoryzacji | Spójne checki `multi_db.has_admin_access`, kontrola w DB |

## 7.2. OWASP Top 10 – mapowanie i środki zaradcze

1. Broken Access Control
   - Mitigacja: Dekoratory `login_required`, `admin_required`, `owner_required`; wszystkie zapytania DB filtrowane po `home_id` użytkownika.
2. Cryptographic Failures
   - Mitigacja: bcrypt (cost ≥ 12), TLS 1.2+, `SECURE_*` nagłówki; brak logowania haseł.
3. Injection (SQLi/XSS)
   - Mitigacja: Parametryzowane zapytania w `MultiHomeDBManager`; autoescape Jinja2; walidacja i sanitizacja wejścia.
4. Insecure Design
   - Mitigacja: Izolacja multi-tenant od poziomu schematu i kwerend; threat modeling STRIDE; testy bezpieczeństwa.
5. Security Misconfiguration
   - Mitigacja: Nginx hardening (security headers), Docker minimal base image, „least privilege” w DB.
6. Vulnerable and Outdated Components
   - Mitigacja: Skan zależności (CI), pinned versions w `requirements.txt`, regularne aktualizacje.
7. Identification and Authentication Failures
   - Mitigacja: Sól i koszt bcrypt; blokada konta po N nieudanych próbach; sesje z krótkim TTL.
8. Software and Data Integrity Failures
   - Mitigacja: CI/CD z weryfikacją buildów; brak wykonywania danych z zewnątrz; checksumy assetów.
9. Security Logging and Monitoring Failures
   - Mitigacja: `management_logger` + `database_management_logger`; śledzenie zmian i akcji użytkowników.
10. Server-Side Request Forgery (SSRF)
    - Mitigacja: Brak bezpośrednich SSRF endpointów; whitelisting dla ewentualnych integracji.

## 7.3. Uwierzytelnianie i zarządzanie sesją

- Hasła: bcrypt, minimalna długość, wymogi złożoności.
- Sesje: cookie `HttpOnly`, `SameSite=Lax/Strict`, wygasanie po 24h; rotacja przy logowaniu.
- Wylogowanie: natychmiastowe unieważnianie sesji.
- Opcjonalnie: 2FA (do wdrożenia – TOTP/Email OTP).

## 7.4. Autoryzacja (RBAC) i izolacja multi-tenant

- Role: `owner`, `admin`, `member`, `sys-admin` (globalny).
- Spójne kontrole uprawnień w `SimpleAuthManager` + `multi_db.has_admin_access`.
- Każde zapytanie do DB wymaga poprawnego `home_id` z sesji i dodatkowej walidacji w kwerendzie.

## 7.5. Ochrona danych i prywatność

- Dane osobowe: minimalizacja zakresu, przechowywanie tylko koniecznych pól.
- Backupy: szyfrowane, z rotacją, test odtwarzania.
- Zrzuty ekranu/logi: anonimizacja identyfikatorów gdzie możliwe.

## 7.6. Bezpieczeństwo komunikacji i API

- HTTPS/TLS: terminacja w Nginx, „modern profile” (Mozilla SSL).
- WebSocket: `wss://` z odpowiednimi timeoutami i limitami.
- CORS: restrykcyjny (origin whitelist), nagłówki bezpieczeństwa (`X-Frame-Options`, `Content-Security-Policy`).

## 7.7. Bezpieczeństwo wdrożenia i kontenerów

- Docker: multi-stage build, bez kompilatorów w warstwie runtime.
- User w kontenerze nie-root (jeśli możliwe); minimalne obrazy bazowe.
- Sekrety przez environment (nie w repo); walidacja `.env` (`utils/validate_env.py`).

## 7.8. Testy bezpieczeństwa

- Static Analysis: skan zależności i lintery bezpieczeństwa.
- Dynamic: testy SQLi/XSS, brute-force, rate limiting.
- Konfiguracja: weryfikacja nagłówków bezpieczeństwa (securityheaders.com), SSL Labs.

## 7.9. Podsumowanie

Zastosowane mechanizmy zapewniają solidny poziom bezpieczeństwa przy zachowaniu wygody użytkownika i wydajności. Krytyczne są: spójne kontrole uprawnień, izolacja per-home, poprawna konfiguracja TLS i higiena zależności. Kolejny krok to 2FA oraz rozproszone sesje (Redis store) w klastrze.
