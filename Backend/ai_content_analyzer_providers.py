#!/usr/bin/env python3

"""
AI Content Analyzer - Mixin provider AI (OpenAI / Gemini) e fallback.

Metodi spostati VERBATIM da ai_content_analyzer.py (solo raggruppamento).
Il mixin usa solo `self.` e NON importa ai_content_analyzer (evita import circolari).
"""

import requests

from typing import Dict, Any, Optional


class _ProvidersMixin:
    """Provider AI: ordine di tentativo, fallback, chiamate OpenAI/Gemini."""

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

                    # JSON mode: Gemini restituisce JSON puro (niente ```json/prosa)
                    "responseMimeType": "application/json",

                    # Alzato per evitare troncamenti su pagine con molti prodotti
                    "maxOutputTokens": 8192

                }

            }



            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"



            response = requests.post(url, headers=headers, json=payload, timeout=120)



            if response.status_code == 200:

                result = response.json()

                ai_response = result["candidates"][0]["content"]["parts"][0]["text"]

                print(f"🤖 Gemini Response: {ai_response[:200]}...")

                parsed_result = self._extract_json_from_response(ai_response)

                if not parsed_result:

                    print(f"❌ Gemini: risposta non parsabile come JSON")

                    return None

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
