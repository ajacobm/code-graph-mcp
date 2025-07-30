"""
Graph Serialization and Export for RustworkX Code Graph

Provides comprehensive graph export and import functionality:
- JSON serialization and deserialization
- DOT format export for Graphviz visualization
- GraphML export for graph analysis tools
- Comprehensive analysis reporting
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import rustworkx as rx

from ..universal_graph import (
    UniversalNode,
    UniversalRelationship,
    UniversalLocation,
    NodeType,
    RelationshipType,
    CacheConfig
)

logger = logging.getLogger(__name__)


class GraphSerializationMixin:
    """
    Mixin class providing graph serialization and export functionality.
    
    Provides:
    - JSON export/import
    - DOT format export 
    - GraphML export
    - Comprehensive analysis reporting
    """

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
            data = json.loads(json_data) if isinstance(json_data, str) else json_data

            # Clear existing graph
            self.clear()

            # Recreate graph from node-link format
            if hasattr(rx, 'node_link_graph'):
                self.graph = getattr(rx, 'node_link_graph')(data)
                # TODO: Extract node and relationship objects from rustworkx graph data
            else:
                # Manual reconstruction from JSON data
                self.graph = rx.PyDiGraph()

                # First, recreate all node objects from JSON data
                for node_data in data.get('nodes', []):
                    try:
                        # Reconstruct UniversalLocation
                        location = UniversalLocation(
                            file_path=node_data.get('file', ''),
                            start_line=int(node_data.get('line', 1)),
                            end_line=int(node_data.get('end_line', node_data.get('line', 1))),
                            language=node_data.get('language', '')
                        )

                        # Reconstruct UniversalNode
                        node = UniversalNode(
                            id=node_data['id'],
                            name=node_data.get('name', ''),
                            node_type=NodeType(node_data.get('type', 'function')),
                            location=location,
                            language=node_data.get('language', ''),
                            complexity=int(node_data.get('complexity', 0))
                        )

                        # Add to our nodes dictionary
                        self.nodes[node.id] = node

                        # Add to rustworkx graph with node ID as data
                        node_index = self.graph.add_node(node.id)

                        # Store rustworkx index in node object
                        node._rustworkx_index = node_index

                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Failed to reconstruct node {node_data.get('id', 'unknown')}: {e}")
                        continue

                # Then, recreate all relationship objects and edges
                for edge_data in data.get('edges', []):
                    try:
                        # Reconstruct UniversalRelationship
                        rel = UniversalRelationship(
                            id=edge_data['id'],
                            source_id=edge_data['source'],
                            target_id=edge_data['target'],
                            relationship_type=RelationshipType(edge_data.get('type', 'calls')),
                            strength=float(edge_data.get('strength', 1.0))
                        )

                        # Add to our relationships dictionary
                        self.relationships[rel.id] = rel

                        # Find source and target node indices
                        source_node = self.nodes.get(rel.source_id)
                        target_node = self.nodes.get(rel.target_id)

                        if source_node and target_node:
                            source_idx = getattr(source_node, '_rustworkx_index', None)
                            target_idx = getattr(target_node, '_rustworkx_index', None)

                            if source_idx is not None and target_idx is not None:
                                # Add edge to rustworkx graph
                                edge_index = self.graph.add_edge(source_idx, target_idx, rel.id)

                                # Store edge index in relationship object
                                rel._rustworkx_edge_index = edge_index
                            else:
                                logger.warning(f"Could not find indices for relationship {rel.id}")
                        else:
                            logger.warning(f"Could not find nodes for relationship {rel.id}")

                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Failed to reconstruct relationship {edge_data.get('id', 'unknown')}: {e}")
                        continue

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
                with open(filename, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif format.lower() == "yaml":
                try:
                    import yaml
                    with open(filename, 'w') as f:
                        yaml.dump(report, f, default_flow_style=False)
                except ImportError:
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