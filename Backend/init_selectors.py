#!/usr/bin/env python3

"""
Init Selectors - Inizializza selettori predefiniti nel database
================================================================

Carica selettori di qualità predefiniti per siti comuni nel database
invece di hardcodarli nel codice.

USO:
- python init_selectors.py
"""

import asyncio
import sys
import os

# Aggiungi directory corrente al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from selector_database import SelectorDatabase

async def main():
    """Inizializza selettori predefiniti"""
    try:
        print("🚀 Inizializzazione selettori predefiniti...")
        
        # Inizializza database
        selector_db = SelectorDatabase()
        # initialize_database() viene chiamato automaticamente nel costruttore
        
        # Inizializza selettori predefiniti
        await selector_db.initialize_default_selectors()
        
        print("✅ Inizializzazione completata!")
        
        # Mostra selettori caricati
        print("\n📊 Selettori disponibili per dominio:")
        domains = ['amazon', 'unieuro', 'mediaworld', 'euronics', 'trony', 'conad', 'carrefour', 'esselunga', 'immobiliare', 'casa']
        
        for domain in domains:
            selectors = await selector_db.get_quality_selectors(domain)
            print(f"  - {domain}: {len(selectors)} selettori")
        
        print(f"\n🎯 Totale selettori predefiniti: {len(domains)}")
        
    except Exception as e:
        print(f"❌ Errore inizializzazione: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("🎉 Inizializzazione completata con successo!")
    else:
        print("💥 Inizializzazione fallita!")
        sys.exit(1)
