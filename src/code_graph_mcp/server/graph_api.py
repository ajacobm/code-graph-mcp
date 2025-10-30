"""
Graph Query API Routes

FastAPI routes for graph traversal, search, and analysis endpoints.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from ..server.analysis_engine import UniversalAnalysisEngine
from ..universal_graph import NodeType
from ..graph.query_response import (
    NodeResponse,
    RelationshipResponse,
    TraversalResponse,
    SearchResultResponse,
    CallChainResponse,
    GraphStatsResponse,
    SeamResponse,
    ErrorResponse,
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

    return router
