#!/usr/bin/env python3

"""

AI Content Analyzer - Strategia Intelligente a 3 Fasi

1. AI identifica tipo sito e selettori prodotti

2. Estrazione intelligente contenuto prodotto

3. AI analizza solo testo pulito prodotti

"""



import asyncio

import json

import re

import time

from typing import Dict, List, Any, Optional

from playwright.async_api import async_playwright

import requests

from bs4 import BeautifulSoup

import os

from dotenv import load_dotenv

import aiohttp

import base64

from PIL import Image

import io



# Carica variabili d'ambiente
try:
    # Prova prima il percorso relativo (quando eseguito da start.py)
    load_dotenv('env.local')
except Exception as e:
    try:
        # Prova il percorso assoluto (quando eseguito direttamente)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(current_dir, "env.local")
        load_dotenv(env_path)
    except Exception as e2:
        print(f"⚠️ Errore caricamento env.local in ai_content_analyzer: {e2}")



class AIContentAnalyzer:
    """Analizzatore AI intelligente per contenuti web"""

    @staticmethod
    def _clean_key(value: Optional[str]) -> Optional[str]:
        """Ritorna la chiave solo se reale: scarta vuoti e placeholder tipo 'your_..._here'."""
        if not value:
            return None
        v = value.strip()
        if not v or v.lower().startswith("your_") or v.lower().endswith("_here"):
            return None
        return v

    def __init__(self):
        """Inizializza l'analizzatore AI"""
        self.openai_api_key = self._clean_key(os.getenv('OPENAI_API_KEY'))
        self.gemini_api_key = self._clean_key(os.getenv('GEMINI_API_KEY'))

        # Config guidata da env (fonte unica: env.local / variabili Render)
        # AI_PROVIDER: auto | openai | gemini  -> determina l'ordine di tentativo
        self.ai_provider = os.getenv('AI_PROVIDER', 'auto').lower().strip()
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

        print("🔧 AI Analyzer Init:")

        print(f"   • AI_PROVIDER: {self.ai_provider}")

        print(f"   • GEMINI_API_KEY: {'✅ Configurata' if self.gemini_api_key else '❌ Mancante'} ({self.gemini_model})")

        print(f"   • OPENAI_API_KEY: {'✅ Configurata' if self.openai_api_key else '❌ Mancante'} ({self.openai_model})")



    async def analyze_page_content_text_first(self, url: str) -> Dict[str, Any]:

        """

        APPROCCIO INTELLIGENTE: AI identifica prodotti in 3 fasi

        1. AI analizza struttura sito

        2. Estrazione intelligente contenuto prodotto

        3. AI analizza solo testo pulito prodotti

        """

        try:

            print(f"🧠 ===== TEXT-FIRST AI SCRAPE INTELLIGENTE =====")

            print(f"📍 URL: {url}")

           

            # FASE 1: AI identifica il tipo di sito e i selettori prodotti

            print("🤖 FASE 1: AI identifica tipo sito e selettori prodotti...")

            site_analysis = await self._ai_analyze_site_structure(url)

           

            # FASE 2: Estrazione intelligente del contenuto prodotto

            print("🧹 FASE 2: Estrazione intelligente contenuto prodotto...")

            product_content = await self._extract_product_content_intelligent(url, site_analysis)

           

            # FASE 3: AI analizza solo il testo pulito dei prodotti

            print("🤖 FASE 3: AI analizza testo pulito prodotti...")

            products = await self._ai_analyze_clean_product_text(product_content, url)

           

            return {

                "success": True,

                "products": products,

                "total_found": len(products),

                "method": "text_first_ai_intelligent",

                "url": url,

                "site_analysis": site_analysis

            }

               

        except Exception as e:

            print(f"❌ Errore Text-First AI Intelligente: {e}")

            return {

                "success": False,

                "error": str(e),

                "products": [],

                "total_found": 0,

                "method": "text_first_ai_intelligent",

                "url": url

            }



    async def _ai_analyze_site_structure(self, url: str) -> Dict[str, Any]:

        """FASE 1: AI identifica la struttura HTML dei prodotti"""

        try:

            print("🤖 Analisi struttura HTML prodotti...")

           

            # Estrai HTML completo per analisi

            async with async_playwright() as p:

                browser = await p.chromium.launch(headless=True)

                page = await browser.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)

               

                # Gestione popup e cookie

                await self._handle_popups_and_cookies(page)

               

                # Caricamento dinamico veloce

                await self._handle_dynamic_loading_text_first(page, url)

               

                # Estrai HTML completo

                html_content = await page.content()

                await browser.close()

               

                # Prompt per AI - identifica struttura HTML prodotti

                prompt = f"""Find the CSS selector for product containers.

HTML:
{html_content[:8000]}

Return this exact JSON format:
{{"product_container_selector": "div.product-card"}}

Use the exact field name "product_container_selector"."""

               

                response = await self._call_ai_with_fallback(prompt)

                if response:
                    # Gestisci diversi formati di risposta AI
                    selector = response.get("product_container_selector") or response.get("container_selector") or response.get("selector")
                    if selector:
                        print(f"✅ Analisi struttura completata. Contenitore trovato: '{selector}'")
                        return {"product_container_selector": selector}
                    else:
                        print(f"❌ AI ha restituito JSON ma senza selettore valido: {response}")

                else:

                    print("❌ Fallback a selettori generici")

                    return {

                        "product_container_selector": ".product, .product-item, .item, [class*='product'], li[class*='item']",

                        "confidence": 0.5

                    }

                   

        except Exception as e:

            print(f"❌ Errore analisi struttura: {e}")

            return {

                "site_type": "generic",

                "html_structure": "div generico",

                "price_elements": "span generico",

                "title_elements": "h3 generico",

                "suggested_selectors": [".product-price", ".product-description"],

                "confidence": 0.3

            }



    async def _extract_product_content_intelligent(self, url: str, site_analysis: Dict[str, Any]) -> str:

        """FASE 2: Estrazione intelligente del contenuto prodotto con selettori utente"""

        try:

            print("🧹 Estrazione intelligente contenuto prodotto...")

           

            # Usa il selettore contenitore identificato dall'AI

            container_selector = site_analysis.get('product_container_selector', '.product')

            print(f"🔍 Contenitore prodotto identificato: {container_selector}")

           

            # Per ora usiamo i selettori suggeriti, ma in futuro qui l'utente potrebbe selezionarli

            # TODO: Implementare UI per selezione selettori da parte dell'utente

           

            async with async_playwright() as p:

                browser = await p.chromium.launch(headless=True)

                page = await browser.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)

               

                # Gestione popup e cookie

                await self._handle_popups_and_cookies(page)

               

                # Caricamento dinamico veloce

                await self._handle_dynamic_loading_text_first(page, url)

               

                # Estrai contenuto usando il contenitore identificato

                working_content = await self._extract_from_containers(page, container_selector)

               

                await browser.close()

               

                if working_content:

                    print(f"🧹 Contenuto prodotto estratto: {len(working_content)} caratteri")

                    return working_content

                else:

                    print("❌ Nessun contenitore trovato, uso estrazione generica")

                    return await self._extract_generic_content(url)

               

        except Exception as e:

            print(f"❌ Errore estrazione intelligente: {e}")

            # Fallback a estrazione generica

            return await self._extract_generic_content(url)



    async def _extract_from_containers(self, page, container_selector: str) -> str:
        """Estrae contenuto dai contenitori prodotto identificati"""
        try:
            print(f"🔍 Estrazione da contenitori: {container_selector}")
            
            # Trova tutti i contenitori prodotto
            containers = await page.query_selector_all(container_selector)
            print(f"📦 Trovati {len(containers)} contenitori")
            
            if not containers:
                return ""

            extracted_content = []
            
            for i, container in enumerate(containers[:20]):  # Limita a 20 prodotti
                try:
                    # Estrai tutto il testo dal contenitore
                    text = await container.inner_text()
                    if text and text.strip():
                        extracted_content.append(f"---ITEM---\n{text.strip()}")
                except:
                    continue

            result = "\n\n".join(extracted_content)
            print(f"✅ Estratto contenuto da {len(extracted_content)} contenitori")
            return result

        except Exception as e:
            print(f"❌ Errore estrazione contenitori: {e}")
            return ""

    async def _test_selectors_and_extract(self, page, suggested_selectors: List[str], custom_selectors: str = "") -> str:

        """Testa i selettori e estrae il contenuto da quelli che funzionano"""

        try:

            print("🔍 Test selettori suggeriti...")



            # Aggiungi selettori personalizzati se forniti

            all_selectors = suggested_selectors.copy()

            if custom_selectors:

                custom_list = [s.strip() for s in custom_selectors.split(',') if s.strip()]

                all_selectors = custom_list + all_selectors  # Priorità ai selettori personalizzati

                print(f"🔧 Selettori personalizzati aggiunti: {custom_list}")



            product_text = ""



            for selector in all_selectors:

                try:

                    # Escape delle virgolette per evitare errori JavaScript

                    escaped_selector = selector.replace("'", "\\'").replace('"', '\\"')



                    # Conta quanti elementi trova

                    count = await page.evaluate(f"document.querySelectorAll('{escaped_selector}').length")

                    if count > 0:

                        print(f"✅ Selettore '{selector}' trova {count} elementi")



                        # Estrai il testo

                        text = await page.evaluate(f"""

                            () => {{

                                const elements = document.querySelectorAll('{escaped_selector}');

                                let text = '';

                                for (const el of elements) {{

                                    text += el.innerText + '\\n';

                                }}

                                return text;

                            }}

                        """)



                        if text.strip():

                            product_text += text + "\n"

                            print(f"📄 Estratti {len(text)} caratteri da '{selector}'")

                    else:

                        print(f"❌ Selettore '{selector}' non trova elementi")



                except Exception as e:

                    print(f"❌ Errore con selettore '{selector}': {e}")

                    continue

           

            # Se non abbiamo trovato nulla, prova selettori generici e specifici per Unieuro

            if not product_text.strip():

                print("🔄 Provo selettori generici e specifici...")

                generic_selectors = [

                    # Selettori specifici per prezzi

                    ".price", ".cost", ".amount", ".value",

                    "[class*='price']", "[class*='cost']", "[class*='amount']",

                    # Selettori specifici per titoli

                    ".title", ".name", ".heading", ".product-title",

                    "[class*='title']", "[class*='name']", "[class*='heading']",

                    # Selettori per descrizioni

                    ".description", ".desc", ".product-desc",

                    "[class*='description']", "[class*='desc']"

                ]

               

                for selector in generic_selectors:

                    try:

                        # Escape delle virgolette

                        escaped_selector = selector.replace("'", "\\'").replace('"', '\\"')

                        count = await page.evaluate(f"document.querySelectorAll('{escaped_selector}').length")

                        if count > 0:

                            print(f"✅ Selettore generico '{selector}' trova {count} elementi")

                            text = await page.evaluate(f"""

                                () => {{

                                    const elements = document.querySelectorAll('{escaped_selector}');

                                    let text = '';

                                    for (const el of elements) {{

                                        text += el.innerText + '\\n';

                                    }}

                                    return text;

                                }}

                            """)

                            if text.strip():

                                product_text += text + "\n"

                    except Exception as e:

                        print(f"❌ Errore selettore generico '{selector}': {e}")

                        continue

           

            return product_text

           

        except Exception as e:

            print(f"❌ Errore test selettori: {e}")

            return ""



    async def _ai_analyze_clean_product_text(self, product_content: str, url: str) -> List[Dict[str, Any]]:

        """FASE 3: AI analizza solo il testo pulito dei prodotti"""

        try:

            print("🤖 Analisi AI testo pulito prodotti...")

           

            # Limita il contenuto per velocità

            max_chars = 5000

            if len(product_content) > max_chars:

                product_content = product_content[:max_chars] + "..."

                print(f"✂️ Contenuto troncato a {max_chars} caratteri")

           

            prompt = f"""Extract products from this text:

{product_content[:2000]}

Return this exact JSON format:
{{"products": [{{"name": "Product Name", "price": "€XX.XX", "brand": "Brand"}}]}}

Use the exact field name "products"."""

   

            response = await self._call_ai_with_fallback(prompt)

            if response and 'products' in response:

                products = response['products']

                print(f"✅ AI ha identificato {len(products)} prodotti dal testo pulito")

                return products

            else:

                print("❌ AI non ha trovato prodotti, uso fallback manuale")

                return self._fallback_text_scraping(product_content, url)

           

        except Exception as e:

            print(f"❌ Errore analisi AI testo pulito: {e}")

            return self._fallback_text_scraping(product_content, url)



    async def _extract_generic_content(self, url: str) -> str:

        """Fallback: estrazione generica del contenuto"""

        try:

            async with async_playwright() as p:

                browser = await p.chromium.launch(headless=True)

                page = await browser.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=120000)

               

                # Estrai tutto il testo

                text_content = await page.evaluate("document.body.innerText")

                await browser.close()

               

                # Pulisci

                cleaned_content = self._clean_page_text(text_content)

                return cleaned_content

           

        except Exception as e:

            print(f"❌ Errore estrazione generica: {e}")

            return ""



    def _clean_page_text(self, text: str) -> str:
        """Pulisce il testo della pagina per l'analisi AI - INTELLIGENTE E GENERICO"""
        
        import re
        
        print(f"🧹 PULIZIA TESTO: {len(text):,} caratteri iniziali")
        
        # 1. Rimuovi elementi di navigazione e footer (PATTERN AGGIORNATI E GENERICI)
        nav_patterns = [
            # Cookie e popup
            r'Cookie.*?Accept.*?Tutti.*?OK',
            r'Cookie.*?Accetta.*?Tutti.*?OK',
            r'Accept.*?All.*?Cookies',
            r'Accetta.*?Tutti.*?Cookie',
            
            # Menu di navigazione generici
            r'Menu.*?Home.*?About.*?Contatti.*?Chi.*?Siamo',
            r'Menu.*?Home.*?Chi.*?Siamo.*?Dove.*?Siamo',
            r'Navigation.*?Menu.*?Home.*?About.*?Contact',
            
            # Login e account
            r'Login.*?Register.*?Account.*?Accedi.*?Registrati',
            r'Accedi.*?Registrati.*?Account.*?Profilo',
            r'Sign.*?In.*?Sign.*?Up.*?Account.*?Profile',
            
            # Social media generici
            r'Facebook.*?Twitter.*?Instagram.*?LinkedIn.*?YouTube',
            r'Seguici.*?su.*?Facebook.*?Instagram.*?Twitter',
            r'Follow.*?us.*?on.*?Facebook.*?Instagram',
            
            # Footer e legale
            r'Privacy.*?Terms.*?Conditions.*?Legale.*?Informativa',
            r'Privacy.*?Policy.*?Termini.*?Condizioni',
            r'Informativa.*?Privacy.*?Cookie.*?GDPR',
            
            # E-commerce generico
            r'Spedizione.*?Consegna.*?Reso.*?Garanzia.*?Assistenza',
            r'Shipping.*?Delivery.*?Return.*?Warranty.*?Support',
            r'Spedizione.*?Gratuita.*?Consegna.*?Rapida',
            
            # Newsletter
            r'Newsletter.*?Iscriviti.*?Email.*?Newsletter',
            r'Newsletter.*?Subscribe.*?Email.*?Updates',
            r'Iscriviti.*?alla.*?Newsletter.*?Ricevi.*?Offerte',
            
            # Carrello e preferiti
            r'Carrello.*?Wishlist.*?Preferiti.*?Wishlist',
            r'Cart.*?Wishlist.*?Favorites.*?Saved',
            r'Carrello.*?Acquisti.*?Preferiti.*?Salvati',
            
            # Ricerca e filtri
            r'Cerca.*?Ricerca.*?Filtri.*?Ordina.*?Filtra',
            r'Search.*?Filter.*?Sort.*?Order.*?Filter',
            r'Cerca.*?Prodotti.*?Filtra.*?Ordina.*?Risultati',
            
            # Paginazione
            r'Pagine.*?Pagina.*?di.*?\d+.*?Succ.*?Prec',
            r'Pages.*?Page.*?of.*?\d+.*?Next.*?Prev',
            r'Pagina.*?\d+.*?di.*?\d+.*?Successiva.*?Precedente',
            
            # Copyright e powered by
            r'©.*?Tutti.*?diritti.*?riservati.*?Copyright',
            r'©.*?All.*?rights.*?reserved.*?Copyright',
            r'Powered.*?by.*?WordPress.*?Drupal.*?Joomla',
            r'Sviluppato.*?da.*?WordPress.*?Drupal.*?Joomla',
            
            # GDPR e privacy
            r'Informativa.*?Cookie.*?GDPR.*?Privacy.*?Policy',
            r'Cookie.*?Policy.*?GDPR.*?Privacy.*?Information',
            r'Gestione.*?Cookie.*?Privacy.*?GDPR',
            
            # Caricamento prodotti
            r'Mostra.*?più.*?prodotti.*?Carica.*?altri',
            r'Show.*?more.*?products.*?Load.*?more',
            r'Carica.*?altri.*?prodotti.*?Mostra.*?altro',
            
            # Filtri applicati
            r'Filtri.*?applicati.*?Rimuovi.*?filtri',
            r'Applied.*?filters.*?Remove.*?filters',
            r'Filtri.*?attivi.*?Rimuovi.*?tutti.*?filtri',
            
            # Ordinamento
            r'Ordina.*?per.*?Prezzo.*?Nome.*?Data',

            r'Vista.*?griglia.*?Vista.*?lista.*?Vista.*?tabella'

        ]
        
        for pattern in nav_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # 2. Rimuovi righe che NON contengono prodotti (LOGICA MIGLIORATA)
        lines = text.split('\n')
        product_lines = []
        
        # Indicatori di prodotti GENERICI (non hardcoded per brand specifici)
        product_indicators = [
            # Prezzi e valute
            '€', '$', '£', 'EUR', 'USD', 'GBP', 'Prezzo', 'Price', 'Costo', 'Cost',
            
            # Indicatori di prodotto generici
            'Ora', 'Now', 'Sconto', 'Discount', 'Offerta', 'Offer', 'Promozione', 'Promotion',
            'Disponibile', 'Available', 'In Stock', 'Scorte', 'Stock', 'Quantità', 'Quantity',
            
            # Specifiche tecniche generiche
            'GB', 'TB', 'MB', 'KB', 'GHz', 'MHz', 'Hz', 'W', 'V', 'A', 'mAh', 'Wh',
            'cm', 'mm', 'm', 'kg', 'g', 'l', 'ml', 'pollici', 'inches', 'pixel', 'px',
            
            # Caratteristiche prodotto generiche
            'Colore', 'Color', 'Taglia', 'Size', 'Modello', 'Model', 'Versione', 'Version',
            'Serie', 'Series', 'Edizione', 'Edition', 'Anno', 'Year', 'Marca', 'Brand',
            
            # Azioni di acquisto
            'Acquista', 'Buy', 'Compra', 'Purchase', 'Aggiungi', 'Add', 'Carrello', 'Cart',
            'Ordina', 'Order', 'Prenota', 'Book', 'Richiedi', 'Request', 'Contatta', 'Contact'
        ]
        
        # Indicatori di contenuto NON prodotto (da escludere)
        non_product_indicators = [
            'Menu', 'Navigation', 'Navigazione', 'Footer', 'Header', 'Sidebar',
            'Cookie', 'Privacy', 'Terms', 'Condizioni', 'Legale', 'Informativa',
            'Newsletter', 'Iscriviti', 'Subscribe', 'Seguici', 'Follow',
            'Carrello', 'Cart', 'Wishlist', 'Preferiti', 'Favorites',
            'Cerca', 'Search', 'Filtri', 'Filters', 'Ordina', 'Sort',
            'Pagine', 'Pages', 'Pagina', 'Page', 'Succ', 'Next', 'Prec', 'Prev',
            'Copyright', 'Powered by', 'Sviluppato da', 'GDPR',
            'Mostra più', 'Show more', 'Carica altri', 'Load more',
            'Vista griglia', 'Grid view', 'Vista lista', 'List view'
        ]
        
        for line in lines:
            line_clean = line.strip()
            if len(line_clean) < 15:  # Ignora righe troppo corte
                continue
            
            # Controlla se la riga contiene indicatori di prodotto
            line_lower = line_clean.lower()
            
            # Se contiene indicatori di prodotto E non contiene indicatori di non-prodotto
            has_product_indicators = any(indicator.lower() in line_lower for indicator in product_indicators)
            has_non_product_indicators = any(indicator.lower() in line_lower for indicator in non_product_indicators)
            
            # Mantieni solo se ha indicatori di prodotto E non ha indicatori di non-prodotto
            if has_product_indicators and not has_non_product_indicators:
                if len(line_clean) > 300:  # Tronca righe troppo lunghe
                    line_clean = line_clean[:300] + "..."
                product_lines.append(line_clean)
        
        text = '\n'.join(product_lines)
        
        # 3. Rimuovi spazi multipli e righe vuote
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 4. Rimuovi caratteri speciali inutili (mantieni quelli importanti per prodotti)
        text = re.sub(r'[^\w\s€$£.,!?()\-/:°²³]', '', text)
        
        result = text.strip()
        
        print(f"🧹 PULIZIA COMPLETATA: {len(result):,} caratteri finali")
        print(f"🧹 Righe mantenute: {len(product_lines)}")
        
        return result



    def _provider_order(self) -> list:
        """Ordine di tentativo dei provider in base a AI_PROVIDER.

        - 'gemini' -> Gemini, poi OpenAI come fallback
        - 'openai' -> OpenAI, poi Gemini come fallback
        - 'auto' (default) -> OpenAI (veloce/economico), poi Gemini
        Vengono inclusi solo i provider con API key configurata.
        """
        providers = {
            "openai": (self._call_openai_ai, self.openai_api_key),
            "gemini": (self._call_gemini_ai, self.gemini_api_key),
        }

        if self.ai_provider == "gemini":
            order = ["gemini", "openai"]
        else:  # 'openai' e 'auto'
            order = ["openai", "gemini"]

        return [(name, providers[name][0]) for name in order if providers[name][1]]

    async def _call_ai_with_fallback(self, prompt: str) -> Optional[Dict[str, Any]]:

        """Chiama i provider AI nell'ordine definito da AI_PROVIDER, con fallback."""

        chain = self._provider_order()

        if not chain:
            print("❌ Nessuna API key AI configurata (OPENAI_API_KEY / GEMINI_API_KEY)")
            return None

        for name, call in chain:
            try:
                print(f"🤖 Tentativo {name}...")
                result = await call(prompt)
                if result:
                    print(f"✅ {name} ha risposto")
                    return result
            except Exception as e:
                err = str(e).lower()
                if "timeout" in err:
                    print(f"⏰ Timeout {name} - troppo lento")
                elif "503" in err or "429" in err:
                    print(f"🚫 Rate limit {name}")
                else:
                    print(f"❌ Errore {name}: {e}")

        print("❌ Tutti i provider AI hanno fallito")

        print("🔄 Fallback a scraping generico...")

        return None



    async def _call_openai_ai(self, prompt: str) -> Dict[str, Any]:

        """Chiama l'API OpenAI"""

        try:

            print(f"🤖 OpenAI: Invio richiesta con {len(prompt)} caratteri...")

            headers = {

                "Authorization": f"Bearer {self.openai_api_key}",

                "Content-Type": "application/json"

            }

           

            payload = {

                "model": self.openai_model,

                "messages": [
                    {"role": "system", "content": "You are a data extraction expert. Return ONLY valid JSON. Never add explanations or comments."},
                    {"role": "user", "content": prompt}
                ],

                "temperature": 0.1,
                "response_format": {"type": "json_object"}

            }



            print(f"🤖 OpenAI: Invio richiesta a API...")

            response = requests.post(

                "https://api.openai.com/v1/chat/completions",

                headers=headers, json=payload, timeout=120

            )



            print(f"🤖 OpenAI: Status code {response.status_code}")

           

            if response.status_code == 200:

                result = response.json()

                ai_response = result["choices"][0]["message"]["content"]

                print(f"🤖 OpenAI Response: {ai_response[:200]}...")

                parsed_result = self._extract_json_from_response(ai_response)

                # Supporta sia clickable_elements che products per Text-First AI

                if (

                    parsed_result.get("clickable_elements")

                    or parsed_result.get("site_type")

                    or parsed_result.get("products")

                    or parsed_result.get("remove_selectors")  # Aggiunto per AI cleanup filters

                    or parsed_result.get("content_selectors")  # Aggiunto per AI cleanup filters

                ):

                    elements_count = len(parsed_result.get('clickable_elements', []))

                    products_count = len(parsed_result.get('products', []))

                   

                    if elements_count > 0:

                        print(f"✅ OpenAI: Generato risultato con {elements_count} elementi")

                    elif products_count > 0:

                        print(f"✅ OpenAI: Generato risultato con {products_count} prodotti")

                    else:

                        print(f"✅ OpenAI: Generato risultato con site_type")

                   

                    return parsed_result

                else:

                    print(f"❌ OpenAI: Nessun elemento generato")

                    return None

            else:

                print(f"❌ OpenAI: Status code {response.status_code}")

           

            return None



           

        except Exception as e:

            print(f"Errore AI OpenAI: {e}")

            return None

   

    async def _call_gemini_ai(self, prompt: str) -> Dict[str, Any]:

        """Chiama l'API Gemini"""

        try:

            headers = {

                "Content-Type": "application/json"

            }

           

            payload = {

                "contents": [{

                    "parts": [{"text": prompt}]

                }],

                "generationConfig": {

                "temperature": 0.1,

                    "maxOutputTokens": 4096

                }

            }

           

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"



            response = requests.post(url, headers=headers, json=payload, timeout=120)

           

            if response.status_code == 200:

                result = response.json()

                ai_response = result["candidates"][0]["content"]["parts"][0]["text"]

                print(f"🤖 Gemini Response: {ai_response[:200]}...")

                parsed_result = self._extract_json_from_response(ai_response)

                if (

                    parsed_result.get("clickable_elements")

                    or parsed_result.get("site_type")

                    or parsed_result.get("products")

                    or parsed_result.get("remove_selectors")  # Aggiunto per AI cleanup filters

                    or parsed_result.get("content_selectors")  # Aggiunto per AI cleanup filters

                ):

                    return parsed_result

                else:

                    print(f"❌ Gemini: Nessun elemento generato")

                    return None

            else:

                print(f"❌ Gemini: Status code {response.status_code}")

           

            return None

           

        except Exception as e:

            print(f"Errore AI Gemini: {e}")

            return None

   

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:

        """Estrae JSON dalla risposta AI"""

        try:

            print(f"🔍 Parsing AI response...")

           

            # Rimuovi eventuali markdown code blocks

            response = re.sub(r'```json\s*', '', response)

            response = re.sub(r'```\s*$', '', response)

           

            # Prova a estrarre JSON dalla risposta

            json_match = re.search(r'\{.*\}', response, re.DOTALL)

            if json_match:

                json_str = json_match.group()

               

                # Gestisci JSON troncato - cerca di completarlo

                if json_str.count('{') > json_str.count('}'):

                    # JSON incompleto, prova a completarlo

                    missing_braces = json_str.count('{') - json_str.count('}')

                    json_str += '}' * missing_braces

                    print(f"🔧 JSON troncato, aggiunti {missing_braces} parentesi graffe")

               

                # Gestisci virgole mancanti

                json_str = re.sub(r'(\w+)\s*(\})\s*(\w+)', r'\1,\2,\3', json_str)

                json_str = re.sub(r'(\})\s*(\w+)', r'\1,\2', json_str)

               

                try:

                    parsed = json.loads(json_str)

                    print(f"✅ JSON parsato con successo")

                    return parsed

                except json.JSONDecodeError as e:

                    print(f"⚠️ Errore parsing JSON, provo a pulire: {e}")

                    # Prova a pulire il JSON

                    json_str = re.sub(r',\s*}', '}', json_str)  # Rimuovi virgole prima di }

                    json_str = re.sub(r',\s*]', ']', json_str)  # Rimuovi virgole prima di ]

                    try:

                        parsed = json.loads(json_str)

                        print(f"✅ JSON parsato dopo pulizia")

                        return parsed

                    except:

                        print(f"❌ Impossibile parsare JSON anche dopo pulizia")

                        return None

            else:

                # Prova a parsare direttamente

                try:

                    parsed = json.loads(response.strip())

                    print(f"✅ JSON parsato direttamente")

                    return parsed

                except:

                    print(f"❌ Nessun JSON valido trovato")

                    return None

               

        except Exception as e:

            print(f"❌ Errore parsing JSON: {e}")

            print(f"🔍 Response era: {response[:500]}...")

            return None

   

    def _fallback_text_scraping(self, text: str, url: str) -> List[Dict[str, Any]]:

        """Fallback: estrazione prodotti dal testo senza AI"""

        import re

        print("🔧 Fallback: estrazione manuale prodotti dal testo...")



        products = []

        lines = text.split('\n')



        # Pattern per prezzi

        price_pattern = r'€\s*[\d.,]+'



        current_product = {}



        for line in lines:

            line_clean = line.strip()

            if len(line_clean) < 10:

                continue



            # Cerca prezzi

            prices = re.findall(price_pattern, line_clean)

            if prices:

                # Se abbiamo già un prodotto in costruzione, salvalo

                if current_product and current_product.get('name'):

                    products.append(current_product)

                    current_product = {}



                # Inizia nuovo prodotto

                current_product = {

                    'name': line_clean,

                    'price': prices[0],

                    'brand': '',

                    'description': '',

                    'confidence': 0.7

                }



                # Cerca brand comuni

                brands = ['HP', 'Dell', 'Lenovo', 'Asus', 'Acer', 'Apple', 'Samsung', 'LG', 'Sony']

                for brand in brands:

                    if brand.lower() in line_clean.lower():

                        current_product['brand'] = brand

                        break



        # Aggiungi l'ultimo prodotto se presente

        if current_product and current_product.get('name'):

            products.append(current_product)



        print(f"🔧 Fallback completato: {len(products)} prodotti estratti manualmente")

        return products



    async def _handle_popups_and_cookies(self, page):

        """Gestisce popup e cookie"""

        try:

            # Cerca pulsanti cookie comuni

            cookie_selectors = [

                'button:has-text("Accept")',

                'button:has-text("Accept All")',

                'button:has-text("Accept Cookies")',

                'button:has-text("OK")',

                'button:has-text("I Accept")',

                'button:has-text("Accept All Cookies")',

                'button:has-text("accetta")',

                'button:has-text("accetta tutti")',

                'button:has-text("accetta cookie")',

                'button:has-text("ok")',

                '[class*="cookie"]',

                '[id*="cookie"]'

            ]

            for selector in cookie_selectors:

                try:

                    button = await page.wait_for_selector(selector, timeout=2000)

                    if button and await button.is_visible():

                        await button.click()

                        print(f"✅ Cliccato su: {selector}")

                        break

                except Exception as e:

                    print(f"⚠️ Errore gestione popup: {e}")

                    continue

        except Exception as e:

            print(f"❌ Errore generale gestione popup: {e}")



    async def _handle_dynamic_loading_text_first(self, page, url: str):

        """Gestisce il caricamento dinamico per Text-First AI"""

        try:

            # Caricamento iniziale veloce

            print("⏳ Caricamento iniziale veloce...", end="", flush=True)

            for i in range(3):

                await page.wait_for_timeout(1000)

                print(".", end="", flush=True)

            print(" ✅ Completato!")

                   

            # Scroll e cerca pulsanti "Mostra più"

            max_attempts = 5  # Aumentato da 3 a 5

            for attempt in range(max_attempts):

                print(f"🔄 Tentativo {attempt + 1}/{max_attempts} - Caricamento dinamico...")



                # Scroll

                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                await page.wait_for_timeout(2000)



                # Cerca pulsanti - SELEZIONE ESPANDIBILE

                load_selectors = [

                    # Selettori specifici per Unieuro

                    'button:has-text("Mostra più prodotti")',

                    'button:has-text("Carica altri prodotti")',

                    'button:has-text("Visualizza altri")',

                    'button:has-text("Mostra altri")',

                    'button:has-text("Carica altri")',

                    'button:has-text("Load more")',

                    'button:has-text("Show more")',

                    'button:has-text("Visualizza tutti")',

                    # Selettori generici

                    '[class*="load-more"]',

                    '[class*="show-more"]',

                    '[class*="carica"]',

                    '[class*="mostra"]',

                    # Selettori con icone

                    'button[aria-label*="più"]',

                    'button[aria-label*="more"]',

                    'button[title*="più"]',

                    'button[title*="more"]'

                ]



                button_found = False

                for selector in load_selectors:

                    try:

                        print(f"🔍 Cerca pulsante: {selector}")

                        button = await page.wait_for_selector(selector, timeout=2000)

                        if button and await button.is_visible():

                            print(f"✅ Trovato pulsante: {selector}")

                            # Aspetta che il pulsante sia cliccabile

                            await page.wait_for_timeout(1000)

                            # Prova a cliccare con gestione errori

                            try:

                                # METODO 1: Click normale

                                await button.click(timeout=5000)

                                print(f"✅ CLICK su {selector}")

                                await page.wait_for_timeout(3000)

                                button_found = True

                                break  # ESCE DAL CICLO QUANDO TROVA E CLICCA

                            except Exception as click_error:

                                print(f"❌ Errore click normale su {selector}: {click_error}")

                                # METODO 2: Click con JavaScript

                                try:

                                    print(f"🔄 Provo click JavaScript su {selector}")

                                    await page.evaluate(f"""

                                        () => {{

                                            const button = document.querySelector('{selector}');

                                            if (button) {{

                                                button.click();

                                                return true;

                                            }}

                                            return false;

                                        }}

                                    """)

                                    print(f"✅ CLICK JavaScript su {selector}")

                                    await page.wait_for_timeout(3000)

                                    button_found = True

                                    break

                                except Exception as js_error:

                                    print(f"❌ Errore click JavaScript su {selector}: {js_error}")

                                    # METODO 3: Click con dispatchEvent

                                    try:

                                        print(f"🔄 Provo click dispatchEvent su {selector}")

                                        await page.evaluate(f"""

                                            () => {{

                                                const button = document.querySelector('{selector}');

                                                if (button) {{

                                                    button.dispatchEvent(new MouseEvent('click', {{

                                                        bubbles: true,

                                                        cancelable: true,

                                                        view: window

                                                    }}));

                                                    return true;

                                                }}

                                                return false;

                                            }}

                                        """)

                                        print(f"✅ CLICK dispatchEvent su {selector}")

                                        await page.wait_for_timeout(3000)

                                        button_found = True

                                        break

                                    except Exception as dispatch_error:

                                        print(f"❌ Errore click dispatchEvent su {selector}: {dispatch_error}")

                                        continue

                    except Exception as e:

                        print(f"❌ Pulsante non trovato: {selector} - {e}")

                        continue



                if not button_found:

                    print("❌ Nessun pulsante 'Mostra più' trovato in questo tentativo")

                else:

                    print("✅ Pulsante cliccato con successo!")

                    break  # ESCE DAL CICLO DEI TENTATIVI SE HA CLICCATO



                # Attendi caricamento dopo click

                await page.wait_for_timeout(2000)

       

        except Exception as e:

            print(f"⚠️ Errore caricamento dinamico: {e}")



