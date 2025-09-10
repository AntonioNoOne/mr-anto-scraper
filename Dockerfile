# Usa Python 3.11 con Playwright preinstallato
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file di requirements
COPY requirements.txt .
COPY Backend/requirements.txt Backend/

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r Backend/requirements.txt

# I browser Playwright sono già installati nell'immagine base
# RUN playwright install chromium

# Copia il codice dell'applicazione
COPY . .

# Esponi la porta
EXPOSE 8000

# Comando di avvio
CMD ["cd", "Backend", "&&", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
