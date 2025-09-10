#!/usr/bin/env python3

"""
Clean Database - Pulisce completamente il database storico
================================================================

Rimuove tutti i prodotti, sessioni e statistiche per fare un test pulito.
ATTENZIONE: Questo script ELIMINA TUTTI I DATI!

USO:
- python clean_database.py --confirm
"""

import sqlite3
import os
import argparse
from pathlib import Path

class DatabaseCleaner:
    def __init__(self):
        self.db_path = "data/database/historical_products.db"
        
    def clean_database(self):
        """Pulisce completamente il database"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ Database non trovato: {self.db_path}")
                return False
                
            print(f"🧹 Pulizia database: {self.db_path}")
            
            # Connessione al database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Conta record prima della pulizia
            cursor.execute("SELECT COUNT(*) FROM products")
            products_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extraction_sessions")
            sessions_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM site_statistics")
            stats_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM dashboard_stats")
            dashboard_count = cursor.fetchone()[0]
            
            print(f"📊 Record trovati:")
            print(f"  - Prodotti: {products_count}")
            print(f"  - Sessioni: {sessions_count}")
            print(f"  - Statistiche sito: {stats_count}")
            print(f"  - Statistiche dashboard: {dashboard_count}")
            
            # Conferma utente
            confirm = input(f"\n⚠️ ATTENZIONE: Stai per ELIMINARE TUTTI i dati! Digita 'CONFERMO' per continuare: ")
            
            if confirm != "CONFERMO":
                print("❌ Operazione annullata dall'utente")
                conn.close()
                return False
            
            print("🔄 Eliminazione in corso...")
            
            # Elimina tutti i dati
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM extraction_sessions")
            cursor.execute("DELETE FROM site_statistics")
            cursor.execute("DELETE FROM dashboard_stats")
            
            # Reset auto-increment
            cursor.execute("DELETE FROM sqlite_sequence")
            
            # Commit modifiche
            conn.commit()
            
            print("✅ Database pulito con successo!")
            
            # Verifica pulizia
            cursor.execute("SELECT COUNT(*) FROM products")
            new_products_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM extraction_sessions")
            new_sessions_count = cursor.fetchone()[0]
            
            print(f"📊 Record dopo pulizia:")
            print(f"  - Prodotti: {new_products_count}")
            print(f"  - Sessioni: {new_sessions_count}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Errore pulizia database: {e}")
            return False
    
    def reset_database(self):
        """Rimuove completamente il database e lo ricrea"""
        try:
            print("🔄 Reset completo database...")
            
            # Rimuovi database esistente
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print(f"🗑️ Database rimosso: {self.db_path}")
            
            # Ricrea database vuoto
            from historical_products_db import HistoricalProductsDB
            db = HistoricalProductsDB()
            db.initialize_database()
            
            print("✅ Database ricreato e inizializzato!")
            return True
            
        except Exception as e:
            print(f"❌ Errore reset database: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Pulisce il database storico")
    parser.add_argument("--confirm", action="store_true", help="Conferma automatica (ATTENZIONE!)")
    parser.add_argument("--reset", action="store_true", help="Rimuove e ricrea completamente il database")
    
    args = parser.parse_args()
    
    cleaner = DatabaseCleaner()
    
    if args.reset:
        print("🔄 Reset completo database...")
        cleaner.reset_database()
    else:
        if args.confirm:
            print("⚠️ Modalità conferma automatica attivata")
            # Simula conferma
            import builtins
            original_input = builtins.input
            builtins.input = lambda x: "CONFERMO"
            
            try:
                cleaner.clean_database()
            finally:
                builtins.input = original_input
        else:
            cleaner.clean_database()

if __name__ == "__main__":
    main()
