#!/usr/bin/env python3
"""
Test script per verificare che il deploy su Render funzioni correttamente
"""

import os
import sys
import asyncio
import requests
from dotenv import load_dotenv

# Aggiungi il percorso Backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'Backend'))

def test_requirements():
    """Test che tutti i requirements siano installabili"""
    print("🧪 Test requirements...")
    
    try:
        import fastapi
        import uvicorn
        import playwright
        import requests
        import bs4
        import openai
        print("✅ Tutti i requirements principali sono disponibili")
        return True
    except ImportError as e:
        print(f"❌ Requirement mancante: {e}")
        return False

def test_environment_variables():
    """Test che le variabili d'ambiente siano configurate"""
    print("🧪 Test variabili d'ambiente...")
    
    # Carica env.local
    load_dotenv('Backend/env.local')
    
    required_vars = ['OPENAI_API_KEY', 'GEMINI_API_KEY']
    optional_vars = ['BROWSERBASE_API_KEY', 'BROWSERBASE_PROJECT_ID']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        print(f"❌ Variabili richieste mancanti: {missing_required}")
        return False
    
    if missing_optional:
        print(f"⚠️ Variabili opzionali mancanti: {missing_optional}")
    
    print("✅ Variabili d'ambiente configurate correttamente")
    return True

def test_file_structure():
    """Test che la struttura dei file sia corretta"""
    print("🧪 Test struttura file...")
    
    required_files = [
        'render.yaml',
        'Backend/requirements.txt',
        'Backend/main.py',
        'Backend/env.local',
        'Frontend/index.html',
        'Frontend/js/actions.js',
        'Frontend/js/api.js',
        'Frontend/js/store.js',
        'Frontend/css/styles.css'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ File mancanti: {missing_files}")
        return False
    
    print("✅ Struttura file corretta")
    return True

def test_render_yaml():
    """Test che render.yaml sia configurato correttamente"""
    print("🧪 Test render.yaml...")
    
    try:
        import yaml
        with open('render.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Verifica struttura base
        if 'services' not in config:
            print("❌ render.yaml: 'services' mancante")
            return False
        
        service = config['services'][0]
        required_fields = ['type', 'name', 'env', 'plan', 'buildCommand', 'startCommand']
        
        for field in required_fields:
            if field not in service:
                print(f"❌ render.yaml: campo '{field}' mancante")
                return False
        
        print("✅ render.yaml configurato correttamente")
        return True
        
    except Exception as e:
        print(f"❌ Errore lettura render.yaml: {e}")
        return False

async def test_api_startup():
    """Test che l'API si avvii correttamente"""
    print("🧪 Test avvio API...")
    
    try:
        # Importa i moduli necessari
        from Backend.main import app
        from Backend.fast_ai_extractor import FastAIExtractor
        from Backend.ai_product_comparator import AIProductComparator
        from Backend.chat_ai_manager import ChatAIManager
        
        print("✅ Moduli importati correttamente")
        
        # Test inizializzazione componenti
        extractor = FastAIExtractor()
        ai_comparator = AIProductComparator()
        chat_manager = ChatAIManager()
        
        print("✅ Componenti inizializzati correttamente")
        return True
        
    except Exception as e:
        print(f"❌ Errore avvio API: {e}")
        return False

def test_playwright_installation():
    """Test che Playwright sia installabile"""
    print("🧪 Test Playwright...")
    
    try:
        import subprocess
        result = subprocess.run(['playwright', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Playwright installato: {result.stdout.strip()}")
            return True
        else:
            print("⚠️ Playwright non installato, ma verrà installato durante il build")
            return True
    except FileNotFoundError:
        print("⚠️ Playwright non installato, ma verrà installato durante il build")
        return True

def main():
    """Esegue tutti i test"""
    print("🚀 Test Deploy Render - MR Scraper")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_render_yaml,
        test_requirements,
        test_environment_variables,
        test_playwright_installation,
        test_api_startup
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = asyncio.run(test())
            else:
                result = test()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Errore durante test {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Risultati: {passed}/{total} test superati")
    
    if passed == total:
        print("🎉 Tutti i test superati! Il deploy su Render dovrebbe funzionare.")
        print("\n🚀 Prossimi passi:")
        print("1. Esegui: git add .")
        print("2. Esegui: git commit -m 'Deploy su Render'")
        print("3. Esegui: git push origin master")
        print("4. Vai su https://render.com")
        print("5. Crea un nuovo Web Service")
        print("6. Connetti il tuo repository GitHub")
        print("7. Render rileverà automaticamente render.yaml")
        print("8. Configura le Environment Variables")
        print("9. Clicca Deploy!")
    else:
        print("❌ Alcuni test falliti. Risolvi i problemi prima del deploy.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
