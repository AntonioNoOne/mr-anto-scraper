#!/usr/bin/env python3

"""
Stagehand AI Extractor - Sistema di estrazione intelligente con AI
================================================================

Sistema per estrarre dati da siti e-commerce usando Stagehand + Playwright + AI.
Rimpiazza i selettori hardcoded con intelligenza artificiale per un'estrazione
più robusta e adattiva.

VANTAGGI:
- AI-driven: L'AI capisce automaticamente la struttura della pagina
- Meno selettori hardcoded: Non serve specificare CSS selectors precisi
- Più robusto: Si adatta ai cambiamenti del layout
- Estrazione intelligente: L'AI estrae i dati in modo più accurato
- Meno manutenzione: Meno codice da aggiornare quando i siti cambiano

DIPENDENZE:
- stagehand: Framework AI per Playwright
- playwright: Browser automation
- openai: AI per l'estrazione intelligente
- asyncio: Programmazione asincrona

USO:
- Sostituisce i selettori hardcoded in google_search_integration.py
- Migliora l'estrazione da DuckDuckGo, Bing, Amazon, etc.
- Estrazione più accurata di titoli, prezzi, URL
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

# Import Stagehand
try:
    from stagehand import Stagehand
    STAGEHAND_AVAILABLE = True
    print("✅ Stagehand 0.5.2 importato correttamente")
except ImportError:
    STAGEHAND_AVAILABLE = False
    print("⚠️ Stagehand non disponibile. Installa con: pip install stagehand")

# Import Playwright
from playwright.async_api import async_playwright

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StagehandExtractor:
    """Estrattore intelligente usando Stagehand + AI"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.stagehand_available = STAGEHAND_AVAILABLE
        
        if not self.stagehand_available:
            logger.warning("❌ Stagehand non disponibile. Usa l'estrattore tradizionale.")
            return
        
        # Inizializza Stagehand
        try:
            # Carica variabili d'ambiente
            from dotenv import load_dotenv
            load_dotenv('env.local')
            
            # Prova a inizializzare Stagehand (con o senza Browserbase)
            browserbase_key = os.getenv('BROWSERBASE_API_KEY')
            if browserbase_key and browserbase_key != 'your_browserbase_api_key_here':
                # Stagehand con Browserbase
                self.stagehand = Stagehand()
                self.stagehand_available = True
                logger.info("✅ Stagehand con Browserbase inizializzato correttamente")
            else:
                # Stagehand locale con Playwright (senza Browserbase)
                self.stagehand = Stagehand(use_browserbase=False)
                self.stagehand_available = True
                logger.info("✅ Stagehand locale con Playwright inizializzato correttamente")
        except Exception as e:
            logger.error(f"❌ Errore inizializzazione Stagehand: {e}")
            # Fallback: usa OpenAI + Playwright diretto
            logger.info("⚠️ Fallback a OpenAI + Playwright diretto")
            self.stagehand_available = True
            self.stagehand = None
    
    async def extract_products_from_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Estrae prodotti da una pagina specifica usando Stagehand + AI
        """
        if not self.stagehand_available:
            logger.warning("❌ Stagehand non disponibile")
            return []
        
        try:
            logger.info(f"🤖 Estrazione AI da pagina specifica: {url}")
            
            # Usa Stagehand per estrarre dalla pagina
            if self.stagehand:
                # Stagehand - usa il metodo corretto per 0.5.2
                try:
                    result = await self.stagehand.run(
                        f"Vai su {url} e estrai tutti i prodotti con nome, prezzo e URL",
                        model="gpt-4o-mini"
                    )
                    products = self._process_ai_results(result)
                except AttributeError:
                    # Fallback se il metodo run non esiste
                    logger.info("🔄 Usando estrazione tradizionale per Stagehand")
                    products = await self._extract_with_openai(url, "Estrai tutti i prodotti con nome, prezzo e URL")
            else:
                # Fallback: OpenAI + Playwright diretto
                products = await self._extract_with_openai(url, "Estrai tutti i prodotti con nome, prezzo e URL")
            
            logger.info(f"✅ Estrazione AI completata: {len(products)} prodotti trovati")
            return products
            
        except Exception as e:
            logger.error(f"❌ Errore estrazione AI: {e}")
            return []

    async def extract_products_from_search(self, query: str, search_engine: str = "duckduckgo") -> List[Dict[str, Any]]:
        """
        Estrae prodotti da una pagina di ricerca usando Stagehand + AI
        """
        if not self.stagehand_available:
            logger.warning("⚠️ Stagehand non disponibile, uso estrazione tradizionale")
            return await self._fallback_extraction(query, search_engine)
        
        try:
            logger.info(f"🤖 Estrazione AI con Stagehand per: {query}")
            
            # URL di ricerca
            search_url = self._get_search_url(query, search_engine)
            logger.info(f"🔍 URL ricerca: {search_url}")
            
            # Prompt per l'AI
            extraction_prompt = self._get_extraction_prompt(query)
            
            # Estrazione con Stagehand 0.5.2
            # L'API di Stagehand 0.5.2 è diversa, usiamo un approccio semplificato
            results = await self._extract_with_stagehand_v052(search_url, extraction_prompt)
            
            # Processa i risultati
            products = self._process_ai_results(results, query)
            
            logger.info(f"✅ Estrazione AI completata: {len(products)} prodotti trovati")
            return products
            
        except Exception as e:
            logger.error(f"❌ Errore estrazione AI: {e}")
            # Fallback all'estrazione tradizionale
            return await self._fallback_extraction(query, search_engine)
    
    def _get_search_url(self, query: str, search_engine: str) -> str:
        """Genera URL di ricerca per il motore specificato"""
        from urllib.parse import quote_plus
        
        if search_engine == "duckduckgo":
            return f"https://duckduckgo.com/?q={quote_plus(query)}+shopping&t=h_&iax=shopping&ia=shopping"
        elif search_engine == "bing":
            return f"https://www.bing.com/shop?q={quote_plus(query)}&setlang=it-IT"
        elif search_engine == "amazon":
            return f"https://www.amazon.it/s?k={quote_plus(query)}"
        else:
            return f"https://duckduckgo.com/?q={quote_plus(query)}+shopping"
    
    async def _extract_with_stagehand_v052(self, url: str, prompt: str) -> Any:
        """Estrazione con Stagehand 0.5.2 usando Playwright diretto"""
        try:
            logger.info(f"🤖 Estrazione Stagehand 0.5.2 per: {url}")
            
            # Per ora usiamo un approccio semplificato con Playwright diretto
            # e OpenAI per l'estrazione AI
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Vai alla pagina
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                
                # Estrai HTML
                html_content = await page.content()
                
                # Usa OpenAI per estrarre i dati
                products = await self._extract_with_openai(html_content, prompt)
                
                await browser.close()
                return products
                
        except Exception as e:
            logger.error(f"❌ Errore estrazione Stagehand 0.5.2: {e}")
            return []
    
    async def _extract_with_openai(self, html_content: str, prompt: str) -> List[Dict[str, Any]]:
        """Estrazione usando OpenAI direttamente"""
        try:
            import openai
            
            # Configura OpenAI
            client = openai.AsyncOpenAI()
            
            # Crea prompt completo
            full_prompt = f"""
            Analizza questo HTML e estrai tutti i prodotti/immobili con le seguenti informazioni:
            
            IMPORTANTE: Cerca specificamente:
            - Titoli di prodotti/immobili (h1, h2, h3, .product-title, .product-name, .property-title, .listing-title, .card-title, .announcement-title)
            - Prezzi (€, euro, .price, .cost, .property-price, .listing-price, .price-value, .amount)
            - Link di prodotti/immobili (href che contengono /product/, /notebook/, /pid, /vendita/, /affitto/, /immobile/, /annuncio/)
            
            Per Tempocasa, cerca:
            - Annunci immobiliari con titoli come "Villa", "Appartamento", "Casa", "Trilocale", "Bilocale"
            - Prezzi in formato "€ 150.000" o "150.000 €"
            - Link che contengono "/annuncio/" o "/immobile/"
            
            Per ogni prodotto/immobile trovato, estrai:
            - nome: Nome completo del prodotto/immobile (es. "Villa indipendente a Zola Predosa")
            - prezzo: Prezzo in formato numerico (es. 150000.00)
            - url: URL completo del prodotto/immobile
            - sito: Nome del sito (es. amazon, unieuro, tempocasa, etc.)
            
            Rispondi SOLO con un JSON valido in questo formato:
            {{
                "products": [
                    {{
                        "name": "Nome Prodotto/Immobile",
                        "price": 150000.00,
                        "url": "https://esempio.com/prodotto",
                        "sito": "tempocasa"
                    }}
                ]
            }}
            
            Se non trovi prodotti/immobili, rispondi con: {{"products": []}}
            
            HTML da analizzare:
            {html_content[:15000]}
            """
            
            # Chiama OpenAI
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sei un esperto di estrazione dati da pagine web. Estrai solo prodotti reali in formato JSON."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Processa la risposta
            content = response.choices[0].message.content
            logger.info(f"🔍 Risposta OpenAI (primi 500 caratteri): {content[:500]}")
            
            # Estrai JSON dalla risposta
            import json
            try:
                # Cerca JSON nella risposta
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    logger.info(f"🔍 JSON estratto: {json_str[:200]}...")
                    data = json.loads(json_str)
                    
                    if isinstance(data, dict) and "products" in data:
                        logger.info(f"✅ Trovati {len(data['products'])} prodotti nel JSON")
                        return data["products"]
                    elif isinstance(data, list):
                        logger.info(f"✅ Trovati {len(data)} prodotti nella lista")
                        return data
                
                # Se non trova JSON, prova a estrarre manualmente
                logger.info("🔄 Tentativo estrazione manuale...")
                return self._extract_products_from_text(content)
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Risposta OpenAI non è JSON valido: {e}")
                logger.info("🔄 Tentativo estrazione manuale...")
                return self._extract_products_from_text(content)
                
        except Exception as e:
            logger.error(f"❌ Errore estrazione OpenAI: {e}")
            return []
    
    def _extract_products_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Estrae prodotti da testo non-JSON"""
        products = []
        
        try:
            # Cerca pattern di prodotti nel testo
            lines = text.split('\n')
            current_product = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Cerca nome prodotto
                if any(keyword in line.lower() for keyword in ['iphone', 'samsung', 'macbook', 'ipad', 'smartphone', 'laptop']):
                    if current_product:
                        products.append(current_product)
                    current_product = {"name": line}
                
                # Cerca prezzo
                elif '€' in line and any(char.isdigit() for char in line):
                    price_match = re.search(r'€\s*(\d+[.,]\d+)', line)
                    if price_match:
                        current_product["price"] = f"€{price_match.group(1)}"
                
                # Cerca URL
                elif line.startswith('http'):
                    current_product["url"] = line
            
            # Aggiungi ultimo prodotto
            if current_product:
                products.append(current_product)
            
        except Exception as e:
            logger.error(f"❌ Errore estrazione manuale: {e}")
        
        return products

    def _get_extraction_prompt(self, query: str) -> str:
        """Genera prompt per l'estrazione AI"""
        return f"""
        Estrai tutti i prodotti di ricerca per "{query}" da questa pagina.
        
        Per ogni prodotto trovato, estrai:
        1. Nome del prodotto (titolo completo)
        2. Prezzo (se disponibile, in formato €X,XX)
        3. URL del prodotto (se disponibile)
        4. Nome del sito/venditore
        5. Descrizione breve (se disponibile)
        
        Formato di output JSON:
        {{
            "products": [
                {{
                    "name": "Nome prodotto completo",
                    "price": "€123,45",
                    "url": "https://esempio.com/prodotto",
                    "site": "NomeSito",
                    "description": "Descrizione breve"
                }}
            ]
        }}
        
        Regole:
        - Estrai SOLO prodotti reali, non filtri o categorie
        - I prezzi devono essere in formato €X,XX
        - Gli URL devono essere completi e funzionanti
        - Salta prodotti con prezzi chiaramente errati (es: €999999)
        - Massimo 20 prodotti
        - Se non trovi prodotti, restituisci array vuoto
        """
    
    def _process_ai_results(self, ai_results: Any, query: str) -> List[Dict[str, Any]]:
        """Processa i risultati dell'AI e li converte nel formato standard"""
        products = []
        
        try:
            # Stagehand restituisce i risultati in formato JSON
            if isinstance(ai_results, str):
                data = json.loads(ai_results)
            else:
                data = ai_results
            
            # Estrai prodotti dal JSON
            if isinstance(data, dict) and "products" in data:
                raw_products = data["products"]
            elif isinstance(data, list):
                raw_products = data
            else:
                logger.warning("⚠️ Formato risultati AI non riconosciuto")
                return products
            
            # Processa ogni prodotto
            for i, product in enumerate(raw_products):
                try:
                    # Valida e pulisci i dati
                    name = self._clean_text(product.get("name", ""))
                    price = self._clean_price(product.get("price", ""))
                    url = self._clean_url(product.get("url", ""))
                    site = self._clean_text(product.get("site", ""))
                    description = self._clean_text(product.get("description", ""))
                    
                    # Filtra prodotti non validi
                    if not name or len(name) < 5:
                        continue
                    
                    # Calcola score di validazione
                    validation_score = self._calculate_ai_validation_score(name, query)
                    
                    if validation_score < 0.2:
                        continue
                    
                    products.append({
                        "name": name,
                        "price": price,
                        "price_numeric": self._extract_price_numeric(price),
                        "url": url,
                        "site": site or self._extract_site_from_url(url),
                        "description": description or f"Prodotto {query}",
                        "source": f"stagehand_{search_engine}",
                        "query": query,
                        "validation_score": validation_score
                    })
                    
                    logger.info(f"🤖 Prodotto AI {i+1}: {name[:50]} - {price} - Score: {validation_score}")
                    
                except Exception as e:
                    logger.error(f"❌ Errore processamento prodotto AI {i+1}: {e}")
                    continue
            
            # Ordina per score di validazione
            products.sort(key=lambda x: x.get("validation_score", 0), reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Errore processamento risultati AI: {e}")
        
        return products
    
    def _clean_text(self, text: str) -> str:
        """Pulisce il testo estratto"""
        if not text:
            return ""
        
        # Rimuovi caratteri speciali e spazi multipli
        cleaned = re.sub(r'\s+', ' ', str(text).strip())
        cleaned = re.sub(r'[^\w\s\-.,()€$%]', '', cleaned)
        
        # Limita lunghezza
        if len(cleaned) > 100:
            cleaned = cleaned[:97] + "..."
        
        return cleaned
    
    def _clean_price(self, price: str) -> str:
        """Pulisce il prezzo estratto"""
        if not price:
            return "Prezzo non disponibile"
        
        # Cerca pattern di prezzo
        price_patterns = [
            r'€\s*(\d+[.,]\d+)',
            r'(\d+[.,]\d+)\s*€',
            r'€\s*(\d+)',
            r'(\d+)\s*€'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, str(price))
            if match:
                return f"€{match.group(1).replace(',', '.')}"
        
        return "Prezzo non disponibile"
    
    def _clean_url(self, url: str) -> str:
        """Pulisce l'URL estratto"""
        if not url:
            return ""
        
        # Rimuovi spazi e caratteri non validi
        url = str(url).strip()
        
        # Aggiungi https:// se manca
        if url and not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        return url
    
    def _extract_price_numeric(self, price_text: str) -> float:
        """Estrae prezzo numerico dal testo"""
        try:
            if not price_text or price_text == "Prezzo non disponibile":
                return 0.0
            
            # Rimuovi simboli di valuta e spazi
            price_clean = re.sub(r'[€$£\s]', '', str(price_text))
            
            # Gestisci virgole e punti decimali
            if ',' in price_clean and '.' in price_clean:
                price_clean = price_clean.replace('.', '').replace(',', '.')
            elif ',' in price_clean:
                price_clean = price_clean.replace(',', '.')
            
            # Estrai solo numeri e punto decimale
            price_match = re.search(r'[\d.]+', price_clean)
            if price_match:
                return float(price_match.group())
            
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Errore estrazione prezzo numerico: {e}")
            return 0.0
    
    def _extract_site_from_url(self, url: str) -> str:
        """Estrae nome del sito dall'URL"""
        try:
            if not url:
                return "Sconosciuto"
            
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Mappa domini comuni
            site_mapping = {
                'www.amazon.it': 'Amazon',
                'amazon.it': 'Amazon',
                'www.mediaworld.it': 'MediaWorld',
                'mediaworld.it': 'MediaWorld',
                'www.unieuro.it': 'Unieuro',
                'unieuro.it': 'Unieuro',
                'www.ebay.it': 'eBay',
                'ebay.it': 'eBay',
                'duckduckgo.com': 'DuckDuckGo',
                'bing.com': 'Bing'
            }
            
            domain_clean = domain.replace('www.', '')
            return site_mapping.get(domain_clean, domain_clean.title())
            
        except Exception as e:
            logger.error(f"❌ Errore estrazione sito: {e}")
            return "Sconosciuto"
    
    def _calculate_ai_validation_score(self, product_name: str, query: str) -> float:
        """Calcola score di validazione per prodotto AI"""
        try:
            if not product_name or not query:
                return 0.0
            
            # Converti in lowercase per confronto
            name_lower = product_name.lower()
            query_lower = query.lower()
            
            # Estrai parole chiave dalla query
            query_words = [w.strip() for w in query_lower.split() if len(w.strip()) > 2]
            
            # Conta match delle parole chiave
            matches = 0
            for word in query_words:
                if word in name_lower:
                    matches += 1
            
            # Calcola score basato su match
            if matches == 0:
                return 0.0
            elif matches == len(query_words):
                return 0.9  # Tutte le parole trovate
            else:
                return (matches / len(query_words)) * 0.7  # Parziale match
            
        except Exception as e:
            logger.error(f"❌ Errore calcolo score AI: {e}")
            return 0.0
    
    async def _fallback_extraction(self, query: str, search_engine: str) -> List[Dict[str, Any]]:
        """Fallback all'estrazione tradizionale se Stagehand non è disponibile"""
        logger.info(f"🔄 Usando estrazione tradizionale per: {query}")
        
        # Qui potresti chiamare il tuo sistema di estrazione esistente
        # Per ora restituisco una lista vuota
        return []

# Istanza globale
stagehand_extractor = StagehandExtractor()

# Funzione standalone per compatibilità
async def extract_products_with_ai(query: str, search_engine: str = "duckduckgo") -> List[Dict[str, Any]]:
    """Funzione standalone per estrazione AI"""
    return await stagehand_extractor.extract_products_from_search(query, search_engine)
