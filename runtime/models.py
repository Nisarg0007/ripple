from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class RuntimeObservation(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    source_service: str
    destination_service: str
    operation: str  # e.g. "POST /payments"
    duration_ms: float
    status_code: int = 200  # HTTP status or gRPC code
    is_error: bool = False
    timestamp: float = 0.0

class RuntimeEdge(BaseModel):
    source_service: str
    destination_service: str
    operation: str
    request_count: int = 0
    error_count: int = 0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0

class RuntimeGraph(BaseModel):
    services: List[str] = Field(default_factory=list)
    edges: List[RuntimeEdge] = Field(default_factory=list)
    observations_count: int = 0

class DriftItem(BaseModel):
    source: str
    target: str
    operation: Optional[str] = None
    drift_type: str  # "static_only", "runtime_only", "verified"
    description: str

class ArchitectureDriftReport(BaseModel):
    verified_dependencies: List[DriftItem] = Field(default_factory=list)
    static_only_dependencies: List[DriftItem] = Field(default_factory=list)
    runtime_only_dependencies: List[DriftItem] = Field(default_factory=list)  # Runtime drift!
    drift_score: int = 0  # 0 to 100 percentage of unverified or extra dependencies
