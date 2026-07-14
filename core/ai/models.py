from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AgentResult:
    agent_name: str
    role: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
