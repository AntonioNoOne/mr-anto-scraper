#!/usr/bin/env python3
"""
Aggiornatore Automatico Proxy da Digitale.co
Scarica e aggiorna la lista di proxy funzionanti
"""

import asyncio
import aiohttp
import re
import json
import random
from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import async_playwright

class ProxyUpdater:
    def __init__(self):
        self.digitale_url = "https://www.digitale.co/server-proxy"
        self.proxy_file = "working_proxies.json"
        
    async def scrape_digitale_proxies(self) -> List[Dict]:
        """Scarica i proxy da digitale.co o usa quelli manuali"""
        print("🔄 Caricamento proxy da lista manuale...")
        
        # Proxy manuali da digitale.co (aggiornati periodicamente)
        manual_proxies = [
            {'ip': '192.252.220.89', 'port': '4145', 'type': 'SOCKS5', 'country': 'Stati Uniti', 'reliability': 90},
            {'ip': '198.8.94.170', 'port': '4145', 'type': 'SOCKS5', 'country': 'Stati Uniti', 'reliability': 92},
            {'ip': '139.162.78.109', 'port': '8080', 'type': 'HTTPS', 'country': 'Giappone', 'reliability': 56},
            {'ip': '103.23.196.21', 'port': '8080', 'type': 'HTTPS', 'country': 'Indonesia', 'reliability': 6},
            {'ip': '98.170.57.231', 'port': '4145', 'type': 'SOCKS5', 'country': 'Stati Uniti', 'reliability': 88},
            {'ip': '196.202.91.43', 'port': '8080', 'type': 'HTTPS', 'country': 'Egitto', 'reliability': 16},
            {'ip': '8.137.38.48', 'port': '4000', 'type': 'SOCKS5', 'country': 'Regno Unito', 'reliability': 53},
            {'ip': '103.172.42.81', 'port': '8080', 'type': 'HTTPS', 'country': 'Indonesia', 'reliability': 7},
            {'ip': '184.181.217.206', 'port': '4145', 'type': 'SOCKS5', 'country': 'Stati Uniti', 'reliability': 91},
            {'ip': '103.120.76.145', 'port': '8080', 'type': 'HTTPS', 'country': 'Indonesia', 'reliability': 6},
            {'ip': '98.188.47.132', 'port': '4145', 'type': 'SOCKS5', 'country': 'Stati Uniti', 'reliability': 92},
            {'ip': '65.108.159.129', 'port': '8081', 'type': 'HTTPS', 'country': 'Finlandia', 'reliability': 12},
            {'ip': '192.252.216.81', 'port': '4145', 'type': 'SOCKS5', 'country': 'Stati Uniti', 'reliability': 93},
            {'ip': '47.92.152.43', 'port': '8118', 'type': 'SOCKS5', 'country': 'Regno Unito', 'reliability': 32},
            {'ip': '142.54.229.249', 'port': '4145', 'type': 'SOCKS5', 'country': 'Stati Uniti', 'reliability': 93},
        ]
        
        proxies = []
        for proxy in manual_proxies:
            if proxy['reliability'] > 50:  # Solo proxy con affidabilità > 50%
                proxy_url = self._format_proxy_url(proxy['ip'], proxy['port'], proxy['type'])
                proxies.append({
                    'ip': proxy['ip'],
                    'port': proxy['port'],
                    'type': proxy['type'],
                    'country': proxy['country'],
                    'reliability': proxy['reliability'],
                    'url': proxy_url,
                    'last_checked': datetime.now().isoformat()
                })
        
        print(f"📊 Proxy caricati: {len(proxies)}")
        return proxies
    
    def _format_proxy_url(self, ip: str, port: str, proxy_type: str) -> str:
        """Formatta l'URL del proxy"""
        if proxy_type == 'SOCKS5':
            return f"socks5://{ip}:{port}"
        elif proxy_type == 'HTTPS':
            return f"http://{ip}:{port}"
        else:
            return f"http://{ip}:{port}"
    
    async def test_proxy(self, proxy_url: str) -> bool:
        """Testa se un proxy funziona"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'http://httpbin.org/ip',
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
        except Exception:
            pass
        return False
    
    async def test_proxy_list(self, proxies: List[Dict]) -> List[Dict]:
        """Testa tutti i proxy e restituisce quelli funzionanti"""
        print("🧪 Test proxy...")
        working_proxies = []
        
        for proxy in proxies:
            print(f"🔍 Test: {proxy['url']} ({proxy['country']} - {proxy['reliability']}%)")
            if await self.test_proxy(proxy['url']):
                working_proxies.append(proxy)
                print(f"✅ Funziona: {proxy['url']}")
            else:
                print(f"❌ Non funziona: {proxy['url']}")
        
        print(f"📊 Proxy funzionanti: {len(working_proxies)}/{len(proxies)}")
        return working_proxies
    
    def save_proxies(self, proxies: List[Dict]):
        """Salva i proxy funzionanti su file"""
        try:
            with open(self.proxy_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_update': datetime.now().isoformat(),
                    'total_proxies': len(proxies),
                    'proxies': proxies
                }, f, indent=2, ensure_ascii=False)
            print(f"💾 Proxy salvati in {self.proxy_file}")
        except Exception as e:
            print(f"❌ Errore salvataggio: {e}")
    
    def load_proxies(self) -> List[Dict]:
        """Carica i proxy dal file"""
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('proxies', [])
        except Exception:
            return []
    
    async def update_proxy_list(self, force_update: bool = False):
        """Aggiorna la lista dei proxy"""
        print("🚀 Aggiornamento lista proxy...")
        
        # Controlla se dobbiamo aggiornare
        if not force_update:
            existing_proxies = self.load_proxies()
            if existing_proxies:
                print(f"📋 Proxy esistenti: {len(existing_proxies)}")
                return existing_proxies
        
        # Scarica nuovi proxy
        new_proxies = await self.scrape_digitale_proxies()
        if not new_proxies:
            print("⚠️ Nessun proxy scaricato, uso quelli esistenti")
            return self.load_proxies()
        
        # Testa i proxy
        working_proxies = await self.test_proxy_list(new_proxies)
        
        # Salva i proxy funzionanti
        if working_proxies:
            self.save_proxies(working_proxies)
        
        return working_proxies

# Istanza globale
proxy_updater = ProxyUpdater()

async def main():
    """Funzione principale"""
    print("🔄 Aggiornatore Proxy Digitale.co")
    
    # Aggiorna la lista
    proxies = await proxy_updater.update_proxy_list(force_update=True)
    
    if proxies:
        print(f"✅ Aggiornamento completato: {len(proxies)} proxy funzionanti")
        
        # Mostra i migliori proxy
        print("\n🏆 Migliori proxy:")
        sorted_proxies = sorted(proxies, key=lambda x: x['reliability'], reverse=True)
        for i, proxy in enumerate(sorted_proxies[:5]):
            print(f"{i+1}. {proxy['url']} - {proxy['country']} ({proxy['reliability']}%)")
    else:
        print("❌ Nessun proxy funzionante trovato")

if __name__ == "__main__":
    asyncio.run(main()) 