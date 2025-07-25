"""
Universal multi-language parser using ast-grep backend.

This module provides a pluggable parser architecture that can analyze code
in 25+ programming languages and convert them to universal graph structures.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Union, Any
import logging
from dataclasses import dataclass
import re

import ast_grep_py as ag  # type: ignore[import-untyped]

from .universal_graph import (
    UniversalNode,
    UniversalGraph,
    SourceLocation,
    NodeType,
    LanguageMapping,
)

logger = logging.getLogger(__name__)


@dataclass
class LanguageConfig:
    """Configuration for a specific programming language."""

    name: str  # Language name
    extensions: List[str]  # File extensions (.py, .js, etc.)
    ast_grep_id: str  # ast-grep language identifier
    comment_patterns: List[str]  # Comment syntax patterns
    node_extractors: Optional[Dict[str, Callable]] = None  # Custom node extraction logic

    def __post_init__(self):
        if self.node_extractors is None:
            self.node_extractors = {}


class LanguageRegistry:
    """Registry of supported programming languages with their configurations."""

    # Comprehensive language support for enterprise environments
    LANGUAGES = {
        # Web & Frontend
        "javascript": LanguageConfig(
            name="JavaScript",
            extensions=[".js", ".mjs", ".jsx"],
            ast_grep_id="javascript",
            comment_patterns=["//", "/*", "*/"],
        ),
        "typescript": LanguageConfig(
            name="TypeScript",
            extensions=[".ts", ".tsx", ".d.ts"],
            ast_grep_id="typescript",
            comment_patterns=["//", "/*", "*/"],
        ),
        "html": LanguageConfig(
            name="HTML",
            extensions=[".html", ".htm"],
            ast_grep_id="html",
            comment_patterns=["<!--", "-->"],
        ),
        "css": LanguageConfig(
            name="CSS",
            extensions=[".css", ".scss", ".sass", ".less"],
            ast_grep_id="css",
            comment_patterns=["/*", "*/"],
        ),
        # Backend & Systems
        "python": LanguageConfig(
            name="Python",
            extensions=[".py", ".pyi", ".pyw"],
            ast_grep_id="python",
            comment_patterns=["#", '"""', "'''"],
        ),
        "java": LanguageConfig(
            name="Java",
            extensions=[".java"],
            ast_grep_id="java",
            comment_patterns=["//", "/*", "*/"],
        ),
        "csharp": LanguageConfig(
            name="C#",
            extensions=[".cs"],
            ast_grep_id="c_sharp",
            comment_patterns=["//", "/*", "*/"],
        ),
        "cpp": LanguageConfig(
            name="C++",
            extensions=[".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".h"],
            ast_grep_id="cpp",
            comment_patterns=["//", "/*", "*/"],
        ),
        "c": LanguageConfig(
            name="C", extensions=[".c", ".h"], ast_grep_id="c", comment_patterns=["//", "/*", "*/"]
        ),
        "rust": LanguageConfig(
            name="Rust", extensions=[".rs"], ast_grep_id="rust", comment_patterns=["//", "/*", "*/"]
        ),
        "go": LanguageConfig(
            name="Go", extensions=[".go"], ast_grep_id="go", comment_patterns=["//", "/*", "*/"]
        ),
        # JVM Languages
        "kotlin": LanguageConfig(
            name="Kotlin",
            extensions=[".kt", ".kts"],
            ast_grep_id="kotlin",
            comment_patterns=["//", "/*", "*/"],
        ),
        "scala": LanguageConfig(
            name="Scala",
            extensions=[".scala", ".sc"],
            ast_grep_id="scala",
            comment_patterns=["//", "/*", "*/"],
        ),
        # Functional Languages
        "elixir": LanguageConfig(
            name="Elixir", extensions=[".ex", ".exs"], ast_grep_id="elixir", comment_patterns=["#"]
        ),
        "elm": LanguageConfig(
            name="Elm", extensions=[".elm"], ast_grep_id="elm", comment_patterns=["--", "{-", "-}"]
        ),
        # Mobile Development
        "swift": LanguageConfig(
            name="Swift",
            extensions=[".swift"],
            ast_grep_id="swift",
            comment_patterns=["//", "/*", "*/"],
        ),
        "dart": LanguageConfig(
            name="Dart",
            extensions=[".dart"],
            ast_grep_id="dart",
            comment_patterns=["//", "/*", "*/"],
        ),
        # Scripting & Dynamic
        "ruby": LanguageConfig(
            name="Ruby", extensions=[".rb", ".rbw"], ast_grep_id="ruby", comment_patterns=["#"]
        ),
        "php": LanguageConfig(
            name="PHP",
            extensions=[".php", ".phtml"],
            ast_grep_id="php",
            comment_patterns=["//", "/*", "*/", "#"],
        ),
        "lua": LanguageConfig(
            name="Lua",
            extensions=[".lua"],
            ast_grep_id="lua",
            comment_patterns=["--", "--[[", "]]"],
        ),
        # Data & Config
        "sql": LanguageConfig(
            name="SQL", extensions=[".sql"], ast_grep_id="sql", comment_patterns=["--", "/*", "*/"]
        ),
        "yaml": LanguageConfig(
            name="YAML", extensions=[".yml", ".yaml"], ast_grep_id="yaml", comment_patterns=["#"]
        ),
        "json": LanguageConfig(
            name="JSON",
            extensions=[".json", ".jsonc"],
            ast_grep_id="json",
            comment_patterns=[],  # JSON doesn't support comments
        ),
        "toml": LanguageConfig(
            name="TOML", extensions=[".toml"], ast_grep_id="toml", comment_patterns=["#"]
        ),
        # Markup & Documentation
        "xml": LanguageConfig(
            name="XML",
            extensions=[".xml", ".xsd", ".xsl"],
            ast_grep_id="xml",
            comment_patterns=["<!--", "-->"],
        ),
        "markdown": LanguageConfig(
            name="Markdown",
            extensions=[".md", ".markdown"],
            ast_grep_id="markdown",
            comment_patterns=["<!--", "-->"],
        ),
        # Additional Enterprise Languages
        "haskell": LanguageConfig(
            name="Haskell",
            extensions=[".hs", ".lhs"],
            ast_grep_id="haskell",
            comment_patterns=["--", "{-", "-}"],
        ),
        "ocaml": LanguageConfig(
            name="OCaml",
            extensions=[".ml", ".mli"],
            ast_grep_id="ocaml",
            comment_patterns=["(*", "*)"],
        ),
        "fsharp": LanguageConfig(
            name="F#",
            extensions=[".fs", ".fsi", ".fsx"],
            ast_grep_id="fsharp",
            comment_patterns=["//", "(*", "*)"],
        ),
    }

    @classmethod
    def get_language_by_extension(cls, file_path: Path) -> Optional[LanguageConfig]:
        """Determine language from file extension."""
        ext = file_path.suffix.lower()
        for lang_config in cls.LANGUAGES.values():
            if ext in lang_config.extensions:
                return lang_config
        return None

    @classmethod
    def get_supported_extensions(cls) -> Set[str]:
        """Get all supported file extensions."""
        extensions = set()
        for config in cls.LANGUAGES.values():
            extensions.update(config.extensions)
        return extensions

    @classmethod
    def get_language_count(cls) -> int:
        """Get total number of supported languages."""
        return len(cls.LANGUAGES)


