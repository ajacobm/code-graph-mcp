"""
Universal language-agnostic graph structures for multi-language code analysis.

This module defines abstract data structures that can represent code constructs
across 25+ programming languages using ast-grep as the parsing backend.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Union
from pathlib import Path


class NodeType(Enum):
    """Universal node types that work across all programming languages."""

    # Structural elements
    MODULE = "module"  # Python module, JS file, Java package
    CLASS = "class"  # Class, struct, interface
    FUNCTION = "function"  # Function, method, procedure
    VARIABLE = "variable"  # Variable, field, constant
    PARAMETER = "parameter"  # Function parameter

    # Control flow
    CONDITIONAL = "conditional"  # if/else, switch, match
    LOOP = "loop"  # for, while, do-while
    EXCEPTION = "exception"  # try/catch, error handling

    # Language-specific that map to universal concepts
    INTERFACE = "interface"  # Interface, trait, protocol
    ENUM = "enum"  # Enumeration, union type
    NAMESPACE = "namespace"  # Package, namespace, module
    IMPORT = "import"  # Import, include, using

    # Literals and expressions
    LITERAL = "literal"  # String, number, boolean
    CALL = "call"  # Function/method call
    REFERENCE = "reference"  # Variable/function reference


class RelationType(Enum):
    """Types of relationships between code nodes."""

    CALLS = "calls"  # A calls B
    REFERENCES = "references"  # A references B
    INHERITS = "inherits"  # A inherits from B
    IMPLEMENTS = "implements"  # A implements interface B
    CONTAINS = "contains"  # A contains B (structural)
    IMPORTS = "imports"  # A imports B
    OVERRIDES = "overrides"  # A overrides B
    RETURNS = "returns"  # A returns type B
    THROWS = "throws"  # A throws exception B


@dataclass
class SourceLocation:
    """Universal source location representation."""

    file_path: Path
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def __str__(self) -> str:
        return f"{self.file_path}:{self.start_line}:{self.start_column}"


@dataclass
class UniversalNode:  # pylint: disable=too-many-instance-attributes
    """Language-agnostic representation of a code node."""

    # Core identification
    id: str  # Unique identifier
    node_type: NodeType  # Universal node type
    name: str  # Node name/identifier
    qualified_name: str  # Fully qualified name

    # Source information
    location: SourceLocation  # Where this node is defined
    language: str  # Programming language
    raw_kind: str  # Original ast-grep node kind

    # Content and metadata
    source_text: str = ""  # Original source code
    documentation: Optional[str] = None  # Docstring/comments
    signature: Optional[str] = None  # Function/method signature

    # Analysis metrics
    complexity: int = 1  # Cyclomatic complexity
    line_count: int = 0  # Lines of code

    # Language-specific attributes
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    children: List[UniversalNode] = field(default_factory=list)

    def add_child(self, child: UniversalNode) -> None:
        """Add a child node."""
        self.children.append(child)

    def get_children_by_type(self, node_type: NodeType) -> List[UniversalNode]:
        """Get all children of a specific type."""
        return [child for child in self.children if child.node_type == node_type]


@dataclass
class UniversalRelation:
    """Represents a relationship between two nodes."""

    source_id: str  # Source node ID
    target_id: str  # Target node ID
    relation_type: RelationType  # Type of relationship
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.source_id} --{self.relation_type.value}--> {self.target_id}"


class LanguageMapping:
    """Maps language-specific AST node kinds to universal types."""

    # Language-specific mappings for ast-grep node kinds
    MAPPINGS: Dict[str, Dict[str, NodeType]] = {
        "python": {
            "module": NodeType.MODULE,
            "class_definition": NodeType.CLASS,
            "function_definition": NodeType.FUNCTION,
            "assignment": NodeType.VARIABLE,
            "parameters": NodeType.PARAMETER,
            "if_statement": NodeType.CONDITIONAL,
            "while_statement": NodeType.LOOP,
            "for_statement": NodeType.LOOP,
            "try_statement": NodeType.EXCEPTION,
            "import_statement": NodeType.IMPORT,
            "import_from_statement": NodeType.IMPORT,
            "call": NodeType.CALL,
            "identifier": NodeType.REFERENCE,
        },
        "javascript": {
            "program": NodeType.MODULE,
            "class_declaration": NodeType.CLASS,
            "function_declaration": NodeType.FUNCTION,
            "method_definition": NodeType.FUNCTION,
            "variable_declaration": NodeType.VARIABLE,
            "formal_parameters": NodeType.PARAMETER,
            "if_statement": NodeType.CONDITIONAL,
            "while_statement": NodeType.LOOP,
            "for_statement": NodeType.LOOP,
            "try_statement": NodeType.EXCEPTION,
            "import_statement": NodeType.IMPORT,
            "call_expression": NodeType.CALL,
            "identifier": NodeType.REFERENCE,
        },
        "typescript": {
            "program": NodeType.MODULE,
            "class_declaration": NodeType.CLASS,
            "interface_declaration": NodeType.INTERFACE,
            "function_declaration": NodeType.FUNCTION,
            "method_definition": NodeType.FUNCTION,
            "variable_declaration": NodeType.VARIABLE,
            "formal_parameters": NodeType.PARAMETER,
            "if_statement": NodeType.CONDITIONAL,
            "while_statement": NodeType.LOOP,
            "for_statement": NodeType.LOOP,
            "try_statement": NodeType.EXCEPTION,
            "import_statement": NodeType.IMPORT,
            "call_expression": NodeType.CALL,
            "identifier": NodeType.REFERENCE,
        },
        "java": {
            "program": NodeType.MODULE,
            "class_declaration": NodeType.CLASS,
            "interface_declaration": NodeType.INTERFACE,
            "method_declaration": NodeType.FUNCTION,
            "variable_declarator": NodeType.VARIABLE,
            "formal_parameter": NodeType.PARAMETER,
            "if_statement": NodeType.CONDITIONAL,
            "while_statement": NodeType.LOOP,
            "for_statement": NodeType.LOOP,
            "try_statement": NodeType.EXCEPTION,
            "import_declaration": NodeType.IMPORT,
            "method_invocation": NodeType.CALL,
            "identifier": NodeType.REFERENCE,
        },
        "rust": {
            "source_file": NodeType.MODULE,
            "struct_item": NodeType.CLASS,
            "impl_item": NodeType.CLASS,
            "function_item": NodeType.FUNCTION,
            "let_declaration": NodeType.VARIABLE,
            "parameters": NodeType.PARAMETER,
            "if_expression": NodeType.CONDITIONAL,
            "while_expression": NodeType.LOOP,
            "for_expression": NodeType.LOOP,
            "use_declaration": NodeType.IMPORT,
            "call_expression": NodeType.CALL,
            "identifier": NodeType.REFERENCE,
        },
        "go": {
            "source_file": NodeType.MODULE,
            "type_declaration": NodeType.CLASS,
            "function_declaration": NodeType.FUNCTION,
            "method_declaration": NodeType.FUNCTION,
            "var_declaration": NodeType.VARIABLE,
            "parameter_list": NodeType.PARAMETER,
            "if_statement": NodeType.CONDITIONAL,
            "for_statement": NodeType.LOOP,
            "import_declaration": NodeType.IMPORT,
            "call_expression": NodeType.CALL,
            "identifier": NodeType.REFERENCE,
        },
        "c": {
            "translation_unit": NodeType.MODULE,
            "struct_specifier": NodeType.CLASS,
            "function_definition": NodeType.FUNCTION,
            "declaration": NodeType.VARIABLE,
            "parameter_declaration": NodeType.PARAMETER,
            "if_statement": NodeType.CONDITIONAL,
            "while_statement": NodeType.LOOP,
            "for_statement": NodeType.LOOP,
            "preproc_include": NodeType.IMPORT,
            "call_expression": NodeType.CALL,
            "identifier": NodeType.REFERENCE,
        },
    }

    @classmethod
    def get_universal_type(cls, language: str, ast_kind: str) -> NodeType:
        """Map language-specific AST kind to universal node type."""
        lang_mapping = cls.MAPPINGS.get(language.lower(), {})
        return lang_mapping.get(ast_kind, NodeType.REFERENCE)  # Default fallback

    @classmethod
    def supported_languages(cls) -> List[str]:
        """Get list of supported languages."""
        return list(cls.MAPPINGS.keys())


@dataclass
class UniversalGraph:
    """Language-agnostic code graph containing nodes and relationships."""

    nodes: Dict[str, UniversalNode] = field(default_factory=dict)
    relations: List[UniversalRelation] = field(default_factory=list)
    root_nodes: Set[str] = field(default_factory=set)  # Top-level modules

    # Metadata
    languages: Set[str] = field(default_factory=set)
    file_count: int = 0
    total_lines: int = 0

    def add_node(self, node: UniversalNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.languages.add(node.language)
        self.total_lines += node.line_count

        # Track root nodes (typically modules/files)
        if node.node_type == NodeType.MODULE:
            self.root_nodes.add(node.id)

    def add_relation(self, relation: UniversalRelation) -> None:
        """Add a relationship to the graph."""
        self.relations.append(relation)

    def get_nodes_by_type(self, node_type: NodeType) -> List[UniversalNode]:
        """Get all nodes of a specific type."""
        return [node for node in self.nodes.values() if node.node_type == node_type]

    def get_nodes_by_language(self, language: str) -> List[UniversalNode]:
        """Get all nodes from a specific language."""
        return [node for node in self.nodes.values() if node.language == language]

    def get_relations_by_type(self, relation_type: RelationType) -> List[UniversalRelation]:
        """Get all relations of a specific type."""
        return [rel for rel in self.relations if rel.relation_type == relation_type]

    def get_node_relations(self, node_id: str) -> List[UniversalRelation]:
        """Get all relations involving a specific node."""
        return [
            rel for rel in self.relations if node_id in (rel.source_id, rel.target_id)
        ]

    def calculate_complexity(self) -> Dict[str, Union[int, float]]:
        """Calculate complexity metrics for the entire graph."""
        return {
            "total_nodes": len(self.nodes),
            "total_relations": len(self.relations),
            "languages": len(self.languages),
            "files": self.file_count,
            "lines": self.total_lines,
            "avg_complexity": (
                sum(node.complexity for node in self.nodes.values()) / len(self.nodes)
                if self.nodes
                else 0
            ),
        }
