"""Mixin AI (suggerimento selettori), proxy e creazione browser per FastAIExtractor."""

import os
import json
import aiohttp
from typing import Dict, List, Any, Optional
from playwright.async_api import Browser
from fast_ai_extractor_config import (
    BROWSER_ARGS_BASE,
    BROWSER_ARGS_STEALTH,
    BROWSER_ARGS_VISIBLE,
)


class _AiSelectorMixin:
    """Auto-apprendimento/suggerimento selettori via AI, gestione proxy e browser."""

    async def _extract_via_crawl4ai(self, url: str, stop_flag: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Fetcher PRIMARIO via Crawl4AI (AsyncWebCrawler + stealth integrato).

        Rende la pagina con browser + playwright-stealth (passa Cloudflare/anti-bot
        senza la logica captcha custom), restituisce markdown pulito che passiamo
        all'AI parser cloud esistente (_ai_parse_products / Gemini). Riusa il
        chromium gia' installato da playwright: nessun setup aggiuntivo nel deploy.
        Ritorna None se non trova prodotti, cosi' si puo' fare fallback.
        """
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
            from crawl4ai.content_filter_strategy import PruningContentFilter
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        except Exception as e:
            print(f"⚠️ Crawl4AI non disponibile: {e}")
            return None

        try:
            print(f"🕷️ Crawl4AI fetch: {url}")
            # Content filter: rimuove nav/footer/boilerplate -> fit_markdown piu'
            # corto (meno chunk, AI parsing piu' veloce), mantenendo i prodotti.
            md_gen = DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.48))
            cfg = CrawlerRunConfig(markdown_generator=md_gen)
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url, config=cfg)

            if not result or not getattr(result, "success", False):
                print("❌ Crawl4AI: fetch non riuscito")
                return None

            # Usa il markdown pulito (fit_markdown); fallback al raw se troppo corto
            md_obj = result.markdown
            raw_md = str(getattr(md_obj, "raw_markdown", md_obj) or "")
            fit_md = str(getattr(md_obj, "fit_markdown", "") or "")
            markdown = fit_md if len(fit_md.strip()) >= 300 else raw_md
            if len(markdown.strip()) < 100:
                print("❌ Crawl4AI: contenuto troppo corto")
                return None

            print(f"📄 Crawl4AI: {len(markdown)} caratteri (fit={len(fit_md)}, raw={len(raw_md)})")
            products = await self._ai_parse_products(markdown, url, stop_flag)
            if not products:
                print("❌ Crawl4AI: AI non ha trovato prodotti")
                return None

            print(f"✅ Crawl4AI: {len(products)} prodotti estratti")
            return {
                "success": True,
                "products": products,
                "error": None,
                "total_found": len(products),
                "containers_found": 0,
                "container_selector": None,
                "url": url,
                "extraction_method": "crawl4ai",
            }
        except Exception as e:
            print(f"❌ Errore Crawl4AI: {e}")
            return None

    async def _extract_via_jina_reader(self, url: str, stop_flag: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Fallback estrazione via Jina Reader (r.jina.ai).

        Servizio cloud che fetcha e renderizza la pagina lato server e restituisce
        markdown pulito pronto per LLM: bypassa rendering JS e spesso l'anti-bot,
        senza browser locale ne' Ollama. Il markdown viene passato all'AI parser
        cloud esistente (_ai_parse_products). Ritorna None se non trova prodotti,
        cosi' il chiamante puo' fare fallback al risultato del browser.
        """
        try:
            print(f"🪄 Fallback Jina Reader per {url}")
            headers = {
                "X-Return-Format": "markdown",
                "User-Agent": "Mozilla/5.0",
            }
            # API key opzionale: alza i rate limit (keyless funziona comunque)
            jina_key = os.getenv("JINA_API_KEY")
            if jina_key:
                headers["Authorization"] = f"Bearer {jina_key}"

            jina_url = f"https://r.jina.ai/{url}"
            timeout = aiohttp.ClientTimeout(total=90)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(jina_url, headers=headers) as resp:
                    if resp.status != 200:
                        print(f"❌ Jina Reader: HTTP {resp.status}")
                        return None
                    markdown = await resp.text()

            if not markdown or len(markdown.strip()) < 100:
                print("❌ Jina Reader: contenuto troppo corto")
                return None

            print(f"📄 Jina Reader: {len(markdown)} caratteri di markdown")
            products = await self._ai_parse_products(markdown, url, stop_flag)
            if not products:
                print("❌ Jina Reader: AI non ha trovato prodotti")
                return None

            print(f"✅ Jina Reader: {len(products)} prodotti estratti")
            return {
                "success": True,
                "products": products,
                "error": None,
                "total_found": len(products),
                "containers_found": 0,
                "container_selector": None,
                "url": url,
                "extraction_method": "jina_reader",
            }
        except Exception as e:
            print(f"❌ Errore Jina Reader: {e}")
            return None

    async def _extract_via_duckduckgo(self, url: str) -> Dict[str, Any]:
        """Estrae dati via DuckDuckGo per bypassare blocchi"""
        try:
            from google_search_integration import GoogleSearchIntegration
            
            search_integration = GoogleSearchIntegration()
            
            if 'immobiliare.it' in url:
                if 'casalecchio-di-reno' in url:
                    zona = "Casalecchio di Reno"
                elif 'zola-predosa' in url:
                    zona = "Zola Predosa"
                else:
                    zona = "Bologna"
                
                product_data = {
                    'name': f"Case in vendita {zona}",
                    'brand': 'immobiliare.it',
                    'price': '0',
                    'url': url,
                    'category': 'immobili'
                }
            else:
                product_data = {
                    'name': 'immobili in vendita',
                    'brand': 'immobiliare',
                    'price': '0',
                    'url': url,
                    'category': 'immobili'
                }
            
            results = await search_integration.search_alternative_vendors(product_data)
            
            if results and results.get('alternative_vendors'):
                products = []
                for i, vendor in enumerate(results['alternative_vendors']):
                    if vendor.get('title'):
                        product = {
                            'name': vendor['title'],
                            'price': vendor.get('price', 'Prezzo non disponibile'),
                            'url': vendor.get('url', ''),
                            'source': 'DuckDuckGo Search',
                            'description': vendor.get('description', '')
                        }
                        products.append(product)
                
                if products:
                    return {
                        'success': True,
                        'products': products,
                        'source': 'DuckDuckGo Search',
                        'total_found': len(products)
                    }
                else:
                    return {"success": False, "error": "Nessun prodotto valido trovato"}
            else:
                return {"success": False, "error": "Nessun risultato DuckDuckGo"}
            
        except Exception as e:
            return {"success": False, "error": f"Errore DuckDuckGo: {e}"}

    async def _ai_learn_selectors(self, page, page_content: str, url: str) -> List[Dict[str, Any]]:
        """Sistema di auto-apprendimento generico - AI impara selettori dai risultati"""
        try:
            domain = self._extract_domain(url)
            print(f"🧠 SISTEMA AUTO-APPRENDIMENTO: Analizzo {domain}...")
            
            # Genera selettori candidati generici
            candidate_selectors = [
                # Selettori per prodotti/articoli
                "[class*='product']", "[class*='item']", "[class*='card']", 
                "[class*='listing']", "[class*='result']", "[class*='entry']",
                "[data-testid*='product']", "[data-testid*='item']", "[data-testid*='card']",
                "article", "li", ".product", ".item", ".card", ".listing",
                
                # Selettori per contenitori
                "[class*='container']", "[class*='content']", "[class*='main']",
                "[class*='wrapper']", "[class*='box']", "[class*='tile']",
                
                # Selettori per immobili
                "[class*='property']", "[class*='house']", "[class*='apartment']",
                "[class*='real-estate']", "[class*='listing']",
                
                # Selettori generici
                "div[class]", "section[class]", "article[class]", "li[class]"
            ]
            
            learned_selectors = []
            
            # Testa ogni selettore candidato
            for selector in candidate_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    
                    # Filtra per numero ragionevole di elementi
                    if not elements or len(elements) < 3 or len(elements) > 100:
                        continue
                    
                    # Testa i primi 3 elementi per qualità del contenuto
                    valid_elements = 0
                    total_text_length = 0
                    
                    for element in elements[:5]:  # Testa solo i primi 5
                        try:
                            text = await element.inner_text()
                            if text and len(text.strip()) > 20:
                                # Controlla se il contenuto sembra un prodotto
                                if self._looks_like_product_content(text, url):
                                    valid_elements += 1
                                    total_text_length += len(text)
                        except:
                            continue
                    
                    # Criteri di validazione standard per tutti i siti
                    min_valid_elements = 2
                    min_ratio = 0.6
                    
                    if valid_elements >= min_valid_elements and valid_elements >= len(elements[:5]) * min_ratio:
                        avg_text_length = total_text_length / valid_elements if valid_elements > 0 else 0
                        quality_score = min(1000, (valid_elements * 100) + (avg_text_length / 10))
                        
                        selector_data = {
                            'selectors': {
                                'product_container': selector,
                                'title': selector,  # Per ora usa lo stesso
                                'price': selector   # Per ora usa lo stesso
                            },
                            'products_found': len(elements),
                            'valid_elements': valid_elements,
                            'quality_score': quality_score,
                            'avg_text_length': avg_text_length
                        }
                        
                        learned_selectors.append(selector_data)
                        print(f"✅ Selettore appreso: {selector} - {len(elements)} elementi, {valid_elements} validi")
                        
                except Exception as e:
                    continue
            
            # Ordina per qualità e restituisce i migliori
            learned_selectors.sort(key=lambda x: x['quality_score'], reverse=True)
            return learned_selectors[:3]  # Massimo 3 selettori migliori
            
        except Exception as e:
            print(f"❌ Errore sistema auto-apprendimento: {e}")
            return []

    async def _ai_analyze_html_for_selectors(self, html_content: str, url: str) -> dict:
        """AI analizza HTML e suggerisce selettori CSS - FALLBACK INTELLIGENTE"""
        try:
            # Prendi solo una parte dell'HTML per l'analisi (primi 8000 caratteri)
            html_sample = html_content[:8000]
            
            prompt = f"""Analizza questo HTML e suggerisci selettori CSS specifici per estrarre prodotti.

SITO: {url}
HTML SAMPLE: {html_sample}

Suggerisci selettori CSS che:
1. Trovino contenitori di prodotti
2. Estraggano titoli di prodotti
3. Estraggano prezzi (cerca pattern come €, euro, prezzo)
4. Estraggano descrizioni
5. Estraggano immagini

Rispondi SOLO con JSON valido:
{{
    "suggested_selectors": {{
        "product_container": "selettore_css_per_contenitori",
        "title": "selettore_css_per_titoli", 
        "price": "selettore_css_per_prezzi",
        "description": "selettore_css_per_descrizioni",
        "image": "selettore_css_per_immagini"
    }},
    "reasoning": "breve spiegazione dei selettori suggeriti"
}}

IMPORTANTE: Rispondi SOLO con JSON, niente altro testo."""

            print(f"🤖 FALLBACK INTELLIGENTE: AI analizza HTML per selettori...")
            
            # Prova OpenAI prima
            try:
                response = await self._call_openai_for_selectors(prompt)
                if response and 'suggested_selectors' in response:
                    print(f"✅ OpenAI ha suggerito selettori per fallback")
                    return response['suggested_selectors']
            except Exception as e:
                print(f"⚠️ OpenAI fallito per selettori fallback: {e}")
            
            # Fallback a Gemini
            try:
                response = await self._call_gemini_for_selectors(prompt)
                if response and 'suggested_selectors' in response:
                    print(f"✅ Gemini ha suggerito selettori per fallback")
                    return response['suggested_selectors']
            except Exception as e:
                print(f"⚠️ Gemini fallito per selettori fallback: {e}")
            
            return None
            
        except Exception as e:
            print(f"❌ Errore analisi AI HTML fallback: {e}")
            return None

    async def _call_openai_for_selectors(self, prompt: str) -> dict:
        """Chiama OpenAI per analisi selettori - FALLBACK"""
        try:
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        return json.loads(content)
                    else:
                        print(f"❌ OpenAI fallback status {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ Errore OpenAI selettori fallback: {e}")
            return None

    async def _call_gemini_for_selectors(self, prompt: str) -> dict:
        """Chiama Gemini per analisi selettori - FALLBACK"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                return None
                
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
            
            data = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 1000
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        return json.loads(content)
                    else:
                        print(f"❌ Gemini fallback status {response.status}")
                        return None
                        
        except Exception as e:
            print(f"❌ Errore Gemini selettori fallback: {e}")
            return None

    async def _test_ai_suggested_selectors(self, page, suggested_selectors: dict) -> dict:
        """Testa i selettori suggeriti dall'AI - FALLBACK"""
        working_selectors = {}
        
        print(f"🧪 FALLBACK: Test selettori AI suggeriti...")
        
        for selector_name, css_selector in suggested_selectors.items():
            try:
                if not css_selector or css_selector.strip() == "":
                    continue
                    
                elements = await page.query_selector_all(css_selector)
                if elements and len(elements) > 0:
                    print(f"✅ FALLBACK {selector_name}: {css_selector} - Trovati {len(elements)} elementi")
                    working_selectors[selector_name] = css_selector
                else:
                    print(f"❌ FALLBACK {selector_name}: {css_selector} - Nessun elemento trovato")
                    
            except Exception as e:
                print(f"⚠️ Errore test fallback {selector_name}: {e}")
        
        return working_selectors

    async def _extract_with_ai_selectors(self, page, working_selectors: dict, url: str) -> dict:
        """Estrae prodotti usando i selettori AI testati - FALLBACK"""
        try:
            print(f"🚀 FALLBACK: Estrazione con selettori AI...")
            
            # Estrai contenitori
            container_selector = working_selectors.get('product_container', 'body')
            containers = await page.query_selector_all(container_selector)
            
            if not containers:
                print(f"❌ FALLBACK: Nessun contenitore trovato con selettori AI")
                return {"error": "Nessun contenitore trovato"}
            
            print(f"📦 FALLBACK: Trovati {len(containers)} contenitori con selettori AI")
            
            products = []
            
            for i, container in enumerate(containers[:5]):  # Limita a 5 prodotti
                try:
                    product = {}
                    
                    # Estrai titolo
                    if 'title' in working_selectors:
                        title_elem = await container.query_selector(working_selectors['title'])
                        if title_elem:
                            product['name'] = await title_elem.inner_text()
                    
                    # Estrai prezzo
                    if 'price' in working_selectors:
                        price_elem = await container.query_selector(working_selectors['price'])
                        if price_elem:
                            product['price'] = await price_elem.inner_text()
                    
                    # Estrai descrizione
                    if 'description' in working_selectors:
                        desc_elem = await container.query_selector(working_selectors['description'])
                        if desc_elem:
                            product['description'] = await desc_elem.inner_text()
                    
                    # Estrai immagine
                    if 'image' in working_selectors:
                        img_elem = await container.query_selector(working_selectors['image'])
                        if img_elem:
                            product['image'] = await img_elem.get_attribute('src')
                    
                    # Aggiungi URL e source
                    product['url'] = url
                    product['source'] = self._extract_domain(url)
                    
                    if product.get('name') or product.get('price'):
                        products.append(product)
                        print(f"✅ FALLBACK: Prodotto {i+1} estratto: {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
                    
                except Exception as e:
                    print(f"⚠️ Errore estrazione fallback prodotto {i+1}: {e}")
                    continue
            
            if products:
                print(f"🎯 FALLBACK: Estrazione AI completata: {len(products)} prodotti trovati")
                return {
                    "success": True,
                    "products": products,
                    "method": "ai_selectors_fallback",
                    "selectors_used": working_selectors
                }
            else:
                print(f"❌ FALLBACK: Nessun prodotto estratto con selettori AI")
                return {"error": "Nessun prodotto estratto"}
                
        except Exception as e:
            print(f"❌ Errore estrazione fallback con selettori AI: {e}")
            return {"error": str(e)}

    async def _find_available_proxy(self) -> Optional[str]:
        """Trova un proxy disponibile dalla lista"""
        try:
            # Prova i proxy nella lista in ordine
            for i in range(len(self.proxy_list)):
                proxy = self.proxy_list[self.current_proxy_index]
                self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
                
                # Test rapido del proxy
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get('http://httpbin.org/ip', 
                                            proxy=proxy, 
                                            timeout=5) as response:
                            if response.status == 200:
                                print(f"✅ Proxy disponibile: {proxy}")
                                return proxy
                except:
                    continue
            
            print("⚠️ Nessun proxy disponibile")
            return None
            
        except Exception as e:
            print(f"⚠️ Errore ricerca proxy: {e}")
            return None

    async def _create_browser(self, needs_visible_browser: bool, proxy: str = None) -> Browser:
        """Crea un nuovo browser con le configurazioni specificate"""
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Determina modalità headless
                headless = not needs_visible_browser
                
                # Configura argomenti browser
                browser_args = BROWSER_ARGS_BASE.copy()
                
                if needs_visible_browser:
                    browser_args.extend(BROWSER_ARGS_VISIBLE)
                else:
                    browser_args.extend(BROWSER_ARGS_STEALTH)
                
                # Aggiungi proxy se specificato
                if proxy:
                    if proxy.startswith('socks5://'):
                        proxy_host = proxy.replace('socks5://', '').split(':')[0]
                        proxy_port = proxy.replace('socks5://', '').split(':')[1]
                        proxy_arg = f'--proxy-server=socks5://{proxy_host}:{proxy_port}'
                    else:
                        proxy_arg = f'--proxy-server={proxy}'
                    browser_args.append(proxy_arg)
                
                # Lancia browser
                browser = await p.chromium.launch(
                    headless=headless,
                    args=browser_args
                )
                
                return browser
                
        except Exception as e:
            print(f"❌ Errore creazione browser: {e}")
            raise e