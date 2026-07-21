// Store methods split out of store.js for the 900-line file guard.
// Behavior-preserving: prototype augmentation, loaded AFTER store.js (class def)
// and BEFORE store.init.js (instantiation). Relies on global `Store`.
Object.assign(Store.prototype, {
    // Dashboard Actions
    async loadInitialDashboardData() {
        try {
            console.log('📊 Caricamento dati iniziali dashboard...');
            
            // Carica statistiche dal database
            const response = await fetch('/dashboard-stats');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                
                // Aggiorna le statistiche con i dati reali
                this.setState({
                    stats: {
                        totalProducts: stats.total_products || 0,
                        newProductsToday: stats.new_products_today || 0,
                        sitesMonitored: stats.sites_monitored || 0,
                        activeSites: stats.active_sites || 0,
                        extractionsToday: stats.extractions_today || 0,
                        aiAccuracy: stats.ai_accuracy || 0,
                        aiModel: stats.ai_model || 'N/A',
                        avgResponseTime: stats.avg_response_time || 0,
                        uptime: stats.uptime || 0,
                        totalSites: stats.total_sites || 0,
                        categoryStats: stats.category_stats || []
                    }
                });
                
                // Carica attività recenti dal database
                await this.loadRecentActivities();

                // Fallback: se +oggi è 0 ma le attività di oggi hanno prodotti, calcola dal frontend
                try {
                    const today = new Date().toISOString().split('T')[0];
                    console.log('🔍 DEBUG: Calcolo +oggi, data oggi:', today);
                    console.log('🔍 DEBUG: Attività disponibili:', this.state.recentActivities);
                    
                    const sumToday = (this.state.recentActivities || []).reduce((sum, act) => {
                        try {
                            const d = new Date(act.rawTimestamp || act.timestamp);
                            if (isNaN(d.getTime())) {
                                // Timestamp mancante o non valido: salta questa attività
                                return sum;
                            }
                            const actDate = d.toISOString().split('T')[0];
                            console.log(`🔍 DEBUG: Attività ${act.id}, timestamp: ${act.rawTimestamp || act.timestamp}, data: ${actDate}, prodotti: ${act.productsFound}`);
                            return actDate === today ? sum + (act.productsFound || 0) : sum;
                        } catch (e) {
                            console.error('🔍 DEBUG: Errore parsing timestamp per +oggi:', e, 'per attività:', act);
                            return sum;
                        }
                    }, 0);
                    
                    console.log('🔍 DEBUG: Somma prodotti oggi calcolata:', sumToday);
                    console.log('🔍 DEBUG: Valore attuale newProductsToday:', this.state.stats.newProductsToday);
                    
                    // Aggiorna sempre se il valore calcolato è maggiore di quello attuale
                    if (sumToday > (this.state.stats.newProductsToday || 0)) {
                        console.log('🔍 DEBUG: Aggiorno +oggi da', this.state.stats.newProductsToday, 'a:', sumToday);
                        this.updateState('stats.newProductsToday', sumToday);
                    } else if ((this.state.stats.newProductsToday || 0) === 0 && sumToday > 0) {
                        console.log('🔍 DEBUG: Aggiorno +oggi da 0 a:', sumToday);
                        this.updateState('stats.newProductsToday', sumToday);
                    }
                } catch (e) {
                    console.error('🔍 DEBUG: Errore calcolo +oggi:', e);
                }
                
                // Carica top categorie dal database
                await this.loadTopCategories();
                
                // Carica dati performance per sito
                await this.loadSitePerformanceData();
                
                // IMPORTANTE: Inizializza i grafici DOPO aver caricato tutti i dati
                console.log('🔧 Tentativo inizializzazione grafici...');
                console.log('🔧 chartManager disponibile:', !!window.chartManager);
                console.log('🔧 chartManager type:', typeof window.chartManager);
                
                if (window.chartManager) {
                    console.log('🔧 Inizializzazione grafici con dati reali...');
                    try {
                        const activityChart = window.chartManager.initializeActivityChart();
                        const performanceChart = window.chartManager.initializePerformanceChart();
                        console.log('🔧 Grafici creati:', { activityChart: !!activityChart, performanceChart: !!performanceChart });
                        
                        // FORZA AGGIORNAMENTO GRAFICI con dati reali
                        console.log('🔧 Forzando aggiornamento grafici con dati reali...');
                        console.log('🔧 chartManager disponibile:', !!window.chartManager);
                        console.log('🔧 activityChart disponibile:', !!activityChart);
                        console.log('🔧 performanceChart disponibile:', !!performanceChart);
                        
                        if (activityChart && window.chartManager) {
                            console.log('🔧 Chiamando updateActivityChart...');
                            try {
                                // Passa le attività recenti se disponibili
                                const recentActivities = this.state.recentActivities || [];
                                console.log('🔧 DEBUG: Attività da passare al ChartManager:', recentActivities);
                                console.log('🔧 DEBUG: Tipo di attività:', typeof recentActivities);
                                console.log('🔧 DEBUG: Lunghezza attività:', recentActivities.length);
                                console.log('🔧 DEBUG: Prima attività:', recentActivities[0]);
                                
                                // Verifica che il metodo esista
                                if (typeof window.chartManager.updateActivityChart === 'function') {
                                    console.log('✅ Metodo updateActivityChart disponibile');
                                    window.chartManager.updateActivityChart(recentActivities);
                                    console.log('🔧 updateActivityChart completato con', recentActivities.length, 'attività');
                                } else {
                                    console.error('❌ Metodo updateActivityChart non disponibile');
                                    console.log('🔍 Metodi disponibili in chartManager:', Object.getOwnPropertyNames(window.chartManager));
                                }
                            } catch (error) {
                                console.error('❌ Errore updateActivityChart:', error);
                                console.error('❌ Stack trace:', error.stack);
                            }
                        } else {
                            console.warn('⚠️ activityChart o chartManager non disponibili');
                        }
                        
                        if (performanceChart && window.chartManager) {
                            console.log('🔧 Chiamando updatePerformanceChart...');
                            try {
                                window.chartManager.updatePerformanceChart();
                                console.log('🔧 updatePerformanceChart completato');
                            } catch (error) {
                                console.error('❌ Errore updatePerformanceChart:', error);
                            }
                        } else {
                            console.warn('⚠️ performanceChart o chartManager non disponibili');
                        }
                        
                        console.log('🔧 Grafici aggiornati con dati reali');
                        
                        // VERIFICA FINALE: controlla se il valore è stato aggiornato correttamente
                        console.log('🔍 VERIFICA FINALE: newProductsToday dopo aggiornamento:', this.state.stats.newProductsToday);
                        console.log('🔍 VERIFICA FINALE: Store state completo:', this.state.stats);
                        
                        // FORZA AGGIORNAMENTO TEMPLATE
                        console.log('🔧 Forzando aggiornamento template...');
                        this.notifyListeners();
                        console.log('🔧 Template aggiornato');
                        
                        // VERIFICA FINALE: controlla se il valore è stato propagato
                        setTimeout(() => {
                            console.log('🔍 VERIFICA FINALE DOPO 100ms: newProductsToday:', this.state.stats.newProductsToday);
                            console.log('🔍 VERIFICA FINALE DOPO 100ms: Store state completo:', this.state.stats);
                        }, 100);
                    } catch (error) {
                        console.error('❌ Errore inizializzazione grafici:', error);
                    }
                } else {
                    console.warn('⚠️ chartManager non disponibile, grafici non inizializzati');
                }
                
                console.log('✅ Dashboard inizializzata con dati reali:', stats);
                
            } else {
                console.warn('⚠️ Errore caricamento statistiche iniziali:', data.error);
            }
            
        } catch (error) {
            console.error('❌ Errore caricamento dati iniziali dashboard:', error);
        }
    },
    
    // Carica attività recenti dal database
    async loadRecentActivities() {
        try {
            console.log('📋 Caricamento attività recenti...');
            
            // Carica sessioni di estrazione recenti
            const response = await fetch('/extraction-sessions/recent');
            const data = await response.json();
            
            if (data.success) {
                console.log('🔍 DEBUG: Dati ricevuti dal backend:', data);
                console.log('🔍 DEBUG: Prima sessione:', data.sessions[0]);
                
                const activities = data.sessions.map(session => ({
                    id: session.id || Date.now(),
                    type: session.activity_type || this._getActivityType(session.session_type || 'extraction'),
                    icon: session.icon || this._getActivityIcon(session.session_type || 'extraction'),
                    description: session.description || this._getActivityDescription(session),
                    // Mantieni sia timestamp RAW (ISO) che quello formattato per la UI
                    rawTimestamp: (session.start_time || session.created_at),
                    timestamp: this.formatTimestamp(session.start_time || session.created_at),
                    status: session.success ? 'success' : 'error',
                    productsFound: session.products_found || 0,
                    duration: session.duration,
                    // DEBUG: Log della durata
                    _debug_duration: session.duration,
                    siteName: session.site_name,
                    additionalInfo: [
                        ...(session.additional_info || []),
                        `Durata: ${session.duration || 'N/A'}`
                    ]
                }));
                
                // Se non ci sono attività, crea alcune attività di esempio per evitare grafico vuoto
                if (activities.length === 0) {
                    const now = new Date();
                    activities.push({
                        id: 'demo-1',
                        type: 'scrape',
                        icon: 'fas fa-spider',
                        description: 'Nessuna attività recente - Inizia lo scraping per vedere i dati',
                        timestamp: this.formatTimestamp(now.toISOString()),
                        status: 'info',
                        productsFound: 0,
                        duration: null,
                        siteName: 'Demo',
                        additionalInfo: ['Durata: N/A']
                    });
                }
                
                this.setState({ recentActivities: activities });
                
                // DEBUG: Log delle attività finali
                console.log('🔍 DEBUG: Attività mappate:', activities.map(a => ({
                    id: a.id,
                    duration: a.duration,
                    _debug_duration: a._debug_duration,
                    description: a.description
                })));
                
                // Aggiorna il grafico attività con i nuovi dati
                if (window.chartManager) {
                    console.log('🔧 Aggiornamento grafico attività con', activities.length, 'attività');
                    console.log('🔧 DEBUG: Attività complete:', activities);
                    console.log('🔧 DEBUG: Prima attività (dettagli):', JSON.stringify(activities[0], null, 2));
                    
                    try {
                        // Verifica che il metodo esista
                        if (typeof window.chartManager.updateActivityChart === 'function') {
                            console.log('✅ Metodo updateActivityChart disponibile in loadRecentActivities');
                            // Passa le attività direttamente al ChartManager
                            window.chartManager.updateActivityChart(activities);
                            console.log('🔧 Grafico attività aggiornato con attività passate direttamente');
                        } else {
                            console.error('❌ Metodo updateActivityChart non disponibile in loadRecentActivities');
                            console.log('🔍 Metodi disponibili in chartManager:', Object.getOwnPropertyNames(window.chartManager));
                        }
                    } catch (error) {
                        console.error('❌ Errore aggiornamento grafico attività:', error);
                        console.error('❌ Stack trace:', error.stack);
                    }
                } else {
                    console.warn('⚠️ chartManager non disponibile per aggiornamento grafico');
                }
                console.log('✅ Attività recenti caricate:', activities.length);
                
            } else {
                console.warn('⚠️ Errore caricamento attività recenti:', data.error);
            }
            
        } catch (error) {
            console.error('❌ Errore caricamento attività recenti:', error);
        }
    },
    
    // Carica top categorie dal database
    async loadTopCategories() {
        try {
            console.log('📊 Caricamento top categorie...');
            
            // Carica statistiche per categoria dal database
            const response = await fetch('/products/categories/stats');
            const data = await response.json();
            
            if (data.success) {
                const categories = data.categories.map(cat => ({
                    name: cat.category || 'Generale',
                    percentage: cat.percentage || 0,
                    color: this.getRandomColor(),
                    count: cat.count || 0
                }));
                
                this.setState({ topCategories: categories });
                console.log('✅ Top categorie caricate:', categories.length);
                
            } else {
                console.warn('⚠️ Errore caricamento top categorie:', data.error);
            }
            
        } catch (error) {
            console.error('❌ Errore caricamento top categorie:', error);
        }
    },
    
    // Carica dati per il grafico performance per sito
    async loadSitePerformanceData() {
        try {
            console.log('📊 Caricamento dati performance per sito...');
            
            // Carica statistiche per sito dal database
            const response = await fetch('/sites/performance/stats');
            const data = await response.json();
            
            if (data.success) {
                const sitePerformance = data.sites.map(site => ({
                    name: site.site || 'Sito sconosciuto',
                    successRate: site.success_rate || 0,
                    avgProducts: site.avg_products || 0,
                    avgResponseTime: site.avg_response_time || 0,
                    color: this.getRandomColor()
                }));
                
                this.setState({ sitePerformance });
                console.log('✅ Performance per sito caricate:', sitePerformance.length);
                
            } else {
                console.warn('⚠️ Errore caricamento performance sito:', data.error);
                // Crea dati di esempio se non ci sono dati reali
                this.setState({ 
                    sitePerformance: [
                        { name: 'Nessun dato', successRate: 0, avgProducts: 0, avgResponseTime: 0, color: '#6B7280' }
                    ] 
                });
            }
            
        } catch (error) {
            console.error('❌ Errore caricamento performance sito:', error);
            // Fallback con dati di esempio
            this.setState({ 
                sitePerformance: [
                    { name: 'Nessun dato', successRate: 0, avgProducts: 0, avgResponseTime: 0, color: '#6B7280' }
                ] 
            });
        }
    },
    
    // =================================================
    // HELPER METHODS PER ATTIVITÀ RECENTI
    // =================================================
    
    _getActivityType(sessionType) {
        const typeMap = {
            'extraction': 'extraction',
            'comparison': 'comparison',
            'update': 'update',
            'error': 'error'
        };
        return typeMap[sessionType] || 'extraction';
    },
    
    _getActivityIcon(sessionType) {
        const iconMap = {
            'extraction': 'fas fa-spider',
            'comparison': 'fas fa-balance-scale',
            'update': 'fas fa-sync-alt',
            'error': 'fas fa-exclamation-triangle'
        };
        return iconMap[sessionType] || 'fas fa-spider';
    },
    
    _getActivityDescription(session) {
        if (session.session_type === 'extraction') {
            const siteName = session.source || session.domain || 'sito sconosciuto';
            const productCount = session.products_found || 0;
            const duration = session.duration || 'N/A';
            return `Scraping completato su ${siteName}: ${productCount} prodotti (Durata: ${duration})`;
        } else if (session.session_type === 'comparison') {
            return `Confronto prodotti completato`;
        } else if (session.session_type === 'update') {
            return `Aggiornamento prezzi completato`;
        } else {
            return `Attività completata`;
        }
    },
    
    _prepareActivityChartData(activities) {
        // Prepara i dati per il grafico delle attività (ultimi 7 giorni)
        const last7Days = [];
        const today = new Date();
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            const dayActivities = activities.filter(activity => {
                try {
                    const activityDate = new Date(activity.timestamp);
                    return activityDate.toISOString().split('T')[0] === dateStr;
                } catch (error) {
                    return false;
                }
            });
            
            last7Days.push({
                date: dateStr,
                count: dayActivities.length,
                label: date.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })
            });
        }
        
        return last7Days;
    },
    
    // Utility per formattare timestamp
    formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);
            
            if (diffMins < 1) return 'Adesso';
            if (diffMins < 60) return `${diffMins} minuti fa`;
            if (diffHours < 24) return `${diffHours} ore fa`;
            if (diffDays < 7) return `${diffDays} giorni fa`;
            return date.toLocaleDateString('it-IT');
            
        } catch (error) {
            return 'Data sconosciuta';
        }

    },
    
    // Utility per colori casuali
    getRandomColor() {
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'];
        return colors[Math.floor(Math.random() * colors.length)];
    },
    
    // =================================================
    // AI MODELS & MONITORING METHODS
    // =================================================
    
    async loadAvailableAIModels() {
        try {
            console.log('🤖 Caricamento modelli AI disponibili...');
            
            // Per ora, usa modelli predefiniti
            const models = [
                { id: 'openai', name: 'OpenAI GPT-4', status: 'available', config: { apiKey: 'configurato' } },
                { id: 'gemini', name: 'Google Gemini', status: 'available', config: { apiKey: 'configurato' } },
                { id: 'claude', name: 'Anthropic Claude', status: 'unavailable', config: { apiKey: 'non configurato' } }
            ];
            
            this.setState({ 
                availableAIModels: models,
                selectedAIModel: 'openai'
            });
            
            console.log('✅ Modelli AI caricati:', models.length);
            
        } catch (error) {
            console.error('❌ Errore caricamento modelli AI:', error);
            this.setState({ 
                availableAIModels: [],
                selectedAIModel: 'openai'
            });
        }
    },
    
    async loadMonitoredProducts() {
        try {
            console.log('📊 Caricamento prodotti monitorati...');
            
            // Per ora, usa dati di esempio
            const monitoredProducts = [
                { id: 1, name: 'iPhone 15 Pro', url: 'https://example.com', price: '999€', status: 'active' },
                { id: 2, name: 'Samsung Galaxy S24', url: 'https://example.com', price: '899€', status: 'active' }
            ];
            
            this.setState({ monitoredProducts });
            console.log('✅ Prodotti monitorati caricati:', monitoredProducts.length);
            
        } catch (error) {
            console.error('❌ Errore caricamento prodotti monitorati:', error);
            this.setState({ monitoredProducts: [] });
        }
    },
    
    async loadPriceAlerts() {
        try {
            console.log('🔔 Caricamento allerte prezzi...');
            
            // Per ora, usa dati di esempio
            const priceAlerts = [
                { id: 1, product: 'iPhone 15 Pro', oldPrice: '1099€', newPrice: '999€', change: '-9.1%', date: new Date().toISOString() },
                { id: 2, product: 'Samsung Galaxy S24', oldPrice: '999€', newPrice: '899€', change: '-10.0%', date: new Date().toISOString() }
            ];
            
            this.setState({ priceAlerts });
            console.log('✅ Allerte prezzi caricate:', priceAlerts.length);
            
        } catch (error) {
            console.error('❌ Errore caricamento allerte prezzi:', error);
            this.setState({ priceAlerts: [] });
        }
    },
    
    async loadMonitoringStats() {
        try {
            console.log('📈 Caricamento statistiche monitoring...');
            
            // Per ora, usa dati di esempio
            const monitoringStats = {
                totalMonitored: 15,
                activeMonitors: 12,
                pausedMonitors: 2,
                errorMonitors: 1,
                priceChanges: 8,
                savings: 156.50
            };
            
            this.setState({ monitoringStats });
            console.log('✅ Statistiche monitoring caricate');
            
        } catch (error) {
            console.error('❌ Errore caricamento statistiche monitoring:', error);
            this.setState({ 
                monitoringStats: {
                    totalMonitored: 0,
                    activeMonitors: 0,
                    pausedMonitors: 0,
                    errorMonitors: 0,
                    priceChanges: 0,
                    savings: 0
                }
            });
        }
    },
    
    async loadSchedulerStats() {
        try {
            console.log('⏰ Caricamento statistiche scheduler...');
            
            // Per ora, usa dati di esempio
            const schedulerStats = {
                totalScheduled: 8,
                activeSchedules: 6,
                completedToday: 3,
                nextRun: new Date(Date.now() + 3600000).toISOString(), // 1 ora da ora
                lastRun: new Date(Date.now() - 7200000).toISOString() // 2 ore fa
            };
            
            this.setState({ schedulerStats });
            console.log('✅ Statistiche scheduler caricate');
            
        } catch (error) {
            console.error('❌ Errore caricamento statistiche scheduler:', error);
            this.setState({ 
                schedulerStats: {
                    totalScheduled: 0,
                    activeSchedules: 0,
                    completedToday: 0,
                    nextRun: null,
                    lastRun: null
                }
            });
        }
    }
});
