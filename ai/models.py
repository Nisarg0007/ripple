from typing import List, Optional
from pydantic import BaseModel, Field

class ExplanationResponse(BaseModel):
    summary: str
    why_risky: str
    affected_components: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    provider_used: str = "fallback"  # "groq", "nvidia_nim", "fallback"
    is_fallback: bool = False
    fallback_reason: Optional[str] = None
