@echo off
echo 🚀 Deploy MR Anto Scraper
echo ========================

echo 📁 Controllo directory...
cd /d "C:\Users\anto_\Desktop\AIDev\MR_Scraper\mr.-anto-scraper"

echo 🔧 Inizializzazione Git...
git init
git add .
git commit -m "Deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm')"

echo 📤 Push su GitHub...
git remote add origin https://github.com/tuo-username/mr-anto-scraper.git
git push -u origin main

echo ✅ Deploy completato!
echo 🌐 Vai su railway.app per configurare il deploy
pause
