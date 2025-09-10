// Configurazione principale dell'applicazione
const CONFIG = {
    // API Configuration
    API_BASE_URL: 'http://127.0.0.1:8000',
    
    // UI Configuration
    UI: {
        CHAT_SIDEBAR_WIDTH: 450,
        MIN_WINDOW_WIDTH: 1200,
        AUTO_REFRESH_INTERVAL: 120000, // 2 minuti (ridotto da 30 secondi)
        CHART_ANIMATION_DURATION: 1000,
        FADE_IN_DURATION: 500
    },
    
    // Default Data
    DEFAULT_STATS: {
        totalProducts: 1247,
        newProductsToday: 23,
        aiAccuracy: 94,
        aiModel: 'GPT-4',
        sitesMonitored: 12,
        activeSites: 9,
        avgResponseTime: 280,
        uptime: 99.8
    },
    
    // Default Categories
    DEFAULT_CATEGORIES: [
        { name: 'Elettronica', percentage: 35, color: '#3b82f6' },
        { name: 'Abbigliamento', percentage: 28, color: '#10b981' },
        { name: 'Casa & Giardino', percentage: 22, color: '#f59e0b' },
        { name: 'Sport', percentage: 15, color: '#8b5cf6' }
    ],
    
    // Default Recent Activities
    DEFAULT_ACTIVITIES: [
        {
            id: 1,
            type: 'scrape',
            icon: 'fas fa-spider',
            description: 'Scraping completato su Amazon.it',
            timestamp: '2 minuti fa',
            status: 'success'
        },
        {
            id: 2,
            type: 'analysis',
            icon: 'fas fa-brain',
            description: 'Analisi AI su 45 prodotti completata',
            timestamp: '5 minuti fa',
            status: 'success'
        },
        {
            id: 3,
            type: 'update',
            icon: 'fas fa-sync',
            description: 'Aggiornamento prezzi in corso',
            timestamp: '12 minuti fa',
            status: 'processing'
        }
    ],
    
    // Scraper Configuration
    SCRAPER_CONFIG: {
        url: '',
        depth: 1,
        delay: 1000,
        useAI: true,
        saveImages: false
    },
    
    // Monitoring Configuration
    MONITORING_CONFIG: {
        frequency: 'daily',
        priceThreshold: 5,
        notifications: {
            priceDecrease: true,
            priceIncrease: true,
            unavailable: true
        },
        email: ''
    },
    
    // AI Models Configuration
    AI_MODELS: {
        openai: { available: false, status: 'Non configurato' },
        ollama: { available: false, status: 'Non disponibile' },
        gemini: { available: false, status: 'Non configurato' }
    },
    
    // System Settings
    SYSTEM_SETTINGS: {
        scrapingTimeout: 60,
        maxProducts: 100,
        requestDelay: 1000,
        debugMode: false
    },
    
    // Section Titles and Descriptions
    SECTIONS: {
        dashboard: {
            title: 'Dashboard Riepilogativa',
            description: 'Una visione d\'insieme delle tue attività di scraping.'
        },
        scraping: {
            title: 'Scraping Generico',
            description: 'Estrai prodotti da uno o più URL utilizzando il sistema AI ottimizzato.'
        },
        comparison: {
            title: 'Confronto Prodotti',
            description: 'Confronta prodotti con nome uguale e analizza gli scostamenti di prezzo.'
        },
        'google-search': {
            title: 'Google Search',
            description: 'Trova venditori alternativi per i tuoi prodotti usando Google Search.'
        },
        scheduling: {
            title: 'Scheduling & Monitoring',
            description: 'Monitora i prodotti e ricevi notifiche sui cambiamenti di prezzo.'
        },
        'system-config': {
            title: 'Configurazione Sistema',
            description: 'Controlla il comportamento del browser e le impostazioni anti-bot per lo scraping.'
        },
        chat: {
            title: 'Chat AI',
            description: 'Interagisci con i tuoi dati attraverso l\'intelligenza artificiale.'
        }
    },
    
    // Chart Colors
    CHART_COLORS: {
        primary: 'rgba(16, 185, 129, 1)',
        primaryBg: 'rgba(16, 185, 129, 0.2)',
        secondary: 'rgba(59, 130, 246, 1)',
        secondaryBg: 'rgba(59, 130, 246, 0.2)',
        accent: 'rgba(139, 92, 246, 1)',
        accentBg: 'rgba(139, 92, 246, 0.2)'
    },
    
    // Local Storage Keys
    STORAGE_KEYS: {
        STATS: 'jusper_stats',
        SETTINGS: 'jusper_settings',
        CHAT_HISTORY: 'jusper_chat_history',
        SELECTED_PRODUCTS: 'jusper_selected_products'
    },
    
    // Error Messages
    ERROR_MESSAGES: {
        NETWORK_ERROR: 'Errore di connessione. Verifica che il server sia attivo.',
        API_ERROR: 'Errore del server. Riprova più tardi.',
        VALIDATION_ERROR: 'Dati non validi. Controlla i campi inseriti.',
        PERMISSION_ERROR: 'Non hai i permessi per eseguire questa operazione.',
        TIMEOUT_ERROR: 'Operazione scaduta. Riprova.'
    },
    
    // Success Messages
    SUCCESS_MESSAGES: {
        SCRAPING_COMPLETED: 'Scraping completato con successo!',
        COMPARISON_COMPLETED: 'Confronto prodotti completato!',
        MONITORING_STARTED: 'Monitoring avviato con successo!',
        SETTINGS_SAVED: 'Impostazioni salvate con successo!',
        CHAT_MESSAGE_SENT: 'Messaggio inviato con successo!'
    }
};

// Esporta la configurazione
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
} 