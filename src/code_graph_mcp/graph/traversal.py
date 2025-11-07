"""
Graph Traversal Algorithms for RustworkX Code Graph

Provides comprehensive graph traversal and search algorithms:
- Depth-first and breadth-first search
- Layer-based node organization  
- Dominating set analysis
- Node connectivity analysis
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import rustworkx as rx

from ..universal_graph import RelationshipType

logger = logging.getLogger(__name__)


class GraphTraversalMixin:
    """
    Mixin class providing graph traversal and node analysis algorithms.
    
    Provides:
    - DFS and BFS traversal
    - Layer-based node organization
    - Dominating set calculation
    - Node connectivity analysis
    """

    def depth_first_search(self, source_id: str, visitor_fn=None) -> List[str]:
        """
        Perform depth-first search traversal starting from source node.

        Args:
            source_id: Starting node ID
            visitor_fn: Optional visitor function called for each node

        Returns:
            List of node IDs in DFS order
        """
        with self._lock:
            try:
                source_node = self.nodes.get(source_id)
                if not source_node or not hasattr(source_node, '_rustworkx_index'):
                    return []

                # Perform DFS traversal
                dfs_edges = rx.dfs_edges(self.graph, source_node._rustworkx_index)

                # Extract unique nodes in DFS order
                visited_nodes = [source_id]  # Start with source
                for edge in dfs_edges:
                    target_idx = edge[1]
                    if target_idx < len(self.graph):
                        target_id = self.graph[target_idx]
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
        with self._lock:
            try:
                source_node = self.nodes.get(source_id)
                if not source_node or not hasattr(source_node, '_rustworkx_index'):
                    return []

                # Perform BFS traversal using successor iteration
                source_index = source_node._rustworkx_index
                visited = set([source_index])
                queue = [source_index]
                visited_nodes = [source_id]

                while queue:
                    current_index = queue.pop(0)
                    for successor in self.graph.successors(current_index):
                        if successor not in visited:
                            visited.add(successor)
                            queue.append(successor)
                            if successor < len(self.graph):
                                successor_id = self.graph[successor]
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
            source_node = self.nodes.get(source_id)
            if not source_node:
                return {}

            source_index = getattr(source_node, '_rustworkx_index', None)
            if source_index is None:
                return {}

            # Get shortest path lengths to organize by layers (unit weight function)
            distances = rx.dijkstra_shortest_path_lengths(self.graph, source_index, lambda _: 1)

            layers = {}
            for target_index, distance in distances.items():
                target_id = self.graph[target_index]  # Get node ID from graph data
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
        with self._lock:
            try:
                # Check if dominating_set is available
                if hasattr(rx, 'dominating_set'):
                    dominating_indices = getattr(rx, 'dominating_set')(self.graph)
                    result = []
                    for idx in dominating_indices:
                        if idx < len(self.graph):
                            node_id = self.graph[idx]
                            if node_id:
                                result.append(node_id)
                    return result
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

    def dfs_traversal_with_depth(
        self,
        start_node_id: str,
        max_depth: int = 10,
        include_seams: bool = True,
        visited: Optional[Set[str]] = None
    ) -> Dict[str, Any]:
        """DFS traversal with depth tracking and SEAM edge awareness."""
        if visited is None:
            visited = set()

        try:
            if start_node_id not in self.nodes:
                return {"nodes_by_depth": {}, "total_nodes": 0, "seam_edges": []}

            depth_map = {start_node_id: 0}
            current_level = {start_node_id}
            seam_edges = []
            nodes_by_depth = {0: [start_node_id]}

            for depth in range(1, max_depth + 1):
                next_level = set()
                for node_id in current_level:
                    if node_id not in visited:
                        visited.add(node_id)
                        
                        rels = self.get_relationships_from(node_id)
                        for rel in rels:
                            successor_id = rel.target_id
                            if successor_id not in visited and successor_id not in depth_map:
                                depth_map[successor_id] = depth
                                next_level.add(successor_id)
                                
                                if include_seams and rel.relationship_type == RelationshipType.SEAM:
                                    seam_edges.append((node_id, successor_id))

                if not next_level:
                    break

                nodes_by_depth[depth] = list(next_level)
                current_level = next_level

            return {
                "nodes_by_depth": nodes_by_depth,
                "total_nodes": len(visited),
                "seam_edges": seam_edges,
                "max_depth_reached": max(depth_map.values()) if depth_map else 0,
            }

        except Exception as e:
            logger.warning(f"DFS traversal with depth failed: {e}")
            return {"nodes_by_depth": {}, "total_nodes": 0, "seam_edges": []}

    def find_call_chain(
        self,
        start_node_id: str,
        end_node_id: Optional[str] = None,
        follow_seams: bool = True,
        max_depth: int = 50
    ) -> List[Tuple[str, str]]:
        """Find shortest path between nodes, optionally crossing language boundaries."""
        try:
            if start_node_id not in self.nodes:
                return []

            if end_node_id is None:
                bfs_nodes = self.breadth_first_search(start_node_id)
                return [(bfs_nodes[i], bfs_nodes[i + 1]) 
                        for i in range(min(len(bfs_nodes) - 1, max_depth))]

            visited = {start_node_id}
            parent_map = {start_node_id: None}
            queue = [start_node_id]
            depth = 0

            while queue and depth < max_depth:
                next_queue = []
                for node_id in queue:
                    if node_id == end_node_id:
                        path = []
                        current = end_node_id
                        while parent_map[current] is not None:
                            path.append((parent_map[current], current))
                            current = parent_map[current]
                        return list(reversed(path))

                    rels = self.get_relationships_from(node_id)
                    for rel in rels:
                        successor_id = rel.target_id
                        if not follow_seams and rel.relationship_type == RelationshipType.SEAM:
                            continue

                        if successor_id not in visited:
                            visited.add(successor_id)
                            parent_map[successor_id] = node_id
                            next_queue.append(successor_id)

                queue = next_queue
                depth += 1

            return []

        except Exception as e:
            logger.warning(f"Call chain search failed: {e}")
            return []

    def trace_cross_language_flow(
        self,
        start_node_id: str,
        max_depth: int = 20
    ) -> Dict[str, Any]:
        """Trace execution flow across language boundaries."""
        try:
            language_flow = {}
            visited = set()
            queue = [(start_node_id, 0)]
            seam_bridges = []

            while queue:
                node_id, depth = queue.pop(0)
                if depth > max_depth or node_id in visited:
                    continue

                visited.add(node_id)
                node = self.nodes.get(node_id)
                if not node:
                    continue

                language = getattr(node, 'language', 'unknown')
                if language not in language_flow:
                    language_flow[language] = []

                language_flow[language].append({
                    'node_id': node_id,
                    'name': getattr(node, 'name', ''),
                    'depth': depth
                })

                rels = self.get_relationships_from(node_id)
                for rel in rels:
                    successor_id = rel.target_id
                    if successor_id not in visited:
                        successor = self.nodes.get(successor_id)
                        if successor:
                            successor_lang = getattr(successor, 'language', 'unknown')

                            if successor_lang != language:
                                seam_bridges.append({
                                    'from_node': node_id,
                                    'from_language': language,
                                    'to_node': successor_id,
                                    'to_language': successor_lang,
                                    'type': rel.relationship_type.value if rel.relationship_type else 'unknown'
                                })

                        queue.append((successor_id, depth + 1))

            return {
                'language_flow': language_flow,
                'seam_bridges': seam_bridges,
                'languages_involved': list(language_flow.keys())
            }

        except Exception as e:
            logger.warning(f"Cross-language flow tracing failed: {e}")
            return {'language_flow': {}, 'seam_bridges': [], 'languages_involved': []}
