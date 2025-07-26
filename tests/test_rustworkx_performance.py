#!/usr/bin/env python3
"""
Performance benchmarks for RustworkxCodeGraph functionality.

This module provides benchmarks to demonstrate the performance improvements
offered by the rustworkx-backed graph implementation.
"""

import time
import pytest
from typing import List, Dict, Any

from code_graph_mcp.rustworkx_graph import RustworkxCodeGraph
from code_graph_mcp.universal_graph import (
    UniversalNode, UniversalRelationship, UniversalLocation,
    NodeType, RelationshipType
)


class PerformanceBenchmarks:
    """Performance benchmarks for rustworkx functionality."""

    def create_large_graph(self, num_nodes: int = 1000, connectivity: float = 0.3) -> RustworkxCodeGraph:
        """Create a large graph for performance testing."""
        graph = RustworkxCodeGraph()
        
        print(f"Creating graph with {num_nodes} nodes...")
        
        # Create nodes
        start_time = time.time()
        nodes = []
        for i in range(num_nodes):
            node = UniversalNode(
                id=f"node_{i}",
                name=f"Function_{i}",
                node_type=NodeType.FUNCTION if i % 4 != 0 else NodeType.CLASS,
                location=UniversalLocation(
                    file_path=f"/test/file_{i // 50}.py",
                    start_line=10 + (i % 100),
                    end_line=20 + (i % 100),
                    language="Python"
                ),
                language="Python",
                complexity=(i % 20) + 1,
                metadata={"module": f"module_{i // 100}"}
            )
            nodes.append(node)
            graph.add_node(node)
        
        node_creation_time = time.time() - start_time
        print(f"Node creation took: {node_creation_time:.3f}s")
        
        # Create relationships based on connectivity
        start_time = time.time()
        import random
        relationships = []
        num_relationships = int(num_nodes * connectivity)
        
        for i in range(num_relationships):
            source_idx = random.randint(0, num_nodes - 1)
            target_idx = random.randint(0, num_nodes - 1)
            
            if source_idx != target_idx:  # Avoid self-loops
                rel_type = random.choice([
                    RelationshipType.CALLS,
                    RelationshipType.REFERENCES,
                    RelationshipType.CONTAINS
                ])
                
                rel = UniversalRelationship(
                    id=f"rel_{i}_{source_idx}_{target_idx}",
                    source_id=f"node_{source_idx}",
                    target_id=f"node_{target_idx}",
                    relationship_type=rel_type,
                    strength=random.uniform(0.1, 1.0)
                )
                relationships.append(rel)
                graph.add_relationship(rel)
        
        relationship_creation_time = time.time() - start_time
        print(f"Relationship creation took: {relationship_creation_time:.3f}s")
        print(f"Created {len(relationships)} relationships")
        
        return graph

    def benchmark_centrality_algorithms(self, graph: RustworkxCodeGraph) -> Dict[str, float]:
        """Benchmark centrality calculation algorithms."""
        print("\\n=== Centrality Algorithm Benchmarks ===")
        results = {}
        
        # Betweenness centrality
        start_time = time.time()
        betweenness = graph.calculate_centrality()
        betweenness_time = time.time() - start_time
        results['betweenness'] = betweenness_time
        print(f"Betweenness centrality: {betweenness_time:.3f}s ({len(betweenness)} nodes)")
        
        # PageRank
        start_time = time.time()
        pagerank = graph.calculate_pagerank(alpha=0.85, max_iter=100, tol=1e-6)
        pagerank_time = time.time() - start_time
        results['pagerank'] = pagerank_time
        print(f"PageRank: {pagerank_time:.3f}s ({len(pagerank)} nodes)")
        
        # Closeness centrality
        start_time = time.time()
        closeness = graph.calculate_closeness_centrality()
        closeness_time = time.time() - start_time
        results['closeness'] = closeness_time
        print(f"Closeness centrality: {closeness_time:.3f}s ({len(closeness)} nodes)")
        
        # Eigenvector centrality
        start_time = time.time()
        eigenvector = graph.calculate_eigenvector_centrality(max_iter=100)
        eigenvector_time = time.time() - start_time
        results['eigenvector'] = eigenvector_time
        print(f"Eigenvector centrality: {eigenvector_time:.3f}s ({len(eigenvector)} nodes)")
        
        return results

    def benchmark_structural_analysis(self, graph: RustworkxCodeGraph) -> Dict[str, float]:
        """Benchmark structural analysis algorithms."""
        print("\\n=== Structural Analysis Benchmarks ===")
        results = {}
        
        # Cycle detection
        start_time = time.time()
        cycles = graph.detect_cycles()
        cycle_time = time.time() - start_time
        results['cycles'] = cycle_time
        print(f"Cycle detection: {cycle_time:.3f}s ({len(cycles)} cycles found)")
        
        # Strongly connected components
        start_time = time.time()
        components = graph.get_strongly_connected_components()
        scc_time = time.time() - start_time
        results['scc'] = scc_time
        print(f"Strongly connected components: {scc_time:.3f}s ({len(components)} components)")
        
        # Articulation points
        start_time = time.time()
        articulation_points = graph.find_articulation_points()
        articulation_time = time.time() - start_time
        results['articulation'] = articulation_time
        print(f"Articulation points: {articulation_time:.3f}s ({len(articulation_points)} points)")
        
        # Bridges
        start_time = time.time()
        bridges = graph.find_bridges()
        bridges_time = time.time() - start_time
        results['bridges'] = bridges_time
        print(f"Bridge finding: {bridges_time:.3f}s ({len(bridges)} bridges)")
        
        # DAG check
        start_time = time.time()
        is_dag = graph.is_directed_acyclic()
        dag_time = time.time() - start_time
        results['dag'] = dag_time
        print(f"DAG check: {dag_time:.3f}s (Result: {is_dag})")
        
        return results

    def benchmark_path_algorithms(self, graph: RustworkxCodeGraph, sample_nodes: List[str]) -> Dict[str, float]:
        """Benchmark shortest path algorithms."""
        print("\\n=== Path Algorithm Benchmarks ===")
        results = {}
        
        if len(sample_nodes) < 2:
            print("Not enough nodes for path benchmarks")
            return results
        
        source, target = sample_nodes[0], sample_nodes[1]
        
        # Shortest path
        start_time = time.time()
        shortest_path = graph.find_shortest_path(source, target)
        shortest_path_time = time.time() - start_time
        results['shortest_path'] = shortest_path_time
        print(f"Shortest path: {shortest_path_time:.3f}s (Length: {len(shortest_path)})")
        
        # All paths (limited)
        start_time = time.time()
        all_paths = graph.find_all_paths(source, target, max_length=5)
        all_paths_time = time.time() - start_time
        results['all_paths'] = all_paths_time
        print(f"All paths (max 5): {all_paths_time:.3f}s ({len(all_paths)} paths)")
        
        # Distance matrix (Floyd-Warshall) - only for smaller graphs
        if len(graph.nodes) <= 200:  # Limit to avoid excessive computation
            start_time = time.time()
            distance_matrix = graph.calculate_graph_distance_matrix()
            distance_matrix_time = time.time() - start_time
            results['distance_matrix'] = distance_matrix_time
            total_distances = sum(len(targets) for targets in distance_matrix.values())
            print(f"Distance matrix: {distance_matrix_time:.3f}s ({total_distances} distances)")
        
        # Bellman-Ford path lengths
        start_time = time.time()
        bellman_ford = graph.calculate_bellman_ford_path_lengths()
        bellman_ford_time = time.time() - start_time
        results['bellman_ford'] = bellman_ford_time
        total_bf_distances = sum(len(targets) for targets in bellman_ford.values())
        print(f"Bellman-Ford paths: {bellman_ford_time:.3f}s ({total_bf_distances} distances)")
        
        return results

    def benchmark_traversal_algorithms(self, graph: RustworkxCodeGraph, sample_nodes: List[str]) -> Dict[str, float]:
        """Benchmark graph traversal algorithms."""
        print("\\n=== Traversal Algorithm Benchmarks ===")
        results = {}
        
        if not sample_nodes:
            print("No nodes for traversal benchmarks")
            return results
        
        source = sample_nodes[0]
        
        # DFS
        start_time = time.time()
        dfs_nodes = graph.depth_first_search(source)
        dfs_time = time.time() - start_time
        results['dfs'] = dfs_time
        print(f"DFS traversal: {dfs_time:.3f}s ({len(dfs_nodes)} nodes visited)")
        
        # BFS
        start_time = time.time()
        bfs_nodes = graph.breadth_first_search(source)
        bfs_time = time.time() - start_time
        results['bfs'] = bfs_time
        print(f"BFS traversal: {bfs_time:.3f}s ({len(bfs_nodes)} nodes visited)")
        
        # Node layers
        start_time = time.time()
        layers = graph.find_node_layers(source)
        layers_time = time.time() - start_time
        results['layers'] = layers_time
        total_nodes_in_layers = sum(len(nodes) for nodes in layers.values())
        print(f"Node layers: {layers_time:.3f}s ({len(layers)} layers, {total_nodes_in_layers} nodes)")
        
        return results

    def benchmark_serialization(self, graph: RustworkxCodeGraph) -> Dict[str, float]:
        """Benchmark serialization methods."""
        print("\\n=== Serialization Benchmarks ===")
        results = {}
        
        # JSON serialization
        start_time = time.time()
        json_data = graph.to_json()
        json_time = time.time() - start_time
        results['json'] = json_time
        print(f"JSON serialization: {json_time:.3f}s ({len(json_data)} characters)")
        
        # DOT serialization
        start_time = time.time()
        dot_data = graph.to_dot()
        dot_time = time.time() - start_time
        results['dot'] = dot_time
        print(f"DOT serialization: {dot_time:.3f}s ({len(dot_data)} characters)")
        
        # Statistics generation
        start_time = time.time()
        stats = graph.get_statistics()
        stats_time = time.time() - start_time
        results['statistics'] = stats_time
        print(f"Statistics generation: {stats_time:.3f}s")
        
        return results

    def run_comprehensive_benchmark(self, num_nodes: int = 500):
        """Run comprehensive performance benchmarks."""
        print(f"\\n{'='*60}")
        print(f"RUSTWORKX CODE GRAPH PERFORMANCE BENCHMARK")
        print(f"Graph size: {num_nodes} nodes")
        print(f"{'='*60}")
        
        # Create test graph
        total_start_time = time.time()
        graph = self.create_large_graph(num_nodes, connectivity=0.3)
        
        # Get sample nodes for path testing
        sample_nodes = list(graph.nodes.keys())[:10]
        
        # Run benchmarks
        benchmark_results = {}
        benchmark_results['centrality'] = self.benchmark_centrality_algorithms(graph)
        benchmark_results['structural'] = self.benchmark_structural_analysis(graph)
        benchmark_results['paths'] = self.benchmark_path_algorithms(graph, sample_nodes)
        benchmark_results['traversal'] = self.benchmark_traversal_algorithms(graph, sample_nodes)
        benchmark_results['serialization'] = self.benchmark_serialization(graph)
        
        total_time = time.time() - total_start_time
        
        # Summary
        print("\\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        print(f"Total benchmark time: {total_time:.3f}s")
        print(f"Graph statistics:")
        stats = graph.get_statistics()
        print(f"  - Nodes: {stats['total_nodes']}")
        print(f"  - Relationships: {stats['total_relationships']}")
        print(f"  - Density: {stats['density']:.4f}")
        print(f"  - Average degree: {stats['average_degree']:.2f}")
        
        # Performance highlights
        print("\\nPerformance highlights:")
        if 'pagerank' in benchmark_results['centrality']:
            pagerank_time = benchmark_results['centrality']['pagerank']
            nodes_per_sec = stats['total_nodes'] / pagerank_time if pagerank_time > 0 else 0
            print(f"  - PageRank: {nodes_per_sec:.0f} nodes/second")
        
        if 'betweenness' in benchmark_results['centrality']:
            betweenness_time = benchmark_results['centrality']['betweenness']
            nodes_per_sec = stats['total_nodes'] / betweenness_time if betweenness_time > 0 else 0
            print(f"  - Betweenness centrality: {nodes_per_sec:.0f} nodes/second")
        
        if 'cycles' in benchmark_results['structural']:
            cycles_time = benchmark_results['structural']['cycles']
            edges_per_sec = stats['total_relationships'] / cycles_time if cycles_time > 0 else 0
            print(f"  - Cycle detection: {edges_per_sec:.0f} edges/second")
        
        return benchmark_results


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Test class for performance benchmarks."""
    
    def test_small_graph_performance(self):
        """Test performance with a small graph (fast test)."""
        benchmarks = PerformanceBenchmarks()
        results = benchmarks.run_comprehensive_benchmark(num_nodes=100)
        
        # Basic assertions that operations completed
        assert 'centrality' in results
        assert 'structural' in results
        assert 'serialization' in results
        
    @pytest.mark.slow
    def test_medium_graph_performance(self):
        """Test performance with a medium graph (slower test)."""
        benchmarks = PerformanceBenchmarks()
        results = benchmarks.run_comprehensive_benchmark(num_nodes=500)
        
        # Verify all benchmark categories completed
        expected_categories = ['centrality', 'structural', 'paths', 'traversal', 'serialization']
        for category in expected_categories:
            assert category in results
    
    @pytest.mark.slow
    def test_large_graph_performance(self):
        """Test performance with a large graph (very slow test)."""
        benchmarks = PerformanceBenchmarks()
        results = benchmarks.run_comprehensive_benchmark(num_nodes=1000)
        
        # Verify operations scale reasonably
        assert 'centrality' in results
        
        # PageRank should complete in reasonable time even for large graphs
        if 'pagerank' in results['centrality']:
            assert results['centrality']['pagerank'] < 10.0  # Should complete in under 10 seconds
    
    def test_connectivity_analysis_performance(self):
        """Test performance of connectivity analysis features."""
        benchmarks = PerformanceBenchmarks()
        graph = benchmarks.create_large_graph(num_nodes=200, connectivity=0.4)
        
        # Test comprehensive connectivity analysis
        start_time = time.time()
        connectivity = graph.analyze_graph_connectivity()
        analysis_time = time.time() - start_time
        
        print(f"\\nConnectivity analysis took: {analysis_time:.3f}s")
        
        # Verify analysis completed and has expected structure
        assert 'basic_metrics' in connectivity
        assert 'connectivity_metrics' in connectivity
        assert 'distance_metrics' in connectivity
        
        # Should complete in reasonable time
        assert analysis_time < 30.0  # Should complete in under 30 seconds


if __name__ == "__main__":
    # Run benchmarks directly
    benchmarks = PerformanceBenchmarks()
    
    print("Running performance benchmarks...")
    print("Note: This will take several minutes to complete.")
    
    # Run different sized benchmarks
    for size in [100, 200, 500]:
        print(f"\\n{'='*80}")
        print(f"RUNNING BENCHMARK FOR {size} NODES")
        print(f"{'='*80}")
        benchmarks.run_comprehensive_benchmark(num_nodes=size)
        print("\\n" + "="*80)