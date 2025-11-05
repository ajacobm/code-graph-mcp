"""
Graph Query API Routes

FastAPI routes for graph traversal, search, and analysis endpoints.
"""

import logging
import time
from typing import Optional, Dict, Any

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from ..server.analysis_engine import UniversalAnalysisEngine
from ..universal_graph import NodeType
from ..entry_detector import EntryDetector
from ..graph.query_response import (
    NodeResponse,
    RelationshipResponse,
    TraversalResponse,
    SearchResultResponse,
    CallChainResponse,
    GraphStatsResponse,
    SeamResponse,
    EntryPointResponse,
)

logger = logging.getLogger(__name__)


class TraversalQuery(BaseModel):
    """Request model for graph traversal."""
    start_node: str = Field(..., description="Starting node ID")
    query_type: str = Field("bfs", description="Traversal type: 'dfs', 'bfs', 'call_chain'")
    max_depth: int = Field(10, ge=1, le=100, description="Maximum traversal depth")
    include_seams: bool = Field(True, description="Follow SEAM (cross-language) edges")


class NodeSearchQuery(BaseModel):
    """Request model for node search."""
    name: Optional[str] = Field(None, description="Node name pattern")
    language: Optional[str] = Field(None, description="Programming language filter")
    node_type: Optional[str] = Field(None, description="Node type filter (function, class, etc)")
    limit: int = Field(50, ge=1, le=500, description="Result limit")


