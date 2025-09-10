#!/usr/bin/env python3

"""
Setup Browserbase - Configurazione per Stagehand
===============================================

Script per configurare Browserbase e attivare Stagehand completamente.
"""

import os
import sys

def setup_browserbase():
    """Configura Browserbase per Stagehand"""
    print("🌐 Configurazione Browserbase per Stagehand")
    print("=" * 50)
    
    # Controlla se esiste già
    if os.getenv('BROWSERBASE_API_KEY'):
        print("✅ BROWSERBASE_API_KEY già configurata")
        return True
    
    print("📝 Per attivare Stagehand hai bisogno di Browserbase:")
    print("   1. Vai su: https://browserbase.com")
    print("   2. Crea un account gratuito")
    print("   3. Ottieni la tua API key")
    print("   4. Inseriscila qui sotto")
    print()
    
    api_key = input("Browserbase API Key: ").strip()
    
    if not api_key:
        print("❌ API Key non inserita")
        return False
    
    # Salva nel file .env
    try:
        with open('env.local', 'a') as f:
            f.write(f"\n# Browserbase Configuration\n")
            f.write(f"BROWSERBASE_API_KEY={api_key}\n")
        
        print("✅ API Key salvata in env.local")
        
        # Imposta la variabile d'ambiente per questa sessione
        os.environ['BROWSERBASE_API_KEY'] = api_key
        
        print("✅ Variabile d'ambiente impostata")
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False

def test_stagehand_with_browserbase():
    """Testa Stagehand con Browserbase"""
    try:
        print("🧪 Testando Stagehand con Browserbase...")
        
        from stagehand_extractor import stagehand_extractor
        
        # Test estrazione
        import asyncio
        async def test():
            products = await stagehand_extractor.extract_products_from_search("iPhone 15 128GB", "duckduckgo")
            print(f"✅ Stagehand funzionante: {len(products)} prodotti estratti")
            return len(products) > 0
        
        return asyncio.run(test())
        
    except Exception as e:
        print(f"❌ Errore test Stagehand: {e}")
        return False

def main():
    """Funzione principale"""
    print("🚀 Setup Browserbase per Stagehand")
    print("=" * 40)
    
    # Setup API key
    if setup_browserbase():
        print("\n🧪 Testando configurazione...")
        if test_stagehand_with_browserbase():
            print("\n🎉 Setup completato con successo!")
            print("✅ Ora Stagehand è completamente attivo")
            print("\n💡 Prossimi passi:")
            print("   1. Riavvia il server")
            print("   2. Testa la ricerca Google con AI")
            return True
        else:
            print("\n❌ Test fallito")
            return False
    else:
        print("\n❌ Setup fallito")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
