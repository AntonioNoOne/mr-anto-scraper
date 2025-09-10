#!/usr/bin/env python3

"""
Backup Manager - Sistema di backup automatico per fast_ai_extractor.py
====================================================================

Ogni volta che fast_ai_extractor.py viene modificato, crea automaticamente
un backup con timestamp. Mantiene gli ultimi 10 backup per evitare
di riempire il disco.

USO:
- Backup automatico: Si attiva quando modifichi fast_ai_extractor.py
- Backup manuale: python backup_manager.py --manual
- Ripristino: python backup_manager.py --restore <timestamp>
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path
import argparse

class BackupManager:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.source_file = Path("fast_ai_extractor.py")
        self.max_backups = 10
        
        # Crea directory backup se non esiste
        self.backup_dir.mkdir(exist_ok=True)
        
        # File di controllo per l'ultima modifica
        self.last_modified_file = self.backup_dir / "last_modified.txt"
        
    def get_file_hash(self, file_path):
        """Calcola hash semplice del file per rilevare modifiche"""
        try:
            stat = file_path.stat()
            return f"{stat.st_mtime}_{stat.st_size}"
        except:
            return None
    
    def needs_backup(self):
        """Controlla se serve fare un backup"""
        if not self.source_file.exists():
            return False
            
        current_hash = self.get_file_hash(self.source_file)
        if not current_hash:
            return False
            
        # Leggi hash precedente
        if self.last_modified_file.exists():
            try:
                with open(self.last_modified_file, 'r') as f:
                    last_hash = f.read().strip()
                return current_hash != last_hash
            except:
                return True
        else:
            return True
    
    def create_backup(self, reason="auto"):
        """Crea un backup del file"""
        if not self.source_file.exists():
            print(f"❌ File sorgente {self.source_file} non trovato")
            return False
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"fast_ai_extractor_{timestamp}_{reason}.py"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Copia il file
            shutil.copy2(self.source_file, backup_path)
            
            # Salva hash corrente
            current_hash = self.get_file_hash(self.source_file)
            with open(self.last_modified_file, 'w') as f:
                f.write(current_hash)
            
            print(f"✅ Backup creato: {backup_name}")
            
            # Pulisci backup vecchi
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ Errore creazione backup: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Rimuove backup vecchi mantenendo solo gli ultimi max_backups"""
        try:
            # Lista tutti i backup
            backups = list(self.backup_dir.glob("fast_ai_extractor_*.py"))
            
            if len(backups) <= self.max_backups:
                return
                
            # Ordina per data di creazione (più vecchi prima)
            backups.sort(key=lambda x: x.stat().st_ctime)
            
            # Rimuovi i più vecchi
            to_remove = backups[:-self.max_backups]
            
            for backup in to_remove:
                try:
                    backup.unlink()
                    print(f"🗑️ Rimosso backup vecchio: {backup.name}")
                except Exception as e:
                    print(f"⚠️ Errore rimozione {backup.name}: {e}")
                    
        except Exception as e:
            print(f"⚠️ Errore pulizia backup: {e}")
    
    def list_backups(self):
        """Lista tutti i backup disponibili"""
        try:
            backups = list(self.backup_dir.glob("fast_ai_extractor_*.py"))
            
            if not backups:
                print("📁 Nessun backup trovato")
                return
                
            print(f"📁 Backup disponibili ({len(backups)}):")
            print("-" * 60)
            
            for backup in sorted(backups, key=lambda x: x.stat().st_ctime, reverse=True):
                stat = backup.stat()
                size = stat.st_size / 1024  # KB
                created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"📄 {backup.name}")
                print(f"   📅 Creato: {created}")
                print(f"   📏 Dimensione: {size:.1f} KB")
                print()
                
        except Exception as e:
            print(f"❌ Errore lista backup: {e}")
    
    def restore_backup(self, timestamp):
        """Ripristina un backup specifico"""
        try:
            # Trova il backup
            backup_pattern = f"fast_ai_extractor_{timestamp}_*.py"
            backups = list(self.backup_dir.glob(backup_pattern))
            
            if not backups:
                print(f"❌ Nessun backup trovato con timestamp {timestamp}")
                return False
                
            backup_path = backups[0]
            
            # Crea backup del file corrente prima del ripristino
            current_backup = f"fast_ai_extractor_{datetime.now().strftime('%Y%m%d_%H%M%S')}_before_restore.py"
            shutil.copy2(self.source_file, self.backup_dir / current_backup)
            
            # Ripristina il backup
            shutil.copy2(backup_path, self.source_file)
            
            print(f"✅ Ripristinato backup: {backup_path.name}")
            print(f"📁 Backup corrente salvato come: {current_backup}")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore ripristino: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Backup Manager per fast_ai_extractor.py")
    parser.add_argument("--manual", action="store_true", help="Crea backup manuale")
    parser.add_argument("--list", action="store_true", help="Lista backup disponibili")
    parser.add_argument("--restore", type=str, help="Ripristina backup con timestamp (es: 20241201_143022)")
    parser.add_argument("--auto", action="store_true", help="Controlla e crea backup automatico se necessario")
    parser.add_argument("--watch", action="store_true", help="Modalità watch continua per rilevare modifiche")
    
    args = parser.parse_args()
    
    backup_mgr = BackupManager()
    
    if args.manual:
        print("🔄 Creazione backup manuale...")
        backup_mgr.create_backup("manual")
        
    elif args.list:
        backup_mgr.list_backups()
        
    elif args.restore:
        print(f"🔄 Ripristino backup {args.restore}...")
        backup_mgr.restore_backup(args.restore)
        
    elif args.watch:
        print("👀 Modalità WATCH attiva - Monitoro modifiche in tempo reale...")
        print("💡 Premi Ctrl+C per fermare")
        try:
            while True:
                if backup_mgr.needs_backup():
                    print("🔄 Rilevata modifica, creo backup automatico...")
                    backup_mgr.create_backup("auto")
                time.sleep(2)  # Controlla ogni 2 secondi
        except KeyboardInterrupt:
            print("\n✅ Modalità watch fermata")
        
    elif args.auto:
        if backup_mgr.needs_backup():
            print("🔄 Rilevata modifica, creo backup automatico...")
            backup_mgr.create_backup("auto")
        else:
            print("✅ Nessuna modifica rilevata, backup non necessario")
            
    else:
        # Modalità automatica (default)
        if backup_mgr.needs_backup():
            print("🔄 Rilevata modifica, creo backup automatico...")
            backup_mgr.create_backup("auto")
        else:
            print("✅ Nessuna modifica rilevata")

if __name__ == "__main__":
    main()
