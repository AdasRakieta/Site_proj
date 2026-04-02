**3.2.2 Diagram ER i transformacja**

Diagram związków encji (ER) systemu SmartHome Multi-Home modeluje pięć głównych encji oraz relacje między nimi: `User`, `Home`, `Room`, `Device`, `Automation` oraz tabelę asocjacyjną `user_homes` opisującą członkostwa.

Główne właściwości modeli:
- `User`: `id` (UUID PK), `username`, `email`, `password_hash`, `role` (sys-admin | user).
- `Home`: `id` (UUID PK), `name`, `description`, `address`, `latitude`, `longitude`, `owner_id` (FK → `users.id`).
- `Room`: `id` (UUID PK), `home_id` (FK → `homes.id`), `name`, `description`, `display_order`.
- `Device`: `id` (UUID PK), `home_id` (FK → `homes.id`), `room_id` (FK → `rooms.id`, nullable), `name`, `device_type`, `state`, `temperature`, `settings` (JSONB).
- `Automation` (home_automations): `id` (UUID PK), `home_id` (FK → `homes.id`), `name`, `trigger_config` (JSONB), `actions_config` (JSONB), `enabled`.
- `user_homes`: tabela asocjacyjna z `user_id`, `home_id`, atrybutami relacji `role` i `permissions` (JSONB).

Relacje i własności:
- User ↔ Home: many-to-many przez `user_homes` (dodatkowe atrybuty `role`, `permissions`) oraz dodatkowa relacja własności `homes.owner_id` (User 1:N Home jako właściciel).
- Home → Room: 1:N z `room.home_id` (ON DELETE CASCADE).
- Room → Device: 1:N (device.room_id może być NULL; ON DELETE SET NULL).
- Home → Device: 1:N z `device.home_id` (ON DELETE CASCADE) — relacja paralelna do Room-Device zapewniająca spójność przynależności do gospodarstwa.
- Home → Automation: 1:N (ON DELETE CASCADE) z constraintem `UNIQUE(home_id, name)`.

Transformacja modelu konceptualnego do relacyjnego:
- Każda encja staje się tabelą z kolumnami odpowiadającymi atrybutom; klucze PK używają UUID generowanych przez `uuid_generate_v4()`.
- Relacje 1:N implementowane są przez klucze obce po stronie "many" (`home_id`, `room_id`).
- Relacje N:M implementowane są przez tabelę pośredniczącą `user_homes` z constraintem `UNIQUE(user_id, home_id)`.
- Atrybuty złożone/wielowartościowe (np. `device.settings`, `automation.trigger_config`, `user_homes.permissions`) mapowane do typu `JSONB` w PostgreSQL dla elastyczności i wydajnych zapytań.
- Integralność referencyjna: stosowane `ON DELETE CASCADE` dla strict ownership, `ON DELETE SET NULL` dla optional assignments, oraz `RESTRICT` gdzie usunięcie powinno być zablokowane.
- Indeksy: unikalne indeksy dla `email`, `username`; indeksy pomocnicze `idx_devices_home ON devices(home_id)`, `idx_rooms_home ON rooms(home_id)`, `idx_user_homes_user ON user_homes(user_id)`.

Rysunek ER: [Inzynierka/figure_3_3_er_diagram.mmd](Inzynierka/figure_3_3_er_diagram.mmd)
