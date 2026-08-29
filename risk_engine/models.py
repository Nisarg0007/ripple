from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskFactor(BaseModel):
    name: str
    description: str
    score: int  # Numerical point contribution
    severity: str  # "info", "low", "medium", "high", "critical"

class RiskReport(BaseModel):
    total_score: int  # 0 to 100
    risk_level: RiskLevel
    factors: List[RiskFactor] = Field(default_factory=list)
    directly_changed_files: List[str] = Field(default_factory=list)
    directly_changed_nodes: List[str] = Field(default_factory=list)
    impacted_nodes: List[str] = Field(default_factory=list)
    affected_services: List[str] = Field(default_factory=list)
    affected_endpoints: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    is_breaking_change: bool = False
