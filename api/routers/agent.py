from fastapi import APIRouter, Request
from ..services.agent import run_agent_stream
from ..schemas.agent import AgentRequest

router = APIRouter(prefix = "/agent", tags = ["Agent"])

@router.post("/run")
async def run_agent_endpoint(request: Request, payload: AgentRequest):
    return await run_agent_stream(request, payload)