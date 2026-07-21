"""Mixin di parsing/detection per FastAIExtractor."""

import asyncio
from typing import Dict, List, Any, Optional


class _ParsingMixin:
    """Metodi di detection contenuto, pulizia testo e parsing AI dei prodotti."""

    def _detect_real_estate_site_from_content(self, content_text: str) -> bool:
        """Rileva automaticamente se è un sito immobiliare dal contenuto (multilingua)"""
        try:
            content_lower = content_text.lower()
            
            # 🔍 LOG DETECTION: Mostra cosa viene analizzato
            print(f"🔍 Analisi contenuto per detection real estate...")
            
            # Indicatori FORTI per siti immobiliari (più specifici)
            strong_real_estate_indicators = [
                # Italiano - molto specifici
                'bilocale', 'trilocale', 'quadrilocale', 'monolocale',
                'appartamento', 'villa', 'casa indipendente', 'attico',
                'mansarda', 'loft', 'rustico', 'casale', 'masseria',
                'vendita immobili', 'affitto immobili', 'agenzia immobiliare',
                'annunci immobiliari', 'cerca casa', 'trova casa',
                
                # Inglese - molto specifici
                'studio apartment', 'one bedroom', 'two bedroom', 'three bedroom',
                'penthouse', 'townhouse', 'duplex', 'condo', 'condominium',
                'real estate agency', 'property for sale', 'property for rent',
                'house hunting', 'find home', 'real estate listings',
                
                # Francese - molto specifici
                'studio', 'deux pièces', 'trois pièces', 'appartement',
                'maison individuelle', 'maison de ville', 'loft',
                'agence immobilière', 'bien immobilier', 'achat maison',
                
                # Tedesco - molto specifici
                'ein zimmer', 'zwei zimmer', 'drei zimmer', 'wohnung',
                'einfamilienhaus', 'reihenhaus', 'loft', 'penthouse',
                'immobilienbüro', 'immobilienangebote', 'haus kaufen',
                
                # Spagnolo - molto specifici
                'estudio', 'dos habitaciones', 'tres habitaciones',
                'apartamento', 'casa individual', 'casa adosada',
                'agencia inmobiliaria', 'inmuebles en venta', 'comprar casa'
            ]
            
            # Indicatori DEBOLI per siti immobiliari (generici, da usare con cautela)
            weak_real_estate_indicators = [
                'mq', 'metri quadri', 'bagno', 'bagni', 'camera', 'camere',
                'piano', 'vendita', 'affitto', 'immobile', 'proprietà', 'terreno',
                'sqm', 'square meters', 'bathroom', 'bathrooms', 'bedroom', 'bedrooms',
                'floor', 'for sale', 'for rent', 'property', 'land', 'acres', 'sq ft'
            ]
            
            # Match per PAROLA INTERA (word boundary): evita falsi positivi da
            # substring (es. 'ml' dentro '.html', 'g ' dentro '16gb', 'camera'
            # dentro 'fotocamera') che facevano classificare notebook come immobili.
            import re
            def _count(indicators):
                n = 0
                for ind in indicators:
                    if re.search(r'\b' + re.escape(ind.strip()) + r'\b', content_lower):
                        n += 1
                return n

            strong_score = _count(strong_real_estate_indicators)
            weak_score = _count(weak_real_estate_indicators)
            total_score = (strong_score * 3) + weak_score

            print(f"🔍 Punteggio indicatori forti: {strong_score}")
            print(f"🔍 Punteggio indicatori deboli: {weak_score}")
            print(f"🔍 Punteggio totale: {total_score}")

            # Servono almeno DUE indicatori forti distinti (appartamento, bilocale,
            # trilocale, villa, attico...). Un solo match forte è spesso un falso
            # positivo (es. 'studio'/'loft' presenti in prodotti elettronici come
            # "Mac Studio"). Una vera pagina immobiliare ne contiene sempre parecchi;
            # una pagina e-commerce praticamente mai.
            is_real_estate = strong_score >= 2

            print(f"🔍 Rilevato come real estate: {is_real_estate}")

            return is_real_estate
            
        except Exception as e:
            print(f"⚠️ Errore detection sito immobiliare: {e}")
            return False

    def _detect_food_site_from_content(self, content_text: str) -> bool:
        """Rileva automaticamente se è un sito alimentare dal contenuto"""
        try:
            content_lower = content_text.lower()
            
            # Indicatori universali per siti alimentari (multilingua)
            food_indicators = [
                # Italiano
                'kg', 'g ', 'litri', 'ml', 'prezzo al kg', 'prezzo al litro',
                'alimentari', 'supermercato', 'spesa', 'cibo', 'frutta', 'verdura',
                'carne', 'pesce', 'latte', 'formaggio', 'pane', 'pasta',
                
                # Inglese
                'kg', 'g ', 'liters', 'ml', 'price per kg', 'price per liter',
                'grocery', 'supermarket', 'food', 'fresh', 'meat', 'fish',
                'milk', 'cheese', 'bread', 'pasta', 'vegetables', 'fruits',
                
                # Francese
                'kg', 'g ', 'litres', 'ml', 'prix au kg', 'prix au litre',
                'alimentation', 'supermarché', 'nourriture', 'frais', 'viande',
                
                # Tedesco
                'kg', 'g ', 'liter', 'ml', 'preis pro kg', 'preis pro liter',
                'lebensmittel', 'supermarkt', 'nahrung', 'frisch', 'fleisch'
            ]
            
            # Conta quanti indicatori alimentari sono presenti
            food_score = sum(1 for indicator in food_indicators if indicator in content_lower)
            
            # Se ci sono molti indicatori alimentari, è probabilmente un sito alimentare
            return food_score >= 3
            
        except Exception as e:
            print(f"⚠️ Errore detection sito alimentare: {e}")
            return False

    def _clean_extracted_text(self, text: str) -> str:
        """Pulisce il testo estratto da link lunghi e contenuto non necessario"""
        import re
        
        text = re.sub(r'https?://[^\s]{100,}', '[LINK]', text)
        text = re.sub(r'[?&][^=]{50,}=[^&\s]{50,}', '', text)
        text = re.sub(r'([A-Za-z0-9])\1{20,}', r'\1', text)
        
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if len(line.strip()) > 200:
                cleaned_lines.append(line[:200].strip() + "...")
            else:
                cleaned_lines.append(line.strip())
        
        cleaned_text = '\n'.join(cleaned_lines)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        return cleaned_text.strip()

    async def _test_saved_selectors(self, page, saved_selectors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Testa selettori salvati e restituisce il migliore"""
        try:
            # Ordina per qualità e success rate
            sorted_selectors = sorted(saved_selectors, 
                                    key=lambda x: (x.get('quality_score', 0), x.get('success_rate', 0)), 
                                    reverse=True)
            
            for selector_data in sorted_selectors:
                # Prova prima product_container
                if selector_data.get('product_container'):
                    selector = selector_data['product_container']
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0 and len(elements) <= 100:
                            test_text = await elements[0].inner_text()
                            if len(test_text) > 20:
                                return selector_data  # Ritorna tutto l'oggetto selettore
                    except Exception as e:
                        continue
                
                # Fallback su altri selettori
                for selector_type in ['title', 'price']:
                    if selector_data.get(selector_type):
                        selector = selector_data[selector_type]
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements and len(elements) > 0 and len(elements) <= 100:
                                test_text = await elements[0].inner_text()
                                if len(test_text) > 20:
                                    return selector_data
                        except Exception as e:
                            continue
            
            return None
            
        except Exception as e:
            return None

    async def _ai_parse_products(self, content_text: str, url: str = "", stop_flag: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Parse AI veloce del contenuto estratto con chunking intelligente"""
        try:
            # CHECKPOINT 4: Controlla se deve fermarsi prima dell'elaborazione AI
            if stop_flag and stop_flag.get('stop'):
                print(f"🛑 Elaborazione AI fermata per {url}")
                return []
                
            if len(content_text) > 15000:
                try:
                    products = await self._process_single_chunk(content_text, url, stop_flag)
                    
                    if products and len(products) >= 5:
                        return products
                    else:
                        raise Exception("Not enough products found")
                        
                except Exception as e:
                    # Fallback a chunk multipli
                    
                    if len(content_text) > 25000:
                        num_chunks = 6
                        chunk_size = len(content_text) // num_chunks
                    elif len(content_text) > 15000:
                        num_chunks = 4
                        chunk_size = len(content_text) // num_chunks
                    else:
                        num_chunks = 3
                        chunk_size = len(content_text) // num_chunks
                    
                    # Preparazione chunk
                    
                    chunks = []
                    for i in range(num_chunks):
                        start = i * chunk_size
                        end = start + chunk_size if i < num_chunks - 1 else len(content_text)
                        
                        if i < num_chunks - 1:
                            search_start = min(end, len(content_text) - 100)
                            search_end = min(end + 500, len(content_text))
                            
                            separators = ["---ITEM---", "---PRODUCT---", "---SEPARATOR---"]
                            found_separator = False
                            
                            for separator in separators:
                                next_separator = content_text.find(separator, search_start, search_end)
                                if next_separator != -1:
                                    end = next_separator + len(separator)
                                    found_separator = True
                                    break
                            
                            if not found_separator:
                                next_euro = content_text.find("€", search_start, search_end)
                                if next_euro != -1:
                                    line_end = content_text.find("\n", next_euro, search_end)
                                    if line_end != -1:
                                        end = line_end
                                    else:
                                        end = next_euro + 1
                        
                        chunk = content_text[start:end]
                        chunks.append(chunk)
                    
                    # CHECKPOINT 5: stop prima di lanciare i chunk
                    if stop_flag and stop_flag.get('stop'):
                        print(f"🛑 Elaborazione chunk fermata per {url}")
                        return []

                    # Elabora i chunk IN PARALLELO (asyncio.gather) invece che in
                    # serie: le chiamate AI sono I/O-bound, girano insieme -> molto
                    # piu' veloce (da ~N*t a ~t).
                    async def _proc_chunk(ch):
                        try:
                            return await self._process_single_chunk(ch, url, stop_flag)
                        except Exception:
                            return []

                    chunk_results = await asyncio.gather(*[_proc_chunk(c) for c in chunks])
                    all_products = []
                    for cp in chunk_results:
                        all_products.extend(cp or [])
                    
                    # Finalizzazione risultati
                    
                    unique_products = []
                    seen_names = set()
                    for product in all_products:
                        name = product.get('name', '').lower()
                        if name and name not in seen_names:
                            unique_products.append(product)
                            seen_names.add(name)
                    
                    # Completato
                    
                    return unique_products
            else:
                # Chunk singolo
                
                result = await self._process_single_chunk(content_text, url, stop_flag)
                
                return result
                
        except Exception as e:
            return []

    async def _process_single_chunk(self, content_text: str, url: str = "", stop_flag: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Processa un singolo chunk di contenuto"""
        try:
            content_lower = content_text.lower()
            
            # Detection automatica universale basata sul contenuto
            is_real_estate = self._detect_real_estate_site_from_content(content_text)
            
            # 🔍 LOG DETECTION: Mostra cosa viene rilevato
            print(f"\n🔍 === DETECTION AUTOMATICA SITO ===")
            print(f"📊 Rilevato come real estate: {is_real_estate}")
            print(f"🔍 Contenuto analizzato: {len(content_text)} caratteri")
            print(f"🔤 Primi 200 caratteri: '{content_text[:200]}...'")
            print(f"🔍 === FINE DETECTION ===\n")
            
            if is_real_estate:
                import re
                price_patterns = [
                    r'(\d{1,3}(?:\.\d{3})*)\s*€',
                    r'€\s*(\d{1,3}(?:\.\d{3})*)',
                    r'(\d{1,3}(?:,\d{3})*)\s*€',
                    r'€\s*(\d{1,3}(?:,\d{3})*)',
                ]
                
                all_prices = []
                for pattern in price_patterns:
                    matches = re.findall(pattern, content_text)
                    all_prices.extend(matches)
                
                unique_prices = list(set(all_prices))
                
                content_chunks = []
                lines = content_text.split('\n')
                current_chunk = []
                
                for line in lines:
                    current_chunk.append(line)
                    if '€' in line and 'mq' in line and len('\n'.join(current_chunk)) > 200:
                        content_chunks.append('\n'.join(current_chunk))
                        current_chunk = []
                
                if current_chunk:
                    content_chunks.append('\n'.join(current_chunk))
                
                if len(content_chunks) > 1:
                    main_content = '\n'.join(content_chunks)
                else:
                    main_content = content_text[:15000]
                
                prompt = f"""ANALYZE this real estate content and EXTRACT ALL PROPERTIES with DETAILED CHARACTERISTICS:

{main_content}

INSTRUCTIONS:
1. Count how many different prices you see (€249.000, €138.000, €169.000, etc.)
2. For EACH price, create ONE property entry with ALL available details
3. Extract these fields for each property:
   - name: Property name/description
   - price: Exact price in € format
   - address: Full address if available
   - sqm: Square meters (mq)
   - rooms: Number of rooms (bilocale, trilocale, etc.)
   - bathrooms: Number of bathrooms
   - floor: Floor number if mentioned
   - type: Property type (appartamento, villa, casa, etc.)
   - condition: Condition if mentioned (nuovo, ristrutturato, etc.)
   - features: Any special features (giardino, terrazza, cantina, etc.)

4. Look for patterns like:
   - "Bilocale 60mq" → rooms: "2", sqm: "60"
   - "Via Roma 15" → address: "Via Roma 15"
   - "2 bagni" → bathrooms: "2"
   - "3° piano" → floor: "3"

Return this JSON format with ALL properties and their characteristics:
{{"products": [{{"name": "Property Description", "price": "€XXX.XXX", "address": "Full Address", "sqm": "XX", "rooms": "X", "bathrooms": "X", "floor": "X", "type": "Property Type", "condition": "Condition", "features": "Special Features"}}]}}

CRITICAL: Extract as many properties as you can find. Count the prices and return that many properties with ALL available details."""
                
                # 🔍 LOG PROMPT: Mostra il prompt finale
                print(f"\n🚀 === PROMPT FINALE REAL ESTATE ===")
                print(f"📝 Prompt: {prompt[:500]}...")
                print(f"🚀 === FINE PROMPT ===\n")
            else:
                # Determina automaticamente se è un sito alimentare dal contenuto
                is_food_site = self._detect_food_site_from_content(content_text)
                
                if is_food_site:
                    price_kg_instruction = 'For "price_per_kg": include if the product shows "€X.XX/Kg" or "€X.XX / Kg". If it shows "0,00 €/Kg", use "Prezzo variabile".'
                else:
                    price_kg_instruction = 'For "price_per_kg": always use "0,00€" for non-food products (electronics, clothing, etc.).'
                
                main_content = content_text[:15000]
                
                prompt = f"""ANALYZE this e-commerce content and EXTRACT ALL REAL PRODUCTS with DETAILED CHARACTERISTICS:

{main_content}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. **ONLY extract products that have BOTH:**
   - A SPECIFIC product name (not generic categories)
   - A REAL price in € format (not placeholder prices)

2. **NEVER extract these items (they are NOT products):**
   - Navigation menu items or category names
   - Menu links or navigation elements
   - Items without specific product details
   - Items without real prices

3. **PRICE VALIDATION RULES:**
   - Price MUST be a real number like "€19,90" or "€1.499,90"
   - NEVER use placeholder prices like "€XX.XX" or "€0,00" unless it's actually free
   - If you cannot find a real price, DO NOT extract that item as a product
   - Price must be visible and clearly associated with the product

4. **PRODUCT VALIDATION RULES:**
   - Product name must be specific (not just "Computer", "Smartphone", "Lavatrici")
   - Must have product details or specifications
   - Must NOT be just a category or menu item
   - Must have a real, visible price

5. **For EACH VALID product, extract (INFER from the product name when not a separate field):**
   - name: Full product name
   - price: Exact price in € format (ONLY if you can see a real price) DON'T USE PLACEHOLDER PRICES or Invented prices!
   - brand: The manufacturer. ALWAYS infer it from the product name — it is almost
     always the first word/token (e.g. "HP 15-FC0110NL" -> "HP"; "ASUS Vivobook 16" ->
     "ASUS"; "APPLE MacBook" -> "APPLE"; "ACER Chromebook 314" -> "ACER"). Only leave
     empty if truly not identifiable.
   - model: The model code/identifier taken from the name (e.g. "HP 15-FC0110NL" ->
     "15-FC0110NL"; "ASUS Vivobook 16 F1607" -> "Vivobook 16 F1607").
   - weight: Weight if mentioned
   - price_per_kg: Price per kg if applicable
   - rating: Star rating if available
   - description: Product description
   - category: Product category (infer from context, e.g. "Notebook", "Smartphone")
   - availability: Stock status
   - warranty: Warranty info
   - specs: Technical specs present in the name/description (CPU, RAM, storage,
     screen size, etc.). Extract whatever is present, e.g. "Intel Core i5, 16GB, 512GB SSD, 15,6\"".

6. **Examples of what to EXTRACT:**
   ✅ Any product with a real name and real price
   ✅ "Samsung Display 6.9''" with price "€1.699,90"
   ✅ "iPhone 15 Pro 128GB" with price "€1.099,90"
   ✅ "Lattina Coca Cola 33cl" with price "€1,10"
   ✅ "Lavatrice Samsung 8kg" with price "€399,90" (if it's a real product, not menu)

7. **Examples of what to IGNORE:**
   ❌ "LAVATRICI CARICA FRONTALE" (just a menu category, no real price)
   ❌ "Computer" (generic category, no specific product)
   ❌ "Smartphone" (generic category, no specific product)
   ❌ Any menu navigation items without real prices

8. Look for patterns like:
- Product names with brands/models
- Prices in € format
- Product descriptions
- Technical specifications
- Weight information
- Rating stars

Return this JSON format with ONLY VALID PRODUCTS that have REAL PRICES:
{{"products": [{{"name": "Specific Product Name", "price": "€XX.XX", "brand": "Brand Name", "model": "Model Number", "weight": "Weight", "price_per_kg": "€X.XX/Kg", "rating": "X.X", "description": "Product description", "category": "Category", "availability": "In Stock", "warranty": "Warranty info", "specs": "Technical specs"}}]}}

FINAL CHECK: Before returning, verify that each product has a REAL name (not just a category) and a REAL price (not placeholder). If you cannot find a real price for an item, DO NOT include it in the results."""
                
                # 🔍 LOG PROMPT: Mostra il prompt finale
                print(f"\n🚀 === PROMPT FINALE E-COMMERCE ===")
                print(f"📝 Prompt: {prompt[:500]}...")
                print(f"🚀 === FINE PROMPT ===\n")

            response = await self.ai_analyzer._call_ai_with_fallback(prompt)
            
            if response and 'products' in response:
                products = response['products']
                return products
            else:
                return []
                
        except Exception as e:
            return []

    def _looks_like_product_content(self, text: str, url: str) -> bool:
        """Determina se il testo sembra contenuto di un prodotto"""
        try:
            text_lower = text.lower()
            
            # Indicatori comuni di prodotti
            product_indicators = [
                '€', '$', '£', 'prezzo', 'price', 'costo', 'cost',
                'acquista', 'buy', 'compra', 'add to cart', 'aggiungi',
                'stelle', 'stars', 'rating', 'recensioni', 'reviews',
                'disponibile', 'available', 'in stock', 'scorte',
                'spedizione', 'shipping', 'delivery', 'consegna'
            ]
            
            # Indicatori per immobili
            real_estate_indicators = [
                'mq', 'sqm', 'metri quadri', 'square meters',
                'bagno', 'bagni', 'bathroom', 'bathrooms',
                'camera', 'camere', 'bedroom', 'bedrooms',
                'piano', 'floor', 'via ', 'street', 'viale',
                'vendita', 'affitto', 'sale', 'rent',
                'bilocale', 'trilocale', 'quadrilocale'
            ]
            
            # Indicatori per e-commerce
            ecommerce_indicators = [
                'marca', 'brand', 'modello', 'model',
                'caratteristiche', 'features', 'specifiche', 'specs',
                'garanzia', 'warranty', 'assistenza', 'support',
                'kg', 'g', 'litri', 'ml', 'cm', 'mm'
            ]
            
            # Conta indicatori presenti
            product_score = sum(1 for indicator in product_indicators if indicator in text_lower)
            real_estate_score = sum(1 for indicator in real_estate_indicators if indicator in text_lower)
            ecommerce_score = sum(1 for indicator in ecommerce_indicators if indicator in text_lower)
            
            total_score = product_score + real_estate_score + ecommerce_score
            
            # Criteri standard per tutti i siti
            min_score = 2
            min_length = 30
            
            # Deve avere indicatori sufficienti e testo ragionevole
            return total_score >= min_score and len(text.strip()) > min_length and len(text.strip()) < 2000
            
        except:
            return False
