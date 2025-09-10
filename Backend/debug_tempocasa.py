#!/usr/bin/env python3
"""
Debug Tempocasa - Test diretto con Playwright
"""

import asyncio
import logging
from playwright.async_api import async_playwright

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_tempocasa():
    """Debug diretto delle pagine Tempocasa"""
    
    print("🔍 Debug Tempocasa - Test Diretto")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Avvia browser
        browser = await p.chromium.launch(headless=False)  # Visibile per debug
        page = await browser.new_page()
        
        # Test pagine
        test_urls = [
            "https://tempocasa.it/it/vendita/bologna/zola-predosa",
            "https://tempocasa.it/it/vendita/bologna/zola-predosa/trilocale/2186414"
        ]
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n🔍 Test {i}: {url}")
            print("-" * 50)
            
            try:
                # Vai alla pagina
                response = await page.goto(url, wait_until="networkidle")
                print(f"✅ Status: {response.status}")
                
                # Aspetta un po' per il caricamento
                await page.wait_for_timeout(3000)
                
                # Ottieni titolo
                title = await page.title()
                print(f"📄 Titolo: {title}")
                
                # Conta elementi
                h1_count = await page.locator("h1").count()
                h2_count = await page.locator("h2").count()
                h3_count = await page.locator("h3").count()
                print(f"📊 H1: {h1_count}, H2: {h2_count}, H3: {h3_count}")
                
                # Cerca prezzi
                price_elements = await page.locator("text=/€|euro|prezzo/i").count()
                print(f"💰 Elementi con prezzo: {price_elements}")
                
                # Cerca link immobili
                property_links = await page.locator("a[href*='/vendita/'], a[href*='/affitto/'], a[href*='/immobile/']").count()
                print(f"🏠 Link immobili: {property_links}")
                
                # Ottieni HTML sample
                html_sample = await page.content()
                print(f"📄 HTML length: {len(html_sample)}")
                
                # Cerca pattern specifici
                if "tempocasa" in html_sample.lower():
                    print("✅ Sito Tempocasa rilevato")
                else:
                    print("❌ Sito Tempocasa NON rilevato")
                
                if "zola predosa" in html_sample.lower():
                    print("✅ Zola Predosa rilevato")
                else:
                    print("❌ Zola Predosa NON rilevato")
                
                # Cerca errori o blocchi
                if "access denied" in html_sample.lower() or "blocked" in html_sample.lower():
                    print("❌ Pagina bloccata")
                elif "captcha" in html_sample.lower():
                    print("❌ Captcha rilevato")
                else:
                    print("✅ Nessun blocco rilevato")
                
            except Exception as e:
                print(f"❌ Errore: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_tempocasa())
