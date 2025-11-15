"""MCP Cypher Resources - Pre-built Graph Queries

10+ ready-to-use Cypher patterns for common code architecture analysis tasks.
Registered as MCP resources for easy access from LLMs and tools.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class CypherResource:
    """A pre-built Cypher query resource."""

    uri: str
    name: str
    description: str
    cypher_query: str
    parameters: Dict[str, str]  # param_name -> param_type


class CypherResources:
    """Collection of pre-built Cypher patterns."""

    RESOURCES: List[CypherResource] = [
        CypherResource(
            uri="cypher://entry-to-db-paths",
            name="Find Entry Point → DB Paths",
            description="Find all call paths from HTTP endpoints to database operations",
            cypher_query="""
            MATCH path = (entry:Function {is_entry_point: true})
                        -[:CALLS*1..15]->
                        (db:Function)
            WHERE db.name =~ '.*(insert|update|delete|save|query|execute).*'
            RETURN {
                path: [node in nodes(path) | {id: node.id, name: node.name}],
                hops: length(path),
                entry: entry.name,
                db_op: db.name
            } as result
            ORDER BY hops
            LIMIT 20
            """,
            parameters={"max_hops": "int"},
        ),
        CypherResource(
            uri="cypher://impact-analysis",
            name="Impact Analysis",
            description="Show what breaks if you change a specific function",
            cypher_query="""
            MATCH (changed:Function {name: $symbol})
            MATCH (impacted:Function)-[:CALLS*1..10]->(changed)
            RETURN {
                impacted_function: impacted.name,
                impacted_file: impacted.file,
                distance_hops: length(path),
                impacted_complexity: impacted.complexity
            } as result
            ORDER BY distance_hops
            LIMIT 50
            """,
            parameters={"symbol": "string"},
        ),
        CypherResource(
            uri="cypher://circular-dependencies",
            name="Find Circular Dependencies",
            description="Detect cycles in call graph (circular dependencies)",
            cypher_query="""
            MATCH (n:Function)-[:CALLS*]->(n)
            WITH n, [x in relationships(path) | type(x)] as rel_types
            RETURN {
                function: n.name,
                file: n.file,
                cycle_length: length(path),
                complexity: n.complexity
            } as result
            LIMIT 30
            """,
            parameters={},
        ),
        CypherResource(
            uri="cypher://architectural-seams",
            name="Find Architectural Seams",
            description="Identify high-coupling boundaries between modules (cross-file calls)",
            cypher_query="""
            MATCH (a:Function)-[c:CALLS]->(b:Function)
            WHERE a.file <> b.file
            WITH a.file as file_a, b.file as file_b, count(c) as coupling, collect(a.name) as callers
            WHERE coupling > $min_coupling
            RETURN {
                module_a: file_a,
                module_b: file_b,
                coupling_strength: coupling,
                sample_callers: callers[0..3]
            } as result
            ORDER BY coupling DESC
            LIMIT 20
            """,
            parameters={"min_coupling": "int"},
        ),
        CypherResource(
            uri="cypher://god-functions",
            name="Find God Functions (Refactoring Targets)",
            description="High complexity + many callers/callees = refactoring candidates",
            cypher_query="""
            MATCH (func:Function)
            WHERE func.complexity > $min_complexity
            WITH func,
                 size((func)<-[:CALLS]-()) as caller_count,
                 size((func)-[:CALLS]->()) as callee_count
            WHERE caller_count + callee_count > $min_degree
            RETURN {
                function: func.name,
                file: func.file,
                complexity: func.complexity,
                callers: caller_count,
                callees: callee_count,
                total_degree: caller_count + callee_count
            } as result
            ORDER BY func.complexity DESC
            LIMIT 20
            """,
            parameters={"min_complexity": "int", "min_degree": "int"},
        ),
        CypherResource(
            uri="cypher://orphan-code",
            name="Find Orphan Code",
            description="Functions with no callers or callees (dead code candidates)",
            cypher_query="""
            MATCH (func:Function)
            WHERE size((func)<-[:CALLS]-()) = 0 AND size((func)-[:CALLS]->()) = 0
            RETURN {
                function: func.name,
                file: func.file,
                language: func.language,
                line: func.line,
                complexity: func.complexity
            } as result
            ORDER BY func.file
            LIMIT 50
            """,
            parameters={},
        ),
        CypherResource(
            uri="cypher://authentication-flow",
            name="Trace Authentication Flow",
            description="Follow auth logic: entry point → auth boundary → session management",
            cypher_query="""
            MATCH (entry:Function {is_entry_point: true})
            MATCH path = (entry)-[:CALLS*1..20]->(auth:Function)
            WHERE auth.name =~ '.*auth.*|.*login.*|.*token.*|.*password.*'
            WITH entry, auth, path
            MATCH (auth)-[:CALLS*1..10]->(session:Function)
            WHERE session.name =~ '.*session.*|.*cache.*|.*store.*'
            RETURN {
                entry_point: entry.name,
                auth_function: auth.name,
                session_function: session.name,
                auth_depth: length(path)
            } as result
            LIMIT 20
            """,
            parameters={},
        ),
        CypherResource(
            uri="cypher://error-handling-paths",
            name="Error Handling Paths",
            description="Find paths from entry points to error handlers",
            cypher_query="""
            MATCH (entry:Function {is_entry_point: true})
            MATCH path = (entry)-[:CALLS*1..15]->(error:Function)
            WHERE error.name =~ '.*error.*|.*exception.*|.*catch.*|.*handle.*'
            RETURN {
                entry_point: entry.name,
                error_handler: error.name,
                path_length: length(path),
                file: error.file
            } as result
            ORDER BY path_length
            LIMIT 30
            """,
            parameters={},
        ),
        CypherResource(
            uri="cypher://test-coverage-gaps",
            name="Test Coverage Gaps",
            description="Functions without test callers (potential coverage gaps)",
            cypher_query="""
            MATCH (prod:Function)
            WHERE NOT prod.file CONTAINS 'test' AND NOT prod.file CONTAINS 'spec'
            WHERE size((prod)<-[:CALLS]-(test:Function)) = 0
            RETURN {
                function: prod.name,
                file: prod.file,
                language: prod.language,
                complexity: prod.complexity,
                callers: size((prod)<-[:CALLS]-())
            } as result
            WHERE result.complexity > 0
            ORDER BY result.complexity DESC
            LIMIT 50
            """,
            parameters={},
        ),
        CypherResource(
            uri="cypher://api-surface",
            name="API Surface Analysis",
            description="All public entry points (endpoints, controllers, exports)",
            cypher_query="""
            MATCH (entry:Function {is_entry_point: true})
            RETURN {
                function: entry.name,
                file: entry.file,
                language: entry.language,
                complexity: entry.complexity,
                direct_callers: size((entry)<-[:CALLS]-()),
                direct_callees: size((entry)-[:CALLS]->())
            } as result
            ORDER BY result.complexity DESC
            LIMIT 50
            """,
            parameters={},
        ),
        CypherResource(
            uri="cypher://code-layers",
            name="Architectural Layers",
            description="Detect layers based on call depth from entry points",
            cypher_query="""
            MATCH (entry:Function {is_entry_point: true})
            MATCH path = (entry)-[:CALLS*0..5]->()
            WITH nodes(path) as nodes_in_path
            UNWIND nodes_in_path as node
            WITH DISTINCT node, length(path)-1 as layer
            RETURN {
                layer: layer,
                layer_name: CASE layer
                    WHEN 0 THEN 'Entry Points'
                    WHEN 1 THEN 'Controllers/Handlers'
                    WHEN 2 THEN 'Business Logic'
                    WHEN 3 THEN 'Data Access'
                    ELSE 'Deep Dependencies'
                END,
                functions: collect(node.name),
                count: count(node)
            } as result
            ORDER BY layer
            """,
            parameters={},
        ),
        CypherResource(
            uri="cypher://module-boundaries",
            name="Module Boundaries",
            description="Identify module clusters via community detection (Louvain-like)",
            cypher_query="""
            MATCH (f1:Function)-[:CALLS]->(f2:Function)
            WITH f1.file as file1, f2.file as file2, count(*) as calls
            WHERE file1 <> file2
            RETURN {
                module_a: file1,
                module_b: file2,
                coupling: calls
            } as result
            ORDER BY calls DESC
            LIMIT 50
            """,
            parameters={},
        ),
    ]

    @classmethod
    def get_resource(cls, uri: str) -> CypherResource:
        """Get a resource by URI."""
        for resource in cls.RESOURCES:
            if resource.uri == uri:
                return resource
        raise ValueError(f"Unknown resource: {uri}")

    @classmethod
    def list_resources(cls) -> List[Dict[str, str]]:
        """List all available resources."""
        return [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
            }
            for r in cls.RESOURCES
        ]

    @classmethod
    def get_mcp_resources(cls) -> List[Dict[str, Any]]:
        """Get resources in MCP format for registration."""
        return [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mimeType": "text/plain",
            }
            for r in cls.RESOURCES
        ]


# Convenience functions for MCP handlers
def list_cypher_resources() -> List[Dict[str, Any]]:
    """MCP handler: list available Cypher resources."""
    return CypherResources.get_mcp_resources()


def get_cypher_resource(uri: str) -> str:
    """MCP handler: get Cypher query for a resource."""
    resource = CypherResources.get_resource(uri)
    return f"""
# {resource.name}

{resource.description}

## Query

{resource.cypher_query}

## Parameters

{resource.parameters}
"""
