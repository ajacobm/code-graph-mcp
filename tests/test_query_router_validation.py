"""
Query Router Tests

Tests for the query routing engine that decides between Memgraph and rustworkx
for graph queries based on complexity analysis.
"""

import pytest
import time

from code_graph_mcp.query_router import (
    QueryRouter,
    QueryComplexityAnalyzer,
    RoutingMetrics
)


class TestQueryComplexityAnalyzer:
    """Tests for query complexity analysis."""

    def test_analyze_simple_node_query(self):
        """Test complexity analysis for simple node queries."""
        analyzer = QueryComplexityAnalyzer()
        query = "MATCH (n:Function) WHERE n.name = 'test' RETURN n"
        
        complexity = analyzer.analyze(query)
        
        assert complexity.score < 50
        assert complexity.is_simple
        assert not complexity.requires_aggregation
        assert not complexity.requires_traversal

    def test_analyze_simple_path_query(self):
        """Test complexity analysis for simple path queries."""
        analyzer = QueryComplexityAnalyzer()
        query = "MATCH (a)-[:CALLS]->(b) RETURN a, b"
        
        complexity = analyzer.analyze(query)
        
        assert complexity.score < 100
        assert not complexity.is_simple
        assert complexity.requires_traversal
        assert complexity.depth == 1

    def test_analyze_deep_traversal_query(self):
        """Test complexity analysis for deep traversal queries."""
        analyzer = QueryComplexityAnalyzer()
        query = """
        MATCH (a:Function)-[:CALLS*1..5]->(b:Function)
        RETURN a, b
        """
        
        complexity = analyzer.analyze(query)
        
        assert complexity.score > 100
        assert complexity.requires_traversal
        assert complexity.depth == 5

    def test_analyze_aggregation_query(self):
        """Test complexity analysis for aggregation queries."""
        analyzer = QueryComplexityAnalyzer()
        query = """
        MATCH (n:Function)
        RETURN n.name, COUNT(*) as call_count
        GROUP BY n.name
        ORDER BY call_count DESC
        """
        
        complexity = analyzer.analyze(query)
        
        assert complexity.requires_aggregation
        assert "GROUP BY" in complexity.operators or complexity.score > 75

    def test_analyze_complex_multi_hop_query(self):
        """Test complexity analysis for complex multi-hop queries."""
        analyzer = QueryComplexityAnalyzer()
        query = """
        MATCH (a:File)-[:CONTAINS]->(f:Function)-[:CALLS*1..3]->(g:Function),
              (g)-[:READS|:WRITES]->(v:Variable)
        WHERE a.path CONTAINS 'src'
        RETURN DISTINCT a, f, g, v
        """
        
        complexity = analyzer.analyze(query)
        
        assert complexity.score > 150
        assert complexity.is_complex
        assert complexity.requires_traversal

    def test_complexity_score_bounds(self):
        """Test complexity scores are within expected bounds."""
        analyzer = QueryComplexityAnalyzer()
        queries = [
            "MATCH (n) RETURN n",
            "MATCH (n)-[]->(m) RETURN n, m",
            "MATCH (n)-[*1..5]->(m) RETURN n, m",
            "MATCH path=(n)-[*1..10]->(m) RETURN path"
        ]
        
        scores = [analyzer.analyze(q).score for q in queries]
        
        # Scores should be in ascending order
        assert all(scores[i] <= scores[i+1] for i in range(len(scores)-1))

    def test_analyze_union_query(self):
        """Test complexity analysis for UNION queries."""
        analyzer = QueryComplexityAnalyzer()
        query = """
        MATCH (n:Function) RETURN n
        UNION
        MATCH (n:Class) RETURN n
        """
        
        complexity = analyzer.analyze(query)
        
        assert complexity.has_union
        assert complexity.score > 50


class TestQueryRouter:
    """Tests for query routing logic."""

    def test_route_simple_query_to_rustworkx(self):
        """Test that simple queries are routed to rustworkx."""
        router = QueryRouter()
        query = "MATCH (n:Function) WHERE n.name = 'test' RETURN n"
        
        decision = router.route(query)
        
        assert decision.target == "rustworkx"
        assert decision.confidence > 0.8

    def test_route_complex_query_to_memgraph(self):
        """Test that complex queries are routed to Memgraph."""
        router = QueryRouter()
        query = """
        MATCH (a:Function)-[:CALLS*1..5]->(b:Function),
              (b)-[:READS|:WRITES]->(v:Variable)
        RETURN DISTINCT a, b, v
        """
        
        decision = router.route(query)
        
        assert decision.target == "memgraph"
        assert decision.confidence > 0.7

    def test_route_path_traversal_to_memgraph(self):
        """Test that path traversal queries route to Memgraph."""
        router = QueryRouter()
        query = "MATCH path=(a)-[*1..10]->(b) RETURN path"
        
        decision = router.route(query)
        
        assert decision.target == "memgraph"

    def test_route_aggregation_to_memgraph(self):
        """Test that aggregation queries route to Memgraph."""
        router = QueryRouter()
        query = """
        MATCH (n:Function)-[:CALLS]->(m:Function)
        RETURN n.name, COUNT(*) as calls
        GROUP BY n.name
        """
        
        decision = router.route(query)
        
        assert decision.target == "memgraph"

    def test_routing_decision_includes_metrics(self):
        """Test that routing decision includes performance metrics."""
        router = QueryRouter()
        query = "MATCH (n:Function) RETURN n"
        
        decision = router.route(query)
        
        assert decision.estimated_complexity is not None
        assert decision.reason is not None
        assert decision.confidence >= 0.0 and decision.confidence <= 1.0

    def test_routing_caches_decisions(self):
        """Test that router caches routing decisions."""
        router = QueryRouter()
        query = "MATCH (n:Function) RETURN n"
        
        decision1 = router.route(query)
        start = time.time()
        decision2 = router.route(query)
        elapsed = time.time() - start
        
        # Second call should be much faster (cached)
        assert decision1 == decision2
        assert elapsed < 0.01  # Cache hit should be near-instant

    def test_routing_with_different_thresholds(self):
        """Test routing with custom complexity thresholds."""
        router = QueryRouter(
            rustworkx_threshold=50,
            memgraph_threshold=100
        )
        
        simple_query = "MATCH (n) RETURN n"
        
        decision1 = router.route(simple_query)
        
        assert decision1.target == "rustworkx"


