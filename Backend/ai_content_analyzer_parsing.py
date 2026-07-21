#!/usr/bin/env python3

"""
AI Content Analyzer - Mixin parsing risposte AI e fallback testuale.

Metodi spostati VERBATIM da ai_content_analyzer.py (solo raggruppamento).
Il mixin usa solo `self.` e NON importa ai_content_analyzer (evita import circolari).
"""

import json
import re

from typing import Dict, List, Any


class _ParsingMixin:
    """Parsing JSON dalle risposte AI ed estrazione manuale di fallback."""

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:

        """Estrae JSON dalla risposta AI"""

        try:

            print(f"🔍 Parsing AI response...")



            # Rimuovi eventuali markdown code blocks

            response = re.sub(r'```json\s*', '', response)

            response = re.sub(r'```\s*$', '', response)



            # Con JSON mode (responseMimeType) la risposta è già JSON valido:
            # il parse diretto è il caso normale. Solo se fallisce si passa alle euristiche.

            try:

                return json.loads(response.strip())

            except json.JSONDecodeError:

                pass



            # Prova a estrarre JSON dalla risposta

            json_match = re.search(r'\{.*\}', response, re.DOTALL)

            if json_match:

                json_str = json_match.group()



                # Gestisci JSON troncato - cerca di completarlo

                if json_str.count('{') > json_str.count('}'):

                    # JSON incompleto, prova a completarlo

                    missing_braces = json_str.count('{') - json_str.count('}')

                    json_str += '}' * missing_braces

                    print(f"🔧 JSON troncato, aggiunti {missing_braces} parentesi graffe")



                # NB: niente inserimento automatico di virgole (corrompeva JSON valido).
                # Rimuovi solo virgole di troppo prima di } o ] (errore comune e sicuro da fixare).

                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)



                try:

                    parsed = json.loads(json_str)

                    print(f"✅ JSON parsato con successo")

                    return parsed

                except json.JSONDecodeError as e:

                    print(f"⚠️ Errore parsing JSON, provo a pulire: {e}")

                    # Prova a pulire il JSON

                    json_str = re.sub(r',\s*}', '}', json_str)  # Rimuovi virgole prima di }

                    json_str = re.sub(r',\s*]', ']', json_str)  # Rimuovi virgole prima di ]

                    try:

                        parsed = json.loads(json_str)

                        print(f"✅ JSON parsato dopo pulizia")

                        return parsed

                    except:

                        print(f"❌ Impossibile parsare JSON anche dopo pulizia")

                        return None

            else:

                # Prova a parsare direttamente

                try:

                    parsed = json.loads(response.strip())

                    print(f"✅ JSON parsato direttamente")

                    return parsed

                except:

                    print(f"❌ Nessun JSON valido trovato")

                    return None



        except Exception as e:

            print(f"❌ Errore parsing JSON: {e}")

            print(f"🔍 Response era: {response[:500]}...")

            return None



    def _fallback_text_scraping(self, text: str, url: str) -> List[Dict[str, Any]]:

        """Fallback: estrazione prodotti dal testo senza AI"""

        import re

        print("🔧 Fallback: estrazione manuale prodotti dal testo...")



        products = []

        lines = text.split('\n')



        # Pattern per prezzi

        price_pattern = r'€\s*[\d.,]+'



        current_product = {}



        for line in lines:

            line_clean = line.strip()

            if len(line_clean) < 10:

                continue



            # Cerca prezzi

            prices = re.findall(price_pattern, line_clean)

            if prices:

                # Se abbiamo già un prodotto in costruzione, salvalo

                if current_product and current_product.get('name'):

                    products.append(current_product)

                    current_product = {}



                # Inizia nuovo prodotto

                current_product = {

                    'name': line_clean,

                    'price': prices[0],

                    'brand': '',

                    'description': '',

                    'confidence': 0.7

                }



                # Cerca brand comuni

                brands = ['HP', 'Dell', 'Lenovo', 'Asus', 'Acer', 'Apple', 'Samsung', 'LG', 'Sony']

                for brand in brands:

                    if brand.lower() in line_clean.lower():

                        current_product['brand'] = brand

                        break



        # Aggiungi l'ultimo prodotto se presente

        if current_product and current_product.get('name'):

            products.append(current_product)



        print(f"🔧 Fallback completato: {len(products)} prodotti estratti manualmente")

        return products