class UniversalParser:
    """Multi-language parser using ast-grep with universal graph output."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.registry = LanguageRegistry()
        self.node_id_counter = 0

    def _generate_node_id(self, file_path: Path, node_kind: str, line: int) -> str:
        """Generate unique node ID."""
        self.node_id_counter += 1
        return f"{file_path.stem}_{node_kind}_{line}_{self.node_id_counter}"

    def _extract_source_location(self, node: Any, file_path: Path) -> SourceLocation:
        """Extract source location from ast-grep node."""
        # ast-grep provides byte positions, convert to line/column
        # This is a simplified implementation - real implementation would need
        # to map byte positions to line/column coordinates
        return SourceLocation(
            file_path=file_path,
            start_line=1,  # Placeholder - need proper byte-to-line mapping
            start_column=1,
            end_line=1,
            end_column=len(node.text()) + 1,
        )

    def _extract_documentation(self, _node: Any, _language: str) -> Optional[str]:
        """Extract documentation/comments for a node."""
        # Look for preceding comments based on language patterns
        # lang_config = self.registry.LANGUAGES.get(_language)
        # if not lang_config or not lang_config.comment_patterns:
        # Simplified implementation - would need to scan preceding nodes
        # for comment patterns and extract documentation
        return None

    def _calculate_node_complexity(self, node: Any) -> int:
        """Calculate cyclomatic complexity for a node."""
        complexity = 1

        # Simple complexity calculation based on node text patterns
        # This avoids invalid AST kind issues while still providing useful metrics
        text = node.text().lower()

        # Count decision keywords that increase complexity
        decision_keywords = ["if", "while", "for", "switch", "case", "catch", "elif", "else if"]

        for keyword in decision_keywords:
            # Count occurrences but avoid double-counting (e.g., "else if" vs "if")
            if keyword in ("elif", "else if"):
                complexity += text.count("elif") + text.count("else if")
            elif keyword not in ["if"]:  # Skip 'if' to avoid double counting with elif
                complexity += text.count(f" {keyword} ") + text.count(f"{keyword}(")

        # Add basic if counting (avoiding elif double count)
        if_count = text.count(" if ") + text.count("if(")
        elif_count = text.count("elif") + text.count("else if")
        complexity += max(0, if_count - elif_count)

        return max(1, complexity)  # Minimum complexity is 1

    def _parse_node_recursive(
        self, node: Any, file_path: Path, language: str, parent_qualified_name: str = ""
    ) -> List[UniversalNode]:
        """Recursively parse ast-grep nodes into universal nodes."""
        nodes = []

        # Map ast-grep kind to universal type
        node_type = LanguageMapping.get_universal_type(language, node.kind())

        # Skip non-significant nodes
        if node_type == NodeType.REFERENCE and not self._is_significant_reference(node):
            return nodes

        # Generate node info
        node_id = self._generate_node_id(file_path, node.kind(), 1)
        node_text = node.text()
        node_name = self._extract_node_name(node, node_type)

        # Build qualified name
        if parent_qualified_name:
            qualified_name = f"{parent_qualified_name}.{node_name}"
        else:
            qualified_name = node_name

        # Create universal node
        universal_node = UniversalNode(
            id=node_id,
            node_type=node_type,
            name=node_name,
            qualified_name=qualified_name,
            location=self._extract_source_location(node, file_path),
            language=language,
            raw_kind=node.kind(),
            source_text=node_text,
            documentation=self._extract_documentation(node, language),
            complexity=self._calculate_node_complexity(node),
            line_count=len(node_text.split("\n")),
        )

        nodes.append(universal_node)

        # Process children recursively
        for child in node.children():
            child_nodes = self._parse_node_recursive(child, file_path, language, qualified_name)
            nodes.extend(child_nodes)

            # Add parent-child relationships
            for child_node in child_nodes:
                universal_node.add_child(child_node)

        return nodes

    def _extract_node_name(self, node: Any, node_type: NodeType) -> str:
        """Extract meaningful name from a node."""
        # Look for identifier children first
        identifiers = node.find_all({"rule": {"kind": "identifier"}})
        if identifiers:
            return identifiers[0].text()

        # Fallback to node text (truncated)
        text = node.text().strip()
        if len(text) > 50:
            text = text[:47] + "..."
        return text or f"anonymous_{node_type.value}"

    def _is_significant_reference(self, node: Any) -> bool:
        """Determine if a reference node is significant enough to include."""
        # Skip very short or common identifiers
        text = node.text().strip()
        if len(text) < 2 or text in ["i", "j", "k", "x", "y", "z"]:
            return False
        return True

    def parse_file(self, file_path: Path) -> Optional[UniversalGraph]:
        """Parse a single file into a universal graph."""
        try:
            # Detect language
            lang_config = self.registry.get_language_by_extension(file_path)
            if not lang_config:
                logger.warning("Unsupported file type: %s", file_path)
                return None

            # Read file content
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            # Parse with ast-grep
            root = ag.SgRoot(content, lang_config.ast_grep_id)
            root_node = root.root()

            # Convert to universal nodes
            nodes = self._parse_node_recursive(root_node, file_path, lang_config.name.lower())

            # Build graph
            graph = UniversalGraph()
            for node in nodes:
                graph.add_node(node)

            graph.file_count = 1

            logger.info("Parsed %s: %d nodes", file_path, len(nodes))
            return graph

        except (OSError, ValueError, RuntimeError) as e:
            logger.error("Failed to parse %s: %s", file_path, e)
            return None

    def parse_directory(
        self,
        directory: Optional[Path] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> UniversalGraph:
        """Parse all supported files in a directory."""
        if directory is None:
            directory = self.project_root

        combined_graph = UniversalGraph()
        supported_extensions = self.registry.get_supported_extensions()

        # Find all supported files
        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            # Check extension support
            if file_path.suffix.lower() not in supported_extensions:
                continue

            # Apply include/exclude patterns
            if include_patterns and not any(
                re.search(pattern, str(file_path)) for pattern in include_patterns
            ):
                continue

            if exclude_patterns and any(
                re.search(pattern, str(file_path)) for pattern in exclude_patterns
            ):
                continue

            # Parse file
            file_graph = self.parse_file(file_path)
            if file_graph:
                # Merge into combined graph
                for node in file_graph.nodes.values():
                    combined_graph.add_node(node)
                for relation in file_graph.relations:
                    combined_graph.add_relation(relation)

                combined_graph.file_count += 1

        logger.info(
            "Parsed %d files across %d languages",
            combined_graph.file_count,
            len(combined_graph.languages),
        )

        return combined_graph

    def get_supported_languages(self) -> List[str]:
        """Get list of all supported programming languages."""
        return [config.name for config in self.registry.LANGUAGES.values()]

    def get_language_stats(self) -> Dict[str, Union[int, Dict[str, int]]]:
        """Get statistics about supported languages."""
        return {
            "total_languages": self.registry.get_language_count(),
            "supported_extensions": len(self.registry.get_supported_extensions()),
            "language_categories": {
                "web_frontend": 4,
                "backend_systems": 7,
                "jvm_languages": 3,
                "functional": 2,
                "mobile": 2,
                "scripting": 3,
                "data_config": 4,
                "markup_docs": 2,
                "additional": 3,
            },
        }
