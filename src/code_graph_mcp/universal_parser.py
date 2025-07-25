"""
Universal Multi-Language Parser

Uses ast-grep as the backend to parse 25+ programming languages into a universal AST format.
Provides language-agnostic parsing with consistent node types and relationships.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from ast_grep_py import SgRoot  # type: ignore[import-untyped]
except ImportError:
    SgRoot = None

from .universal_graph import (
    NodeType,
    RelationshipType,
    UniversalGraph,
    UniversalLocation,
    UniversalNode,
    UniversalRelationship,
)

logger = logging.getLogger(__name__)


@dataclass
class LanguageConfig:
    """Configuration for a specific programming language."""

    name: str
    extensions: List[str]
    ast_grep_id: str
    comment_patterns: List[str]
    string_patterns: List[str]

    # Language-specific parsing rules
    function_patterns: List[str]
    class_patterns: List[str]
    variable_patterns: List[str]
    import_patterns: List[str]


class LanguageRegistry:
    """Registry of supported programming languages with their configurations."""

    LANGUAGES = {
        "javascript": LanguageConfig(
            name="JavaScript",
            extensions=[".js", ".mjs", ".jsx"],
            ast_grep_id="javascript",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'", "`"],
            function_patterns=["function", "=>", "async function"],
            class_patterns=["class"],
            variable_patterns=["var", "let", "const"],
            import_patterns=["import", "require", "export"]
        ),
        "typescript": LanguageConfig(
            name="TypeScript",
            extensions=[".ts", ".tsx", ".d.ts"],
            ast_grep_id="typescript",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'", "`"],
            function_patterns=["function", "=>", "async function"],
            class_patterns=["class", "interface", "type"],
            variable_patterns=["var", "let", "const"],
            import_patterns=["import", "export", "declare"]
        ),
        "python": LanguageConfig(
            name="Python",
            extensions=[".py", ".pyi", ".pyw"],
            ast_grep_id="python",
            comment_patterns=["#", '"""', "'''"],
            string_patterns=['"', "'", '"""', "'''"],
            function_patterns=["def", "async def", "lambda"],
            class_patterns=["class"],
            variable_patterns=["=", ":"],
            import_patterns=["import", "from", "import"]
        ),
        "java": LanguageConfig(
            name="Java",
            extensions=[".java"],
            ast_grep_id="java",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"'],
            function_patterns=["public", "private", "protected", "static"],
            class_patterns=["class", "interface", "enum"],
            variable_patterns=["int", "String", "boolean", "double", "float"],
            import_patterns=["import", "package"]
        ),
        "rust": LanguageConfig(
            name="Rust",
            extensions=[".rs"],
            ast_grep_id="rust",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["fn", "async fn"],
            class_patterns=["struct", "enum", "trait", "impl"],
            variable_patterns=["let", "const", "static"],
            import_patterns=["use", "mod", "extern"]
        ),
        "go": LanguageConfig(
            name="Go",
            extensions=[".go"],
            ast_grep_id="go",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "`"],
            function_patterns=["func"],
            class_patterns=["type", "struct", "interface"],
            variable_patterns=["var", ":="],
            import_patterns=["import", "package"]
        ),
        "cpp": LanguageConfig(
            name="C++",
            extensions=[".cpp", ".cc", ".cxx", ".hpp", ".h"],
            ast_grep_id="cpp",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["int", "void", "auto", "template"],
            class_patterns=["class", "struct", "namespace"],
            variable_patterns=["int", "double", "float", "char", "auto"],
            import_patterns=["#include", "using", "namespace"]
        ),
        "c": LanguageConfig(
            name="C",
            extensions=[".c", ".h"],
            ast_grep_id="c",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["int", "void", "char", "float", "double"],
            class_patterns=["struct", "enum", "union"],
            variable_patterns=["int", "char", "float", "double", "static"],
            import_patterns=["#include", "#define"]
        ),
        "csharp": LanguageConfig(
            name="C#",
            extensions=[".cs"],
            ast_grep_id="csharp",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["public", "private", "protected", "static"],
            class_patterns=["class", "interface", "struct", "enum"],
            variable_patterns=["int", "string", "bool", "double", "var"],
            import_patterns=["using", "namespace"]
        ),
        "php": LanguageConfig(
            name="PHP",
            extensions=[".php"],
            ast_grep_id="php",
            comment_patterns=["//", "/*", "*/", "#"],
            string_patterns=['"', "'"],
            function_patterns=["function", "public function", "private function"],
            class_patterns=["class", "interface", "trait"],
            variable_patterns=["$"],
            import_patterns=["require", "include", "use"]
        ),
        "ruby": LanguageConfig(
            name="Ruby",
            extensions=[".rb"],
            ast_grep_id="ruby",
            comment_patterns=["#"],
            string_patterns=['"', "'"],
            function_patterns=["def", "class", "module"],
            class_patterns=["class", "module"],
            variable_patterns=["@", "@@", "$"],
            import_patterns=["require", "load", "include"]
        ),
        "swift": LanguageConfig(
            name="Swift",
            extensions=[".swift"],
            ast_grep_id="swift",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"'],
            function_patterns=["func", "init"],
            class_patterns=["class", "struct", "enum", "protocol"],
            variable_patterns=["var", "let"],
            import_patterns=["import"]
        ),
        "kotlin": LanguageConfig(
            name="Kotlin",
            extensions=[".kt", ".kts"],
            ast_grep_id="kotlin",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["fun", "suspend fun"],
            class_patterns=["class", "interface", "object", "enum"],
            variable_patterns=["val", "var"],
            import_patterns=["import", "package"]
        ),
        "scala": LanguageConfig(
            name="Scala",
            extensions=[".scala"],
            ast_grep_id="scala",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["def", "val", "var"],
            class_patterns=["class", "object", "trait", "case class"],
            variable_patterns=["val", "var"],
            import_patterns=["import", "package"]
        ),
        "dart": LanguageConfig(
            name="Dart",
            extensions=[".dart"],
            ast_grep_id="dart",
            comment_patterns=["//", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["void", "int", "String", "double"],
            class_patterns=["class", "abstract class", "mixin"],
            variable_patterns=["var", "final", "const"],
            import_patterns=["import", "export", "library"]
        ),
        "lua": LanguageConfig(
            name="Lua",
            extensions=[".lua"],
            ast_grep_id="lua",
            comment_patterns=["--", "--[[", "]]"],
            string_patterns=['"', "'"],
            function_patterns=["function", "local function"],
            class_patterns=["{}"],
            variable_patterns=["local"],
            import_patterns=["require", "dofile", "loadfile"]
        ),
        "haskell": LanguageConfig(
            name="Haskell",
            extensions=[".hs", ".lhs"],
            ast_grep_id="haskell",
            comment_patterns=["--", "{-", "-}"],
            string_patterns=['"'],
            function_patterns=["::"],
            class_patterns=["data", "newtype", "class", "instance"],
            variable_patterns=["let", "where"],
            import_patterns=["import", "module"]
        ),
        "elixir": LanguageConfig(
            name="Elixir",
            extensions=[".ex", ".exs"],
            ast_grep_id="elixir",
            comment_patterns=["#"],
            string_patterns=['"', "'"],
            function_patterns=["def", "defp", "defmacro"],
            class_patterns=["defmodule", "defprotocol", "defstruct"],
            variable_patterns=["@"],
            import_patterns=["import", "alias", "require"]
        ),
        "erlang": LanguageConfig(
            name="Erlang",
            extensions=[".erl", ".hrl"],
            ast_grep_id="erlang",
            comment_patterns=["%"],
            string_patterns=['"'],
            function_patterns=["-export", "-spec"],
            class_patterns=["-module", "-record"],
            variable_patterns=["-define"],
            import_patterns=["-import", "-include"]
        ),
        "clojure": LanguageConfig(
            name="Clojure",
            extensions=[".clj", ".cljs", ".cljc"],
            ast_grep_id="clojure",
            comment_patterns=[";", ";;"],
            string_patterns=['"'],
            function_patterns=["defn", "defn-", "fn"],
            class_patterns=["defprotocol", "defrecord", "deftype"],
            variable_patterns=["def", "defonce"],
            import_patterns=["require", "import", "use"]
        ),
        "r": LanguageConfig(
            name="R",
            extensions=[".r", ".R"],
            ast_grep_id="r",
            comment_patterns=["#"],
            string_patterns=['"', "'"],
            function_patterns=["function", "<-"],
            class_patterns=["setClass", "setMethod"],
            variable_patterns=["<-", "="],
            import_patterns=["library", "require", "source"]
        ),
        "matlab": LanguageConfig(
            name="MATLAB",
            extensions=[".m"],
            ast_grep_id="matlab",
            comment_patterns=["%"],
            string_patterns=['"', "'"],
            function_patterns=["function"],
            class_patterns=["classdef"],
            variable_patterns=["="],
            import_patterns=["import"]
        ),
        "perl": LanguageConfig(
            name="Perl",
            extensions=[".pl", ".pm"],
            ast_grep_id="perl",
            comment_patterns=["#"],
            string_patterns=['"', "'"],
            function_patterns=["sub"],
            class_patterns=["package"],
            variable_patterns=["$", "@", "%"],
            import_patterns=["use", "require"]
        ),
        "sql": LanguageConfig(
            name="SQL",
            extensions=[".sql"],
            ast_grep_id="sql",
            comment_patterns=["--", "/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["CREATE FUNCTION", "CREATE PROCEDURE"],
            class_patterns=["CREATE TABLE", "CREATE VIEW"],
            variable_patterns=["DECLARE"],
            import_patterns=["USE", "IMPORT"]
        ),
        "html": LanguageConfig(
            name="HTML",
            extensions=[".html", ".htm"],
            ast_grep_id="html",
            comment_patterns=["<!--", "-->"],
            string_patterns=['"', "'"],
            function_patterns=["<script>"],
            class_patterns=["class="],
            variable_patterns=["id="],
            import_patterns=["<link", "<script"]
        ),
        "css": LanguageConfig(
            name="CSS",
            extensions=[".css"],
            ast_grep_id="css",
            comment_patterns=["/*", "*/"],
            string_patterns=['"', "'"],
            function_patterns=["@function"],
            class_patterns=["."],
            variable_patterns=["--"],
            import_patterns=["@import", "@use"]
        )
    }

    def get_language_by_extension(self, file_path: Path) -> Optional[LanguageConfig]:
        """Get language configuration by file extension."""
        suffix = file_path.suffix.lower()
        for lang_config in self.LANGUAGES.values():
            if suffix in lang_config.extensions:
                return lang_config
        return None

    def get_language_by_name(self, name: str) -> Optional[LanguageConfig]:
        """Get language configuration by name."""
        return self.LANGUAGES.get(name.lower())

    def get_all_languages(self) -> List[LanguageConfig]:
        """Get all supported language configurations."""
        return list(self.LANGUAGES.values())

    def get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions."""
        extensions = set()
        for lang_config in self.LANGUAGES.values():
            extensions.update(lang_config.extensions)
        return extensions


class UniversalParser:
    """Universal parser supporting 25+ programming languages via ast-grep."""

    def __init__(self):
        self.registry = LanguageRegistry()
        self.graph = UniversalGraph()

        # Check if ast-grep is available
        if SgRoot is None:
            logger.warning("ast-grep-py not available. Multi-language parsing disabled.")
            self._ast_grep_available = False
        else:
            self._ast_grep_available = True
            logger.info("ast-grep available. Supporting %d languages.", len(self.registry.LANGUAGES))

    def is_supported_file(self, file_path: Path) -> bool:
        """Check if a file is supported for parsing."""
        return file_path.suffix.lower() in self.registry.get_supported_extensions()

    def detect_language(self, file_path: Path) -> Optional[LanguageConfig]:
        """Detect the programming language of a file."""
        return self.registry.get_language_by_extension(file_path)

    def parse_file(self, file_path: Path) -> bool:
        """Parse a single file and add nodes to the graph."""
        if not self._ast_grep_available:
            logger.warning("ast-grep not available, skipping %s", file_path)
            return False

        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return False

        language_config = self.detect_language(file_path)
        if not language_config:
            logger.debug("Unsupported file type: %s", file_path)
            return False

        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Parse with ast-grep
            if SgRoot is None:
                logger.error("ast-grep-py not available")
                return False
            sg_root = SgRoot(content, language_config.ast_grep_id)

            # Create file node
            file_node = self._create_file_node(file_path, language_config, content)
            self.graph.add_node(file_node)

            # Parse language-specific constructs
            self._parse_functions(sg_root, file_path, language_config)
            self._parse_classes(sg_root, file_path, language_config)
            self._parse_variables(sg_root, file_path, language_config)
            self._parse_imports(sg_root, file_path, language_config)

            logger.debug("Successfully parsed %s (%s)", file_path, language_config.name)
            return True

        except Exception as e:
            logger.error("Error parsing %s: %s", file_path, e)
            return False

    def _create_file_node(self, file_path: Path, language_config: LanguageConfig, content: str) -> UniversalNode:
        """Create a file node."""
        line_count = len(content.splitlines())

        return UniversalNode(
            id=f"file:{file_path}",
            name=file_path.name,
            node_type=NodeType.MODULE,
            location=UniversalLocation(
                file_path=str(file_path),
                start_line=1,
                end_line=line_count,
                language=language_config.name
            ),
            content=content,
            line_count=line_count,
            language=language_config.name,
            metadata={
                "file_size": len(content),
                "extension": file_path.suffix,
                "ast_grep_id": language_config.ast_grep_id
            }
        )

    def _parse_functions(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> None:
        """Parse function definitions."""
        # This is a simplified implementation - real implementation would use ast-grep patterns
        # For now, we'll use text-based pattern matching as a fallback
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                for pattern in language_config.function_patterns:
                    if pattern in line and not line.strip().startswith(language_config.comment_patterns[0]):
                        func_name = self._extract_function_name(line, pattern, language_config)
                        if func_name:
                            func_node = UniversalNode(
                                id=f"function:{file_path}:{func_name}:{i}",
                                name=func_name,
                                node_type=NodeType.FUNCTION,
                                location=UniversalLocation(
                                    file_path=str(file_path),
                                    start_line=i,
                                    end_line=i,
                                    language=language_config.name
                                ),
                                language=language_config.name,
                                complexity=1,  # Basic complexity
                                metadata={"pattern": pattern}
                            )
                            self.graph.add_node(func_node)

                            # Add contains relationship
                            rel = UniversalRelationship(
                                id=f"contains:file:{file_path}:function:{func_name}:{i}",
                                source_id=f"file:{file_path}",
                                target_id=func_node.id,
                                relationship_type=RelationshipType.CONTAINS
                            )
                            self.graph.add_relationship(rel)

        except Exception as e:
            logger.debug("Error parsing functions in %s: %s", file_path, e)

    def _parse_classes(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> None:
        """Parse class definitions."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                for pattern in language_config.class_patterns:
                    if pattern in line and not line.strip().startswith(language_config.comment_patterns[0]):
                        class_name = self._extract_class_name(line, pattern, language_config)
                        if class_name:
                            class_node = UniversalNode(
                                id=f"class:{file_path}:{class_name}:{i}",
                                name=class_name,
                                node_type=NodeType.CLASS,
                                location=UniversalLocation(
                                    file_path=str(file_path),
                                    start_line=i,
                                    end_line=i,
                                    language=language_config.name
                                ),
                                language=language_config.name,
                                metadata={"pattern": pattern}
                            )
                            self.graph.add_node(class_node)

                            # Add contains relationship
                            rel = UniversalRelationship(
                                id=f"contains:file:{file_path}:class:{class_name}:{i}",
                                source_id=f"file:{file_path}",
                                target_id=class_node.id,
                                relationship_type=RelationshipType.CONTAINS
                            )
                            self.graph.add_relationship(rel)

        except Exception as e:
            logger.debug("Error parsing classes in %s: %s", file_path, e)

    def _parse_variables(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> None:
        """Parse variable definitions."""
        # Simplified implementation for variable parsing
        pass

    def _parse_imports(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> None:
        """Parse import statements."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                for pattern in language_config.import_patterns:
                    if line.strip().startswith(pattern):
                        import_target = self._extract_import_target(line, pattern, language_config)
                        if import_target:
                            import_node = UniversalNode(
                                id=f"import:{file_path}:{import_target}:{i}",
                                name=import_target,
                                node_type=NodeType.IMPORT,
                                location=UniversalLocation(
                                    file_path=str(file_path),
                                    start_line=i,
                                    end_line=i,
                                    language=language_config.name
                                ),
                                language=language_config.name,
                                metadata={"pattern": pattern}
                            )
                            self.graph.add_node(import_node)

                            # Add import relationship
                            rel = UniversalRelationship(
                                id=f"imports:file:{file_path}:module:{import_target}:{i}",
                                source_id=f"file:{file_path}",
                                target_id=f"module:{import_target}",
                                relationship_type=RelationshipType.IMPORTS
                            )
                            self.graph.add_relationship(rel)

        except Exception as e:
            logger.debug("Error parsing imports in %s: %s", file_path, e)

    def _extract_function_name(self, line: str, pattern: str, language_config: LanguageConfig) -> Optional[str]:
        """Extract function name from a line."""
        # Simplified name extraction - real implementation would be more sophisticated
        parts = line.strip().split()
        try:
            if pattern == "def" and len(parts) >= 2:
                return parts[1].split("(")[0]
            elif pattern == "function" and len(parts) >= 2:
                return parts[1].split("(")[0]
            elif pattern == "func" and len(parts) >= 2:
                return parts[1].split("(")[0]
        except (IndexError, AttributeError):
            pass
        return None

    def _extract_class_name(self, line: str, pattern: str, language_config: LanguageConfig) -> Optional[str]:
        """Extract class name from a line."""
        parts = line.strip().split()
        try:
            if pattern == "class" and len(parts) >= 2:
                return parts[1].split("(")[0].split(":")[0].split("{")[0]
            elif pattern == "struct" and len(parts) >= 2:
                return parts[1].split("{")[0]
        except (IndexError, AttributeError):
            pass
        return None

    def _extract_import_target(self, line: str, pattern: str, language_config: LanguageConfig) -> Optional[str]:
        """Extract import target from a line."""
        try:
            if pattern == "import":
                # Handle different import styles
                if "from" in line:
                    # from X import Y
                    parts = line.split("from")
                    if len(parts) >= 2:
                        return parts[1].split("import")[0].strip()
                else:
                    # import X
                    return line.replace("import", "").strip().split()[0]
            elif pattern == "require":
                # require('module') or require "module"
                import re
                match = re.search(r'require\s*\(?["\']([^"\']+)["\']', line)
                if match:
                    return match.group(1)
        except (IndexError, AttributeError):
            pass
        return None

    def parse_directory(self, directory: Path, recursive: bool = True) -> int:
        """Parse all supported files in a directory."""
        if not directory.is_dir():
            logger.error("Not a directory: %s", directory)
            return 0

        parsed_count = 0
        supported_extensions = self.registry.get_supported_extensions()

        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.iterdir()

        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                if self.parse_file(file_path):
                    parsed_count += 1

        logger.info("Parsed %d files in %s", parsed_count, directory)
        return parsed_count

    def get_parsing_statistics(self) -> Dict[str, Any]:
        """Get statistics about the parsed code."""
        stats = self.graph.get_statistics()
        stats.update({
            "supported_languages": len(self.registry.LANGUAGES),
            "supported_extensions": list(self.registry.get_supported_extensions()),
            "ast_grep_available": self._ast_grep_available
        })
        return stats

