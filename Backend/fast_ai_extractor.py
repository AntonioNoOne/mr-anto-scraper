#!/usr/bin/env python3

"""
Fast AI Extractor - Estrazione veloce e semplice da singola pagina
Niente caricamenti dinamici, niente paginazione, solo estrazione chirurgica
"""

import asyncio
import json
import random
import time
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page, Browser
from ai_content_analyzer import AIContentAnalyzer
from selector_database import SelectorDatabase
from historical_products_db import HistoricalProductsDB
from proxy_manager import ProxyManager
from captcha_handler import CaptchaHandler
from datetime import datetime
import logging
import os
import aiohttp

# Costanti per configurazioni
ANTI_BOT_SITES = ['unieuro.it', 'amazon.', 'ebay.', 'mediaworld.it', 'euronics.it', 'trony.it']
STRONG_ANTI_BOT_SITES = ['unieuro.it', 'amazon.', 'ebay.']

# Configurazioni browser
BROWSER_ARGS_BASE = [
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor'
]

BROWSER_ARGS_STEALTH = [
    '--window-size=1,1',
    '--window-position=9999,9999',
    '--disable-gpu',
    '--disable-images',
    '--disable-extensions-except=',
    '--disable-plugins-discovery',
    '--disable-default-apps',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',
    '--disable-ipc-flooding-protection'
]

BROWSER_ARGS_VISIBLE = [
    '--window-size=1600,1000',
    '--window-position=0,0',
    '--start-maximized',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding'
]

