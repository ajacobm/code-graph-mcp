"""
Advanced Graph Algorithms for RustworkX Code Graph

Provides sophisticated graph analysis algorithms including:
- Centrality measures (betweenness, pagerank, closeness, eigenvector)
- Path finding and traversal algorithms
- Cycle detection and topological analysis
- Connectivity and structural analysis
"""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

import rustworkx as rx

from ..universal_graph import (
    UniversalNode,
    UniversalRelationship,
    NodeType,
    RelationshipType,
    CacheConfig
)

logger = logging.getLogger(__name__)


class GraphAlgorithmsMixin:
    """
    Mixin class providing advanced graph algorithms for RustworkX code graphs.
    
    Provides:
    - Centrality analysis
    - Path finding algorithms  
    - Cycle detection
    - Connectivity analysis
    - Traversal algorithms
    """

    def find_shortest_path(self, source_id: str, target_id: str) -> List[str]:
        """Find shortest path between two nodes."""
        with self._lock:
            source_node = self.nodes.get(source_id)
            target_node = self.nodes.get(target_id)

            if not source_node or not target_node:
                return []

            source_index = getattr(source_node, '_rustworkx_index', None)
            target_index = getattr(target_node, '_rustworkx_index', None)

            if source_index is None or target_index is None:
                return []

            try:
                # Use dijkstra shortest path
                path_indices = rx.dijkstra_shortest_paths(
                    self.graph, source_index, target_index, lambda _: 1
                )
                if path_indices and target_index in path_indices:
                    # Convert indices to node IDs using graph data
                    return [self.graph[idx] for idx in path_indices[target_index] if idx < len(self.graph)]
                return []
            except Exception:
                return []

    def find_all_paths(self, source_id: str, target_id: str, max_length: int = 10) -> List[List[str]]:
        """Find all paths between two nodes up to max_length."""
        with self._lock:
            source_node = self.nodes.get(source_id)
            target_node = self.nodes.get(target_id)

            if not source_node or not target_node:
                return []

            source_index = getattr(source_node, '_rustworkx_index', None)
            target_index = getattr(target_node, '_rustworkx_index', None)

            if source_index is None or target_index is None:
                return []

            try:
                paths = rx.all_simple_paths(self.graph, source_index, target_index, min_depth=1, cutoff=max_length)
                # Convert indices to node IDs using graph data
                return [[self.graph[idx] for idx in path if idx < len(self.graph)] for path in paths]
            except Exception:
                return []

    def detect_cycles(self) -> List[List[str]]:
        """Detect meaningful cycles in the code graph, filtering out legitimate recursion."""
        with self._lock:
            try:
                # Get all cycles from rustworkx
                all_cycles = list(rx.simple_cycles(self.graph))
                meaningful_cycles = []

                for cycle in all_cycles:
                    # Filter out single-node cycles (self-loops) which are often legitimate recursion
                    if len(cycle) == 1:
                        node_index = cycle[0]
                        node_id = self.graph[node_index]  # Get node ID from graph data
                        node = self.nodes.get(node_id)

                        if node and self._is_legitimate_recursion(node):
                            continue  # Skip legitimate recursive functions

                    # Convert indices to node IDs using graph data (no mapping corruption)
                    cycle_node_ids = []
                    for idx in cycle:
                        node_id = self.graph[idx]  # Get node ID from graph data
                        if node_id:
                            cycle_node_ids.append(node_id)

                    if len(cycle_node_ids) > 1:  # Only report multi-node cycles
                        meaningful_cycles.append(cycle_node_ids)

                return meaningful_cycles

            except Exception as e:
                logger.error(f"Cycle detection failed: {e}")
                return []

    def _is_legitimate_recursion(self, node: UniversalNode) -> bool:
        """Check if a self-loop represents legitimate recursion rather than a circular dependency."""
        # Recursive functions are legitimate if they:
        # 1. Are actual functions (not modules/classes)
        # 2. Have recursive patterns in their name or are common recursive algorithms
        if node.node_type != NodeType.FUNCTION:
            return False

        # Common recursive function patterns
        recursive_patterns = [
            'recursive', 'recurse', 'factorial', 'fibonacci', 'traverse',
            'walk', 'visit', 'search', 'sort', 'merge', 'quick', 'binary'
        ]

        node_name_lower = node.name.lower()
        return any(pattern in node_name_lower for pattern in recursive_patterns)

    def get_strongly_connected_components(self) -> List[List[str]]:
        """Find strongly connected components (circular dependency groups)."""
        with self._lock:
            try:
                components = rx.strongly_connected_components(self.graph)
                # Convert indices to node IDs using graph data
                result = []
                for component in components:
                    component_ids = []
                    for idx in component:
                        if idx < len(self.graph):
                            node_id = self.graph[idx]
                            if node_id:
                                component_ids.append(node_id)
                    if component_ids:
                        result.append(component_ids)
                return result
            except Exception as e:
                logger.error(f"Strongly connected components calculation failed: {e}")
                return []

    @lru_cache(maxsize=CacheConfig.SMALL_CACHE)
    def calculate_centrality(self) -> Dict[str, float]:
        """Calculate betweenness centrality with LRU caching for performance."""
        with self._lock:
            try:
                # Use the correct API for directed graphs
                centrality = rx.digraph_betweenness_centrality(self.graph)
                # Convert indices to node IDs using graph data
                result = {}
                for idx, score in centrality.items():
                    if idx < len(self.graph):
                        node_id = self.graph[idx]
                        if node_id:
                            result[node_id] = score
                return result
            except Exception as e:
                logger.error(f"Centrality calculation failed: {e}")
                return {}

    @lru_cache(maxsize=CacheConfig.MEDIUM_CACHE)
    def calculate_pagerank(self, alpha: float = 0.85, max_iter: int = 100, tol: float = 1e-6) -> Dict[str, float]:
        """Calculate PageRank with LRU caching for optimal performance."""
        with self._lock:
            try:
                # Use optimized PageRank with configurable damping factor and convergence
                pagerank_scores = rx.pagerank(
                    self.graph,
                    alpha=alpha,        # Damping factor (0.85 is standard)
                    max_iter=max_iter,  # Maximum iterations for convergence
                    tol=tol            # Convergence tolerance
                )
                # Convert indices to node IDs using graph data
                result = {}
                for idx, score in pagerank_scores.items():
                    if idx < len(self.graph):
                        node_id = self.graph[idx]
                        if node_id:
                            result[node_id] = score
                return result
            except rx.FailedToConverge as e:
                logger.warning(f"PageRank failed to converge: {e}")
                return {}
            except Exception as e:
                logger.error(f"PageRank calculation failed: {e}")
                return {}

    def find_ancestors(self, node_id: str) -> Set[str]:
        """Find all nodes that can reach this node."""
        with self._lock:
            node = self.nodes.get(node_id)
            if not node or not hasattr(node, '_rustworkx_index'):
                return set()

            try:
                ancestor_indices = rx.ancestors(self.graph, node._rustworkx_index)
                result = set()
                for idx in ancestor_indices:
                    if idx < len(self.graph):
                        ancestor_id = self.graph[idx]
                        if ancestor_id:
                            result.add(ancestor_id)
                return result
            except Exception:
                return set()

    def find_descendants(self, node_id: str) -> Set[str]:
        """Find all nodes reachable from this node."""
        with self._lock:
            node = self.nodes.get(node_id)
            if not node or not hasattr(node, '_rustworkx_index'):
                return set()

            try:
                descendant_indices = rx.descendants(self.graph, node._rustworkx_index)
                result = set()
                for idx in descendant_indices:
                    if idx < len(self.graph):
                        descendant_id = self.graph[idx]
                        if descendant_id:
                            result.add(descendant_id)
                return result
            except Exception:
                return set()

    def get_node_degree(self, node_id: str) -> Tuple[int, int, int]:
        """Get node degree (in_degree, out_degree, total_degree)."""
        with self._lock:
            node = self.nodes.get(node_id)
            if not node or not hasattr(node, '_rustworkx_index'):
                return (0, 0, 0)

            try:
                in_degree = self.graph.in_degree(node._rustworkx_index)
                out_degree = self.graph.out_degree(node._rustworkx_index)
                total_degree = in_degree + out_degree
                return (in_degree, out_degree, total_degree)
            except Exception:
                return (0, 0, 0)

    def is_directed_acyclic(self) -> bool:
        """Check if the graph is a DAG (no circular dependencies)."""
        return rx.is_directed_acyclic_graph(self.graph)

    def topological_sort(self) -> List[str]:
        """Get topological ordering of nodes (dependency order)."""
        with self._lock:
            try:
                sorted_indices = rx.topological_sort(self.graph)
                result = []
                for idx in sorted_indices:
                    if idx < len(self.graph):
                        node_id = self.graph[idx]
                        if node_id:
                            result.append(node_id)
                return result
            except Exception:
                return []

    @lru_cache(maxsize=CacheConfig.SMALL_CACHE)
    def calculate_closeness_centrality(self) -> Dict[str, float]:
        """Calculate closeness centrality with LRU caching."""
        with self._lock:
            try:
                centrality = rx.closeness_centrality(self.graph)
                result = {}
                for idx, score in centrality.items():
                    if idx < len(self.graph):
                        node_id = self.graph[idx]
                        if node_id:
                            result[node_id] = score
                return result
            except Exception as e:
                logger.warning(f"Closeness centrality calculation failed: {e}")
                return {}

    @lru_cache(maxsize=CacheConfig.LARGE_CACHE)
    def calculate_eigenvector_centrality(self, max_iter: int = 100, tol: float = 1e-6) -> Dict[str, float]:
        """Calculate eigenvector centrality with LRU caching."""
        with self._lock:
            try:
                centrality = rx.eigenvector_centrality(self.graph, max_iter=max_iter, tol=tol)
                result = {}
                for idx, score in centrality.items():
                    if idx < len(self.graph):
                        node_id = self.graph[idx]
                        if node_id:
                            result[node_id] = score
                return result
            except Exception as e:
                logger.warning(f"Eigenvector centrality calculation failed: {e}")
                return {}

    def find_articulation_points(self) -> List[str]:
        """Find articulation points (nodes whose removal increases connected components)."""
        with self._lock:
            try:
                # Convert to undirected for articulation point analysis
                undirected = self.graph.to_undirected()
                articulation_indices = rx.articulation_points(undirected)
                result = []
                for idx in articulation_indices:
                    if idx < len(self.graph):
                        node_id = self.graph[idx]
                        if node_id:
                            result.append(node_id)
                return result
            except Exception as e:
                logger.warning(f"Articulation points calculation failed: {e}")
                return []

    def find_bridges(self) -> List[tuple]:
        """Find bridge edges (edges whose removal increases connected components)."""
        try:
            # Convert to undirected for bridge analysis
            undirected = self.graph.to_undirected()
            bridge_edges = rx.bridges(undirected)
            bridges = []
            for edge in bridge_edges:
                if len(edge) >= 2:  # Ensure edge has at least 2 elements
                    source_id = self.graph[edge[0]]  # Get node ID from graph data
                    target_id = self.graph[edge[1]]  # Get node ID from graph data
                    if source_id and target_id:
                        bridges.append((source_id, target_id))
            return bridges
        except Exception as e:
            logger.warning(f"Bridge calculation failed: {e}")
            return []

    def calculate_graph_distance_matrix(self) -> Dict[str, Dict[str, float]]:
        """Calculate shortest path distances between all pairs of nodes using Floyd-Warshall."""
        try:
            distance_matrix = rx.floyd_warshall_numpy(self.graph)
            result = {}
            # Iterate through all node indices in the graph
            for i in range(len(self.graph)):
                source_id = self.graph[i]  # Get node ID from graph data
                if source_id:
                    result[source_id] = {}
                    for j in range(len(self.graph)):
                        target_id = self.graph[j]  # Get node ID from graph data
                        if target_id and i < len(distance_matrix) and j < len(distance_matrix[i]):
                            distance = distance_matrix[i][j]
                            if distance != float('inf'):
                                result[source_id][target_id] = distance
            return result
        except Exception as e:
            logger.warning(f"Distance matrix calculation failed: {e}")
            return {}

    def calculate_bellman_ford_path_lengths(self, weight_fn=None) -> Dict[str, Dict[str, float]]:
        """
        Calculate all-pairs shortest path lengths using Bellman-Ford algorithm.
        Superior to Floyd-Warshall for sparse graphs and can handle negative weights.
        """
        try:
            # Use Bellman-Ford for all pairs shortest path lengths
            edge_cost_fn = weight_fn if weight_fn else lambda _: 1
            paths_result = rx.all_pairs_bellman_ford_path_lengths(self.graph, edge_cost_fn)

            result = {}
            for source_idx, target_distances in paths_result.items():
                source_id = self.graph[source_idx]  # Get node ID from graph data
                if source_id:
                    result[source_id] = {}

                    # Convert target indices to node IDs
                    for target_idx, distance in target_distances.items():
                        target_id = self.graph[target_idx]  # Get node ID from graph data
                        if target_id:
                            result[source_id][target_id] = distance

            return result

        except Exception as e:
            logger.warning(f"Bellman-Ford path lengths calculation failed: {e}")
            return {}

    def detect_negative_cycles(self, weight_fn=None) -> bool:
        """Detect if the graph contains negative cycles using Bellman-Ford algorithm."""
        try:
            # Check for negative cycles by trying Bellman-Ford from each node
            for source_idx in self.graph.node_indices():
                try:
                    # If Bellman-Ford raises an exception, there's a negative cycle
                    edge_cost_fn = weight_fn if weight_fn else lambda _: 1
                    rx.bellman_ford_shortest_path_lengths(
                        self.graph,
                        source_idx,
                        edge_cost_fn
                    )
                except Exception:
                    # Negative cycle detected
                    return True

            return False

        except Exception as e:
            logger.warning(f"Negative cycle detection failed: {e}")
            return False

    def calculate_weighted_shortest_paths(self, source_id: str, weight_fn=None) -> Dict[str, Any]:
        """Calculate shortest paths from a source node using Bellman-Ford algorithm."""
        try:
            source_node = self.nodes.get(source_id)
            if not source_node:
                return {}

            source_index = getattr(source_node, '_rustworkx_index', None)
            if source_index is None:
                return {}

            # Use Bellman-Ford from single source
            edge_cost_fn = weight_fn if weight_fn else lambda _: 1
            distances = rx.bellman_ford_shortest_path_lengths(
                self.graph,
                source_index,
                edge_cost_fn
            )

            result = {
                "source": source_id,
                "distances": {},
                "has_negative_cycles": False
            }

            for target_idx, distance in distances.items():
                target_id = self.graph[target_idx]  # Get node ID from graph data
                if target_id:
                    result["distances"][target_id] = distance

            return result

        except Exception as e:
            logger.warning(f"Weighted shortest paths calculation failed: {e}")
            return {}

    def analyze_graph_connectivity(self, weight_fn=None) -> Dict[str, Any]:
        """Comprehensive connectivity analysis using multiple rustworkx algorithms."""
        try:
            # Basic connectivity
            num_nodes = len(self.nodes)
            num_edges = len(self.relationships)

            # Shortest path analysis
            floyd_warshall_distances = self.calculate_graph_distance_matrix()
            bellman_ford_distances = self.calculate_bellman_ford_path_lengths(weight_fn)

            # Check for negative cycles
            has_negative_cycles = self.detect_negative_cycles(weight_fn)

            # Analyze path lengths
            all_distances = []
            reachable_pairs = 0

            for source, targets in floyd_warshall_distances.items():
                for target, distance in targets.items():
                    if source != target and distance != float('inf'):
                        all_distances.append(distance)
                        reachable_pairs += 1

            # Calculate connectivity metrics
            total_possible_pairs = num_nodes * (num_nodes - 1)
            connectivity_ratio = reachable_pairs / total_possible_pairs if total_possible_pairs > 0 else 0

            avg_distance = sum(all_distances) / len(all_distances) if all_distances else 0
            max_distance = max(all_distances) if all_distances else 0
            min_distance = min(all_distances) if all_distances else 0

            return {
                "basic_metrics": {
                    "num_nodes": num_nodes,
                    "num_edges": num_edges,
                    "density": num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0
                },
                "connectivity_metrics": {
                    "reachable_pairs": reachable_pairs,
                    "total_possible_pairs": total_possible_pairs,
                    "connectivity_ratio": connectivity_ratio,
                    "is_strongly_connected": connectivity_ratio == 1.0
                },
                "distance_metrics": {
                    "average_distance": avg_distance,
                    "maximum_distance": max_distance,
                    "minimum_distance": min_distance,
                    "has_negative_cycles": has_negative_cycles
                },
                "algorithm_comparison": {
                    "floyd_warshall_computed": len(floyd_warshall_distances),
                    "bellman_ford_computed": len(bellman_ford_distances),
                    "algorithms_agree": self._compare_distance_algorithms(
                        floyd_warshall_distances,
                        bellman_ford_distances
                    )
                }
            }

        except Exception as e:
            logger.warning(f"Connectivity analysis failed: {e}")
            return {}

    def _compare_distance_algorithms(self, floyd_distances, bellman_distances) -> bool:
        """Compare results from Floyd-Warshall and Bellman-Ford algorithms."""
        try:
            tolerance = 1e-6

            for source in floyd_distances:
                if source not in bellman_distances:
                    continue

                for target in floyd_distances[source]:
                    if target not in bellman_distances[source]:
                        continue

                    floyd_dist = floyd_distances[source][target]
                    bellman_dist = bellman_distances[source][target]

                    if abs(floyd_dist - bellman_dist) > tolerance:
                        return False

            return True

        except Exception:
            return False