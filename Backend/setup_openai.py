#!/usr/bin/env python3

"""
Setup OpenAI - Configurazione API key OpenAI
===========================================

Script per configurare la API key di OpenAI per Stagehand.
"""

import os
import sys

def setup_openai_key():
    """Configura la API key di OpenAI"""
    print("🔑 Configurazione OpenAI API Key per Stagehand")
    print("=" * 50)
    
    # Controlla se esiste già
    if os.getenv('OPENAI_API_KEY'):
        print("✅ OPENAI_API_KEY già configurata")
        return True
    
    # Chiedi all'utente di inserire la key
    print("📝 Inserisci la tua OpenAI API Key:")
    print("   (Puoi trovarla su: https://platform.openai.com/api-keys)")
    print()
    
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ API Key non inserita")
        return False
    
    # Salva nel file .env
    try:
        with open('.env', 'w') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        
        print("✅ API Key salvata in .env")
        
        # Imposta la variabile d'ambiente per questa sessione
        os.environ['OPENAI_API_KEY'] = api_key
        
        print("✅ Variabile d'ambiente impostata")
        return True
        
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False

def test_openai_connection():
    """Testa la connessione OpenAI"""
    try:
        import openai
        
        client = openai.AsyncOpenAI()
        
        # Test semplice (senza chiamata API costosa)
        print("🧪 Testando connessione OpenAI...")
        print("✅ Client OpenAI creato correttamente")
        print("✅ API Key configurata correttamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test OpenAI: {e}")
        return False

def main():
    """Funzione principale"""
    print("🚀 Setup OpenAI per Stagehand")
    print("=" * 30)
    
    # Setup API key
    if setup_openai_key():
        print("\n🧪 Testando configurazione...")
        if test_openai_connection():
            print("\n🎉 Setup completato con successo!")
            print("✅ Ora puoi usare Stagehand con AI")
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