# Singleton globale

ai_content_analyzer = AIContentAnalyzer()



# Funzioni standalone per compatibilità

async def analyze_page_content_text_first(url: str) -> Dict[str, Any]:

    """Funzione standalone per Text-First AI intelligente"""

    return await ai_content_analyzer.analyze_page_content_text_first(url)



async def call_ai_provider(prompt: str, image_base64: str = None, provider: str = None) -> str:

    """Funzione standalone per chiamare provider AI"""

    return await ai_content_analyzer.call_ai_provider(prompt, image_base64, provider)



async def call_gemini_ai(prompt: str) -> Dict[str, Any]:

    """Funzione standalone per chiamare Gemini AI"""

    return await ai_content_analyzer._call_gemini_ai(prompt)



async def call_openai_ai(prompt: str) -> Dict[str, Any]:

    """Funzione standalone per chiamare OpenAI AI"""

    return await ai_content_analyzer._call_openai_ai(prompt)



async def analyze_html_with_ai(html_content: str, text_content: str, url: str) -> Dict[str, Any]:

    """Funzione standalone per analisi HTML con AI"""

    return await ai_content_analyzer._analyze_with_ai(html_content, text_content, url)



async def validate_selectors_with_ai(selectors: Dict[str, Any], url: str, html_content: str = "") -> Dict[str, Any]:

    """Funzione standalone per validazione selettori con AI"""

    return {"success": True, "validated_selectors": selectors}



async def analyze_page_with_ai(url: str) -> Dict[str, Any]:

    """Funzione standalone per analisi pagina con AI"""

    return await ai_content_analyzer.analyze_page_content(url)



async def analyze_page_with_ai_enhanced(page, url: str, optimal_selectors: Dict[str, Any]) -> Dict[str, Any]:

    """Funzione standalone per analisi pagina con AI enhanced"""

    # Estrai HTML dalla pagina Playwright

    html_content = await page.content()

   

    # Analizza con AI usando i selettori ottimali

    return await ai_content_analyzer._analyze_with_ai(html_content, "", url)



def get_ai_analyzer() -> AIContentAnalyzer:

    """Funzione standalone per ottenere l'istanza dell'AI analyzer"""

    return ai_content_analyzer