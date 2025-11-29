"""Graph data client for Jupyter notebooks.

Provides unified access to the CodeNav backend API for data science workflows.
Updated for modern Jupyter async support (uses native await, no run_until_complete).

Usage in Jupyter:
    from utils.graph_client import GraphClient
    
    client = GraphClient()
    await client.connect()
    
    # Get graph stats
    stats = await client.get_stats()
    
    # Export filtered graph
    data = await client.export_graph(exclude_tests=True)
    
    # Build NetworkX graph directly
    G = await client.build_networkx_graph()
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import os

import httpx
import networkx as nx
import pandas as pd


@dataclass
class GraphStats:
    """Statistics about the graph."""
    total_nodes: int = 0
    total_relationships: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    node_types: Dict[str, int] = field(default_factory=dict)
    relationship_types: Dict[str, int] = field(default_factory=dict)
    seam_count: int = 0


class GraphClient:
    """
    Unified client for CodeNav graph data operations.
    
    Designed for Jupyter notebooks with native async support.
    Uses the /api/graph/* endpoints from the CodeNav backend.
    """

    def __init__(
        self,
        api_url: str = None,
        timeout: int = 30,
    ):
        """Initialize client with API URL from parameter or environment."""
        self.api_url = api_url or os.getenv("CODENAV_API_URL", "http://localhost:8000")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_url, 
                timeout=self.timeout
            )
        return self._client

    async def connect(self) -> bool:
        """Test connection to the backend API."""
        try:
            resp = await self.client.get("/health")
            if resp.status_code == 200:
                print(f"✅ Connected to CodeNav API at {self.api_url}")
                return True
            else:
                print(f"⚠️  API returned status {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            print("✅ Client closed")

    async def get_stats(self) -> GraphStats:
        """Get high-level graph statistics."""
        resp = await self.client.get("/api/graph/stats")
        resp.raise_for_status()
        data = resp.json()
        
        return GraphStats(
            total_nodes=data.get("total_nodes", 0),
            total_relationships=data.get("total_relationships", 0),
            languages=data.get("languages", {}),
            node_types=data.get("node_types", {}),
            relationship_types=data.get("relationship_types", {}),
            seam_count=data.get("seam_count", 0),
        )

    async def export_graph(
        self,
        limit: int = 10000,
        language: str = None,
        node_type: str = None,
        exclude_stdlib: bool = True,
        exclude_tests: bool = True,
        include_private: bool = True,
        include_dunder: bool = True,
    ) -> Dict[str, Any]:
        """
        Export graph data for visualization with filtering.
        
        Args:
            limit: Maximum nodes to return
            language: Filter by programming language (e.g., 'Python')
            node_type: Filter by node type (e.g., 'function', 'class')
            exclude_stdlib: Exclude standard library imports
            exclude_tests: Exclude test files and directories
            include_private: Include private symbols (_prefix)
            include_dunder: Include Python dunder methods (__x__)
            
        Returns:
            Dict with 'nodes', 'links', and 'stats' keys
        """
        params = {
            "limit": limit,
            "exclude_stdlib": str(exclude_stdlib).lower(),
            "exclude_tests": str(exclude_tests).lower(),
            "include_private": str(include_private).lower(),
            "include_dunder": str(include_dunder).lower(),
        }
        if language:
            params["language"] = language
        if node_type:
            params["node_type"] = node_type
            
        resp = await self.client.get("/api/graph/export", params=params)
        resp.raise_for_status()
        return resp.json()

    async def search_nodes(
        self,
        name: str = None,
        language: str = None,
        node_type: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search for nodes by name, language, or type."""
        params = {"limit": limit}
        if name:
            params["name"] = name
        if language:
            params["language"] = language
        if node_type:
            params["node_type"] = node_type
            
        resp = await self.client.get("/api/graph/nodes/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", data.get("nodes", []))

    async def get_entry_points(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get detected entry points (CLI commands, HTTP handlers, etc.)."""
        resp = await self.client.get("/api/graph/entry-points", params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()
        return data.get("entry_points", [])

    async def get_seams(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get cross-language seam points."""
        resp = await self.client.get("/api/graph/seams", params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()
        return data.get("seams", [])

    async def get_callers(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get functions that call the specified node."""
        resp = await self.client.get(
            "/api/graph/query/callers",
            params={"node_id": node_id, "depth": depth}
        )
        resp.raise_for_status()
        return resp.json()

    async def get_callees(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get functions called by the specified node."""
        resp = await self.client.get(
            "/api/graph/query/callees",
            params={"node_id": node_id, "depth": depth}
        )
        resp.raise_for_status()
        return resp.json()

    async def build_networkx_graph(
        self,
        exclude_stdlib: bool = True,
        exclude_tests: bool = True,
        include_private: bool = True,
        directed: bool = True,
    ) -> nx.DiGraph:
        """
        Build a NetworkX graph from the exported data.
        
        Args:
            exclude_stdlib: Exclude standard library imports
            exclude_tests: Exclude test files
            include_private: Include private symbols
            directed: Create DiGraph (True) or Graph (False)
            
        Returns:
            NetworkX graph with nodes and edges
        """
        data = await self.export_graph(
            exclude_stdlib=exclude_stdlib,
            exclude_tests=exclude_tests,
            include_private=include_private,
        )
        
        G = nx.DiGraph() if directed else nx.Graph()
        
        # Add nodes
        for node in data.get("nodes", []):
            node_id = node.get("id", node.get("name"))
            G.add_node(
                node_id,
                name=node.get("name", ""),
                type=node.get("type", ""),
                language=node.get("language", ""),
                file=node.get("file", ""),
                complexity=node.get("complexity", 0),
            )
        
        # Add edges
        for link in data.get("links", []):
            source = link.get("source")
            target = link.get("target")
            if source and target and source in G and target in G:
                G.add_edge(
                    source, 
                    target,
                    type=link.get("type", ""),
                )
        
        return G

    async def get_nodes_dataframe(
        self,
        exclude_stdlib: bool = True,
        exclude_tests: bool = True,
    ) -> pd.DataFrame:
        """Get nodes as a pandas DataFrame."""
        data = await self.export_graph(
            exclude_stdlib=exclude_stdlib,
            exclude_tests=exclude_tests,
        )
        nodes = data.get("nodes", [])
        if not nodes:
            return pd.DataFrame()
        return pd.DataFrame(nodes)

    async def get_links_dataframe(
        self,
        exclude_stdlib: bool = True,
        exclude_tests: bool = True,
    ) -> pd.DataFrame:
        """Get links/edges as a pandas DataFrame."""
        data = await self.export_graph(
            exclude_stdlib=exclude_stdlib,
            exclude_tests=exclude_tests,
        )
        links = data.get("links", [])
        if not links:
            return pd.DataFrame()
        return pd.DataFrame(links)


# Backward compatibility alias
GraphDataClient = GraphClient
