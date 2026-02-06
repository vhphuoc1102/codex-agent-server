from typing import Optional, List, Any
from pydantic import BaseModel


class Thread(BaseModel):
    """Thread object representing a conversation."""

    id: str
    preview: str = ""
    modelProvider: Optional[str] = None
    createdAt: Optional[int] = None
    updatedAt: Optional[int] = None
    turns: Optional[List[Any]] = None


class ThreadStartParams(BaseModel):
    """Parameters for thread/start."""

    model: Optional[str] = None
    cwd: Optional[str] = None
    approvalPolicy: Optional[str] = None  # "never", "unlessTrusted", etc.
    sandbox: Optional[str] = None
    personality: Optional[str] = None


class ThreadStartResponse(BaseModel):
    """Response from thread/start."""

    thread: Thread


class ThreadResumeParams(BaseModel):
    """Parameters for thread/resume."""

    threadId: str
    personality: Optional[str] = None


class ThreadResumeResponse(BaseModel):
    """Response from thread/resume."""

    thread: Thread


class ThreadForkParams(BaseModel):
    """Parameters for thread/fork."""

    threadId: str


class ThreadForkResponse(BaseModel):
    """Response from thread/fork."""

    thread: Thread


class ThreadReadParams(BaseModel):
    """Parameters for thread/read."""

    threadId: str
    includeTurns: bool = False


class ThreadReadResponse(BaseModel):
    """Response from thread/read."""

    thread: Thread
