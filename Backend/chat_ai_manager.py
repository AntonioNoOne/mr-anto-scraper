#!/usr/bin/env python3
"""
Chat AI Manager per MR Scraper
Gestisce le conversazioni con ChatGPT, Ollama e Gemini
"""

import os
import json
import requests
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import subprocess
import sys
from dotenv import load_dotenv

class ChatAIManager:
    """Gestore per le conversazioni AI con multiple models"""
    
    def __init__(self):
        # Carica configurazioni da env.local
        self.load_config()
        
    def load_config(self):
        """Carica configurazioni da env.local"""
        try:
            # Prova prima il percorso relativo (quando eseguito da start.py)
            load_dotenv("env.local")
            print("✅ Configurazioni caricate da env.local")
        except Exception as e:
            try:
                # Prova il percorso assoluto (quando eseguito direttamente)
                current_dir = os.path.dirname(os.path.abspath(__file__))
                env_path = os.path.join(current_dir, "env.local")
                load_dotenv(env_path)
                print(f"✅ Configurazioni caricate da {env_path}")
            except Exception as e2:
                print(f"⚠️ Errore caricamento env.local: {e2}, usando variabili d'ambiente di sistema")
        
        # Configurazioni AI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # Configurazione Ollama
        self.ollama_base_url = "http://localhost:11434"
        self.ollama_model = "llama3.2"  # Modello di default per Ollama
        
    async def send_message(self, message: str, model: str = "openai", 
                          conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Invia messaggio all'AI selezionata"""
        
        if conversation_history is None:
            conversation_history = []
            
        try:
            if model == "openai":
                return await self._call_openai(message, conversation_history)
            elif model == "ollama":
                return await self._call_ollama(message, conversation_history)
            elif model == "gemini":
                return await self._call_gemini(message, conversation_history)
            else:
                return {
                    "success": False,
                    "response": "",
                    "model_used": model,
                    "error": f"Modello '{model}' non supportato. Usa: openai, ollama, gemini"
                }
                
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "model_used": model,
                "error": f"Errore nella chiamata a {model}: {str(e)}"
            }
    
    async def _call_openai(self, message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Chiama OpenAI API"""
        if not self.openai_api_key:
            return {
                "success": False,
                "response": "",
                "model_used": "openai",
                "error": "OpenAI API key non configurata"
            }
            
        try:
            # Prepara i messaggi per OpenAI
            messages = [
                {
                    "role": "system",
                    "content": """Sei un assistente AI esperto di web scraping e analisi dati. 
                    Aiuti gli utenti con:
                    - Analisi di dati estratti da siti web
                    - Interpretazione di risultati di scraping
                    - Suggerimenti per ottimizzare le estrazioni
                    - Spiegazioni tecniche sui processi di scraping
                    - Analisi di prodotti e prezzi trovati
                    - Confronti tra venditori alternativi
                    
                    Se l'utente chiede informazioni sui prodotti trovati, puoi accedere ai risultati di Google Search tramite l'endpoint /google-search-results.
                    Usa sempre dati reali quando disponibili per fornire risposte accurate e utili."""
                }
            ]
            
            # Aggiungi la cronologia della conversazione
            for msg in conversation_history[-10:]:  # Ultimi 10 messaggi per evitare token limit
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Aggiungi il messaggio corrente
            messages.append({
                "role": "user",
                "content": message
            })
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.openai_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                
                return {
                    "success": True,
                    "response": ai_response,
                    "model_used": "openai",
                    "error": None
                }
            else:
                error_detail = f"Errore API OpenAI: {response.status_code}"
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        error_detail += f" - {error_json['error'].get('message', 'Errore sconosciuto')}"
                except:
                    error_detail += f" - {response.text[:200]}"
                
                return {
                    "success": False,
                    "response": "",
                    "model_used": "openai",
                    "error": error_detail
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "model_used": "openai",
                "error": "Timeout nella chiamata a OpenAI (60s). Verifica la connessione internet."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "model_used": "openai",
                "error": "Errore di connessione a OpenAI. Verifica la connessione internet."
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "model_used": "openai",
                "error": f"Errore nella chiamata OpenAI: {str(e)}"
            }
    
    async def _call_ollama(self, message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Chiama Ollama API locale"""
        try:
            # Prepara il prompt per Ollama
            system_prompt = """Sei un assistente AI esperto di web scraping e analisi dati. 
            Aiuti gli utenti con analisi di dati estratti da siti web, interpretazione di risultati 
            di scraping, suggerimenti per ottimizzare le estrazioni e spiegazioni tecniche sui processi 
            di scraping.
            
            IMPORTANTE: Se ricevi dati estratti nel messaggio, analizza attentamente quei dati 
            e rispondi basandoti su di essi. Fornisci analisi dettagliate e suggerimenti utili.
            
            Rispondi sempre in italiano in modo chiaro e professionale."""
            
            # Costruisci il prompt completo
            full_prompt = f"{system_prompt}\n\n"
            
            # Aggiungi la cronologia (ultimi 5 messaggi per Ollama)
            for msg in conversation_history[-5:]:
                role = "Utente" if msg["role"] == "user" else "Assistente"
                full_prompt += f"{role}: {msg['content']}\n"
            
            full_prompt += f"Utente: {message}\nAssistente:"
            
            payload = {
                "model": self.ollama_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=60  # Ollama può essere più lento
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("response", "").strip()
                
                return {
                    "success": True,
                    "response": ai_response,
                    "model_used": "ollama",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "response": "",
                    "model_used": "ollama",
                    "error": f"Errore API Ollama: {response.status_code} - {response.text}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "model_used": "ollama",
                "error": "Ollama non è in esecuzione. Avvia Ollama con: ollama serve"
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "model_used": "ollama",
                "error": f"Errore nella chiamata Ollama: {str(e)}"
            }
    
    async def _call_gemini(self, message: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Chiama Google Gemini API"""
        if not self.gemini_api_key:
            return {
                "success": False,
                "response": "",
                "model_used": "gemini",
                "error": "Gemini API key non configurata"
            }
            
        try:
            # Prepara il prompt per Gemini
            system_prompt = """Sei un assistente AI esperto di web scraping e analisi dati. 
            Aiuti gli utenti con analisi di dati estratti da siti web, interpretazione di risultati 
            di scraping, suggerimenti per ottimizzare le estrazioni e spiegazioni tecniche sui processi 
            di scraping.
            
            IMPORTANTE: Se ricevi dati estratti nel messaggio, analizza attentamente quei dati 
            e rispondi basandoti su di essi. Fornisci analisi dettagliate e suggerimenti utili.
            
            Rispondi sempre in italiano in modo chiaro e professionale."""
            
            # Costruisci il prompt completo
            full_prompt = f"{system_prompt}\n\n"
            
            # Aggiungi la cronologia (ultimi 5 messaggi per Gemini)
            for msg in conversation_history[-5:]:
                role = "Utente" if msg["role"] == "user" else "Assistente"
                full_prompt += f"{role}: {msg['content']}\n"
            
            full_prompt += f"Utente: {message}\nAssistente:"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1000
                }
            }
            
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
                
                return {
                    "success": True,
                    "response": ai_response,
                    "model_used": "gemini",
                    "error": None
                }
            else:
                error_detail = f"Errore API Gemini: {response.status_code}"
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        error_detail += f" - {error_json['error'].get('message', 'Errore sconosciuto')}"
                except:
                    error_detail += f" - {response.text[:200]}"
                
                return {
                    "success": False,
                    "response": "",
                    "model_used": "gemini",
                    "error": error_detail
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "model_used": "gemini",
                "error": "Timeout nella chiamata a Gemini (60s). Verifica la connessione internet."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "model_used": "gemini",
                "error": "Errore di connessione a Gemini. Verifica la connessione internet."
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "model_used": "gemini",
                "error": f"Errore nella chiamata Gemini: {str(e)}"
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """Restituisce i modelli disponibili e il loro stato"""
        models = {
            "openai": {
                "available": bool(self.openai_api_key),
                "model": self.openai_model,
                "status": "Configurato" if self.openai_api_key else "Non configurato"
            },
            "gemini": {
                "available": bool(self.gemini_api_key),
                "model": self.gemini_model,
                "status": "Configurato" if self.gemini_api_key else "Non configurato"
            },
            "ollama": {
                "available": False,
                "model": self.ollama_model,
                "status": "Non disponibile"
            }
        }
        
        # Verifica se Ollama è in esecuzione
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models["ollama"]["available"] = True
                models["ollama"]["status"] = "In esecuzione"
        except:
            pass
            
        return models 