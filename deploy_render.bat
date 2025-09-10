@echo off
echo 🚀 Deploy su Render - MR Scraper
echo ================================

echo.
echo 📋 Preparazione file...
echo.

REM Verifica che i file necessari esistano
if not exist "render.yaml" (
    echo ❌ File render.yaml non trovato!
    pause
    exit /b 1
)

if not exist "Backend\requirements.txt" (
    echo ❌ File Backend\requirements.txt non trovato!
    pause
    exit /b 1
)

if not exist "Backend\main.py" (
    echo ❌ File Backend\main.py non trovato!
    pause
    exit /b 1
)

echo ✅ File di configurazione verificati!

echo.
echo 🔧 Configurazione Git...
echo.

REM Aggiungi tutti i file al commit
git add .
git commit -m "Deploy su Render - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

echo.
echo 📤 Push su GitHub...
echo.

REM Push su GitHub
git push origin master

echo.
echo ✅ Codice pushato su GitHub!
echo.
echo 🎯 Prossimi passi:
echo 1. Vai su https://render.com
echo 2. Clicca "New +" → "Web Service"
echo 3. Connetti il tuo repository GitHub
echo 4. Seleziona il repository "mr-anto-scraper"
echo 5. Render rileverà automaticamente render.yaml
echo 6. Clicca "Deploy"
echo.
echo 🔑 Ricorda di configurare le Environment Variables:
echo - OPENAI_API_KEY
echo - GEMINI_API_KEY
echo - BROWSERBASE_API_KEY
echo - BROWSERBASE_PROJECT_ID
echo.
echo 🎉 Deploy completato! Buona fortuna!
echo.
pause
