#!/usr/bin/env python3
"""
Debug OpenAI Input - Mostra cosa riceve OpenAI
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_openai_input():
    """Debug cosa riceve OpenAI"""
    
    print("🔍 Debug OpenAI Input - Tempocasa")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Avvia browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://tempocasa.it/it/vendita/bologna/zola-predosa"
        
        try:
            # Vai alla pagina con timeout più lungo
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print(f"✅ Status: {response.status}")
            
            # Aspetta caricamento
            await page.wait_for_timeout(5000)
            
            # Ottieni HTML
            html_content = await page.content()
            print(f"📄 HTML length: {len(html_content)}")
            
            # Cerca pattern specifici
            print("\n🔍 Pattern Search:")
            
            # Cerca titoli immobili
            villa_count = html_content.lower().count('villa')
            appartamento_count = html_content.lower().count('appartamento')
            casa_count = html_content.lower().count('casa')
            trilocale_count = html_content.lower().count('trilocale')
            bilocale_count = html_content.lower().count('bilocale')
            
            print(f"  🏠 Villa: {villa_count}")
            print(f"  🏢 Appartamento: {appartamento_count}")
            print(f"  🏡 Casa: {casa_count}")
            print(f"  🏘️ Trilocale: {trilocale_count}")
            print(f"  🏘️ Bilocale: {bilocale_count}")
            
            # Cerca prezzi
            euro_count = html_content.count('€')
            price_patterns = ['€', 'euro', 'prezzo']
            for pattern in price_patterns:
                count = html_content.lower().count(pattern)
                print(f"  💰 {pattern}: {count}")
            
            # Cerca link immobili
            vendita_links = html_content.count('/vendita/')
            annuncio_links = html_content.count('/annuncio/')
            immobile_links = html_content.count('/immobile/')
            
            print(f"  🔗 /vendita/: {vendita_links}")
            print(f"  🔗 /annuncio/: {annuncio_links}")
            print(f"  🔗 /immobile/: {immobile_links}")
            
            # Mostra sample HTML
            print(f"\n📄 HTML Sample (primi 2000 caratteri):")
            print("-" * 50)
            print(html_content[:2000])
            print("-" * 50)
            
            # Cerca sezioni specifiche
            if 'class="card' in html_content:
                print("✅ Trovate card immobiliari")
            else:
                print("❌ Nessuna card immobiliare trovata")
                
            if 'data-testid' in html_content:
                print("✅ Trovati data-testid")
            else:
                print("❌ Nessun data-testid trovato")
                
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_openai_input())
