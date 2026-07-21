// Instantiation tail relocated from store.js (file-length guard split).
// Loaded AFTER store.js + store method files so class + prototype are ready.
// Crea un'istanza globale dello store
const store = new Store();

// Carica i dati iniziali della dashboard
store.loadInitialDashboardData();

// Esporta l'istanza
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Store, store };
} else {
    window.store = store;
} 
