from typing import Optional, List, Any
from pydantic import BaseModel


class SkillInterface(BaseModel):
    """Skill UI interface metadata."""

    displayName: Optional[str] = None
    shortDescription: Optional[str] = None


class SkillDependencies(BaseModel):
    """Skill dependencies."""

    tools: Optional[List[Any]] = None


class Skill(BaseModel):
    """Skill object."""

    name: str
    description: Optional[str] = None
    enabled: bool = True
    interface: Optional[SkillInterface] = None
    dependencies: Optional[SkillDependencies] = None


class SkillsForCwd(BaseModel):
    """Skills for a specific cwd."""

    cwd: str
    skills: List[Skill] = []
    errors: List[str] = []


class SkillsListParams(BaseModel):
    """Parameters for skills/list."""

    cwds: Optional[List[str]] = None
    forceReload: bool = False


class SkillsListResponse(BaseModel):
    """Response from skills/list."""

    data: List[SkillsForCwd]


class SkillsConfigWriteParams(BaseModel):
    """Parameters for skills/config/write."""

    path: str
    enabled: bool


class SkillsConfigWriteResponse(BaseModel):
    """Response from skills/config/write."""

    pass  # Empty response on success
