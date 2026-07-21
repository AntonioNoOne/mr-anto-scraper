# Immagine Playwright + Python. La versione del tag DEVE combaciare con il pin
# di playwright in requirements.txt (>=1.61,<2.0) per allineare i binari del browser.
FROM mcr.microsoft.com/playwright/python:v1.61.0-noble

WORKDIR /app

# Dipendenze: gestite in un unico requirements.txt alla root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Assicura che i browser combacino con la versione di playwright installata da pip
RUN playwright install --with-deps chromium

# Codice applicazione
COPY . .

# Inizializza i selettori predefiniti
WORKDIR /app/Backend
RUN python init_selectors.py

# Render inietta $PORT; fallback 8000 in locale. Shell form per espandere la variabile.
EXPOSE 8000
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
