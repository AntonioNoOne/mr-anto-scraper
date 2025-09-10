"""
Price Scheduler - Sistema di controlli automatici prezzi
Background task per monitoraggio continuo dei prezzi competitor
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import threading
import json
from pathlib import Path

from price_extractor import competitor_monitor
from price_monitor import price_monitor

logger = logging.getLogger(__name__)

class PriceScheduler:
    """Sistema di scheduling per controlli automatici prezzi"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.config_file = "Backend/database/scheduler_config.json"
        self.last_run_file = "Backend/database/last_run.json"
        
        # Configurazione default
        self.config = {
            'enabled': False,
            'check_interval_hours': 12,  # Controllo ogni 12 ore
            'retry_failed_after_hours': 2,  # Riprova falliti dopo 2 ore
            'max_concurrent_checks': 3,  # Max 3 controlli paralleli
            'notification_email': '',
            'send_daily_report': True,
            'send_price_alerts': True
        }
        
        self.load_config()
        logger.info("📅 Price Scheduler inizializzato")
    
    def load_config(self):
        """Carica configurazione da file"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                logger.info(f"📋 Configurazione caricata: {self.config}")
        except Exception as e:
            logger.error(f"❌ Errore caricamento config: {e}")
    
    def save_config(self):
        """Salva configurazione su file"""
        try:
            Path(self.config_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("💾 Configurazione salvata")
        except Exception as e:
            logger.error(f"❌ Errore salvataggio config: {e}")
    
    def update_config(self, new_config: Dict[str, Any]):
        """Aggiorna configurazione"""
        self.config.update(new_config)
        self.save_config()
        
        # Riavvia scheduler se necessario
        if self.is_running:
            self.stop_scheduler()
            self.start_scheduler()
    
    def save_last_run(self, run_data: Dict[str, Any]):
        """Salva dati ultimo controllo"""
        try:
            Path(self.last_run_file).parent.mkdir(parents=True, exist_ok=True)
            run_data['timestamp'] = datetime.now().isoformat()
            with open(self.last_run_file, 'w') as f:
                json.dump(run_data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Errore salvataggio last run: {e}")
    
    def get_last_run(self) -> Optional[Dict[str, Any]]:
        """Ottiene dati ultimo controllo"""
        try:
            if Path(self.last_run_file).exists():
                with open(self.last_run_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Errore lettura last run: {e}")
        return None
    
    async def run_price_check(self):
        """Esegue controllo prezzi completo"""
        logger.info("🔄 SCHEDULER: Inizio controllo prezzi automatico")
        start_time = datetime.now()
        
        try:
            # Esegui controllo completo
            results = await competitor_monitor.check_all_products_all_sites()
            
            # Salva risultati
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            run_data = {
                'duration_seconds': duration,
                'results': results,
                'status': 'completed'
            }
            
            self.save_last_run(run_data)
            
            # Log risultati
            logger.info(f"✅ SCHEDULER: Controllo completato in {duration:.1f}s")
            logger.info(f"📊 Risultati: {results['successful_checks']}/{results['total_checks']} successi")
            
            # Invia notifiche se configurate
            if self.config.get('send_price_alerts'):
                await self._check_and_send_alerts(results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ SCHEDULER: Errore controllo prezzi: {e}")
            
            run_data = {
                'duration_seconds': 0,
                'error': str(e),
                'status': 'error'
            }
            self.save_last_run(run_data)
            
            return None
    
    async def _check_and_send_alerts(self, results: Dict[str, Any]):
        """Controlla se ci sono cambi prezzo significativi e invia alert"""
        try:
            # TODO: Implementare logica di alert
            # - Confronta prezzi precedenti
            # - Identifica cambi significativi (>5% o sotto target price)
            # - Invia notifiche email/telegram
            
            significant_changes = []
            
            for detail in results.get('details', []):
                if detail.get('success') and detail.get('price'):
                    # Qui aggiungeremo la logica di confronto prezzi
                    pass
            
            if significant_changes:
                logger.info(f"🔔 ALERT: {len(significant_changes)} cambi prezzo significativi")
                # Invia notifiche
            
        except Exception as e:
            logger.error(f"❌ Errore check alerts: {e}")
    
    def _schedule_jobs(self):
        """Configura job schedule"""
        schedule.clear()  # Pulisci job esistenti
        
        if not self.config.get('enabled'):
            logger.info("📅 Scheduler disabilitato")
            return
        
        interval_hours = self.config.get('check_interval_hours', 12)
        
        # Job principale controllo prezzi
        schedule.every(interval_hours).hours.do(self._run_async_job, self.run_price_check)
        
        # Job giornaliero report (se abilitato)
        if self.config.get('send_daily_report'):
            schedule.every().day.at("09:00").do(self._run_async_job, self.generate_daily_report)
        
        logger.info(f"📅 Job schedulati: controllo ogni {interval_hours}h")
    
    def _run_async_job(self, async_func):
        """Wrapper per eseguire funzioni async nei job"""
        try:
            asyncio.run(async_func())
        except Exception as e:
            logger.error(f"❌ Errore job async: {e}")
    
    def _scheduler_worker(self):
        """Worker thread per scheduler"""
        logger.info("🚀 SCHEDULER: Thread worker avviato")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check ogni minuto
            except Exception as e:
                logger.error(f"❌ SCHEDULER: Errore worker: {e}")
                time.sleep(60)
        
        logger.info("🛑 SCHEDULER: Thread worker fermato")
    
    def start_scheduler(self):
        """Avvia scheduler in background"""
        if self.is_running:
            logger.warning("⚠️ Scheduler già avviato")
            return
        
        if not self.config.get('enabled'):
            logger.info("📅 Scheduler disabilitato - non avviato")
            return
        
        self.is_running = True
        self._schedule_jobs()
        
        # Avvia thread worker
        self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ SCHEDULER: Avviato con successo")
    
    def stop_scheduler(self):
        """Ferma scheduler"""
        if not self.is_running:
            logger.warning("⚠️ Scheduler già fermato")
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("🛑 SCHEDULER: Fermato")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Ottiene stato scheduler"""
        last_run = self.get_last_run()
        
        return {
            'is_running': self.is_running,
            'config': self.config,
            'last_run': last_run,
            'next_run': self._get_next_run_time(),
            'scheduled_jobs': len(schedule.jobs)
        }
    
    def _get_next_run_time(self) -> Optional[str]:
        """Calcola prossimo run time"""
        try:
            if schedule.jobs:
                next_run = schedule.next_run()
                return next_run.isoformat() if next_run else None
        except:
            pass
        return None
    
    async def generate_daily_report(self):
        """Genera report giornaliero"""
        try:
            logger.info("📊 SCHEDULER: Generazione report giornaliero")
            
            # Ottieni dati dashboard
            dashboard_data = price_monitor.get_monitoring_dashboard_data()
            
            # Calcola statistiche
            total_products = dashboard_data.get('total_products', 0)
            total_sites = dashboard_data.get('total_sites', 0)
            
            # TODO: Implementare invio email report
            # - Statistiche generali
            # - Top 5 migliori offerte
            # - Prodotti con cambi prezzo significativi
            # - Grafici trend settimanali
            
            logger.info(f"📧 Report giornaliero: {total_products} prodotti, {total_sites} siti")
            
        except Exception as e:
            logger.error(f"❌ Errore generazione report: {e}")
    
    async def manual_check(self) -> Dict[str, Any]:
        """Controllo manuale (forzato)"""
        logger.info("🔧 SCHEDULER: Controllo manuale richiesto")
        return await self.run_price_check()

# Singleton scheduler globale
price_scheduler = PriceScheduler()

# Auto-start DISABILITATO per evitare controlli automatici indesiderati
# if price_scheduler.config.get('enabled') and price_scheduler.config.get('auto_start', True):
#     price_scheduler.start_scheduler()
    
print("🛑 Scheduler AUTO-START disabilitato - Avvio manuale richiesto") 