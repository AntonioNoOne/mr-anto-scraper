// Store per la gestione dello stato globale dell'applicazione
class Store {
    constructor() {
        this.state = {
            // UI State
            activeSection: 'dashboard',
            chatSidebarOpen: false,
            isLoading: false,
            lastUpdate: new Date().toLocaleTimeString('it-IT'),
            
            // Stats Data
            stats: {
                totalProducts: 0,
                newProductsToday: 0,
                aiAccuracy: 0,
                aiModel: 'N/A',
                sitesMonitored: 0,
                activeSites: 0,
                avgResponseTime: 0,
                uptime: 0,
                extractionsToday: 0,
                totalSites: 0,
                categoryStats: []
            },
            topCategories: [],
            recentActivities: [],
            
            // Scraping Data
            scrapingUrls: [''],
            genericUrls: [''],  // Aggiunto per il pannello URL
            isScrapingGeneric: false,
            canStopScraping: false,  // Nuovo: permette di fermare lo scraping
            genericScrapingProgress: [],
            genericResults: [],
            
            // Comparison Data
            isComparingProducts: false,
            comparisonResults: null,
            selectedUrlResult: null,
            isComparing: false,
            
            // Database Products
            databaseProducts: [],
            isLoadingDbProducts: false,
            
            // Monitoring Data
            selectedProducts: [],
            monitoringConfig: { ...CONFIG.MONITORING_CONFIG },
            isStartingMonitoring: false,
            activeMonitors: [],
            monitoredProducts: [],
            priceAlerts: [],
            monitoringStats: {},
            schedulerStats: {},
            
            // Historical Search
            historicalSearch: {
                productName: '',
                brand: '',
                date: ''
            },
            isSearchingHistorical: false,
            historicalResults: [],
            
            // Google Search
            googleSearchData: {
                name: '',
                brand: '',
                price: '',
                source: ''
            },
            isGoogleSearching: false,
            googleSearchResults: [],
            isTypingNewSearch: false, // Nasconde il messaggio "Ricerca terminata" quando si scrive
            hasSearched: false, // Traccia se è stata fatta almeno una ricerca
            
            // Chat AI
            chatMessages: [],
            chatInput: '',
            isAITyping: false,
            showDataSummary: false,
            selectedAIModel: 'openai',
            availableAIModels: { ...CONFIG.AI_MODELS },
            
            // Charts
            activityChart: null,
            priceChart: null,
            sitePerformance: [],
            
            // Legacy Data (mantenuti per compatibilità)
            scrapingProgress: {
                pagesProcessed: 0,
                productsFound: 0,
                errors: 0,
                percentage: 0
            },
            scrapingResults: [],
            singleResults: [],
            multipleResults: [],
            multipleUrls: [''],
            
            // Configuration
            aiConfig: {
                provider: 'auto',
                geminiConfigured: false,
                openaiConfigured: false
            },
            systemSettings: { ...CONFIG.SYSTEM_SETTINGS },
            
            // Domains Selection
            selectedDomains: [],  // Array di domini selezionati per confronto specifico
            
            // Debug
            debugInfo: null
        };
        
        this.listeners = [];
        this.loadFromStorage();
    }
    
    // =================================================
    // STATE MANAGEMENT
    // =================================================
    
