"""
Seed dati demo: popola il DB storico con prodotti realistici SE e' vuoto.

Serve per avere sempre qualcosa da mostrare (dashboard, confronto, ricerca)
anche su Render free dove il disco e' effimero e il DB si azzera ad ogni
restart/deploy. I prodotti veri estratti dagli scan si aggiungono a questi.
Molti prodotti sono ripetuti su piu' siti a prezzi diversi cosi' il confronto
prezzi ha subito dei match da mostrare.
"""

import logging

logger = logging.getLogger(__name__)


def _p(name, price, brand, model, category, source, rating=""):
    dominio = source
    slug = model.lower().replace(" ", "-")
    return {
        "name": name, "price": price, "brand": brand, "model": model,
        "category": category, "source": dominio, "rating": rating,
        "availability": "Disponibile",
        "url": f"https://www.{dominio}/p/{slug}",
    }


# Prodotti demo: stesso prodotto su piu' siti (per il confronto) + varieta'
SEED_PRODUCTS = [
    # iPhone 15 128GB (3 siti)
    _p("Apple iPhone 15 128GB Nero", "€ 799,00", "Apple", "iPhone 15 128GB", "Smartphone", "unieuro.it", "4.6"),
    _p("APPLE iPhone 15 128GB Nero", "€ 789,00", "Apple", "iPhone 15 128GB", "Smartphone", "mediaworld.it", "4.7"),
    _p("Apple iPhone 15 (128 GB) - Nero", "€ 779,00", "Apple", "iPhone 15 128GB", "Smartphone", "amazon.it", "4.7"),
    # HP 15-fc1007nl (2 siti)
    _p("HP 15-fc1007nl AI AMD Ryzen 5 7520U", "€ 529,00", "HP", "15-fc1007nl", "Notebook", "unieuro.it", "4.1"),
    _p("HP 15-fc1007nl Notebook AMD Ryzen 5", "€ 499,00", "HP", "15-fc1007nl", "Notebook", "mediaworld.it", "4.2"),
    # ASUS Vivobook 15 (2 siti)
    _p("ASUS Vivobook 15 F1504VA Intel Core 7", "€ 669,00", "ASUS", "Vivobook 15 F1504VA", "Notebook", "unieuro.it", "4.3"),
    _p("ASUS Vivobook 15 F1504VA-BQ232W", "€ 689,00", "ASUS", "Vivobook 15 F1504VA", "Notebook", "euronics.it", "4.0"),
    # Lenovo IdeaPad Slim 3 (2 siti)
    _p("Lenovo IdeaPad Slim 3 15IRU8 Core i5", "€ 699,00", "Lenovo", "IdeaPad Slim 3", "Notebook", "unieuro.it", "4.2"),
    _p("LENOVO IdeaPad Slim 3 15IRU8", "€ 679,00", "Lenovo", "IdeaPad Slim 3", "Notebook", "mediaworld.it", "4.4"),
    # Samsung Galaxy S24 (2 siti)
    _p("Samsung Galaxy S24 256GB", "€ 719,00", "Samsung", "Galaxy S24 256GB", "Smartphone", "mediaworld.it", "4.6"),
    _p("Samsung Galaxy S24 256GB Nero", "€ 699,00", "Samsung", "Galaxy S24 256GB", "Smartphone", "amazon.it", "4.5"),
    # Cuffie Sony (2 siti)
    _p("Sony WH-1000XM5 Cuffie Wireless", "€ 329,00", "Sony", "WH-1000XM5", "Audio", "amazon.it", "4.8"),
    _p("SONY WH-1000XM5 Noise Cancelling", "€ 349,00", "Sony", "WH-1000XM5", "Audio", "mediaworld.it", "4.7"),
    # Varieta' a sito singolo
    _p("Dyson V15 Detect Absolute", "€ 599,00", "Dyson", "V15 Detect", "Elettrodomestici", "euronics.it", "4.5"),
    _p("APPLE MacBook Air 13 M3 256GB", "€ 1199,00", "Apple", "MacBook Air M3", "Notebook", "unieuro.it", "4.9"),
    _p("Acer Chromebook 314", "€ 279,00", "Acer", "Chromebook 314", "Notebook", "mediaworld.it", "4.0"),
    _p("Samsung TV QLED 55 QE55Q60D", "€ 649,00", "Samsung", "QE55Q60D", "TV", "trony.it", "4.4"),
    _p("LG OLED evo 55 OLED55C4", "€ 1290,00", "LG", "OLED55C4", "TV", "euronics.it", "4.8"),
    _p("PlayStation 5 Slim Digital", "€ 449,00", "Sony", "PS5 Slim", "Console", "amazon.it", "4.9"),
    _p("Nintendo Switch OLED", "€ 319,00", "Nintendo", "Switch OLED", "Console", "unieuro.it", "4.7"),
    _p("Xiaomi Redmi Note 13 Pro 256GB", "€ 279,00", "Xiaomi", "Redmi Note 13 Pro", "Smartphone", "mediaworld.it", "4.3"),
    _p("De'Longhi Magnifica S Macchina Caffè", "€ 249,00", "De'Longhi", "Magnifica S", "Elettrodomestici", "trony.it", "4.5"),
    _p("Bosch Serie 4 Lavatrice 8kg", "€ 429,00", "Bosch", "Serie 4", "Elettrodomestici", "euronics.it", "4.2"),
    _p("Apple Watch Series 10 GPS 42mm", "€ 449,00", "Apple", "Watch Series 10", "Wearable", "unieuro.it", "4.6"),
]


async def seed_if_empty(historical_db) -> None:
    """Popola il DB con i prodotti demo se non ci sono prodotti."""
    try:
        existing = await historical_db.search_historical_products({"limit": 1})
        if existing.get("success") and existing.get("products"):
            return  # gia' popolato (reale o demo)

        # Raggruppa per sito e salva (un "scan" demo per sito)
        by_site = {}
        for prod in SEED_PRODUCTS:
            by_site.setdefault(prod["source"], []).append(prod)

        tot = 0
        for site, prods in by_site.items():
            res = await historical_db.save_extracted_products(
                url=f"https://www.{site}/demo",
                products=prods,
                session_id=None,
                extraction_method="seed_demo",
            )
            tot += res.get("saved_count", 0) if res else 0
        logger.info(f"🌱 Seed demo: inseriti {tot} prodotti in DB vuoto")
    except Exception as e:
        logger.warning(f"⚠️ Seed demo non riuscito: {e}")
