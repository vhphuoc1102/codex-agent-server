import asyncio
import json
import structlog
from typing import Optional, AsyncIterator

logger = structlog.get_logger(__name__)


class ProcessManager:
    """Manages the lifecycle of the codex app-server subprocess."""

    def __init__(
        self,
        codex_path: str = "codex",
        client_name: str = "codex-bridge-server",
        client_title: str = "Codex Bridge Server",
        client_version: str = "0.1.0",
    ):
        self._codex_path = codex_path
        self._client_info = {
            "name": client_name,
            "title": client_title,
            "version": client_version,
        }
        self._process: Optional[asyncio.subprocess.Process] = None
        self._stdin_lock = asyncio.Lock()
        self._initialized = False

    @property
    def is_alive(self) -> bool:
        """Check if the subprocess is running."""
        return self._process is not None and self._process.returncode is None

    async def start(self) -> None:
        """Spawn the codex app-server subprocess."""
        if self.is_alive:
            logger.warning("Process already running")
            return

        logger.info("Starting codex app-server", codex_path=self._codex_path)

        self._process = await asyncio.create_subprocess_exec(
            self._codex_path,
            "app-server",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info("Codex app-server started", pid=self._process.pid)
        self._initialized = False

    async def stop(self) -> None:
        """Gracefully terminate the subprocess."""
        if not self.is_alive:
            return

        logger.info("Stopping codex app-server")

        try:
            self._process.terminate()
            await asyncio.wait_for(self._process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Process did not terminate, killing")
            self._process.kill()
            await self._process.wait()

        self._process = None
        self._initialized = False
        logger.info("Codex app-server stopped")

    async def send_message(self, message: dict) -> None:
        """Write a JSON message to subprocess stdin."""
        if not self.is_alive or self._process.stdin is None:
            raise RuntimeError("Process not running")

        line = json.dumps(message) + "\n"
        async with self._stdin_lock:
            self._process.stdin.write(line.encode())
            await self._process.stdin.drain()

        logger.debug("Sent message", method=message.get("method"), id=message.get("id"))

    async def read_line(self) -> Optional[dict]:
        """Read a single JSON line from subprocess stdout."""
        if not self.is_alive or self._process.stdout is None:
            return None

        try:
            line = await self._process.stdout.readline()
            if not line:
                return None

            data = json.loads(line.decode().strip())
            logger.debug(
                "Received message",
                method=data.get("method"),
                id=data.get("id"),
                has_result="result" in data,
                has_error="error" in data,
            )
            return data
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON", error=str(e), line=line)
            return None

    async def read_messages(self) -> AsyncIterator[dict]:
        """Yield parsed JSON messages from subprocess stdout."""
        while self.is_alive:
            message = await self.read_line()
            if message is None:
                break
            yield message

    async def initialize(self, timeout: float = 30.0) -> dict:
        """Send initialize + initialized handshake."""
        if self._initialized:
            logger.warning("Already initialized")
            return {}

        if not self.is_alive:
            raise RuntimeError("Process not running")

        # Send initialize request
        init_request = {
            "method": "initialize",
            "id": 0,
            "params": {"clientInfo": self._client_info},
        }
        await self.send_message(init_request)

        # Wait for initialize response
        start_time = asyncio.get_event_loop().time()
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Initialize timeout")

            message = await self.read_line()
            if message is None:
                raise RuntimeError("Process closed during initialization")

            # Check if this is the initialize response
            if message.get("id") == 0:
                if "error" in message:
                    raise RuntimeError(f"Initialize failed: {message['error']}")
                break

        # Send initialized notification
        await self.send_message({"method": "initialized", "params": {}})

        self._initialized = True
        logger.info("Codex app-server initialized")

        return message.get("result", {})

    async def ensure_alive(self) -> None:
        """Check process health and restart if needed."""
        if not self.is_alive:
            logger.warning("Codex process died, restarting")
            await self.start()
            await self.initialize()
