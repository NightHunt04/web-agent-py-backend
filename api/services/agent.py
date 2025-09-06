from fastapi.responses import StreamingResponse
from fastapi import HTTPException, Request
from ..schemas.agent import AgentRequest
from ..agent_core.browser import Browser
from ..agent_core.models.gemini import GeminiProvider
from ..agent_core.agent.agent import Agent
from ..utils.load_ws_endpoint import load_ws_endpoint
from ..utils.update_ws_traffic import update_ws_traffic
from ..utils.concurrent_tasks import add_session, remove_session
import asyncio
import time
import json

async def run_agent_stream(request: Request, payload: AgentRequest):
    try:
        ws_endpoint = load_ws_endpoint()
        if ws_endpoint is None:
            raise HTTPException(status_code = 503, detail="All browser instances are busy")

        client_ip = request.headers.get("X-Forwarded-For") or request.client.host
        add_session(ip = client_ip)

        browser = Browser(ws_endpoint = ws_endpoint)

        model = GeminiProvider(
            api_key = payload.api_key, 
            model = payload.model,
            max_tokens = payload.max_tokens, 
            reasoning_effort = payload.reasoning_effort, 
            temperature = payload.temperature, 
            top_p = payload.top_p
        )

        agent = Agent(
            browser = browser, 
            model = model, 
            scraper_response_json_format = payload.scraper_schema
        )

        update_ws_traffic(ws_endpoint, increment = True)

        async def event_stream():
            try:
                yield f"{json.dumps({"type": "browser_init", "data": "Initializing browser..."}, ensure_ascii=False)}\n"
                await browser.init_browser()
                yield f"{json.dumps({"type": "browser_init_done", "data": "Browser initialized"}, ensure_ascii=False)}\n"

                yield f"{json.dumps({"type": "agent_start", "data": "Running agent..."}, ensure_ascii=False)}\n"
                async for update in agent.arun(
                    query = payload.prompt,
                    verbose = True,
                    wait_between_actions = payload.wait_between_actions,
                    screenshot_each_step = True
                ):
                    if await request.is_disconnected():
                        yield f"{json.dumps({"type": "cancelled", "data": "Client disconnected"}, ensure_ascii=False)}\n"
                        break

                    yield f"{update}\n"
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                yield f"{json.dumps({"type": "cancelled", "data": "Request cancelled by the server"}, ensure_ascii=False)}\n"
            except Exception as e:
                yield f"{json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False)}\n"
            finally:
                remove_session(client_ip)
                update_ws_traffic(ws_endpoint, decrement=True)
                print("Stream completed")
                yield f"{json.dumps({"type": "done", "data": "Stream completed"}, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))