    getState() {
        return this.state;
    }
    
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.notifyListeners();
        this.saveToStorage();
    }
    
    updateState(path, value) {
        const keys = path.split('.');
        let current = this.state;
        
        for (let i = 0; i < keys.length - 1; i++) {
            current = current[keys[i]];
        }
        
        current[keys[keys.length - 1]] = value;
        this.notifyListeners();
        this.saveToStorage();
    }
    
    // =================================================
    // SUBSCRIPTION SYSTEM
    // =================================================
    
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            const index = this.listeners.indexOf(listener);
            if (index > -1) {
                this.listeners.splice(index, 1);
            }
        };
    }
    
    notifyListeners() {
        this.listeners.forEach(listener => listener(this.state));
    }
    
    // =================================================
    // STORAGE MANAGEMENT
    // =================================================
    
    saveToStorage() {
        try {
            const dataToSave = {
                stats: this.state.stats,
                settings: this.state.systemSettings,
                chatHistory: this.state.chatMessages.slice(-50), // Salva solo ultimi 50 messaggi
                selectedProducts: this.state.selectedProducts
            };
            
            Object.keys(dataToSave).forEach(key => {
                localStorage.setItem(CONFIG.STORAGE_KEYS[key.toUpperCase()], JSON.stringify(dataToSave[key]));
            });
        } catch (error) {
            console.error('Errore salvataggio in localStorage:', error);
        }
    }
    
    loadFromStorage() {
        try {
            // Carica stats
            const storedStats = localStorage.getItem(CONFIG.STORAGE_KEYS.STATS);
            if (storedStats) {
                this.state.stats = { ...this.state.stats, ...JSON.parse(storedStats) };
            }
            
            // Carica settings
            const storedSettings = localStorage.getItem(CONFIG.STORAGE_KEYS.SETTINGS);
            if (storedSettings) {
                this.state.systemSettings = { ...this.state.systemSettings, ...JSON.parse(storedSettings) };
            }
            
            // Carica chat history
            const storedChatHistory = localStorage.getItem(CONFIG.STORAGE_KEYS.CHAT_HISTORY);
            if (storedChatHistory) {
                this.state.chatMessages = JSON.parse(storedChatHistory);
            }
            
            // Carica selected products
            const storedSelectedProducts = localStorage.getItem(CONFIG.STORAGE_KEYS.SELECTED_PRODUCTS);
            if (storedSelectedProducts) {
                this.state.selectedProducts = JSON.parse(storedSelectedProducts);
            }
        } catch (error) {
            console.error('Errore caricamento da localStorage:', error);
        }
    }
    
    clearStorage() {
        try {
            Object.values(CONFIG.STORAGE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
        } catch (error) {
            console.error('Errore pulizia localStorage:', error);
        }
    }
    
    // =================================================
    // UTILITY METHODS
    // =================================================
    
    getTotalProducts() {
        return this.state.genericResults.reduce((total, site) => total + site.products.length, 0);
    }
    
    getTotalProductsFromMultiple() {
        return this.state.multipleResults.reduce((total, result) => {
            return total + (result.products ? result.products.length : 0);
        }, 0);
    }
    
    getSuccessfulUrls() {
        return this.state.multipleResults.filter(result => result.success).length;
    }
    
    isProductSelected(url, product) {
        return this.state.selectedProducts.some(p => 
            p.url === url && p.product.name === product.name
        );
    }
    
    getSectionTitle() {
        return CONFIG.SECTIONS[this.state.activeSection]?.title || 'Dashboard';
    }
    
    getSectionDescription() {
        return CONFIG.SECTIONS[this.state.activeSection]?.description || 'Benvenuto in Jusper.';
    }
    
    // =================================================
    // ACTION METHODS
    // =================================================
    
    // UI Actions
    setActiveSection(section) {
        this.setState({ activeSection: section });
    }
    
    toggleChatSidebar() {
        this.setState({ chatSidebarOpen: !this.state.chatSidebarOpen });
    }
    
    setLoading(loading) {
        this.setState({ isLoading: loading });
    }
    
    updateTime() {
        this.setState({ lastUpdate: new Date().toLocaleTimeString('it-IT') });
    }
    
    // Scraping Actions
    addUrl() {
        const newUrls = [...this.state.genericUrls, ''];
        this.setState({ genericUrls: newUrls });
    }
    
    removeUrl(index) {
        const newUrls = this.state.genericUrls.filter((_, i) => i !== index);
        this.setState({ genericUrls: newUrls });
    }
    
    updateScrapingUrl(index, url) {
        const newUrls = [...this.state.genericUrls];
        newUrls[index] = url;
        this.setState({ genericUrls: newUrls });
    }
    
    setScrapingProgress(progress) {
        this.setState({ genericScrapingProgress: progress });
    }
    
    resetScrapingProgress() {
        // Resetta tutte le barre di progresso a 0
        const resetProgress = this.state.genericScrapingProgress.map(progress => ({
            ...progress,
            percentage: 0,
            status: 'pending',
            message: 'In attesa...'
        }));
        this.setState({ genericScrapingProgress: resetProgress });
    }
    
    addScrapingResult(result) {
        // Aggiungi il nome del sito per ogni prodotto
        if (result.success && result.products) {
            const siteName = this.getSiteNameFromUrl(result.url);
            result.products = result.products.map(product => ({
                ...product,
                site: siteName,
                source: siteName,
                source_url: result.url
            }));
        }
        
        const newResults = [...this.state.genericResults, result];
        this.setState({ genericResults: newResults });
    }
    
    getSiteNameFromUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname.replace('www.', '');
        } catch (e) {
            return 'Sito Sconosciuto';
        }
    }
    
    clearScrapingResults() {
        this.setState({ 
            genericResults: [],
            comparisonResults: null
        });
        // NON resettare più il progresso - le barre rimangono al 100%
        // this.resetScrapingProgress();
    }
    
    // Comparison Actions
    setComparisonResults(results) {
        this.setState({ comparisonResults: results });
    }
    
    setSelectedUrlResult(result) {
        this.setState({ selectedUrlResult: result });
    }
    
    // Monitoring Actions
    toggleProductSelection(url, product) {
        const index = this.state.selectedProducts.findIndex(p => 
            p.url === url && p.product.name === product.name
        );
        
        let newSelectedProducts;
        if (index >= 0) {
            newSelectedProducts = this.state.selectedProducts.filter((_, i) => i !== index);
        } else {
            newSelectedProducts = [...this.state.selectedProducts, {
                url: url,
                site: api.getSiteName(url),
                product: product,
                selectedAt: new Date().toISOString()
            }];
        }
        
        this.setState({ selectedProducts: newSelectedProducts });
    }
    
    selectAllProducts() {
        const newSelectedProducts = [];
        this.state.genericResults.forEach(siteResult => {
            siteResult.products.forEach(product => {
                newSelectedProducts.push({
                    url: siteResult.url,
                    site: api.getSiteName(siteResult.url),
                    product: product,
                    selectedAt: new Date().toISOString()
                });
            });
        });
        this.setState({ selectedProducts: newSelectedProducts });
    }
    
    clearSelectedProducts() {
        this.setState({ selectedProducts: [] });
    }
    
    updateMonitoringConfig(config) {
        this.setState({ monitoringConfig: { ...this.state.monitoringConfig, ...config } });
    }
    
    addMonitor(monitor) {
        const newMonitors = [...this.state.activeMonitors, monitor];
        this.setState({ activeMonitors: newMonitors });
    }
    
    removeMonitor(monitorId) {
        const newMonitors = this.state.activeMonitors.filter(m => m.id !== monitorId);
        this.setState({ activeMonitors: newMonitors });
    }
    
    updateMonitor(monitorId, updates) {
        const newMonitors = this.state.activeMonitors.map(m => 
            m.id === monitorId ? { ...m, ...updates } : m
        );
        this.setState({ activeMonitors: newMonitors });
    }
    
    // Chat Actions
    addChatMessage(message) {
        const newMessages = [...this.state.chatMessages, message];
        this.setState({ chatMessages: newMessages });
    }
    
    clearChat() {
        this.setState({ chatMessages: [] });
    }
    
    setAITyping(typing) {
        this.setState({ isAITyping: typing });
    }
    
    updateChatInput(input) {
        this.setState({ chatInput: input });
    }
    
    // Stats Actions
    updateStats(newStats) {
        this.setState({ stats: { ...this.state.stats, ...newStats } });
    }
    
    addActivity(activity) {
        const newActivities = [activity, ...this.state.recentActivities];
        this.setState({ recentActivities: newActivities.slice(0, 10) }); // Mantieni solo ultimi 10
    }
    
    resetDailyStats() {
        this.setState({ 
            stats: { ...this.state.stats, newProductsToday: 0 }
        });
        this.addActivity({
            id: Date.now(),
            type: 'system',
            icon: 'fas fa-history',
            description: 'Statistiche giornaliere resettate.',
            timestamp: new Date().toLocaleTimeString('it-IT'),
            status: 'success'
        });
    }
    
    // Historical Search Actions
    updateHistoricalSearch(search) {
        this.setState({ historicalSearch: { ...this.state.historicalSearch, ...search } });
    }
    
    setHistoricalResults(results) {
        this.setState({ historicalResults: results });
    }
    
    clearHistoricalSearch() {
        this.setState({ 
            historicalSearch: { productName: '', brand: '', date: '' },
            historicalResults: []
        });
    }
    
    // Chart Actions
    setActivityChart(chart) {
        this.setState({ activityChart: chart });
    }
    
    setPriceChart(chart) {
        this.setState({ priceChart: chart });
    }
    
    destroyActivityChart() {
        if (this.state.activityChart) {
            this.state.activityChart.destroy();
            this.setState({ activityChart: null });
        }
    }
    
    destroyPriceChart() {
        if (this.state.priceChart) {
            this.state.priceChart.destroy();
            this.setState({ priceChart: null });
        }
    }

    // Google Search Actions
    updateGoogleSearchData(data) {
        this.setState({ googleSearchData: { ...this.state.googleSearchData, ...data } });
    }
    
    clearGoogleSearchData() {
        this.setState({ 
            googleSearchData: { name: '', brand: '', price: '', source: '' },
            googleSearchResults: []
        });
    }
    
    setGoogleSearchResults(results) {
        this.setState({ googleSearchResults: results });
    }
    
    // AI Model Actions
    setSelectedAIModel(model) {
        this.setState({ selectedAIModel: model });
    }

    stopScraping() {
        this.state.canStopScraping = true;
        this.state.isScraping = false;
        this.state.isScrapingGeneric = false;
        
        // Aggiorna lo stato per fermare tutti i processi attivi
        this.setState({
            canStopScraping: true,
            isScraping: false,
            isScrapingGeneric: false
        });
        
        console.log('🛑 Scraping fermato dall\'utente');
    }
    
    // Getter protetto per selectedDomains
    getSelectedDomains() {
        // Se selectedDomains non è definito o non è un array, restituisci array vuoto
        if (!this.state.selectedDomains || !Array.isArray(this.state.selectedDomains)) {
            console.warn('⚠️ selectedDomains non è un array, resetto a array vuoto:', this.state.selectedDomains);
            this.state.selectedDomains = [];
        }
        return this.state.selectedDomains;
    }
    
    // Setter protetto per selectedDomains
    setSelectedDomains(domains) {
        // Assicurati che domains sia sempre un array
        if (!Array.isArray(domains)) {
            console.warn('⚠️ Tentativo di impostare selectedDomains con valore non-array:', domains);
            domains = [];
        }
        this.state.selectedDomains = domains;
    }
}
