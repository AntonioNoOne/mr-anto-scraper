"""
Pydantic models per MR Scraper API.
"""

from pydantic import BaseModel
from typing import List, Optional


class ExtractRequest(BaseModel):
    url: str

class MultipleExtractRequest(BaseModel):
    urls: List[str]

class ExtractResponse(BaseModel):
    success: bool
    products: List[dict] = []
    error: Optional[str] = None
    total_found: int = 0
    containers_found: int = 0
    container_selector: Optional[str] = None
    url: Optional[str] = None
    extraction_method: Optional[str] = None  # es: "browser" | "jina_reader"

class MultipleExtractResponse(BaseModel):
    success: bool
    results: List[ExtractResponse] = []
    total_sites: int = 0
    total_products: int = 0
    errors: List[str] = []

class CompareRequest(BaseModel):
    results: List[dict]  # Risultati da comparare
    sources: Optional[List[str]] = None  # Domini selezionati per il confronto (es: ['amazon.it', 'mediaworld.it'])

class ComparePricesRequest(BaseModel):
    products: List[dict]  # Prodotti estratti da confrontare

class BrowserConfigRequest(BaseModel):
    mode: str  # 'normal', 'stealth', 'visible'
    timeout: int = 60
    human_delay: float = 2.0
    user_agent: str = 'auto'
    proxy: Optional[str] = None

class CompareResponse(BaseModel):
    success: bool
    matches: List[dict] = []
    statistics: dict = {}
    total_sites: int = 0
    total_products: int = 0
    comparable_products: int = 0
    error: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # "user" o "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model: str = "openai"  # "openai", "ollama", "gemini"
    conversation_history: List[ChatMessage] = []
    context_data: Optional[dict] = None  # Contesto completo dell'applicazione

class ChatResponse(BaseModel):
    success: bool
    response: str
    model_used: str
    error: Optional[str] = None
