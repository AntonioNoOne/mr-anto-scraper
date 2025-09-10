#!/usr/bin/env python3
"""
Test Bing Extraction
Verifica che Bing estragga correttamente prezzi e titoli
"""

import asyncio
import sys
import os
sys.path.append('Backend')

from google_search_integration import GoogleSearchIntegration

async def test_bing_extraction():
    """Test estrazione Bing"""
    
    print("🧪 === TEST BING EXTRACTION ===")
    
    # Inizializza GoogleSearchIntegration
    gsi = GoogleSearchIntegration()
    
    # Test query
    query = "iphone 15"
    print(f"🔍 Test query: {query}")
    
    try:
        # Test Bing Shopping
        print("\n🦆 === TEST BING SHOPPING ===")
        bing_results = await gsi._try_bing_shopping(query)
        
        print(f"📊 Risultati Bing: {len(bing_results)}")
        
        if bing_results:
            print("\n✅ RISULTATI BING TROVATI:")
            for i, result in enumerate(bing_results[:5], 1):
                name = result.get('name', 'N/A')
                price = result.get('price', 'N/A')
                price_numeric = result.get('price_numeric', 0)
                site = result.get('site', 'N/A')
                source = result.get('source', 'N/A')
                
                print(f"\n🔍 Risultato {i}:")
                print(f"  📱 Nome: {name}")
                print(f"  💰 Prezzo: {price} (numerico: {price_numeric})")
                print(f"  🌐 Sito: {site}")
                print(f"  🔗 Fonte: {source}")
            
            # Conta prezzi validi
            valid_prices = [r for r in bing_results if r.get('price_numeric', 0) > 0]
            print(f"\n💰 Prezzi validi: {len(valid_prices)}/{len(bing_results)}")
            
            if len(valid_prices) > 0:
                print("🎉 SUCCESSO: Bing estrae prezzi correttamente!")
                return True
            else:
                print("⚠️ PROBLEMA: Bing non estrae prezzi validi")
                return False
        else:
            print("❌ PROBLEMA: Nessun risultato Bing")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_duckduckgo_extraction():
    """Test estrazione DuckDuckGo"""
    
    print("\n🦆 === TEST DUCKDUCKGO EXTRACTION ===")
    
    # Inizializza GoogleSearchIntegration
    gsi = GoogleSearchIntegration()
    
    # Test query
    query = "iphone 15"
    print(f"🔍 Test query: {query}")
    
    try:
        # Test DuckDuckGo Shopping
        duckduckgo_results = await gsi._try_duckduckgo_shopping(query)
        
        print(f"📊 Risultati DuckDuckGo: {len(duckduckgo_results)}")
        
        if duckduckgo_results:
            print("\n✅ RISULTATI DUCKDUCKGO TROVATI:")
            for i, result in enumerate(duckduckgo_results[:3], 1):
                name = result.get('name', 'N/A')
                price = result.get('price', 'N/A')
                price_numeric = result.get('price_numeric', 0)
                site = result.get('site', 'N/A')
                source = result.get('source', 'N/A')
                
                print(f"\n🔍 Risultato {i}:")
                print(f"  📱 Nome: {name}")
                print(f"  💰 Prezzo: {price} (numerico: {price_numeric})")
                print(f"  🌐 Sito: {site}")
                print(f"  🔗 Fonte: {source}")
            
            # Conta prezzi validi
            valid_prices = [r for r in duckduckgo_results if r.get('price_numeric', 0) > 0]
            print(f"\n💰 Prezzi validi: {len(valid_prices)}/{len(duckduckgo_results)}")
            
            if len(valid_prices) > 0:
                print("🎉 SUCCESSO: DuckDuckGo estrae prezzi correttamente!")
                return True
            else:
                print("⚠️ PROBLEMA: DuckDuckGo non estrae prezzi validi")
                return False
        else:
            print("❌ PROBLEMA: Nessun risultato DuckDuckGo")
            return False
            
    except Exception as e:
        print(f"❌ Errore durante il test DuckDuckGo: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Test principale"""
    
    print("🚀 Avvio test estrazione locale...")
    
    # Test DuckDuckGo
    duckduckgo_success = await test_duckduckgo_extraction()
    
    # Test Bing
    bing_success = await test_bing_extraction()
    
    print("\n📊 === RIEPILOGO TEST ===")
    print(f"🦆 DuckDuckGo: {'✅ SUCCESSO' if duckduckgo_success else '❌ FALLITO'}")
    print(f"🔍 Bing: {'✅ SUCCESSO' if bing_success else '❌ FALLITO'}")
    
    if duckduckgo_success and bing_success:
        print("\n🎉 TUTTI I TEST PASSATI!")
        print("🎯 I risultati sono corretti, possiamo pushare!")
    else:
        print("\n⚠️ ALCUNI TEST FALLITI!")
        print("🔧 Serve ulteriore debugging")

if __name__ == "__main__":
    asyncio.run(main())
