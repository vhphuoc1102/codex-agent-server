from fastapi import APIRouter, Depends, HTTPException
import structlog

from ..dependencies import get_jsonrpc_client
from ..core.jsonrpc_client import JsonRpcClient, JsonRpcError
from ..models.turn import TurnStartParams, TurnStartResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/turn", tags=["turn"])


@router.post("/start", response_model=TurnStartResponse)
async def turn_start(
    params: TurnStartParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> TurnStartResponse:
    """Start a new turn (user input + agent response)."""
    try:
        # Convert input items to dicts
        params_dict = params.model_dump(exclude_none=True)

        result = await client.call(
            "turn/start",
            params_dict,
        )
        return TurnStartResponse(**result)
    except JsonRpcError as e:
        logger.error("turn/start failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("turn/start error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
