"""
Universal AST abstraction layer providing unified analysis capabilities
across all supported programming languages.

This module creates a high-level interface that abstracts away language-specific
differences while preserving the semantic meaning of code structures.
"""

from __future__ import annotations
from typing import Dict, List, Any, Protocol
from dataclasses import dataclass
import logging

from .universal_graph import (
    UniversalNode,
    UniversalGraph,
    NodeType,
    RelationType,
)
from .universal_parser import UniversalParser

logger = logging.getLogger(__name__)


class ASTAnalyzer(Protocol):
    """Protocol for language-specific AST analyzers."""

    def analyze_complexity(self, node: UniversalNode) -> int:
        """Calculate cyclomatic complexity for a node."""
        ...  # pragma: no cover

    def extract_dependencies(self, node: UniversalNode) -> List[str]:
        """Extract import/dependency information."""
        ...  # pragma: no cover

    def find_test_patterns(self, node: UniversalNode) -> bool:
        """Determine if node represents test code."""
        ...  # pragma: no cover


@dataclass
class AnalysisResult:
    """Result of analyzing a code construct."""

    node: UniversalNode
    complexity: int
    dependencies: List[str]
    is_test: bool
    metrics: Dict[str, Any]
    issues: List[str]


class UniversalASTAnalyzer:
    """High-level analyzer that works across all programming languages."""

    def __init__(self, parser: UniversalParser):
        self.parser = parser
        self.language_analyzers: Dict[str, ASTAnalyzer] = {}
        self._setup_language_analyzers()

    def _setup_language_analyzers(self) -> None:
        """Initialize language-specific analyzers."""
        # For now, use generic analyzers - can be extended with language-specific ones
        for language in self.parser.get_supported_languages():
            self.language_analyzers[language.lower()] = GenericASTAnalyzer()

    def analyze_function(self, node: UniversalNode) -> AnalysisResult:
        """Analyze a function/method node across any language."""
        if node.node_type != NodeType.FUNCTION:
            raise ValueError(f"Expected function node, got {node.node_type}")

        analyzer = self.language_analyzers.get(node.language, GenericASTAnalyzer())

        return AnalysisResult(
            node=node,
            complexity=analyzer.analyze_complexity(node),
            dependencies=analyzer.extract_dependencies(node),
            is_test=analyzer.find_test_patterns(node),
            metrics=self._calculate_function_metrics(node),
            issues=self._detect_function_issues(node),
        )

    def analyze_class(self, node: UniversalNode) -> AnalysisResult:
        """Analyze a class/struct/interface node across any language."""
        if node.node_type not in [NodeType.CLASS, NodeType.INTERFACE]:
            raise ValueError(f"Expected class/interface node, got {node.node_type}")

        analyzer = self.language_analyzers.get(node.language, GenericASTAnalyzer())

        return AnalysisResult(
            node=node,
            complexity=analyzer.analyze_complexity(node),
            dependencies=analyzer.extract_dependencies(node),
            is_test=analyzer.find_test_patterns(node),
            metrics=self._calculate_class_metrics(node),
            issues=self._detect_class_issues(node),
        )

    def find_similar_patterns(
        self, target_node: UniversalNode, graph: UniversalGraph, similarity_threshold: float = 0.8
    ) -> List[UniversalNode]:
        """Find structurally similar code patterns across languages."""
        similar_nodes = []

        # Get nodes of same type
        candidates = graph.get_nodes_by_type(target_node.node_type)

        for candidate in candidates:
            if candidate.id == target_node.id:
                continue

            similarity = self._calculate_structural_similarity(target_node, candidate)
            if similarity >= similarity_threshold:
                similar_nodes.append(candidate)

        return sorted(
            similar_nodes,
            key=lambda n: self._calculate_structural_similarity(target_node, n),
            reverse=True,
        )

    def detect_code_smells(self, graph: UniversalGraph) -> Dict[str, List[UniversalNode]]:
        """Detect common code smells across all languages."""
        smells = {
            "long_functions": [],
            "complex_functions": [],
            "large_classes": [],
            "duplicate_logic": [],
            "deep_nesting": [],
            "dead_code": [],
        }

        functions = graph.get_nodes_by_type(NodeType.FUNCTION)
        classes = graph.get_nodes_by_type(NodeType.CLASS)

        # Long functions (>50 lines)
        smells["long_functions"] = [f for f in functions if f.line_count > 50]

        # Complex functions (complexity >15)
        smells["complex_functions"] = [f for f in functions if f.complexity > 15]

        # Large classes (>500 lines or >20 methods)
        for cls in classes:
            if cls.line_count > 500:
                smells["large_classes"].append(cls)
            elif len(cls.get_children_by_type(NodeType.FUNCTION)) > 20:
                smells["large_classes"].append(cls)

        # Find potential duplicates
        smells["duplicate_logic"] = self._find_duplicate_patterns(functions)

        return smells

    def generate_call_graph(self, graph: UniversalGraph) -> Dict[str, List[str]]:
        """Generate function call graph across all languages."""
        call_graph = {}

        # Get all call relations
        call_relations = graph.get_relations_by_type(RelationType.CALLS)

        for relation in call_relations:
            source_node = graph.nodes.get(relation.source_id)
            target_node = graph.nodes.get(relation.target_id)

            if source_node and target_node:
                if source_node.qualified_name not in call_graph:
                    call_graph[source_node.qualified_name] = []
                call_graph[source_node.qualified_name].append(target_node.qualified_name)

        return call_graph

    def find_circular_dependencies(self, graph: UniversalGraph) -> List[List[str]]:
        """Find circular dependencies in the codebase."""
        import_relations = graph.get_relations_by_type(RelationType.IMPORTS)

        # Build dependency graph
        deps = {}
        for relation in import_relations:
            source = graph.nodes.get(relation.source_id)
            target = graph.nodes.get(relation.target_id)

            if source and target:
                if source.qualified_name not in deps:
                    deps[source.qualified_name] = []
                deps[source.qualified_name].append(target.qualified_name)

        # Find cycles using DFS
        return self._find_cycles_dfs(deps)

    def calculate_maintainability_index(self, graph: UniversalGraph) -> float:
        """Calculate overall maintainability index for the codebase."""
        if not graph.nodes:
            return 0.0

        total_complexity = sum(node.complexity for node in graph.nodes.values())
        total_lines = sum(node.line_count for node in graph.nodes.values())
        avg_complexity = total_complexity / len(graph.nodes)

        # Simplified maintainability index calculation
        # Real implementation would use Halstead metrics and other factors
        complexity_factor = max(0, 100 - (avg_complexity * 5))
        size_factor = max(0, 100 - (total_lines / 1000))

        return (complexity_factor + size_factor) / 2

    def _calculate_function_metrics(self, node: UniversalNode) -> Dict[str, Any]:
        """Calculate detailed metrics for a function."""
        return {
            "lines_of_code": node.line_count,
            "cyclomatic_complexity": node.complexity,
            "parameter_count": len(node.get_children_by_type(NodeType.PARAMETER)),
            "nested_depth": self._calculate_nesting_depth(node),
            "has_documentation": node.documentation is not None,
            "return_points": self._count_return_statements(node),
        }

    def _calculate_class_metrics(self, node: UniversalNode) -> Dict[str, Any]:
        """Calculate detailed metrics for a class."""
        methods = node.get_children_by_type(NodeType.FUNCTION)
        variables = node.get_children_by_type(NodeType.VARIABLE)

        return {
            "lines_of_code": node.line_count,
            "method_count": len(methods),
            "field_count": len(variables),
            "avg_method_complexity": (
                sum(m.complexity for m in methods) / len(methods) if methods else 0
            ),
            "public_methods": len([m for m in methods if not m.name.startswith("_")]),
            "has_documentation": node.documentation is not None,
        }

    def _detect_function_issues(self, node: UniversalNode) -> List[str]:
        """Detect potential issues in a function."""
        issues = []

        if node.line_count > 50:
            issues.append("Function is too long (>50 lines)")

        if node.complexity > 10:
            issues.append(f"High cyclomatic complexity ({node.complexity})")

        param_count = len(node.get_children_by_type(NodeType.PARAMETER))
        if param_count > 7:
            issues.append(f"Too many parameters ({param_count})")

        if not node.documentation:
            issues.append("Missing documentation")

        if self._calculate_nesting_depth(node) > 4:
            issues.append("Deep nesting detected")

        return issues

    def _detect_class_issues(self, node: UniversalNode) -> List[str]:
        """Detect potential issues in a class."""
        issues = []

        methods = node.get_children_by_type(NodeType.FUNCTION)

        if node.line_count > 500:
            issues.append("Class is too large (>500 lines)")

        if len(methods) > 20:
            issues.append(f"Too many methods ({len(methods)})")

        if not node.documentation:
            issues.append("Missing class documentation")

        # Check for god class pattern
        if len(methods) > 15 and node.line_count > 300:
            issues.append("Potential god class (too many responsibilities)")

        return issues

    def _calculate_structural_similarity(self, node1: UniversalNode, node2: UniversalNode) -> float:
        """Calculate structural similarity between two nodes."""
        if node1.node_type != node2.node_type:
            return 0.0

        # Compare various structural aspects
        similarity_factors = []

        # Line count similarity
        size_diff = abs(node1.line_count - node2.line_count)
        max_size = max(node1.line_count, node2.line_count)
        size_similarity = 1.0 - (size_diff / max_size) if max_size > 0 else 1.0
        similarity_factors.append(size_similarity)

        # Complexity similarity
        complexity_diff = abs(node1.complexity - node2.complexity)
        max_complexity = max(node1.complexity, node2.complexity)
        complexity_similarity = (
            1.0 - (complexity_diff / max_complexity) if max_complexity > 0 else 1.0
        )
        similarity_factors.append(complexity_similarity)

        # Child count similarity
        child_diff = abs(len(node1.children) - len(node2.children))
        max_children = max(len(node1.children), len(node2.children))
        child_similarity = 1.0 - (child_diff / max_children) if max_children > 0 else 1.0
        similarity_factors.append(child_similarity)

        return sum(similarity_factors) / len(similarity_factors)

    def _find_duplicate_patterns(self, functions: List[UniversalNode]) -> List[UniversalNode]:
        """Find potentially duplicate function implementations."""
        duplicates = []

        for i, func1 in enumerate(functions):
            for func2 in functions[i + 1 :]:
                similarity = self._calculate_structural_similarity(func1, func2)
                if similarity > 0.9:  # High similarity threshold
                    if func1 not in duplicates:
                        duplicates.append(func1)
                    if func2 not in duplicates:
                        duplicates.append(func2)

        return duplicates

    def _calculate_nesting_depth(self, node: UniversalNode) -> int:
        """Calculate maximum nesting depth in a node."""

        def depth_recursive(current_node: UniversalNode, current_depth: int) -> int:
            max_depth = current_depth

            for child in current_node.children:
                if child.node_type in [NodeType.CONDITIONAL, NodeType.LOOP]:
                    child_depth = depth_recursive(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = depth_recursive(child, current_depth)
                    max_depth = max(max_depth, child_depth)

            return max_depth

        return depth_recursive(node, 0)

    def _count_return_statements(self, node: UniversalNode) -> int:
        """Count return statements in a function."""
        # Simplified implementation - would need language-specific logic
        return node.source_text.count("return") if node.source_text else 0

    def _find_cycles_dfs(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Find cycles in a directed graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles


class GenericASTAnalyzer:
    """Generic AST analyzer that works across all languages."""

    def analyze_complexity(self, node: UniversalNode) -> int:
        """Calculate cyclomatic complexity using universal node structure."""
        complexity = 1

        def count_decision_points(current_node: UniversalNode) -> int:
            count = 0

            # Count control flow nodes that increase complexity
            if current_node.node_type in [NodeType.CONDITIONAL, NodeType.LOOP]:
                count += 1
            elif current_node.node_type == NodeType.EXCEPTION:
                count += 1

            # Recursively count in children
            for child in current_node.children:
                count += count_decision_points(child)

            return count

        return complexity + count_decision_points(node)

    def extract_dependencies(self, node: UniversalNode) -> List[str]:
        """Extract import/dependency information from any language."""
        dependencies = []

        def find_imports(current_node: UniversalNode) -> None:
            if current_node.node_type == NodeType.IMPORT:
                dependencies.append(current_node.name)

            for child in current_node.children:
                find_imports(child)

        find_imports(node)
        return dependencies

    def find_test_patterns(self, node: UniversalNode) -> bool:
        """Determine if node represents test code using universal patterns."""
        test_indicators = [
            "test_",
            "Test",
            "spec_",
            "Spec",
            "it(",
            "describe(",
            "assert",
            "expect",
            "should",
            "mock",
            "stub",
        ]

        # Check node name and source text for test patterns
        text_to_check = f"{node.name} {node.source_text}".lower()

        return any(indicator.lower() in text_to_check for indicator in test_indicators)
