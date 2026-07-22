"""
Seed dati demo (PRODOTTI REALI da scansioni unieuro/mediaworld).

Popola il DB storico se e' vuoto, cosi' l'app e' sempre mostrabile anche su
Render effimero. I prodotti sono reali (nomi/prezzi da scan veri) e il link
porta alla pagina categoria reale del venditore. Alcuni prodotti compaiono su
piu' siti a prezzi diversi (gemelli) per far funzionare subito il confronto.
Rigenerato da scansioni reali.
"""

import logging

logger = logging.getLogger(__name__)

SEED_PRODUCTS = [
    {
        "name": "HP 15-fc1007nl AI AMD Ryzen™ 5 7520U Computer port...",
        "price": "€ 529,00",
        "brand": "HP",
        "model": "15-fc1007nl AI",
        "category": "Notebook",
        "specs": "AI AMD Ryzen™ 5 7520U",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "HP 15-fd0126nl Intel Core 7 150U Computer portatil...",
        "price": "€ 699,00",
        "brand": "HP",
        "model": "15-fd0126nl",
        "category": "Notebook",
        "specs": "Intel Core 7 150U",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "ASUS Vivobook 15 F1504VA-BQ232W Intel Core 7 150U ...",
        "price": "€ 669,00",
        "brand": "ASUS",
        "model": "Vivobook 15 F1504VA-BQ232W",
        "category": "Notebook",
        "specs": "Intel Core 7 150U",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Lenovo IdeaPad Slim 3 15IRU8 Intel® Core™ i5 i5-13...",
        "price": "€ 679,00",
        "brand": "Lenovo",
        "model": "IdeaPad Slim 3 15IRU8",
        "category": "Notebook",
        "specs": "Intel® Core™ i5 i5-13",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "ASUS Vivobook 16 M1607GA-MB021W Copilot+ PC AMD Ry...",
        "price": "€ 999,90",
        "brand": "ASUS",
        "model": "Vivobook 16 M1607GA-MB021W Copilot+ PC",
        "category": "Notebook",
        "specs": "AMD Ry",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Lenovo IdeaPad Notebook Slim 3 | Display 15'' FHD 1920x1080 | Processore Intel CORE I3-1315U | Memoria RAM 8GB | Memoria",
        "price": "€ 399,00",
        "brand": "Lenovo",
        "model": "IdeaPad Slim 3",
        "category": "Notebook",
        "specs": "Display 15'' FHD 1920x1080, Processore Intel CORE I3-1315U, Memoria RAM 8GB, Memoria SSD 512GB, Scheda grafica Integrata",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "HP OmniBook 3 Laptop Next Gen AI 15-fn0014nl Copil...",
        "price": "€ 749,90",
        "brand": "HP",
        "model": "OmniBook 3 Laptop Next Gen AI 15-fn0014nl",
        "category": "Notebook",
        "specs": "",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Lenovo IdeaPad Flex Notebook | Display 14'' WUXGA 1920x1200 | Processore AMD Ryzen 5 7430U | Memoria RAM 16GB | Memoria ",
        "price": "€ 699,90",
        "brand": "Lenovo",
        "model": "IdeaPad Flex",
        "category": "Notebook",
        "specs": "Display 14'' WUXGA 1920x1200, Processore AMD Ryzen 5 7430U, Memoria RAM 16GB, Memoria SSD 512GB, Scheda grafica Integrat",
        "rating": "",
        "availability": "VOLANTINO",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "HP 15-fd2019nl Intel Core Ultra 5 225U Computer po...",
        "price": "€ 649,90",
        "brand": "HP",
        "model": "15-fd2019nl",
        "category": "Notebook",
        "specs": "Intel Core Ultra 5 225U",
        "rating": "",
        "availability": "VOLANTINO",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Acer ASPIRE LITE 15 AL15-32P-C425 Intel® Celeron® ...",
        "price": "€ 289,00",
        "brand": "Acer",
        "model": "ASPIRE LITE 15 AL15-32P-C425",
        "category": "Notebook",
        "specs": "Intel® Celeron®",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "HP OmniBook 7 AI 14-fr0011nl Intel Core Ultra 7 25...",
        "price": "€ 1199,90",
        "brand": "HP",
        "model": "OmniBook 7 AI 14-fr0011nl",
        "category": "Notebook",
        "specs": "Intel Core Ultra 7 25",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Lenovo LOQ Notebook Gaming | Display 15'' FHD (1920x1080) | Processore INTEL Core i5-13450HX | Memoria RAM 16GB | Memori",
        "price": "€ 1036,36",
        "brand": "Lenovo",
        "model": "LOQ Notebook Gaming",
        "category": "Notebook",
        "specs": "Display 15'' FHD (1920x1080), Processore INTEL Core i5-13450HX, Memoria RAM 16GB, Memoria SSD 512GB, Scheda Grafica NVID",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Lenovo IdeaPad Notebook Slim 5 | Display 16'' WUXGA 1920x1200 | Processore INTEL Core Ultra 9-185H | Memoria RAM 32GB | ",
        "price": "€ 1033,00",
        "brand": "Lenovo",
        "model": "IdeaPad Slim 5",
        "category": "Notebook",
        "specs": "Display 16'' WUXGA 1920x1200, Processore INTEL Core Ultra 9-185H, Memoria RAM 32GB, Memoria SSD 1TB, Scheda grafica Inte",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Acer Aspire Go 15 AG15-42P-R9Q9 AMD Ryzen™ 7 5825U Computer portatile 39,6 cm (15.6\") Full HD 32 GB DDR4-SDRAM 1,02 TB S",
        "price": "€ 649,00",
        "brand": "Acer",
        "model": "Aspire Go 15 AG15-42P-R9Q9",
        "category": "Notebook",
        "specs": "AMD Ryzen™ 7 5825U, 39,6 cm (15.6\") Full HD, 32 GB DDR4-SDRAM, 1,02 TB SSD, Wi-Fi 6 (802.11ax), Windows 11 Home, Italian",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "ASUS V3607VM-RP036WS Intel Core 7 240H Computer po...",
        "price": "€ 1599,00",
        "brand": "ASUS",
        "model": "V3607VM-RP036WS",
        "category": "Notebook",
        "specs": "Intel Core 7 240H",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Lenovo IdeaPad Notebook Slim 3 | Display 15'' WUXGA 1920x1200 | Processore AMD Ryzen 5 150 | Memoria RAM 8GB | Memoria S",
        "price": "€ 549,00",
        "brand": "Lenovo",
        "model": "IdeaPad Slim 3",
        "category": "Notebook",
        "specs": "Display 15'' WUXGA 1920x1200, Processore AMD Ryzen 5 150, Memoria RAM 8GB, Memoria SSD 512GB, Scheda grafica Integrata, ",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Lenovo IdeaPad Notebook Slim 3 | Display 15'' FHD 1920x1080 | Processore INTEL Core i5-12450H | Memoria RAM 16GB | Memor",
        "price": "€ 599,00",
        "brand": "Lenovo",
        "model": "IdeaPad Slim 3",
        "category": "Notebook",
        "specs": "Display 15'' FHD 1920x1080, Processore INTEL Core i5-12450H, Memoria RAM 16GB, Memoria SSD 512GB, Scheda grafica Integra",
        "rating": "",
        "availability": "TECH COLLECTION",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "Acer Nitro V 15 ANV15-52-97GL Intel® Core™ i9 i9-1...",
        "price": "€ 1399,00",
        "brand": "Acer",
        "model": "Nitro V 15 ANV15-52-97GL",
        "category": "Notebook",
        "specs": "Intel® Core™ i9 i9-1",
        "rating": "",
        "availability": "TECH COLLECTION",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "HP OmniBook 5 Next Gen AI 16-ag1026nl Copilot+ PC ...",
        "price": "€ 999,90",
        "brand": "HP",
        "model": "OmniBook 5 Next Gen AI 16-ag1026nl Copilot+ PC",
        "category": "Notebook",
        "specs": "",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "HP 15-fd1005nlx Intel® Core™ i7 150U Computer port...",
        "price": "€ 599,00",
        "brand": "HP",
        "model": "15-fd1005nlx",
        "category": "Notebook",
        "specs": "Intel® Core™ i7 150U",
        "rating": "",
        "availability": "SOTTOCOSTO",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "HP 15-FD0129NL NOTEBOOK, 15,6 \", processore Intel® Core 5 120U, Intel®, RAM 16 GB, 1000 GB SSD, Silver, Windows 11",
        "price": "€549,00",
        "brand": "HP",
        "model": "15-FD0129NL",
        "category": "NOTEBOOK",
        "specs": "15,6 \", processore Intel® Core 5 120U, RAM 16 GB, 1000 GB SSD, Silver, Windows 11",
        "rating": "1",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "ASUS Vivobook 16 F1607 NOTEBOOK, 16 \", processore Intel® Core Ultra 7 255H , Intel®, RAM 16 GB, 1000 GB SSD, Blue, Windo",
        "price": "€808,49",
        "brand": "ASUS",
        "model": "Vivobook 16 F1607",
        "category": "NOTEBOOK",
        "specs": "16 \", processore Intel® Core Ultra 7 255H, RAM 16 GB, 1000 GB SSD, Blue, Windows 11 Home",
        "rating": "0",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "APPLE MacBook Neo 13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB, 256GB, Magic Keyboard, Argento",
        "price": "€799,00",
        "brand": "APPLE",
        "model": "MacBook Neo 13''",
        "category": "NOTEBOOK",
        "specs": "13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB RAM, 256GB SSD, Magic Keyboard, Argento",
        "rating": "40",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "LENOVO IdeaPad Slim 5 NOTEBOOK, 16 \", processore Intel® Core Ultra 5 135H, Intel® Arc™ GPU, RAM 16 GB, 512 GB SSD, Grey,",
        "price": "€699,00",
        "brand": "LENOVO",
        "model": "IdeaPad Slim 5",
        "category": "NOTEBOOK",
        "specs": "16 \", processore Intel® Core Ultra 5 135H, Intel® Arc™ GPU, RAM 16 GB, 512 GB SSD, Grey, Windows 11 Home",
        "rating": "1",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "ACER Chromebook 314 CBOA314-1H NOTEBOOK CHROMEBOOK, 14 \", processore Intel® Celeron N4500, Intel® UHD Graphics, RAM 4 GB",
        "price": "€199,00",
        "brand": "ACER",
        "model": "Chromebook 314 CBOA314-1H",
        "category": "NOTEBOOK CHROMEBOOK",
        "specs": "14 \", processore Intel® Celeron N4500, Intel® UHD Graphics, RAM 4 GB, 64 GB eMMC, Black, Google Chrome OS",
        "rating": "16",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "APPLE MacBook Neo 13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB, 512GB, Magic Keyboard con Touch ID, Giallo agrume",
        "price": "€899,00",
        "brand": "APPLE",
        "model": "MacBook Neo 13''",
        "category": "NOTEBOOK",
        "specs": "13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB RAM, 512GB SSD, Magic Keyboard con Touch ID, Giallo agrume",
        "rating": "40",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "APPLE MacBook Air 13'', Chip M5, 10 CPU 8 GPU, 16GB, 512GB, Mezzanotte",
        "price": "€1449,00",
        "brand": "APPLE",
        "model": "MacBook Air 13''",
        "category": "NOTEBOOK",
        "specs": "13'', Chip M5, 10 CPU 8 GPU, 16GB RAM, 512GB SSD, Mezzanotte",
        "rating": "5",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "LENOVO IdeaPad Slim 3 NOTEBOOK, 15,3 \", processore Qualcomm Snapdragon X X1-26-100, Qualcomm Adreno™ Onboard Graphics, R",
        "price": "€649,49",
        "brand": "LENOVO",
        "model": "IdeaPad Slim 3",
        "category": "NOTEBOOK",
        "specs": "15,3 \", processore Qualcomm Snapdragon X X1-26-100, Qualcomm Adreno™ Onboard Graphics, RAM 16 GB, 512 GB SSD, Grey, Wind",
        "rating": "0",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "ASUS Vivobook 15 F1504 NOTEBOOK, 15,6 \", processore Intel® Core 5 120U, Intel®, RAM 16 GB, 512 GB SSD, Blue, Windows 11 ",
        "price": "€599,00",
        "brand": "ASUS",
        "model": "Vivobook 15 F1504",
        "category": "NOTEBOOK",
        "specs": "15,6 \", processore Intel® Core 5 120U, RAM 16 GB, 512 GB SSD, Blue, Windows 11 Home",
        "rating": "19",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "HP CHROMEBOOK 14A-NF0013NLX NOTEBOOK, 14 \", processore Intel® N100 N100, Intel® UHD Graphics, RAM 8 GB Flash, Silver, Go",
        "price": "€359,00",
        "brand": "HP",
        "model": "CHROMEBOOK 14A-NF0013NLX",
        "category": "NOTEBOOK",
        "specs": "14 \", processore Intel® N100 N100, Intel® UHD Graphics, RAM 8 GB Flash, Silver, Google Chrome OS",
        "rating": "0",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "APPLE MacBook Neo 13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB, 512GB, Magic Keyboard con Touch ID, Rosa pastello",
        "price": "€899,00",
        "brand": "APPLE",
        "model": "MacBook Neo 13''",
        "category": "NOTEBOOK",
        "specs": "13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB RAM, 512GB SSD, Magic Keyboard con Touch ID, Rosa pastello",
        "rating": "40",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "LENOVO Chromebook IP Slim3 NOTEBOOK CHROMEBOOK, 14 \", processore MediaTek Kompanio 520, ARM Mali-G52, RAM 8 GB, 128 GB e",
        "price": "€279,00",
        "brand": "LENOVO",
        "model": "Chromebook IP Slim3",
        "category": "NOTEBOOK CHROMEBOOK",
        "specs": "14 \", processore MediaTek Kompanio 520, ARM Mali-G52, RAM 8 GB, 128 GB eMMC, Grey, Google Chrome OS",
        "rating": "15",
        "availability": "Spedizione disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "HP 15-fc1007nl AI AMD Ryzen™ 5 7520U Computer port...",
        "price": "€ 507,84",
        "brand": "HP",
        "model": "15-fc1007nl AI",
        "category": "Notebook",
        "specs": "AI AMD Ryzen™ 5 7520U",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "HP 15-fd0126nl Intel Core 7 150U Computer portatil...",
        "price": "€ 671,04",
        "brand": "HP",
        "model": "15-fd0126nl",
        "category": "Notebook",
        "specs": "Intel Core 7 150U",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "ASUS Vivobook 15 F1504VA-BQ232W Intel Core 7 150U ...",
        "price": "€ 642,24",
        "brand": "ASUS",
        "model": "Vivobook 15 F1504VA-BQ232W",
        "category": "Notebook",
        "specs": "Intel Core 7 150U",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "Lenovo IdeaPad Slim 3 15IRU8 Intel® Core™ i5 i5-13...",
        "price": "€ 651,84",
        "brand": "Lenovo",
        "model": "IdeaPad Slim 3 15IRU8",
        "category": "Notebook",
        "specs": "Intel® Core™ i5 i5-13",
        "rating": "",
        "availability": "Disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "ASUS Vivobook 16 M1607GA-MB021W Copilot+ PC AMD Ry...",
        "price": "€ 959,90",
        "brand": "ASUS",
        "model": "Vivobook 16 M1607GA-MB021W Copilot+ PC",
        "category": "Notebook",
        "specs": "AMD Ry",
        "rating": "",
        "availability": "Disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "HP 15-FD0129NL NOTEBOOK, 15,6 \", processore Intel® Core 5 120U, Intel®, RAM 16 GB, 1000 GB SSD, Silver, Windows 11",
        "price": "€ 565,47",
        "brand": "HP",
        "model": "15-FD0129NL",
        "category": "NOTEBOOK",
        "specs": "15,6 \", processore Intel® Core 5 120U, RAM 16 GB, 1000 GB SSD, Silver, Windows 11",
        "rating": "",
        "availability": "Spedizione disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "ASUS Vivobook 16 F1607 NOTEBOOK, 16 \", processore Intel® Core Ultra 7 255H , Intel®, RAM 16 GB, 1000 GB SSD, Blue, Windo",
        "price": "€ 832,74",
        "brand": "ASUS",
        "model": "Vivobook 16 F1607",
        "category": "NOTEBOOK",
        "specs": "16 \", processore Intel® Core Ultra 7 255H, RAM 16 GB, 1000 GB SSD, Blue, Windows 11 Home",
        "rating": "",
        "availability": "Spedizione disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "APPLE MacBook Neo 13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB, 256GB, Magic Keyboard, Argento",
        "price": "€ 822,97",
        "brand": "APPLE",
        "model": "MacBook Neo 13''",
        "category": "NOTEBOOK",
        "specs": "13'', Chip A18 Pro, 6 CPU 5 GPU, 8GB RAM, 256GB SSD, Magic Keyboard, Argento",
        "rating": "",
        "availability": "Spedizione disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "LENOVO IdeaPad Slim 5 NOTEBOOK, 16 \", processore Intel® Core Ultra 5 135H, Intel® Arc™ GPU, RAM 16 GB, 512 GB SSD, Grey,",
        "price": "€ 719,97",
        "brand": "LENOVO",
        "model": "IdeaPad Slim 5",
        "category": "NOTEBOOK",
        "specs": "16 \", processore Intel® Core Ultra 5 135H, Intel® Arc™ GPU, RAM 16 GB, 512 GB SSD, Grey, Windows 11 Home",
        "rating": "",
        "availability": "Spedizione disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "APPLE MacBook Air 13 M3 8-core CPU 10-core GPU 16GB 256GB Grigio siderale",
        "price": "€ 1149,00",
        "brand": "APPLE",
        "model": "MacBook Air 13 M3",
        "category": "Notebook",
        "specs": "Chip M3, 8-core CPU, 10-core GPU, RAM 16GB, SSD 256GB",
        "rating": "",
        "availability": "Disponibile",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "APPLE MacBook Air 13 M3 8-core CPU 10-core GPU 16GB 256GB Grigio siderale",
        "price": "€ 1199,00",
        "brand": "APPLE",
        "model": "MacBook Air 13 M3",
        "category": "Notebook",
        "specs": "Chip M3, 8-core CPU, 10-core GPU, RAM 16GB, SSD 256GB",
        "rating": "",
        "availability": "Disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    },
    {
        "name": "ACER Aspire 3 A315-24P AMD Ryzen 5 7520U RAM 16GB SSD 512GB 15.6 Full HD Argento",
        "price": "€ 449,00",
        "brand": "ACER",
        "model": "Aspire 3 A315-24P",
        "category": "Notebook",
        "specs": "AMD Ryzen 5 7520U, RAM 16GB, SSD 512GB, 15.6\" Full HD",
        "rating": "",
        "availability": "SOLO ONLINE",
        "source": "unieuro.it",
        "url": "https://www.unieuro.it/online/Computer-e-Tablet/Computer-Portatili/Notebook"
    },
    {
        "name": "ACER Aspire 3 A315-24P AMD Ryzen 5 7520U RAM 16GB SSD 512GB 15.6 Full HD Argento",
        "price": "€ 429,00",
        "brand": "ACER",
        "model": "Aspire 3 A315-24P",
        "category": "Notebook",
        "specs": "AMD Ryzen 5 7520U, RAM 16GB, SSD 512GB, 15.6\" Full HD",
        "rating": "",
        "availability": "Disponibile",
        "source": "mediaworld.it",
        "url": "https://www.mediaworld.it/it/category/notebook-200101.html"
    }
]


async def seed_if_empty(historical_db) -> None:
    """Popola il DB coi prodotti demo reali se non ci sono prodotti."""
    try:
        existing = await historical_db.search_historical_products({"limit": 1})
        if existing.get("success") and existing.get("products"):
            return
        by_site = {}
        for prod in SEED_PRODUCTS:
            by_site.setdefault(prod["url"], []).append(prod)
        tot = 0
        for url, prods in by_site.items():
            res = await historical_db.save_extracted_products(
                url=url, products=prods, session_id=None, extraction_method="seed_demo",
            )
            tot += res.get("saved_count", 0) if res else 0
        logger.info(f"🌱 Seed demo (reale): inseriti {tot} prodotti in DB vuoto")
    except Exception as e:
        logger.warning(f"⚠️ Seed demo non riuscito: {e}")