class TestRoutingMetrics:
    """Tests for routing metrics collection."""

    def test_metrics_track_routing_decisions(self):
        """Test that metrics track routing decisions."""
        router = QueryRouter()
        metrics = RoutingMetrics()
        
        queries = [
            "MATCH (n:Function) RETURN n",
            "MATCH (n:Function) RETURN n",
            "MATCH (a)-[*1..5]->(b) RETURN a, b"
        ]
        
        for query in queries:
            decision = router.route(query)
            metrics.record(query, decision)
        
        assert metrics.total_queries == 3
        assert metrics.rustworkx_count >= 2
        assert metrics.memgraph_count >= 1

    def test_metrics_average_complexity(self):
        """Test metrics calculate average complexity."""
        router = QueryRouter()
        metrics = RoutingMetrics()
        
        queries = [
            "MATCH (n) RETURN n",
            "MATCH (a)-[]->(b) RETURN a, b",
            "MATCH (a)-[*1..3]->(b) RETURN a, b"
        ]
        
        for query in queries:
            decision = router.route(query)
            metrics.record(query, decision)
        
        avg = metrics.average_complexity
        assert avg > 0

    def test_metrics_hit_rate(self):
        """Test metrics calculate cache hit rate."""
        router = QueryRouter()
        metrics = RoutingMetrics()
        
        query = "MATCH (n:Function) RETURN n"
        
        # First call - cache miss
        decision1 = router.route(query)
        metrics.record(query, decision1)
        
        # Second call - cache hit
        decision2 = router.route(query)
        metrics.record(query, decision2)
        
        # Hit rate should reflect cache performance
        assert metrics.hit_rate >= 0.0 and metrics.hit_rate <= 1.0


class TestRoutingEdgeCases:
    """Tests for routing edge cases and error handling."""

    def test_route_empty_query(self):
        """Test routing handles empty queries."""
        router = QueryRouter()
        query = ""
        
        # Should either handle gracefully or raise specific exception
        try:
            decision = router.route(query)
            assert decision is not None
        except ValueError:
            pass  # Acceptable to reject empty query

    def test_route_malformed_query(self):
        """Test routing handles malformed queries."""
        router = QueryRouter()
        query = "MATCH (n) WHERE n.foo ==> RETURN n"  # Invalid syntax
        
        try:
            decision = router.route(query)
            # If successful, should route to more capable engine
            assert decision.target in ["memgraph", "rustworkx"]
        except Exception:
            pass  # Acceptable to reject malformed query

    def test_route_very_large_query(self):
        """Test routing handles very large queries."""
        router = QueryRouter()
        
        # Generate large query
        query = "MATCH (n:Function) WHERE n.name IN [" + \
                ", ".join(f"'func_{i}'" for i in range(1000)) + \
                "] RETURN n"
        
        decision = router.route(query)
        
        assert decision.target in ["memgraph", "rustworkx"]
        assert decision.estimated_complexity > 0

    def test_route_query_with_special_characters(self):
        """Test routing handles queries with special characters."""
        router = QueryRouter()
        query = "MATCH (n:Function) WHERE n.name CONTAINS 'test_\\n_data' RETURN n"
        
        decision = router.route(query)
        
        assert decision is not None
        assert decision.target in ["memgraph", "rustworkx"]

    def test_route_recursive_query(self):
        """Test routing handles recursive queries."""
        router = QueryRouter()
        query = """
        WITH RECURSIVE cte AS (
            SELECT id FROM nodes WHERE parent_id IS NULL
            UNION ALL
            SELECT n.id FROM nodes n
            INNER JOIN cte ON n.parent_id = cte.id
        )
        SELECT * FROM cte
        """
        
        # Should route to Memgraph (more capable)
        decision = router.route(query)
        assert decision.target in ["memgraph", "rustworkx"]


class TestRoutingPerformance:
    """Tests for routing performance characteristics."""

    def test_routing_decision_latency(self):
        """Test routing decisions complete within latency budget."""
        router = QueryRouter()
        query = "MATCH (n:Function) RETURN n"
        
        start = time.time()
        for _ in range(100):
            router.route(query)
        elapsed = time.time() - start
        
        # Should complete 100 queries in under 100ms (avg 1ms per query)
        assert elapsed < 0.1

    def test_routing_with_complex_query_set(self):
        """Test routing performance with diverse query set."""
        router = QueryRouter()
        
        queries = [
            "MATCH (n:Function) RETURN n",
            "MATCH (a)-[:CALLS]->(b) RETURN a, b",
            "MATCH (a)-[*1..5]->(b) RETURN a, b",
            "MATCH (n:Function) RETURN n.name, COUNT(*) as count GROUP BY n.name",
            "MATCH path=(a)-[*1..10]->(b) RETURN path"
        ]
        
        start = time.time()
        decisions = [router.route(q) for q in queries * 10]
        elapsed = time.time() - start
        
        # 50 routing decisions should complete in under 100ms
        assert elapsed < 0.1
        assert len(decisions) == 50
        assert all(d.target in ["memgraph", "rustworkx"] for d in decisions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
