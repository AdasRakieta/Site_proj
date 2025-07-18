#!/usr/bin/env python3
"""
Skrypt uruchamiający serwer Smart Home
Dostosowany do środowiska Windows z obsługą SocketIO
"""
import os
import sys
from app import app, socketio

def main():
    """Główna funkcja uruchamiająca serwer"""
    print("=== Smart Home Server ===")
    print("Uruchamianie serwera...")
    
    # Sprawdź czy wszystkie pliki konfiguracyjne istnieją
    config_files = [
        'smart_home_config.json',
        'notifications_settings.json'
    ]
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"UWAGA: Plik konfiguracyjny {config_file} nie istnieje")
    
    # Sprawdź czy folder dla zdjęć profilowych istnieje
    profile_pics_dir = 'static/profile_pictures'
    if not os.path.exists(profile_pics_dir):
        os.makedirs(profile_pics_dir)
        print(f"Utworzono folder: {profile_pics_dir}")
    
    # Parametry serwera
    host = "0.0.0.0"
    port = 5000
    debug = False
    
    # Sprawdź argumenty wiersza poleceń
    if len(sys.argv) > 1:
        if "--debug" in sys.argv:
            debug = True
            print("Tryb DEBUG włączony")
        if "--port" in sys.argv:
            try:
                port_idx = sys.argv.index("--port")
                port = int(sys.argv[port_idx + 1])
            except (ValueError, IndexError):
                print("Błędna wartość portu, używam domyślnego: 5000")
    
    print(f"Serwer będzie dostępny pod adresem: http://{host}:{port}")
    print("Aby zatrzymać serwer, naciśnij Ctrl+C")
    print("-" * 50)
    
    try:
        # Uruchom serwer SocketIO (najlepszy dla Windows)
        socketio.run(
            app, 
            debug=debug, 
            host=host, 
            port=port,
            use_reloader=False,  # Wyłącz reloader w produkcji
            allow_unsafe_werkzeug=True  # Dla kompatybilności
        )
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...")
    except Exception as e:
        print(f"Błąd serwera: {e}")
        return 1
    
    print("Serwer zatrzymany")
    return 0

if __name__ == "__main__":
    sys.exit(main())
