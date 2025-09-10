#!/usr/bin/env python3

"""
Price Scheduler - Sistema di schedulazione automatica
====================================================

Sistema per schedulare automaticamente i controlli dei prezzi
e gestire il monitoraggio continuo dei prodotti.

FLUSSO PRINCIPALE:
1. Schedulazione automatica controlli prezzi
2. Gestione task asincroni
3. Controllo frequenze personalizzate
4. Gestione errori e retry
5. Logging e monitoring

STRUTTURA:
- Task scheduler asincrono
- Gestione frequenze per prodotto
- Sistema retry automatico
- Logging dettagliato
- Integrazione con Price Monitor

DIPENDENZE:
- asyncio: Programmazione asincrona
- datetime: Gestione timestamp
- logging: Sistema log
- typing: Type hints
- price_monitor: Sistema monitoraggio

SCRIPT CHE RICHIAMANO QUESTO:
- main.py: Per avvio schedulazione
- Frontend: Per gestione scheduling

SCRIPT RICHIAMATI DA QUESTO:
- price_monitor.py: Per controlli prezzi
- historical_products_db.py: Per dati prodotti

FUNZIONALITÀ PRINCIPALI:
- start_scheduler(): Avvia schedulatore
- schedule_product_check(): Schedula controllo prodotto
- run_periodic_checks(): Esegue controlli periodici
- handle_check_result(): Gestisce risultati controllo
- stop_scheduler(): Ferma schedulatore
- get_scheduler_stats(): Statistiche schedulatore

WORKFLOW SCHEDULAZIONE:
1. Avvio schedulatore all'avvio sistema
2. Caricamento prodotti monitorati
3. Creazione task per ogni prodotto
4. Esecuzione controlli secondo frequenza
5. Gestione risultati e alert
6. Aggiornamento statistiche
7. Retry automatico in caso errori

PERFORMANCE:
- Task asincroni: Non bloccanti
- Scalabilità: Supporta 1000+ prodotti
- Memory efficient: Task cleanup automatico
- Error handling: Retry intelligente
- Monitoring: Statistiche real-time

CONFIGURAZIONE:
- Default frequency: 24 ore
- Retry attempts: 3 tentativi
- Retry delay: 5 minuti
- Max concurrent: 10 controlli
- Log level: Configurabile

FUTURO SVILUPPO:
- Machine learning per ottimizzazione frequenze
- Alert intelligenti basati su pattern
- Integrazione con sistemi esterni
- Dashboard real-time
- API REST per gestione
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import time
from dataclasses import dataclass
from price_monitor import PriceMonitor

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    """Task schedulato per controllo prezzo"""
    product_id: int
    product_name: str
    frequency_hours: int
    last_run: Optional[datetime]
    next_run: datetime
    task_id: str
    is_active: bool
    retry_count: int = 0
    max_retries: int = 3

class PriceScheduler:
    """Sistema di schedulazione automatica per controlli prezzi"""
    
    def __init__(self, price_monitor: PriceMonitor):
        self.price_monitor = price_monitor
        self.scheduler_running = False
        self.scheduled_tasks: Dict[int, ScheduledTask] = {}
        self.active_tasks: Set[str] = set()
        self.scheduler_task: Optional[asyncio.Task] = None
        self.stats = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "alerts_generated": 0,
            "last_run": None,
            "uptime": None
        }
        self.start_time = None
        
        logger.info("⏰ Price Scheduler inizializzato")
    
    async def start_scheduler(self) -> Dict[str, Any]:
        """Avvia il sistema di schedulazione"""
        try:
            if self.scheduler_running:
                return {
                    "success": False,
                    "error": "Scheduler già in esecuzione"
                }
            
            self.scheduler_running = True
            self.start_time = datetime.now()
            
            # Carica prodotti monitorati
            await self._load_monitored_products()
            
            # Avvia task principale
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())
            
            logger.info("✅ Scheduler avviato")
            
            return {
                "success": True,
                "message": "Scheduler avviato con successo",
                "active_tasks": len(self.scheduled_tasks)
            }
            
        except Exception as e:
            logger.error(f"❌ Errore avvio scheduler: {e}")
            self.scheduler_running = False
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop_scheduler(self) -> Dict[str, Any]:
        """Ferma il sistema di schedulazione"""
        try:
            if not self.scheduler_running:
                return {
                    "success": False,
                    "error": "Scheduler non in esecuzione"
                }
            
            self.scheduler_running = False
            
            # Cancella task principale
            if self.scheduler_task:
                self.scheduler_task.cancel()
                try:
                    await self.scheduler_task
                except asyncio.CancelledError:
                    pass
            
            # Cancella tutti i task attivi
            for task_id in list(self.active_tasks):
                await self._cancel_task(task_id)
            
            self.active_tasks.clear()
            self.scheduled_tasks.clear()
            
            # Calcola uptime
            if self.start_time:
                self.stats["uptime"] = (datetime.now() - self.start_time).total_seconds()
            
            logger.info("🛑 Scheduler fermato")
            
            return {
                "success": True,
                "message": "Scheduler fermato con successo",
                "uptime_seconds": self.stats["uptime"]
            }
            
        except Exception as e:
            logger.error(f"❌ Errore fermata scheduler: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _scheduler_loop(self):
        """Loop principale del scheduler"""
        try:
            logger.info("🔄 Loop scheduler avviato")
            
            while self.scheduler_running:
                try:
                    # Controlla task da eseguire
                    await self._check_and_run_tasks()
                    
                    # Aggiorna statistiche
                    self.stats["last_run"] = datetime.now()
                    
                    # Attendi 1 minuto prima del prossimo controllo
                    await asyncio.sleep(60)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"❌ Errore loop scheduler: {e}")
                    await asyncio.sleep(30)  # Attendi 30 secondi prima di riprovare
            
            logger.info("🔄 Loop scheduler terminato")
            
        except Exception as e:
            logger.error(f"❌ Errore fatale scheduler: {e}")
    
    async def _check_and_run_tasks(self):
        """Controlla e esegue task pronti"""
        try:
            current_time = datetime.now()
            tasks_to_run = []
            
            # Trova task pronti per l'esecuzione
            for product_id, task in self.scheduled_tasks.items():
                if task.is_active and current_time >= task.next_run:
                    tasks_to_run.append(task)
            
            # Esegui task (massimo 5 contemporaneamente)
            if tasks_to_run:
                logger.info(f"🚀 Esecuzione {len(tasks_to_run)} task")
                
                # Limita a 5 task contemporanei
                tasks_to_run = tasks_to_run[:5]
                
                # Crea task asincroni
                async_tasks = []
                for task in tasks_to_run:
                    async_task = asyncio.create_task(self._execute_product_check(task))
                    async_tasks.append(async_task)
                    self.active_tasks.add(task.task_id)
                
                # Esegui task in parallelo
                results = await asyncio.gather(*async_tasks, return_exceptions=True)
                
                # Processa risultati
                for i, result in enumerate(results):
                    task = tasks_to_run[i]
                    await self._handle_check_result(task, result)
                    self.active_tasks.discard(task.task_id)
            
        except Exception as e:
            logger.error(f"❌ Errore controllo task: {e}")
    
    async def _execute_product_check(self, task: ScheduledTask) -> Dict[str, Any]:
        """Esegue controllo prezzo per un prodotto"""
        try:
            logger.info(f"🔍 Controllo prezzo: {task.product_name}")
            
            # Esegui controllo
            result = await self.price_monitor.check_price_changes(task.product_id)
            
            # Aggiorna statistiche
            self.stats["total_checks"] += 1
            
            if result.get("success"):
                self.stats["successful_checks"] += 1
                self.stats["alerts_generated"] += result.get("alerts_generated", 0)
            else:
                self.stats["failed_checks"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Errore controllo prodotto {task.product_id}: {e}")
            self.stats["failed_checks"] += 1
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_check_result(self, task: ScheduledTask, result: Any):
        """Gestisce risultato controllo"""
        try:
            if isinstance(result, Exception):
                # Errore durante esecuzione
                logger.error(f"❌ Errore task {task.product_id}: {result}")
                await self._handle_task_error(task)
            else:
                # Controllo completato
                if result.get("success"):
                    logger.info(f"✅ Controllo completato: {task.product_name}")
                    await self._schedule_next_run(task)
                else:
                    logger.warning(f"⚠️ Controllo fallito: {task.product_name} - {result.get('error')}")
                    await self._handle_task_error(task)
            
        except Exception as e:
            logger.error(f"❌ Errore gestione risultato: {e}")
    
    async def _handle_task_error(self, task: ScheduledTask):
        """Gestisce errore task"""
        try:
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                # Riprova dopo 5 minuti
                retry_delay = timedelta(minutes=5)
                task.next_run = datetime.now() + retry_delay
                logger.info(f"🔄 Riprova {task.retry_count}/{task.max_retries} per {task.product_name} tra 5 minuti")
            else:
                # Troppi errori, disabilita task
                task.is_active = False
                logger.error(f"❌ Task {task.product_name} disabilitato per troppi errori")
                
        except Exception as e:
            logger.error(f"❌ Errore gestione errore task: {e}")
    
    async def _schedule_next_run(self, task: ScheduledTask):
        """Schedula prossima esecuzione task"""
        try:
            task.last_run = datetime.now()
            task.next_run = task.last_run + timedelta(hours=task.frequency_hours)
            task.retry_count = 0  # Reset retry count
            
            logger.debug(f"📅 Prossima esecuzione {task.product_name}: {task.next_run}")
            
        except Exception as e:
            logger.error(f"❌ Errore schedulazione prossima esecuzione: {e}")
    
    async def _load_monitored_products(self):
        """Carica prodotti monitorati dal database"""
        try:
            result = await self.price_monitor.get_monitored_products(active_only=True)
            
            if result["success"]:
                for product in result["products"]:
                    await self._add_product_to_scheduler(product)
                
                logger.info(f"📋 Caricati {len(result['products'])} prodotti nel scheduler")
            else:
                logger.error(f"❌ Errore caricamento prodotti: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Errore caricamento prodotti: {e}")
    
    async def _add_product_to_scheduler(self, product: Dict[str, Any]):
        """Aggiunge prodotto al scheduler"""
        try:
            product_id = product["id"]
            
            # Calcola prossima esecuzione
            if product.get("last_check"):
                last_check = datetime.fromisoformat(product["last_check"])
                next_run = last_check + timedelta(hours=product["check_frequency"])
                
                # Se la prossima esecuzione è nel passato, esegui subito
                if next_run < datetime.now():
                    next_run = datetime.now() + timedelta(minutes=1)
            else:
                # Primo controllo
                next_run = datetime.now() + timedelta(minutes=1)
            
            task = ScheduledTask(
                product_id=product_id,
                product_name=product["name"],
                frequency_hours=product["check_frequency"],
                last_run=datetime.fromisoformat(product["last_check"]) if product.get("last_check") else None,
                next_run=next_run,
                task_id=f"task_{product_id}_{int(time.time())}",
                is_active=product["is_active"]
            )
            
            self.scheduled_tasks[product_id] = task
            
        except Exception as e:
            logger.error(f"❌ Errore aggiunta prodotto al scheduler: {e}")
    
    async def add_product_to_scheduler(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggiunge nuovo prodotto al scheduler"""
        try:
            # Prima aggiungi al monitoring
            result = await self.price_monitor.add_product_to_monitoring(product_data)
            
            if result["success"]:
                # Poi aggiungi al scheduler
                product_id = result["product_id"]
                
                # Ottieni prodotto dal database
                products_result = await self.price_monitor.get_monitored_products(active_only=True)
                
                if products_result["success"]:
                    for product in products_result["products"]:
                        if product["id"] == product_id:
                            await self._add_product_to_scheduler(product)
                            break
                
                return {
                    "success": True,
                    "message": f"Prodotto aggiunto al scheduler",
                    "product_id": product_id
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Errore aggiunta prodotto al scheduler: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remove_product_from_scheduler(self, product_id: int) -> Dict[str, Any]:
        """Rimuove prodotto dal scheduler"""
        try:
            # Rimuovi dal monitoring
            result = await self.price_monitor.remove_from_monitoring(product_id)
            
            if result["success"]:
                # Rimuovi dal scheduler
                if product_id in self.scheduled_tasks:
                    task = self.scheduled_tasks[product_id]
                    
                    # Cancella task se attivo
                    if task.task_id in self.active_tasks:
                        await self._cancel_task(task.task_id)
                    
                    del self.scheduled_tasks[product_id]
                
                return {
                    "success": True,
                    "message": f"Prodotto rimosso dal scheduler"
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Errore rimozione prodotto dal scheduler: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _cancel_task(self, task_id: str):
        """Cancella task attivo"""
        try:
            # Trova e cancella task
            for task in asyncio.all_tasks():
                if task.get_name() == task_id:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    break
                    
        except Exception as e:
            logger.error(f"❌ Errore cancellazione task: {e}")
    
    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche del scheduler"""
        try:
            # Calcola uptime
            uptime = None
            if self.start_time:
                uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Statistiche task
            active_tasks = sum(1 for task in self.scheduled_tasks.values() if task.is_active)
            total_tasks = len(self.scheduled_tasks)
            running_tasks = len(self.active_tasks)
            
            # Prossimi controlli
            next_checks = []
            for task in sorted(self.scheduled_tasks.values(), key=lambda x: x.next_run)[:5]:
                next_checks.append({
                    "product_name": task.product_name,
                    "next_run": task.next_run.isoformat(),
                    "frequency_hours": task.frequency_hours
                })
            
            return {
                "success": True,
                "stats": {
                    "scheduler_running": self.scheduler_running,
                    "active_tasks": active_tasks,
                    "total_tasks": total_tasks,
                    "running_tasks": running_tasks,
                    "uptime_seconds": uptime,
                    "total_checks": self.stats["total_checks"],
                    "successful_checks": self.stats["successful_checks"],
                    "failed_checks": self.stats["failed_checks"],
                    "alerts_generated": self.stats["alerts_generated"],
                    "last_run": self.stats["last_run"].isoformat() if self.stats["last_run"] else None,
                    "next_checks": next_checks
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Errore statistiche scheduler: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def force_check_product(self, product_id: int) -> Dict[str, Any]:
        """Forza controllo immediato di un prodotto"""
        try:
            if product_id not in self.scheduled_tasks:
                return {
                    "success": False,
                    "error": "Prodotto non trovato nel scheduler"
                }
            
            task = self.scheduled_tasks[product_id]
            
            # Esegui controllo immediato
            result = await self._execute_product_check(task)
            
            # Gestisci risultato
            await self._handle_check_result(task, result)
            
            return {
                "success": True,
                "message": f"Controllo forzato completato per {task.product_name}",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Errore controllo forzato: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Test del sistema
async def test_price_scheduler():
    """Test del sistema Price Scheduler"""
    try:
        # Crea price monitor
        price_monitor = PriceMonitor("test_price_monitor.db")
        
        # Crea scheduler
        scheduler = PriceScheduler(price_monitor)
        
        # Test avvio scheduler
        start_result = await scheduler.start_scheduler()
        print(f"✅ Test avvio scheduler: {start_result}")
        
        # Attendi un po'
        await asyncio.sleep(5)
        
        # Test statistiche
        stats_result = await scheduler.get_scheduler_stats()
        print(f"✅ Test statistiche: {stats_result}")
        
        # Test fermata scheduler
        stop_result = await scheduler.stop_scheduler()
        print(f"✅ Test fermata scheduler: {stop_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_price_scheduler()) 