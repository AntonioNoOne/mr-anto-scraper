"""
Stato condiviso dell'applicazione (single source of truth).

Le istanze dei componenti sono inizializzate a None all'import e assegnate
realmente nell'handler di startup di main.py (es. app_state.extractor = FastAIExtractor()).
I router leggono queste attributi come app_state.<name>.
"""

# Istanze dei componenti (inizializzate in startup_event di main.py)
extractor = None
ai_comparator = None
chat_manager = None
selector_db = None
google_search = None
historical_db = None
price_monitor = None
price_scheduler = None
url_monitor = None

# Configurazione globale del browser (condivisa tra i router)
browser_config = {
    "mode": "stealth",
    "timeout": 60,
    "human_delay": 2.0,
    "user_agent": "auto",
    "proxy": None
}