def create_graph_api_router(engine: UniversalAnalysisEngine) -> APIRouter:
    """Create FastAPI router with graph query endpoints."""
    
    router = APIRouter(prefix="/api/graph", tags=["graph"])

    @router.get("/stats", response_model=Dict[str, Any])
    async def get_graph_stats():
        """Get comprehensive graph statistics."""
        try:
            start_time = time.time()
            
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            graph = engine.analyzer.graph
            
            node_types = {}
            for node in graph.nodes.values():
                ntype = getattr(node, 'node_type', 'unknown')
                ntype_str = ntype.value if hasattr(ntype, 'value') else str(ntype)
                node_types[ntype_str] = node_types.get(ntype_str, 0) + 1
            
            rel_types = {}
            for rel in graph.relationships.values():
                rtype = getattr(rel, 'relationship_type', 'unknown')
                rtype_str = rtype.value if hasattr(rtype, 'value') else str(rtype)
                rel_types[rtype_str] = rel_types.get(rtype_str, 0) + 1
            
            languages = {}
            for node in graph.nodes.values():
                lang = getattr(node, 'language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
            
            seam_count = rel_types.get('seam', 0)
            
            # Get top functions by complexity
            top_functions = []
            function_nodes = [node for node in graph.nodes.values() 
                            if getattr(node, 'node_type', None) == NodeType.FUNCTION]
            for node in sorted(function_nodes, key=lambda n: getattr(n, 'complexity', 0), reverse=True)[:10]:
                top_functions.append({
                    'id': node.id,
                    'name': getattr(node, 'name', ''),
                    'complexity': getattr(node, 'complexity', 0),
                    'language': getattr(node, 'language', '')
                })
            
            response = GraphStatsResponse(
                total_nodes=len(graph.nodes),
                total_relationships=len(graph.relationships),
                node_types=node_types,
                relationship_types=rel_types,
                languages=languages,
                seam_count=seam_count,
                complexity_distribution={},
                execution_time_ms=(time.time() - start_time) * 1000
            )
            result = response.to_dict()
            result['top_functions'] = top_functions
            return result
        
        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/nodes/{node_id}", response_model=Dict[str, Any])
    async def get_node(node_id: str):
        """Get detailed node information."""
        try:
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            graph = engine.analyzer.graph
            node = graph.nodes.get(node_id)
            
            if not node:
                raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
            
            location = getattr(node, 'location', None)
            response = NodeResponse(
                id=node_id,
                name=getattr(node, 'name', ''),
                type=getattr(node, 'node_type', ''),
                language=getattr(node, 'language', ''),
                file_path=location.file_path if location else None,
                start_line=location.start_line if location else None,
                end_line=location.end_line if location else None,
                complexity=getattr(node, 'complexity', 0),
                metadata={
                    'docstring': getattr(node, 'docstring', ''),
                    'line_count': getattr(node, 'line_count', 0),
                }
            )
            return response.to_dict()
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Node fetch failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/traverse", response_model=Dict[str, Any])
    async def traverse_graph(query: TraversalQuery):
        """Traverse graph starting from a node."""
        try:
            start_time = time.time()
            
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            graph = engine.analyzer.graph
            
            if query.start_node not in graph.nodes:
                raise HTTPException(status_code=404, detail=f"Start node not found: {query.start_node}")
            
            node_list = []
            edge_list = []
            
            if query.query_type == "dfs":
                nodes = graph.depth_first_search(query.start_node)
                node_list = nodes[:query.max_depth] if query.max_depth else nodes
            
            elif query.query_type == "bfs":
                nodes = graph.breadth_first_search(query.start_node)
                node_list = nodes[:query.max_depth] if query.max_depth else nodes
            
            elif query.query_type == "call_chain":
                result = graph.dfs_traversal_with_depth(
                    query.start_node,
                    max_depth=query.max_depth,
                    include_seams=query.include_seams
                )
                nodes_by_depth = result.get('nodes_by_depth', {})
                for depth_nodes in nodes_by_depth.values():
                    node_list.extend(depth_nodes)
            
            else:
                raise HTTPException(status_code=400, detail=f"Unknown query type: {query.query_type}")
            
            for node_id in node_list:
                node = graph.nodes.get(node_id)
                if node:
                    location = getattr(node, 'location', None)
                    node_resp = NodeResponse(
                        id=node_id,
                        name=getattr(node, 'name', ''),
                        type=getattr(node, 'node_type', ''),
                        language=getattr(node, 'language', ''),
                        file_path=location.file_path if location else None,
                        start_line=location.start_line if location else None,
                        complexity=getattr(node, 'complexity', 0)
                    )
                    edge_list.append(node_resp)
            
            stats = {
                "nodes_traversed": len(node_list),
                "max_depth": query.max_depth,
                "include_seams": query.include_seams,
            }
            
            response = TraversalResponse(
                nodes=edge_list,
                edges=[],
                stats=stats,
                execution_time_ms=(time.time() - start_time) * 1000,
                query_type=query.query_type,
                start_node_id=query.start_node,
                max_depth=query.max_depth
            )
            return response.to_dict()
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Traversal failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/nodes/search", response_model=Dict[str, Any])
    async def search_nodes(
        name: Optional[str] = Query(None),
        language: Optional[str] = Query(None),
        node_type: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=500)
    ):
        """Search for nodes by name, language, or type."""
        try:
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            graph = engine.analyzer.graph
            results = []
            
            for node_id, node in graph.nodes.items():
                if len(results) >= limit:
                    break
                
                if name and name.lower() not in getattr(node, 'name', '').lower():
                    continue
                
                if language and getattr(node, 'language', '') != language:
                    continue
                
                if node_type:
                    ntype = getattr(node, 'node_type', '')
                    ntype_str = ntype.value if hasattr(ntype, 'value') else str(ntype)
                    if ntype_str != node_type:
                        continue
                
                location = getattr(node, 'location', None)
                node_resp = NodeResponse(
                    id=node_id,
                    name=getattr(node, 'name', ''),
                    type=getattr(node, 'node_type', ''),
                    language=getattr(node, 'language', ''),
                    file_path=location.file_path if location else None,
                    start_line=location.start_line if location else None,
                    complexity=getattr(node, 'complexity', 0)
                )
                results.append(node_resp)
            
            response = SearchResultResponse(
                results=results,
                total_count=len(results),
                query=f"name={name},language={language},type={node_type}"
            )
            return response.to_dict()
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/seams", response_model=Dict[str, Any])
    async def get_seams(limit: int = Query(100, ge=1, le=1000)):
        """Get all cross-language (SEAM) relationships."""
        try:
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            graph = engine.analyzer.graph
            seams = []
            
            for rel_id, rel in list(graph.relationships.items())[:limit]:
                rel_type = getattr(rel, 'relationship_type', None)
                rel_type_str = rel_type.value if hasattr(rel_type, 'value') else str(rel_type)
                
                if rel_type_str != 'seam':
                    continue
                
                source_id = getattr(rel, 'source_id', '')
                target_id = getattr(rel, 'target_id', '')
                
                source = graph.nodes.get(source_id)
                target = graph.nodes.get(target_id)
                
                seam_resp = SeamResponse(
                    id=rel_id,
                    source_id=source_id,
                    source_name=getattr(source, 'name', '') if source else '',
                    source_language=getattr(source, 'language', '') if source else '',
                    target_id=target_id,
                    target_name=getattr(target, 'name', '') if target else '',
                    target_language=getattr(target, 'language', '') if target else ''
                )
                seams.append(seam_resp)
            
            return {
                "seams": [s.to_dict() for s in seams],
                "total_count": len(seams)
            }
        
        except Exception as e:
            logger.error(f"Seam query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/call-chain/{start_node}", response_model=Dict[str, Any])
    async def get_call_chain(
        start_node: str,
        follow_seams: bool = Query(True),
        max_depth: int = Query(20, ge=1, le=100)
    ):
        """Get call chain from a starting node."""
        try:
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            graph = engine.analyzer.graph
            
            if start_node not in graph.nodes:
                raise HTTPException(status_code=404, detail=f"Start node not found: {start_node}")
            
            start_time = time.time()
            
            chain_edges = graph.find_call_chain(
                start_node,
                follow_seams=follow_seams,
                max_depth=max_depth
            )
            
            chain_nodes = []
            visited = set()
            
            for source_id, target_id in chain_edges:
                if source_id not in visited:
                    node = graph.nodes.get(source_id)
                    if node:
                        location = getattr(node, 'location', None)
                        chain_nodes.append(NodeResponse(
                            id=source_id,
                            name=getattr(node, 'name', ''),
                            type=getattr(node, 'node_type', ''),
                            language=getattr(node, 'language', ''),
                            file_path=location.file_path if location else None,
                            complexity=getattr(node, 'complexity', 0)
                        ))
                        visited.add(source_id)
                
                if target_id not in visited:
                    node = graph.nodes.get(target_id)
                    if node:
                        location = getattr(node, 'location', None)
                        chain_nodes.append(NodeResponse(
                            id=target_id,
                            name=getattr(node, 'name', ''),
                            type=getattr(node, 'node_type', ''),
                            language=getattr(node, 'language', ''),
                            file_path=location.file_path if location else None,
                            complexity=getattr(node, 'complexity', 0)
                        ))
                        visited.add(target_id)
            
            seam_count = 0
            edges_resp = []
            for source_id, target_id in chain_edges:
                rel = graph.find_relationship(source_id, target_id)
                rel_type = getattr(rel, 'relationship_type', None)
                rel_type_str = rel_type.value if hasattr(rel_type, 'value') else str(rel_type)
                
                if rel_type_str == 'seam':
                    seam_count += 1
                
                edges_resp.append(RelationshipResponse(
                    id=f"{source_id}-{target_id}",
                    source_id=source_id,
                    target_id=target_id,
                    type=rel_type_str,
                    is_seam=(rel_type_str == 'seam')
                ))
            
            response = CallChainResponse(
                chain=chain_nodes,
                edges=edges_resp,
                has_seams=(seam_count > 0),
                seam_count=seam_count,
                total_hops=len(chain_edges),
                execution_time_ms=(time.time() - start_time) * 1000
            )
            return response.to_dict()
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Call chain query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/query/callers", response_model=Dict[str, Any])
    async def find_callers(symbol: str = Query(..., description="Function name to find callers for")):
        """Find all functions that call the specified function."""
        try:
            if not engine:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            start_time = time.time()
            callers = await engine.find_function_callers(symbol)
            
            results = []
            for caller in callers:
                results.append({
                    "caller_id": f"{caller['file']}:{caller['caller']}",
                    "caller": caller['caller'],
                    "caller_type": caller['caller_type'],
                    "file": caller['file'],
                    "line": caller['line'],
                    "target_function": caller['target_function']
                })
            
            return {
                "symbol": symbol,
                "total_callers": len(results),
                "callers": results,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            logger.error(f"Find callers failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/query/callees", response_model=Dict[str, Any])
    async def find_callees(symbol: str = Query(..., description="Function name to find callees for")):
        """Find all functions called by the specified function."""
        try:
            if not engine:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            start_time = time.time()
            callees = await engine.find_function_callees(symbol)
            
            results = []
            for callee in callees:
                results.append({
                    "callee_id": f"{callee['file']}:{callee['callee']}",
                    "callee": callee['callee'],
                    "callee_type": callee['callee_type'],
                    "file": callee['file'],
                    "line": callee['line'],
                    "call_line": callee['call_line']
                })
            
            return {
                "symbol": symbol,
                "total_callees": len(results),
                "callees": results,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            logger.error(f"Find callees failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/query/references", response_model=Dict[str, Any])
    async def find_references(symbol: str = Query(..., description="Symbol name to find references for")):
        """Find all references to a symbol."""
        try:
            if not engine:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            start_time = time.time()
            references = await engine.find_symbol_references(symbol)
            
            results = []
            for ref in references:
                results.append({
                    "reference_id": f"{ref['file']}:{ref['line']}",
                    "referencing_symbol": ref['referencing_symbol'],
                    "file": ref['file'],
                    "line": ref['line'],
                    "context": ref['context']
                })
            
            return {
                "symbol": symbol,
                "total_references": len(results),
                "references": results,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            logger.error(f"Find references failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/categories/{category}")
    async def get_nodes_by_category(
        category: str,
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0)
    ):
        """Get nodes by category: entry_points, hubs, or leaves."""
        try:
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            graph = engine.analyzer.graph
            start_time = time.time()
            
            # Calculate node importance metrics
            in_degree = {}
            out_degree = {}
            
            for node_id in graph.nodes:
                in_degree[node_id] = len([r for r in graph.relationships.values() if r.target_id == node_id])
                out_degree[node_id] = len([r for r in graph.relationships.values() if r.source_id == node_id])
            
            categorized = []
            
            if category == "entry_points":
                # Nodes with 0 incoming edges
                categorized = [
                    node for node_id, node in graph.nodes.items()
                    if in_degree.get(node_id, 0) == 0
                ]
            elif category == "hubs":
                # Nodes with high degree centrality (both in and out)
                degree_scores = [
                    (node_id, in_degree.get(node_id, 0) + out_degree.get(node_id, 0))
                    for node_id in graph.nodes
                ]
                degree_scores.sort(key=lambda x: x[1], reverse=True)
                top_25_percentile = max(1, len(degree_scores) // 4)
                hub_ids = {node_id for node_id, _ in degree_scores[:top_25_percentile]}
                categorized = [
                    graph.nodes[node_id] for node_id in hub_ids
                ]
            elif category == "leaves":
                # Nodes with 0 outgoing edges
                categorized = [
                    node for node_id, node in graph.nodes.items()
                    if out_degree.get(node_id, 0) == 0
                ]
            else:
                raise HTTPException(status_code=400, detail=f"Unknown category: {category}")
            
            # Apply pagination
            total = len(categorized)
            paginated = categorized[offset:offset + limit]
            
            # Format response
            nodes = []
            for node in paginated:
                node_id = node.node_id if hasattr(node, 'node_id') else str(node.id)
                location = getattr(node, 'location', None)
                file_path = location.file_path if location else ""
                line = location.start_line if location else 0
                
                nodes.append({
                    "id": node_id,
                    "name": node.name,
                    "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                    "language": node.language,
                    "file_path": file_path,
                    "line": line,
                    "complexity": node.complexity,
                    "in_degree": in_degree.get(node_id, 0),
                    "out_degree": out_degree.get(node_id, 0),
                })
            
            return {
                "category": category,
                "total": total,
                "offset": offset,
                "limit": limit,
                "nodes": nodes,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            logger.error(f"Get nodes by category failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/subgraph")
    async def get_subgraph(
        node_id: str = Query(...),
        depth: int = Query(2, ge=1, le=10),
        limit: int = Query(100, ge=10, le=1000)
    ):
        """Get focused subgraph around a node with limited depth and node count."""
        try:
            if not engine or not engine.analyzer:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            start_time = time.time()
            graph = engine.analyzer.graph
            
            # Check if node exists
            if node_id not in graph.nodes:
                raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
            
            # BFS traversal with depth and node limit
            from collections import deque
            visited = set()
            queue = deque([(node_id, 0)])
            subgraph_nodes = []
            subgraph_rels = []
            
            while queue and len(visited) < limit:
                current_node_id, current_depth = queue.popleft()
                
                if current_node_id in visited or current_depth > depth:
                    continue
                
                visited.add(current_node_id)
                node = graph.nodes.get(current_node_id)
                if node:
                    subgraph_nodes.append({
                        "id": node.node_id if hasattr(node, 'node_id') else str(node.id),
                        "name": node.name,
                        "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                        "language": node.language,
                        "file_path": node.location.file_path if node.location else "",
                        "line": node.location.start_line if node.location else 0,
                        "complexity": node.complexity,
                    })
                
                # Find connected relationships
                if current_depth < depth:
                    for rel in graph.relationships.values():
                        if rel.source_id == current_node_id or rel.target_id == current_node_id:
                            next_node = rel.target_id if rel.source_id == current_node_id else rel.source_id
                            if next_node not in visited and len(visited) < limit:
                                queue.append((next_node, current_depth + 1))
                                subgraph_rels.append({
                                    "id": f"{rel.source_id}-{rel.target_id}",
                                    "source": rel.source_id,
                                    "target": rel.target_id,
                                    "type": rel.relationship_type.value if hasattr(rel.relationship_type, 'value') else str(rel.relationship_type),
                                })
            
            if not subgraph_nodes:
                raise HTTPException(status_code=404, detail=f"No connections found for {node_id}")
            
            return {
                "node_id": node_id,
                "depth": depth,
                "nodes": subgraph_nodes,
                "relationships": subgraph_rels,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        
        except Exception as e:
            logger.error(f"Get subgraph failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/debug/analysis")
    async def debug_analysis():
        """Debug endpoint showing analysis status and file information."""
        try:
            if not engine or not engine.analyzer:
                return {
                    "status": "not_initialized",
                    "message": "Analysis engine not initialized",
                    "project_root": str(engine.project_root) if engine else None
                }
            
            graph = engine.analyzer.graph
            processed_files = getattr(graph, '_processed_files', set())
            cache_manager = getattr(engine.analyzer, 'cache_manager', None)
            
            return {
                "status": "initialized",
                "project_root": str(engine.project_root),
                "graph_nodes": len(graph.nodes),
                "graph_relationships": len(graph.relationships),
                "processed_files_count": len(processed_files),
                "file_watcher_enabled": getattr(engine, '_enable_file_watcher', False),
                "file_watcher_running": bool(getattr(engine, '_file_watcher', None) and getattr(getattr(engine, '_file_watcher', None), 'is_running', False)),
                "is_analyzed": getattr(engine, '_is_analyzed', False),
                "cache_enabled": cache_manager is not None,
                "node_types_sample": {
                    str(node.node_type): sum(1 for n in graph.nodes.values() if n.node_type == node.node_type)
                    for node in list(graph.nodes.values())[:50]
                } if graph.nodes else {},
                "first_10_files": list(processed_files)[:10]
            }
        except Exception as e:
            logger.error(f"Debug analysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/debug/files")
    async def debug_files(limit: int = Query(50, ge=1, le=500)):
        """Debug endpoint showing all processed files and their node counts."""
        try:
            if not engine or not engine.analyzer:
                raise HTTPException(status_code=500, detail="Analysis engine not initialized")
            
            graph = engine.analyzer.graph
            processed_files = getattr(graph, '_processed_files', set())
            
            file_info = []
            for file_path_str in sorted(processed_files)[:limit]:
                file_nodes = [n for n in graph.nodes.values() 
                            if n.location.file_path == file_path_str]
                file_info.append({
                    "file_path": file_path_str,
                    "node_count": len(file_nodes),
                    "node_types": {
                        str(node.node_type): sum(1 for n in file_nodes if n.node_type == node.node_type)
                        for node in file_nodes
                    }
                })
            
            return {
                "total_processed_files": len(processed_files),
                "showing": len(file_info),
                "files": file_info
            }
        except Exception as e:
            logger.error(f"Debug files failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/admin/reanalyze")
    async def admin_reanalyze(force: bool = Query(False)):
        """Force re-analysis of the project."""
        try:
            if not engine:
                raise HTTPException(status_code=500, detail="Analysis engine not initialized")
            
            logger.info(f"Admin reanalysis requested (force={force})")
            start_time = time.time()
            
            await engine.force_reanalysis()
            
            elapsed = time.time() - start_time
            graph = engine.analyzer.graph if engine.analyzer else None
            
            return {
                "status": "success",
                "message": "Re-analysis completed",
                "elapsed_seconds": elapsed,
                "total_nodes": len(graph.nodes) if graph else 0,
                "total_relationships": len(graph.relationships) if graph else 0
            }
        except Exception as e:
            logger.error(f"Admin reanalysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/entry-points", response_model=Dict[str, Any])
    async def get_entry_points(limit: int = Query(50, ge=1, le=500), min_confidence: float = Query(0.5, ge=0.0, le=10.0)):
        """Get detected entry points with confidence scoring."""
        try:
            if not engine or not engine.analyzer or not engine.analyzer.graph:
                raise HTTPException(status_code=500, detail="Analysis engine not ready")
            
            start_time = time.time()
            graph = engine.analyzer.graph
            
            # Initialize entry detector
            detector = EntryDetector()
            
            # Prepare node data and file contents for analysis
            nodes_data = []
            file_contents = {}
            
            # Collect all nodes with their file information
            for node_id, node in graph.nodes.items():
                location = getattr(node, 'location', None)
                file_path = location.file_path if location else ""
                
                if file_path:
                    node_data = {
                        'id': node_id,
                        'name': getattr(node, 'name', ''),
                        'file_path': file_path,
                        'line': location.start_line if location else 0,
                        'complexity': getattr(node, 'complexity', 0),
                        'language': getattr(node, 'language', ''),
                        'type': str(getattr(node, 'node_type', ''))
                    }
                    nodes_data.append(node_data)
                    
                    # Read file content if not already cached
                    if file_path not in file_contents:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_contents[file_path] = f.read()
                        except Exception as e:
                            logger.warning(f"Could not read file {file_path}: {e}")
                            file_contents[file_path] = ""
            
            # Detect entry points
            candidates = detector.detect_entry_points(nodes_data, file_contents)
            
            # Filter by minimum confidence
            filtered_candidates = [c for c in candidates if c.confidence_score >= min_confidence]
            
            # Apply limit
            limited_candidates = filtered_candidates[:limit]
            
            # Convert to response format
            entry_points_response = []
            for candidate in limited_candidates:
                entry_point = EntryPointResponse(
                    id=candidate.node_id,
                    name=candidate.name,
                    file_path=candidate.file_path,
                    language=candidate.language,
                    line_number=candidate.line_number,
                    pattern_matched=candidate.pattern_matched,
                    confidence_score=candidate.confidence_score,
                    complexity=candidate.complexity
                )
                entry_points_response.append(entry_point)
            
            return {
                "entry_points": [ep.to_dict() for ep in entry_points_response],
                "total_count": len(entry_points_response),
                "filtered_count": len(filtered_candidates),
                "min_confidence": min_confidence,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
            
        except Exception as e:
            logger.error(f"Entry points detection failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
