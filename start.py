#!/usr/bin/env python3
"""
🚀 Jusper - AI-Powered E-commerce Scraper
Avvio del server principale

FLUSSO PRINCIPALE:
1. Parsing argomenti da linea di comando
2. Setup path e directory di lavoro
3. Avvio server FastAPI con uvicorn
4. Configurazione logging e auto-reload
5. Auto-apertura browser

DIPENDENZE:
- uvicorn: Server ASGI per FastAPI
- argparse: Parsing argomenti linea di comando
- pathlib: Gestione path cross-platform
- os, sys: Operazioni sistema
- webbrowser: Auto-apertura browser
- threading: Avvio browser in thread separato

SCRIPT CHE RICHIAMANO QUESTO:
- Procfile: Per deployment su Railway/Heroku
- railway.json: Configurazione deployment Railway
- Comando diretto: python start.py

SCRIPT RICHIAMATI DA QUESTO:
- mr_anto_scraper.py: Server FastAPI principale
- Tutti i moduli Backend/ importati da mr_anto_scraper.py

ARGOMENTI SUPPORTATI:
--port: Porta del server (default: 8000)
--host: Host del server (default: 0.0.0.0)
--reload: Abilita auto-reload per sviluppo
--no-browser: Disabilita auto-apertura browser
"""

import os
import sys
import argparse
import uvicorn
import webbrowser
import threading
import time
from pathlib import Path

def open_browser(host: str, port: int, delay: int = 2):
    """
    Apre il browser dopo un delay
    
    FLUSSO:
    1. Attende che il server sia pronto
    2. Apre browser con URL del server (usa localhost per browser)
    3. Gestisce errori di apertura browser
    
    UTILIZZO:
    - Chiamato in thread separato per non bloccare server
    - Delay per permettere al server di avviarsi
    """
    time.sleep(delay)
    # Usa localhost per il browser anche se il server è su 0.0.0.0
    browser_host = "localhost" if host == "0.0.0.0" else host
    url = f"http://{browser_host}:{port}"
    try:
        webbrowser.open(url)
        print(f"🌐 Browser aperto: {url}")
    except Exception as e:
        print(f"⚠️ Errore apertura browser: {e}")
        print(f"🔗 Apri manualmente: {url}")

def main():
    """
    Funzione principale di avvio
    
    FLUSSO:
    1. Configura parser per argomenti linea di comando
    2. Parsing argomenti (port, host, reload, no-browser)
    3. Setup path Backend per import moduli
    4. Cambio directory di lavoro
    5. Avvio thread per auto-apertura browser
    6. Avvio server uvicorn con configurazione
    
    UTILIZZO:
    - Entry point principale dell'applicazione
    - Gestisce configurazione server per sviluppo/produzione
    """
    parser = argparse.ArgumentParser(description="Avvia Jusper Scraper")
    parser.add_argument("--port", type=int, default=8000, help="Porta del server (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host del server (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Abilita auto-reload per sviluppo")
    parser.add_argument("--no-browser", action="store_true", help="Disabilita auto-apertura browser")
    
    args = parser.parse_args()
    
    # Aggiungi la directory Backend al path per import moduli
    backend_path = Path(__file__).parent / "Backend"
    sys.path.insert(0, str(backend_path))
    
    # Cambia directory di lavoro per file relativi
    os.chdir(backend_path)
    
    print("🚀 Avvio Jusper Scraper...")
    print(f"📁 Directory: {os.getcwd()}")
    print(f"🌐 Server: http://{args.host}:{args.port}")
    print(f"🔄 Auto-reload: {'Sì' if args.reload else 'No'}")
    
    # Test import prima di avviare il server
    try:
        print("🔍 Testando import dei moduli...")
        import main
        print("✅ Modulo main importato con successo")
        
        # Verifica che l'app sia definita
        if hasattr(main, 'app'):
            print("✅ App FastAPI trovata nel modulo main")
        else:
            print("❌ App FastAPI non trovata nel modulo main")
            return
            
    except ImportError as e:
        print(f"❌ Errore import modulo main: {e}")
        print("💡 Verifica che tutte le dipendenze siano installate:")
        print("   pip install -r requirements.txt")
        return
    except Exception as e:
        print(f"❌ Errore generico durante l'import: {e}")
        return
    
    # Avvia thread per auto-apertura browser (se non disabilitato)
    if not args.no_browser:
        browser_thread = threading.Thread(
            target=open_browser, 
            args=(args.host, args.port),
            daemon=True
        )
        browser_thread.start()
        print("🌐 Auto-apertura browser abilitata")
    else:
        print("🌐 Auto-apertura browser disabilitata")
    
    # Avvia il server FastAPI con uvicorn
    # main:app -> importa app da main.py
    try:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Errore avvio server: {e}")
        print("💡 Verifica che la porta non sia già in uso")

if __name__ == "__main__":
    main() 