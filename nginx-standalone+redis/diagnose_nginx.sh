#!/bin/bash
# Skrypt do sprawdzenia i naprawy konfiguracji nginx na malinie

echo "=== Diagnostyka nginx na malinie ==="
echo ""

# 1. Sprawdź strukturę katalogów
echo "1. Sprawdzam strukturę katalogów..."
echo "   /opt/nginx:"
ls -la /opt/nginx/ 2>/dev/null || echo "   Katalog nie istnieje"
echo ""
echo "   /opt/nginx/conf.d:"
ls -la /opt/nginx/conf.d/ 2>/dev/null || echo "   Katalog nie istnieje"
echo ""

# 2. Sprawdź docker-compose
echo "2. Sprawdzam docker-compose nginx..."
if [ -f "/opt/nginx/docker-compose.yml" ]; then
    echo "   Plik: /opt/nginx/docker-compose.yml"
    grep -A5 "volumes:" /opt/nginx/docker-compose.yml
elif [ -f "$HOME/nginx/docker-compose.yml" ]; then
    echo "   Plik: $HOME/nginx/docker-compose.yml"
    grep -A5 "volumes:" $HOME/nginx/docker-compose.yml
else
    echo "   Nie znaleziono docker-compose.yml"
fi
echo ""

# 3. Sprawdź mounty w kontenerze
echo "3. Sprawdzam mounty w kontenerze nginx..."
docker exec nginx-proxy ls -la /etc/nginx/conf.d/ 2>/dev/null || echo "   Kontener nie działa lub brak dostępu"
echo ""

# 4. Sprawdź czy nginx ładuje conf.d
echo "4. Sprawdzam główną konfigurację nginx..."
docker exec nginx-proxy cat /etc/nginx/nginx.conf 2>/dev/null | grep -A2 "include.*conf.d" || echo "   Nie można odczytać"
echo ""

# 5. Pokaż status kontenera
echo "5. Status kontenera nginx-proxy..."
docker ps -a | grep nginx-proxy
echo ""

echo "=== Koniec diagnostyki ==="
echo ""
echo "Rozwiązania:"
echo "1. Jeśli /opt/nginx/ nie istnieje:"
echo "   sudo mkdir -p /opt/nginx/conf.d"
echo ""
echo "2. Jeśli docker-compose nie montuje conf.d, dodaj do volumes:"
echo "   - /opt/nginx/conf.d:/etc/nginx/conf.d:ro"
echo ""
echo "3. Zrestartuj nginx po zmianach:"
echo "   cd /ścieżka/do/nginx && docker-compose restart"
