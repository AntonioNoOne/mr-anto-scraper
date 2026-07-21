#!/usr/bin/env python3

"""
Fast AI Extractor - Estrazione veloce e semplice da singola pagina
Niente caricamenti dinamici, niente paginazione, solo estrazione chirurgica
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from ai_content_analyzer import AIContentAnalyzer
from selector_database import SelectorDatabase
from historical_products_db import HistoricalProductsDB
from proxy_manager import ProxyManager
from captcha_handler import CaptchaHandler

# Costanti/configurazioni condivise (re-export per retro-compatibilita' import)
from fast_ai_extractor_config import (
    ANTI_BOT_SITES,
    STRONG_ANTI_BOT_SITES,
    BROWSER_ARGS_BASE,
    BROWSER_ARGS_STEALTH,
    BROWSER_ARGS_VISIBLE,
)

# Mixin che compongono la classe FastAIExtractor
from fast_ai_extractor_extraction import _ExtractionMixin
from fast_ai_extractor_selectorflow import _SelectorFlowMixin
from fast_ai_extractor_parsing import _ParsingMixin
from fast_ai_extractor_ai import _AiSelectorMixin


class FastAIExtractor(_ExtractionMixin, _SelectorFlowMixin, _ParsingMixin, _AiSelectorMixin):
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
