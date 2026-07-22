#!/usr/bin/env python3

"""
AI Product Comparator - AI analysis & clustering mixin
======================================================

Blocco estratto (mixin) contenente le helper di analisi AI semantica e di
clustering usate da AIProductComparator:
- Analisi AI diretta e per gruppi
- Estrazione/parsing JSON dalle risposte AI
- Merge e similarità tra cluster

NOTA: split puramente meccanico per rispettare il limite di lunghezza file.
Nessuna modifica a logica/stringhe/firme. Il mixin usa solo `self.` e NON
importa ai_product_comparator (per evitare import circolari).
"""

import json
import logging
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class _ComparatorAiMixin:
    async def _analyze_products_direct(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analisi AI diretta per pochi prodotti"""
        try:
            # Prepara dati per AI
            products_text = []
            for product in products:
                product_info = f"Nome: {product['original_name']}\n"
                product_info += f"Brand: {product['original_brand']}\n"
                product_info += f"Prezzo: {product['original_price']}\n"
                product_info += f"Fonte: {product['source']}\n"
                products_text.append(product_info)

            # Analisi AI per similarità
            analysis_prompt = f"""SEI UN ASSISTENTE SPECIALIZZATO NELL'ANALISI DI PRODOTTI.

REGOLE OBBLIGATORIE:
1. Analizza SOLO i prodotti forniti qui sotto
2. NON accedere a siti esterni o cercare informazioni esterne
3. Rispondi SEMPRE e SOLO con JSON valido
4. Non includere mai testo esplicativo, spiegazioni o commenti
5. Non dire "Mi dispiace" o "non posso accedere"

MISSIONE: Raggruppa i prodotti per similarità SEMANTICA PRECISA basandoti sui dati forniti.

PRODOTTI DA ANALIZZARE:
{chr(10).join(f"---PRODOTTO {i+1}---{chr(10)}{text}" for i, text in enumerate(products_text))}

ANALISI RICHIESTA:
- Confronta NOME, BRAND, MEMORIA, PESO, COLORE, MODELLO
- Raggruppa SOLO prodotti dello STESSO PRODOTTO con caratteristiche SIMILI
- Usa score da 0.85 a 1.0 (più restrittivo)
- Crea gruppi LOGICI di prodotti confrontabili

CRITERI DI RAGGRUPPAMENTO OBBLIGATORI:
- STESSO BRAND (es: Apple, Samsung, etc.)
- STESSO MODELLO (es: iPhone 15 Pro, Galaxy S24)
- STESSA MEMORIA (es: 128GB, 256GB, 512GB, 1TB)
- STESSO COLORE/FINISH (es: Titanio, Grigio, Nero, Bianco, Blu)

ESEMPI DI RAGGRUPPAMENTO CORRETTO:
✅ iPhone 15 Pro 128GB Nero + iPhone 15 Pro 128GB Nero (stesso prodotto, stesso colore, stessa memoria)
✅ iPhone 15 Pro 256GB Bianco + iPhone 15 Pro 256GB Bianco (stesso prodotto, stesso colore, stessa memoria)
✅ Samsung Display AMOLED 8'' + Samsung Display AMOLED 8'' (stesso prodotto, stesse dimensioni)

ESEMPI DI RAGGRUPPAMENTO SBAGLIATO:
❌ iPhone 15 Pro 128GB + iPhone 15 Pro 256GB (memorie diverse)
❌ iPhone 15 Pro Nero + iPhone 15 Pro Bianco (colori diversi)
❌ iPhone 15 Pro + Fire TV Stick (prodotti completamente diversi)
❌ iPhone + Samsung (brand diversi)

RISPOSTA OBBLIGATORIA (SOLO JSON):
{{
  "groups": [
    {{
      "group_id": 1,
      "similarity_score": 0.95,
      "products_indices": [0, 2],
      "common_features": ["stesso brand", "stesso modello", "stessa memoria", "stesso colore"]
    }}
  ]
}}

RICORDA: SOLO JSON, NIENTE ALTRO. Se non puoi analizzare, restituisci JSON con array vuoto."""

            # Chiamata AI in JSON mode (Gemini). NB: prima usava chat_manager con
            # model="openai" -> con chiave OpenAI assente/placeholder dava 401 e il
            # confronto restituiva 0 match; inoltre la risposta non era JSON puro.
            # call_json usa Gemini in JSON mode e ritorna gia' il dict parsato.
            ai_response = await self.ai_analyzer.call_json(analysis_prompt, max_tokens=4096)
            if not ai_response:
                logger.warning("⚠️ Analisi AI confronto: nessun JSON valido")
                return []

            # Parsing risultato AI
            try:
                logger.info(f"✅ DEBUG - JSON AI ricevuto")
                logger.info(f"  Numero gruppi ricevuti: {len(ai_response.get('groups', []))}")

                clusters = []

                for group in ai_response.get('groups', []):
                    logger.info(f"🔍 DEBUG - Analizzando gruppo: {group}")
                    group_products = [products[i] for i in group['products_indices'] if i < len(products)]
                    if len(group_products) > 1:  # Solo gruppi con più di un prodotto
                        logger.info(f"✅ Gruppo valido con {len(group_products)} prodotti")
                        clusters.append({
                            'products': group_products,
                            'similarity_score': group.get('similarity_score', 0.8),
                            'common_features': group.get('common_features', []),
                            'group_id': group.get('group_id', len(clusters) + 1)
                        })
                    else:
                        logger.info(f"⚠️ Gruppo scartato: solo {len(group_products)} prodotto/i")

                # GUARD deterministico: l'AI a volte mette insieme brand diversi
                # (es. Apple MacBook + ASUS Vivobook). Filtra ogni cluster al
                # brand dominante e scarta chi non combacia. Generalista: usa
                # solo uguaglianza di brand, nessun elenco hardcoded.
                clusters = self._enforce_brand_consistency(clusters)
                # Secondo guard: stesso brand ma modello diverso non deve unirsi
                # (es. MacBook Neo vs MacBook Air). Sotto-raggruppa per nome.
                clusters = self._enforce_model_consistency(clusters)

                logger.info(f"✅ DEBUG - Cluster finali creati: {len(clusters)}")
                return clusters

            except Exception as e:
                logger.warning(f"⚠️ Errore elaborazione gruppi AI: {e}")
                # ai_response e' gia' JSON parsato (call_json); se la struttura non
                # e' quella attesa, prova comunque il processore tollerante.
                try:
                    return self._process_extracted_json(ai_response, products)
                except Exception:
                    return []

        except Exception as e:
            logger.error(f"❌ Errore analisi AI diretta: {e}")
            return []

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Tenta di estrarre JSON da una risposta AI non valida"""
        try:
            # Cerca pattern JSON nella risposta
            import re

            # Pattern per trovare JSON nella risposta
            json_pattern = r'\{[^{}]*"groups"[^{}]*\[[^\]]*\]'
            matches = re.findall(json_pattern, response_text, re.DOTALL)

            if matches:
                # Prendi il primo match e prova a parsarlo
                potential_json = matches[0]
                logger.info(f"🔍 JSON potenziale estratto: {potential_json[:200]}...")

                # Prova a parsare
                return json.loads(potential_json)

            # Se non trova pattern, cerca qualsiasi JSON valido
            json_pattern2 = r'\{[^{}]*\}'
            matches2 = re.findall(json_pattern2, response_text, re.DOTALL)

            for match in matches2:
                try:
                    return json.loads(match)
                except:
                    continue

            return None

        except Exception as e:
            logger.error(f"❌ Errore estrazione JSON: {e}")
            return None

    def _process_extracted_json(self, extracted_json: Dict[str, Any], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processa JSON estratto dal fallback"""
        try:
            clusters = []

            for group in extracted_json.get('groups', []):
                group_products = [products[i] for i in group.get('products_indices', []) if i < len(products)]
                if len(group_products) > 1:  # Solo gruppi con più di un prodotto
                    clusters.append({
                        'products': group_products,
                        'similarity_score': group.get('similarity_score', 0.8),
                        'common_features': group.get('common_features', []),
                        'group_id': group.get('group_id', len(clusters) + 1)
                    })

            return clusters

        except Exception as e:
            logger.error(f"❌ Errore processamento JSON estratto: {e}")
            return []

    def _brand_key(self, product: Dict[str, Any]) -> str:
        """Chiave brand per un prodotto: brand normalizzato, altrimenti prima
        parola del nome. Minuscolo e senza spazi. Generalista, nessun elenco."""
        brand = (product.get('normalized_brand') or product.get('original_brand') or '').strip().lower()
        if not brand:
            name = (product.get('normalized_name') or product.get('original_name') or '').strip().lower()
            brand = name.split()[0] if name else ''
        return brand

    def _enforce_brand_consistency(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Garantisce che ogni cluster contenga un solo brand.

        L'AI a volte raggruppa prodotti di brand diversi. Per ogni cluster si
        determina il brand dominante e si tengono solo i prodotti di quel brand;
        i cluster che scendono sotto 2 prodotti vengono scartati.
        """
        cleaned = []
        for cluster in clusters:
            products = cluster.get('products', [])
            if not products:
                continue
            from collections import Counter
            counts = Counter(self._brand_key(p) for p in products)
            # brand dominante (ignora chiavi vuote se esistono alternative)
            non_empty = {b: c for b, c in counts.items() if b}
            dominant = max(non_empty, key=non_empty.get) if non_empty else ''
            kept = [p for p in products if self._brand_key(p) == dominant]
            dropped = len(products) - len(kept)
            if dropped:
                logger.info(f"🛡️ Brand guard: cluster brand='{dominant}', rimossi {dropped} prodotti di altri brand")
            if len(kept) > 1:
                cluster = {**cluster, 'products': kept}
                cleaned.append(cluster)
            else:
                logger.info(f"⚠️ Cluster scartato dopo brand guard: resta {len(kept)} prodotto")
        return cleaned

    # Attributi generici da ignorare quando si confronta il MODELLO (colore,
    # taglio memoria, unita'). Sono attributi di prodotto, non un elenco di
    # domini/brand: il sistema resta generalista.
    _MODEL_STOPWORDS = {
        "gb", "tb", "ram", "ssd", "hdd", "cm", "mm", "pollici", "kg", "g",
        "notebook", "laptop", "computer", "portatile", "portatili", "pc",
        "con", "di", "e", "il", "la", "the", "and",
        "nero", "bianco", "grigio", "argento", "silver", "oro", "gold", "blu",
        "blue", "azzurro", "rosa", "pink", "giallo", "yellow", "verde", "green",
        "rosso", "red", "viola", "purple", "titanio", "titanium", "grafite",
        "space", "gray", "grey", "pastello", "agrume", "mezzanotte", "midnight",
        "galassia", "starlight", "sabbia",
    }

    def _model_signature(self, product: Dict[str, Any]) -> str:
        """Firma-modello: nome senza brand, colori, tagli memoria e unita'.
        Serve a confrontare il modello ignorando le varianti estetiche."""
        import re
        name = (product.get('normalized_name') or product.get('original_name') or '').lower()
        brand = self._brand_key(product)
        tokens = re.split(r'[^a-z0-9]+', name)
        sig = []
        for t in tokens:
            if not t or t == brand:
                continue
            if t in self._MODEL_STOPWORDS:
                continue
            if t.isdigit() and len(t) >= 3:  # es. 512, 1000 (memoria) -> scarta
                continue
            sig.append(t)
        return " ".join(sig)

    def _enforce_model_consistency(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dentro ogni cluster (gia' mono-brand) separa i modelli diversi.

        Raggruppa i prodotti per similarita' della firma-modello: varianti di
        colore/memoria dello stesso modello restano insieme, modelli diversi
        dello stesso brand finiscono in cluster distinti. Sotto-gruppi con meno
        di 2 prodotti vengono scartati.
        """
        threshold = 0.72
        result = []
        for cluster in clusters:
            products = cluster.get('products', [])
            subgroups = []  # lista di {sig, products}
            for p in products:
                sig = self._model_signature(p)
                placed = False
                for sg in subgroups:
                    if SequenceMatcher(None, sig, sg['sig']).ratio() >= threshold:
                        sg['products'].append(p)
                        placed = True
                        break
                if not placed:
                    subgroups.append({'sig': sig, 'products': [p]})
            if len(subgroups) > 1:
                logger.info(f"🛡️ Model guard: cluster diviso in {len(subgroups)} modelli distinti")
            for i, sg in enumerate(subgroups):
                if len(sg['products']) > 1:
                    result.append({**cluster, 'products': sg['products'],
                                   'group_id': cluster.get('group_id', 0) * 100 + i})
        return result

    async def _analyze_products_in_groups(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analisi AI per gruppi quando ci sono troppi prodotti"""
        try:
            # Dividi prodotti in gruppi più piccoli
            groups = [products[i:i + self.max_products_per_analysis]
                     for i in range(0, len(products), self.max_products_per_analysis)]

            all_clusters = []

            for i, group in enumerate(groups):
                logger.info(f"📊 Analizzando gruppo {i+1}/{len(groups)} ({len(group)} prodotti)")

                group_clusters = await self._analyze_products_direct(group)

                # Aggiusta indici per il gruppo globale
                for cluster in group_clusters:
                    cluster['group_id'] = len(all_clusters) + 1

                all_clusters.extend(group_clusters)

            # Unisci cluster simili tra gruppi diversi
            merged_clusters = self._merge_similar_clusters(all_clusters)

            # Il merge usa similarità di nome e può re-unire brand diversi:
            # riapplica il guard sul brand.
            merged_clusters = self._enforce_brand_consistency(merged_clusters)
            merged_clusters = self._enforce_model_consistency(merged_clusters)

            return merged_clusters

        except Exception as e:
            logger.error(f"❌ Errore analisi AI per gruppi: {e}")
            return []

    def _merge_similar_clusters(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Unisce cluster simili tra gruppi diversi"""
        try:
            if len(clusters) <= 1:
                return clusters

            merged = []
            used_indices = set()

            for i, cluster1 in enumerate(clusters):
                if i in used_indices:
                    continue

                current_cluster = cluster1.copy()
                used_indices.add(i)

                # Cerca cluster simili
                for j, cluster2 in enumerate(clusters[i+1:], i+1):
                    if j in used_indices:
                        continue

                    # Calcola similarità tra cluster
                    similarity = self._calculate_cluster_similarity(cluster1, cluster2)

                    if similarity > 0.6:  # Soglia per unione
                        current_cluster['products'].extend(cluster2['products'])
                        current_cluster['similarity_score'] = max(
                            current_cluster['similarity_score'],
                            cluster2['similarity_score']
                        )
                        used_indices.add(j)

                merged.append(current_cluster)

            return merged

        except Exception as e:
            logger.error(f"❌ Errore merge cluster: {e}")
            return clusters

    def _calculate_cluster_similarity(self, cluster1: Dict, cluster2: Dict) -> float:
        """Calcola similarità tra due cluster"""
        try:
            # Confronta nomi normalizzati dei prodotti
            names1 = [p['normalized_name'] for p in cluster1['products']]
            names2 = [p['normalized_name'] for p in cluster2['products']]

            similarities = []
            for name1 in names1:
                for name2 in names2:
                    similarity = SequenceMatcher(None, name1, name2).ratio()
                    similarities.append(similarity)

            return max(similarities) if similarities else 0.0

        except:
            return 0.0
