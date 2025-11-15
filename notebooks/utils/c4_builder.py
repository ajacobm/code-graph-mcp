"""C4 diagram builder for architectural visualization.

Transforms graph queries and community detection results into C4 context/container/component diagrams.
Uses PlantUML format for rendering.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import networkx as nx


@dataclass
class C4Element:
    """Represents a C4 element (system, container, or component)."""

    id: str
    name: str
    type: str  # System, Container, Component, Person
    description: str = ""
    technology: str = ""


@dataclass
class C4Relationship:
    """Represents a C4 relationship between elements."""

    source: str
    target: str
    description: str
    protocol: str = ""


class C4Builder:
    """Build C4 diagrams from graph data."""

    def __init__(self):
        self.elements: Dict[str, C4Element] = {}
        self.relationships: List[C4Relationship] = []

    def add_element(
        self,
        element_id: str,
        name: str,
        elem_type: str,
        description: str = "",
        technology: str = "",
    ) -> None:
        """Add a C4 element."""
        self.elements[element_id] = C4Element(element_id, name, elem_type, description, technology)

    def add_relationship(
        self, source: str, target: str, description: str, protocol: str = ""
    ) -> None:
        """Add a C4 relationship."""
        self.relationships.append(C4Relationship(source, target, description, protocol))

    def to_plantuml(self, title: str = "System Architecture") -> str:
        """Export diagram as PlantUML C4 syntax."""
        lines = [
            "@startuml",
            f"title {title}",
            "!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml",
            "",
        ]

        # Add elements
        for elem in self.elements.values():
            if elem.type == "System":
                lines.append(f"System({elem.id}, \"{elem.name}\", \"{elem.description}\")")
            elif elem.type == "Container":
                lines.append(
                    f"Container({elem.id}, \"{elem.name}\", \"{elem.technology}\", \"{elem.description}\")"
                )
            elif elem.type == "Component":
                lines.append(
                    f"Component({elem.id}, \"{elem.name}\", \"{elem.technology}\", \"{elem.description}\")"
                )
            elif elem.type == "Person":
                lines.append(f"Person({elem.id}, \"{elem.name}\", \"{elem.description}\")")

        # Add relationships
        lines.append("")
        for rel in self.relationships:
            lines.append(f"Rel({rel.source}, {rel.target}, \"{rel.description}\")")

        lines.append("")
        lines.append("@enduml")

        return "\n".join(lines)

    @staticmethod
    def from_communities(
        G: nx.DiGraph, communities: Dict[str, int], seams: List[Tuple[str, str, int]]
    ) -> "C4Builder":
        """Build C4 diagram from community detection results.

        Args:
            G: NetworkX directed graph
            communities: Node -> community_id mapping
            seams: List of (file_a, file_b, coupling_count) tuples
        """
        builder = C4Builder()

        # Add components (one per community)
        community_names: Dict[int, str] = {}
        for node, comm_id in communities.items():
            if comm_id not in community_names:
                # Create component name from community
                community_names[comm_id] = f"Component_{comm_id}"
                builder.add_element(
                    f"comp_{comm_id}",
                    f"Module {comm_id}",
                    "Component",
                    f"Community {comm_id}",
                    "Python",
                )

        # Add architectural seam relationships (high coupling)
        seen_seams = set()
        for file_a, file_b, coupling in seams:
            seam_key = tuple(sorted([file_a, file_b]))
            if seam_key not in seen_seams:
                seen_seams.add(seam_key)
                builder.add_relationship(
                    f"comp_{communities.get(file_a, 0)}",
                    f"comp_{communities.get(file_b, 0)}",
                    f"Coupling: {coupling} calls",
                )

        return builder

    @staticmethod
    def from_entry_points(
        G: nx.DiGraph, entry_points: List[str], critical_paths: Dict[str, List[str]]
    ) -> "C4Builder":
        """Build C4 diagram highlighting entry points and critical paths.

        Args:
            G: NetworkX directed graph
            entry_points: List of entry point node IDs
            critical_paths: Dict mapping entry_point -> [path_nodes]
        """
        builder = C4Builder()

        # Add external person/system
        builder.add_element("user", "User", "Person", "External user")
        builder.add_element("api", "API System", "System", "Entry points")

        # Add entry points as containers
        for i, entry_id in enumerate(entry_points[:5]):  # Limit to top 5
            node_data = G.nodes[entry_id]
            builder.add_element(
                f"entry_{i}",
                node_data.get("name", entry_id),
                "Container",
                "Entry point",
                node_data.get("language", ""),
            )
            builder.add_relationship("user", f"entry_{i}", "Calls")

        return builder


class ArchitecturalAnalyzer:
    """Analyze architectural properties of the graph."""

    @staticmethod
    def detect_layers(G: nx.DiGraph) -> Dict[str, List[str]]:
        """Detect architectural layers based on import patterns.

        Heuristic: Nodes at similar call depths form layers.
        Returns mapping of layer_name -> [node_ids]
        """
        # Calculate call depth from entry points
        depths: Dict[str, int] = {}
        entry_points = [node for node in G.nodes() if G.in_degree(node) == 0]

        for entry in entry_points:
            # BFS to calculate depth
            visited = {entry: 0}
            queue = [(entry, 0)]

            while queue:
                node, depth = queue.pop(0)
                if node not in visited or visited[node] < depth:
                    visited[node] = depth

                for neighbor in G.successors(node):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))

            depths.update(visited)

        # Group by depth
        layers = {}
        for depth in range(max(depths.values()) + 1 if depths else 0):
            nodes_at_depth = [node for node, d in depths.items() if d == depth]
            if nodes_at_depth:
                layers[f"Layer_{depth}"] = nodes_at_depth

        return layers

    @staticmethod
    def detect_technical_domains(G: nx.DiGraph, communities: Dict[str, int]) -> Dict[str, str]:
        """Infer technical domain from node names and communities.

        Returns mapping of community_id -> inferred_domain
        """
        domains = {}

        # Heuristic keywords for different domains
        domain_keywords = {
            "api": ["endpoint", "handler", "route", "controller", "view"],
            "auth": ["auth", "login", "password", "token", "jwt", "oauth"],
            "database": ["db", "repository", "dao", "query", "model", "schema"],
            "cache": ["cache", "redis", "memcache", "session"],
            "messaging": ["queue", "kafka", "pubsub", "message", "broker"],
            "ui": ["component", "page", "screen", "widget", "render"],
        }

        for comm_id in set(communities.values()):
            # Get all nodes in this community
            nodes = [node for node, c in communities.items() if c == comm_id]

            # Count keyword matches
            keyword_scores = {domain: 0 for domain in domain_keywords}

            for node in nodes:
                node_name = node.lower()
                for domain, keywords in domain_keywords.items():
                    for keyword in keywords:
                        if keyword in node_name:
                            keyword_scores[domain] += 1

            # Pick highest scoring domain
            best_domain = max(keyword_scores, key=keyword_scores.get)
            if keyword_scores[best_domain] > 0:
                domains[comm_id] = best_domain
            else:
                domains[comm_id] = "business_logic"

        return domains

    @staticmethod
    def extract_ontology(G: nx.DiGraph) -> Dict[str, List[str]]:
        """Extract domain vocabulary and concepts.

        Returns mapping of concept_type -> [concept_instances]
        """
        ontology = {
            "entities": [],
            "services": [],
            "repositories": [],
            "controllers": [],
            "utilities": [],
            "models": [],
        }

        for node in G.nodes():
            node_name = node.split(":")[-2].lower()  # Extract function/class name

            if any(x in node_name for x in ["repository", "dao"]):
                ontology["repositories"].append(node)
            elif any(x in node_name for x in ["service", "manager", "handler"]):
                ontology["services"].append(node)
            elif any(x in node_name for x in ["controller", "view", "endpoint", "route"]):
                ontology["controllers"].append(node)
            elif any(x in node_name for x in ["model", "entity", "schema", "dto"]):
                ontology["models"].append(node)
            elif any(x in node_name for x in ["util", "helper", "tool"]):
                ontology["utilities"].append(node)
            else:
                ontology["entities"].append(node)

        return ontology
