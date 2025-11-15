"""Query Router - Intelligent Query Routing Between Memgraph and Rustworkx

Routes graph queries to the most appropriate backend based on complexity analysis.
- Simple queries → rustworkx (Python graph library, fast for small graphs)
- Complex queries → Memgraph (scalable graph database with query optimization)
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class RoutingTarget(str, Enum):
    """Available routing targets."""

    RUSTWORKX = "rustworkx"
    MEMGRAPH = "memgraph"


@dataclass
class QueryComplexity:
    """Analysis result for query complexity."""

    score: int
    is_simple: bool
    is_complex: bool
    requires_traversal: bool
    requires_aggregation: bool
    has_union: bool
    depth: int = 0
    operators: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate and normalize complexity."""
        if not self.operators:
            self.operators = []


@dataclass
class RoutingDecision:
    """Decision result for query routing."""

    target: RoutingTarget
    confidence: float
    estimated_complexity: int
    reason: str
    cached: bool = False


@dataclass
class RoutingMetrics:
    """Metrics tracking for routing decisions."""

    total_queries: int = 0
    rustworkx_count: int = 0
    memgraph_count: int = 0
    hit_rate: float = 0.0
    average_complexity: float = 0.0
    _complexities: List[int] = field(default_factory=list)

    def record(self, query: str, decision: RoutingDecision) -> None:
        """Record routing decision."""
        self.total_queries += 1

        if decision.target == RoutingTarget.RUSTWORKX:
            self.rustworkx_count += 1
        else:
            self.memgraph_count += 1

        self._complexities.append(decision.estimated_complexity)
        self.average_complexity = (
            sum(self._complexities) / len(self._complexities) if self._complexities else 0
        )


class QueryComplexityAnalyzer:
    """Analyzes Cypher query complexity."""

    SIMPLE_THRESHOLD = 50
    COMPLEX_THRESHOLD = 150

    def analyze(self, query: str) -> QueryComplexity:
        """Analyze query complexity."""
        score = 0
        operators = []

        # Parse query structure
        query_upper = query.upper()

        # Count MATCH clauses (each hop adds complexity)
        match_count = len(re.findall(r'\bMATCH\b', query_upper))
        score += match_count * 20

        # Variable-length paths (traversal) - handles [:TYPE*1..5] format
        has_var_length = bool(re.search(r'\[[^\]]*\*\d+\.\.\d+[^\]]*\]', query))
        if has_var_length:
            score += 80
            operators.append("VARIABLE_LENGTH_PATH")

        # Get traversal depth
        depth = self._extract_depth(query)
        if depth > 0:
            score += depth * 30

        # Edge traversal (any arrow or bracket relationship) adds base score
        has_any_traversal = bool(re.search(r'-\[.*?\]-', query))
        if has_any_traversal:
            # Single or multi-hop edges always add traversal complexity
            score += 40
            operators.append("EDGE_TRAVERSAL")

        # Aggregation functions and GROUP BY
        has_group_by = "GROUP BY" in query_upper
        agg_funcs = ["COUNT", "SUM", "AVG", "MIN", "MAX", "COLLECT"]
        has_aggregation = has_group_by or any(func in query_upper for func in agg_funcs)
        if has_aggregation:
            score += 50
            if has_group_by:
                operators.append("GROUP BY")
            else:
                operators.append("AGGREGATION")

        # UNION queries
        has_union = "UNION" in query_upper
        if has_union:
            score += 40
            operators.append("UNION")

        # WHERE clause complexity
        where_conditions = len(re.findall(r'\bAND\b|\bOR\b', query_upper))
        score += where_conditions * 8

        # ORDER BY, SKIP, LIMIT
        if "ORDER BY" in query_upper:
            score += 15
            operators.append("ORDER_BY")
        if "SKIP" in query_upper or "LIMIT" in query_upper:
            score += 10
            operators.append("LIMIT")

        # RETURN complexity
        return_clause = self._extract_return_clause(query)
        if return_clause:
            if "DISTINCT" in return_clause.upper():
                score += 20
                operators.append("DISTINCT")

        is_simple = score < self.SIMPLE_THRESHOLD
        is_complex = score >= self.COMPLEX_THRESHOLD

        return QueryComplexity(
            score=score,
            is_simple=is_simple,
            is_complex=is_complex,
            requires_traversal=has_var_length or has_any_traversal,
            requires_aggregation=has_aggregation,
            has_union=has_union,
            depth=depth,
            operators=operators,
        )

    def _extract_depth(self, query: str) -> int:
        """Extract traversal depth from query."""
        # Look for variable-length paths like [:CALLS*1..5]
        match = re.search(r'\[[^\]]*\*\d+\.\.(\d+)[^\]]*\]', query)
        if match:
            return int(match.group(1))

        # Count arrows in path as proxy for depth
        # Each arrow represents one hop in the path
        arrows = len(re.findall(r'-\[.*?\]->', query))
        if arrows > 0:
            return arrows
        # Also check for undirected edges
        undirected = len(re.findall(r'-\[.*?\]-', query))
        return undirected

    def _extract_return_clause(self, query: str) -> Optional[str]:
        """Extract RETURN clause from query."""
        match = re.search(r'RETURN\s+(.+?)(?:ORDER|SKIP|LIMIT|$)', query, re.IGNORECASE)
        return match.group(1) if match else None


class QueryRouter:
    """Routes queries to appropriate backend."""

    def __init__(
        self,
        rustworkx_threshold: int = 50,
        memgraph_threshold: int = 150,
    ):
        self.rustworkx_threshold = rustworkx_threshold
        self.memgraph_threshold = memgraph_threshold
        self.analyzer = QueryComplexityAnalyzer()
        self._cache: Dict[str, RoutingDecision] = {}

    def route(self, query: str) -> RoutingDecision:
        """Route query to appropriate backend."""
        # Check cache
        if query in self._cache:
            cached_decision = self._cache[query]
            cached_decision.cached = True
            return cached_decision

        # Analyze complexity
        complexity = self.analyzer.analyze(query)

        # Make routing decision
        if complexity.score < self.rustworkx_threshold:
            target = RoutingTarget.RUSTWORKX
            confidence = 0.95 if complexity.is_simple else 0.8
            reason = "Simple query, rustworkx sufficient"
        elif complexity.score >= self.memgraph_threshold:
            target = RoutingTarget.MEMGRAPH
            confidence = 0.95
            reason = "Complex query requires Memgraph"
        else:
            # Moderate complexity - prefer Memgraph for safety
            target = RoutingTarget.MEMGRAPH
            confidence = 0.7
            reason = "Moderate complexity, routing to Memgraph for optimization"

        decision = RoutingDecision(
            target=target,
            confidence=confidence,
            estimated_complexity=complexity.score,
            reason=reason,
            cached=False,
        )

        # Cache decision
        self._cache[query] = decision

        return decision


class QueryRouterManager:
    """Manages query routing with metrics collection."""

    def __init__(
        self,
        rustworkx_threshold: int = 50,
        memgraph_threshold: int = 150,
    ):
        self.router = QueryRouter(rustworkx_threshold, memgraph_threshold)
        self.metrics = RoutingMetrics()

    def route(self, query: str) -> RoutingDecision:
        """Route query and collect metrics."""
        decision = self.router.route(query)
        self.metrics.record(query, decision)
        return decision

    def get_metrics(self) -> RoutingMetrics:
        """Get routing metrics."""
        return self.metrics

    def clear_metrics(self) -> None:
        """Clear metrics."""
        self.metrics = RoutingMetrics()
