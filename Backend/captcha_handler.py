#!/usr/bin/env python3
"""
Captcha Handler - Gestione semplificata dei captcha
"""

import logging

logger = logging.getLogger(__name__)

class CaptchaHandler:
    """Gestore semplificato per i captcha"""
    
    def __init__(self):
        self.captcha_detected = False
        logger.info("🔐 Captcha Handler inizializzato")
    
    def detect_captcha(self, page_content: str) -> bool:
        """Rileva se una pagina contiene un captcha o protezione - VERSIONE MIGLIORATA"""
        # Indicatori di captcha FORTI (sicuramente un captcha)
        strong_captcha_indicators = [
            'captcha',
            'recaptcha',
            'verification',
            'human verification',
            'verify you are human',
            'robot check',
            'bot detection',
            'security check',
            'cloudflare',
            'checking your browser',
            'ddos protection',
            'rate limit',
            'access denied',
            'blocked',
            'challenge'
        ]
        
        # Indicatori DEBOLI (potrebbero essere falsi positivi)
        weak_captcha_indicators = [
            'please wait',
            'loading',
            'robot',
            'human',
            'security',
            'protection'
        ]
        
        content_lower = page_content.lower()
        
        # Conta indicatori forti e deboli
        strong_count = sum(1 for indicator in strong_captcha_indicators if indicator in content_lower)
        weak_count = sum(1 for indicator in weak_captcha_indicators if indicator in content_lower)
        
        # Logica di rilevamento migliorata
        if strong_count >= 2:
            # Se ci sono 2+ indicatori forti, è sicuramente un captcha
            self.captcha_detected = True
            logger.warning(f"🚨 CAPTCHA SICURO rilevato: {strong_count} indicatori forti")
            return True
        elif strong_count == 1 and weak_count >= 2:
            # Se c'è 1 indicatore forte + 2+ deboli, probabilmente è un captcha
            self.captcha_detected = True
            logger.warning(f"🚨 CAPTCHA PROBABILE rilevato: 1 forte + {weak_count} deboli")
            return True
        elif strong_count == 1 and 'cloudflare' in content_lower:
            # Cloudflare è sempre un indicatore forte
            self.captcha_detected = True
            logger.warning(f"🚨 CLOUDFLARE rilevato: {strong_count} indicatori forti")
            return True
        elif strong_count == 0 and weak_count >= 4:
            # Solo indicatori deboli, potrebbe essere un falso positivo
            logger.info(f"⚠️ Possibile falso positivo: {weak_count} indicatori deboli, nessuno forte")
            return False
        else:
            # Nessun captcha rilevato
            self.captcha_detected = False
            return False
    
    def handle_captcha(self, page) -> bool:
        """Gestisce il captcha (per ora solo log)"""
        if self.captcha_detected:
            logger.warning("🚨 Captcha rilevato, richiede intervento manuale")
            return False
        return True
    
    async def handle_cloudflare_challenge(self, page) -> bool:
        """Gestisce le sfide Cloudflare in modo più intelligente"""
        try:
            # Aspetta che la pagina si carichi completamente
            await page.wait_for_timeout(5000)
            
            # Cerca elementi di sfida Cloudflare
            challenge_selectors = [
                'iframe[src*="challenges"]',
                '[data-testid="challenge-stage"]',
                '.cf-browser-verification',
                '#challenge-form',
                '[class*="challenge"]',
                'div[class*="cf-"]',
                'form[action*="challenge"]',
                # NUOVI SELEttori per Backmarket e siti simili
                '[class*="verification"]',
                '[class*="checking"]',
                '[class*="browser"]',
                '[class*="human"]',
                '[class*="robot"]',
                '[class*="captcha"]',
                '[class*="ddos"]',
                '[class*="protection"]',
                '[class*="rate"]',
                '[class*="limit"]',
                '[class*="blocked"]',
                '[class*="access"]',
                '[class*="denied"]',
                # Selettori specifici per Backmarket
                '[class*="bm-"]',
                '[class*="backmarket"]',
                '[class*="security"]',
                '[class*="check"]'
            ]
            
            challenge_detected = False
            for selector in challenge_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        challenge_detected = True
                        logger.info(f"🔍 Sfida Cloudflare rilevata con selettore: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"⚠️ Errore selettore {selector}: {e}")
                    continue
            
            if not challenge_detected:
                logger.info("✅ Nessuna sfida Cloudflare rilevata")
                return True
            
            # Se c'è una sfida, prova a gestirla automaticamente
            verify_selectors = [
                'button:has-text("Verify you are human")',
                'button:has-text("I am human")',
                'button:has-text("Continue")',
                'button:has-text("Proceed")',
                'button:has-text("Submit")',
                'input[type="submit"]',
                'button[type="submit"]',
                'button[class*="cf-"]',
                'button[class*="challenge"]'
            ]
            
            for verify_selector in verify_selectors:
                try:
                    verify_button = await page.query_selector(verify_selector)
                    if verify_button and await verify_button.is_visible():
                        await verify_button.click()
                        logger.info(f"✅ Cliccato su: {verify_selector}")
                        await page.wait_for_timeout(3000)
                        break
                except Exception as e:
                    logger.debug(f"⚠️ Errore clic su {verify_selector}: {e}")
                    continue
            
            # Aspetta un tempo fisso per la risoluzione (evita loop infiniti)
            logger.info("⏳ Attendo risoluzione sfida Cloudflare...")
            await page.wait_for_timeout(10000)  # 10 secondi fissi
            
            # Controlla se la sfida è stata risolta
            try:
                current_content = await page.text_content('body')
                if 'checking your browser' not in current_content.lower() and 'challenge' not in current_content.lower():
                    logger.info("✅ Sfida Cloudflare risolta automaticamente")
                    return True
                else:
                    logger.warning("⚠️ Sfida Cloudflare ancora presente, continuo comunque")
                    return False
            except Exception as e:
                logger.warning(f"⚠️ Errore controllo sfida: {e}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Errore gestione Cloudflare: {e}")
            return False
    
    async def wait_for_page_load(self, page, timeout: int = 30000) -> bool:
        """Aspetta che la pagina si carichi completamente"""
        try:
            # Aspetta che la pagina sia in idle
            await page.wait_for_load_state('networkidle', timeout=timeout)
            
            # Aspetta un po' di più per JavaScript dinamico
            await page.wait_for_timeout(2000)
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ Timeout attesa pagina: {e}")
            return False
    
    def get_site_protection_status(self, page_content: str) -> dict:
        """Analizza il livello di protezione di un sito"""
        protection_level = "none"
        protection_type = "none"
        
        content_lower = page_content.lower()
        
        if 'cloudflare' in content_lower:
            protection_type = "cloudflare"
            if 'checking your browser' in content_lower:
                protection_level = "high"
            elif 'ddos protection' in content_lower:
                protection_level = "medium"
            else:
                protection_level = "low"
        elif 'captcha' in content_lower or 'recaptcha' in content_lower:
            protection_type = "captcha"
            protection_level = "high"
        elif 'rate limit' in content_lower or 'blocked' in content_lower:
            protection_type = "rate_limit"
            protection_level = "medium"
        
        return {
            "protected": protection_level != "none",
            "level": protection_level,
            "type": protection_type,
            "suggestion": self._get_protection_suggestion(protection_type, protection_level)
        }
    
    def _get_protection_suggestion(self, protection_type: str, protection_level: str) -> str:
        """Suggerisce strategie per superare la protezione"""
        suggestions = {
            "cloudflare": {
                "low": "Prova a cambiare user agent o aggiungere delay",
                "medium": "Usa modalità stealth e aumenta delay",
                "high": "Richiede intervento manuale o proxy"
            },
            "captcha": {
                "high": "Richiede risoluzione manuale del captcha"
            },
            "rate_limit": {
                "medium": "Riduci frequenza richieste o usa proxy"
            }
        }
        
        return suggestions.get(protection_type, {}).get(protection_level, "Prova a cambiare configurazione browser")
    
    def get_user_agent(self, browser_config: dict = None) -> str:
        """Restituisce un user agent appropriato per il browser"""
        if browser_config and 'user_agent' in browser_config and browser_config['user_agent'] != 'auto':
            return browser_config['user_agent']
        
        # User agent moderno e realistico
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Istanza globale
captcha_handler = CaptchaHandler()
