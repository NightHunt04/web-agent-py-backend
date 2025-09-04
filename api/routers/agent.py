from fastapi import APIRouter, Request, Depends
from ..services.agent import run_agent_stream
from ..schemas.agent import AgentRequest
from ..dependencies.concurrent_tasks import check_traffic

router = APIRouter(prefix = "/agent", tags = ["Agent"])

@router.post("/run")
async def run_agent_endpoint(request: Request, payload: AgentRequest, is_free: bool = Depends(check_traffic)):
    if not is_free:
        return { "type": "error", "data": { "message": "Too many concurrent tasks running. Please try again later." } }

    return await run_agent_stream(request, payload)