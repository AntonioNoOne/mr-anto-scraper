"""Mixin con il flusso principale di estrazione singola pagina."""

import os
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright
from fast_ai_extractor_config import ANTI_BOT_SITES, STRONG_ANTI_BOT_SITES


class _ExtractionMixin:
    """Tentativo singolo di estrazione (browser, navigazione, orchestrazione)."""

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
                
                # 🚀 RENDER FIX: Forza headless=True su Render DOPO tutte le altre logiche
                if os.environ.get('RENDER'):
                    headless = True
                    print(f"🌐 RENDER FINAL FIX: Forzo headless=True dopo tutte le logiche")
                    # Su Render, disabilita completamente browser visibili
                    needs_visible_browser = False
                
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
                
                # PRIMA TENTATIVO: selettori salvati nel database (delegato al mixin)
                _db_result = await self._try_db_selectors(page, url, domain, browser, stop_flag)
                if _db_result is not None:
                    return _db_result

                
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
                return await self._fallback_ai_parsing(page, browser, url, domain, stop_flag)
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
