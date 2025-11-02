"""Debug script to check mock graph setup."""

from unittest.mock import MagicMock
from code_graph_mcp.universal_graph import UniversalGraph, UniversalNode, UniversalRelationship, UniversalLocation, NodeType, RelationshipType

def create_mock_graph():
    """Create a mock graph with test data."""
    
    # Create test graph
    graph = UniversalGraph()
    
    # Add test nodes with varying degrees
    nodes_data = [
        ("main", 0, 2),
        ("entry_func", 0, 3),
        ("utility_hub", 5, 5),
        ("helper_func", 4, 6),
        ("leaf_util", 3, 0),
        ("leaf_worker", 2, 0),
    ]
    
    for name, in_count, out_count in nodes_data:
        loc = UniversalLocation(file_path="test_file.py", start_line=1, end_line=10)
        node = UniversalNode(
            id=f"test_file.py:{name}:1",
            name=name,
            node_type=NodeType.FUNCTION,
            location=loc,
            language="python",
            complexity=1
        )
        graph.add_node(node)
    
    # Add relationships - create a proper DAG structure
    node_ids = [f"test_file.py:{name}:1" for name, _, _ in nodes_data]
    print(f"Node IDs: {node_ids}")
    
    rel_id = 0
    
    # Create a simple linear flow: main -> entry_func -> utility_hub -> helper_func -> leaf_util -> leaf_worker
    # This ensures entry points have 0 incoming, leaves have 0 outgoing
    
    # Entry points (main, entry_func) have no incoming
    # main -> entry_func
    if len(node_ids) > 1:
        rel = UniversalRelationship(
            id=f"rel_{rel_id}",
            source_id=node_ids[0],  # main
            target_id=node_ids[1],   # entry_func
            relationship_type=RelationshipType.CALLS
        )
        graph.add_relationship(rel)
        print(f"Added relationship: {node_ids[0]} -> {node_ids[1]}")
        rel_id += 1
    
    # entry_func -> utility_hub
    if len(node_ids) > 2:
        rel = UniversalRelationship(
            id=f"rel_{rel_id}",
            source_id=node_ids[1],  # entry_func
            target_id=node_ids[2],   # utility_hub
            relationship_type=RelationshipType.CALLS
        )
        graph.add_relationship(rel)
        print(f"Added relationship: {node_ids[1]} -> {node_ids[2]}")
        rel_id += 1
    
    # utility_hub -> helper_func
    if len(node_ids) > 3:
        rel = UniversalRelationship(
            id=f"rel_{rel_id}",
            source_id=node_ids[2],  # utility_hub
            target_id=node_ids[3],   # helper_func
            relationship_type=RelationshipType.CALLS
        )
        graph.add_relationship(rel)
        print(f"Added relationship: {node_ids[2]} -> {node_ids[3]}")
        rel_id += 1
    
    # helper_func -> leaf_util
    if len(node_ids) > 4:
        rel = UniversalRelationship(
            id=f"rel_{rel_id}",
            source_id=node_ids[3],  # helper_func
            target_id=node_ids[4],   # leaf_util
            relationship_type=RelationshipType.CALLS
        )
        graph.add_relationship(rel)
        print(f"Added relationship: {node_ids[3]} -> {node_ids[4]}")
        rel_id += 1
    
    # helper_func -> leaf_worker
    if len(node_ids) > 5:
        rel = UniversalRelationship(
            id=f"rel_{rel_id}",
            source_id=node_ids[3],  # helper_func
            target_id=node_ids[5],   # leaf_worker
            relationship_type=RelationshipType.CALLS
        )
        graph.add_relationship(rel)
        print(f"Added relationship: {node_ids[3]} -> {node_ids[5]}")
        rel_id += 1
    
    print(f"Total relationships created: {rel_id}")
    return graph

def check_degrees(graph):
    """Check incoming and outgoing degrees."""
    
    in_degree = {}
    out_degree = {}
    
    for node_id in graph.nodes:
        in_degree[node_id] = len([r for r in graph.relationships.values() if r.target_id == node_id])
        out_degree[node_id] = len([r for r in graph.relationships.values() if r.source_id == node_id])
    
    print("\nNode degrees:")
    for node_id in sorted(in_degree.keys()):
        print(f"{node_id}: in={in_degree[node_id]}, out={out_degree[node_id]}")
    
    entry_points = [node_id for node_id, degree in in_degree.items() if degree == 0]
    print(f"\nEntry points (0 incoming): {len(entry_points)}")
    for ep in entry_points:
        print(f"  - {ep}")
    
    return in_degree, out_degree

if __name__ == "__main__":
    graph = create_mock_graph()
    in_degree, out_degree = check_degrees(graph)