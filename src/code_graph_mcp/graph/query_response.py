"""
Query Response Data Structures

Standardized response formats for graph query API endpoints.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class NodeResponse:
    """Serializable node response for API endpoints."""
    id: str
    name: str
    type: str
    language: str
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    complexity: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class RelationshipResponse:
    """Serializable relationship response for API endpoints."""
    id: str
    source_id: str
    target_id: str
    type: str
    is_seam: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class TraversalResponse:
    """Complete response for graph traversal queries."""
    nodes: List[NodeResponse]
    edges: List[RelationshipResponse]
    stats: Dict[str, Any]
    execution_time_ms: float
    query_type: str = ""
    start_node_id: Optional[str] = None
    max_depth: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "stats": self.stats,
            "execution_time_ms": self.execution_time_ms,
            "query_type": self.query_type,
            "start_node_id": self.start_node_id,
            "max_depth": self.max_depth,
        }


@dataclass
class SearchResultResponse:
    """Response for node search queries."""
    results: List[NodeResponse]
    total_count: int
    query: str
    filters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_count": self.total_count,
            "query": self.query,
            "filters": self.filters,
        }


@dataclass
class CallChainResponse:
    """Response for call chain traversal."""
    chain: List[NodeResponse]
    edges: List[RelationshipResponse]
    has_seams: bool
    seam_count: int
    total_hops: int
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chain": [n.to_dict() for n in self.chain],
            "edges": [e.to_dict() for e in self.edges],
            "has_seams": self.has_seams,
            "seam_count": self.seam_count,
            "total_hops": self.total_hops,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class GraphStatsResponse:
    """Response for graph statistics queries."""
    total_nodes: int
    total_relationships: int
    node_types: Dict[str, int]
    relationship_types: Dict[str, int]
    languages: Dict[str, int]
    seam_count: int
    complexity_distribution: Dict[str, int]
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class SeamResponse:
    """Response for seam (cross-language) relationship."""
    id: str
    source_id: str
    source_name: str
    source_language: str
    target_id: str
    target_name: str
    target_language: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ErrorResponse:
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: int = 500
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
