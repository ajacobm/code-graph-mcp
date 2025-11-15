"""Graph data client for Jupyter notebooks.

Provides unified access to Redis, Memgraph, and Backend API for data science workflows.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import os

import redis.asyncio as redis
from neo4j import GraphDatabase
import httpx
import networkx as nx
from collections import defaultdict


@dataclass
class GraphStats:
    """Statistics about the graph."""
    nodes: int
    relationships: int
    languages: List[str]
    entry_points: int
    circular_deps: int


class GraphDataClient:
    """Unified client for graph data science operations."""

    def __init__(
        self,
        redis_url: str = None,
        memgraph_url: str = None,
        api_url: str = None,
        timeout: int = 10,
    ):
        """Initialize client with service URLs from environment or parameters."""
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379")
        self.memgraph_url = memgraph_url or os.getenv("MEMGRAPH_URL", "bolt://memgraph:7687")
        self.api_url = api_url or os.getenv("BACKEND_API_URL", "http://code-graph-http:8000")
        self.timeout = timeout

        self.redis: Optional[redis.Redis] = None
        self.memgraph_driver = None
        self.api_client = httpx.AsyncClient(base_url=self.api_url, timeout=timeout)

    async def connect(self) -> None:
        """Establish connections to all services."""
        try:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            print("✓ Redis connected")
        except Exception as e:
            print(f"✗ Redis connection failed: {e}")

        try:
            self.memgraph_driver = GraphDatabase.driver(self.memgraph_url)
            with self.memgraph_driver.session() as session:
                session.run("RETURN 1")
            print("✓ Memgraph connected")
        except Exception as e:
            print(f"✗ Memgraph connection failed: {e}")

        try:
            resp = await self.api_client.get("/health")
            print(f"✓ Backend API connected ({resp.status_code})")
        except Exception as e:
            print(f"✗ Backend API connection failed: {e}")

    async def close(self) -> None:
        """Close all connections."""
        if self.redis:
            await self.redis.close()
        if self.memgraph_driver:
            self.memgraph_driver.close()
        await self.api_client.aclose()

    async def get_graph_stats(self) -> GraphStats:
        """Get high-level graph statistics."""
        resp = await self.api_client.get("/api/graph/stats")
        data = resp.json()
        return GraphStats(
            nodes=data.get("total_nodes", 0),
            relationships=data.get("total_relationships", 0),
            languages=data.get("languages", []),
            entry_points=data.get("entry_points", 0),
            circular_deps=data.get("circular_dependencies", 0),
        )

    async def get_all_nodes(self, limit: int = 10000) -> List[Dict[str, Any]]:
        """Fetch all nodes from API."""
        resp = await self.api_client.get(f"/api/graph/nodes/search?limit={limit}")
        return resp.json().get("nodes", [])

    async def get_all_relationships(self, limit: int = 50000) -> List[Dict[str, Any]]:
        """Fetch all relationships from API."""
        resp = await self.api_client.get(f"/api/graph/relationships?limit={limit}")
        return resp.json().get("relationships", [])

    def run_cypher(self, query: str, **params) -> List[Dict[str, Any]]:
        """Execute Cypher query against Memgraph."""
        if not self.memgraph_driver:
            raise RuntimeError("Memgraph not connected")

        with self.memgraph_driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]

    async def build_networkx_graph(self) -> nx.DiGraph:
        """Build NetworkX graph from all nodes and relationships."""
        print("Loading graph data...")
        nodes = await self.get_all_nodes()
        relationships = await self.get_all_relationships()

        G = nx.DiGraph()

        # Add nodes with attributes
        for node in nodes:
            G.add_node(
                node["id"],
                name=node.get("name", ""),
                type=node.get("type", ""),
                language=node.get("language", ""),
                complexity=node.get("complexity", 0),
                is_entry_point=node.get("is_entry_point", False),
            )

        # Add edges
        for rel in relationships:
            G.add_edge(rel["source"], rel["target"], rel_type=rel.get("type", ""))

        print(f"✓ Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
        return G

    def get_node_centrality(
        self, G: nx.DiGraph, metric: str = "betweenness"
    ) -> Dict[str, float]:
        """Calculate centrality metrics for nodes.

        Args:
            G: NetworkX directed graph
            metric: "betweenness", "closeness", "degree", or "pagerank"
        """
        if metric == "betweenness":
            return nx.betweenness_centrality(G)
        elif metric == "closeness":
            return nx.closeness_centrality(G)
        elif metric == "degree":
            return {node: G.degree(node) for node in G.nodes()}
        elif metric == "pagerank":
            return nx.pagerank(G)
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def detect_communities(self, G: nx.DiGraph, algorithm: str = "louvain") -> Dict[str, int]:
        """Detect communities in graph.

        Args:
            G: NetworkX directed graph
            algorithm: "louvain" or "label_propagation"
        """
        # Convert to undirected for community detection
        G_undirected = G.to_undirected()

        if algorithm == "louvain":
            try:
                import community
                communities = community.best_partition(G_undirected)
                return communities
            except ImportError:
                raise RuntimeError("python-louvain not installed")

        elif algorithm == "label_propagation":
            communities_gen = nx.community.label_propagation_communities(G_undirected)
            communities = {}
            for comm_id, nodes in enumerate(communities_gen):
                for node in nodes:
                    communities[node] = comm_id
            return communities

        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def find_critical_nodes(
        self, G: nx.DiGraph, top_n: int = 20, metric: str = "pagerank"
    ) -> List[Tuple[str, float]]:
        """Find most critical nodes by centrality metric."""
        centrality = self.get_node_centrality(G, metric)
        return sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def find_architecture_seams(
        self, G: nx.DiGraph, min_coupling: int = 10
    ) -> List[Tuple[str, str, int]]:
        """Find high-coupling boundaries between modules.

        Returns list of (module_a, module_b, coupling_count)
        """
        seams = defaultdict(int)

        for source, target, data in G.edges(data=True):
            # Extract file path from node id (format: type:/path/file:func:line)
            source_file = source.split(":")[1] if ":" in source else source
            target_file = target.split(":")[1] if ":" in target else target

            if source_file != target_file:
                pair = tuple(sorted([source_file, target_file]))
                seams[pair] += 1

        # Filter by minimum coupling
        return [
            (a, b, count)
            for (a, b), count in seams.items()
            if count >= min_coupling
        ]

    def get_call_paths(
        self, G: nx.DiGraph, start: str, end: str, max_length: int = 10
    ) -> List[List[str]]:
        """Find all call paths between two nodes."""
        try:
            paths = nx.all_simple_paths(G, start, end, cutoff=max_length)
            return list(paths)
        except nx.NetworkXNoPath:
            return []

    async def query_cypher_resource(self, resource_name: str, **params) -> List[Dict[str, Any]]:
        """Execute a pre-built MCP Cypher resource.

        Args:
            resource_name: Name of resource (e.g., "entry-to-db-paths")
            **params: Query parameters
        """
        resp = await self.api_client.get(
            f"/api/resources/cypher/{resource_name}", params=params
        )
        return resp.json().get("results", [])


# Context manager for easy notebook usage
class GraphAnalysis:
    """Context manager for graph analysis sessions."""

    def __init__(
        self,
        redis_url: str = None,
        memgraph_url: str = None,
        api_url: str = None,
    ):
        self.client = GraphDataClient(redis_url, memgraph_url, api_url)
        self.graph = None

    async def __aenter__(self):
        await self.client.connect()
        return self

    async def __aexit__(self, *args):
        if self.graph:
            del self.graph
        await self.client.close()

    async def load_graph(self) -> nx.DiGraph:
        """Load full graph."""
        self.graph = await self.client.build_networkx_graph()
        return self.graph
