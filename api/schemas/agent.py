from pydantic import BaseModel
from typing import Optional, Dict, Any

class AgentRequest(BaseModel):
    prompt: str
    scraper_schema: Optional[Dict[str, Any]] = None
    api_key: Optional[str] = None
    wait_between_actions: int = 1
    max_tokens: int = 19334
    temperature: float = 0.4
    top_p: float = 1.0
    reasoning_effort: str = 'disable'
    model: str = 'gemini-2.5-flash'