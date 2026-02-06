from fastapi import APIRouter, Depends, HTTPException
import structlog

from ..dependencies import get_jsonrpc_client
from ..core.jsonrpc_client import JsonRpcClient, JsonRpcError
from ..models.skill import (
    SkillsListParams,
    SkillsListResponse,
    SkillsConfigWriteParams,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.post("/list", response_model=SkillsListResponse)
async def skills_list(
    params: SkillsListParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> SkillsListResponse:
    """List available skills."""
    try:
        result = await client.call(
            "skills/list",
            params.model_dump(exclude_none=True),
        )
        return SkillsListResponse(**result)
    except JsonRpcError as e:
        logger.error("skills/list failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("skills/list error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/write")
async def skills_config_write(
    params: SkillsConfigWriteParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> dict:
    """Enable or disable a skill by path."""
    try:
        result = await client.call(
            "skills/config/write",
            params.model_dump(exclude_none=True),
        )
        return result
    except JsonRpcError as e:
        logger.error("skills/config/write failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("skills/config/write error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
