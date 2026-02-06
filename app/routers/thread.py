from fastapi import APIRouter, Depends, HTTPException
import structlog

from ..dependencies import get_jsonrpc_client
from ..core.jsonrpc_client import JsonRpcClient, JsonRpcError
from ..models.thread import (
    ThreadStartParams,
    ThreadStartResponse,
    ThreadResumeParams,
    ThreadResumeResponse,
    ThreadForkParams,
    ThreadForkResponse,
    ThreadReadParams,
    ThreadReadResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/thread", tags=["thread"])


@router.post("/start", response_model=ThreadStartResponse)
async def thread_start(
    params: ThreadStartParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> ThreadStartResponse:
    """Create a new conversation thread."""
    try:
        result = await client.call(
            "thread/start",
            params.model_dump(exclude_none=True),
        )
        return ThreadStartResponse(**result)
    except JsonRpcError as e:
        logger.error("thread/start failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("thread/start error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=ThreadResumeResponse)
async def thread_resume(
    params: ThreadResumeParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> ThreadResumeResponse:
    """Resume an existing thread."""
    try:
        result = await client.call(
            "thread/resume",
            params.model_dump(exclude_none=True),
        )
        return ThreadResumeResponse(**result)
    except JsonRpcError as e:
        logger.error("thread/resume failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("thread/resume error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fork", response_model=ThreadForkResponse)
async def thread_fork(
    params: ThreadForkParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> ThreadForkResponse:
    """Fork a thread into a new thread."""
    try:
        result = await client.call(
            "thread/fork",
            params.model_dump(exclude_none=True),
        )
        return ThreadForkResponse(**result)
    except JsonRpcError as e:
        logger.error("thread/fork failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("thread/fork error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read", response_model=ThreadReadResponse)
async def thread_read(
    params: ThreadReadParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> ThreadReadResponse:
    """Read a stored thread without resuming."""
    try:
        result = await client.call(
            "thread/read",
            params.model_dump(exclude_none=True),
        )
        return ThreadReadResponse(**result)
    except JsonRpcError as e:
        logger.error("thread/read failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("thread/read error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
