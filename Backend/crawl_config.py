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


def prefer_cloud_fetch() -> bool:
    """True se conviene usare il fetch CLOUD (Jina Reader) invece del browser locale.

    Su ambienti con poca CPU/RAM (Render free: 0.1 vCPU, 512MB) il browser
    Chromium è lento e pesante -> meglio Jina (cloud, nessun browser). Attivo
    automaticamente su Render (env RENDER) o forzabile con PREFER_CLOUD_FETCH=1.
    In locale resta il browser (crawl4ai), più potente.
    """
    val = os.getenv("PREFER_CLOUD_FETCH")
    if val is not None:
        return val.strip().lower() in ("1", "true", "yes", "on")
    return bool(os.getenv("RENDER"))


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
