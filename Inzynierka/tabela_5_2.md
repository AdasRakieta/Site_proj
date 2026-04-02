**Tabela 5.2 — Porównanie strategii backup**

| Metoda | Częstotliwość | Retention | Restore Time | Use Case |
|---|---:|---|---:|---|
| PostgreSQL dump (pg_dump + gzip) | Automatyczny: daily (cron), możliwe ręczne zrzuty przed zmianami | Lokalnie: rotacja (np. 7 dni). Opcjonalnie offsite przez `rclone` | Średni — od kilku do kilkudziesięciu minut w zależności od rozmiaru bazy i środowiska | Pełny restore bazy, disaster recovery, migracje między hostami, audyt danych |
| JSON fallback sync (json_backup_manager.py) | Natychmiast przy każdej zmianie konfiguracji (export on write) | Zwykle utrzymuje bieżący plik + jedno backup `.backup` (można rozszerzyć do rotacji) | Szybki — sekundy do kilku minut (podmiana pliku + import) | Szybkie przywrócenie konfiguracji aplikacji, fallback przy awarii DB, migracje konfiguracji, debug i ręczne inspekcje |
| Hybrydowy: pg_dump + offsite copy (rclone) | Daily + offsite kopiowanie po wykonaniu dumpa | Długoterminowe zależne od remote storage (np. miesięczna polityka) | Podobny do lokalnego dumpa; może wymagać pobrania (dodatkowy czas) | Offsite disaster recovery, długoterminowe archiwizowanie backupów, zgodność z politykami backup |

Krótka uwaga: `pg_dump` daje spójną kopię całej bazy (dobre dla odzyskiwania danych), natomiast JSON fallback jest lekki, czytelny i szybki do przywrócenia konfiguracji aplikacji — zalecane stosowanie obu mechanizmów równolegle (pełne zrzuty + szybkie JSON backups) dla minimalizacji RTO i RPO.
