"""
Configurazione Crawl4AI condivisa, ottimizzata per ambienti con poca RAM
(es. Render free 512MB). Un browser leggero + basso parallelismo evitano
il crash per saturazione memoria (502/OOM).
"""

import os


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# Quante pagine fetchare in parallelo durante l'arricchimento prezzi.
# Basso di default per non saturare la RAM; alzabile via env su macchine capienti.
ENRICH_CONCURRENCY = _int_env("CRAWL_CONCURRENCY", 2)


def light_browser_config():
    """BrowserConfig Crawl4AI a bassa impronta di memoria.

    - light_mode: disabilita feature non essenziali del browser
    - extra_args: flag Chromium per ambienti containerizzati con poca /dev/shm
    NB: niente text_mode (disabilita immagini/link) perche' su alcuni siti
    impoverisce troppo il markdown e l'AI non trova i prodotti. Il vero
    risparmio RAM viene dal riuso di UN solo browser + basso parallelismo.
    """
    from crawl4ai import BrowserConfig
    return BrowserConfig(
        headless=True,
        light_mode=True,
        verbose=False,
        extra_args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",   # usa /tmp invece della piccola /dev/shm
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--js-flags=--max-old-space-size=384",
        ],
    )
