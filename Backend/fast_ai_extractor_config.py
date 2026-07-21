"""Configurazioni e costanti condivise per FastAIExtractor."""

# Costanti per configurazioni
ANTI_BOT_SITES = ['unieuro.it', 'amazon.', 'ebay.', 'mediaworld.it', 'euronics.it', 'trony.it']
STRONG_ANTI_BOT_SITES = ['unieuro.it', 'amazon.', 'ebay.']

# Configurazioni browser
BROWSER_ARGS_BASE = [
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor'
]

BROWSER_ARGS_STEALTH = [
    '--window-size=1,1',
    '--window-position=9999,9999',
    '--disable-gpu',
    '--disable-images',
    '--disable-extensions-except=',
    '--disable-plugins-discovery',
    '--disable-default-apps',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',
    '--disable-ipc-flooding-protection'
]

BROWSER_ARGS_VISIBLE = [
    '--window-size=1600,1000',
    '--window-position=0,0',
    '--start-maximized',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding'
]

