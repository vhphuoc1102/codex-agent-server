import asyncio
from fastapi import APIRouter, Depends, HTTPException
import structlog

from ..dependencies import get_jsonrpc_client
from ..core.jsonrpc_client import JsonRpcClient, JsonRpcError
from ..models.turn import TurnStartParams, TurnStartResponse
from ..config import settings

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/turn", tags=["turn"])


@router.post("/start", response_model=TurnStartResponse)
async def turn_start(
    params: TurnStartParams,
    client: JsonRpcClient = Depends(get_jsonrpc_client),
) -> TurnStartResponse:
    """Start a new turn and wait for completion.

    This endpoint starts a turn and waits for the turn/completed notification
    before returning the full response with all items.
    """
    try:
        params_dict = params.model_dump(exclude_none=True)

        # Track state for matching the completion notification
        turn_state = {"expected_id": None, "completed": None}
        completion_event = asyncio.Event()

        async def on_turn_completed(notification_params: dict) -> None:
            """Handle turn/completed notification."""
            turn = notification_params.get("turn", {})
            turn_id = turn.get("id")

            # Match by turn ID if we have it
            if turn_state["expected_id"] is not None:
                if turn_id == turn_state["expected_id"]:
                    turn_state["completed"] = notification_params
                    completion_event.set()
            else:
                # Store for later verification (shouldn't normally happen)
                turn_state["completed"] = notification_params
                completion_event.set()

        # Register handler before starting turn to avoid race conditions
        client.on_notification("turn/completed", on_turn_completed)

        try:
            # Start the turn - returns immediately with inProgress status
            result = await client.call("turn/start", params_dict)
            turn_state["expected_id"] = result.get("turn", {}).get("id")

            if not turn_state["expected_id"]:
                # No turn ID returned, return immediate result
                logger.warning("turn/start returned no turn ID")
                return TurnStartResponse(**result)

            logger.info(
                "Turn started, waiting for completion",
                turn_id=turn_state["expected_id"],
            )

            # Check if we already got the completion (unlikely but possible)
            if turn_state["completed"] is not None:
                completed_id = turn_state["completed"].get("turn", {}).get("id")
                if completed_id == turn_state["expected_id"]:
                    logger.info("Turn already completed", turn_id=completed_id)
                    return TurnStartResponse(**turn_state["completed"])

            # Wait for turn/completed notification
            await asyncio.wait_for(
                completion_event.wait(),
                timeout=settings.request_timeout,
            )

            logger.info(
                "Turn completed",
                turn_id=turn_state["expected_id"],
                status=turn_state["completed"].get("turn", {}).get("status"),
            )

            return TurnStartResponse(**turn_state["completed"])

        finally:
            # Always clean up the notification handler
            client.remove_notification_handler("turn/completed", on_turn_completed)

    except asyncio.TimeoutError:
        logger.error(
            "turn/start timeout waiting for completion",
            turn_id=turn_state.get("expected_id"),
            timeout=settings.request_timeout,
        )
        raise HTTPException(
            status_code=504,
            detail=f"Turn completion timeout after {settings.request_timeout}s",
        )
    except JsonRpcError as e:
        logger.error("turn/start failed", error=e.message, code=e.code)
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        logger.error("turn/start error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
