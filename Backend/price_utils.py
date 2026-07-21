"""
Utility per l'estrazione del prezzo dal testo/markdown di una pagina.

Problema: le pagine venditore sono spesso liste/generiche con MOLTI prezzi;
prendere "il primo €" dà spesso il prezzo sbagliato. Qui scegliamo il prezzo
€ più vicino (nel testo) alle parole chiave del prodotto cercato.
"""

import re
from typing import List, Optional

# Prezzo in € formato IT/EN: "1.299,90 €", "€ 1299", "599,49€", "€49"
_PRICE_RE = re.compile(r'€\s?\d[\d.]*(?:,\d{2})?|\d[\d.]*(?:,\d{2})?\s?€')

_STOPWORDS = {
    "the", "and", "con", "per", "di", "da", "in", "il", "la", "le", "lo", "gli",
    "un", "una", "nero", "black", "nuovo", "new", "gb", "online", "su", "a",
}


def _to_float(price_str: str) -> float:
    """Converte '1.299,90 €' / '€ 599' in float. 0 se non parsabile."""
    s = re.sub(r'[^\d.,]', '', price_str)
    if not s:
        return 0.0
    # Formato IT: '.' migliaia, ',' decimali
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def _keywords(name: str) -> List[str]:
    words = re.findall(r'[a-zA-Z0-9]{3,}', (name or '').lower())
    return [w for w in words if w not in _STOPWORDS]


def pick_price_near_product(text: str, product_name: str = "",
                            min_value: float = 1.0) -> Optional[str]:
    """Ritorna il prezzo € più pertinente al prodotto.

    Strategia:
    1. Trova tutti i prezzi € (con posizione) sopra `min_value`.
    2. Se abbiamo il nome prodotto, dà punteggio a ogni prezzo in base a quante
       parole chiave del nome compaiono in una finestra di ±250 caratteri.
    3. Ritorna il prezzo col punteggio più alto; senza contesto, il primo valido.
    Ritorna None se non trova prezzi plausibili.
    """
    if not text:
        return None

    candidates = []  # (price_str, value, position)
    for m in _PRICE_RE.finditer(text):
        raw = m.group().strip()
        val = _to_float(raw)
        if val >= min_value:
            candidates.append((raw, val, m.start()))
    if not candidates:
        return None

    kws = _keywords(product_name)
    if not kws:
        return candidates[0][0]

    lower = text.lower()
    # Posizioni di ogni keyword nel testo
    kw_positions = {}
    for kw in kws:
        pos_list = [m.start() for m in re.finditer(re.escape(kw), lower)]
        if pos_list:
            kw_positions[kw] = pos_list
    if not kw_positions:
        return candidates[0][0]

    # Per ogni prezzo: quante keyword hanno un'occorrenza entro 150 char
    # (peso maggiore) e distanza media dalla keyword più vicina (tie-break).
    best = None
    best_key = (-1, float("inf"))
    for raw, val, pos in candidates:
        near = 0
        total_dist = 0
        for kw, positions in kw_positions.items():
            d = min(abs(pos - p) for p in positions)
            total_dist += d
            if d <= 150:
                near += 1
        avg_dist = total_dist / len(kw_positions)
        key = (near, -avg_dist)  # più keyword vicine, poi distanza minore
        if key > best_key:
            best_key = key
            best = raw

    return best if best else candidates[0][0]
