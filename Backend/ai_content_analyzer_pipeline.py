#!/usr/bin/env python3

"""
AI Content Analyzer - Mixin pipeline di analisi pagina (fasi 1-3) ed estrazione.

Metodi spostati VERBATIM da ai_content_analyzer.py (solo raggruppamento).
Il mixin usa solo `self.` e NON importa ai_content_analyzer (evita import circolari).
"""

import re

from typing import Dict, List, Any

from playwright.async_api import async_playwright


class _PipelineMixin:
    """Pipeline text-first a 3 fasi ed estrazione/pulizia del contenuto."""

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