class FastAIExtractor:
    """Estrattore veloce con AI chirurgica"""
    
    def __init__(self):
        """Inizializza l'estrattore AI"""
        self.ai_analyzer = AIContentAnalyzer()
        self.selector_db = SelectorDatabase()
        self.historical_db = HistoricalProductsDB()
        self.proxy_manager = ProxyManager()
        self.captcha_handler = CaptchaHandler()
        self.browser_config = {
            'mode': 'stealth',
            'timeout': 60,
            'human_delay': 2.0,
            'user_agent': 'auto',
            'proxy': ''
        }
        self.logger = logging.getLogger(__name__)
        
        # User agents più realistici e variati per evitare rilevamento
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/117.0.0.0'
        ]
        
        # Delays realistici per simulare comportamento umano
        self.human_delays = [0.5, 1.0, 1.5, 2.0, 2.5]
        
        # Rate limiting per evitare blocchi
        self.last_request_time = {}
        self.min_delay_between_requests = 10
        
        # Proxy gratuiti per bypassare blocchi IP
        self.proxy_list = [
            'http://103.149.162.194:80',
            'http://103.149.162.195:80',
            'http://103.149.162.196:80',
            'http://103.149.162.197:80',
            'http://103.149.162.198:80',
        ]
        self.current_proxy_index = 0
        self.immobiliare_selectors = []
        self.initial_html_cache = None
        self.initial_text_cache = None
        self.start_time = None  # Variabile globale per il timestamp di inizio
    
    def _get_user_agent(self, browser_config: dict = None) -> str:
        """Restituisce l'user agent appropriato in base alla configurazione"""
        if browser_config and 'user_agent' in browser_config:
            user_agent_setting = browser_config['user_agent']
            if user_agent_setting == 'chrome':
                return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
            elif user_agent_setting == 'firefox':
                return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0'
            elif user_agent_setting == 'safari':
                return 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15'
            elif user_agent_setting == 'edge':
                return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
            else:
                return self.captcha_handler.get_user_agent()
        else:
            return self.captcha_handler.get_user_agent()
    
    async def extract_products_fast(self, url: str, browser_config: Optional[Dict] = None, stop_flag: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Estrazione veloce da singola pagina con checkpoint di stop
        
        Args:
            url: URL da estrarre
            browser_config: Configurazione browser
            stop_flag: Dizionario con flag 'stop' per fermare l'estrazione
        """
        # 🕐 REGISTRA INIZIO SCRAPING
        self.start_time = datetime.now()
        print(f"🚀 Fast AI Extractor - URL: {url}")
        print(f"⏰ INIZIO SCRAPING: {self.start_time.isoformat()}")
        
        # Usa configurazione personalizzata se fornita, altrimenti default
        if browser_config:
            mode = browser_config.get('mode', 'stealth')
            timeout = browser_config.get('timeout', 60)
            human_delay = browser_config.get('human_delay', 2.0)
            user_agent = browser_config.get('user_agent', 'auto')
            proxy = browser_config.get('proxy')
            
            # Determina headless in base alla modalità
            if mode == 'visible':
                headless = False
            elif mode == 'stealth':
                headless = False
            elif mode == 'normal':
                headless = True
        else:
            mode = 'stealth'
            timeout = 60
            human_delay = 2.0
            user_agent = 'auto'
            proxy = None
        
        # Rate limiting per evitare blocchi
        domain = self._extract_domain(url)
        current_time = time.time()
        
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            if time_since_last < self.min_delay_between_requests:
                wait_time = self.min_delay_between_requests - time_since_last
                await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = current_time
        
        # Prima prova sempre in modalità normale (veloce)
        needs_visible_browser = False
        
        # Per altri siti, usa il metodo normale
        return await self._extract_single_attempt(url, headless, needs_visible_browser, None, browser_config, stop_flag)
    

    
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
    
    async def _extract_single_attempt(self, url: str, headless: bool, needs_visible_browser: bool, proxy: str = None, browser_config: dict = None, stop_flag: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Tentativo singolo di estrazione
        
        Args:
            url: URL da estrarre
            headless: Modalità headless
            needs_visible_browser: Se serve browser visibile
            proxy: Proxy da usare
            browser_config: Configurazione browser
            stop_flag: Flag per fermare l'estrazione
        """
        

        
        if needs_visible_browser and headless:
            headless = False
        
        try:
            async with async_playwright() as p:
                browser = None
                
                # 🚀 RENDER FIX: Forza headless=True su Render per evitare errori browser
                if os.environ.get('RENDER'):
                    headless = True
                    print(f"🌐 RENDER DETECTED: Forzo headless=True")
                else:
                    # Determina la modalità browser in base alla configurazione
                    if browser_config and 'mode' in browser_config:
                        mode = browser_config['mode']
                        if mode == 'visible':
                            headless = False
                        elif mode == 'stealth':
                            headless = False
                        elif mode == 'normal':
                            headless = True
                    else:
                        # Fallback alla logica automatica basata sul sito
                        needs_stealth_mode = any(site in url.lower() for site in ANTI_BOT_SITES)
                        
                        if needs_stealth_mode:
                            headless = False
                        else:
                            headless = True
                    
                    # 🚨 CORREZIONE CRITICA: Se serve browser visibile, forza headless=False
                    if needs_visible_browser:
                        headless = False
                        print(f"🖥️ FORZO BROWSER VISIBILE: headless={headless}")
                
                # Rilevamento speciale per siti con anti-bot molto forte
                is_strong_anti_bot = any(site in url.lower() for site in STRONG_ANTI_BOT_SITES)
                
                if is_strong_anti_bot:
                    if browser_config and browser_config.get('mode') == 'visible':
                        headless = False
                    else:
                        headless = False
                
                # Usa il proxy dalla configurazione personalizzata, dal parametro o carica uno nuovo
                if browser_config and 'proxy' in browser_config and browser_config['proxy']:
                    proxy = browser_config['proxy']
                elif proxy:
                    pass
                else:
                    proxy = self.proxy_manager.get_random_proxy()
                
                # Configura proxy per SOCKS5 o HTTP
                if proxy and proxy.startswith('socks5://'):
                    proxy_host = proxy.replace('socks5://', '').split(':')[0]
                    proxy_port = proxy.replace('socks5://', '').split(':')[1]
                    proxy_arg = f'--proxy-server=socks5://{proxy_host}:{proxy_port}'
                elif proxy:
                    proxy_arg = f'--proxy-server={proxy}'
                else:
                    proxy_arg = None
                
                # Configurazione browser args consolidata
                mode = browser_config.get('mode', 'stealth') if browser_config else 'stealth'
                user_agent = self._get_user_agent(browser_config)
                browser_args = self._get_browser_args(mode, is_strong_anti_bot, user_agent)
                
                if proxy_arg:
                    browser_args.append(proxy_arg)
                
                # Lancia browser con configurazione appropriata
                browser = await p.chromium.launch(
                    headless=headless,
                    args=browser_args
                )
                
                page = await browser.new_page()
                
                # Verifica che il browser sia visibile (per modalità non-headless)
                if not headless:
                    try:
                        await page.set_viewport_size({"width": 1600, "height": 1000})
                        
                        if is_strong_anti_bot:
                            await page.wait_for_timeout(3000)
                            
                            try:
                                await page.bring_to_front()
                                
                                try:
                                    await page.mouse.click(800, 500)
                                    await page.wait_for_timeout(1000)
                                except Exception as e:
                                    pass
                                    
                            except Exception as e:
                                pass
                    except Exception as e:
                        pass
                
                # Script anti-detection semplificato
                anti_detection_script = """
                    (function() {
                        Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                            configurable: true
                        });
                        
                        const propertiesToRemove = [
                            'webdriver', 'automation', 'selenium'
                        ];
                        
                        propertiesToRemove.forEach(prop => {
                            try {
                                delete navigator[prop];
                                delete navigator.__proto__[prop];
                                delete window[prop];
                                delete window.navigator[prop];
                            } catch(e) {}
                        });
                        
                        if (window.chrome) {
                            window.chrome = {
                                runtime: {},
                                loadTimes: function() {},
                                csi: function() {},
                                app: {}
                            };
                        }
                    })();
                """
                
                await page.add_init_script(anti_detection_script)
                
                # Simula comportamento umano: delay casuale prima del caricamento
                if browser_config and 'human_delay' in browser_config:
                    human_delay = browser_config['human_delay']
                elif needs_stealth_mode:
                    human_delay = random.uniform(2.0, 5.0)
                else:
                    human_delay = random.choice(self.human_delays)
                
                # Delay extra per siti anti-bot forti
                if is_strong_anti_bot:
                    extra_delay = random.uniform(2.0, 4.0)
                    human_delay += extra_delay
                
                await page.wait_for_timeout(int(human_delay * 1000))
                
                # Timeout adattivo
                if browser_config and 'timeout' in browser_config:
                    timeout = browser_config['timeout'] * 1000
                elif needs_stealth_mode:
                    timeout = 60000 if proxy else 90000
                else:
                    timeout = 20000 if proxy else 40000
                
                # Per siti anti-bot forti, rimuovi header che rivelano automazione
                if is_strong_anti_bot:
                    pass
                else:
                    await page.set_extra_http_headers({
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Cache-Control': 'max-age=0',
                        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"Windows"'
                    })
                
                # Navigazione semplice
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                
                # CHECKPOINT 1: Controlla se deve fermarsi dopo la navigazione
                if stop_flag and stop_flag.get('stop'):
                    print(f"🛑 Estrazione fermata per {url} dopo navigazione")
                    await browser.close()
                    return {"success": False, "error": "Estrazione fermata dall'utente"}
                
                # 🚀 RUBO HTML IMMEDIATAMENTE - Prima che il captcha si attivi!
                try:
                    # Estrai HTML subito dopo il caricamento
                    initial_html = await page.content()
                    initial_text = await page.text_content('body') or ""
                    
                    # Controlla se c'è già contenuto utile (prima del captcha)
                    if len(initial_text) > 500 and not any(blocker in initial_text.lower() for blocker in ['checking your browser', 'cloudflare', 'captcha', 'verification']):
                        print(f"🎯 HTML rubato con successo prima del captcha! ({len(initial_text)} caratteri)")
                        # Salva l'HTML iniziale per usarlo se il captcha fallisce
                        self.initial_html_cache = initial_html
                        self.initial_text_cache = initial_text
                        
                        # Se abbiamo HTML utile, salta il controllo captcha per velocizzare
                        print(f"⚡ Sito normale rilevato, salto controllo captcha per velocizzare")
                        skip_captcha_check = True
                    else:
                        print(f"⚠️ HTML iniziale non utile o già bloccato ({len(initial_text)} caratteri)")
                        self.initial_html_cache = None
                        self.initial_text_cache = None
                        skip_captcha_check = False
                except Exception as e:
                    print(f"⚠️ Errore estrazione HTML iniziale: {e}")
                    self.initial_html_cache = None
                    self.initial_text_cache = None
                    skip_captcha_check = False
                
                # GESTIONE CLOUDFLARE E CAPTCHA - Solo se necessario
                if not skip_captcha_check:
                    try:
                        # Rileva se c'è un captcha o challenge Cloudflare
                        page_content = await page.text_content('body') or ""
                        if self.captcha_handler.detect_captcha(page_content):
                            print(f"🛡️ Captcha rilevato su {url}, tentativo di risoluzione...")
                            
                            # Gestisci la challenge Cloudflare
                            if await self.captcha_handler.handle_cloudflare_challenge(page):
                                print(f"✅ Challenge Cloudflare risolta per {url}")
                                # Aspetta che la pagina si carichi completamente dopo la risoluzione
                                await self.captcha_handler.wait_for_page_load(page)
                            else:
                                print(f"⚠️ Challenge Cloudflare non risolta per {url}, continuo comunque...")
                    except Exception as e:
                        print(f"⚠️ Errore gestione captcha per {url}: {e}")
                else:
                    print(f"🚀 Sito normale, procedo direttamente con l'estrazione")
                
                # CHECKPOINT 2: Controlla se deve fermarsi dopo l'estrazione HTML
                if stop_flag and stop_flag.get('stop'):
                    print(f"🛑 Estrazione fermata per {url} dopo estrazione HTML")
                    await browser.close()
                    return {"success": False, "error": "Estrazione fermata dall'utente"}
                
                # 🚀 ESTRAZIONE NORMALE - Sistema generico per tutti i siti
                print(f"🎯 Estrazione normale per {url}...")
                
                # Prima estrazione sempre in modalità normale (veloce)
                print("🚀 Prima estrazione in modalità normale...")
                
                # CHECKPOINT 3: Controlla se deve fermarsi prima dell'estrazione AI
                if stop_flag and stop_flag.get('stop'):
                    print(f"🛑 Estrazione fermata per {url} prima dell'estrazione AI")
                    await browser.close()
                    return {"success": False, "error": "Estrazione fermata dall'utente"}
                
                # Attesa per caricamento dinamico
                if is_strong_anti_bot:
                    # CHECKPOINT durante attesa lunga
                    for i in range(8):
                        if stop_flag and stop_flag.get('stop'):
                            print(f"🛑 Estrazione fermata per {url} durante attesa caricamento")
                            await browser.close()
                            return {"success": False, "error": "Estrazione fermata dall'utente"}
                        await page.wait_for_timeout(1000)
                else:
                    # CHECKPOINT durante attesa breve
                    for i in range(3):
                        if stop_flag and stop_flag.get('stop'):
                            print(f"🛑 Estrazione fermata per {url} durante attesa caricamento")
                            await browser.close()
                            return {"success": False, "error": "Estrazione fermata dall'utente"}
                        await page.wait_for_timeout(1000)
                
                # Verifica che la pagina si sia caricata correttamente
                try:
                    page_title = await page.title()
                    page_url = page.url
                    
                    if not page_title or page_title == "about:blank" or page_url == "about:blank":
                        return {"success": False, "error": "Pagina non caricata"}
                    
                    if page_url == "about:blank" or not page_url:
                        return {"success": False, "error": "Navigazione fallita - pagina non caricata"}
                    
                    if "error" in page_title.lower() or "not found" in page_title.lower():
                        return {"success": False, "error": "Pagina di errore"}
                    
                    page_content = await page.text_content('body')
                    if not page_content or len(page_content.strip()) < 100:
                        return {"success": False, "error": "Pagina vuota o quasi vuota"}
                        
                    # Per siti anti-bot forti, forza il caricamento completo
                    if is_strong_anti_bot:
                        try:
                            # CHECKPOINT durante scroll
                            if stop_flag and stop_flag.get('stop'):
                                print(f"🛑 Estrazione fermata per {url} durante scroll")
                                await browser.close()
                                return {"success": False, "error": "Estrazione fermata dall'utente"}
                            await page.wait_for_timeout(2000)
                            
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            
                            if stop_flag and stop_flag.get('stop'):
                                print(f"🛑 Estrazione fermata per {url} durante scroll")
                                await browser.close()
                                return {"success": False, "error": "Estrazione fermata dall'utente"}
                            await page.wait_for_timeout(1000)
                            
                            await page.evaluate("window.scrollTo(0, 0)")
                            
                            if stop_flag and stop_flag.get('stop'):
                                print(f"🛑 Estrazione fermata per {url} durante scroll")
                                await browser.close()
                                return {"success": False, "error": "Estrazione fermata dall'utente"}
                            await page.wait_for_timeout(1000)
                            
                            page_content = await page.text_content('body')
                        except Exception as e:
                            pass
                    
                    # Gestione popup e overlay per siti anti-bot
                    if is_strong_anti_bot:
                        try:
                            popup_selectors = [
                                'button[aria-label*="chiudi"]',
                                'button[aria-label*="close"]',
                                '.close',
                                '.popup-close',
                                '[data-dismiss="modal"]',
                                '.modal-close',
                                '.overlay-close'
                            ]
                            
                            for selector in popup_selectors:
                                try:
                                    elements = await page.query_selector_all(selector)
                                    for element in elements:
                                        if await element.is_visible():
                                            await element.click()
                                            await page.wait_for_timeout(500)
                                except Exception as e:
                                    continue
                            
                            await page.wait_for_timeout(1000)
                            
                        except Exception as e:
                            pass
                        
                except Exception as e:
                    return {"success": False, "error": f"Errore verifica pagina: {e}"}
                
                # Gestione banner cookie e popup
                try:
                    await page.click("button:has-text('ACCETTA')", timeout=3000)
                except:
                    try:
                        await page.click("button:has-text('OK')", timeout=3000)
                    except:
                        try:
                            await page.click("button:has-text('Accept')", timeout=3000)
                        except:
                            try:
                                await page.click("button:has-text('Accetta tutti')", timeout=3000)
                            except:
                                pass
                
                try:
                    await page.click("button:has-text('Chiudi')", timeout=3000)
                except:
                    try:
                        await page.click("[class*='close']", timeout=3000)
                    except:
                        pass
                
                # Attesa standard per tutti i siti (modalità normale)
                # CHECKPOINT durante attesa standard
                for i in range(15):
                    if stop_flag and stop_flag.get('stop'):
                        print(f"🛑 Estrazione fermata per {url} durante attesa standard")
                        await browser.close()
                        return {"success": False, "error": "Estrazione fermata dall'utente"}
                    await page.wait_for_timeout(1000)
                
                try:
                    title = await page.title()
                    if "just a moment" in title.lower() or "verify" in title.lower() or "non trovata" in title.lower() or "qualcosa blocca" in title.lower():
                        await page.wait_for_timeout(15000)
                        title = await page.title()
                except Exception as e:
                    return {"success": False, "error": "Errore verifica titolo pagina"}
                
                # Simula comportamento umano: scroll e movimenti
                if needs_visible_browser:
                    try:
                        await page.evaluate("window.scrollTo(0, 300)")
                        await page.wait_for_timeout(1000)
                        await page.evaluate("window.scrollTo(0, 600)")
                        await page.wait_for_timeout(1000)
                        await page.evaluate("window.scrollTo(0, 0)")
                    except Exception as e:
                        pass
                
                # Verifica che la pagina si sia caricata correttamente
                try:
                    current_url = page.url
                    title = await page.title()
                    
                    if current_url == "about:blank" or not title or title == "about:blank":
                        return {"success": False, "error": "Pagina non caricata - about:blank"}
                        
                except Exception as e:
                    return {"success": False, "error": f"Errore verifica pagina: {e}"}
                
                # Estrai dominio per database selettori
                domain = self._extract_domain(url)
                print(f"🔍 DOMINIO ESTRATTO: {domain}")
                
                # PRIMA TENTATIVO: Usa selettori salvati nel database
                print(f"🔍 Ricerca selettori per {domain}")
                print(f"🎯 CERCO SELEttori nel database per dominio: {domain}")
                saved_selectors = await self.selector_db.get_quality_selectors(domain, min_quality=100)
                print(f"📊 SELEttori trovati nel database: {len(saved_selectors)}")
                
                if saved_selectors:
                    print(f"✅ USO SELEttori dal database invece di hardcodati!")
                    print("🧪 Test selettori salvati")
                    print(f"🔍 PRIMO SELEttore: {saved_selectors[0]}")
                    best_selector = await self._test_saved_selectors(page, saved_selectors)
                    if best_selector:
                        print(f"🎯 MIGLIOR SELEttore dal database: {best_selector}")
                        print("✅ Selettore migliore trovato")
                        containers = await page.query_selector_all(best_selector.get('product_container'))
                        if containers:
                            print(f"📦 CONTENITORI TROVATI con selettore database: {len(containers)}")
                            extracted_content = []
                            for i, container in enumerate(containers[:30]):
                                try:
                                    text = await container.inner_text()
                                    if text and text.strip() and len(text) > 20:
                                        extracted_content.append(f"---ITEM---\n{text.strip()}")
                                except Exception as e:
                                    continue
                            
                            if extracted_content:
                                await browser.close()
                                
                                content_text = "\n\n".join(extracted_content[:25])
                                
                                # 🔍 LOG COMPLETO: Mostra esattamente cosa viene inviato all'AI
                                print(f"\n🚀 === CONTENUTO INVIATO ALL'AI (SELEttore DATABASE) ===")
                                print(f"📏 Lunghezza contenuto: {len(content_text)} caratteri")
                                print(f"🔤 Primi 500 caratteri:")
                                print(f"'{content_text[:500]}...'")
                                print(f"🔤 Ultimi 500 caratteri:")
                                print(f"...'{content_text[-500:]}'")
                                print(f"🚀 === FINE CONTENUTO AI ===\n")
                                
                                products = await self._ai_parse_products(content_text, url, stop_flag)
                                
                                if products:
                                    
                                    # Validazione e pulizia prodotti
                                    validated_products = []
                                    for i, product in enumerate(products):
                                        # Validazione base del prodotto
                                        if product.get('name') and product.get('price'):
                                            validated_products.append(product)
                                    
                                    print(f"✅ Validazione completata: {len(validated_products)} prodotti validi")
                                    
                                    print(f"🤖 PRODOTTI ESTRATTI con selettore database: {len(validated_products)}")
                                    
                                    # Aggiorna qualità selettore
                                    await self.selector_db.update_selector_quality(
                                        selector_id=best_selector.get('id'),
                                        success=True,
                                        products_found=len(validated_products)
                                    )
                                    
                                    print("✅ Risultati salvati con successo")
                                    print(f"✅ Estrazione completata: {len(validated_products)} prodotti")
                                    
                                    # 🕐 CALCOLA DURATA SCRAPING
                                    end_time = datetime.now()
                                    duration_ms = (end_time - self.start_time).total_seconds() * 1000
                                    duration_str = f"{duration_ms:.0f}ms" if duration_ms < 1000 else f"{duration_ms/1000:.1f}s"
                                    
                                    print(f"⏰ FINE SCRAPING: {end_time.isoformat()}")
                                    print(f"⏱️ DURATA TOTALE: {duration_str}")
                                    
                                    return {
                                        "success": True,
                                        "products": validated_products,
                                        "total_found": len(validated_products),
                                        "url": url,
                                        "extraction_method": "saved_selectors",
                                        "container_selector": best_selector.get('product_container'),
                                        "containers_found": len(containers),
                                        "timestamp": datetime.now().isoformat(),
                                        "start_time": self.start_time.isoformat(),
                                        "end_time": end_time.isoformat(),
                                        "duration": duration_str
                                    }
                                else:
                                    print("❌ Estrazione fallita - AI non ha trovato prodotti")
                                    return {"success": False, "error": "AI non ha trovato prodotti"}
                                
                            # Aggiorna qualità selettore
                            await self.selector_db.update_selector_quality(
                                selector_id=best_selector.get('id'),
                                success=True,
                                products_found=len(products)
                            )
                            
                            return {
                                "success": True,
                                "products": products,
                                "total_found": len(products),
                                "url": url,
                                "extraction_method": "saved_selectors",
                                "container_selector": best_selector.get('product_container'),
                                "containers_found": len(containers),
                                "timestamp": datetime.now().isoformat()
                            }
                else:
                    print(f"⚠️ NESSUN SELEttore specifico nel database per {domain}, uso selettori universali...")
                
                # PROVA SECONDA: Selettori universali dal database
                print(f"🌍 CERCO SELEttori universali nel database...")
                universal_selectors = await self.selector_db.get_quality_selectors('*', min_quality=100)
                
                if universal_selectors:
                    print(f"✅ TROVATI {len(universal_selectors)} selettori universali dal database!")
                    best_selector = await self._test_saved_selectors(page, universal_selectors)
                    if best_selector:
                        print(f"🎯 MIGLIOR SELEttore universale: {best_selector}")
                        containers = await page.query_selector_all(best_selector.get('product_container'))
                        if containers:
                            print(f"📦 CONTENITORI TROVATI con selettori universali: {len(containers)}")
                            extracted_content = []
                            for i, container in enumerate(containers[:30]):
                                try:
                                    text = await container.inner_text()
                                    if text and text.strip() and len(text) > 20:
                                        extracted_content.append(f"---ITEM---\n{text.strip()}")
                                except Exception as e:
                                    continue
                            
                            if extracted_content:
    
                                await browser.close()
                                
                                print("🔄 Preparazione contenuto universale per AI...")
                                content_text = "\n\n".join(extracted_content[:25])
                                
                                print("🔄 Invio contenuto universale all'AI...")
                                products = await self._ai_parse_products(content_text, url, stop_flag)
                                
                                if products:
                                    print(f"✅ Risposta AI universale: {len(products)} prodotti")
                                    print("🔄 Validazione prodotti universali...")
                                    
                                    # Validazione e pulizia prodotti
                                    validated_products = []
                                    for i, product in enumerate(products):
                                        # Validazione base del prodotto
                                        if product.get('name') and product.get('price'):
                                            validated_products.append(product)
                                    
                                    print(f"✅ Validazione universale completata: {len(validated_products)} prodotti")
                                    
                                    print(f"🤖 PRODOTTI ESTRATTI con selettore universale: {len(validated_products)}")
                                    
                                    # Aggiorna qualità selettore
                                    await self.selector_db.update_selector_quality(
                                        selector_id=best_selector.get('id'),
                                        success=True,
                                        products_found=len(validated_products)
                                    )
                                    
                                    print("✅ Risultati universali salvati")
                                    print(f"✅ Estrazione completata: {len(validated_products)} prodotti")
                                    
                                    return {
                                        "success": True,
                                        "products": validated_products,
                                        "total_found": len(validated_products),
                                        "url": url,
                                        "extraction_method": "universal_selectors",
                                        "container_selector": best_selector.get('product_container'),
                                        "containers_found": len(containers),
                                        "timestamp": datetime.now().isoformat()
                                    }
                                else:
                                    print("❌ Estrazione universale fallita - AI non ha trovato prodotti")
                                    
                                    # 🚀 FALLBACK INTELLIGENTE: AI analizza HTML per suggerire selettori
                                    print("🤖 ATTIVO FALLBACK INTELLIGENTE: AI analizza HTML per selettori...")
                                    
                                    try:
                                        # Estrai HTML per analisi AI
                                        html_content = await page.content()
                                        
                                        # AI analizza HTML e suggerisce selettori
                                        suggested_selectors = await self._ai_analyze_html_for_selectors(html_content, url)
                                        
                                        if suggested_selectors:
                                            print(f"✅ AI ha suggerito {len(suggested_selectors)} selettori per fallback")
                                            
                                            # Testa i selettori suggeriti dall'AI
                                            working_selectors = await self._test_ai_suggested_selectors(page, suggested_selectors)
                                            
                                            if working_selectors:
                                                print(f"✅ {len(working_selectors)} selettori AI funzionano per fallback!")
                                                
                                                # Estrai prodotti usando i selettori AI testati
                                                fallback_result = await self._extract_with_ai_selectors(page, working_selectors, url)
                                                
                                                if fallback_result.get('success'):
                                                    print("🎯 FALLBACK INTELLIGENTE COMPLETATO CON SUCCESSO!")
                                                    await browser.close()
                                                    return fallback_result
                                                else:
                                                    print("❌ Fallback intelligente non ha estratto prodotti")
                                            else:
                                                print("❌ Nessun selettore AI funziona per fallback")
                                        else:
                                            print("❌ AI non ha suggerito selettori per fallback")
                                    except Exception as e:
                                        print(f"⚠️ Errore fallback intelligente: {e}")
                                    
                                    return {"success": False, "error": "AI non ha trovato prodotti universali"}
                                
                                # Aggiorna qualità selettore
                                await self.selector_db.update_selector_quality(
                                    selector_id=best_selector.get('id'),
                                    success=True,
                                    products_found=len(products)
                                )
                                
                                return {
                                    "success": True,
                                    "products": products,
                                    "total_found": len(products),
                                    "url": url,
                                    "extraction_method": "universal_selectors",
                                    "container_selector": best_selector.get('product_container'),
                                    "containers_found": len(containers),
                                    "timestamp": datetime.now().isoformat()
                                }
                            else:
                                print(f"❌ NESSUN SELEttore trovato nel database (né specifico né universale)")
                                print(f"💡 SUGGERIMENTO: Inizializza i selettori predefiniti con: python init_selectors.py")
                            
                            # FALLBACK FINALE: AI parsing diretto + Auto-apprendimento + RIUTILIZZO IMMEDIATO
                            print(f"🤖 FALLBACK: Uso AI parsing diretto della pagina...")
                            
                            # Inizializza extracted_content se non è stata definita
                if 'extracted_content' not in locals():
                    extracted_content = []
                
                # 🚨 SE L'ESTRAZIONE FALLISCE, ATTIVA BROWSER VISIBILE PER CAPTCHA
                if not extracted_content:
                    # 🔍 CONTROLLO INTELLIGENTE: Verifica se c'è realmente un captcha prima di attivare browser visibile
                    print("🔍 Verifico se è realmente necessario un browser visibile...")
                    
                    # 🚨 CONTROLLO ANTI-LOOP: Se abbiamo già provato troppe volte, non riprovare
                    if hasattr(self, '_extraction_attempts'):
                        self._extraction_attempts += 1
                    else:
                        self._extraction_attempts = 1
                    
                    if self._extraction_attempts > 3:
                        print("🚨 TROPPI TENTATIVI DI ESTRAZIONE, EVITO LOOP INFINITO")
                        await browser.close()
                        return {
                            "success": False, 
                            "error": "Estrazione fallita dopo troppi tentativi - possibile problema con il sito o selettori",
                            "extraction_method": "failed_after_multiple_attempts",
                            "attempts": self._extraction_attempts
                        }
                    
                    print(f"🔄 Tentativo di estrazione #{self._extraction_attempts}")
                    
                    try:
                        # Controlla il contenuto attuale della pagina per rilevare captcha reali
                        current_page_content = await page.text_content('body') or ""
                        current_title = await page.title()
                        current_url = page.url
                        
                        # Indicatori di captcha reale
                        captcha_indicators = [
                            'checking your browser', 'cloudflare', 'captcha', 'verification',
                            'just a moment', 'please wait', 'security check', 'human verification',
                            'robot check', 'bot detection', 'challenge', 'verify you are human'
                        ]
                        
                        # Controlla se c'è realmente un captcha
                        has_real_captcha = any(indicator in current_page_content.lower() for indicator in captcha_indicators)
                        has_captcha_title = any(indicator in current_title.lower() for indicator in captcha_indicators)
                        
                        # 🔍 CONTROLLO AVANZATO: Verifica se la pagina ha contenuto utile nonostante i possibili indicatori
                        has_useful_content = (
                            len(current_page_content.strip()) > 1000 and
                            any(keyword in current_page_content.lower() for keyword in ['€', 'prezzo', 'price', 'product', 'prodotto', 'acquista', 'buy', 'mq', 'metri'])
                        )
                        
                        # Controlla se la pagina è bloccata o ha errori
                        is_page_blocked = (
                            current_url == "about:blank" or 
                            not current_title or 
                            current_title == "about:blank" or
                            "error" in current_title.lower() or
                            "not found" in current_title.lower() or
                            len(current_page_content.strip()) < 100
                        )
                        
                        # 🧠 LOGICA INTELLIGENTE: Determina se è realmente necessario un browser visibile
                        if has_real_captcha or has_captcha_title:
                            if has_useful_content:
                                print(f"🛡️ CAPTCHA rilevato MA pagina ha contenuto utile ({len(current_page_content)} caratteri)")
                                print("🔄 Provo estrazione AI diretta invece di browser visibile...")
                                needs_visible_browser = False
                                
                                # Estrazione AI diretta con contenuto utile
                                try:
                                    page_content = await page.content()
                                    print("🔄 Estrazione AI diretta con contenuto utile...")
                                    
                                    products = await self._ai_parse_products(page_content, url, stop_flag)
                                    
                                    if products and len(products) > 0:
                                        print(f"✅ Estrazione AI diretta riuscita: {len(products)} prodotti")
                                        await browser.close()
                                        return {
                                            "success": True,
                                            "products": products,
                                            "total_found": len(products),
                                            "url": url,
                                            "extraction_method": "ai_direct_with_captcha_content",
                                            "container_selector": "N/A",
                                            "containers_found": 0,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                    else:
                                        print("⚠️ Estrazione AI diretta non ha trovato prodotti, attivo browser visibile")
                                        needs_visible_browser = True
                                except Exception as ai_error:
                                    print(f"⚠️ Errore estrazione AI diretta: {ai_error}")
                                    needs_visible_browser = True
                            else:
                                print(f"🛡️ CAPTCHA REALE rilevato: {current_title}")
                                needs_visible_browser = True
                        elif is_page_blocked:
                            print(f"⚠️ Pagina bloccata o con errori: {current_title}")
                            print("🔄 Riprovo con modalità stealth invece di browser visibile...")
                            needs_visible_browser = False
                            
                            # Prova a ricaricare la pagina con modalità stealth
                            try:
                                await page.reload(wait_until='domcontentloaded', timeout=30000)
                                await page.wait_for_timeout(5000)
                                
                                # Verifica se ora la pagina si carica
                                new_content = await page.text_content('body') or ""
                                new_title = await page.title()
                                
                                if len(new_content.strip()) > 500 and new_title and new_title != "about:blank":
                                    print("✅ Pagina ora caricata correttamente in modalità stealth")
                                    # Riprova estrazione normale
                                    return await self._extract_single_attempt(url, headless, False, None, browser_config, stop_flag)
                                else:
                                    print("⚠️ Pagina ancora bloccata, attivo browser visibile come ultima risorsa")
                                    needs_visible_browser = True
                            except Exception as reload_error:
                                print(f"⚠️ Errore ricarica pagina: {reload_error}")
                                needs_visible_browser = True
                        else:
                            print("🔍 Nessun captcha reale rilevato, problema di estrazione selettori")
                            print("🔄 Provo estrazione AI diretta invece di browser visibile...")
                            needs_visible_browser = False
                            
                            # Estrazione AI diretta senza browser visibile
                            try:
                                page_content = await page.content()
                                print("🔄 Estrazione AI diretta in corso...")
                                
                                products = await self._ai_parse_products(page_content, url, stop_flag)
                                
                                if products and len(products) > 0:
                                    print(f"✅ Estrazione AI diretta riuscita: {len(products)} prodotti")
                                    await browser.close()
                                    return {
                                        "success": True,
                                        "products": products,
                                        "total_found": len(products),
                                        "url": url,
                                        "extraction_method": "ai_direct_fallback",
                                        "container_selector": "N/A",
                                        "containers_found": 0,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                else:
                                    print("⚠️ Estrazione AI diretta non ha trovato prodotti")
                                    needs_visible_browser = True
                            except Exception as ai_error:
                                print(f"⚠️ Errore estrazione AI diretta: {ai_error}")
                                needs_visible_browser = True
                        
                    except Exception as check_error:
                        print(f"⚠️ Errore controllo captcha: {check_error}")
                        needs_visible_browser = True
                    
                    # Solo se è realmente necessario, attiva browser visibile
                    if needs_visible_browser:
                        print("⚠️ Browser visibile necessario per gestire CAPTCHA o problema persistente...")
                        
                        # 🚨 RICREA BROWSER IN MODALITÀ VISIBILE
                        print("🔄 Ricreo browser in modalità visibile...")
                        try:
                            await browser.close()
                            
                            # Ricrea browser con modalità visibile
                            print("🔄 Ricreo browser in modalità visibile...")
                            try:
                                await browser.close()
                                
                                # 🖥️ CONFIGURAZIONE SPECIFICA PER WINDOWS
                                windows_args = [
                                    '--no-sandbox',
                                    '--disable-blink-features=AutomationControlled',
                                    '--window-size=1600,1000',
                                    '--window-position=0,0',
                                    '--start-maximized',
                                    '--disable-background-timer-throttling',
                                    '--disable-backgrounding-occluded-windows',
                                    '--disable-renderer-backgrounding',
                                    '--disable-features=TranslateUI',
                                    '--disable-ipc-flooding-protection',
                                    '--force-device-scale-factor=1',
                                    '--disable-hid-policy'
                                ]
                                
                                print("🖥️ Configurazione Windows per browser visibile...")
                                browser = await p.chromium.launch(
                                    headless=False,  # FORZA modalità visibile
                                    args=windows_args
                                )
                                
                                page = await browser.new_page()
                                await page.set_viewport_size({"width": 1600, "height": 1000})
                                
                                # 🔍 VERIFICA: Controlla che il browser sia realmente visibile
                                print("🔍 Verifico che il browser sia realmente visibile...")
                                try:
                                    # Prova a portare il browser in primo piano
                                    await page.bring_to_front()
                                    print("✅ Browser portato in primo piano")
                                    
                                    # Prova a fare un click per attivare la finestra
                                    await page.mouse.click(800, 500)
                                    print("✅ Click per attivare finestra browser")
                                    
                                    # Verifica che la finestra sia attiva
                                    await page.wait_for_timeout(2000)
                                    print("✅ Browser visibile attivato e pronto")
                                    
                                except Exception as visibility_error:
                                    print(f"⚠️ Errore attivazione browser visibile: {visibility_error}")
                                    print("🔄 Riprovo con configurazione alternativa...")
                                    
                                    # Prova configurazione alternativa
                                    try:
                                        await browser.close()
                                        browser = await p.chromium.launch(
                                            headless=False,
                                            args=[
                                                '--no-sandbox',
                                                '--disable-blink-features=AutomationControlled',
                                                '--window-size=1600,1000',
                                                '--window-position=0,0',
                                                '--start-maximized',
                                                '--disable-background-timer-throttling',
                                                '--disable-backgrounding-occluded-windows',
                                                '--disable-renderer-backgrounding'
                                            ]
                                        )
                                        page = await browser.new_page()
                                        await page.set_viewport_size({"width": 1600, "height": 1000})
                                        print("✅ Browser visibile ricreato con configurazione alternativa")
                                    except Exception as alt_error:
                                        print(f"❌ Errore configurazione alternativa: {alt_error}")
                                
                                # Ricarica la pagina
                                print("🔄 Ricarico pagina con browser visibile...")
                                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                                await page.wait_for_timeout(5000)
                                
                                print("✅ Browser visibile ricreato e pagina ricaricata")
                                
                            except Exception as browser_error:
                                print(f"⚠️ Errore ricreazione browser visibile: {browser_error}")
                        except Exception as browser_error:
                            print(f"⚠️ Errore ricreazione browser visibile: {browser_error}")
                    else:
                        print("✅ Browser visibile non necessario, continuo con estrazione normale")
                        # Continua con il flusso normale senza attivare browser visibile
                

                
                # Aggiorna progresso: Inizio fallback AI
                print("🔄 Fallback AI parsing iniziato")
                
                # Estrazione diretta con AI parsing
                try:
                    page_content = await page.content()
                    print("🔄 Contenuto pagina estratto")
                    
                    # NUOVO: Sistema di auto-apprendimento generico
                    print("🔄 Avvio auto-apprendimento selettori")
                    learned_selectors = await self._ai_learn_selectors(page, page_content, url)
                    
                    if learned_selectors:
                        print(f"🧠 AI ha imparato {len(learned_selectors)} nuovi selettori per {domain}")
                    
                        
                        # 🚀 NUOVO: RIUTILIZZO IMMEDIATO dei selettori appresi!
                        print(f"🔄 RIUTILIZZO IMMEDIATO dei selettori appresi...")
                    
                        best_learned_selector = learned_selectors[0]  # Prendi il migliore
                        
                        try:
                            # Testa immediatamente il selettore appreso
                            selector = best_learned_selector['selectors']['product_container']
                            print(f"🧪 Testo selettore appreso: {selector}")
                            
                            containers = await page.query_selector_all(selector)
                            if containers and len(containers) > 0:
                                print(f"📦 CONTENITORI TROVATI con selettore appreso: {len(containers)}")
                                
                                # Estrai contenuto dai contenitori
                                extracted_content = []
                                for i, container in enumerate(containers[:30]):  # Limita a 30 per performance
                                    try:
                                        text = await container.inner_text()
                                        if text and text.strip() and len(text) > 20:
                                            extracted_content.append(f"---ITEM---\n{text.strip()}")
                                    except Exception as e:
                                        continue
                                
                                if extracted_content:
                                    print(f"📝 CONTENUTO ESTRATTO: {len(extracted_content)} elementi")
                                    content_text = "\n\n".join(extracted_content[:25])
                                    
                        
                                    
                                    if products:
                                        print(f"🤖 PRODOTTI ESTRATTI con selettore appreso: {len(products)}")
                                        
                                        # Salva selettori appresi automaticamente
                                        for selector_data in learned_selectors:
                                            try:
                                                await self.selector_db.save_selectors(
                                                    domain=domain,
                                                    selectors=selector_data['selectors'],
                                                    approved=True,  # Auto-approva se AI ha trovato prodotti
                                                    products_found=selector_data['products_found'],
                                                    quality_score=selector_data.get('quality_score', 500),
                                                    success_rate=0.8  # Iniziale ottimistico
                                                )
                                                print(f"💾 Salvato selettore auto-appreso: {selector_data['selectors']['product_container']}")
                                            except Exception as e:
                                                print(f"⚠️ Errore salvataggio selettore auto-appreso: {e}")
                                        
                                        await browser.close()
                                        
                                        return {
                                            "success": True,
                                            "products": products,
                                            "total_found": len(products),
                                            "url": url,
                                            "extraction_method": "learned_selectors_reused",
                                            "container_selector": selector,
                                            "containers_found": len(containers),
                                            "timestamp": datetime.now().isoformat()
                                        }
                                    
                        except Exception as e:
                            print(f"⚠️ Errore riutilizzo selettore appreso: {e}")
                    
                    # Se il riutilizzo fallisce, salva comunque i selettori e usa AI parsing diretto
                    if learned_selectors:
                        for selector_data in learned_selectors:
                            try:
                                await self.selector_db.save_selectors(
                                    domain=domain,
                                    selectors=selector_data['selectors'],
                                    approved=True,
                                    products_found=selector_data['products_found'],
                                    quality_score=selector_data.get('quality_score', 500),
                                    success_rate=0.8
                                )
                                print(f"💾 Salvato selettore auto-appreso: {selector_data['selectors']['product_container']}")
                            except Exception as e:
                                print(f"⚠️ Errore salvataggio selettore auto-appreso: {e}")
                    
                    await browser.close()
                    
                    # Usa AI per estrarre prodotti direttamente dal HTML
                    print(f"🚀 Avvio elaborazione AI...")
                    
                    products = await self._ai_parse_products(page_content, url, stop_flag)
                    
                    if products:
                        print(f"✅ Risposta AI ricevuta: {len(products)} prodotti")
                        
                        # Validazione e pulizia prodotti
                        validated_products = []
                        for i, product in enumerate(products):
                            # Validazione base del prodotto
                            if product.get('name') and product.get('price'):
                                validated_products.append(product)
                        
                        print(f"✅ Validazione AI diretta completata: {len(validated_products)} prodotti")
                        print(f"🤖 PRODOTTI ESTRATTI con AI parsing diretto: {len(validated_products)}")
                        
                        print(f"✅ Estrazione completata: {len(validated_products)} prodotti")
                        return {
                            "success": True,
                            "products": validated_products,
                            "total_found": len(validated_products),
                            "url": url,
                            "extraction_method": "ai_direct_parsing",
                            "container_selector": "N/A",
                            "containers_found": 0,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        print(f"❌ Nessun prodotto estratto con AI parsing diretto")
                        print("❌ Estrazione fallita - nessun prodotto trovato")
                        return {"success": False, "error": "Nessun prodotto trovato"}
                        
                except Exception as e:
                    print(f"❌ Errore AI parsing diretto: {e}")
                    return {"success": False, "error": f"Errore AI parsing: {e}"}
                

                
                if not best_selector:
                    try:
                        content = await page.content()
                        products = await self._ai_parse_products(content, url, stop_flag)
                        
                        if products:
                            await browser.close()
                            return {
                                'success': True,
                                'products': products,
                                'source': 'AI Direct',
                                'total_found': len(products)
                            }
                        else:
                            await browser.close()
                            return {"success": False, "error": "AI non ha trovato prodotti"}
                            
                    except Exception as e:
                        await browser.close()
                        return {"success": False, "error": f"Errore AI parsing: {e}"}
                
                # SALVA SELEttori se funzionano bene
                if best_selector and best_count >= 3:
                    try:
                        selectors_to_save = {
                            'product_container': best_selector,
                            'title': best_selector,
                            'price': best_selector
                        }
                        
                        await self.selector_db.save_selectors(
                            domain=domain,
                            selectors=selectors_to_save,
                            approved=False,
                            products_found=best_count,
                            suggested_at=datetime.now()
                        )
                    except Exception as e:
                        pass
                
                # Estrai contenuto dai contenitori
                try:
                    containers = await page.query_selector_all(best_selector)
                    extracted_content = []
                    
                    if 'amazon' in url.lower():
                        if len(containers) > 200:
                            max_containers = 150
                        elif len(containers) > 100:
                            max_containers = 120
                        elif len(containers) > 50:
                            max_containers = 100
                        elif len(containers) > 20:
                            max_containers = 80
                        else:
                            max_containers = len(containers)
                    else:
                        if len(containers) > 100:
                            max_containers = 100
                        elif len(containers) > 50:
                            max_containers = 80
                        elif len(containers) > 20:
                            max_containers = 60
                        else:
                            max_containers = len(containers)
                        
                    if len(containers) > max_containers:
                        containers = containers[:max_containers]
                    
                    valid_containers = 0
                    for i, container in enumerate(containers):
                        try:
                            text = await container.inner_text()
                            if text and text.strip() and len(text) > 20:
                                cleaned_text = self._clean_extracted_text(text.strip())
                                if cleaned_text and len(cleaned_text) > 20:
                                    extracted_content.append(f"---ITEM---\n{cleaned_text}")
                                    valid_containers += 1
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    pass
                
                # Controlla se abbiamo estratto contenuto
                if not extracted_content:
                    try:
                        full_text = await page.inner_text("body")
                        if full_text and len(full_text) > 1000:
                            lines = full_text.split('\n')
                            product_chunks = []
                            current_product = []
                            
                            product_patterns = [
                                '€', '$', '£', '¥', '₹',
                                'stelle', 'stars', 'rating',
                                'acquista', 'buy', 'compra', 'add to cart',
                                'disponibile', 'available', 'in stock',
                                'recensione', 'review', 'opinioni'
                            ]
                            
                            for line in lines:
                                line = line.strip()
                                if not line:
                                    continue
                                    
                                if any(pattern in line for pattern in product_patterns) and len(line) > 20:
                                    if current_product:
                                        product_chunks.append("---ITEM---\n" + '\n'.join(current_product))
                                    current_product = [line]
                                elif '€' in line and current_product:
                                    current_product.append(line)
                                elif 'stelle' in line and current_product:
                                    current_product.append(line)
                                elif len(current_product) > 0 and len(current_product) < 10:
                                    current_product.append(line)
                                    
                            if current_product:
                                product_chunks.append("---ITEM---\n" + '\n'.join(current_product))
                                
                            max_chunks = 30 if len(lines) > 1000 else 20
                            extracted_content = product_chunks[:max_chunks] if product_chunks else [f"---ITEM---\n{full_text[:15000]}"]
                        else:
                            await browser.close()
                            return {"success": False, "error": "No product content extracted"}
                    except Exception as e:
                        await browser.close()
                        return {"success": False, "error": f"Fallback failed: {e}"}
                
                # NUOVO: Se abbiamo estratto pochi contenuti, prova estrazione più aggressiva
                if len(extracted_content) < 10 and best_selector:
                    print(f"⚠️ Pochi contenuti estratti ({len(extracted_content)}), attivo estrazione aggressiva...")
                    try:
                        # Prova a estrarre da più selettori contemporaneamente
                        aggressive_selectors = [
                            "div", "li", "article", "section", "main", "aside",
                            "[class*='content']", "[class*='main']", "[class*='primary']"
                        ]
                        
                        all_content = []
                        for selector in aggressive_selectors[:5]:  # Limita a 5 selettori per performance
                            try:
                                elements = await page.query_selector_all(selector)
                                if len(elements) > 0 and len(elements) <= 200:  # Limita elementi per performance
                                    for element in elements[:50]:  # Limita a 50 elementi per selettore
                                        try:
                                            text = await element.inner_text()
                                            if text and text.strip() and len(text) > 15:
                                                # Filtra contenuti che sembrano prodotti
                                                if any(pattern in text.lower() for pattern in ['€', 'prezzo', 'acquista', 'buy', 'product', 'prodotto']):
                                                    all_content.append(f"---ITEM---\n{text.strip()}")
                                        except:
                                            continue
                            except:
                                continue
                        
                        # Rimuovi duplicati e unisci con contenuto originale
                        unique_content = []
                        seen_content = set()
                        for content in all_content + extracted_content:
                            content_key = content[:100].lower()  # Usa primi 100 caratteri come chiave
                            if content_key not in seen_content:
                                seen_content.add(content_key)
                                unique_content.append(content)
                        
                        if len(unique_content) > len(extracted_content):
                            print(f"✅ Estrazione aggressiva ha trovato {len(unique_content)} contenuti vs {len(extracted_content)} originali")
                            extracted_content = unique_content
                        else:
                            print(f"⚠️ Estrazione aggressiva non ha migliorato i risultati")
                            
                    except Exception as e:
                        print(f"⚠️ Errore estrazione aggressiva: {e}")
                
                await browser.close()
                
                # AI parsing del contenuto estratto
                if extracted_content and len(extracted_content[0]) > 1000:
                    giant_block = extracted_content[0]
                    lines = giant_block.split('\n')
                    chunks = []
                    current_chunk = []
                    
                    for line in lines:
                        current_chunk.append(line)
                        if 'Aggiungi' in line and len(current_chunk) >= 3:
                            chunk_text = '\n'.join(current_chunk)
                            
                            if 'immobil' in url.lower() or 'casa' in url.lower() or 'vendita' in url.lower():
                                immobile_keywords = ['€', 'mq', 'vendita', 'affitto', 'bilocale', 'trilocale', 'casa', 'appartamento', 'villa', 'via ', 'viale ', 'piazza ']
                                if any(keyword in chunk_text.lower() for keyword in immobile_keywords):
                                    chunks.append("---ITEM---\n" + chunk_text)
                                    current_chunk = []
                            else:
                                ecommerce_keywords = ['€', 'kg', 'g ', ' h ', 'prezzo', 'sconto', 'offerta']
                                if any(keyword in chunk_text.lower() for keyword in ecommerce_keywords):
                                    chunks.append("---ITEM---\n" + chunk_text)
                                    current_chunk = []
                    
                    if chunks:
                        total_chars = 0
                        selected_chunks = []
                        for chunk in chunks:
                            if total_chars + len(chunk) < 2000:
                                selected_chunks.append(chunk)
                                total_chars += len(chunk)
                            else:
                                break
                        
                        content_text = "\n\n".join(selected_chunks)
                    else:
                        small_blocks = [block for block in extracted_content[4:] if len(block) < 200]
                        unique_blocks = []
                        seen_content = set()
                        for block in small_blocks:
                            key = '\n'.join(block.split('\n')[:3])
                            if key not in seen_content:
                                seen_content.add(key)
                                unique_blocks.append(block)
                        
                        largest_block = max(extracted_content, key=len) if extracted_content else ""
                        unique_content = "\n\n".join(unique_blocks[:20])
                        
                        if len(largest_block) > len(unique_content) * 1.5:
                            content_text = largest_block
                            use_largest_first = True
                        else:
                            content_text = unique_content
                            use_largest_first = False
                else:
                    content_text = "\n\n".join(extracted_content[:25])
                
                products = await self._ai_parse_products(content_text, url, stop_flag)
                
                # FALLBACK UNIVERSALE
                if 'use_largest_first' in locals() and use_largest_first and len(products) < 5:
                    fallback_content = unique_content if 'unique_content' in locals() else content_text
                    if len(fallback_content) != len(content_text) and len(fallback_content) > 100:
                        fallback_products = await self._ai_parse_products(fallback_content, url, stop_flag)
                        if len(fallback_products) > len(products):
                            products = fallback_products
                
                result = {
                    "success": True,
                    "products": products,
                    "total_found": len(products),
                    "url": url,
                    "extraction_method": "fast_ai_surgical",
                    "container_selector": best_selector,
                    "containers_found": best_count,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Aggiorna statistiche selettori se l'estrazione ha avuto successo
                if len(products) > 0:
                    try:
                        await self.selector_db.update_success_rate(domain, True, len(products))
                    except Exception as e:
                        pass
                
                return result
                
        except Exception as e:
            # 🕐 CALCOLA DURATA FINALE (errore generale)
            end_time = datetime.now()
            duration_ms = (end_time - self.start_time).total_seconds() * 1000
            duration_str = f"{duration_ms:.0f}ms" if duration_ms < 1000 else f"{duration_ms/1000:.1f}s"
            
            print(f"⏰ FINE SCRAPING (errore): {end_time.isoformat()}")
            print(f"⏱️ DURATA TOTALE: {duration_str}")
            
            if browser:
                try:
                    await browser.close()
                except:
                    pass
            return {
                "success": False, 
                "error": str(e),
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": duration_str
            }
    






    def _get_browser_args(self, mode: str, is_strong_anti_bot: bool, user_agent: str) -> List[str]:
        """Genera argomenti browser consolidati in base alla modalità"""
        args = BROWSER_ARGS_BASE.copy()
        
        if mode == 'visible':
            args.extend(BROWSER_ARGS_VISIBLE)
            if is_strong_anti_bot:
                args.extend([
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-extensions-except=',
                    '--disable-plugins-discovery',
                    '--no-first-run',
                    '--no-default-browser-check'
                ])
        elif mode == 'stealth':
            args.extend(BROWSER_ARGS_STEALTH)
        # 'normal' mode usa solo BROWSER_ARGS_BASE
        
        args.append(f'--user-agent={user_agent}')
        return args
    
    def _extract_domain(self, url: str) -> str:
        """Estrae il dominio da un URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Rimuovi www. se presente
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            print(f"⚠️ Errore estrazione dominio: {e}")
            return "unknown"
    

    
    def _detect_real_estate_site_from_content(self, content_text: str) -> bool:
        """Rileva automaticamente se è un sito immobiliare dal contenuto (multilingua)"""
        try:
            content_lower = content_text.lower()
            
            # 🔍 LOG DETECTION: Mostra cosa viene analizzato
            print(f"🔍 Analisi contenuto per detection real estate...")
            
            # Indicatori FORTI per siti immobiliari (più specifici)
            strong_real_estate_indicators = [
                # Italiano - molto specifici
                'bilocale', 'trilocale', 'quadrilocale', 'monolocale',
                'appartamento', 'villa', 'casa indipendente', 'attico',
                'mansarda', 'loft', 'rustico', 'casale', 'masseria',
                'vendita immobili', 'affitto immobili', 'agenzia immobiliare',
                'annunci immobiliari', 'cerca casa', 'trova casa',
                
                # Inglese - molto specifici
                'studio apartment', 'one bedroom', 'two bedroom', 'three bedroom',
                'penthouse', 'townhouse', 'duplex', 'condo', 'condominium',
                'real estate agency', 'property for sale', 'property for rent',
                'house hunting', 'find home', 'real estate listings',
                
                # Francese - molto specifici
                'studio', 'deux pièces', 'trois pièces', 'appartement',
                'maison individuelle', 'maison de ville', 'loft',
                'agence immobilière', 'bien immobilier', 'achat maison',
                
                # Tedesco - molto specifici
                'ein zimmer', 'zwei zimmer', 'drei zimmer', 'wohnung',
                'einfamilienhaus', 'reihenhaus', 'loft', 'penthouse',
                'immobilienbüro', 'immobilienangebote', 'haus kaufen',
                
                # Spagnolo - molto specifici
                'estudio', 'dos habitaciones', 'tres habitaciones',
                'apartamento', 'casa individual', 'casa adosada',
                'agencia inmobiliaria', 'inmuebles en venta', 'comprar casa'
            ]
            
            # Indicatori DEBOLI per siti immobiliari (generici, da usare con cautela)
            weak_real_estate_indicators = [
                'mq', 'metri quadri', 'bagno', 'bagni', 'camera', 'camere',
                'piano', 'vendita', 'affitto', 'immobile', 'proprietà', 'terreno',
                'sqm', 'square meters', 'bathroom', 'bathrooms', 'bedroom', 'bedrooms',
                'floor', 'for sale', 'for rent', 'property', 'land', 'acres', 'sq ft'
            ]
            
            # Conta indicatori forti (peso maggiore)
            strong_score = sum(1 for indicator in strong_real_estate_indicators if indicator in content_lower)
            
            # Conta indicatori deboli (peso minore)
            weak_score = sum(1 for indicator in weak_real_estate_indicators if indicator in content_lower)
            
            # Calcola punteggio totale (indicator forti valgono di più)
            total_score = (strong_score * 3) + weak_score
            
            # 🔍 LOG DETECTION: Mostra punteggi
            print(f"🔍 Punteggio indicatori forti: {strong_score}")
            print(f"🔍 Punteggio indicatori deboli: {weak_score}")
            print(f"🔍 Punteggio totale: {total_score}")
            
            # Soglia più alta per evitare falsi positivi
            is_real_estate = total_score >= 8
            
            print(f"🔍 Rilevato come real estate: {is_real_estate}")
            
            return is_real_estate
            
        except Exception as e:
            print(f"⚠️ Errore detection sito immobiliare: {e}")
            return False
    
    def _detect_food_site_from_content(self, content_text: str) -> bool:
        """Rileva automaticamente se è un sito alimentare dal contenuto"""
        try:
            content_lower = content_text.lower()
            
            # Indicatori universali per siti alimentari (multilingua)
            food_indicators = [
                # Italiano
                'kg', 'g ', 'litri', 'ml', 'prezzo al kg', 'prezzo al litro',
                'alimentari', 'supermercato', 'spesa', 'cibo', 'frutta', 'verdura',
                'carne', 'pesce', 'latte', 'formaggio', 'pane', 'pasta',
                
                # Inglese
                'kg', 'g ', 'liters', 'ml', 'price per kg', 'price per liter',
                'grocery', 'supermarket', 'food', 'fresh', 'meat', 'fish',
                'milk', 'cheese', 'bread', 'pasta', 'vegetables', 'fruits',
                
                # Francese
                'kg', 'g ', 'litres', 'ml', 'prix au kg', 'prix au litre',
                'alimentation', 'supermarché', 'nourriture', 'frais', 'viande',
                
                # Tedesco
                'kg', 'g ', 'liter', 'ml', 'preis pro kg', 'preis pro liter',
                'lebensmittel', 'supermarkt', 'nahrung', 'frisch', 'fleisch'
            ]
            
            # Conta quanti indicatori alimentari sono presenti
            food_score = sum(1 for indicator in food_indicators if indicator in content_lower)
            
            # Se ci sono molti indicatori alimentari, è probabilmente un sito alimentare
            return food_score >= 3
            
        except Exception as e:
            print(f"⚠️ Errore detection sito alimentare: {e}")
            return False
    
    def _clean_extracted_text(self, text: str) -> str:
        """Pulisce il testo estratto da link lunghi e contenuto non necessario"""
        import re
        
        text = re.sub(r'https?://[^\s]{100,}', '[LINK]', text)
        text = re.sub(r'[?&][^=]{50,}=[^&\s]{50,}', '', text)
        text = re.sub(r'([A-Za-z0-9])\1{20,}', r'\1', text)
        
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if len(line.strip()) > 200:
                cleaned_lines.append(line[:200].strip() + "...")
            else:
                cleaned_lines.append(line.strip())
        
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    async def _test_saved_selectors(self, page, saved_selectors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Testa selettori salvati e restituisce il migliore"""
        try:
            # Ordina per qualità e success rate
            sorted_selectors = sorted(saved_selectors, 
                                    key=lambda x: (x.get('quality_score', 0), x.get('success_rate', 0)), 
                                    reverse=True)
            
            for selector_data in sorted_selectors:
                # Prova prima product_container
                if selector_data.get('product_container'):
                    selector = selector_data['product_container']
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0 and len(elements) <= 100:
                            test_text = await elements[0].inner_text()
                            if len(test_text) > 20:
                                return selector_data  # Ritorna tutto l'oggetto selettore
                    except Exception as e:
                        continue
                
                # Fallback su altri selettori
                for selector_type in ['title', 'price']:
                    if selector_data.get(selector_type):
                        selector = selector_data[selector_type]
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements and len(elements) > 0 and len(elements) <= 100:
                                test_text = await elements[0].inner_text()
                                if len(test_text) > 20:
                                    return selector_data
                        except Exception as e:
                            continue
            
            return None
            
        except Exception as e:
            return None
    
    async def _ai_parse_products(self, content_text: str, url: str = "", stop_flag: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Parse AI veloce del contenuto estratto con chunking intelligente"""
        try:
            # CHECKPOINT 4: Controlla se deve fermarsi prima dell'elaborazione AI
            if stop_flag and stop_flag.get('stop'):
                print(f"🛑 Elaborazione AI fermata per {url}")
                return []
                
            if len(content_text) > 15000:
                try:
                    products = await self._process_single_chunk(content_text, url, stop_flag)
                    
                    if products and len(products) >= 5:
                        return products
                    else:
                        raise Exception("Not enough products found")
                        
                except Exception as e:
                    # Fallback a chunk multipli
                    
                    if len(content_text) > 25000:
                        num_chunks = 6
                        chunk_size = len(content_text) // num_chunks
                    elif len(content_text) > 15000:
                        num_chunks = 4
                        chunk_size = len(content_text) // num_chunks
                    else:
                        num_chunks = 3
                        chunk_size = len(content_text) // num_chunks
                    
                    # Preparazione chunk
                    
                    chunks = []
                    for i in range(num_chunks):
                        start = i * chunk_size
                        end = start + chunk_size if i < num_chunks - 1 else len(content_text)
                        
                        if i < num_chunks - 1:
                            search_start = min(end, len(content_text) - 100)
                            search_end = min(end + 500, len(content_text))
                            
                            separators = ["---ITEM---", "---PRODUCT---", "---SEPARATOR---"]
                            found_separator = False
                            
                            for separator in separators:
                                next_separator = content_text.find(separator, search_start, search_end)
                                if next_separator != -1:
                                    end = next_separator + len(separator)
                                    found_separator = True
                                    break
                            
                            if not found_separator:
                                next_euro = content_text.find("€", search_start, search_end)
                                if next_euro != -1:
                                    line_end = content_text.find("\n", next_euro, search_end)
                                    if line_end != -1:
                                        end = line_end
                                    else:
                                        end = next_euro + 1
                        
                        chunk = content_text[start:end]
                        chunks.append(chunk)
                    
                    all_products = []
                    total_chunks = len(chunks)
                    
                    # Elaborazione chunk
                    
                    for i, chunk in enumerate(chunks, 1):
                        # CHECKPOINT 5: Controlla se deve fermarsi durante l'elaborazione chunk
                        if stop_flag and stop_flag.get('stop'):
                            print(f"🛑 Elaborazione chunk fermata per {url}")
                            return []
                            
                        try:
                            chunk_products = await self._process_single_chunk(chunk, url, stop_flag)
                            all_products.extend(chunk_products)
                        except Exception as chunk_error:
                            continue
                    
                    # Finalizzazione risultati
                    
                    unique_products = []
                    seen_names = set()
                    for product in all_products:
                        name = product.get('name', '').lower()
                        if name and name not in seen_names:
                            unique_products.append(product)
                            seen_names.add(name)
                    
                    # Completato
                    
                    return unique_products
            else:
                # Chunk singolo
                
                result = await self._process_single_chunk(content_text, url, stop_flag)
                
                return result
                
        except Exception as e:
            return []
    
    async def _process_single_chunk(self, content_text: str, url: str = "", stop_flag: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Processa un singolo chunk di contenuto"""
        try:
            content_lower = content_text.lower()
            
            # Detection automatica universale basata sul contenuto
            is_real_estate = self._detect_real_estate_site_from_content(content_text)
            
            # 🔍 LOG DETECTION: Mostra cosa viene rilevato
            print(f"\n🔍 === DETECTION AUTOMATICA SITO ===")
            print(f"📊 Rilevato come real estate: {is_real_estate}")
            print(f"🔍 Contenuto analizzato: {len(content_text)} caratteri")
            print(f"🔤 Primi 200 caratteri: '{content_text[:200]}...'")
            print(f"🔍 === FINE DETECTION ===\n")
            
            if is_real_estate:
                import re
                price_patterns = [
                    r'(\d{1,3}(?:\.\d{3})*)\s*€',
                    r'€\s*(\d{1,3}(?:\.\d{3})*)',
                    r'(\d{1,3}(?:,\d{3})*)\s*€',
                    r'€\s*(\d{1,3}(?:,\d{3})*)',
                ]
                
                all_prices = []
                for pattern in price_patterns:
                    matches = re.findall(pattern, content_text)
                    all_prices.extend(matches)
                
                unique_prices = list(set(all_prices))
                
                content_chunks = []
                lines = content_text.split('\n')
                current_chunk = []
                
                for line in lines:
                    current_chunk.append(line)
                    if '€' in line and 'mq' in line and len('\n'.join(current_chunk)) > 200:
                        content_chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                
                if current_chunk:
                    content_chunks.append('\n'.join(current_chunk))
                
                if len(content_chunks) > 1:
                    main_content = '\n'.join(content_chunks)
                else:
                    main_content = content_text[:15000]
                
                prompt = f"""ANALYZE this real estate content and EXTRACT ALL PROPERTIES with DETAILED CHARACTERISTICS:

{main_content}

INSTRUCTIONS:
1. Count how many different prices you see (€249.000, €138.000, €169.000, etc.)
2. For EACH price, create ONE property entry with ALL available details
3. Extract these fields for each property:
   - name: Property name/description
   - price: Exact price in € format
   - address: Full address if available
   - sqm: Square meters (mq)
   - rooms: Number of rooms (bilocale, trilocale, etc.)
   - bathrooms: Number of bathrooms
   - floor: Floor number if mentioned
   - type: Property type (appartamento, villa, casa, etc.)
   - condition: Condition if mentioned (nuovo, ristrutturato, etc.)
   - features: Any special features (giardino, terrazza, cantina, etc.)

4. Look for patterns like:
   - "Bilocale 60mq" → rooms: "2", sqm: "60"
   - "Via Roma 15" → address: "Via Roma 15"
   - "2 bagni" → bathrooms: "2"
   - "3° piano" → floor: "3"

Return this JSON format with ALL properties and their characteristics:
{{"products": [{{"name": "Property Description", "price": "€XXX.XXX", "address": "Full Address", "sqm": "XX", "rooms": "X", "bathrooms": "X", "floor": "X", "type": "Property Type", "condition": "Condition", "features": "Special Features"}}]}}

CRITICAL: Extract as many properties as you can find. Count the prices and return that many properties with ALL available details."""
                
                # 🔍 LOG PROMPT: Mostra il prompt finale
                print(f"\n🚀 === PROMPT FINALE REAL ESTATE ===")
                print(f"📝 Prompt: {prompt[:500]}...")
                print(f"🚀 === FINE PROMPT ===\n")
            else:
                # Determina automaticamente se è un sito alimentare dal contenuto
                is_food_site = self._detect_food_site_from_content(content_text)
                
                if is_food_site:
                    price_kg_instruction = 'For "price_per_kg": include if the product shows "€X.XX/Kg" or "€X.XX / Kg". If it shows "0,00 €/Kg", use "Prezzo variabile".'
                else:
                    price_kg_instruction = 'For "price_per_kg": always use "0,00€" for non-food products (electronics, clothing, etc.).'
                
                main_content = content_text[:15000]
                
                prompt = f"""ANALYZE this e-commerce content and EXTRACT ALL REAL PRODUCTS with DETAILED CHARACTERISTICS:

{main_content}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. **ONLY extract products that have BOTH:**
   - A SPECIFIC product name (not generic categories)
   - A REAL price in € format (not placeholder prices)

2. **NEVER extract these items (they are NOT products):**
   - Navigation menu items or category names
   - Menu links or navigation elements
   - Items without specific product details
   - Items without real prices

3. **PRICE VALIDATION RULES:**
   - Price MUST be a real number like "€19,90" or "€1.499,90"
   - NEVER use placeholder prices like "€XX.XX" or "€0,00" unless it's actually free
   - If you cannot find a real price, DO NOT extract that item as a product
   - Price must be visible and clearly associated with the product

4. **PRODUCT VALIDATION RULES:**
   - Product name must be specific (not just "Computer", "Smartphone", "Lavatrici")
   - Must have product details or specifications
   - Must NOT be just a category or menu item
   - Must have a real, visible price

5. **For EACH VALID product, extract:**
   - name: Full product name
   - price: Exact price in € format (ONLY if you can see a real price) DON'T USE PLACEHOLDER PRICES or Invented prices!
   - brand: Brand name if mentioned
   - model: Model/identifier if mentioned
   - weight: Weight if mentioned
   - price_per_kg: Price per kg if applicable
   - rating: Star rating if available
   - description: Product description
   - category: Product category
   - availability: Stock status
   - warranty: Warranty info
   - specs: Technical specifications

6. **Examples of what to EXTRACT:**
   ✅ Any product with a real name and real price
   ✅ "Samsung Display 6.9''" with price "€1.699,90"
   ✅ "iPhone 15 Pro 128GB" with price "€1.099,90"
   ✅ "Lattina Coca Cola 33cl" with price "€1,10"
   ✅ "Lavatrice Samsung 8kg" with price "€399,90" (if it's a real product, not menu)

7. **Examples of what to IGNORE:**
   ❌ "LAVATRICI CARICA FRONTALE" (just a menu category, no real price)
   ❌ "Computer" (generic category, no specific product)
   ❌ "Smartphone" (generic category, no specific product)
   ❌ Any menu navigation items without real prices

8. Look for patterns like:
- Product names with brands/models
- Prices in € format
- Product descriptions
- Technical specifications
- Weight information
- Rating stars

Return this JSON format with ONLY VALID PRODUCTS that have REAL PRICES:
{{"products": [{{"name": "Specific Product Name", "price": "€XX.XX", "brand": "Brand Name", "model": "Model Number", "weight": "Weight", "price_per_kg": "€X.XX/Kg", "rating": "X.X", "description": "Product description", "category": "Category", "availability": "In Stock", "warranty": "Warranty info", "specs": "Technical specs"}}]}}

FINAL CHECK: Before returning, verify that each product has a REAL name (not just a category) and a REAL price (not placeholder). If you cannot find a real price for an item, DO NOT include it in the results."""
                
                # 🔍 LOG PROMPT: Mostra il prompt finale
                print(f"\n🚀 === PROMPT FINALE E-COMMERCE ===")
                print(f"📝 Prompt: {prompt[:500]}...")
                print(f"🚀 === FINE PROMPT ===\n")

            response = await self.ai_analyzer._call_ai_with_fallback(prompt)
            
            if response and 'products' in response:
                products = response['products']
                return products
            else:
                return []
                
        except Exception as e:
            return []


    
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
    
    def _looks_like_product_content(self, text: str, url: str) -> bool:
        """Determina se il testo sembra contenuto di un prodotto"""
        try:
            text_lower = text.lower()
            
            # Indicatori comuni di prodotti
            product_indicators = [
                '€', '$', '£', 'prezzo', 'price', 'costo', 'cost',
                'acquista', 'buy', 'compra', 'add to cart', 'aggiungi',
                'stelle', 'stars', 'rating', 'recensioni', 'reviews',
                'disponibile', 'available', 'in stock', 'scorte',
                'spedizione', 'shipping', 'delivery', 'consegna'
            ]
            
            # Indicatori per immobili
            real_estate_indicators = [
                'mq', 'sqm', 'metri quadri', 'square meters',
                'bagno', 'bagni', 'bathroom', 'bathrooms',
                'camera', 'camere', 'bedroom', 'bedrooms',
                'piano', 'floor', 'via ', 'street', 'viale',
                'vendita', 'affitto', 'sale', 'rent',
                'bilocale', 'trilocale', 'quadrilocale'
            ]
            
            # Indicatori per e-commerce
            ecommerce_indicators = [
                'marca', 'brand', 'modello', 'model',
                'caratteristiche', 'features', 'specifiche', 'specs',
                'garanzia', 'warranty', 'assistenza', 'support',
                'kg', 'g', 'litri', 'ml', 'cm', 'mm'
            ]
            
            # Conta indicatori presenti
            product_score = sum(1 for indicator in product_indicators if indicator in text_lower)
            real_estate_score = sum(1 for indicator in real_estate_indicators if indicator in text_lower)
            ecommerce_score = sum(1 for indicator in ecommerce_indicators if indicator in text_lower)
            
            total_score = product_score + real_estate_score + ecommerce_score
            
            # Criteri standard per tutti i siti
            min_score = 2
            min_length = 30
            
            # Deve avere indicatori sufficienti e testo ragionevole
            return total_score >= min_score and len(text.strip()) > min_length and len(text.strip()) < 2000
            
        except:
            return False

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
                "model": "gpt-3.5-turbo",
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