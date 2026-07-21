#!/usr/bin/env python3

"""
Google Search Integration - Parsing / estrazione mixin
======================================================

Contiene i metodi di parsing dei risultati (Google Shopping), l'estrazione
di prezzi numerici, del sito dall'URL e la pulizia dei titoli. Estratto da
google_search_integration.py per rispettare il limite di lunghezza dei file.
Nessuna modifica di logica: solo spostamento.
"""

import re
import asyncio
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

# Import per parsing HTML
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class _ParsingMixin:
    """Metodi di parsing risultati, estrazione prezzo/sito e pulizia titoli."""

    async def _enrich_prices_from_pages(self, results: List[Dict[str, Any]], max_pages: int = 6) -> List[Dict[str, Any]]:
        """Arricchisce i risultati di ricerca col prezzo REALE dalla pagina venditore.

        La ricerca (ddgs) dà URL + snippet, ma il prezzo è nella pagina: qui, per
        i primi `max_pages` risultati senza prezzo, fetchiamo la pagina con Crawl4AI
        (in parallelo) ed estraiamo il primo importo in € plausibile. Best-effort:
        se il fetch fallisce, il risultato resta senza prezzo.
        """
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
            from crawl4ai.content_filter_strategy import PruningContentFilter
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        except Exception as e:
            logger.warning(f"⚠️ Crawl4AI non disponibile per arricchimento prezzi: {e}")
            return results

        # Indici dei risultati da arricchire (senza prezzo, con URL http)
        targets = [
            i for i, r in enumerate(results[:max_pages])
            if not r.get("price") and str(r.get("url", "")).startswith("http")
        ]
        if not targets:
            return results

        md_gen = DefaultMarkdownGenerator(content_filter=PruningContentFilter(threshold=0.48))
        cfg = CrawlerRunConfig(markdown_generator=md_gen)

        try:
            from price_utils import pick_price_near_product
        except Exception:
            pick_price_near_product = None

        async def _fetch_price(idx):
            url = results[idx]["url"]
            name = results[idx].get("name", "")
            try:
                async with AsyncWebCrawler(verbose=False) as crawler:
                    res = await crawler.arun(url=url, config=cfg)
                md = res.markdown if res else None
                text = str(getattr(md, "fit_markdown", "") or getattr(md, "raw_markdown", md) or "")
                # Prezzo € più vicino al nome del prodotto (gestisce pagine liste/negozio)
                price_str = pick_price_near_product(text, name) if pick_price_near_product else None
                if price_str:
                    val = self._extract_price_from_text(price_str)
                    if val and val >= 1:
                        return idx, price_str, val
            except Exception as e:
                logger.info(f"⚠️ Arricchimento prezzo fallito per {url}: {str(e)[:80]}")
            return idx, None, 0

        enriched = await asyncio.gather(*[_fetch_price(i) for i in targets])
        for idx, price_str, val in enriched:
            if price_str:
                results[idx]["price"] = price_str
                results[idx]["price_numeric"] = val
                logger.info(f"💰 Prezzo arricchito: {results[idx].get('site','')} -> {price_str}")
        return results

    def _extract_shopping_results(self, soup: BeautifulSoup, query: str) -> List[Dict[str, Any]]:
        """Estrae risultati da Google Shopping HTML"""
        results = []
        try:
            # Strategia 1: Cerca risultati sponsorizzati (sponsored ads)
            sponsored_items = soup.find_all('div', class_=['pla-unit', 'sh-dgr__content', 'sh-dlr__product-result'])
            logger.info(f"🛒 Trovati {len(sponsored_items)} elementi sponsorizzati")
            for item in sponsored_items[:10]:  # Max 10 risultati
                try:
                    result = self._extract_shopping_item(item, query)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"⚠️ Errore estrazione item sponsorizzato: {e}")
                    continue

            # Strategia 2: Cerca risultati organici
            organic_items = soup.find_all('div', class_=['sh-dgr__content', 'pla-unit'])
            logger.info(f"🛒 Trovati {len(organic_items)} elementi organici")
            for item in organic_items[:10]:  # Max 10 risultati
                try:
                    result = self._extract_shopping_item(item, query)
                    if result and result not in results:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"⚠️ Errore estrazione item organico: {e}")
                    continue

            # Strategia 3: Cerca qualsiasi link con prezzi
            price_links = soup.find_all('a', href=True)
            for link in price_links[:20]:  # Max 20 link
                try:
                    href = link.get('href', '')
                    if 'url=' in href and any(site in href.lower() for site in ['amazon', 'ebay', 'mediaworld', 'unieuro']):
                        result = self._extract_link_result(link, query)
                        if result and result not in results:
                            results.append(result)
                except Exception as e:
                    logger.debug(f"⚠️ Errore estrazione link: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Errore estrazione risultati shopping: {e}")

        return results

    def _extract_shopping_item(self, item, query: str) -> Optional[Dict[str, Any]]:
        """Estrae dati da un item Google Shopping"""
        try:
            # Titolo prodotto
            title_elem = item.find(['h3', 'h4', 'a', 'span'], class_=['shntl', 'sh-dlr__product-title'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            title = self._clean_product_title(title)  # Pulisci il titolo

            # Prezzo
            price_elem = item.find(string=re.compile(r'€\s*\d+'))
            if not price_elem:
                price_elem = item.find(['span', 'div'], string=re.compile(r'\d+[.,]\d+'))

            price_text = price_elem.strip() if price_elem else ""
            price = self._extract_price_from_text(price_text)

            # URL e sito
            link_elem = item.find('a', href=True)
            url = link_elem['href'] if link_elem else ""

            if url.startswith('/url?q='):
                # Decodifica URL Google
                url = url.split('/url?q=')[1].split('&')[0]

            site = self._extract_site_from_url(url)

            # Descrizione
            desc_elem = item.find(['div', 'span'], class_=['aULzUe', 'sh-dlr__product-snippet'])
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            if title and url and site:
                return {
                    'name': title,
                    'price': price_text if price_text else "Prezzo non disponibile",
                    'price_numeric': price,
                    'url': url,
                    'site': site,
                    'description': description,
                    'source': 'google_shopping',
                    'query': query,
                    'validation_score': 0.8
                }

        except Exception as e:
            logger.debug(f"⚠️ Errore estrazione shopping item: {e}")
            return None

    def _extract_link_result(self, link, query: str) -> Optional[Dict[str, Any]]:
        """Estrae dati da un link generico"""
        try:
            title = link.get_text(strip=True)
            title = self._clean_product_title(title)  # Pulisci il titolo
            url = link.get('href', '')

            # Filtra risultati che sono chiaramente filtri o non prodotti
            filter_keywords = [
                'fino a', 'oltre', 'prezzo', 'filtra', 'filtro', 'categoria', 'marca',
                'venditore', 'confronta', 'visualizza', 'accedi', 'elenco', 'collezioni',
                'preferenze', 'desideri', 'ordina', 'sort', 'filter', 'price range',
                'confronta i prezzi', 'visualizza lista', 'prezzo decrescente', 'prezzo crescente'
            ]

            title_lower = title.lower()
            if any(keyword in title_lower for keyword in filter_keywords):
                return None  # Salta questo risultato

            # Verifica che il titolo sia abbastanza lungo (non solo "€" o numeri)
            if len(title) < 5 or title.isdigit() or title in ['€', '€0', '€0,00']:
                return None

            if url.startswith('/url?q='):
                url = url.split('/url?q=')[1].split('&')[0]

            site = self._extract_site_from_url(url)

            if title and url and site:
                return {
                    'name': title,
                    'price': "Prezzo non disponibile",
                    'price_numeric': 0,
                    'url': url,
                    'site': site,
                    'description': f"Risultato per {query}",
                    'source': 'google_shopping_link',
                    'query': query,
                    'validation_score': 0.6
                }

        except Exception as e:
            logger.debug(f"⚠️ Errore estrazione link result: {e}")
            return None

    def _extract_price_from_text(self, price_text: str) -> float:
        """Estrae prezzo numerico dal testo"""
        try:
            if not price_text or price_text == "Prezzo non disponibile":
                logger.info(f"🦆 DEBUG: Prezzo vuoto o non disponibile, ritorno 0.0")
                return 0.0

            logger.info(f"🦆 DEBUG: === CONVERSIONE PREZZO NUMERICO ===")
            logger.info(f"🦆 DEBUG: Prezzo input: '{price_text}'")

            # Cerca pattern di prezzo con regex
            import re
            price_pattern = r'€\s*(\d+[.,]\d+)'
            match = re.search(price_pattern, str(price_text))
            if match:
                price_clean = match.group(1)
                logger.info(f"🦆 DEBUG: Prezzo estratto con regex: '{price_clean}'")
            else:
                # Fallback: rimuovi simboli di valuta e spazi
                price_clean = re.sub(r'[€$£\s]', '', str(price_text))
                logger.info(f"🦆 DEBUG: Dopo rimozione simboli: '{price_clean}'")

            # Gestisci virgole e punti decimali (formato italiano)
            if ',' in price_clean and '.' in price_clean:
                # Se ha entrambi, la virgola è il separatore delle migliaia
                price_clean = price_clean.replace('.', '').replace(',', '.')
                logger.info(f"🦆 DEBUG: Virgola e punto -> virgola migliaia: '{price_clean}'")
            elif ',' in price_clean:
                # Se ha solo virgola, potrebbe essere decimale o migliaia
                if price_clean.count(',') == 1 and len(price_clean.split(',')[1]) <= 2:
                    # Probabilmente decimale (es: 123,45)
                    price_clean = price_clean.replace(',', '.')
                    logger.info(f"🦆 DEBUG: Virgola decimale -> punto: '{price_clean}'")
                else:
                    # Probabilmente migliaia (es: 1,234,567)
                    price_clean = price_clean.replace(',', '')
                    logger.info(f"🦆 DEBUG: Virgola migliaia rimossa: '{price_clean}'")

            # Estrai solo numeri e punto decimale
            price_match = re.search(r'[\d.]+', price_clean)
            if price_match:
                price_float = float(price_match.group())

                # FILTRO PREZZI MALFORMATI (basato su pattern specifici)
                price_str = str(price_float)

                # Pattern 1: Troppi zeri iniziali (es: 093385,72 -> 93385.72)
                if price_str.startswith('0') and len(price_str) > 4:
                    # Rimuovi zeri iniziali e ricalcola
                    price_clean_fixed = price_str.lstrip('0')
                    if price_clean_fixed and price_clean_fixed != '.':
                        try:
                            price_float_fixed = float(price_clean_fixed)
                            logger.info(f"🦆 DEBUG: 🔧 Prezzo corretto da {price_float}€ a {price_float_fixed}€")
                            price_float = price_float_fixed
                        except:
                            pass

                # Pattern 2: Prezzi con troppe cifre decimali (es: 123.456789)
                if '.' in price_str:
                    decimal_part = price_str.split('.')[1]
                    if len(decimal_part) > 2:  # Più di 2 decimali
                        # Arrotonda a 2 decimali
                        price_float = round(price_float, 2)
                        logger.info(f"🦆 DEBUG: 🔧 Prezzo arrotondato a 2 decimali: {price_float}€")

                # Pattern 3: Prezzi con formato strano (es: 123456.789 -> 123456.79)
                if price_float > 0 and price_float < 1:  # Prezzi sotto 1€ sono sospetti per molti prodotti
                    # Controlla se è un errore di parsing (es: 0.123456 -> 123.456)
                    if len(price_str) > 6 and price_str.startswith('0.'):
                        # Potrebbe essere un errore di parsing, prova a moltiplicare per 1000
                        potential_price = price_float * 1000
                        if 1 <= potential_price <= 10000:  # Range ragionevole
                            logger.info(f"🦆 DEBUG: 🔧 Prezzo corretto da {price_float}€ a {potential_price}€")
                            price_float = potential_price

                # Pattern 4: Controlla formato prezzi secondo standard
                # Formati validi: 0,87 | 255,00 | 255.000,00 | 3490.000,00

                # Pattern 5: Controlla formato decimali (sempre 2 cifre max)
                if '.' in price_str:
                    decimal_part = price_str.split('.')[1]
                    if len(decimal_part) > 2:  # Più di 2 decimali
                        # Arrotonda a 2 decimali
                        price_float = round(price_float, 2)
                        logger.info(f"🦆 DEBUG: 🔧 Prezzo arrotondato a 2 decimali: {price_float}€")

                # Pattern 6: Controlla se prezzo alto non è arrotondato al migliaio
                if price_float >= 1000:
                    integer_part = int(price_float)
                    # Se ha più di 3 cifre, dovrebbe essere arrotondato al migliaio
                    if integer_part % 1000 != 0:  # Non è arrotondato al migliaio
                        # Arrotonda al migliaio più vicino
                        price_float = round(integer_part / 1000) * 1000
                        logger.info(f"🦆 DEBUG: 🔧 Prezzo arrotondato al migliaio: {price_float}€")

                # Pattern 7: Scarta prezzi con formato strano (es: 4372869.01)
                # I prezzi alti dovrebbero essere sempre arrotondati al migliaio
                if price_float > 100000:
                    integer_part = int(price_float)
                    # Se non è arrotondato al migliaio, è sospetto
                    if integer_part % 1000 != 0:
                        logger.info(f"🦆 DEBUG: ❌ Prezzo alto non arrotondato al migliaio scartato: {price_float}€")
                        logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (NON ARROTONDATO) ===")
                        return 0.0

                # Pattern 8: Scarta prezzi con troppe cifre intere (es: 4369729,00)
                # I prezzi sopra 100k dovrebbero avere max 6 cifre intere
                if price_float > 100000:
                    integer_part = int(price_float)
                    integer_str = str(integer_part)
                    if len(integer_str) > 6:  # Più di 6 cifre intere
                        logger.info(f"🦆 DEBUG: ❌ Prezzo con troppe cifre intere scartato: {price_float}€ ({len(integer_str)} cifre)")
                        logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (TROPPE CIFRE) ===")
                        return 0.0

                # Pattern 9: Scarta prezzi con zero iniziale (es: 044,80)
                if price_float > 0 and price_float < 1000:
                    price_str = str(price_float)
                    if price_str.startswith('0') and len(price_str) > 3:
                        logger.info(f"🦆 DEBUG: ❌ Prezzo con zero iniziale scartato: {price_float}€")
                        logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (ZERO INIZIALE) ===")
                        return 0.0

                logger.info(f"🦆 DEBUG: ✅ Prezzo convertito e validato: '{price_text}' -> {price_float}")
                logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO ===")
                return price_float
            else:
                logger.info(f"🦆 DEBUG: ❌ Nessun numero trovato in '{price_clean}'")
                logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO ===")
                return 0.0

        except Exception as e:
            logger.error(f"❌ Errore estrazione prezzo '{price_text}': {e}")
            logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (ERRORE) ===")
            return 0.0

    def _extract_site_from_url(self, url: str) -> str:
        """Estrae il nome del sito dall'URL"""
        try:
            if not url:
                return "Sconosciuto"

            # Gestisci URL di tracking DuckDuckGo
            if 'links.duckduckgo.com' in url:
                return "DuckDuckGo"

            # Gestisci URL di Bing
            if 'bing.com' in url:
                return "Bing"

            # Estrai dominio
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Mappa domini a nomi più descrittivi
            site_mapping = {
                'www.amazon.it': 'Amazon',
                'amazon.it': 'Amazon',
                'www.mediaworld.it': 'MediaWorld',
                'mediaworld.it': 'MediaWorld',
                'www.unieuro.it': 'Unieuro',
                'unieuro.it': 'Unieuro',
                'www.carrefour.it': 'Carrefour',
                'carrefour.it': 'Carrefour',
                'www.conad.it': 'Conad',
                'conad.it': 'Conad',
                'www.ebay.it': 'eBay',
                'ebay.it': 'eBay',
                'www.comparor.com': 'Comparor',
                'comparor.com': 'Comparor',
                'www.delupe.it': 'Delupe',
                'delupe.it': 'Delupe',
                'www.prezzoforte.com': 'PrezzoForte',
                'prezzoforte.com': 'PrezzoForte',
                'www.awin1.com': 'Awin',
                'awin1.com': 'Awin'
            }

            # Rimuovi www. se presente per il mapping
            domain_clean = domain.replace('www.', '')

            if domain_clean in site_mapping:
                return site_mapping[domain_clean]

            # Se non è mappato, usa il dominio principale
            if '.' in domain:
                return domain.split('.')[-2].title()

            return domain.title()
        except Exception as e:
            logger.debug(f"⚠️ Errore estrazione sito da '{url}': {e}")
            return "Sconosciuto"

    def _clean_product_title(self, title: str) -> str:
        """Pulisce e normalizza il titolo del prodotto"""
        if not title:
            return ""

        try:
            # Rimuovi caratteri speciali e spazi multipli
            cleaned = re.sub(r'\s+', ' ', title.strip())

            # Rimuovi parti comuni che rendono i titoli confusi
            patterns_to_remove = [
                r'Risultato DuckDuckGo per\s+["\']?[^"\']*["\']?',
                r'Risultato\s+[A-Za-z]+\s+per\s+["\']?[^"\']*["\']?',
                r'Fonte:\s*',
                r'Prezzo:\s*€?\d+[.,]\d+',
                r'Score:\s*[A-Za-z%]+',
                r'Clicca\s*$',
                r'https?://[^\s]+',
                r'www\.[^\s]+',
                r'\.it\s*$',
                r'\.com\s*$',
                r'\.net\s*$',
                r'\.org\s*$',
                # Rimuovi prezzi dal titolo
                r'€\s*\d+[.,]\d+\s*€?[A-Za-z\s]*$',
                r'\d+[.,]\d+\s*€\s*[A-Za-z\s]*$',
                r'€\s*\d+[.,]\d+[A-Za-z\s]*$',
                r'\d+[.,]\d+\s*€?[A-Za-z\s]*$',
                # Rimuovi parti finali con prezzi
                r'\s+\d+[.,]\d+\s*€\s*[A-Za-z\s]*$',
                r'\s+€\s*\d+[.,]\d+\s*[A-Za-z\s]*$'
            ]

            for pattern in patterns_to_remove:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

            # Rimuovi spazi extra e caratteri strani
            cleaned = re.sub(r'\s+', ' ', cleaned.strip())
            cleaned = re.sub(r'[^\w\s\-.,()€$%]', '', cleaned)

            # Limita la lunghezza
            if len(cleaned) > 80:
                cleaned = cleaned[:77] + "..."

            return cleaned

        except Exception as e:
            logger.debug(f"⚠️ Errore pulizia titolo: {e}")
            return title[:80] if len(title) > 80 else title
