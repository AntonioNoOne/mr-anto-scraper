// Modulo per la gestione delle azioni dell'applicazione
class Actions {
    constructor() {
        this.isProcessing = false;
        this.activeTimers = []; // Array per tenere traccia di tutti i timer attivi
    }
    
    // Metodo helper per verificare se chartManager è disponibile e sicuro
    isChartManagerReady() {
        // Verifica che chartManager sia disponibile e abbia tutti i metodi necessari
        const isReady = window.chartManager && 
               typeof window.chartManager === 'object' && 
               typeof window.chartManager.updateActivityChart === 'function' &&
               typeof window.chartManager.charts === 'object' &&
               window.chartManager.charts instanceof Map;
        
        if (!isReady) {
            console.log('🔍 ChartManager status:', {
                exists: !!window.chartManager,
                type: typeof window.chartManager,
                hasUpdateActivity: typeof window.chartManager?.updateActivityChart,
                hasCharts: typeof window.chartManager?.charts,
                chartsType: window.chartManager?.charts?.constructor?.name
            });
        }
        
        return isReady;
    }
    
    // Metodo helper per aggiornare i grafici in modo sicuro
    safeUpdateCharts() {
        if (!this.isChartManagerReady()) {
            console.log('ℹ️ ChartManager non disponibile, salto aggiornamento grafici');
            return false;
        }
        
        try {
            // Prima verifica lo stato dei grafici
            if (typeof window.chartManager.getChartsStatus === 'function') {
                window.chartManager.getChartsStatus();
            }
            
            // Aggiorna il grafico attività
            window.chartManager.updateActivityChart();
            
            // Aggiorna il grafico prezzi se disponibile
            if (typeof window.chartManager.updatePriceChart === 'function') {
                window.chartManager.updatePriceChart();
            }
            
            return true;
        } catch (error) {
            console.warn('⚠️ Errore aggiornamento grafici:', error);
            
            // Prova a forzare l'aggiornamento se disponibile
            try {
                if (typeof window.chartManager.forceUpdateAllCharts === 'function') {
                    console.log('🔄 Tentativo di aggiornamento forzato...');
                    window.chartManager.forceUpdateAllCharts();
                    return true;
                }
            } catch (forceError) {
                console.warn('⚠️ Anche l\'aggiornamento forzato è fallito:', forceError);
            }
            
            return false;
        }
    }
    
    // Metodo per attendere che chartManager sia pronto
    async waitForChartManager(maxWait = 5000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWait) {
            if (this.isChartManagerReady()) {
                console.log('✅ ChartManager pronto dopo', Date.now() - startTime, 'ms');
                return true;
            }
            
            // Attendi 100ms prima di controllare di nuovo
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        console.warn('⏰ Timeout attesa ChartManager dopo', maxWait, 'ms');
        return false;
    }
    
