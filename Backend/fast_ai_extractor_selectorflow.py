"""Mixin dei flussi di estrazione delegati da _extract_single_attempt.

Contiene blocchi estratti VERBATIM (solo de-indentati) dal metodo monolitico
_extract_single_attempt per rispettare il limite di 900 righe per file.
Il comportamento e' invariato: i blocchi delegati terminavano gia' con return.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


class _SelectorFlowMixin:
    """Flussi selettori-DB, fallback AI e coda legacy (non raggiungibile)."""

    async def _try_db_selectors(self, page, url, domain, browser, stop_flag=None):
        """Tentativo con selettori salvati nel database.

        Blocco estratto verbatim da _extract_single_attempt: restituisce il dict
        di risultato quando il blocco originale faceva return, altrimenti None
        (il chiamante prosegue con i selettori universali).
        """
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

    async def _fallback_ai_parsing(self, page, browser, url, domain, stop_flag=None):
        """Fallback: auto-apprendimento + AI parsing diretto.

        Blocco estratto verbatim da _extract_single_attempt (terminava sempre con
        return e catturava internamente le eccezioni).
        """
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

    async def _legacy_extract_tail(self, page=None, browser=None, url=None,
                                   domain=None, stop_flag=None,
                                   best_selector=None, best_count=0):
        """Coda legacy NON RAGGIUNGIBILE dell'originale _extract_single_attempt.

        Nel file monolitico questo codice seguiva un blocco che terminava sempre
        con return, quindi non veniva mai eseguito. Preservato verbatim (solo
        de-indentato) per non alterare il sorgente; non viene mai chiamato.
        """
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
