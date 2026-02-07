# 2. Wymagania funkcjonalne i niefunkcjonalne

2.1 Wymagania funkcjonalne
- Możliwość utworzenia i zarządzania wieloma domami (multi-home).
- Rejestracja i uwierzytelnianie użytkowników; role: owner, member, guest.
- Zarządzanie pokojami, urządzeniami (przyciski, kontrola temperatury), automatyzacjami.
- Sterowanie urządzeniami w czasie rzeczywistym (Socket.IO) oraz aktualizacja stanu dla wszystkich klientów.
- Mechanizm zaproszeń do domu (generowanie kodu, wysłanie maila, akceptacja).

2.2 Wymagania niefunkcjonalne
- Wydajność: obsługa wielu jednoczesnych połączeń WebSocket; użycie puli połączeń do PostgreSQL.
- Niezawodność: transakcje DB z rollback/commit; fallback do JSON dla trybu bez DB.
- Bezpieczeństwo: ochrona sesji, CSRF, hashowanie haseł, ograniczenia ról.
- Rozszerzalność: modularna architektura (RoutesManager, MultiHomeDBManager, CacheManager).