    // Metodo per forzare l'inizializzazione dei grafici se necessario
    forceInitializeCharts() {
        if (!this.isChartManagerReady()) {
            console.log('⚠️ ChartManager non disponibile, impossibile inizializzare grafici');
            return false;
        }
        
        try {
            console.log('🔄 Forzando inizializzazione grafici...');
            
            // Forza l'inizializzazione di tutti i grafici
            if (typeof window.chartManager.forceUpdateAllCharts === 'function') {
                window.chartManager.forceUpdateAllCharts();
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('❌ Errore durante inizializzazione forzata:', error);
            return false;
        }
    }
    
    // =================================================
    // SCRAPING ACTIONS
    // =================================================
    
    async startGenericScraping() {
        if (this.isProcessing) return;
        
        const validUrls = store.state.genericUrls.filter(url => url.trim() !== '');
        if (validUrls.length === 0) {
            console.log('❌ Inserisci almeno un URL valido');
            return;
        }
        
        this.isProcessing = true;
        
        // Resetta le barre esistenti se ce ne sono
        if (store.state.genericScrapingProgress && store.state.genericScrapingProgress.length > 0) {
            store.resetScrapingProgress();
        }
        
        store.setState({ 
            isScrapingGeneric: true,
            genericScrapingProgress: [],
            genericResults: [],
            canStopScraping: false  // Reset del flag di stop
        });
        
        // Inizializza progress per ogni URL
        const initialProgress = validUrls.map(url => ({
            url: url,
            status: 'pending',
            percentage: 0,
            productsFound: 0,
            message: 'In attesa...'
        }));
        store.setScrapingProgress(initialProgress);
        
        try {
            // Processa ogni URL sequenzialmente
            for (let i = 0; i < validUrls.length; i++) {
                if (store.state.canStopScraping) {
                    console.log('🛑 Scraping fermato dall\'utente');
                    break;
                }
                
                const url = validUrls[i];
                console.log(`🚀 Avvio scraping per URL ${i + 1}/${validUrls.length}: ${url}`);
                store.updateState(`genericScrapingProgress.${i}.status`, 'processing');
                
                // Progresso iniziale
                store.updateState(`genericScrapingProgress.${i}.percentage`, 5);
                store.updateState(`genericScrapingProgress.${i}.message`, 'Inizio estrazione...');
                
                // Sistema di incremento automatico FLUIDO e LINEARE
                let autoIncrementInterval;
                let currentProgress = 5;
                
                const startAutoIncrement = () => {
                    if (autoIncrementInterval) return;
                    
                    autoIncrementInterval = setInterval(() => {
                        // Controlla se deve fermarsi
                        if (store.state.canStopScraping) {
                            clearInterval(autoIncrementInterval);
                            return;
                        }
                        
                        if (currentProgress < 95) {
                            // Incremento FLUIDO e costante - MAI tornare indietro!
                            currentProgress += 2;
                            
                            // Assicurati di non superare il 95%
                            if (currentProgress > 95) currentProgress = 95;
                            
                            store.updateState(`genericScrapingProgress.${i}.percentage`, currentProgress);
                            store.updateState(`genericScrapingProgress.${i}.message`, `Elaborazione in corso: ${currentProgress}%`);
                        } else {
                            clearInterval(autoIncrementInterval);
                        }
                    }, 2000); // Ogni 2 secondi per un progresso più fluido
                    
                    // Aggiungi l'interval all'array dei timer attivi
                    this.activeTimers.push({ type: 'interval', id: autoIncrementInterval });
                };
                
                // Avvia incremento automatico dopo 2 secondi (più veloce)
                const startTimeout = setTimeout(() => {
                    if (!store.state.canStopScraping) {
                        startAutoIncrement();
                    }
                }, 2000);
                
                // Aggiungi il timeout all'array dei timer attivi
                this.activeTimers.push({ type: 'timeout', id: startTimeout });
                
                // Controlla se deve fermarsi prima di iniziare
                if (store.state.canStopScraping) {
                    clearTimeout(startTimeout);
                    console.log(`🛑 Scraping fermato prima dell'avvio per URL ${i + 1}`);
                    break;
                }
                
                try {
                    // Controlla se deve fermarsi prima della chiamata API
                    if (store.state.canStopScraping) {
                        if (autoIncrementInterval) {
                            clearInterval(autoIncrementInterval);
                        }
                        console.log(`🛑 Scraping fermato per URL ${i + 1}`);
                        break;
                    }
                    
                    const response = await api.fastExtract(url);
                    
                    // Controlla se è stato fermato durante la chiamata API
                    if (store.state.canStopScraping) {
                        if (autoIncrementInterval) {
                            clearInterval(autoIncrementInterval);
                        }
                        console.log(`🛑 Scraping fermato durante elaborazione URL ${i + 1}`);
                        break;
                    }
                    
                    console.log(`✅ Risposta ricevuta per URL ${i + 1}:`, response);
                    
                    if (autoIncrementInterval) {
                        clearInterval(autoIncrementInterval);
                    }
                    store.updateState(`genericScrapingProgress.${i}.percentage`, 100);
                    store.updateState(`genericScrapingProgress.${i}.message`, 'Estrazione completata');
                    
                    if (response.success) {
                        store.updateState(`genericScrapingProgress.${i}.status`, 'completed');
                        store.updateState(`genericScrapingProgress.${i}.productsFound`, response.total_found || response.products?.length || 0);
                        store.updateState(`genericScrapingProgress.${i}.message`, `✅ Estrazione completata: ${response.total_found || response.products?.length || 0} prodotti`);

                        store.addScrapingResult({
                            url: url,
                            products: response.products || [],
                            success: true
                        });
                        
                        // Barra rimane al 100% - MAI tornare indietro!
                    } else {
                        store.updateState(`genericScrapingProgress.${i}.status`, 'error');
                        store.addScrapingResult({
                            url: url,
                            products: [],
                            success: false,
                            error: response.error
                        });
                        
                        // Barra di errore rimane al 100% - MAI tornare indietro!
                        store.updateState(`genericScrapingProgress.${i}.message`, `❌ Errore: ${response.error}`);
                    }
                } catch (error) {
                    console.log(`❌ Eccezione per URL ${i + 1}:`, error);
                    if (autoIncrementInterval) {
                        clearInterval(autoIncrementInterval);
                    }
                    store.updateState(`genericScrapingProgress.${i}.percentage`, 100);
                    store.updateState(`genericScrapingProgress.${i}.status`, 'error');
                    store.updateState(`genericScrapingProgress.${i}.message`, `❌ Errore connessione: ${error.message}`);
                    store.addScrapingResult({
                        url: url,
                        products: [],
                        success: false,
                        error: error.message
                    });
                    
                    // Barra di errore rimane al 100% - MAI tornare indietro!
                } finally {
                    if (autoIncrementInterval) {
                        clearInterval(autoIncrementInterval);
                    }
                }
            }
            
            const totalProducts = store.getTotalProducts();
            store.addActivity({
                id: Date.now(),
                type: 'scrape',
                icon: 'fas fa-spider',
                description: `Scraping completato: ${totalProducts} prodotti da ${validUrls.length} siti`,
                timestamp: new Date().toLocaleTimeString('it-IT'),
                status: 'success'
            });
            
        } catch (error) {
            console.error('Errore generico scraping:', error);
        } finally {
            this.isProcessing = false;
            store.setState({ isScrapingGeneric: false });
        }
    }
    
    async stopGenericScraping() {
        console.log('🛑 Fermata richiesta scraping generico...');
        
        try {
            // Chiama l'endpoint del backend per fermare lo scraping
            const response = await api.stopScraping();
            if (response.success) {
                console.log('✅ Stop richiesto al backend');
            } else {
                console.log('⚠️ Errore richiesta stop al backend:', response.error);
            }
        } catch (error) {
            console.log('⚠️ Errore chiamata stop al backend:', error);
        }
        
        // Pulisci tutti i timer attivi
        this.activeTimers.forEach(timer => {
            if (timer.type === 'timeout') {
                clearTimeout(timer.id);
            } else if (timer.type === 'interval') {
                clearInterval(timer.id);
            }
        });
        this.activeTimers = []; // Reset array timer
        
        // Ferma tutti gli intervalli di incremento
        store.state.genericScrapingProgress.forEach((progress, index) => {
            if (progress.status === 'processing') {
                store.updateState(`genericScrapingProgress.${index}.status`, 'stopped');
                store.updateState(`genericScrapingProgress.${index}.message`, 'Scraping fermato dall\'utente');
                store.updateState(`genericScrapingProgress.${index}.percentage`, 0); // Reset a 0%
            }
        });
        
        // Ferma tutti i processi attivi
        store.setState({ 
            isScrapingGeneric: false,
            canStopScraping: true  // Abilita lo stop per fermare le chiamate API
        });
        
        // Forza l'interruzione di tutti i processi
        store.stopScraping();
        
        console.log('✅ Scraping fermato con successo');
    }
    
    // =================================================
    // COMPARISON ACTIONS
    // =================================================
    
    async startProductComparison() {
        if (store.state.genericResults.length < 2) {
            console.log('❌ Servono almeno 2 siti con prodotti per il confronto');
            return;
        }
        
        store.setState({ 
            isComparing: true,
            comparisonResults: null
        });
        
        try {
            const preparedResults = store.state.genericResults.map(result => {
                if (result.success && result.products) {
                    const siteName = store.getSiteNameFromUrl(result.url);
                    return {
                        ...result,
                        products: result.products.map(product => ({
                            ...product,
                            site: siteName,
                            source: siteName,
                            source_url: result.url
                        }))
                    };
                }
                return result;
            });
            
            // Estrai i domini selezionati dai risultati
            const selectedDomains = preparedResults
                .filter(result => result.success && result.products)
                .map(result => {
                    const siteName = store.getSiteNameFromUrl(result.url);
                    return siteName;
                });
            
            // PROTEZIONE: Assicurati che selectedDomains sia sempre un array
            if (!Array.isArray(selectedDomains)) {
                console.warn('⚠️ selectedDomains non è un array, resetto a array vuoto:', selectedDomains);
                selectedDomains = [];
            }
            
            console.log('🎯 DOMINI SELEZIONATI PER CONFRONTO:', selectedDomains);
            console.log('🔍 DEBUG - Dati inviati al confronto:', preparedResults);
            
            // Invia anche i domini selezionati per il filtraggio
            const response = await api.compareProducts(preparedResults, selectedDomains);
            
            if (response.success) {
                store.setComparisonResults(response);
                console.log('✅ Confronto completato:', response);
                
                store.addActivity({
                    id: Date.now(),
                    type: 'comparison',
                    icon: 'fas fa-balance-scale',
                    description: `Confronto completato: ${response.comparable_products} gruppi trovati`,
                    timestamp: new Date().toLocaleTimeString('it-IT'),
                    status: 'success'
                });
            } else {
                console.error('❌ Errore confronto:', response.error);
                store.addActivity({
                    id: Date.now(),
                    type: 'comparison',
                    icon: 'fas fa-exclamation-triangle',
                    description: `Errore confronto: ${response.error}`,
                    timestamp: new Date().toLocaleTimeString('it-IT'),
                    status: 'error'
                });
            }
        } catch (error) {
            console.error('❌ Errore confronto API:', error);
            store.addActivity({
                id: Date.now(),
                type: 'comparison',
                icon: 'fas fa-exclamation-triangle',
                description: `Errore connessione: ${error.message}`,
                timestamp: new Date().toLocaleTimeString('it-IT'),
                status: 'error'
            });
        } finally {
            store.setState({ isComparing: false });
        }
    }
    
    // =================================================
    // DASHBOARD ACTIONS
    // =================================================
    
    async refreshDashboardData() {
        try {
            console.log('📊 Aggiornamento dati dashboard...');
            
            // Carica statistiche dal database
            const response = await api.getDashboardStats();
            
            if (response.success) {
                const stats = response.stats;
                
                // Aggiorna lo store con i dati reali
                store.setState({
                    stats: {
                        totalProducts: stats.total_products || 0,
                        newProductsToday: stats.products_today || 0,
                        sitesMonitored: stats.total_sites || 0,
                        activeSites: stats.total_sites || 0,
                        extractionsToday: stats.extractions_today || 0,
                        aiAccuracy: 95, // Valore fisso per ora
                        aiModel: 'GPT-4', // Valore fisso per ora
                        avgResponseTime: 250, // Valore fisso per ora
                        uptime: 99.9 // Valore fisso per ora
                    },
                    topSites: stats.top_sites || [],
                    weeklyStats: stats.weekly_stats || [],
                    lastUpdate: stats.last_update || new Date().toISOString()
                });
                
                console.log('✅ Dashboard aggiornata con dati reali:', stats);
                
            } else {
                console.error('❌ Errore caricamento statistiche:', response.error);
                // Mantieni i dati esistenti se c'è un errore
            }
            
            // 🆕 CARICA ATTIVITÀ RECENTI REALI DAL DATABASE
            console.log('📋 Caricamento attività recenti...');
            
            // Usa i metodi esistenti dello store per caricare attività e categorie
            await store.loadRecentActivities();
            await store.loadTopCategories();
            
            console.log('✅ Attività recenti e categorie caricate dal database');
            
            // 🆕 ATTENDI CHE CHARTMANAGER SIA PRONTO PRIMA DI AGGIORNARE I GRAFICI
            console.log('⏳ Attendo che ChartManager sia pronto...');
            const chartManagerReady = await this.waitForChartManager(3000); // Attendi max 3 secondi
            
            if (chartManagerReady) {
                console.log('✅ ChartManager pronto, aggiorno i grafici...');
                this.safeUpdateCharts();
            } else {
                console.warn('⚠️ ChartManager non disponibile dopo timeout, salto aggiornamento grafici');
            }
            
        } catch (error) {
            console.error('❌ Errore aggiornamento dashboard:', error);
            // Mantieni i dati esistenti se c'è un errore
            
            // Prova comunque ad aggiornare i grafici se possibile
            try {
                if (this.isChartManagerReady()) {
                    this.safeUpdateCharts();
                }
            } catch (chartError) {
                console.warn('⚠️ Errore aggiornamento grafici di fallback:', chartError);
            }
        }
    }
    
    // =================================================
    // GOOGLE SEARCH ACTIONS
    // =================================================
    
    async startGoogleSearch() {
        if (this.isProcessing) return;
        
        const searchData = store.state.googleSearchData;
        
        // Debug: Log dei dati ricevuti
        console.log('🔍 Dati ricevuti dallo store:', searchData);
        console.log('🔍 Tipo di searchData:', typeof searchData);
        console.log('🔍 searchData.name:', searchData?.name);
        
        // Rimuovo completamente la validazione per test
        console.log('🔍 Procedo con la ricerca senza validazione...');
        
        this.isProcessing = true;
        
        // Reset risultati precedenti
        store.setState({ 
            googleSearchResults: [],
            isGoogleSearching: true,
            googleSearchError: null
        });
        
        try {
            console.log('🔍 Avvio ricerca Google per:', searchData);
            
            // Prepara i dati per l'API
            const productData = {
                name: (searchData?.name || '').trim(),
                brand: (searchData?.brand || '').trim(),
                price: (searchData?.price || '').trim(),
                source: (searchData?.source || '').trim()
            };
            
            console.log('🔍 Dati preparati per API:', productData);
            
            // Chiama l'API Google Search
            console.log('🔍 Chiamando API searchAlternativeVendors con:', productData);
            const response = await api.searchAlternativeVendors(productData);
            console.log('🔍 Risposta API ricevuta:', response);
            console.log('🔍 response.success:', response.success);
            console.log('🔍 response.error:', response.error);
            
            if (response.success) {
                store.setGoogleSearchResults(response.alternative_vendors || []);
                console.log('✅ Ricerca Google completata:', response);
                
                store.addActivity({
                    id: Date.now(),
                    type: 'google_search',
                    icon: 'fab fa-google',
                    description: `Ricerca Google completata: ${response.alternative_vendors?.length || 0} venditori trovati`,
                    timestamp: new Date().toLocaleTimeString('it-IT'),
                    status: 'success'
                });
            } else {
                console.error('❌ Errore ricerca Google:', response.error);
                console.error('❌ Response completa:', response);
                console.error('❌ Response.success:', response.success);
                store.setState({ googleSearchError: response.error });
                
                store.addActivity({
                    id: Date.now(),
                    type: 'google_search',
                    icon: 'fab fa-google',
                    description: `Errore ricerca Google: ${response.error}`,
                    timestamp: new Date().toLocaleTimeString('it-IT'),
                    status: 'error'
                });
            }
        } catch (error) {
            console.error('❌ Errore ricerca Google API:', error);
            store.setState({ googleSearchError: error.message });
            
            store.addActivity({
                id: Date.now(),
                type: 'google_search',
                icon: 'fab fa-google',
                description: `Errore connessione: ${error.message}`,
                timestamp: new Date().toLocaleTimeString('it-IT'),
                status: 'error'
            });
        } finally {
            this.isProcessing = false;
            store.setState({ isGoogleSearching: false });
        }
    }
    
    // =================================================
    // UTILITY ACTIONS
    // =================================================
    
    clearScrapingResults() {
        store.clearScrapingResults();
        console.log('✅ Risultati scraping cancellati');
    }
    
    openVendorUrl(url) {
        if (url && url !== '#') {
            console.log('🔗 Apertura URL venditore:', url);
            window.open(url, '_blank');
        } else {
            console.log('⚠️ URL venditore non valido:', url);
        }
    }
    
    selectAllProductsFromResult(result) {
        if (!result.success || !result.products) return;
        
        result.products.forEach(product => {
            store.toggleProductSelection(result.url, product);
        });
        
        console.log(`✅ Selezionati ${result.products.length} prodotti da ${api.getSiteName(result.url)}`);
    }
}

// Crea un'istanza globale delle Actions
const actions = new Actions();

// Esporta l'istanza
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Actions, actions };
} else {
    window.actions = actions;
} 
