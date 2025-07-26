"""
High-Performance Code Graph using rustworkx

Provides blazing-fast graph operations and advanced algorithms for code analysis.
Uses Rust-backed rustworkx for optimal performance with large codebases.
"""

import logging
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple

import rustworkx as rx

from .universal_graph import (
    UniversalNode,
    UniversalRelationship,
    NodeType,
    RelationshipType
)

logger = logging.getLogger(__name__)


class RustworkxCodeGraph:
    """
    High-performance code graph using rustworkx for advanced analytics.

    Provides:
    - 10-100x faster graph operations
    - Advanced graph algorithms (centrality, shortest paths, cycles)
    - Memory-efficient storage for large codebases
    - Sophisticated code analytics
    """

    def __init__(self):
        # Create directed graph for code relationships
        self.graph = rx.PyDiGraph()

        # Node and relationship storage with metadata
        self.nodes: Dict[str, UniversalNode] = {}
        self.relationships: Dict[str, UniversalRelationship] = {}

        # Mapping between our IDs and rustworkx node indices
        self.node_id_to_index: Dict[str, int] = {}
        self.index_to_node_id: Dict[int, str] = {}

        # Edge mapping for relationships
        self.edge_id_to_index: Dict[str, int] = {}
        self.index_to_edge_id: Dict[int, str] = {}

        # Performance indexes
        self._nodes_by_type: Dict[NodeType, Set[str]] = {}
        self._nodes_by_language: Dict[str, Set[str]] = {}

        # Graph metadata
        self.metadata: Dict[str, Any] = {}

    def add_node(self, node: UniversalNode) -> None:
        """Add a node to the high-performance graph."""
        # Store node data
        self.nodes[node.id] = node

        # Add to rustworkx graph with node data
        node_index = self.graph.add_node(node)

        # Update mapping
        self.node_id_to_index[node.id] = node_index
        self.index_to_node_id[node_index] = node.id

        # Update performance indexes
        if node.node_type not in self._nodes_by_type:
            self._nodes_by_type[node.node_type] = set()
        self._nodes_by_type[node.node_type].add(node.id)

        if node.language:
            if node.language not in self._nodes_by_language:
                self._nodes_by_language[node.language] = set()
            self._nodes_by_language[node.language].add(node.id)

    def add_relationship(self, relationship: UniversalRelationship) -> None:
        """Add a relationship to the high-performance graph."""
        # Store relationship data
        self.relationships[relationship.id] = relationship

        # Get node indices
        source_index = self.node_id_to_index.get(relationship.source_id)
        target_index = self.node_id_to_index.get(relationship.target_id)

        if source_index is None or target_index is None:
            logger.warning(f"Cannot add relationship {relationship.id}: missing nodes")
            return

        # Add edge to rustworkx graph
        edge_index = self.graph.add_edge(source_index, target_index, relationship)

        # Update edge mapping
        self.edge_id_to_index[relationship.id] = edge_index
        self.index_to_edge_id[edge_index] = relationship.id

    def get_node(self, node_id: str) -> Optional[UniversalNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_relationship(self, relationship_id: str) -> Optional[UniversalRelationship]:
        """Get a relationship by ID."""
        return self.relationships.get(relationship_id)

    @lru_cache(maxsize=100000)
    def find_nodes_by_name(self, name: str, exact_match: bool = True) -> List[UniversalNode]:
        """Find nodes by name with LRU caching for performance optimization."""
        results = []

        for node in self.nodes.values():
            if exact_match:
                if node.name == name:
                    results.append(node)
            else:
                if name.lower() in node.name.lower():
                    results.append(node)

        return results

    @lru_cache(maxsize=5000)
    def get_nodes_by_type(self, node_type: NodeType) -> List[UniversalNode]:
        """Get all nodes of a specific type with LRU caching."""
        node_ids = self._nodes_by_type.get(node_type, set())
        return [self.nodes[node_id] for node_id in node_ids]

    def get_relationships_from(self, node_id: str) -> List[UniversalRelationship]:
        """Get all relationships originating from a node."""
        node_index = self.node_id_to_index.get(node_id)
        if node_index is None:
            return []

        relationships = []
        # Get outgoing edges
        for edge in self.graph.out_edges(node_index):
            source_idx, target_idx, edge_data = edge
            if isinstance(edge_data, UniversalRelationship):
                relationships.append(edge_data)

        return relationships

    def get_relationships_to(self, node_id: str) -> List[UniversalRelationship]:
        """Get all relationships targeting a node."""
        node_index = self.node_id_to_index.get(node_id)
        if node_index is None:
            return []

        relationships = []
        # Get incoming edges
        for edge in self.graph.in_edges(node_index):
            source_idx, target_idx, edge_data = edge
            if isinstance(edge_data, UniversalRelationship):
                relationships.append(edge_data)

        return relationships

    def get_relationships_by_type(self, relationship_type: RelationshipType) -> List[UniversalRelationship]:
        """Get all relationships of a specific type."""
        return [rel for rel in self.relationships.values()
                if rel.relationship_type == relationship_type]

    # ========================= ADVANCED ANALYTICS =========================

    def find_shortest_path(self, source_id: str, target_id: str) -> List[str]:
        """Find shortest path between two nodes."""
        source_index = self.node_id_to_index.get(source_id)
        target_index = self.node_id_to_index.get(target_id)

        if source_index is None or target_index is None:
            return []

        try:
            # Use dijkstra shortest path
            path_indices = rx.dijkstra_shortest_paths(
                self.graph, source_index, target_index, lambda _: 1
            )
            if path_indices:
                # Convert first path indices back to node IDs
                return [self.index_to_node_id[idx] for idx in path_indices[0] if idx in self.index_to_node_id]
            return []
        except Exception:
            return []

    def find_all_paths(self, source_id: str, target_id: str, max_length: int = 10) -> List[List[str]]:
        """Find all paths between two nodes up to max_length."""
        source_index = self.node_id_to_index.get(source_id)
        target_index = self.node_id_to_index.get(target_id)

        if source_index is None or target_index is None:
            return []

        try:
            paths = rx.all_simple_paths(self.graph, source_index, target_index, min_depth=1, cutoff=max_length)
            # Convert indices back to node IDs
            return [[self.index_to_node_id[idx] for idx in path] for path in paths]
        except Exception:
            return []

    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the code graph (circular dependencies)."""
        try:
            cycles = rx.simple_cycles(self.graph)
            # Convert indices back to node IDs
            return [[self.index_to_node_id[idx] for idx in cycle] for cycle in cycles]
        except Exception:
            return []

    def get_strongly_connected_components(self) -> List[List[str]]:
        """Find strongly connected components (circular dependency groups)."""
        try:
            components = rx.strongly_connected_components(self.graph)
            # Convert indices back to node IDs
            return [[self.index_to_node_id[idx] for idx in component] for component in components]
        except Exception:
            return []

    @lru_cache(maxsize=1000)
    def calculate_centrality(self) -> Dict[str, float]:
        """Calculate betweenness centrality with LRU caching for performance."""
        try:
            centrality = rx.betweenness_centrality(self.graph)
            # Convert indices back to node IDs
            return {self.index_to_node_id[idx]: score for idx, score in centrality.items()}
        except Exception:
            return {}

    @lru_cache(maxsize=10000)
    def calculate_pagerank(self, alpha: float = 0.85, max_iter: int = 100, tol: float = 1e-6) -> Dict[str, float]:
        """Calculate PageRank with LRU caching for optimal performance."""
        try:
            # Use optimized PageRank with configurable damping factor and convergence
            pagerank_scores = rx.pagerank(
                self.graph,
                alpha=alpha,        # Damping factor (0.85 is standard)
                max_iter=max_iter,  # Maximum iterations for convergence
                tol=tol            # Convergence tolerance
            )
            # Convert indices back to node IDs
            return {self.index_to_node_id[idx]: score for idx, score in pagerank_scores.items()}
        except Exception as e:
            logger.warning(f"PageRank calculation failed: {e}")
            return {}

    def find_ancestors(self, node_id: str) -> Set[str]:
        """Find all nodes that can reach this node."""
        node_index = self.node_id_to_index.get(node_id)
        if node_index is None:
            return set()

        try:
            ancestor_indices = rx.ancestors(self.graph, node_index)
            return {self.index_to_node_id[idx] for idx in ancestor_indices}
        except Exception:
            return set()

    def find_descendants(self, node_id: str) -> Set[str]:
        """Find all nodes reachable from this node."""
        node_index = self.node_id_to_index.get(node_id)
        if node_index is None:
            return set()

        try:
            descendant_indices = rx.descendants(self.graph, node_index)
            return {self.index_to_node_id[idx] for idx in descendant_indices}
        except Exception:
            return set()

    def get_node_degree(self, node_id: str) -> Tuple[int, int, int]:
        """Get node degree (in_degree, out_degree, total_degree)."""
        node_index = self.node_id_to_index.get(node_id)
        if node_index is None:
            return (0, 0, 0)

        in_degree = self.graph.in_degree(node_index)
        out_degree = self.graph.out_degree(node_index)
        total_degree = in_degree + out_degree

        return (in_degree, out_degree, total_degree)

    def is_directed_acyclic(self) -> bool:
        """Check if the graph is a DAG (no circular dependencies)."""
        return rx.is_directed_acyclic_graph(self.graph)

    def topological_sort(self) -> List[str]:
        """Get topological ordering of nodes (dependency order)."""
        try:
            sorted_indices = rx.topological_sort(self.graph)
            return [self.index_to_node_id[idx] for idx in sorted_indices]
        except Exception:
            return []

    @lru_cache(maxsize=1000)
    def calculate_closeness_centrality(self) -> Dict[str, float]:
        """Calculate closeness centrality with LRU caching."""
        try:
            centrality = rx.closeness_centrality(self.graph)
            return {self.index_to_node_id[idx]: score for idx, score in centrality.items()}
        except Exception as e:
            logger.warning(f"Closeness centrality calculation failed: {e}")
            return {}

    @lru_cache(maxsize=5000)
    def calculate_eigenvector_centrality(self, max_iter: int = 100, tol: float = 1e-6) -> Dict[str, float]:
        """Calculate eigenvector centrality with LRU caching."""
        try:
            centrality = rx.eigenvector_centrality(self.graph, max_iter=max_iter, tol=tol)
            return {self.index_to_node_id[idx]: score for idx, score in centrality.items()}
        except Exception as e:
            logger.warning(f"Eigenvector centrality calculation failed: {e}")
            return {}

    def find_articulation_points(self) -> List[str]:
        """Find articulation points (nodes whose removal increases connected components)."""
        try:
            # Convert to undirected for articulation point analysis
            undirected = self.graph.to_undirected()
            articulation_indices = rx.articulation_points(undirected)
            return [self.index_to_node_id[idx] for idx in articulation_indices if idx in self.index_to_node_id]
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
                    source_id = self.index_to_node_id.get(edge[0])
                    target_id = self.index_to_node_id.get(edge[1])
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
            for i, source_id in enumerate(self.index_to_node_id.values()):
                result[source_id] = {}
                for j, target_id in enumerate(self.index_to_node_id.values()):
                    if i < len(distance_matrix) and j < len(distance_matrix[i]):
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

        Args:
            weight_fn: Optional weight function for edges. If None, uses unit weights.

        Returns:
            Dict mapping source nodes to target nodes with their shortest distances
        """
        try:
            # Use Bellman-Ford for all pairs shortest path lengths
            edge_cost_fn = weight_fn if weight_fn else lambda _: 1
            paths_result = rx.all_pairs_bellman_ford_path_lengths(self.graph, edge_cost_fn)

            result = {}
            for source_idx, target_distances in paths_result.items():
                source_id = self.index_to_node_id.get(source_idx)
                if source_id:
                    result[source_id] = {}

                    # Convert target indices to node IDs
                    for target_idx, distance in target_distances.items():
                        target_id = self.index_to_node_id.get(target_idx)
                        if target_id:
                            result[source_id][target_id] = distance

            return result

        except Exception as e:
            logger.warning(f"Bellman-Ford path lengths calculation failed: {e}")
            return {}

    def detect_negative_cycles(self, weight_fn=None) -> bool:
        """
        Detect if the graph contains negative cycles using Bellman-Ford algorithm.

        Args:
            weight_fn: Optional weight function for edges

        Returns:
            True if negative cycles exist, False otherwise
        """
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
        """
        Calculate shortest paths from a source node using Bellman-Ford algorithm.

        Args:
            source_id: Source node ID
            weight_fn: Optional weight function for edges

        Returns:
            Dictionary with distances and paths to all reachable nodes
        """
        try:
            source_index = self.node_id_to_index.get(source_id)
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
                target_id = self.index_to_node_id.get(target_idx)
                if target_id:
                    result["distances"][target_id] = distance

            return result

        except Exception as e:
            logger.warning(f"Weighted shortest paths calculation failed: {e}")
            return {}

    def analyze_graph_connectivity(self, weight_fn=None) -> Dict[str, Any]:
        """
        Comprehensive connectivity analysis using multiple rustworkx algorithms.

        Args:
            weight_fn: Optional weight function for edges

        Returns:
            Dictionary with comprehensive connectivity metrics
        """
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

    # ========================= TRAVERSAL ALGORITHMS =========================

    def depth_first_search(self, source_id: str, visitor_fn=None) -> List[str]:
        """
        Perform depth-first search traversal starting from source node.

        Args:
            source_id: Starting node ID
            visitor_fn: Optional visitor function called for each node

        Returns:
            List of node IDs in DFS order
        """
        try:
            source_index = self.node_id_to_index.get(source_id)
            if source_index is None:
                return []

            # Perform DFS traversal
            dfs_edges = rx.dfs_edges(self.graph, source_index)

            # Extract unique nodes in DFS order
            visited_nodes = [source_id]  # Start with source
            for edge in dfs_edges:
                target_id = self.index_to_node_id.get(edge[1])
                if target_id and target_id not in visited_nodes:
                    visited_nodes.append(target_id)
                    if visitor_fn:
                        visitor_fn(target_id)

            return visited_nodes

        except Exception as e:
            logger.warning(f"DFS traversal failed: {e}")
            return []

    def breadth_first_search(self, source_id: str, visitor_fn=None) -> List[str]:
        """
        Perform breadth-first search traversal starting from source node.

        Args:
            source_id: Starting node ID
            visitor_fn: Optional visitor function called for each node

        Returns:
            List of node IDs in BFS order
        """
        try:
            source_index = self.node_id_to_index.get(source_id)
            if source_index is None:
                return []

            # Perform BFS traversal using successor iteration
            visited = set([source_index])
            queue = [source_index]
            visited_nodes = [source_id]

            while queue:
                current_index = queue.pop(0)
                for successor in self.graph.successors(current_index):
                    if successor not in visited:
                        visited.add(successor)
                        queue.append(successor)
                        successor_id = self.index_to_node_id.get(successor)
                        if successor_id:
                            visited_nodes.append(successor_id)
                            if visitor_fn:
                                visitor_fn(successor_id)

            return visited_nodes

        except Exception as e:
            logger.warning(f"BFS traversal failed: {e}")
            return []

    def find_node_layers(self, source_id: str) -> Dict[int, List[str]]:
        """
        Find nodes organized by their distance layers from the source.

        Args:
            source_id: Starting node ID

        Returns:
            Dictionary mapping layer number to list of node IDs at that layer
        """
        try:
            source_index = self.node_id_to_index.get(source_id)
            if source_index is None:
                return {}

            # Get shortest path lengths to organize by layers (unit weight function)
            distances = rx.dijkstra_shortest_path_lengths(self.graph, source_index, lambda _: 1)

            layers = {}
            for target_index, distance in distances.items():
                target_id = self.index_to_node_id.get(target_index)
                if target_id:
                    layer = int(distance)
                    if layer not in layers:
                        layers[layer] = []
                    layers[layer].append(target_id)

            return layers

        except Exception as e:
            logger.warning(f"Layer analysis failed: {e}")
            return {}

    def find_dominating_set(self) -> List[str]:
        """
        Find a dominating set - minimum set of nodes that can reach all other nodes.
        Useful for identifying key architectural components.

        Returns:
            List of node IDs forming a dominating set
        """
        try:
            # Check if dominating_set is available
            if hasattr(rx, 'dominating_set'):
                dominating_indices = getattr(rx, 'dominating_set')(self.graph)
                return [
                    self.index_to_node_id[idx]
                    for idx in dominating_indices
                    if idx in self.index_to_node_id
                ]
            else:
                # Fallback: return nodes with highest degree as approximation
                node_degrees = [(node_id, self.get_node_degree(node_id)[2])
                               for node_id in self.nodes.keys()]
                node_degrees.sort(key=lambda x: x[1], reverse=True)
                # Return top 10% of nodes by degree
                top_count = max(1, len(node_degrees) // 10)
                return [node_id for node_id, _ in node_degrees[:top_count]]

        except Exception as e:
            logger.warning(f"Dominating set calculation failed: {e}")
            return []

    def analyze_node_connectivity(self, node_id: str) -> Dict[str, Any]:
        """
        Analyze connectivity patterns for a specific node.

        Args:
            node_id: Node to analyze

        Returns:
            Dictionary with comprehensive connectivity analysis for the node
        """
        try:
            # Get basic degree information
            in_degree, out_degree, total_degree = self.get_node_degree(node_id)

            # Find reachable nodes
            ancestors = self.find_ancestors(node_id)
            descendants = self.find_descendants(node_id)

            # Analyze traversal patterns
            dfs_reachable = set(self.depth_first_search(node_id))
            bfs_reachable = set(self.breadth_first_search(node_id))

            # Find layers from this node
            layers = self.find_node_layers(node_id)
            max_distance = max(layers.keys()) if layers else 0

            return {
                "node_id": node_id,
                "degree_analysis": {
                    "in_degree": in_degree,
                    "out_degree": out_degree,
                    "total_degree": total_degree
                },
                "reachability": {
                    "ancestors_count": len(ancestors),
                    "descendants_count": len(descendants),
                    "dfs_reachable_count": len(dfs_reachable),
                    "bfs_reachable_count": len(bfs_reachable)
                },
                "distance_analysis": {
                    "max_distance_to_others": max_distance,
                    "layers": {str(k): len(v) for k, v in layers.items()},
                    "influence_radius": max_distance
                },
                "structural_importance": {
                    "is_articulation_point": node_id in self.find_articulation_points(),
                    "centrality_percentile": self._calculate_centrality_percentile(node_id)
                }
            }

        except Exception as e:
            logger.warning(f"Node connectivity analysis failed: {e}")
            return {}

    def _calculate_centrality_percentile(self, node_id: str) -> float:
        """Calculate what percentile this node is in for centrality."""
        try:
            centrality_scores = self.calculate_centrality()
            if not centrality_scores or node_id not in centrality_scores:
                return 0.0

            node_score = centrality_scores[node_id]
            all_scores = list(centrality_scores.values())
            all_scores.sort()

            rank = sum(1 for score in all_scores if score <= node_score)
            percentile = (rank / len(all_scores)) * 100

            return percentile

        except Exception:
            return 0.0

    # ========================= STATISTICS =========================

    @lru_cache(maxsize=10000)
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics with LRU caching."""
        total_nodes = len(self.nodes)
        total_relationships = len(self.relationships)

        # Node type distribution
        node_types = {}
        for node_type, node_ids in self._nodes_by_type.items():
            node_types[node_type.value] = len(node_ids)

        # Language distribution
        languages = {}
        for language, node_ids in self._nodes_by_language.items():
            languages[language] = len(node_ids)

        # Relationship type distribution
        relationship_types = {}
        for rel in self.relationships.values():
            rel_type = rel.relationship_type.value
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

        # Graph metrics
        is_dag = self.is_directed_acyclic()
        num_cycles = len(self.detect_cycles()) if not is_dag else 0

        return {
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "node_types": node_types,
            "languages": languages,
            "relationship_types": relationship_types,
            "is_directed_acyclic": is_dag,
            "num_cycles": num_cycles,
            "density": total_relationships / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0,
            "average_degree": (2 * total_relationships) / total_nodes if total_nodes > 0 else 0,
        }

    def clear(self) -> None:
        """Clear all data from the graph."""
        self.graph.clear()
        self.nodes.clear()
        self.relationships.clear()
        self.node_id_to_index.clear()
        self.index_to_node_id.clear()
        self.edge_id_to_index.clear()
        self.index_to_edge_id.clear()
        self._nodes_by_type.clear()
        self._nodes_by_language.clear()
        self.metadata.clear()

    # ========================= SERIALIZATION =========================

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Serialize the graph to JSON format using rustworkx serialization.

        Args:
            indent: Optional indentation for pretty printing

        Returns:
            JSON string representation of the graph
        """
        try:
            # Use rustworkx node_link_json for efficient serialization
            try:
                json_data = rx.node_link_json(
                    self.graph,
                    node_attrs=lambda node: {
                        "id": str(node.id),
                        "name": str(node.name),
                        "type": str(node.node_type.value),
                        "language": str(node.language),
                        "file": str(node.location.file_path),
                        "line": str(node.location.start_line),
                        "end_line": str(node.location.end_line),
                        "complexity": str(node.complexity)
                    },
                    edge_attrs=lambda edge: {
                        "id": str(edge.id),
                        "type": str(edge.relationship_type.value),
                        "strength": str(edge.strength)
                    }
                )
            except (AttributeError, TypeError):
                # Fallback: manual JSON creation
                json_data = {
                    "nodes": [
                        {
                            "id": node.id,
                            "name": node.name,
                            "type": node.node_type.value,
                            "language": node.language,
                            "file": node.location.file_path,
                            "line": node.location.start_line
                        }
                        for node in self.nodes.values()
                    ],
                    "edges": [
                        {
                            "id": rel.id,
                            "source": rel.source_id,
                            "target": rel.target_id,
                            "type": rel.relationship_type.value
                        }
                        for rel in self.relationships.values()
                    ]
                }

            import json
            if indent:
                return json.dumps(json_data, indent=indent)
            return json.dumps(json_data) if isinstance(json_data, dict) else str(json_data)

        except Exception as e:
            logger.warning(f"JSON serialization failed: {e}")
            return "{}"

    def to_dot(self,
               filename: Optional[str] = None,
               node_attr_fn=None,
               edge_attr_fn=None,
               graph_attr: Optional[Dict[str, str]] = None) -> str:
        """
        Export graph to DOT format for visualization with Graphviz.

        Args:
            filename: Optional filename to write DOT file
            node_attr_fn: Function to generate node attributes
            edge_attr_fn: Function to generate edge attributes
            graph_attr: Graph-level attributes

        Returns:
            DOT format string
        """
        try:
            def default_node_attr(node):
                return {
                    "label": f"{node.name}\\n({node.node_type.value})",
                    "shape": "box" if node.node_type == NodeType.FUNCTION else "ellipse",
                    "color": self._get_node_color(node.node_type)
                }

            def default_edge_attr(edge):
                return {
                    "label": edge.relationship_type.value,
                    "color": self._get_edge_color(edge.relationship_type)
                }

            node_attr_callback = node_attr_fn or default_node_attr
            edge_attr_callback = edge_attr_fn or default_edge_attr

            if hasattr(rx, 'graph_to_dot'):
                dot_string = getattr(rx, 'graph_to_dot')(
                    self.graph,
                    node_attr=node_attr_callback,
                    edge_attr=edge_attr_callback,
                    graph_attr=graph_attr or {"rankdir": "TB", "concentrate": "true"}
                )
            else:
                # Fallback: manual DOT creation
                dot_string = "digraph G {\n"
                for node in self.nodes.values():
                    attrs = node_attr_callback(node)
                    attr_str = ", ".join([f'{k}="{v}"' for k, v in attrs.items()])
                    dot_string += f'  "{node.id}" [{attr_str}];\n'

                for rel in self.relationships.values():
                    attrs = edge_attr_callback(rel)
                    attr_str = ", ".join([f'{k}="{v}"' for k, v in attrs.items()])
                    dot_string += f'  "{rel.source_id}" -> "{rel.target_id}" [{attr_str}];\n'
                dot_string += "}\n"

            if filename:
                with open(filename, 'w') as f:
                    f.write(dot_string)
                logger.info(f"DOT file written to {filename}")

            return dot_string

        except Exception as e:
            logger.warning(f"DOT export failed: {e}")
            return ""

    def to_graphml(self, filename: str) -> bool:
        """
        Export graph to GraphML format for use with graph analysis tools.

        Args:
            filename: Output filename

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create node and edge attributes for GraphML
            def node_map_fn(node):
                return {
                    "id": node.id,
                    "name": node.name,
                    "type": node.node_type.value,
                    "language": node.language,
                    "file": node.location.file_path,
                    "line": str(node.location.start_line),
                    "complexity": str(node.complexity)
                }

            def edge_map_fn(edge):
                return {
                    "id": edge.id,
                    "type": edge.relationship_type.value,
                    "strength": str(edge.strength)
                }

            if hasattr(rx, 'write_graphml'):
                getattr(rx, 'write_graphml')(
                    self.graph,
                    filename,
                    node_attr_fn=node_map_fn,
                    edge_attr_fn=edge_map_fn
                )
            else:
                # Fallback: manual GraphML creation
                with open(filename, 'w') as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
                    f.write('  <graph id="G" edgedefault="directed">\n')

                    for node in self.nodes.values():
                        attrs = node_map_fn(node)
                        f.write(f'    <node id="{node.id}">\n')
                        for key, value in attrs.items():
                            f.write(f'      <data key="{key}">{value}</data>\n')
                        f.write('    </node>\n')

                    for rel in self.relationships.values():
                        attrs = edge_map_fn(rel)
                        f.write(f'    <edge source="{rel.source_id}" target="{rel.target_id}">\n')
                        for key, value in attrs.items():
                            f.write(f'      <data key="{key}">{value}</data>\n')
                        f.write('    </edge>\n')
                    f.write('  </graph>\n')
                    f.write('</graphml>\n')

            logger.info(f"GraphML file written to {filename}")
            return True

        except Exception as e:
            logger.warning(f"GraphML export failed: {e}")
            return False

    def from_json(self, json_data: str) -> bool:
        """
        Load graph from JSON format.

        Args:
            json_data: JSON string representation

        Returns:
            True if successful, False otherwise
        """
        try:
            import json
            data = json.loads(json_data) if isinstance(json_data, str) else json_data

            # Clear existing graph
            self.clear()

            # Recreate graph from node-link format
            if hasattr(rx, 'node_link_graph'):
                self.graph = getattr(rx, 'node_link_graph')(data)
            else:
                self.graph = rx.PyDiGraph()
                for node_data in data.get('nodes', []):
                    node_id = node_data['id']
                    if node_id in self.nodes:
                        node_index = self.graph.add_node(self.nodes[node_id])
                        self.node_id_to_index[node_id] = node_index
                        self.index_to_node_id[node_index] = node_id

                for edge_data in data.get('edges', []):
                    rel_id = edge_data['id']
                    if rel_id in self.relationships:
                        rel = self.relationships[rel_id]
                        source_idx = self.node_id_to_index.get(rel.source_id)
                        target_idx = self.node_id_to_index.get(rel.target_id)
                        if source_idx is not None and target_idx is not None:
                            edge_index = self.graph.add_edge(source_idx, target_idx, rel)
                            self.edge_id_to_index[rel_id] = edge_index
                            self.index_to_edge_id[edge_index] = rel_id

            # Rebuild our mappings
            for i, node_data in enumerate(data.get('nodes', [])):
                node_id = node_data.get('id')
                if node_id:
                    self.node_id_to_index[node_id] = i
                    self.index_to_node_id[i] = node_id

            logger.info("Graph loaded from JSON successfully")
            return True

        except Exception as e:
            logger.warning(f"JSON deserialization failed: {e}")
            return False

    def export_analysis_report(self, filename: str, format: str = "json") -> bool:
        """
        Export comprehensive analysis report in various formats.

        Args:
            filename: Output filename
            format: Export format ("json", "yaml", "csv")

        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate comprehensive analysis
            report = {
                "metadata": {
                    "export_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "graph_size": len(self.nodes),
                    "relationship_count": len(self.relationships)
                },
                "statistics": self.get_statistics(),
                "centrality_analysis": {
                    "betweenness": self.calculate_centrality(),
                    "pagerank": self.calculate_pagerank(),
                    "closeness": self.calculate_closeness_centrality(),
                    "eigenvector": self.calculate_eigenvector_centrality()
                },
                "structural_analysis": {
                    "articulation_points": self.find_articulation_points(),
                    "bridges": self.find_bridges(),
                    "is_dag": self.is_directed_acyclic(),
                    "cycles": self.detect_cycles(),
                    "dominating_set": self.find_dominating_set()
                },
                "connectivity_analysis": self.analyze_graph_connectivity()
            }

            if format.lower() == "json":
                import json
                with open(filename, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif format.lower() == "yaml":
                try:
                    import yaml
                    with open(filename, 'w') as f:
                        yaml.dump(report, f, default_flow_style=False)
                except ImportError:
                    import json
                    logger.warning("PyYAML not available, falling back to JSON")
                    with open(filename.replace('.yaml', '.json').replace('.yml', '.json'), 'w') as f:
                        json.dump(report, f, indent=2, default=str)
            elif format.lower() == "csv":
                import csv
                # Export key metrics to CSV
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Metric", "Value"])
                    stats = report["statistics"]
                    for key, value in stats.items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                writer.writerow([f"{key}_{subkey}", subvalue])
                        else:
                            writer.writerow([key, value])

            logger.info(f"Analysis report exported to {filename}")
            return True

        except Exception as e:
            logger.warning(f"Report export failed: {e}")
            return False

    def _get_node_color(self, node_type: NodeType) -> str:
        """Get color for node type in visualizations."""
        color_map = {
            NodeType.MODULE: "lightblue",
            NodeType.CLASS: "lightgreen",
            NodeType.FUNCTION: "orange",
            NodeType.VARIABLE: "lightgray",
            NodeType.IMPORT: "purple"
        }
        return color_map.get(node_type, "white")

    def _get_edge_color(self, relationship_type: RelationshipType) -> str:
        """Get color for relationship type in visualizations."""
        color_map = {
            RelationshipType.CALLS: "red",
            RelationshipType.CONTAINS: "blue",
            RelationshipType.IMPORTS: "green",
            RelationshipType.REFERENCES: "orange",
            RelationshipType.INHERITS: "purple"
        }
        return color_map.get(relationship_type, "black")
