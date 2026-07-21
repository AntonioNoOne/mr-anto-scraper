#!/usr/bin/env python3

"""
AI Content Analyzer - Mixin gestione browser (popup, cookie, caricamento dinamico).

Metodi spostati VERBATIM da ai_content_analyzer.py (solo raggruppamento).
Il mixin usa solo `self.` e NON importa ai_content_analyzer (evita import circolari).
"""


class _BrowserMixin:
    """Gestione popup/cookie e caricamento dinamico delle pagine Playwright."""

    async def _handle_popups_and_cookies(self, page):

        """Gestisce popup e cookie"""

        try:

            # Cerca pulsanti cookie comuni

            cookie_selectors = [

                'button:has-text("Accept")',

                'button:has-text("Accept All")',

                'button:has-text("Accept Cookies")',

                'button:has-text("OK")',

                'button:has-text("I Accept")',

                'button:has-text("Accept All Cookies")',

                'button:has-text("accetta")',

                'button:has-text("accetta tutti")',

                'button:has-text("accetta cookie")',

                'button:has-text("ok")',

                'button:has-text("Accetta tutto")',

                'button:has-text("Accetta e chiudi")',

                'button:has-text("Consenti tutti")',

                # Consent manager comuni (ID/classi specifiche: hit rate alto)
                '#onetrust-accept-btn-handler',

                '.iubenda-cs-accept-btn',

                'button#didomi-notice-agree-button',

                '[aria-label*="accetta" i]',

                '[class*="cookie"]',

                '[id*="cookie"]'

            ]

            for selector in cookie_selectors:

                try:

                    button = await page.wait_for_selector(selector, timeout=2000)

                    if button and await button.is_visible():

                        await button.click()

                        print(f"✅ Cliccato su: {selector}")

                        break

                except Exception as e:

                    print(f"⚠️ Errore gestione popup: {e}")

                    continue

        except Exception as e:

            print(f"❌ Errore generale gestione popup: {e}")



    async def _handle_dynamic_loading_text_first(self, page, url: str):

        """Gestisce il caricamento dinamico per Text-First AI"""

        try:

            # Caricamento iniziale veloce

            print("⏳ Caricamento iniziale veloce...", end="", flush=True)

            for i in range(3):

                await page.wait_for_timeout(1000)

                print(".", end="", flush=True)

            print(" ✅ Completato!")



            # Scroll e cerca pulsanti "Mostra più"

            max_attempts = 5  # Aumentato da 3 a 5

            for attempt in range(max_attempts):

                print(f"🔄 Tentativo {attempt + 1}/{max_attempts} - Caricamento dinamico...")



                # Scroll

                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                await page.wait_for_timeout(2000)



                # Cerca pulsanti - SELEZIONE ESPANDIBILE

                load_selectors = [

                    # Selettori specifici per Unieuro

                    'button:has-text("Mostra più prodotti")',

                    'button:has-text("Carica altri prodotti")',

                    'button:has-text("Visualizza altri")',

                    'button:has-text("Mostra altri")',

                    'button:has-text("Carica altri")',

                    'button:has-text("Load more")',

                    'button:has-text("Show more")',

                    'button:has-text("Visualizza tutti")',

                    # Selettori generici

                    '[class*="load-more"]',

                    '[class*="show-more"]',

                    '[class*="carica"]',

                    '[class*="mostra"]',

                    # Selettori con icone

                    'button[aria-label*="più"]',

                    'button[aria-label*="more"]',

                    'button[title*="più"]',

                    'button[title*="more"]'

                ]



                button_found = False

                for selector in load_selectors:

                    try:

                        print(f"🔍 Cerca pulsante: {selector}")

                        button = await page.wait_for_selector(selector, timeout=2000)

                        if button and await button.is_visible():

                            print(f"✅ Trovato pulsante: {selector}")

                            # Aspetta che il pulsante sia cliccabile

                            await page.wait_for_timeout(1000)

                            # Prova a cliccare con gestione errori

                            try:

                                # METODO 1: Click normale

                                await button.click(timeout=5000)

                                print(f"✅ CLICK su {selector}")

                                await page.wait_for_timeout(3000)

                                button_found = True

                                break  # ESCE DAL CICLO QUANDO TROVA E CLICCA

                            except Exception as click_error:

                                print(f"❌ Errore click normale su {selector}: {click_error}")

                                # METODO 2: Click con JavaScript

                                try:

                                    print(f"🔄 Provo click JavaScript su {selector}")

                                    await page.evaluate(f"""

                                        () => {{

                                            const button = document.querySelector('{selector}');

                                            if (button) {{

                                                button.click();

                                                return true;

                                            }}

                                            return false;

                                        }}

                                    """)

                                    print(f"✅ CLICK JavaScript su {selector}")

                                    await page.wait_for_timeout(3000)

                                    button_found = True

                                    break

                                except Exception as js_error:

                                    print(f"❌ Errore click JavaScript su {selector}: {js_error}")

                                    # METODO 3: Click con dispatchEvent

                                    try:

                                        print(f"🔄 Provo click dispatchEvent su {selector}")

                                        await page.evaluate(f"""

                                            () => {{

                                                const button = document.querySelector('{selector}');

                                                if (button) {{

                                                    button.dispatchEvent(new MouseEvent('click', {{

                                                        bubbles: true,

                                                        cancelable: true,

                                                        view: window

                                                    }}));

                                                    return true;

                                                }}

                                                return false;

                                            }}

                                        """)

                                        print(f"✅ CLICK dispatchEvent su {selector}")

                                        await page.wait_for_timeout(3000)

                                        button_found = True

                                        break

                                    except Exception as dispatch_error:

                                        print(f"❌ Errore click dispatchEvent su {selector}: {dispatch_error}")

                                        continue

                    except Exception as e:

                        print(f"❌ Pulsante non trovato: {selector} - {e}")

                        continue



                if not button_found:

                    print("❌ Nessun pulsante 'Mostra più' trovato in questo tentativo")

                else:

                    print("✅ Pulsante cliccato con successo!")

                    break  # ESCE DAL CICLO DEI TENTATIVI SE HA CLICCATO



                # Attendi caricamento dopo click

                await page.wait_for_timeout(2000)



        except Exception as e:

            print(f"⚠️ Errore caricamento dinamico: {e}")
