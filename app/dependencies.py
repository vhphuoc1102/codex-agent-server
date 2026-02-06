from typing import Optional
from .core import ProcessManager, JsonRpcClient
from .config import settings

# Global instances (initialized during app lifespan)
_process_manager: Optional[ProcessManager] = None
_jsonrpc_client: Optional[JsonRpcClient] = None


def get_process_manager() -> ProcessManager:
    """Get the ProcessManager instance."""
    if _process_manager is None:
        raise RuntimeError("ProcessManager not initialized")
    return _process_manager


def get_jsonrpc_client() -> JsonRpcClient:
    """Get the JsonRpcClient instance."""
    if _jsonrpc_client is None:
        raise RuntimeError("JsonRpcClient not initialized")
    return _jsonrpc_client


def set_instances(process_manager: ProcessManager, jsonrpc_client: JsonRpcClient) -> None:
    """Set global instances (called during app startup)."""
    global _process_manager, _jsonrpc_client
    _process_manager = process_manager
    _jsonrpc_client = jsonrpc_client


def clear_instances() -> None:
    """Clear global instances (called during app shutdown)."""
    global _process_manager, _jsonrpc_client
    _process_manager = None
    _jsonrpc_client = None
