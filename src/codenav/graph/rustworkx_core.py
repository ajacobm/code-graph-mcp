"""
Core Graph Operations for RustworkX Code Graph

Provides fundamental graph operations including:
- Node and relationship CRUD operations
- Thread-safe graph management
- File tracking and processing
- Basic graph queries
"""

import logging
import threading
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set
from contextlib import contextmanager

import rustworkx as rx

from ..universal_graph import (
    UniversalNode,
    UniversalRelationship,
    NodeType,
    RelationshipType,
    CacheConfig
)

logger = logging.getLogger(__name__)


class RustworkxGraphCore:
    """
    Core graph operations with thread safety and efficient storage.
    
    Handles:
    - Basic CRUD operations
    - Thread-safe graph management  
    - File tracking and processing
    - Performance indexing
    """

    def __init__(self):
        # Thread safety lock
        self._lock = threading.RLock()

        # Create directed graph for code relationships
        self.graph = rx.PyDiGraph()

        # Node and relationship storage with metadata
        self.nodes: Dict[str, UniversalNode] = {}
        self.relationships: Dict[str, UniversalRelationship] = {}

        # Performance indexes
        self._nodes_by_type: Dict[NodeType, Set[str]] = {}
        self._nodes_by_language: Dict[str, Set[str]] = {}

        # Track processed files with thread safety
        self._processed_files: Set[str] = set()
        self._file_to_nodes: Dict[str, Set[str]] = {}  # Track which nodes came from which files

        # Graph metadata
        self.metadata: Dict[str, Any] = {}

        # Generation counter to detect stale operations
        self._generation = 0

    @contextmanager
    def _thread_safe_operation(self):
        """Context manager for thread-safe graph operations."""
        with self._lock:
            generation_start = self._generation
            try:
                yield
            finally:
                # Increment generation to invalidate stale caches
                if self._generation == generation_start:
                    self._generation += 1
                    # Clear LRU caches when graph structure changes
                    self._clear_method_caches()

    def _clear_method_caches(self):
        """Clear all LRU caches to prevent stale data."""
        methods_with_cache = [
            'find_nodes_by_name', 'get_nodes_by_type'
        ]
        for method_name in methods_with_cache:
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                if hasattr(method, 'cache_clear'):
                    method.cache_clear()

    def add_node(self, node: UniversalNode) -> None:
        """Add a node to the high-performance graph with thread safety."""
        with self._thread_safe_operation():
            # Check if node already exists to prevent duplicates
            if node.id in self.nodes:
                logger.debug(f"Node {node.id} already exists, updating...")
                self._remove_node_internal(node.id)

            # Store node data
            self.nodes[node.id] = node

            # Add to rustworkx graph - store the node ID as node data
            # This eliminates the need for separate index mapping
            node_index = self.graph.add_node(node.id)

            # Store the rustworkx index in the node for direct access
            # This prevents index mapping corruption
            node._rustworkx_index = node_index

            # Update performance indexes
            if node.node_type not in self._nodes_by_type:
                self._nodes_by_type[node.node_type] = set()
            self._nodes_by_type[node.node_type].add(node.id)

            if node.language:
                if node.language not in self._nodes_by_language:
                    self._nodes_by_language[node.language] = set()
                self._nodes_by_language[node.language].add(node.id)

            # Track file association for proper cleanup
            file_path = node.location.file_path
            if file_path not in self._file_to_nodes:
                self._file_to_nodes[file_path] = set()
            self._file_to_nodes[file_path].add(node.id)

    def _remove_node_internal(self, node_id: str) -> None:
        """Internal method to remove a node without locking (already locked)."""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # Remove from rustworkx graph if it has an index
        if hasattr(node, '_rustworkx_index'):
            try:
                self.graph.remove_node(node._rustworkx_index)
            except Exception as e:
                logger.debug(f"Failed to remove node from rustworkx: {e}")

        # Remove from our storage
        del self.nodes[node_id]

        # Remove from performance indexes
        if node.node_type in self._nodes_by_type:
            self._nodes_by_type[node.node_type].discard(node_id)
        if node.language and node.language in self._nodes_by_language:
            self._nodes_by_language[node.language].discard(node_id)

        # Remove from file tracking
        file_path = node.location.file_path
        if file_path in self._file_to_nodes:
            self._file_to_nodes[file_path].discard(node_id)

    def add_relationship(self, relationship: UniversalRelationship) -> None:
        """Add a relationship to the high-performance graph with thread safety."""
        with self._thread_safe_operation():
            # Store relationship data
            self.relationships[relationship.id] = relationship

            # Get nodes and their indices directly
            source_node = self.nodes.get(relationship.source_id)
            target_node = self.nodes.get(relationship.target_id)

            if not source_node or not target_node:
                logger.debug(f"Cannot add relationship {relationship.id}: missing nodes")
                return

            # Get indices from nodes directly (no mapping corruption possible)
            source_index = getattr(source_node, '_rustworkx_index', None)
            target_index = getattr(target_node, '_rustworkx_index', None)

            if source_index is None or target_index is None:
                logger.debug(f"Cannot add relationship {relationship.id}: nodes not in rustworkx graph")
                return

            # Add edge to rustworkx graph - store relationship ID as edge data
            edge_index = self.graph.add_edge(source_index, target_index, relationship.id)

            # Store edge index in relationship for direct access
            relationship._rustworkx_edge_index = edge_index

    def get_node(self, node_id: str) -> Optional[UniversalNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_relationship(self, relationship_id: str) -> Optional[UniversalRelationship]:
        """Get a relationship by ID."""
        return self.relationships.get(relationship_id)

    @lru_cache(maxsize=CacheConfig.XLARGE_CACHE)
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

    @lru_cache(maxsize=CacheConfig.LARGE_CACHE)
    def get_nodes_by_type(self, node_type: NodeType) -> List[UniversalNode]:
        """Get all nodes of a specific type with LRU caching."""
        node_ids = self._nodes_by_type.get(node_type, set())
        return [self.nodes[node_id] for node_id in node_ids]

    def get_relationships_from(self, node_id: str) -> List[UniversalRelationship]:
        """Get all relationships originating from a node."""
        with self._lock:
            node = self.nodes.get(node_id)
            if not node or not hasattr(node, '_rustworkx_index'):
                return []

            relationships = []
            # Get outgoing edges
            for edge in self.graph.out_edges(node._rustworkx_index):
                source_idx, target_idx, edge_data = edge
                # edge_data now contains relationship ID
                if isinstance(edge_data, str) and edge_data in self.relationships:
                    relationships.append(self.relationships[edge_data])

            return relationships

    def get_relationships_to(self, node_id: str) -> List[UniversalRelationship]:
        """Get all relationships targeting a node."""
        with self._lock:
            node = self.nodes.get(node_id)
            if not node or not hasattr(node, '_rustworkx_index'):
                return []

            relationships = []
            # Get incoming edges
            for edge in self.graph.in_edges(node._rustworkx_index):
                source_idx, target_idx, edge_data = edge
                # edge_data now contains relationship ID
                if isinstance(edge_data, str) and edge_data in self.relationships:
                    relationships.append(self.relationships[edge_data])

            return relationships

    def get_relationships_by_type(self, relationship_type: RelationshipType) -> List[UniversalRelationship]:
        """Get all relationships of a specific type."""
        return [rel for rel in self.relationships.values()
                if rel.relationship_type == relationship_type]

    def remove_file_nodes(self, file_path: str) -> int:
        """Remove all nodes associated with a specific file and return count removed."""
        with self._thread_safe_operation():
            if file_path not in self._file_to_nodes:
                return 0

            nodes_to_remove = list(self._file_to_nodes[file_path])
            removed_count = 0

            for node_id in nodes_to_remove:
                if node_id in self.nodes:
                    self._remove_node_internal(node_id)
                    removed_count += 1

            # Clean up file tracking
            del self._file_to_nodes[file_path]
            self._processed_files.discard(file_path)

            logger.debug(f"Removed {removed_count} nodes from file: {file_path}")
            return removed_count

    def mark_file_processed(self, file_path: str) -> None:
        """Mark a file as processed for tracking."""
        with self._lock:
            self._processed_files.add(file_path)

    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has been processed."""
        with self._lock:
            return file_path in self._processed_files

    def get_processed_files(self) -> Set[str]:
        """Get set of all processed files."""
        with self._lock:
            return self._processed_files.copy()

    def get_file_node_count(self, file_path: str) -> int:
        """Get the number of nodes associated with a file."""
        with self._lock:
            return len(self._file_to_nodes.get(file_path, set()))

    def add_processed_file(self, file_path: str) -> None:
        """Track a processed file."""
        self._processed_files.add(file_path)

    def clear(self) -> None:
        """Clear all data from the graph with proper thread safety and state reset."""
        with self._thread_safe_operation():
            logger.info(f"CLEARING GRAPH: {len(self.nodes)} nodes, {len(self.relationships)} relationships, {len(self._processed_files)} files")

            # Clear rustworkx graph completely
            self.graph.clear()

            # Clear all our data structures
            self.nodes.clear()
            self.relationships.clear()
            self._processed_files.clear()
            self._file_to_nodes.clear()
            self._nodes_by_type.clear()
            self._nodes_by_language.clear()
            self.metadata.clear()

            # Increment generation to invalidate all caches
            self._generation += 1

            logger.info("GRAPH CLEARED: now has 0 nodes, all state reset")

    def get_basic_statistics(self) -> Dict[str, Any]:
        """Get basic graph statistics."""
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

        file_count = len(self._processed_files)

        return {
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "total_files": file_count,
            "node_types": node_types,
            "languages": languages,
            "relationship_types": relationship_types,
        }