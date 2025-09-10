"""
Google Price Finder - Sistema per trovare automaticamente prezzi tramite Google Shopping
Cerca prodotti su Google e suggerisce siti competitor con prezzi
"""

import requests
import re
import asyncio
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GooglePriceFinder:
    """Sistema per trovare prezzi automaticamente tramite Google Shopping"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Siti e-commerce italiani principali
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
        
        logger.info("🔍 Google Price Finder inizializzato")
    
    async def search_product_sites(self, product_name: str, brand: str = "", model: str = "") -> Dict[str, Any]:
        """Trova SITI che vendono un prodotto (invece di prezzi specifici)"""
        try:
            # Costruisci query di ricerca
            search_query = self._build_search_query(product_name, brand, model)
            logger.info(f"🔍 Ricerca Google SITI: {search_query}")
            
            # Cerca su Google Shopping per trovare siti
            shopping_sites = await self._find_sites_google_shopping(search_query)
            
            # Cerca anche su Google normale per più siti
            web_sites = await self._find_sites_google_web(search_query)
            
            # Combina e pulisci lista siti
            all_sites = self._combine_and_clean_sites(shopping_sites, web_sites)
            
            # Genera URLs prodotto per ogni sito
            site_urls = self._generate_product_urls(all_sites, search_query)
            
            return {
                'success': True,
                'product_query': search_query,
                'total_sites_found': len(all_sites),
                'recommended_sites': site_urls[:10],  # Top 10 siti
                'all_sites': all_sites,
                'search_timestamp': datetime.now().isoformat(),
                'message': f"Trovati {len(all_sites)} siti che vendono questo prodotto"
            }
            
        except Exception as e:
            logger.error(f"❌ Errore ricerca Google: {e}")
            return {
                'success': False,
                'error': str(e),
                'recommended_sites': [],
                'all_sites': []
            }
    
    def _build_search_query(self, product_name: str, brand: str = "", model: str = "") -> str:
        """Costruisce query di ricerca ottimizzata"""
        parts = [product_name]
        if brand:
            parts.append(brand)
        if model:
            parts.append(model)
        
        # Aggiungi termini per migliorare risultati e-commerce
        query = " ".join(parts) + " prezzo acquista online"
        return query.strip()
    
    async def _search_google_shopping(self, query: str) -> List[Dict[str, Any]]:
        """Cerca su Google Shopping"""
        try:
            # URL Google Shopping Italia
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&tbm=shop&hl=it&gl=IT"
            
            logger.info(f"🛒 Google Shopping: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Cerca risultati Google Shopping (struttura può cambiare)
            shopping_items = soup.find_all('div', class_=['sh-dgr__content', 'pla-unit'])
            
            for item in shopping_items[:20]:  # Limita a 20 risultati
                try:
                    result = self._extract_shopping_item(item)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"Errore estrazione item shopping: {e}")
                    continue
            
            logger.info(f"🛒 Google Shopping: {len(results)} risultati")
            return results
            
        except Exception as e:
            logger.error(f"❌ Errore Google Shopping: {e}")
            return []
    
    async def _search_google_web(self, query: str) -> List[Dict[str, Any]]:
        """Cerca su Google normale per trovare più siti e-commerce"""
        try:
            # Cerca specificamente sui nostri siti target
            results = []
            
            for site in self.target_sites[:5]:  # Limita per non fare troppe richieste
                try:
                    site_query = f"{query} site:{site}"
                    encoded_query = quote_plus(site_query)
                    url = f"https://www.google.com/search?q={encoded_query}&hl=it&gl=IT"
                    
                    response = requests.get(url, headers=self.headers, timeout=8)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Estrai primi 3 risultati per sito
                        search_results = soup.find_all('div', class_='g')[:3]
                        
                        for result in search_results:
                            try:
                                item = self._extract_web_result(result, site)
                                if item:
                                    results.append(item)
                            except:
                                continue
                    
                    # Pausa tra richieste per non essere bloccati
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.debug(f"Errore ricerca su {site}: {e}")
                    continue
            
            logger.info(f"🌐 Google Web: {len(results)} risultati")
            return results
            
        except Exception as e:
            logger.error(f"❌ Errore Google Web: {e}")
            return []
    
    def _extract_shopping_item(self, item) -> Optional[Dict[str, Any]]:
        """Estrae dati da un item Google Shopping"""
        try:
            # Titolo prodotto
            title_elem = item.find(['h3', 'h4', 'a'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
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
            
            if title and price and url and site:
                return {
                    'title': title,
                    'price': price,
                    'price_text': price_text,
                    'url': url,
                    'site': site,
                    'source': 'google_shopping'
                }
                
        except Exception as e:
            logger.debug(f"Errore estrazione shopping item: {e}")
        
        return None
    
    def _extract_web_result(self, result, target_site: str) -> Optional[Dict[str, Any]]:
        """Estrae dati da un risultato Google Web"""
        try:
            # Titolo
            title_elem = result.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # URL
            link_elem = result.find('a', href=True)
            url = link_elem['href'] if link_elem else ""
            
            # Snippet per cercare prezzi
            snippet_elem = result.find(['span', 'div'], class_=['st', 'VwiC3b'])
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Cerca prezzo nel snippet
            price = self._extract_price_from_text(f"{title} {snippet}")
            
            if title and url and target_site in url:
                return {
                    'title': title,
                    'price': price,
                    'price_text': snippet[:100] if snippet else "",
                    'url': url,
                    'site': target_site,
                    'source': 'google_web'
                }
                
        except Exception as e:
            logger.debug(f"Errore estrazione web result: {e}")
        
        return None
    
    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Estrae prezzo numerico da testo"""
        if not text:
            return None
        
        # Pattern per prezzi italiani
        patterns = [
            r'€\s*(\d+(?:[.,]\d{2})?)',
            r'(\d+(?:[.,]\d{2})?)\s*€',
            r'EUR\s*(\d+(?:[.,]\d{2})?)',
            r'(\d+(?:[.,]\d{2})?)\s*EUR',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    price_str = matches[0].replace(',', '.')
                    price = float(price_str)
                    if 1 <= price <= 50000:  # Range ragionevole
                        return price
                except:
                    continue
        
        return None
    
    def _extract_site_from_url(self, url: str) -> str:
        """Estrae nome sito da URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Rimuovi www. e sottodomini
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain
        except:
            return ""
    
    def _combine_and_filter_results(self, shopping_results: List[Dict], web_results: List[Dict]) -> List[Dict[str, Any]]:
        """Combina e filtra risultati per rimuovere duplicati"""
        all_results = shopping_results + web_results
        
        # Rimuovi duplicati per URL
        seen_urls = set()
        filtered_results = []
        
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls and result.get('price'):
                seen_urls.add(url)
                filtered_results.append(result)
        
        # Ordina per prezzo
        filtered_results.sort(key=lambda x: x.get('price', 99999))
        
        return filtered_results
    
    def _group_results_by_site(self, results: List[Dict]) -> Dict[str, Any]:
        """Raggruppa risultati per sito"""
        sites = {}
        
        for result in results:
            site = result.get('site', 'unknown')
            if site not in sites:
                sites[site] = {
                    'site_name': site,
                    'products_found': 0,
                    'price_range': {'min': None, 'max': None},
                    'best_result': None,
                    'all_results': []
                }
            
            sites[site]['products_found'] += 1
            sites[site]['all_results'].append(result)
            
            price = result.get('price')
            if price:
                if sites[site]['price_range']['min'] is None or price < sites[site]['price_range']['min']:
                    sites[site]['price_range']['min'] = price
                    sites[site]['best_result'] = result
                
                if sites[site]['price_range']['max'] is None or price > sites[site]['price_range']['max']:
                    sites[site]['price_range']['max'] = price
        
        return sites

    async def _find_sites_google_shopping(self, query: str) -> List[str]:
        """Estrae SITI da Google Shopping (con debug completo)"""
        sites = []
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&tbm=shop&hl=it&gl=IT"
            logger.info(f"🛒 Google Shopping URL: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            logger.info(f"🛒 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.text
                logger.info(f"🛒 HTML Length: {len(html_content)} chars")
                
                # Debug: controlla se c'è contenuto
                if 'mediaworld' in html_content.lower():
                    logger.info("✅ Trovato MediaWorld nell'HTML!")
                if 'amazon' in html_content.lower():
                    logger.info("✅ Trovato Amazon nell'HTML!")
                if 'unieuro' in html_content.lower():
                    logger.info("✅ Trovato Unieuro nell'HTML!")
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Strategia 1: Link con 'url=' (Google Shopping classico)
                links = soup.find_all('a', href=True)
                logger.info(f"🔗 Trovati {len(links)} link totali")
                
                for link in links:
                    href = link.get('href', '')
                    if 'url=' in href:
                        try:
                            real_url = href.split('url=')[1].split('&')[0]
                            domain = urlparse(real_url).netloc.lower()
                            if domain and domain not in sites:
                                sites.append(domain)
                                logger.info(f"✅ Sito trovato: {domain}")
                        except:
                            continue
                
                # Strategia 2: Cerca domini direttamente nel testo
                for target_site in self.target_sites:
                    if target_site in html_content.lower() and target_site not in sites:
                        sites.append(target_site)
                        logger.info(f"✅ Sito target trovato: {target_site}")
                            
            logger.info(f"🛒 Google Shopping SITI: {len(sites)} siti trovati: {sites}")
            return sites[:20]
            
        except Exception as e:
            logger.error(f"❌ Errore Google Shopping: {e}")
            return []

    async def _find_sites_google_web(self, query: str) -> List[str]:
        """Estrae SITI da Google Web (strategia migliorata)"""
        sites = []
        try:
            # Strategia: ricerca normale senza "site:" che confonde
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&hl=it&gl=IT"
            logger.info(f"🌐 Google Web URL: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=15)
            logger.info(f"🌐 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.text
                logger.info(f"🌐 HTML Length: {len(html_content)} chars")
                
                # Debug: controlla contenuto e-commerce
                ecommerce_found = 0
                for target_site in self.target_sites:
                    if target_site.replace('.it', '') in html_content.lower():
                        ecommerce_found += 1
                        
                logger.info(f"🌐 E-commerce trovati nell'HTML: {ecommerce_found}/{len(self.target_sites)}")
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Strategia 1: Risultati organici classici
                results = soup.find_all('div', {'class': ['g', 'tF2Cxc', 'yuRUbf']})
                logger.info(f"🔗 Risultati organici trovati: {len(results)}")
                
                for result in results:
                    link = result.find('a', href=True)
                    if link:
                        href = link.get('href', '')
                        if href.startswith('http'):
                            try:
                                domain = urlparse(href).netloc.lower()
                                if domain and domain not in sites:
                                    # Filtra e-commerce italiani
                                    if any(target in domain for target in self.target_sites) or domain.endswith('.it'):
                                        sites.append(domain)
                                        logger.info(f"✅ Sito Web trovato: {domain}")
                            except:
                                continue
                
                # Strategia 2: Cerca tutti i link e filtra per e-commerce
                all_links = soup.find_all('a', href=True)
                logger.info(f"🔗 Link totali: {len(all_links)}")
                
                for link in all_links:
                    href = link.get('href', '')
                    if href.startswith('http'):
                        try:
                            domain = urlparse(href).netloc.lower()
                            if domain and domain not in sites:
                                # Solo siti target noti
                                if any(target in domain for target in self.target_sites):
                                    sites.append(domain)
                                    logger.info(f"✅ Sito target Web: {domain}")
                        except:
                            continue
                                
            logger.info(f"🌐 Google Web SITI: {len(sites)} siti trovati: {sites}")
            return sites[:15]
            
        except Exception as e:
            logger.error(f"❌ Errore Google Web: {e}")
            return []

    def _combine_and_clean_sites(self, shopping_sites: List[str], web_sites: List[str]) -> List[str]:
        """Combina e pulisce lista siti (con fallback automatico)"""
        all_sites = []
        
        # Priorità ai siti target conosciuti
        priority_sites = []
        other_sites = []
        
        for site in shopping_sites + web_sites:
            if site not in all_sites:
                if any(target in site for target in self.target_sites):
                    priority_sites.append(site)
                else:
                    other_sites.append(site)
        
        # Prima siti prioritari, poi altri
        all_sites = priority_sites + other_sites
        
        # FALLBACK: Se Google non trova nulla, usa i siti principali
        if len(all_sites) == 0:
            logger.info("🔄 FALLBACK: Google non ha trovato siti, uso lista predefinita")
            # Ordina per priorità: prima i più popolari
            priority_order = ['amazon.it', 'mediaworld.it', 'unieuro.it', 'euronics.it', 'eprice.it']
            all_sites = priority_order + [site for site in self.target_sites if site not in priority_order]
        
        logger.info(f"🎯 Siti finali combinati: {all_sites}")
        return all_sites[:20]  # Max 20 siti totali

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
google_price_finder = GooglePriceFinder() 