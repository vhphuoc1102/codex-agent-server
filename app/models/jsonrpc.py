from typing import Any, Optional
from pydantic import BaseModel


class JsonRpcError(BaseModel):
    """JSON-RPC error object."""

    code: int
    message: str
    data: Optional[Any] = None


class JsonRpcRequest(BaseModel):
    """JSON-RPC request (without jsonrpc header per Codex spec)."""

    method: str
    id: int
    params: dict = {}


class JsonRpcResponse(BaseModel):
    """JSON-RPC response."""

    id: int
    result: Optional[dict] = None
    error: Optional[JsonRpcError] = None


class JsonRpcNotification(BaseModel):
    """JSON-RPC notification (no id)."""

    method: str
    params: dict = {}
