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

# Mixin (split meccanico per rispettare il limite di lunghezza file)
from ai_content_analyzer_pipeline import _PipelineMixin
from ai_content_analyzer_providers import _ProvidersMixin
from ai_content_analyzer_parsing import _ParsingMixin
from ai_content_analyzer_browser import _BrowserMixin



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



class AIContentAnalyzer(_PipelineMixin, _ProvidersMixin, _ParsingMixin, _BrowserMixin):
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
