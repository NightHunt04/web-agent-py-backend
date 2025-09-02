from .browser import Browser
from .models.gemini import GeminiProvider
from .agent.agent import Agent
from typing import AsyncGenerator, Dict, Any
import json

async def run_agent(
    prompt: str,
    ws_endpoint: str = "wss://dumb-cdp.onrender.com/dumb-cdp",
    scraper_schema: Dict[str, Any] | None = None,
    api_key: str | None = None,
    wait_between_actions: int = 1,
    max_tokens: int = 19334,
    temperature: float = 0.4,
    top_p: float = 1.0,
    reasoning_effort: str = 'disable',
    model: str = 'gemini-2.5-flash'
) -> AsyncGenerator[str, None]:
    
    try:
        browser = Browser(ws_endpoint = ws_endpoint)

        model = GeminiProvider(
            api_key = api_key, 
            model = model,
            max_tokens = max_tokens, 
            reasoning_effort = reasoning_effort, 
            temperature = temperature, 
            top_p = top_p
        )
        
        agent = Agent(browser = browser, model = model, scraper_response_json_format = scraper_schema)

        async for update in agent.arun(
            query=prompt,
            verbose=True,
            wait_between_actions=wait_between_actions,
            screenshot_each_step=True
        ):
            yield update

    except Exception as e:
        import traceback
        error_str = traceback.format_exc()
        print("ERROR in run_agent:", error_str)
        yield json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)
