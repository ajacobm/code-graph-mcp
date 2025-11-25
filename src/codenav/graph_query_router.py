"""Hybrid Graph Query Router

Routes queries to optimal backend: rustworkx (fast) or Memgraph (complex).
Complexity detection determines routing strategy.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from ..universal_graph import UniversalGraph
from .memgraph_sync import MemgraphClient

logger = logging.getLogger(__name__)


@dataclass
class QueryPlan:
    """Analysis of query complexity and routing decision."""

    query_id: str
    query_type: str
    complexity_score: float  # 0-100
    estimated_hops: int
    has_pattern_matching: bool
    requires_algorithm: bool
    recommended_backend: str  # "rustworkx" or "memgraph"
    reasoning: str
    execution_time_ms: Optional[float] = None
    actual_backend: Optional[str] = None


class QueryComplexityDetector:
    """Analyze query requirements to determine optimal backend."""

    # Thresholds
    HOP_THRESHOLD = 3  # Routes >3 hops to Memgraph
    PATTERN_KEYWORDS = [
        "regex",
        "wildcard",
        "contains",
        "startswith",
        "endswith",
        "matches",
        "~",
        "*",
    ]
    ALGORITHM_KEYWORDS = [
        "pagerank",
        "centrality",
        "community",
        "shortest",
        "all_paths",
        "cycles",
        "articulation",
    ]

    @staticmethod
    def analyze_query(
        query_type: str, start_node: Optional[str] = None, **params
    ) -> QueryPlan:
        """Analyze query and return routing plan."""
        import uuid

        query_id = str(uuid.uuid4())[:8]
        complexity_score = 0.0
        reasoning_parts = []

        # Detect estimated hops
        max_hops = params.get("max_depth", params.get("max_hops", 3))
        has_hops = max_hops > QueryComplexityDetector.HOP_THRESHOLD

        if has_hops:
            complexity_score += 30
            reasoning_parts.append(f"Hop count {max_hops} > threshold")

        # Check for pattern matching
        has_pattern = False
        query_str = str(params).lower()

        for keyword in QueryComplexityDetector.PATTERN_KEYWORDS:
            if keyword in query_str:
                has_pattern = True
                complexity_score += 20
                reasoning_parts.append(f"Pattern matching detected ({keyword})")
                break

        # Check for graph algorithms
        requires_algorithm = False
        for keyword in QueryComplexityDetector.ALGORITHM_KEYWORDS:
            if keyword in query_str:
                requires_algorithm = True
                complexity_score += 40
                reasoning_parts.append(f"Algorithm required ({keyword})")
                break

        # Map query types
        query_complexity_map = {
            "find_callers": 5,
            "find_callees": 5,
            "find_references": 5,
            "impact_analysis": 50,
            "shortest_path": 40,
            "all_paths": 60,
            "community_detection": 80,
            "cycle_detection": 60,
            "god_functions": 70,
        }

        type_complexity = query_complexity_map.get(query_type, 10)
        complexity_score += type_complexity

        # Route based on complexity
        recommended_backend = "rustworkx"
        if complexity_score >= 50 or has_hops or requires_algorithm:
            recommended_backend = "memgraph"

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Simple query"

        return QueryPlan(
            query_id=query_id,
            query_type=query_type,
            complexity_score=complexity_score,
            estimated_hops=max_hops,
            has_pattern_matching=has_pattern,
            requires_algorithm=requires_algorithm,
            recommended_backend=recommended_backend,
            reasoning=reasoning,
        )


class HybridGraphQueryEngine:
    """Routes queries to optimal backend with performance logging."""

    def __init__(
        self,
        rustworkx_graph: UniversalGraph,
        memgraph_client: Optional[MemgraphClient] = None,
    ):
        self.rustworkx_graph = rustworkx_graph
        self.memgraph = memgraph_client
        self.query_history: List[QueryPlan] = []

    async def find_callers(
        self, symbol: str, include_distant: bool = False
    ) -> Tuple[List[str], QueryPlan]:
        """Find nodes that call a given symbol (rustworkx for speed)."""
        plan = QueryComplexityDetector.analyze_query("find_callers", symbol)

        start_time = datetime.now()

        # Always use rustworkx for direct callers (simple, fast)
        try:
            result = self.rustworkx_graph.find_function_callers(symbol)
            plan.actual_backend = "rustworkx"
        except Exception as e:
            logger.error(f"Failed to find callers: {e}")
            result = []

        plan.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.query_history.append(plan)

        return result, plan

    async def find_callees(
        self, symbol: str, include_distant: bool = False
    ) -> Tuple[List[str], QueryPlan]:
        """Find nodes called by a given symbol."""
        plan = QueryComplexityDetector.analyze_query("find_callees", symbol)

        start_time = datetime.now()

        # Always use rustworkx for direct callees
        try:
            result = self.rustworkx_graph.find_function_callees(symbol)
            plan.actual_backend = "rustworkx"
        except Exception as e:
            logger.error(f"Failed to find callees: {e}")
            result = []

        plan.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.query_history.append(plan)

        return result, plan

    async def find_all_paths(
        self, start: str, end: str, max_hops: int = 10
    ) -> Tuple[List[List[str]], QueryPlan]:
        """Find all call paths between two nodes."""
        plan = QueryComplexityDetector.analyze_query(
            "all_paths", start, max_hops=max_hops
        )

        start_time = datetime.now()

        # Use Memgraph for complex multi-hop queries
        if plan.recommended_backend == "memgraph" and self.memgraph:
            try:
                cypher = """
                MATCH path = (a:Function {id: $start})
                           -[:CALLS*1..$max_hops]->
                           (b:Function {id: $end})
                RETURN [node in nodes(path) | node.id] as path
                """
                result = await asyncio.to_thread(
                    self.memgraph.execute, cypher, start=start, end=end, max_hops=max_hops
                )
                paths = [r["path"] for r in result]
                plan.actual_backend = "memgraph"
            except Exception as e:
                logger.warning(f"Memgraph query failed: {e}, falling back to rustworkx")
                paths = self._find_paths_rustworkx(start, end, max_hops)
                plan.actual_backend = "rustworkx"
        else:
            paths = self._find_paths_rustworkx(start, end, max_hops)
            plan.actual_backend = "rustworkx"

        plan.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.query_history.append(plan)

        return paths, plan

    def _find_paths_rustworkx(
        self, start: str, end: str, max_length: int
    ) -> List[List[str]]:
        """Find paths using rustworkx (fallback)."""
        import networkx as nx

        # Convert rustworkx to networkx for path finding
        G = self.rustworkx_graph.graph.to_networkx()

        try:
            paths = list(nx.all_simple_paths(G, start, end, cutoff=max_length))
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    async def find_god_functions(
        self, min_complexity: int = 15, min_callers: int = 10
    ) -> Tuple[List[Dict[str, Any]], QueryPlan]:
        """Find high-complexity functions with many callers (refactoring targets)."""
        plan = QueryComplexityDetector.analyze_query(
            "god_functions", min_complexity=min_complexity, min_callers=min_callers
        )

        start_time = datetime.now()

        if self.memgraph:
            try:
                cypher = """
                MATCH (func:Function)
                WHERE func.complexity > $min_complexity
                WITH func, size((func)<-[:CALLS]-()) as caller_count
                WHERE caller_count > $min_callers
                RETURN {
                    id: func.id,
                    name: func.name,
                    complexity: func.complexity,
                    callers: caller_count
                } as result
                ORDER BY func.complexity DESC
                """
                results = await asyncio.to_thread(
                    self.memgraph.execute,
                    cypher,
                    min_complexity=min_complexity,
                    min_callers=min_callers,
                )
                functions = [r["result"] for r in results]
                plan.actual_backend = "memgraph"
            except Exception as e:
                logger.warning(f"Memgraph query failed: {e}")
                functions = []
                plan.actual_backend = "memgraph_failed"
        else:
            functions = []
            plan.actual_backend = "memgraph_unavailable"

        plan.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.query_history.append(plan)

        return functions, plan

    def get_query_performance(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        if not self.query_history:
            return {"message": "No queries executed yet"}

        rustworkx_queries = [q for q in self.query_history if q.actual_backend == "rustworkx"]
        memgraph_queries = [q for q in self.query_history if q.actual_backend == "memgraph"]

        stats = {
            "total_queries": len(self.query_history),
            "rustworkx": {
                "count": len(rustworkx_queries),
                "avg_time_ms": (
                    sum(q.execution_time_ms for q in rustworkx_queries)
                    / len(rustworkx_queries)
                    if rustworkx_queries
                    else 0
                ),
            },
            "memgraph": {
                "count": len(memgraph_queries),
                "avg_time_ms": (
                    sum(q.execution_time_ms for q in memgraph_queries)
                    / len(memgraph_queries)
                    if memgraph_queries
                    else 0
                ),
            },
        }

        return stats
