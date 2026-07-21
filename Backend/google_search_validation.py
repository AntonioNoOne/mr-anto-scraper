#!/usr/bin/env python3

"""
Google Search Integration - Validazione / confronto mixin
=========================================================

Contiene i metodi di validazione e filtraggio dei risultati, il calcolo
dello score di rilevanza, la formattazione dei venditori alternativi e il
confronto prezzi. Estratto da google_search_integration.py per rispettare il
limite di lunghezza dei file. Nessuna modifica di logica: solo spostamento.
"""

import re
import logging
from typing import Dict, List, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class _ValidationMixin:
    """Metodi di validazione, scoring, formattazione e confronto prezzi."""

    def _validate_and_filter_results(self, results: List[Dict[str, Any]], original_product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida e filtra i risultati"""
        validated = []

        logger.info(f"🔍 DEBUG: === INIZIO VALIDAZIONE DETTAGLIATA ===")
        logger.info(f"🔍 DEBUG: Risultati da validare: {len(results)}")

        # Rimuovi duplicati prima della validazione
        seen_titles = set()
        unique_results = []

        for result in results:
            title_normalized = result.get('name', '').lower().strip()
            if title_normalized not in seen_titles and len(title_normalized) >= 3:
                seen_titles.add(title_normalized)
                unique_results.append(result)

        logger.info(f"🔍 DEBUG: Risultati unici dopo rimozione duplicati: {len(unique_results)}")

        for i, result in enumerate(unique_results):
            try:
                logger.info(f"🔍 DEBUG: Validando risultato {i+1}: {result.get('name', 'N/A')[:50]}")

                url = result.get('url', '')
                if not url:
                    logger.info(f"🔍 DEBUG: Risultato {i+1} scartato - URL vuoto")
                    continue

                # Valida URL
                if not self._is_valid_url(url):
                    logger.info(f"🔍 DEBUG: Risultato {i+1} scartato - URL non valido: {url}")
                    continue

                # Filtro junk: social, forum, recensioni, marketplace esteri
                if self._is_junk_domain(url):
                    logger.info(f"🔍 DEBUG: Risultato {i+1} scartato - dominio non pertinente: {url}")
                    continue

                # Calcola score di validazione
                score = self._calculate_validation_score(result, original_product)
                logger.info(f"🔍 DEBUG: Risultato {i+1} - Score: {score}")

                if score >= 0.20:  # Soglia ridotta per includere più risultati validi
                    result['validation_score'] = score
                    validated.append(result)
                    logger.info(f"🔍 DEBUG: Risultato {i+1} VALIDATO - Score: {score} - Titolo: {result.get('name', 'N/A')[:50]}")
                else:
                    logger.info(f"🔍 DEBUG: Risultato {i+1} scartato - Score troppo basso: {score}")

            except Exception as e:
                logger.error(f"❌ Errore validazione risultato {i+1}: {e}")
                continue

        # Ordina per score
        validated.sort(key=lambda x: x.get('validation_score', 0), reverse=True)

        logger.info(f"🔍 DEBUG: === FINE VALIDAZIONE DETTAGLIATA ===")
        logger.info(f"🔍 DEBUG: Risultati validati: {len(validated)}")

        return validated[:self.max_results]

    def _is_valid_url(self, url: str) -> bool:
        """Verifica se l'URL è valido"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False

    # Domini non pertinenti al confronto prezzi IT: social, forum, recensioni,
    # aggregatori/marketplace esteri. Scartati dai risultati.
    _JUNK_DOMAINS = (
        "reddit.com", "medium.com", "quora.com", "youtube.com", "facebook.com",
        "instagram.com", "twitter.com", "x.com", "pinterest.", "tiktok.com",
        "wikipedia.org", "wikihow", "tomshardware", "hdblog", "ilpost",
        # marketplace/recensioni esteri (non utili per prezzi in Italia)
        "amazon.com", "flipkart.com", "walmart.com", "bestbuy.com", "target.com",
        "thegioididong", "shopdunk", "24hstore", "ceneo.pl", "arukereso",
        "yahoo.co", "yahoo.com", "aliexpress", "backmarket.com",
    )

    def _is_junk_domain(self, url: str) -> bool:
        """True se il dominio non è un venditore pertinente (social/forum/estero)."""
        u = (url or "").lower()
        return any(j in u for j in self._JUNK_DOMAINS)

    def _calculate_validation_score(self, result: Dict[str, Any], original_product: Dict[str, Any]) -> float:
        """Calcola score di validazione per un risultato - SOLO VICINANZA AL TESTO"""
        score = 0.0

        try:
            title = result.get('name', '').lower()
            description = result.get('description', '').lower()

            logger.info(f"🔍 DEBUG: Calcolo score per: {title[:50]}")
            logger.info(f"🔍 DEBUG: Prodotto originale: {original_product.get('name', 'N/A')[:50]}")

            # Score SOLO per rilevanza del contenuto (vicinanza al testo)
            product_name = original_product.get('name', '').lower()
            logger.info(f"🔍 DEBUG: Product name: '{product_name}'")

            if product_name:
                # Cerca parole chiave nel titolo o descrizione (includi numeri ma scarta articoli)
                product_words = []
                for word in product_name.split():
                    word = word.strip()
                    if len(word) > 0:
                        # Includi numeri (anche se corti)
                        if word.isdigit() or word.replace('.', '').replace(',', '').isdigit():
                            product_words.append(word)
                        # Includi parole normali (ma scarta articoli comuni)
                        elif len(word) > 2 and word.lower() not in ['il', 'la', 'lo', 'gli', 'le', 'un', 'una', 'uno', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'e', 'o', 'ma', 'se', 'che', 'chi', 'cosa', 'dove', 'quando', 'come', 'perché']:
                            product_words.append(word)
                logger.info(f"🔍 DEBUG: Product words: {product_words}")

                matches = 0
                for word in product_words:
                    # LOGICA MIGLIORATA - Riconosce varianti delle parole
                    title_words = title.lower().split()
                    description_words = description.lower().split()

                    word_lower = word.lower()

                    # Controlla se la parola è presente nel TITOLO (esatta o come parte di una parola)
                    title_match = False

                    # 1. Cerca parola esatta
                    exact_match = any(w.strip('.,!?;:()[]{}"\'-') == word_lower for w in title_words)

                    # 2. Cerca parola come parte di altre parole (es: "128" in "128GB")
                    partial_match = any(word_lower in w.strip('.,!?;:()[]{}"\'-') for w in title_words)

                    # 3. Cerca varianti comuni (es: "128" -> "128gb", "128 gb", "128GB")
                    variant_matches = []
                    if word_lower.isdigit():
                        # Per numeri, cerca varianti con unità comuni
                        variants = [word_lower, word_lower + 'gb', word_lower + ' gb', word_lower + 'gb', word_lower + 'tb', word_lower + ' tb']
                        for variant in variants:
                            if any(variant in w.strip('.,!?;:()[]{}"\'-') for w in title_words):
                                variant_matches.append(variant)
                    else:
                        # Per parole, cerca varianti con suffissi comuni
                        variants = [word_lower, word_lower + 's', word_lower + 'es', word_lower + 'ing']
                        for variant in variants:
                            if any(variant in w.strip('.,!?;:()[]{}"\'-') for w in title_words):
                                variant_matches.append(variant)

                    title_match = exact_match or partial_match or len(variant_matches) > 0

                    # DEBUG: Log dettagliato per capire i match
                    logger.info(f"🔍 DEBUG: Cercando '{word_lower}' in titolo: {title_words[:10]}")
                    logger.info(f"🔍 DEBUG: Match esatto: {exact_match}")
                    logger.info(f"🔍 DEBUG: Match parziale: {partial_match}")
                    logger.info(f"🔍 DEBUG: Varianti trovate: {variant_matches}")

                    if title_match:
                        matching_words = [w for w in title_words if word_lower in w.strip('.,!?;:()[]{}"\'-')]
                        logger.info(f"🔍 DEBUG: ✅ MATCH TITOLO: '{word_lower}' trovata come: {matching_words}")
                    else:
                        logger.info(f"🔍 DEBUG: ❌ PAROLA '{word_lower}' NON trovata nel titolo")

                    if title_match:
                        matches += 1
                        logger.info(f"🔍 DEBUG: Parola '{word}' trovata in titolo (esatta/parziale/variante)")
                    else:
                        logger.info(f"🔍 DEBUG: Parola '{word}' NON trovata in titolo")

                # LOGICA COMPLETAMENTE NUOVA - FORZA AGGIORNAMENTO
                logger.info(f"🔍 DEBUG: *** NUOVA LOGICA ATTIVA *** Matches trovati: {matches}")

                # LOGICA CON PENALIZZAZIONE - Solo risultati con TUTTE le parole sono validi
                total_words = len(product_words)
                logger.info(f"🔍 DEBUG: *** LOGICA PENALIZZANTE *** Trovate {matches}/{total_words} parole")

                if matches == total_words:
                    # TUTTE le parole trovate = Score alto
                    if total_words == 1:
                        score = 0.60  # Una parola, ma è l'unica richiesta
                    elif total_words == 2:
                        score = 0.80  # Due parole, entrambe trovate
                    else:
                        score = 0.90  # Tre o più parole, tutte trovate
                    logger.info(f"🔍 DEBUG: *** TUTTE LE PAROLE TROVATE *** Score: {score} ({matches}/{total_words})")
                elif matches > 0:
                    # PENALIZZAZIONE RIDOTTA - Solo alcune parole trovate
                    penalty_score = (matches / total_words) * 0.50  # Max 50% se manca qualche parola
                    score = penalty_score
                    logger.info(f"🔍 DEBUG: *** PENALIZZAZIONE APPLICATA *** Score: {score} ({matches}/{total_words} parole)")
                    logger.info(f"🔍 DEBUG: *** PAROLE MANCANTI *** Mancano {total_words - matches} parole su {total_words}")
                else:
                    # Nessuna parola trovata = Score ZERO
                    score = 0.0
                    logger.info(f"🔍 DEBUG: *** NESSUNA PAROLA TROVATA *** Score: 0.0")
            else:
                logger.warning(f"🔍 DEBUG: Product name vuoto! Original product: {original_product}")
                score = 0.0  # Score ZERO se non c'è nome prodotto

            # RIMOSSO BONUS PER TITOLO LUNGO - Punteggio basato solo sulle parole trovate
            logger.info(f"🔍 DEBUG: Nessun bonus aggiuntivo - punteggio basato solo su parole trovate")

        except Exception as e:
            logger.error(f"❌ Errore calcolo score: {e}")

        logger.info(f"🔍 DEBUG: Score finale: {score}")
        return min(score, 1.0)

    def _format_alternative_vendors(self, validated_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formatta i venditori alternativi per la UI"""
        vendors = []

        for result in validated_results:
            validation_score = result.get('validation_score', 0)

            # NON troncare URL - gli URL di tracking DuckDuckGo sono lunghi ma funzionanti
            url = result.get('url', '#')

            vendor = {
                'name': result.get('name', 'Prodotto'),
                'price': result.get('price', 'Prezzo non disponibile'),
                'description': result.get('description', ''),
                'url': url,
                'brand': result.get('brand', ''),
                'source': result.get('site', 'Venditore'),
                'validation_score': validation_score
            }

            logger.info(f"🔍 DEBUG: Vendor '{vendor['name'][:30]}' - Score: {validation_score}")
            vendors.append(vendor)

        # Ordina per score di validazione
        vendors.sort(key=lambda x: x.get('validation_score', 0), reverse=True)

        return vendors

    async def _compare_prices(self, original_product: Dict[str, Any], alternative_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Confronta prezzi tra prodotto originale e alternative"""
        try:
            original_price = self._normalize_price(original_product.get('price', '0'))

            if original_price <= 0:
                return {
                    "price_comparison": "Impossibile confrontare prezzi",
                    "best_deal": None,
                    "price_range": None
                }

            # Analizza prezzi alternativi
            valid_prices = []
            for product in alternative_products:
                price = product.get('price_numeric', 0)
                if price > 0:
                    valid_prices.append(price)
                    product['normalized_price'] = price

            if not valid_prices:
                return {
                    "price_comparison": "Nessun prezzo alternativo valido",
                    "best_deal": None,
                    "price_range": None
                }

            # Calcola statistiche
            min_price = min(valid_prices)
            max_price = max(valid_prices)
            avg_price = sum(valid_prices) / len(valid_prices)

            # Trova miglior affare
            best_deal = None
            if min_price < original_price:
                best_deal = {
                    "savings": original_price - min_price,
                    "savings_percentage": ((original_price - min_price) / original_price) * 100,
                    "price": min_price
                }

            return {
                "price_comparison": "Confronto completato",
                "original_price": original_price,
                "min_alternative_price": min_price,
                "max_alternative_price": max_price,
                "average_alternative_price": avg_price,
                "best_deal": best_deal,
                "total_alternatives": len(valid_prices)
            }

        except Exception as e:
            logger.error(f"❌ Errore confronto prezzi: {e}")
            return {
                "price_comparison": f"Errore confronto: {str(e)}",
                "best_deal": None,
                "price_range": None
            }

    def _normalize_price(self, price: str) -> float:
        """Normalizza il prezzo in formato numerico"""
        try:
            if not price:
                return 0.0

            # Rimuovi simboli di valuta e spazi
            price_clean = re.sub(r'[€$£\s]', '', str(price))

            # Gestisci virgole e punti decimali
            price_clean = price_clean.replace(',', '.')

            # Estrai solo numeri e punto decimale
            price_match = re.search(r'[\d.]+', price_clean)
            if price_match:
                return float(price_match.group())

            return 0.0

        except Exception as e:
            logger.error(f"❌ Errore normalizzazione prezzo '{price}': {e}")
            return 0.0
