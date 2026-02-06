import asyncio
from typing import Any, Callable, Optional
import structlog

from .process_manager import ProcessManager
from ..config import settings

logger = structlog.get_logger(__name__)


class JsonRpcClient:
    """Handles JSON-RPC 2.0 protocol communication with codex app-server."""

    def __init__(self, process_manager: ProcessManager):
        self._process = process_manager
        self._next_id = 1
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._notification_handlers: dict[str, list[Callable]] = {}
        self._reader_task: Optional[asyncio.Task] = None
        self._id_lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the background message reader task."""
        if self._reader_task is not None:
            return

        self._reader_task = asyncio.create_task(self._message_reader_loop())
        logger.info("JSON-RPC client started")

    async def stop(self) -> None:
        """Stop the background message reader task."""
        if self._reader_task is None:
            return

        self._reader_task.cancel()
        try:
            await self._reader_task
        except asyncio.CancelledError:
            pass

        self._reader_task = None

        # Cancel all pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        logger.info("JSON-RPC client stopped")

    async def _get_next_id(self) -> int:
        """Generate unique request ID."""
        async with self._id_lock:
            request_id = self._next_id
            self._next_id += 1
            return request_id

    async def call(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 300.0,
    ) -> dict:
        """Send a JSON-RPC request and await the response."""
        request_id = await self._get_next_id()

        request = {
            "method": method,
            "id": request_id,
            "params": params or {},
        }

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            # Send request
            await self._process.send_message(request)

            # Wait for response with timeout
            result = await asyncio.wait_for(future, timeout=timeout)

            if "error" in result:
                error = result["error"]
                raise JsonRpcError(
                    code=error.get("code", -1),
                    message=error.get("message", "Unknown error"),
                    data=error.get("data"),
                )

            return result.get("result", {})

        except asyncio.TimeoutError:
            logger.error("Request timeout", method=method, id=request_id)
            raise
        finally:
            self._pending_requests.pop(request_id, None)

    def on_notification(self, method: str, handler: Callable) -> None:
        """Register a handler for a notification type."""
        if method not in self._notification_handlers:
            self._notification_handlers[method] = []
        self._notification_handlers[method].append(handler)

    def remove_notification_handler(self, method: str, handler: Callable) -> None:
        """Remove a notification handler."""
        if method in self._notification_handlers:
            self._notification_handlers[method] = [
                h for h in self._notification_handlers[method] if h != handler
            ]

    async def wait_for_notification(
        self,
        method: str,
        predicate: Optional[Callable[[dict], bool]] = None,
        timeout: Optional[float] = None,
    ) -> dict:
        """Wait for a notification matching the predicate.

        Args:
            method: The notification method to wait for.
            predicate: Optional function to filter notifications.
            timeout: Timeout in seconds (defaults to settings.request_timeout).

        Returns:
            The notification params that matched.
        """
        if timeout is None:
            timeout = settings.request_timeout

        future: asyncio.Future = asyncio.get_event_loop().create_future()

        async def handler(params: dict) -> None:
            if predicate is None or predicate(params):
                if not future.done():
                    future.set_result(params)

        self.on_notification(method, handler)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        finally:
            self.remove_notification_handler(method, handler)

    async def _message_reader_loop(self) -> None:
        """Background task that reads and routes messages."""
        logger.info("Message reader loop started")

        try:
            async for message in self._process.read_messages():
                await self._handle_message(message)
        except asyncio.CancelledError:
            logger.info("Message reader loop cancelled")
            raise
        except Exception as e:
            logger.error("Message reader loop error", error=str(e))
            raise

    async def _handle_message(self, message: dict) -> None:
        """Route a message to the appropriate handler."""
        # Check if this is a response (has id)
        if "id" in message and message["id"] is not None:
            request_id = message["id"]
            future = self._pending_requests.get(request_id)

            if future is not None and not future.done():
                future.set_result(message)
            else:
                logger.warning("Received response for unknown request", id=request_id)

        # Check if this is a notification (has method, no id)
        elif "method" in message:
            method = message["method"]
            params = message.get("params", {})

            handlers = self._notification_handlers.get(method, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(params)
                    else:
                        handler(params)
                except Exception as e:
                    logger.error(
                        "Notification handler error",
                        method=method,
                        error=str(e),
                    )


class JsonRpcError(Exception):
    """JSON-RPC error response."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict:
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result
