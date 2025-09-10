# 🚀 Deploy su Render - Guida Completa

## 📋 **Prerequisiti**
- Account Render (gratuito)
- Repository GitHub con il codice
- API Keys configurate

## 🔧 **Configurazione Iniziale**

### **1. Crea Account Render**
1. Vai su [render.com](https://render.com)
2. Clicca "Get Started"
3. Connetti il tuo account GitHub

### **2. Prepara il Repository**
Assicurati che il repository contenga:
- ✅ `render.yaml` (già presente)
- ✅ `Backend/requirements.txt`
- ✅ `Backend/main.py`
- ✅ `Frontend/` (per i file statici)

## 🚀 **Deploy Automatico**

### **Opzione 1: Deploy da GitHub (Raccomandato)**

1. **Vai su Render Dashboard**
2. **Clicca "New +" → "Web Service"**
3. **Connetti Repository GitHub**
4. **Seleziona il tuo repository**
5. **Configurazione:**
   ```
   Name: mr-anto-scraper
   Environment: Python
   Region: Oregon (US West)
   Branch: master
   Root Directory: (lascia vuoto)
   Build Command: cd Backend && pip install -r requirements.txt && playwright install
   Start Command: cd Backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### **Opzione 2: Deploy da render.yaml (Automatico)**

1. **Push del codice su GitHub**
2. **Render rileverà automaticamente `render.yaml`**
3. **Clicca "Deploy"**

## 🔑 **Configurazione Environment Variables**

### **Nel Dashboard Render:**
1. **Vai su "Environment"**
2. **Aggiungi le variabili:**
   ```
   OPENAI_API_KEY=sk-...
   GEMINI_API_KEY=...
   BROWSERBASE_API_KEY=bb_live_...
   BROWSERBASE_PROJECT_ID=...
   ```

## 📁 **Configurazione File Statici**

### **Per servire il Frontend:**
1. **Vai su "Settings"**
2. **Aggiungi Build Command:**
   ```bash
   cd Backend && pip install -r requirements.txt && playwright install && cd ../Frontend && cp -r * ../Backend/static/
   ```

## 🎯 **Test del Deploy**

### **1. Verifica Build**
- Controlla i log di build
- Assicurati che Playwright si installi correttamente

### **2. Test Endpoints**
- `https://tuo-app.onrender.com/` - Frontend
- `https://tuo-app.onrender.com/docs` - API Docs
- `https://tuo-app.onrender.com/google-search` - Test API

### **3. Test Scraping**
- Prova la ricerca Google
- Verifica che Playwright funzioni

## ⚠️ **Limitazioni Free Tier**

### **RAM: 512 MB**
- Potrebbe essere insufficiente per Playwright
- Se va in crash, considera upgrade a Standard ($25/mese)

### **Sleep dopo 15 min**
- Il servizio si sospende senza traffico
- I colleghi possono "svegliarlo" visitando il sito

### **CPU: 0.1 vCPU**
- Scraping potrebbe essere lento
- Considera upgrade per performance migliori

## 🔄 **Upgrade Piano**

### **Se 512 MB non bastano:**
1. **Vai su "Settings"**
2. **Clicca "Change Plan"**
3. **Seleziona "Standard" ($25/mese)**
4. **Riavvio automatico**

## 📊 **Monitoring**

### **Logs:**
- Dashboard → "Logs"
- Monitora errori e performance

### **Metrics:**
- CPU, RAM, Network usage
- Response times

## 🎉 **Condivisione con Colleghi**

### **URL del Deploy:**
```
https://mr-anto-scraper.onrender.com
```

### **Istruzioni per Colleghi:**
1. Visita l'URL
2. Se il sito è "dormiente", aspetta 30 secondi
3. Prova la ricerca Google
4. Testa lo scraping

## 🆘 **Troubleshooting**

### **Build Fallisce:**
- Controlla `requirements.txt`
- Verifica che Playwright si installi

### **App Crashes:**
- Probabilmente RAM insufficiente
- Considera upgrade a Standard

### **Playwright Non Funziona:**
- Verifica che `playwright install` sia nel build command
- Controlla i log per errori specifici

## 💡 **Tips**

1. **Testa localmente** prima del deploy
2. **Monitora i log** durante il primo deploy
3. **Considera upgrade** se performance insufficienti
4. **Usa domini personalizzati** per professionalità

---

**Buon deploy! 🚀**
