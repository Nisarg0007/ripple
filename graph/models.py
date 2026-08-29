from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    FILE = "file"
    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    ENDPOINT = "endpoint"

class EdgeType(str, Enum):
    IMPORTS = "imports"
    CONTAINS = "contains"
    CALLS = "calls"
    EXPOSES = "exposes"
    INHERITS = "inherits"

class GraphNode(BaseModel):
    id: str  # Unique identifier (e.g. "file:services/user.py", "function:services/user.py::read_user", "endpoint:GET:/users/{id}")
    label: str
    type: NodeType
    file_path: Optional[str] = None
    lineno: Optional[int] = None
    end_lineno: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    source: str
    target: str
    type: EdgeType
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ImpactedNode(BaseModel):
    node: GraphNode
    distance: int  # 0 for directly changed, 1 for immediate dependents, 2+ for indirect dependents
    impact_type: str  # "direct", "indirect_caller", "impacted_endpoint", "impacted_file"
    path: List[str] = Field(default_factory=list)  # Dependency path leading to this impact

class BlastRadiusResult(BaseModel):
    directly_changed_files: List[str] = Field(default_factory=list)
    directly_changed_nodes: List[GraphNode] = Field(default_factory=list)
    impacted_nodes: List[ImpactedNode] = Field(default_factory=list)
    impacted_endpoints: List[GraphNode] = Field(default_factory=list)
    total_impacted_count: int = 0
    max_depth: int = 0

class NetworkGraphExport(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
