// Modulo per la gestione delle API
class API {
    constructor(baseUrl = CONFIG.API_BASE_URL) {
        this.baseUrl = baseUrl;
        this.axios = axios.create({
            baseURL: baseUrl,
            timeout: 300000, // 5 minuti per operazioni lunghe come Google Search
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // Interceptor per gestire gli errori
        this.axios.interceptors.response.use(
            response => response,
            error => {
                console.error('API Error:', error);
                return Promise.reject(error);
            }
        );
    }
    
    // =================================================
    // SCRAPING API
    // =================================================
    
    async scrapeSingleUrl(url) {
        try {
            const response = await this.axios.post('/scrape', { url });
            return response.data;
        } catch (error) {
            throw new Error(`Errore scraping singolo: ${error.message}`);
        }
    }
    
    async fastExtract(url) {
        try {
            const response = await this.axios.post('/fast-extract', { url });
            return response.data;
        } catch (error) {
            throw new Error(`Errore estrazione veloce: ${error.message}`);
        }
    }
    
    async stopScraping() {
        try {
            const response = await this.axios.post('/stop-scraping');
            return response.data;
        } catch (error) {
            throw new Error(`Errore richiesta stop: ${error.message}`);
        }
    }
    
    // =================================================
    // COMPARISON API
    // =================================================
    
    async compareProducts(results, selectedDomains = null) {
        try {
            const requestData = { results };
            
            // Aggiungi domini selezionati se forniti
            if (selectedDomains && selectedDomains.length > 0) {
                requestData.sources = selectedDomains;
                console.log('🎯 API: Invio domini selezionati:', selectedDomains);
            }
            
            const response = await this.axios.post('/compare-products', requestData);
            return response.data;
        } catch (error) {
            throw new Error(`Errore confronto prodotti: ${error.message}`);
        }
    }
    
    async comparePrices(products) {
        try {
            const response = await this.axios.post('/compare-prices', { products });
            return response.data;
        } catch (error) {
            throw new Error(`Errore confronto prezzi: ${error.message}`);
        }
    }
    
    // =================================================
    // MONITORING API
    // =================================================
    
    async addProductToMonitoring(productData) {
        try {
            const response = await this.axios.post('/monitoring/add-product', productData);
            return response.data;
        } catch (error) {
            throw new Error(`Errore aggiunta al monitoring: ${error.message}`);
        }
    }
    
    async getMonitoredProducts() {
        try {
            const response = await this.axios.get('/monitoring/products');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento prodotti monitorati: ${error.message}`);
        }
    }
    
    async getPriceAlerts(unreadOnly = true, limit = 10) {
        try {
            const response = await this.axios.get(`/monitoring/alerts?unread_only=${unreadOnly}&limit=${limit}`);
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento alert: ${error.message}`);
        }
    }
    
    async getMonitoringStats() {
        try {
            const response = await this.axios.get('/monitoring/stats');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento statistiche monitoring: ${error.message}`);
        }
    }
    
    async checkPrices() {
        try {
            const response = await this.axios.post('/monitoring/check-prices');
            return response.data;
        } catch (error) {
            throw new Error(`Errore controllo prezzi: ${error.message}`);
        }
    }
    
    // =================================================
    // SCHEDULER API
    // =================================================
    
    async getSchedulerStats() {
        try {
            const response = await this.axios.get('/scheduler/stats');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento statistiche scheduler: ${error.message}`);
        }
    }
    
    // =================================================
    // HISTORICAL PRODUCTS API
    // =================================================
    
    async searchHistoricalProducts(params) {
        try {
            const queryString = new URLSearchParams(params).toString();
            const response = await this.axios.get(`/historical-products?${queryString}`);
            return response.data;
        } catch (error) {
            throw new Error(`Errore ricerca prodotti storici: ${error.message}`);
        }
    }
    
    // =================================================
    // CHAT AI API
    // =================================================
    
    async sendChatMessage(message, model, conversationHistory, contextData) {
        try {
            const response = await this.axios.post('/chat', {
                message,
                model,
                conversation_history: conversationHistory,
                context_data: contextData
            });
            return response.data;
        } catch (error) {
            throw new Error(`Errore chat AI: ${error.message}`);
        }
    }
    
    async getAvailableAIModels() {
        try {
            const response = await this.axios.get('/chat/models');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento modelli AI: ${error.message}`);
        }
    }

    // =================================================
    // GOOGLE SEARCH API
    // =================================================
    
    async searchAlternativeVendors(productData) {
        try {
            // Timeout dinamico basato sul tipo di operazione
            const timeout = 600000; // 10 minuti per Google Search
            
            const response = await this.axios.post('/google-search', productData, {
                timeout: timeout
            });
            return response.data;
        } catch (error) {
            if (error.code === 'ECONNABORTED') {
                throw new Error(`Timeout ricerca Google: l'operazione ha impiegato troppo tempo. Riprova.`);
            }
            throw new Error(`Errore ricerca Google: ${error.message}`);
        }
    }
    
    // =================================================
    // DASHBOARD API
    // =================================================
    
    async getDashboardStats() {
        try {
            const response = await this.axios.get('/dashboard-stats');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento statistiche dashboard: ${error.message}`);
        }
    }
    
    async getRecentExtractionSessions() {
        try {
            const response = await this.axios.get('/extraction-sessions/recent');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento attività recenti: ${error.message}`);
        }
    }
    
    async getProductCategoriesStats() {
        try {
            const response = await this.axios.get('/products/categories/stats');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento statistiche categorie: ${error.message}`);
        }
    }
    
    // =================================================
    // AI CONFIG API
    // =================================================
    
    async getAIConfig() {
        try {
            const response = await this.axios.get('/ai-config');
            return response.data;
        } catch (error) {
            throw new Error(`Errore caricamento configurazione AI: ${error.message}`);
        }
    }
    
    async saveAIConfig(config) {
        try {
            const response = await this.axios.post('/ai-config', config);
            return response.data;
        } catch (error) {
            throw new Error(`Errore salvataggio configurazione AI: ${error.message}`);
        }
    }
    
    // =================================================
    // UTILITY METHODS
    // =================================================
    
    formatBytes(bytes, decimals = 2) {
        if (!bytes) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    getSiteName(url) {
        try {
            const domain = new URL(url).hostname;
            return domain.replace('www.', '').split('.')[0].toUpperCase();
        } catch {
            return 'Sito';
        }
    }
    
    getRandomColor() {
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    // =================================================
    // ERROR HANDLING
    // =================================================
    
    handleError(error, context = '') {
        console.error(`API Error in ${context}:`, error);
        
        if (error.response) {
            // Server ha risposto con un codice di errore
            const status = error.response.status;
            const message = error.response.data?.error || error.response.data?.message || 'Errore del server';
            
            switch (status) {
                case 400:
                    throw new Error(`Dati non validi: ${message}`);
                case 401:
                    throw new Error('Non autorizzato. Verifica le credenziali.');
                case 403:
                    throw new Error('Accesso negato.');
                case 404:
                    throw new Error('Risorsa non trovata.');
                case 500:
                    throw new Error('Errore interno del server.');
                default:
                    throw new Error(`Errore ${status}: ${message}`);
            }
        } else if (error.request) {
            // Richiesta fatta ma nessuna risposta
            throw new Error(CONFIG.ERROR_MESSAGES.NETWORK_ERROR);
        } else {
            // Errore nella configurazione della richiesta
            throw new Error(`Errore di configurazione: ${error.message}`);
        }
    }
}

// Crea un'istanza globale dell'API
const api = new API();

// Esporta l'istanza
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API, api };
} else {
    window.api = api;
} 