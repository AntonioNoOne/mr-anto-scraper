# 🚀 Deploy su Render - Guida Passo per Passo

## 📋 **Prerequisiti Completati**
- ✅ Repository GitHub: `https://github.com/AntonioNoOne/mr-anto-scraper`
- ✅ Codice pushato senza API keys
- ✅ Configurazione `render.yaml` pronta

## 🔧 **Passo 1: Crea Account Render**
1. Vai su [render.com](https://render.com)
2. Clicca "Get Started"
3. Connetti il tuo account GitHub
4. Autorizza Render ad accedere ai tuoi repository

## 🚀 **Passo 2: Crea Web Service**
1. Nel dashboard Render, clicca **"New +"**
2. Seleziona **"Web Service"**
3. Clicca **"Connect GitHub"**
4. Seleziona il repository **"mr-anto-scraper"**
5. Clicca **"Connect"**

## ⚙️ **Passo 3: Configurazione Automatica**
Render rileverà automaticamente:
- ✅ **Name**: `mr-anto-scraper`
- ✅ **Environment**: `Python`
- ✅ **Build Command**: `cd Backend && pip install -r requirements.txt && playwright install`
- ✅ **Start Command**: `cd Backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

## 🔑 **Passo 4: Configura Environment Variables**
**IMPORTANTE**: Questo è il passaggio cruciale!

1. Nel dashboard Render, vai su **"Environment"**
2. Clicca **"Add Environment Variable"**
3. Aggiungi queste 4 variabili:

### **Variabile 1:**
- **Key**: `OPENAI_API_KEY`
- **Value**: `your_openai_api_key_here`

### **Variabile 2:**
- **Key**: `GEMINI_API_KEY`
- **Value**: `your_gemini_api_key_here`

### **Variabile 3:**
- **Key**: `BROWSERBASE_API_KEY`
- **Value**: `your_browserbase_api_key_here`

### **Variabile 4:**
- **Key**: `BROWSERBASE_PROJECT_ID`
- **Value**: `your_browserbase_project_id_here`

## 🚀 **Passo 5: Deploy**
1. Clicca **"Create Web Service"**
2. Render inizierà il build automaticamente
3. Monitora i log per verificare che tutto vada bene
4. Il deploy richiederà 5-10 minuti

## 🎯 **Passo 6: Test dell'App**
Dopo il deploy, l'app sarà disponibile su:
```
https://mr-anto-scraper.onrender.com
```

### **Test Endpoints:**
- **Frontend**: `https://mr-anto-scraper.onrender.com/`
- **API Docs**: `https://mr-anto-scraper.onrender.com/docs`
- **Health Check**: `https://mr-anto-scraper.onrender.com/health`

## ⚠️ **Limitazioni Free Tier**
- **RAM**: 512 MB (potrebbe essere insufficiente per Playwright)
- **Sleep**: Si sospende dopo 15 min di inattività
- **CPU**: 0.1 vCPU (scraping lento)

## 🔄 **Se 512 MB Non Bastano**
1. Vai su "Settings" in Render
2. Clicca "Change Plan"
3. Seleziona "Standard" ($25/mese) - 2 GB RAM

## 🆘 **Troubleshooting**

### **Build Fallisce:**
- Controlla i log in Render Dashboard
- Verifica che Playwright si installi correttamente

### **App Crashes:**
- Probabilmente RAM insufficiente
- Considera upgrade a Standard

### **Environment Variables Non Funzionano:**
- Verifica che siano configurate correttamente
- Riavvia il servizio dopo aver aggiunto le variabili

## 🎉 **Completato!**
Una volta deployato, potrai condividere l'URL con i tuoi colleghi per testare il sistema!

---

**Buon deploy! 🚀**
