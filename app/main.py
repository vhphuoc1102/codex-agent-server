from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core import ProcessManager, JsonRpcClient
from .dependencies import set_instances, clear_instances
from .routers import thread_router, turn_router, skill_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start/stop codex subprocess."""
    logger.info("Starting Codex Agent Server")

    # Create and start process manager
    process_manager = ProcessManager(
        codex_path=settings.codex_path,
        client_name=settings.client_name,
        client_title=settings.client_title,
        client_version=settings.client_version,
    )

    # Create JSON-RPC client
    jsonrpc_client = JsonRpcClient(process_manager)

    try:
        # Start subprocess and initialize
        await process_manager.start()
        await process_manager.initialize(timeout=settings.initialization_timeout)

        # Start message reader
        await jsonrpc_client.start()

        # Set global instances
        set_instances(process_manager, jsonrpc_client)

        logger.info("Codex Agent Server ready")
        yield

    finally:
        logger.info("Shutting down Codex Agent Server")

        # Stop client and process
        await jsonrpc_client.stop()
        await process_manager.stop()

        # Clear global instances
        clear_instances()

        logger.info("Codex Agent Server stopped")


# Create FastAPI application
app = FastAPI(
    title="Codex Agent Server",
    description="REST API bridge for Codex app-server",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(thread_router)
app.include_router(turn_router)
app.include_router(skill_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from .dependencies import get_process_manager

    try:
        pm = get_process_manager()
        return {
            "status": "healthy",
            "codex_alive": pm.is_alive,
        }
    except RuntimeError:
        return {
            "status": "unhealthy",
            "codex_alive": False,
        }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Codex Agent Server",
        "version": "0.1.0",
        "endpoints": {
            "thread/start": "POST /api/thread/start",
            "thread/resume": "POST /api/thread/resume",
            "thread/fork": "POST /api/thread/fork",
            "thread/read": "POST /api/thread/read",
            "turn/start": "POST /api/turn/start",
            "skills/list": "POST /api/skills/list",
            "skills/config/write": "POST /api/skills/config/write",
        },
    }
