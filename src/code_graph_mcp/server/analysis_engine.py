"""
Code Analysis Engine

Core analysis orchestration class that coordinates code parsing,
graph building, and provides unified interface for code insights.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..file_watcher import DebouncedFileWatcher
from ..universal_ast import UniversalASTAnalyzer
from ..universal_graph import NodeType, RelationshipType

logger = logging.getLogger(__name__)


class UniversalAnalysisEngine:
    """Code analysis engine with comprehensive project analysis capabilities."""

    def __init__(self, project_root: Path, enable_file_watcher: bool = True, redis_config: Optional[any] = None, enable_redis_cache: bool = True):
        self.project_root = project_root
        
        # Import here to avoid circular imports
        from ..redis_cache import RedisConfig
        
        # Set up Redis configuration
        if enable_redis_cache:
            if redis_config is None:
                # Use default Redis config if enabled but no config provided
                redis_config = RedisConfig()
            elif isinstance(redis_config, str):
                # If redis_config is a URL string, create RedisConfig with that URL
                redis_config = RedisConfig(url=redis_config)
            # If redis_config is already a RedisConfig object, use it as-is
        
        self.analyzer = UniversalASTAnalyzer(project_root, redis_config=redis_config, enable_redis_cache=enable_redis_cache)
        self.parser = self.analyzer.parser
        self.graph = self.parser.graph
        self._is_analyzed = False
        self._last_analysis_time = 0

        # File watcher for automatic updates
        self._file_watcher: Optional[DebouncedFileWatcher] = None
        self._enable_file_watcher = enable_file_watcher

        # Prevent concurrent re-analyses
        self._analysis_lock = asyncio.Lock()
        self._analysis_task: Optional[asyncio.Task] = None

    def _clear_all_caches(self):
        """Clear all LRU caches to ensure fresh data."""
        logger.info("Clearing all LRU caches...")

        # Define cache methods to clear
        cache_methods = [
            (self.analyzer, 'analyze_complexity'),
            (self.graph, 'find_nodes_by_name'),
            (self.graph, 'get_nodes_by_type'),
            (self.graph, 'calculate_centrality'),
            (self.graph, 'calculate_pagerank'),
            (self.graph, 'calculate_closeness_centrality'),
            (self.graph, 'calculate_eigenvector_centrality'),
        ]

        cleared_count = 0
        for obj, method_name in cache_methods:
            try:
                method = getattr(obj, method_name, None)
                if method and hasattr(method, 'cache_clear'):
                    method.cache_clear()
                    cleared_count += 1
                    logger.debug(f"Cleared cache for {method_name}")
            except Exception as e:
                logger.warning(f"Failed to clear cache for {method_name}: {e}")

        # Clear analysis cache
        try:
            if hasattr(self.analyzer, '_analysis_cache'):
                self.analyzer._analysis_cache.clear()
                cleared_count += 1
        except Exception as e:
            logger.warning(f"Failed to clear analysis cache: {e}")

        logger.info(f"Cleared {cleared_count} caches")

    async def _analyze_project(self):
        """Async wrapper for project analysis."""
        try:
            # Initialize cache if needed
            if self.analyzer.cache_manager:
                await self.analyzer.initialize_cache()
            
            return await self.analyzer.analyze_project()
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    async def _on_file_change(self, changed_files: Optional[List[str]] = None):
        """Callback for file watcher - triggers incremental re-analysis."""
        logger.info("File changes detected by watcher, triggering incremental re-analysis...")

        # Cancel any existing analysis task
        if self._analysis_task and not self._analysis_task.done():
            logger.info("Cancelling existing analysis task...")
            self._analysis_task.cancel()

        # If we have specific changed files, do incremental update
        if changed_files and self._is_analyzed:
            logger.info(f"Performing incremental update for {len(changed_files)} files")
            self._analysis_task = asyncio.create_task(self._incremental_update(changed_files))
        else:
            # Full re-analysis
            self._is_analyzed = False
            self._last_analysis_time = 0
            self._analysis_task = asyncio.create_task(self._ensure_analyzed())

    async def _incremental_update(self, changed_files: List[str]):
        """Perform incremental update for specific changed files."""
        async with self._analysis_lock:
            try:
                logger.info(f"Starting incremental update for {len(changed_files)} files")

                # Remove nodes from changed files
                removed_count = 0
                for file_path in changed_files:
                    count = self.graph.remove_file_nodes(file_path)
                    removed_count += count

                logger.info(f"Removed {removed_count} nodes from changed files")

                # Re-parse changed files
                for file_path in changed_files:
                    if Path(file_path).exists():
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.parser.parse_file, Path(file_path)
                        )
                        self.graph.mark_file_processed(file_path)

                logger.info("Incremental update completed successfully")

            except Exception as e:
                logger.error(f"Incremental update failed: {e}")
                # Fall back to full re-analysis
                self._is_analyzed = False
                await self._ensure_analyzed()

    async def start_file_watcher(self):
        """Start the file watcher for automatic updates."""
        if not self._enable_file_watcher or self._file_watcher:
            return

        try:
            self._file_watcher = DebouncedFileWatcher(
                project_root=self.project_root,
                callback=self._on_file_change,
                debounce_delay=2.0,  # 2 second debounce
                should_ignore_path=self.parser._should_ignore_path,
                supported_extensions=set(self.parser.registry.get_supported_extensions())
            )
            await self._file_watcher.start()
            logger.info("File watcher started successfully")
        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")
            self._file_watcher = None

    async def stop_file_watcher(self):
        """Stop the file watcher."""
        if self._file_watcher:
            await self._file_watcher.stop()
            self._file_watcher = None
            logger.info("File watcher stopped")

    def _should_reanalyze(self) -> bool:
        """Check if project should be re-analyzed based on file changes."""
        if not self._is_analyzed:
            return True

        # Check if any source files have been modified since last analysis
        try:
            latest_mtime = 0
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file() and not self.parser._should_ignore_path(file_path, self.project_root):
                    if file_path.suffix.lower() in self.parser.registry.get_supported_extensions():
                        mtime = file_path.stat().st_mtime
                        latest_mtime = max(latest_mtime, mtime)

            return latest_mtime > self._last_analysis_time
        except Exception as e:
            logger.warning(f"Error checking file modification times: {e}")
            return False

    async def _ensure_analyzed(self):
        """Ensure the project has been analyzed."""
        async with self._analysis_lock:
            # Double-check if we still need to re-analyze (another task might have completed it)
            if self._should_reanalyze():
                logger.info("Re-analyzing project due to file changes or first run...")

                # Clear all caches before re-analysis
                self._clear_all_caches()

                # Run the analysis directly (now it's async)
                try:
                    # Add timeout to prevent hanging
                    await asyncio.wait_for(
                        self._analyze_project(),
                        timeout=300.0  # 5 minute timeout
                    )
                    self._is_analyzed = True
                    self._last_analysis_time = time.time()
                    logger.info("Analysis completed successfully")

                    # Start file watcher after first successful analysis
                    if not self._file_watcher:
                        await self.start_file_watcher()
                except asyncio.TimeoutError:
                    logger.error("Analysis timed out after 5 minutes")
                    raise Exception("Project analysis timed out - project may be too large")
            else:
                logger.debug("Using cached analysis results")

    async def force_reanalysis(self):
        """Force a complete re-analysis, clearing all caches."""
        logger.info("Forcing complete re-analysis...")
        self._is_analyzed = False
        self._last_analysis_time = 0
        await self._ensure_analyzed()

    def get_file_watcher_stats(self) -> Dict[str, Any]:
        """Get file watcher statistics."""
        if not self._file_watcher:
            return {
                "enabled": self._enable_file_watcher,
                "running": False,
                "stats": None
            }

        return {
            "enabled": self._enable_file_watcher,
            "running": self._file_watcher.is_running,
            "stats": self._file_watcher.get_stats()
        }

    async def get_project_stats(self) -> Dict[str, Any]:
        """Get comprehensive project statistics."""
        logger.info(f"BEFORE _ensure_analyzed: graph has {len(self.graph.nodes)} nodes")
        await self._ensure_analyzed()
        logger.info(f"AFTER _ensure_analyzed: graph has {len(self.graph.nodes)} nodes")
        stats = self.graph.get_statistics()
        logger.info(f"get_statistics returned: {stats.get('total_nodes', 0)} nodes")

        return {
            "total_files": stats.get("total_files", 0),
            "total_nodes": stats.get("total_nodes", 0),
            "total_relationships": stats.get("total_relationships", 0),
            "node_types": stats.get("node_types", {}),
            "languages": stats.get("languages", {}),
            "last_analysis": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "file_watcher": self.get_file_watcher_stats(),
        }

    async def cleanup(self):
        """Clean up resources, including stopping the file watcher."""
        logger.info("Cleaning up analysis engine...")

        # Cancel any running analysis task
        if self._analysis_task and not self._analysis_task.done():
            logger.info("Cancelling running analysis task...")
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass

        await self.stop_file_watcher()
        
        # Cleanup cache resources
        if self.analyzer:
            await self.analyzer.cleanup_cache()

    # Analysis API methods
    
    async def find_symbol_definition(self, symbol: str) -> List[Dict[str, Any]]:
        """Find definition of a symbol using UniversalGraph."""
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if len(symbol) > 200:
            raise ValueError("Symbol name too long (max 200 characters)")
        if not symbol.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Symbol contains invalid characters")

        await self._ensure_analyzed()

        # Find nodes by name (partial match for better results)
        nodes = self.graph.find_nodes_by_name(symbol, exact_match=False)
        results = []

        for node in nodes:
            results.append({
                "name": node.name,
                "type": node.node_type.value,
                "file": node.location.file_path,
                "line": node.location.start_line,
                "complexity": getattr(node, 'complexity', 0),
                "documentation": getattr(node, 'docstring', ''),
                "full_path": node.location.file_path,
            })

        return results

    async def find_symbol_references(self, symbol: str) -> List[Dict[str, Any]]:
        """Find all references to a symbol using UniversalGraph."""
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        if len(symbol) > 200:
            raise ValueError("Symbol name too long (max 200 characters)")
        if not symbol.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Symbol contains invalid characters")

        await self._ensure_analyzed()

        # Find the symbol definition first
        definition_nodes = self.graph.find_nodes_by_name(symbol, exact_match=False)
        results = []

        for def_node in definition_nodes:
            # Get all relationships pointing to this node
            relationships = self.graph.get_relationships_to(def_node.id)

            for rel in relationships:
                if rel.relationship_type == RelationshipType.REFERENCES:
                    source_node = self.graph.get_node(rel.source_id)
                    if source_node:
                        results.append({
                            "reference_type": "references",
                            "file": source_node.location.file_path,
                            "line": source_node.location.start_line,
                            "context": source_node.name,
                            "referencing_symbol": source_node.name,
                        })

        return results

    async def find_function_callers(self, function_name: str) -> List[Dict[str, Any]]:
        """Find all functions that call the specified function."""
        await self._ensure_analyzed()

        # Find function nodes
        function_nodes = [
            node for node in self.graph.find_nodes_by_name(function_name, exact_match=False)
            if node.node_type == NodeType.FUNCTION
        ]

        results = []
        for func_node in function_nodes:
            # Get all CALLS relationships pointing to this function
            relationships = self.graph.get_relationships_to(func_node.id)

            for rel in relationships:
                if rel.relationship_type == RelationshipType.CALLS:
                    caller_node = self.graph.get_node(rel.source_id)
                    if caller_node:
                        results.append({
                            "caller": caller_node.name,
                            "caller_type": caller_node.node_type.value,
                            "file": caller_node.location.file_path,
                            "line": caller_node.location.start_line,
                            "target_function": function_name,
                        })

        return results

    async def find_function_callees(self, function_name: str) -> List[Dict[str, Any]]:
        """Find all functions called by the specified function."""
        await self._ensure_analyzed()

        # Find the function node
        function_nodes = [
            node for node in self.graph.find_nodes_by_name(function_name, exact_match=False)
            if node.node_type == NodeType.FUNCTION
        ]

        results = []
        for func_node in function_nodes:
            # Get all CALLS relationships from this function
            relationships = self.graph.get_relationships_from(func_node.id)

            for rel in relationships:
                if rel.relationship_type == RelationshipType.CALLS:
                    callee_node = self.graph.get_node(rel.target_id)
                    if callee_node:
                        results.append({
                            "callee": callee_node.name,
                            "callee_type": callee_node.node_type.value,
                            "file": callee_node.location.file_path,
                            "line": callee_node.location.start_line,
                            "call_line": func_node.location.start_line,  # Line where the call happens
                        })

        return results

    async def analyze_complexity(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Analyze code complexity using UniversalASTAnalyzer."""
        await self._ensure_analyzed()

        complexity_data = self.analyzer.analyze_complexity(threshold)
        results = []

        # Convert the complexity analysis to the expected format
        for item in complexity_data.get("high_complexity_functions", []):
            risk_level = "high" if item["complexity"] > 20 else "moderate" if item["complexity"] > 10 else "low"
            results.append({
                "name": item["name"],
                "type": item.get("type", "function"),
                "complexity": item["complexity"],
                "risk_level": risk_level,
                "file": item["file"],
                "line": item["line"],
            })

        return results

    async def get_dependency_graph(self) -> Dict[str, Any]:
        """Get dependency analysis using rustworkx advanced algorithms."""
        await self._ensure_analyzed()

        deps = self.analyzer.analyze_dependencies()

        # Enhanced analysis with rustworkx
        is_dag = self.graph.is_directed_acyclic()
        cycles = self.graph.detect_cycles() if not is_dag else []
        components = self.graph.get_strongly_connected_components()

        return {
            "total_files": len(deps.get("files", [])),
            "total_dependencies": len(deps.get("imports", [])),
            "dependencies": deps.get("dependency_graph", {}),
            "circular_dependencies": cycles,
            "is_directed_acyclic": is_dag,
            "strongly_connected_components": len(components),
            "graph_density": self.graph.get_statistics().get("density", 0),
        }

    async def get_code_insights(self) -> Dict[str, Any]:
        """Get comprehensive code insights using advanced rustworkx analytics."""
        await self._ensure_analyzed()

        # Calculate multiple centrality measures for comprehensive analysis
        betweenness_centrality = self.graph.calculate_centrality()
        pagerank = self.graph.calculate_pagerank(alpha=0.85, max_iter=100, tol=1e-6)
        closeness_centrality = self.graph.calculate_closeness_centrality()
        eigenvector_centrality = self.graph.calculate_eigenvector_centrality()

        # Find critical structural elements
        articulation_points = self.graph.find_articulation_points()
        bridges = self.graph.find_bridges()

        # Sort and get top elements for each metric
        sorted_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        sorted_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
        sorted_closeness = sorted(closeness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        sorted_eigenvector = sorted(eigenvector_centrality.items(), key=lambda x: x[1], reverse=True)[:10]

        # Get graph statistics
        stats = self.graph.get_statistics()

        return {
            "centrality_analysis": {
                "betweenness_centrality": [
                    {
                        "node_id": node_id,
                        "score": score,
                        "node_name": (node.name if (node := self.graph.get_node(node_id)) is not None else "Unknown"),
                        "node_type": (node.node_type.value if (node := self.graph.get_node(node_id)) is not None else "unknown")
                    }
                    for node_id, score in sorted_betweenness
                ],
                "pagerank": [
                    {
                        "node_id": node_id,
                        "score": score,
                        "node_name": (node.name if (node := self.graph.get_node(node_id)) is not None else "Unknown"),
                        "node_type": (node.node_type.value if (node := self.graph.get_node(node_id)) is not None else "unknown")
                    }
                    for node_id, score in sorted_pagerank
                ],
                "closeness_centrality": [
                    {
                        "node_id": node_id,
                        "score": score,
                        "node_name": (node.name if (node := self.graph.get_node(node_id)) is not None else "Unknown")
                    }
                    for node_id, score in sorted_closeness
                ],
                "eigenvector_centrality": [
                    {
                        "node_id": node_id,
                        "score": score,
                        "node_name": (node.name if (node := self.graph.get_node(node_id)) is not None else "Unknown")
                    }
                    for node_id, score in sorted_eigenvector
                ]
            },
            "structural_analysis": {
                "articulation_points": [
                    {
                        "node_id": node_id,
                        "node_name": (node.name if (node := self.graph.get_node(node_id)) is not None else "Unknown"),
                        "critical_impact": "Removal would disconnect the graph"
                    }
                    for node_id in articulation_points
                ],
                "bridges": [
                    {
                        "source": source_id,
                        "target": target_id,
                        "source_name": (source_node.name if (source_node := self.graph.get_node(source_id)) is not None else "Unknown"),
                        "target_name": (target_node.name if (target_node := self.graph.get_node(target_id)) is not None else "Unknown"),
                        "critical_impact": "Removal would disconnect components"
                    }
                    for source_id, target_id in bridges
                ]
            },
            "graph_statistics": stats,
            "topology_analysis": {
                "is_directed_acyclic": self.graph.is_directed_acyclic(),
                "num_cycles": len(self.graph.detect_cycles()),
                "strongly_connected_components": len(self.graph.get_strongly_connected_components()),
                "num_articulation_points": len(articulation_points),
                "num_bridges": len(bridges)
            },
            # Legacy fields for backward compatibility
            "most_central_nodes": [
                {
                    "node_id": node_id,
                    "centrality_score": score,
                    "node_name": (node.name if (node := self.graph.get_node(node_id)) is not None else "Unknown")
                }
                for node_id, score in sorted_betweenness
            ],
            "most_influential_nodes": [
                {
                    "node_id": node_id,
                    "pagerank_score": score,
                    "node_name": (node.name if (node := self.graph.get_node(node_id)) is not None else "Unknown")
                }
                for node_id, score in sorted_pagerank
            ]
        }