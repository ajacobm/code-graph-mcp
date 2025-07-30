"""
High-Performance Code Graph using rustworkx

Provides blazing-fast graph operations and advanced algorithms for code analysis.
Uses Rust-backed rustworkx for optimal performance with large codebases.

This module composes all graph functionality using mixins:
- Core operations: Basic CRUD, thread safety, file tracking
- Algorithms: Advanced analytics, centrality, path finding
- Traversal: DFS, BFS, layer analysis, connectivity analysis  
- Serialization: JSON, DOT, GraphML export/import
"""

import logging
from functools import lru_cache
from typing import Any, Dict

from .rustworkx_core import RustworkxGraphCore
from .algorithms import GraphAlgorithmsMixin
from .traversal import GraphTraversalMixin
from .serialization import GraphSerializationMixin
from ..universal_graph import CacheConfig

logger = logging.getLogger(__name__)


class RustworkxCodeGraph(
    RustworkxGraphCore,
    GraphAlgorithmsMixin,
    GraphTraversalMixin,
    GraphSerializationMixin
):
    """
    Thread-safe, high-performance code graph using rustworkx for advanced analytics.

    Provides:
    - 10-100x faster graph operations
    - Advanced graph algorithms (centrality, shortest paths, cycles)
    - Memory-efficient storage for large codebases
    - Thread-safe operations with proper locking
    - Corruption-resistant index mapping
    - Comprehensive export/import capabilities
    """

    def _clear_method_caches(self):
        """Clear all LRU caches to prevent stale data."""
        methods_with_cache = [
            'find_nodes_by_name', 'get_nodes_by_type', 'calculate_centrality',
            'calculate_pagerank', 'calculate_closeness_centrality',
            'calculate_eigenvector_centrality', 'get_statistics'
        ]
        for method_name in methods_with_cache:
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                if hasattr(method, 'cache_clear'):
                    method.cache_clear()

    @lru_cache(maxsize=CacheConfig.MEDIUM_CACHE)
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics with LRU caching."""
        # Get basic statistics from core
        stats = self.get_basic_statistics()
        
        # Add advanced metrics
        is_dag = self.is_directed_acyclic()
        num_cycles = len(self.detect_cycles()) if not is_dag else 0
        
        stats.update({
            "is_directed_acyclic": is_dag,
            "num_cycles": num_cycles,
            "density": stats["total_relationships"] / (stats["total_nodes"] * (stats["total_nodes"] - 1)) if stats["total_nodes"] > 1 else 0,
            "average_degree": (2 * stats["total_relationships"]) / stats["total_nodes"] if stats["total_nodes"] > 0 else 0,
        })

        logger.debug(f"get_statistics: {stats['total_nodes']} nodes, {stats['total_relationships']} relationships, {stats['total_files']} files")
        return stats