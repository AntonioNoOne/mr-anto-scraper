#!/usr/bin/env python3

"""
AI Product Comparator - Sistema di confronto prodotti intelligente
===============================================================

Sistema avanzato per confrontare prodotti usando analisi semantica AI
invece del semplice confronto testuale. Identifica prodotti simili anche
quando i nomi sono diversi ma si riferiscono allo stesso prodotto.

FLUSSO PRINCIPALE:
1. Normalizzazione e pulizia dati prodotti
2. Analisi semantica con AI per similarità
3. Clustering intelligente prodotti simili
4. Calcolo differenze prezzo e statistiche
5. Ranking risultati per rilevanza

DIPENDENZE:
- ai_content_analyzer: Per analisi AI dei prodotti
- difflib: Per confronto testuale di backup
- typing: Type hints per documentazione
- json: Serializzazione risultati
- logging: Sistema di log per debugging

SCRIPT CHE RICHIAMANO QUESTO:
- main.py: Endpoint /compare-products
- product_comparator.py: Fallback al sistema attuale
- fast_ai_extractor.py: Per confronti post-estrazione

SCRIPT RICHIAMATI DA QUESTO:
- ai_content_analyzer.py: Per analisi semantica AI
- chat_ai_manager.py: Per chiamate AI dirette

STRUTTURA RISULTATI:
- Gruppi di prodotti simili
- Score di similarità per ogni gruppo
- Differenze prezzo e statistiche
- Metadati analisi (modello AI usato, timestamp)

FUNZIONALITÀ PRINCIPALI:
- compare_products_ai(): Confronto principale con AI
- analyze_product_similarity(): Analisi similarità semantica
- cluster_similar_products(): Clustering intelligente
- calculate_price_differences(): Calcolo differenze prezzo
- get_similarity_score(): Score di similarità 0-1

WORKFLOW CONFRONTO:
1. Riceve lista prodotti da diversi siti
2. Normalizza e pulisce dati (nomi, prezzi, brand)
3. Usa AI per analizzare similarità semantica
4. Raggruppa prodotti simili in cluster
5. Calcola statistiche prezzo per ogni cluster
6. Restituisce risultati ordinati per rilevanza

PERFORMANCE:
- Analisi AI: ~2-5 secondi per gruppo prodotti
- Fallback testuale: ~100-500ms
- Scalabilità: Ottimizzato per 50-100 prodotti
- Caching: Risultati AI salvati per riuso

VALIDAZIONE:
- Controllo formato dati input
- Verifica prezzi validi
- Validazione score similarità
- Controllo integrità cluster

FUTURO SVILUPPO:
- Embedding vectors: Per similarità più precisa
- Machine learning: Per migliorare accuracy
- Cache intelligente: Per performance
- Analisi immagini: Per confronto visivo
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from difflib import SequenceMatcher

# Import dei nostri moduli
try:
    from ai_content_analyzer import AIContentAnalyzer
    from chat_ai_manager import ChatAIManager
except ImportError:
    # Fallback per import relativi
    from .ai_content_analyzer import AIContentAnalyzer
    from .chat_ai_manager import ChatAIManager

try:
    from ai_product_comparator_ai import _ComparatorAiMixin
except ImportError:
    from .ai_product_comparator_ai import _ComparatorAiMixin

logger = logging.getLogger(__name__)

class AIProductComparator(_ComparatorAiMixin):
    """Sistema di confronto prodotti intelligente con AI"""
    
    def __init__(self):
        self.ai_analyzer = AIContentAnalyzer()
        self.chat_manager = ChatAIManager()
        
        # Configurazione
        self.similarity_threshold = 0.85  # Soglia minima similarità (ancora più restrittiva)
        self.max_products_per_analysis = 20  # Max prodotti per analisi AI
        self.fallback_to_textual = True  # Usa confronto testuale se AI fallisce
        self.enable_deduplication = True  # Abilita deduplicazione intelligente
        
        logger.info("🤖 AI Product Comparator inizializzato")
    
    async def compare_products_ai(self, products_data: List[Dict[str, Any]], selected_domains: List[str] = None) -> Dict[str, Any]:
        """
        Confronto principale prodotti usando AI semantica
        
        ARGS:
        - products_data: Lista di prodotti da diversi siti
        - selected_domains: Lista di domini selezionati per il confronto (es: ['amazon.it', 'mediaworld.it'])
        
        RETURNS:
        - Dict con gruppi di prodotti simili e statistiche
        """
        try:
            logger.info(f"🔍 AI Product Comparator - {len(products_data)} prodotti da analizzare")
            
            # FILTRO PER DOMINI SELEZIONATI
            if selected_domains and len(selected_domains) > 0:
                logger.info(f"🎯 DOMINI SELEZIONATI: {selected_domains}")
                
                # 🆕 DEBUG DETTAGLIATO: Conta prodotti per ogni dominio
                logger.info("🔍 DEBUG - ANALISI PRODOTTI PER DOMINIO:")
                domain_counts = {}
                for domain in selected_domains:
                    domain_counts[domain] = 0
                
                # Conta prodotti per ogni dominio
                for product in products_data:
                    product_source = product.get('source', '').lower()
                    product_name = product.get('name', 'N/A')
                    
                    for domain in selected_domains:
                        if domain.lower() in product_source:
                            domain_counts[domain] += 1
                            logger.info(f"  ✅ {domain}: '{product_name}' (source: {product_source})")
                
                # Mostra conteggio finale per dominio
                logger.info("📊 CONTEGGIO FINALE PER DOMINIO:")
                for domain, count in domain_counts.items():
                    logger.info(f"  - {domain}: {count} prodotti")
                
                # Filtra prodotti SOLO per domini selezionati
                filtered_products = []
                logger.info("🔍 DEBUG - FILTRO PRODOTTI PER DOMINI:")
                
                for product in products_data:
                    product_source = product.get('source', '').lower()
                    product_name = product.get('name', 'N/A')
                    
                    # 🆕 DEBUG: Mostra tutti i campi source disponibili
                    logger.info(f"  🔍 Prodotto: '{product_name}'")
                    logger.info(f"    - source: '{product.get('source', 'N/A')}'")
                    logger.info(f"    - source_url: '{product.get('source_url', 'N/A')}'")
                    logger.info(f"    - site: '{product.get('site', 'N/A')}'")
                    
                    # Controlla se il source del prodotto contiene uno dei domini selezionati
                    matched_domain = None
                    for domain in selected_domains:
                        if domain.lower() in product_source:
                            matched_domain = domain
                            break
                    
                    if matched_domain:
                        filtered_products.append(product)
                        logger.info(f"    ✅ MATCH con dominio: {matched_domain}")
                    else:
                        logger.info(f"    ❌ NO MATCH - source '{product_source}' non contiene domini selezionati")
                
                logger.info(f"🔍 DEBUG - FILTRO COMPLETATO: {len(filtered_products)} prodotti filtrati")
                
                logger.info(f"✅ Prodotti filtrati per domini selezionati: {len(filtered_products)}/{len(products_data)}")
                
                if len(filtered_products) == 0:
                    return {
                        "success": False,
                        "error": f"Nessun prodotto trovato per i domini selezionati: {selected_domains}",
                        "matches": [],
                        "statistics": {}
                    }
                
                # Usa solo i prodotti filtrati
                products_to_analyze = filtered_products
                logger.info(f"🎯 Analizzerò SOLO i prodotti dei domini selezionati")
            else:
                logger.info("🌍 Nessun dominio selezionato, confronto TUTTI i prodotti")
                products_to_analyze = products_data
            
            # DEBUG: Mostra i primi 5 prodotti da analizzare
            logger.info("📋 DEBUG - PRIMI 5 PRODOTTI DA ANALIZZARE:")
            for i, product in enumerate(products_to_analyze[:5]):
                logger.info(f"  Prodotto {i+1}:")
                logger.info(f"    Nome: '{product.get('name', 'N/A')}'")
                logger.info(f"    Brand: '{product.get('brand', 'N/A')}'")
                logger.info(f"    Prezzo: '{product.get('price', 'N/A')}'")
                logger.info(f"    Sorgente: '{product.get('source', 'N/A')}'")
                logger.info(f"    Source URL: '{product.get('source_url', 'N/A')}'")
                logger.info(f"    Site: '{product.get('site', 'N/A')}'")
                logger.info(f"    URL: '{product.get('url', 'N/A')}'")
                logger.info(f"    🔍 DEBUG - Campi disponibili: {list(product.keys())}")
            
            # 🆕 DEDUPLICAZIONE INTELLIGENTE
            if self.enable_deduplication:
                logger.info(f"🧹 Deduplicazione prodotti...")
                deduplicated_products = self._deduplicate_products(products_to_analyze)
                logger.info(f"✅ Prodotti deduplicati: {len(products_to_analyze)} → {len(deduplicated_products)}")
                products_to_analyze = deduplicated_products
            
            # Normalizza e pulisce i dati FILTRATI
            normalized_products = self._normalize_products(products_to_analyze)
            logger.info(f"✅ Prodotti normalizzati: {len(normalized_products)}")
            
            # DEBUG: Mostra i primi 5 prodotti normalizzati
            logger.info("📋 DEBUG - PRIMI 5 PRODOTTI NORMALIZZATI:")
            for i, product in enumerate(normalized_products[:5]):
                logger.info(f"  Prodotto {i+1}:")
                logger.info(f"    Nome originale: '{product.get('original_name', 'N/A')}'")
                logger.info(f"    Nome normalizzato: '{product.get('normalized_name', 'N/A')}'")
                logger.info(f"    Brand originale: '{product.get('original_brand', 'N/A')}'")
                logger.info(f"    Brand normalizzato: '{product.get('normalized_brand', 'N/A')}'")
                logger.info(f"    Prezzo originale: '{product.get('original_price', 'N/A')}'")
                logger.info(f"    Prezzo normalizzato: {product.get('normalized_price', 'N/A')}")
                logger.info(f"    Sorgente: '{product.get('source', 'N/A')}'")
            
            if len(normalized_products) == 0:
                return {
                    "success": False,
                    "error": "Nessun prodotto valido da confrontare",
                    "matches": [],
                    "statistics": {}
                }
            
            # Se pochi prodotti, usa analisi diretta
            if len(normalized_products) <= self.max_products_per_analysis:
                logger.info("🎯 Analisi AI diretta per pochi prodotti")
                clusters = await self._analyze_products_direct(normalized_products)
            else:
                logger.info("📊 Analisi AI per gruppi (troppi prodotti)")
                clusters = await self._analyze_products_in_groups(normalized_products)
            
            # DEBUG: Mostra i cluster trovati
            logger.info(f"📊 DEBUG - CLUSTER TROVATI: {len(clusters)}")
            for i, cluster in enumerate(clusters):
                logger.info(f"  Cluster {i+1}:")
                logger.info(f"    Score similarità: {cluster.get('similarity_score', 'N/A')}")
                logger.info(f"    Prodotti nel cluster: {len(cluster.get('products', []))}")
                logger.info(f"    Caratteristiche comuni: {cluster.get('common_features', [])}")
                for j, product in enumerate(cluster.get('products', [])[:3]):  # Primi 3 prodotti
                    logger.info(f"      Prodotto {j+1}: '{product.get('original_name', 'N/A')}' da {product.get('source', 'N/A')}")
            
            # Calcola statistiche e differenze prezzo
            enriched_clusters = self._calculate_price_statistics(clusters)
            
            # Prepara risultato finale
            result = {
                "success": True,
                "matches": enriched_clusters,
                "statistics": self._calculate_overall_statistics(enriched_clusters, normalized_products),
                "total_sites": len(set(p.get('source', 'Unknown') for p in normalized_products)),
                "total_products": len(normalized_products),
                "comparable_products": sum(len(cluster['products']) for cluster in enriched_clusters),
                "analysis_method": "ai_semantic",
                "similarity_threshold": self.similarity_threshold,
                "timestamp": datetime.now().isoformat()
            }
            
            # 🆕 AGGIUNGI STATISTICHE MIGLIORATE
            if enriched_clusters:
                # Calcola statistiche aggregate più chiare
                all_prices = []
                for cluster in enriched_clusters:
                    cluster_prices = [p.get('normalized_price', 0) for p in cluster.get('products', []) if p.get('normalized_price', 0) > 0]
                    if cluster_prices:
                        all_prices.extend(cluster_prices)
                
                if all_prices:
                    result['summary_stats'] = {
                        'total_groups': len(enriched_clusters),
                        'total_comparable_products': sum(len(cluster['products']) for cluster in enriched_clusters),
                        'price_range': {
                            'min': min(all_prices),
                            'max': max(all_prices),
                            'avg': round(sum(all_prices) / len(all_prices), 2)
                        },
                        'total_savings_opportunity': sum(cluster.get('savings_opportunity', 0) for cluster in enriched_clusters),
                        'best_deal': {
                            'product_name': '',
                            'price': 0,
                            'source': '',
                            'savings': 0
                        }
                    }
                    
                    # Trova il miglior affare
                    best_deal = None
                    best_savings = 0
                    for cluster in enriched_clusters:
                        if cluster.get('savings_opportunity', 0) > best_savings:
                            best_savings = cluster.get('savings_opportunity', 0)
                            cheapest = cluster.get('cheapest_product', {})
                            most_expensive = cluster.get('most_expensive_product', {})
                            if cheapest and most_expensive:
                                best_deal = {
                                    'product_name': cheapest.get('original_name', ''),
                                    'price': cheapest.get('normalized_price', 0),
                                    'source': cheapest.get('source', ''),
                                    'savings': best_savings
                                }
                    
                    if best_deal:
                        result['summary_stats']['best_deal'] = best_deal
            
            logger.info(f"✅ Confronto AI completato: {len(enriched_clusters)} gruppi trovati")
            return result
            
        except Exception as e:
            logger.error(f"❌ Errore confronto AI: {e}")
            
            # Fallback al confronto testuale se abilitato
            if self.fallback_to_textual:
                logger.info("🔄 Fallback al confronto testuale...")
                logger.info("🔍 DEBUG - Motivo fallback: errore AI")
                logger.info(f"🔍 DEBUG - Errore dettagliato: {str(e)}")
                return await self._fallback_textual_comparison(products_data)
            
            logger.error(f"❌ DEBUG - Fallback testuale disabilitato, ritorno errore")
            return {
                "success": False,
                "error": f"Errore confronto AI: {str(e)}",
                "matches": [],
                "statistics": {}
            }
    
    def _deduplicate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplica prodotti basandosi su nome, brand, memoria e colore"""
        logger.info("🧹 Inizio deduplicazione prodotti...")
        
        # Crea un dizionario per tenere traccia dei prodotti unici
        unique_products = {}
        duplicates_removed = 0
        
        for product in products:
            try:
                name = product.get('name', '').lower().strip()
                brand = product.get('brand', '').lower().strip()
                
                # Estrai caratteristiche chiave
                memory = self._extract_memory(name)
                color = self._extract_color(name)
                model = self._extract_model(name, brand)
                
                # Crea una chiave unica per il prodotto
                product_key = f"{brand}|{model}|{memory}|{color}"
                
                if product_key not in unique_products:
                    unique_products[product_key] = product
                    logger.info(f"  ✅ Aggiunto: {name} ({brand} - {memory} - {color})")
                else:
                    # Prodotto duplicato trovato
                    existing_product = unique_products[product_key]
                    existing_price = self._normalize_price(existing_product.get('price', '0'))
                    new_price = self._normalize_price(product.get('price', '0'))
                    
                    # Mantieni quello con prezzo più basso
                    if new_price < existing_price:
                        unique_products[product_key] = product
                        logger.info(f"  🔄 Sostituito: {name} (prezzo migliore: €{new_price} vs €{existing_price})")
                    else:
                        logger.info(f"  ❌ Rimosso duplicato: {name} (prezzo peggiore: €{new_price} vs €{existing_price})")
                    
                    duplicates_removed += 1
                    
            except Exception as e:
                logger.error(f"❌ Errore deduplicazione prodotto: {e}")
                continue
        
        logger.info(f"🧹 Deduplicazione completata: {duplicates_removed} duplicati rimossi")
        return list(unique_products.values())
    
    def _extract_memory(self, product_name: str) -> str:
        """Estrae la memoria dal nome del prodotto"""
        import re
        
        # Pattern per memoria (es: 128GB, 256GB, 512GB, 1TB)
        memory_patterns = [
            r'(\d+)\s*GB',
            r'(\d+)\s*TB',
            r'(\d+)\s*MB'
        ]
        
        for pattern in memory_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                size = match.group(1)
                unit = 'GB' if 'GB' in pattern else ('TB' if 'TB' in pattern else 'MB')
                return f"{size}{unit}"
        
        return "N/A"
    
    def _extract_color(self, product_name: str) -> str:
        """Estrae il colore dal nome del prodotto"""
        import re
        
        # Pattern per colori comuni
        color_patterns = [
            r'(nero|black)',
            r'(bianco|white)',
            r'(grigio|gray|grey)',
            r'(bilocale|trilocale|monolocale|villa)',
            r'(blu|blue)',
            r'(rosso|red)',
            r'(verde|green)',
            r'(giallo|yellow)',
            r'(rosa|pink)',
            r'(viola|purple)',
            r'(arancione|orange)',
            r'(titanio|titanium)',
            r'(oro|gold)',
            r'(argento|silver)'
        ]
        
        for pattern in color_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        
        return "N/A"
    
    def _extract_model(self, product_name: str, brand: str) -> str:
        """Estrae il modello dal nome del prodotto"""
        import re
        
        # Rimuovi il brand dal nome
        clean_name = product_name.replace(brand, '').strip()
        
        # Pattern per modelli comuni
        model_patterns = [
            r'(iPhone\s+\d+\s+Pro)',
            r'(iPhone\s+\d+)',
            r'(Galaxy\s+S\d+)',
            r'(Galaxy\s+Note\s+\d+)',
            r'(iPad\s+\w+)',
            r'(MacBook\s+\w+)',
            r'(Fire\s+TV\s+Stick)',
            r'(DISPLAY\s+AMOLED\s+\d+\'\')',
            r'(Bilocale\s+\d+mq)',
            r'(Trilocale\s+\d+mq)',
            r'(Monolocale\s+\d+mq)',
            r'(Villa\s+\d+mq)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, clean_name, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Se non trova pattern specifici, usa il nome pulito
        return clean_name[:50]  # Limita a 50 caratteri
    
    def _normalize_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalizza e pulisce i dati dei prodotti"""
        normalized = []
        seen_products = set()  # Per evitare duplicati
        
        for product in products:
            try:
                # Estrai dati base
                name = product.get('name', '').strip()
                price = product.get('price', '0')
                brand = product.get('brand', '').strip()
                source = product.get('source', product.get('source_url', 'Unknown'))
                
                # Valida dati minimi
                if not name or len(name) < 3:
                    continue
                
                # Normalizza prezzo
                normalized_price = self._normalize_price(price)
                if normalized_price <= 0:
                    continue
                
                # Normalizza nome e brand
                normalized_name = self._normalize_product_name(name)
                normalized_brand = self._normalize_brand(brand)
                
                # Crea chiave unica per evitare duplicati sullo stesso sito
                product_key = f"{source}_{normalized_name}_{normalized_brand}_{normalized_price}"
                
                # Se già visto questo prodotto su questo sito, salta
                if product_key in seen_products:
                    logger.debug(f"⏭️ Prodotto duplicato saltato: {name} su {source}")
                    continue
                
                seen_products.add(product_key)
                
                normalized.append({
                    'original_name': name,
                    'normalized_name': normalized_name,
                    'original_price': price,
                    'normalized_price': normalized_price,
                    'original_brand': brand,
                    'normalized_brand': normalized_brand,
                    'source': source,
                    'source_url': product.get('source_url', ''),
                    'site': source,  # Mantieni il nome del sito
                    'url': product.get('url', ''),
                    'raw_data': product
                })
                
            except Exception as e:
                logger.warning(f"⚠️ Errore normalizzazione prodotto: {e}")
                continue
        
        return normalized
    
    def _normalize_price(self, price: str) -> float:
        """Normalizza prezzo in float"""
        try:
            # DEBUG: Mostra il prezzo originale
            logger.debug(f"🔍 DEBUG - Normalizzazione prezzo: '{price}' (tipo: {type(price)})")
            
            if isinstance(price, (int, float)):
                logger.debug(f"  Prezzo già numerico: {price}")
                return float(price)
            
            # Rimuovi simboli valuta e spazi
            price_str = str(price).replace('€', '').replace('$', '').replace('£', '').strip()
            logger.debug(f"  Dopo rimozione simboli valuta: '{price_str}'")
            
            # Gestisci separatori decimali
            price_str = price_str.replace(',', '.')
            logger.debug(f"  Dopo sostituzione virgola: '{price_str}'")
            
            # Estrai solo numeri e punto decimale
            price_str = re.sub(r'[^\d.]', '', price_str)
            logger.debug(f"  Dopo estrazione numeri: '{price_str}'")
            
            result = float(price_str) if price_str else 0.0
            logger.debug(f"  Prezzo normalizzato finale: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Errore normalizzazione prezzo '{price}': {e}")
            return 0.0
    
    def _normalize_product_name(self, name: str) -> str:
        """Normalizza nome prodotto per confronto"""
        try:
            # DEBUG: Mostra il nome originale
            logger.debug(f"🔍 DEBUG - Normalizzazione nome: '{name}'")
            
            # Converti in minuscolo
            normalized = name.lower()
            logger.debug(f"  Dopo lowercase: '{normalized}'")
            
            # Rimuovi caratteri speciali ma mantieni spazi
            normalized = re.sub(r'[^\w\s]', ' ', normalized)
            logger.debug(f"  Dopo rimozione caratteri speciali: '{normalized}'")
            
            # Rimuovi spazi multipli
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            logger.debug(f"  Dopo rimozione spazi multipli: '{normalized}'")
            
            # Rimuovi parole comuni non significative
            stop_words = ['il', 'la', 'lo', 'gli', 'le', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'a', 'e', 'o', 'ma', 'se', 'che', 'come', 'quando', 'dove', 'perché']
            words = normalized.split()
            original_words = words.copy()
            words = [w for w in words if w not in stop_words and len(w) > 2]
            logger.debug(f"  Parole originali: {original_words}")
            logger.debug(f"  Parole dopo rimozione stop words: {words}")
            
            final_result = ' '.join(words)
            logger.debug(f"  Nome normalizzato finale: '{final_result}'")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Errore normalizzazione nome '{name}': {e}")
            return name.lower()
    
    def _normalize_brand(self, brand: str) -> str:
        """Normalizza brand per confronto"""
        try:
            if not brand:
                logger.debug(f"🔍 DEBUG - Brand vuoto, ritorno stringa vuota")
                return ""
            
            # DEBUG: Mostra il brand originale
            logger.debug(f"🔍 DEBUG - Normalizzazione brand: '{brand}'")
            
            # Converti in minuscolo e rimuovi spazi extra
            normalized = brand.lower().strip()
            logger.debug(f"  Dopo lowercase e strip: '{normalized}'")
            
            # Rimuovi caratteri speciali
            normalized = re.sub(r'[^\w\s]', '', normalized)
            logger.debug(f"  Dopo rimozione caratteri speciali: '{normalized}'")
            
            logger.debug(f"  Brand normalizzato finale: '{normalized}'")
            return normalized
            
        except Exception as e:
            logger.error(f"❌ Errore normalizzazione brand '{brand}': {e}")
            return brand.lower() if brand else ""
    
    def _calculate_price_statistics(self, clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calcola statistiche prezzo per ogni cluster"""
        enriched_clusters = []
        
        for cluster in clusters:
            try:
                products = cluster['products']
                prices = [p['normalized_price'] for p in products if p['normalized_price'] > 0]
                
                if len(prices) == 0:
                    continue
                
                # Statistiche prezzo
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                price_range = max_price - min_price
                price_variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
                
                # Trova prodotti con prezzo min/max
                cheapest_product = min(products, key=lambda p: p['normalized_price'])
                most_expensive_product = max(products, key=lambda p: p['normalized_price'])
                
                # Calcola differenze percentuali
                price_differences = []
                for i, product1 in enumerate(products):
                    for product2 in products[i+1:]:
                        price1 = product1['normalized_price']
                        price2 = product2['normalized_price']
                        if price1 > 0 and price2 > 0:
                            diff_percent = abs(price1 - price2) / min(price1, price2) * 100
                            price_differences.append({
                                'product1': product1['original_name'],
                                'product2': product2['original_name'],
                                'price1': price1,
                                'price2': price2,
                                'difference': abs(price1 - price2),
                                'difference_percent': diff_percent
                            })
                
                enriched_cluster = {
                    **cluster,
                    'price_statistics': {
                        'min_price': min_price,
                        'max_price': max_price,
                        'avg_price': round(avg_price, 2),
                        'price_range': round(price_range, 2),
                        'price_variance': round(price_variance, 2),
                        'price_differences': sorted(price_differences, key=lambda x: x['difference_percent'], reverse=True)
                    },
                    'cheapest_product': cheapest_product,
                    'most_expensive_product': most_expensive_product,
                    'savings_opportunity': round(max_price - min_price, 2)
                }
                
                enriched_clusters.append(enriched_cluster)
                
            except Exception as e:
                logger.warning(f"⚠️ Errore calcolo statistiche cluster: {e}")
                continue
        
        return enriched_clusters
    
    def _calculate_overall_statistics(self, clusters: List[Dict[str, Any]], all_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcola statistiche generali del confronto"""
        try:
            total_products = len(all_products)
            comparable_products = sum(len(cluster['products']) for cluster in clusters)
            
            # Statistiche prezzo globali
            all_prices = [p['normalized_price'] for p in all_products if p['normalized_price'] > 0]
            
            stats = {
                'total_products': total_products,
                'comparable_products': comparable_products,
                'match_percentage': round((comparable_products / total_products * 100), 2) if total_products > 0 else 0,
                'total_clusters': len(clusters),
                'avg_cluster_size': round(comparable_products / len(clusters), 2) if clusters else 0,
                'price_statistics': {
                    'min_price': min(all_prices) if all_prices else 0,
                    'max_price': max(all_prices) if all_prices else 0,
                    'avg_price': round(sum(all_prices) / len(all_prices), 2) if all_prices else 0
                },
                'total_savings_opportunity': sum(cluster.get('savings_opportunity', 0) for cluster in clusters),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Errore calcolo statistiche generali: {e}")
            return {}
    
    async def _fallback_textual_comparison(self, products_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback al confronto testuale se AI fallisce"""
        try:
            logger.info("🔄 Usando confronto testuale di fallback")
            logger.info(f"🔍 DEBUG - Prodotti per fallback: {len(products_data)}")
            
            # DEBUG: Mostra i primi 3 prodotti per fallback
            for i, product in enumerate(products_data[:3]):
                logger.info(f"  Prodotto fallback {i+1}: '{product.get('name', 'N/A')}' da {product.get('source', 'N/A')}")
            
            # Fallback semplificato senza dipendenze esterne
            logger.info("🔄 Fallback semplificato - confronto testuale base")
            
            # Confronto testuale semplice
            matches = []
            for i, product1 in enumerate(products_data):
                for j, product2 in enumerate(products_data[i+1:], i+1):
                    # Confronto semplice per nome e brand
                    name1 = product1.get('name', '').lower()
                    name2 = product2.get('name', '').lower()
                    brand1 = product1.get('brand', '').lower()
                    brand2 = product2.get('brand', '').lower()
                    
                    # Se stesso brand e nome simile
                    if brand1 and brand2 and brand1 == brand2:
                        similarity = SequenceMatcher(None, name1, name2).ratio()
                        if similarity > 0.6:  # Soglia di similarità
                            matches.append({
                                'products': [product1, product2],
                                'similarity_score': similarity,
                                'common_features': ['stesso brand', 'nome simile'],
                                'group_id': len(matches) + 1
                            })
            
            logger.info(f"✅ DEBUG - Fallback testuale completato: {len(matches)} match trovati")
            
            return {
                "success": True,
                "matches": matches,
                "statistics": {
                    "total_products": len(products_data),
                    "comparable_products": sum(len(match['products']) for match in matches),
                    "analysis_method": "textual_fallback"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Errore anche nel fallback testuale: {e}")
            logger.error(f"🔍 DEBUG - Stack trace completo: {e}")
            return {
                "success": False,
                "error": f"Errore confronto: {str(e)}",
                "matches": [],
                "statistics": {}
            }

# Test del sistema
async def test_ai_comparator():
    """Test del sistema AI Product Comparator"""
    try:
        comparator = AIProductComparator()
        
        # Dati di test
        test_products = [
            {
                'name': 'iPhone 15 Pro 128GB Titanio Naturale',
                'price': '1.199,00€',
                'brand': 'Apple',
                'source': 'amazon.it'
            },
            {
                'name': 'Apple iPhone 15 Pro 128GB Titanio Naturale',
                'price': '1.189,00€',
                'brand': 'Apple',
                'source': 'mediaworld.it'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra 256GB Titanio Grigio',
                'price': '1.399,00€',
                'brand': 'Samsung',
                'source': 'unieuro.it'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra 256GB Titanio Grigio',
                'price': '1.379,00€',
                'brand': 'Samsung',
                'source': 'amazon.it'
            }
        ]
        
        print("🧪 Test AI Product Comparator...")
        result = await comparator.compare_products_ai(test_products)
        
        print(f"✅ Risultato test: {result['success']}")
        print(f"📊 Gruppi trovati: {len(result['matches'])}")
        print(f"📈 Prodotti confrontabili: {result['comparable_products']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_ai_comparator()) 