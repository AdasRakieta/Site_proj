# 8. Podsumowanie i wnioski

W pracy przedstawiono projekt i implementację systemu SmartHome z obsługą wielu domów, komunikacją w czasie rzeczywistym oraz mechanizmami automatyzacji. System wykorzystuje PostgreSQL jako główny magazyn danych, z możliwością fallbacku do JSON, oraz Flask-SocketIO do rozgłaszania stanów urządzeń.

Wnioski:
- Architektura warstwowa i modularna ułatwia rozwój i testowanie.
- Cache znacząco poprawia wydajność odczytów, ale wymaga starannej invalidacji po aktualizacjach.
- Automatyzacje powinny być audytowane i ograniczane przez role ze względu na bezpieczeństwo.

Przyszłe prace: integracja z fizycznymi urządzeniami (Raspberry Pi), automatyczne testy end-to-end, dodatkowe metryki i monitoring.
