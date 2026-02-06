from typing import Optional, List, Any, Literal
from pydantic import BaseModel


class TurnInput(BaseModel):
    """Input item for a turn."""

    type: Literal["text", "image", "localImage", "skill", "mention"]
    text: Optional[str] = None
    url: Optional[str] = None
    path: Optional[str] = None
    name: Optional[str] = None


class SandboxPolicy(BaseModel):
    """Sandbox policy configuration."""

    type: str  # "readOnly", "workspaceWrite", "externalSandbox", "dangerFullAccess"
    writableRoots: Optional[List[str]] = None
    networkAccess: Optional[bool] = None


class TurnStartParams(BaseModel):
    """Parameters for turn/start."""

    threadId: str
    input: List[TurnInput]
    cwd: Optional[str] = None
    approvalPolicy: Optional[str] = None
    sandboxPolicy: Optional[SandboxPolicy] = None
    model: Optional[str] = None
    effort: Optional[str] = None  # "low", "medium", "high"
    summary: Optional[str] = None
    personality: Optional[str] = None
    outputSchema: Optional[dict] = None


class TurnError(BaseModel):
    """Turn error information."""

    message: str
    codexErrorInfo: Optional[str] = None
    additionalDetails: Optional[str] = None


class Turn(BaseModel):
    """Turn object representing a user request and agent response."""

    id: str
    status: str  # "inProgress", "completed", "interrupted", "failed"
    items: List[Any] = []
    error: Optional[TurnError] = None


class TurnStartResponse(BaseModel):
    """Response from turn/start."""

    turn: Turn
