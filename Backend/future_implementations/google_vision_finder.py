"""
Google Vision Finder - Sistema per trovare siti tramite Playwright + AI Vision
Usa Playwright per navigare Google e AI Vision per leggere i risultati
"""

import asyncio
import base64
import json
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus, urlparse
from playwright.async_api import async_playwright
import requests
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class GoogleVisionFinder:
    """Sistema per trovare siti tramite Playwright + AI Vision"""
    
    def __init__(self):
        self.target_sites = [
            'mediaworld.it',
            'unieuro.it', 
            'amazon.it',
            'euronics.it',
            'eprice.it',
            'trony.it',
            'expert.it',
            'comet.it',
            'monclick.it'
        ]
        
        # API Keys per Vision
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        logger.info("🔍 Google Vision Finder inizializzato")
    
    async def search_product_sites_with_vision(self, product_name: str, brand: str = "", model: str = "") -> Dict[str, Any]:
        """Cerca siti che vendono un prodotto usando Playwright + Vision"""
        try:
            # Costruisci query di ricerca
            search_query = self._build_search_query(product_name, brand, model)
            logger.info(f"🔍 Ricerca Google Vision: {search_query}")
            
            # Usa Playwright per navigare Google
            sites_found = await self._search_with_playwright_vision(search_query)
            
            # Genera URLs per ogni sito
            site_urls = self._generate_product_urls(sites_found, search_query)
            
            return {
                'success': True,
                'product_query': search_query,
                'method': 'playwright_vision',
                'total_sites_found': len(sites_found),
                'recommended_sites': site_urls[:10],
                'all_sites': sites_found,
                'search_timestamp': datetime.now().isoformat(),
                'message': f"🤖 Vision AI ha trovato {len(sites_found)} siti che vendono questo prodotto"
            }
            
        except Exception as e:
            logger.error(f"❌ Errore Google Vision: {e}")
            
            # Fallback alla lista predefinita
            fallback_sites = self.target_sites.copy()
            fallback_urls = self._generate_product_urls(fallback_sites, search_query if 'search_query' in locals() else product_name)
            
            return {
                'success': True,
                'product_query': search_query if 'search_query' in locals() else product_name,
                'method': 'fallback',
                'total_sites_found': len(fallback_sites),
                'recommended_sites': fallback_urls[:10],
                'all_sites': fallback_sites,
                'search_timestamp': datetime.now().isoformat(),
                'message': f"🔄 Fallback: usando {len(fallback_sites)} siti predefiniti",
                'error': str(e)
            }
    
    def _build_search_query(self, product_name: str, brand: str = "", model: str = "") -> str:
        """Costruisce query di ricerca ottimizzata"""
        parts = [product_name]
        if brand:
            parts.append(brand)
        if model:
            parts.append(model)
        
        query = " ".join(parts) + " prezzo acquista online"
        return query.strip()
    
    async def _search_with_playwright_vision(self, query: str) -> List[str]:
        """Usa Playwright per navigare Google e Vision AI per leggere risultati"""
        sites_found = []
        
        async with async_playwright() as p:
            try:
                # Lancia browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Naviga a Google
                encoded_query = quote_plus(query)
                google_url = f"https://www.google.com/search?q={encoded_query}&hl=it&gl=IT"
                logger.info(f"🌐 Navigazione: {google_url}")
                
                await page.goto(google_url, wait_until='networkidle', timeout=30000)
                
                # Attendi caricamento completo
                await page.wait_for_timeout(3000)
                
                # Gestisci popup cookie se presente
                try:
                    cookie_button = page.locator('button:has-text("Accetta tutti"), button:has-text("Accept all"), button:has-text("I agree")')
                    if await cookie_button.count() > 0:
                        await cookie_button.first.click()
                        await page.wait_for_timeout(2000)
                except:
                    pass
                
                # Cattura screenshot della pagina risultati
                screenshot = await page.screenshot(type='png', full_page=True)
                
                # Analizza screenshot con AI Vision
                sites_from_vision = await self._analyze_screenshot_with_ai(screenshot, query)
                sites_found.extend(sites_from_vision)
                
                # Cerca anche nei link della pagina (backup)
                links = await page.query_selector_all('a[href]')
                logger.info(f"🔗 Link trovati nella pagina: {len(links)}")
                
                for link in links[:50]:  # Max 50 link per performance
                    try:
                        href = await link.get_attribute('href')
                        if href and href.startswith('http'):
                            domain = urlparse(href).netloc.lower()
                            if domain and any(target in domain for target in self.target_sites):
                                if domain not in sites_found:
                                    sites_found.append(domain)
                                    logger.info(f"✅ Sito trovato nei link: {domain}")
                    except:
                        continue
                
                await browser.close()
                
            except Exception as e:
                logger.error(f"❌ Errore Playwright: {e}")
                if 'browser' in locals():
                    await browser.close()
        
        logger.info(f"🎯 Vision + Link: {len(sites_found)} siti trovati: {sites_found}")
        return sites_found
    
    async def _analyze_screenshot_with_ai(self, screenshot_bytes: bytes, query: str) -> List[str]:
        """Analizza screenshot con AI Vision per trovare siti e-commerce"""
        try:
            # Converti screenshot in base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Prompt per AI Vision
            prompt = f"""
Analizza questa screenshot dei risultati di Google per la ricerca: "{query}"

Trova tutti i siti e-commerce italiani che vendono questo prodotto. 
Cerca domini come: mediaworld.it, unieuro.it, amazon.it, euronics.it, eprice.it, trony.it, expert.it, comet.it, ecc.

Restituisci SOLO una lista JSON dei domini trovati, esempio:
["mediaworld.it", "amazon.it", "unieuro.it"]

Non aggiungere spiegazioni, solo la lista JSON.
"""
            
            # Prova prima Gemini Vision
            if self.gemini_api_key:
                sites = await self._call_gemini_vision(prompt, screenshot_base64)
                if sites:
                    return sites
            
            # Fallback a OpenAI Vision
            if self.openai_api_key:
                sites = await self._call_openai_vision(prompt, screenshot_base64)
                if sites:
                    return sites
            
            logger.warning("⚠️ Nessuna AI Vision disponibile")
            return []
            
        except Exception as e:
            logger.error(f"❌ Errore AI Vision: {e}")
            return []
    
    async def _call_gemini_vision(self, prompt: str, image_base64: str) -> List[str]:
        """Chiama Gemini Vision API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_base64
                            }
                        }
                    ]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"🤖 Gemini Vision raw response: {text_response}")
                
                # Estrai lista JSON dalla risposta (con parsing robusto)
                try:
                    # Cerca JSON array nella risposta
                    import re
                    json_match = re.search(r'\[.*?\]', text_response, re.DOTALL)
                    if json_match:
                        sites = json.loads(json_match.group())
                        logger.info(f"✅ Gemini Vision ha trovato: {sites}")
                        return sites
                    else:
                        logger.warning("⚠️ Nessun JSON array trovato nella risposta Gemini")
                        return []
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Errore parsing JSON Gemini: {e}")
                    return []
            else:
                logger.error(f"❌ Gemini Vision error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Errore Gemini Vision: {e}")
            return []
    
    async def _call_openai_vision(self, prompt: str, image_base64: str) -> List[str]:
        """Chiama OpenAI Vision API"""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                text_response = result['choices'][0]['message']['content']
                
                # Estrai lista JSON dalla risposta
                sites = json.loads(text_response.strip())
                logger.info(f"✅ OpenAI Vision ha trovato: {sites}")
                return sites
            else:
                logger.error(f"❌ OpenAI Vision error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Errore OpenAI Vision: {e}")
            return []
    
    def _generate_product_urls(self, sites: List[str], query: str) -> List[Dict[str, str]]:
        """Genera URLs suggerite per ogni sito"""
        site_urls = []
        
        for site in sites:
            # URLs base per ricerca prodotto su ogni sito
            if 'mediaworld.it' in site:
                search_url = f"https://www.mediaworld.it/search?q={quote_plus(query)}"
            elif 'unieuro.it' in site:
                search_url = f"https://www.unieuro.it/online/search?q={quote_plus(query)}"
            elif 'amazon.it' in site:
                search_url = f"https://www.amazon.it/s?k={quote_plus(query)}"
            elif 'euronics.it' in site:
                search_url = f"https://euronics.it/search?q={quote_plus(query)}"
            else:
                # URL generico
                search_url = f"https://{site}/search?q={quote_plus(query)}"
            
            site_urls.append({
                'site': site,
                'url': search_url,
                'display_name': site.replace('www.', '').replace('.it', '').title(),
                'is_priority': any(target in site for target in self.target_sites)
            })
        
        # Ordina per priorità
        site_urls.sort(key=lambda x: (not x['is_priority'], x['site']))
        
        return site_urls

# Singleton globale
google_vision_finder = GoogleVisionFinder() 