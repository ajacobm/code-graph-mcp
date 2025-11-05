#!/usr/bin/env python3
"""
Direct diagnosis of zero results issue for find_references, find_callees, find_callers.

This script checks:
1. If relationships exist at all
2. What types of relationships exist (CALLS vs REFERENCES)
3. If relationships are properly indexed
4. Why specific queries return zero results
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_graph_mcp.universal_parser import UniversalParser
from code_graph_mcp.universal_graph import RelationshipType, NodeType


def diagnose_zero_results():
    """Diagnose why query tools return zero results."""
    
    workspace_root = Path("/app/workspace")
    if not workspace_root.exists():
        print("❌ Test workspace not found at /app/workspace")
        return
    
    print("="*80)
    print("ZERO RESULTS DIAGNOSIS")
    print("="*80)
    
    parser = UniversalParser(workspace_root)
    graph = parser.graph
    
    print(f"\n📊 GRAPH STATISTICS:")
    print(f"  Total nodes: {len(graph.nodes)}")
    print(f"  Total relationships: {len(graph.relationships)}")
    
    if len(graph.nodes) == 0:
        print("\n❌ CRITICAL: No nodes in graph. Parser didn't extract any code.")
        return
    
    if len(graph.relationships) == 0:
        print("\n❌ CRITICAL: No relationships in graph. Parser extracted nodes but no relationships.")
        return
    
    print("\n📈 RELATIONSHIP TYPES BREAKDOWN:")
    rel_counts = {}
    for rel_type in RelationshipType:
        rels = graph.get_relationships_by_type(rel_type)
        count = len(rels)
        rel_counts[rel_type] = count
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {rel_type.name:15} : {count:5} relationships")
    
    print("\n📍 NODE TYPES BREAKDOWN:")
    for node_type in NodeType:
        nodes = graph.get_nodes_by_type(node_type)
        count = len(nodes)
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {node_type.name:15} : {count:5} nodes")
    
    print("\n🔗 INDEXING CHECK:")
    if not graph.relationships:
        print("  ⚠️  No relationships to check indexing")
    else:
        sample_rel = next(iter(graph.relationships.values()))
        
        rels_from = graph.get_relationships_from(sample_rel.source_id)
        rels_to = graph.get_relationships_to(sample_rel.target_id)
        
        print(f"  Sample relationship: {sample_rel.source_id} -> {sample_rel.target_id}")
        print(f"  Relationships FROM source: {len(rels_from)}")
        print(f"  Relationships TO target: {len(rels_to)}")
        print(f"  Sample in rels_from: {sample_rel in rels_from}")
        print(f"  Sample in rels_to: {sample_rel in rels_to}")
        
        if sample_rel not in rels_from or sample_rel not in rels_to:
            print("  ❌ INDEXING ISSUE: Relationship not properly indexed!")
        else:
            print("  ✓ Indexing appears correct")
    
    print("\n🔍 QUERY CAPABILITY ANALYSIS:")
    
    find_refs_capable = rel_counts.get(RelationshipType.REFERENCES, 0) > 0
    find_callers_capable = rel_counts.get(RelationshipType.CALLS, 0) > 0
    
    print(f"  find_symbol_references capable: {'✓ YES' if find_refs_capable else '❌ NO'}")
    print(f"    (requires: REFERENCES relationships)")
    print(f"    (found: {rel_counts.get(RelationshipType.REFERENCES, 0)} REFERENCES)")
    
    print(f"\n  find_function_callers/callees capable: {'✓ YES' if find_callers_capable else '❌ NO'}")
    print(f"    (requires: CALLS relationships)")
    print(f"    (found: {rel_counts.get(RelationshipType.CALLS, 0)} CALLS)")
    
    print("\n🎯 ROOT CAUSE ANALYSIS:")
    
    if not find_refs_capable and not find_callers_capable:
        print("  ❌ SEVERE: No query-capable relationships exist at all!")
        print("     The parser needs to create either REFERENCES or CALLS relationships.")
        print("     Check UniversalParser for relationship creation code.")
    elif find_callers_capable and not find_refs_capable:
        print("  ⚠️  Parser creates CALLS but not REFERENCES relationships")
        print("     find_symbol_references will always return zero results")
        print("     find_function_callers/callees should work")
    elif find_refs_capable and not find_callers_capable:
        print("  ⚠️  Parser creates REFERENCES but not CALLS relationships")
        print("     find_symbol_references should work")
        print("     find_function_callers/callees will always return zero results")
    else:
        print("  ✓ Both REFERENCES and CALLS relationships exist")
        print("    All query methods should work")
    
    print("\n" + "="*80)
    print("END DIAGNOSIS")
    print("="*80)
    
    print("\n💡 NEXT STEPS:")
    print("  1. If NO relationships exist: Check UniversalParser relationship creation")
    print("  2. If wrong types: Modify parser to create correct relationship types")
    print("  3. If indexing broken: Check UniversalGraph.add_relationship() method")


if __name__ == "__main__":
    diagnose_zero_results()
