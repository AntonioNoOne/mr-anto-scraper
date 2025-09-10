#!/usr/bin/env python3
"""
Test Google Search in locale
Verifica che la ricerca online funzioni correttamente
"""

import requests
import json
import time

def test_google_search():
    """Test ricerca Google in locale"""
    
    print("🧪 === TEST GOOGLE SEARCH LOCALE ===")
    
    # URL del server locale
    url = "http://127.0.0.1:8000/google-search"
    
    # Dati di test
    test_data = {
        "name": "iphone 15",
        "brand": "",
        "price": "",
        "source": ""
    }
    
    print(f"📡 Invio richiesta a: {url}")
    print(f"📦 Dati: {test_data}")
    
    try:
        # Invia richiesta
        response = requests.post(url, json=test_data, timeout=120)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Successo! Risultati ricevuti:")
            print(f"📊 Totale risultati: {len(data.get('results', []))}")
            
            # Mostra i primi 5 risultati
            results = data.get('results', [])
            for i, result in enumerate(results[:5], 1):
                name = result.get('name', 'N/A')
                price = result.get('price', 'N/A')
                site = result.get('site', 'N/A')
                source = result.get('source', 'N/A')
                
                print(f"\n🔍 Risultato {i}:")
                print(f"  📱 Nome: {name}")
                print(f"  💰 Prezzo: {price}")
                print(f"  🌐 Sito: {site}")
                print(f"  🔗 Fonte: {source}")
            
            # Conta risultati per fonte
            sources = {}
            for result in results:
                source = result.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n📊 Risultati per fonte:")
            for source, count in sources.items():
                print(f"  {source}: {count}")
            
            # Verifica se ci sono prezzi validi
            valid_prices = [r for r in results if r.get('price') and r.get('price') != 'Prezzo non disponibile']
            print(f"\n💰 Prezzi validi: {len(valid_prices)}/{len(results)}")
            
            if len(valid_prices) > 0:
                print("🎉 SUCCESSO: Trovati prodotti con prezzi validi!")
                return True
            else:
                print("⚠️ ATTENZIONE: Nessun prezzo valido trovato")
                return False
                
        else:
            print(f"❌ Errore HTTP: {response.status_code}")
            print(f"📄 Risposta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout: La richiesta ha impiegato troppo tempo")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Errore connessione: Il server non è raggiungibile")
        return False
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Avvio test Google Search locale...")
    print("⏳ Attendo 5 secondi per il server...")
    time.sleep(5)
    
    success = test_google_search()
    
    if success:
        print("\n✅ TEST COMPLETATO CON SUCCESSO!")
        print("🎯 I risultati sono corretti, possiamo pushare!")
    else:
        print("\n❌ TEST FALLITO!")
        print("🔧 Serve ulteriore debugging")
