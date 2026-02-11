#!/bin/bash
# Skrypt aktualizacji nginx na malinie
# Uruchom po skopiowaniu pliku default.conf do /tmp/

set -e  # Zatrzymaj przy błędzie

echo "🔧 Aktualizacja konfiguracji Nginx dla SmartHome"
echo "================================================"

# Kolory
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Sprawdź czy plik istnieje
if [ ! -f "/tmp/default.conf" ]; then
    echo -e "${RED}❌ Błąd: Nie znaleziono /tmp/default.conf${NC}"
    echo "Najpierw skopiuj plik używając:"
    echo "scp nginx-standalone/conf.d/default.conf adas.rakieta@192.168.1.218:/tmp/default.conf"
    exit 1
fi

# Sprawdź możliwe lokalizacje konfiguracji nginx
NGINX_CONFIG_DIR=""
if [ -d "/opt/nginx/conf.d" ]; then
    NGINX_CONFIG_DIR="/opt/nginx/conf.d"
elif [ -d "/opt/nginx" ]; then
    # Katalog /opt/nginx istnieje, ale brak conf.d - utwórz
    echo -e "${YELLOW}📁 Tworzę katalog /opt/nginx/conf.d...${NC}"
    sudo mkdir -p /opt/nginx/conf.d
    NGINX_CONFIG_DIR="/opt/nginx/conf.d"
elif [ -d "/etc/nginx/conf.d" ]; then
    # Używaj systemowego katalogu nginx
    NGINX_CONFIG_DIR="/etc/nginx/conf.d"
else
    echo -e "${RED}❌ Błąd: Nie znaleziono katalogu konfiguracji nginx${NC}"
    echo "Sprawdź gdzie jest nginx używając: docker exec nginx-proxy ls -la /etc/nginx/"
    exit 1
fi

echo -e "${GREEN}✓ Znaleziono katalog konfiguracji: $NGINX_CONFIG_DIR${NC}"

# Utwórz backup z datą
BACKUP_FILE="$NGINX_CONFIG_DIR/default.conf.backup.$(date +%Y%m%d_%H%M%S)"
if [ -f "$NGINX_CONFIG_DIR/default.conf" ]; then
    echo -e "${YELLOW}📦 Tworzę backup: $BACKUP_FILE${NC}"
    sudo cp "$NGINX_CONFIG_DIR/default.conf" "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backup utworzony${NC}"
else
    echo -e "${YELLOW}⚠️  Plik default.conf nie istnieje, tworzę nowy${NC}"
fi

# Skopiuj nowy plik
echo -e "${YELLOW}📄 Kopiuję nową konfigurację...${NC}"
sudo mv /tmp/default.conf "$NGINX_CONFIG_DIR/default.conf"
sudo chown root:root "$NGINX_CONFIG_DIR/default.conf"
sudo chmod 644 "$NGINX_CONFIG_DIR/default.conf"
echo -e "${GREEN}✓ Plik skopiowany${NC}"

# Sprawdź składnię nginx
echo -e "${YELLOW}🔍 Sprawdzam składnię nginx...${NC}"
if docker exec nginx-proxy nginx -t 2>&1; then
    echo -e "${GREEN}✓ Składnia poprawna${NC}"
else
    echo -e "${RED}❌ Błąd składni! Przywracam backup...${NC}"
    if [ -f "$BACKUP_FILE" ]; then
        sudo cp "$BACKUP_FILE" "$NGINX_CONFIG_DIR/default.conf"
        echo -e "${YELLOW}Backup przywrócony${NC}"
    fi
    exit 1
fi

# Przeładuj nginx
echo -e "${YELLOW}🔄 Przeładowuję nginx...${NC}"
if docker exec nginx-proxy nginx -s reload; then
    echo -e "${GREEN}✓ Nginx przeładowany${NC}"
else
    echo -e "${YELLOW}⚠️  Reload nie zadziałał, restartuję kontener...${NC}"
    docker restart nginx-proxy
    echo -e "${GREEN}✓ Kontener zrestartowany${NC}"
fi

# Restart SmartHome
echo -e "${YELLOW}🔄 Restartuję SmartHome...${NC}"
if docker restart smarthome_app; then
    echo -e "${GREEN}✓ SmartHome zrestartowany${NC}"
else
    echo -e "${RED}❌ Nie udało się zrestartować SmartHome${NC}"
    echo "Sprawdź czy kontener nazywa się 'smarthome_app' używając: docker ps -a"
fi

# Wyświetl status
echo ""
echo "================================================"
echo -e "${GREEN}✅ Aktualizacja zakończona!${NC}"
echo ""
echo "📋 Kolejne kroki:"
echo "1. Wyczyść cookies w przeglądarce dla malina.tail384b18.ts.net"
echo "2. Zaloguj się ponownie do SmartHome"
echo "3. Sprawdź logi jeśli coś nie działa:"
echo "   - docker logs smarthome_app --tail 50"
if [ -f "$BACKUP_FILE" ]; then
    echo "📦 Backup zapisany w: $BACKUP_FILE"
fi
echo "📁 Konfiguracja w: $NGINX_CONFIG_DIR/default.confl 50"
echo ""
echo "📦 Backup zapisany w: $BACKUP_FILE"
echo "================================================"

# Sprawdź czy ProxyFix jest włączony
echo ""
echo "🔍 Weryfikacja ProxyFix w SmartHome..."
if docker logs smarthome_app 2>&1 | grep -q "ProxyFix middleware enabled"; then
    echo -e "${GREEN}✓ ProxyFix middleware jest włączony${NC}"
else
    echo -e "${YELLOW}⚠️  ProxyFix middleware nie znaleziony w logach${NC}"
    echo "To może oznaczać że kontener używa starego obrazu."
    echo "Przebuduj obraz SmartHome i uruchom ponownie."
fi

echo ""
echo "🌐 Otwórz w przeglądarce: https://malina.tail384b18.ts.net/"
