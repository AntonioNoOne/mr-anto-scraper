#!/usr/bin/env python3
"""
Script per inizializzare selettori predefiniti nel database
"""

import asyncio
from selector_database import SelectorDatabase

async def main():
    """Inizializza selettori predefiniti"""
    print("🚀 Inizializzazione selettori predefiniti...")
    
    # Crea istanza database
    db = SelectorDatabase()
    
    # Inizializza selettori predefiniti
    await db.initialize_default_selectors()
    
    print("✅ Selettori predefiniti inizializzati con successo!")
    
    # Chiudi connessione
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
