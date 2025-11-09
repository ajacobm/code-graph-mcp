"""
Universal Multi-Language Parser

Uses ast-grep as the backend to parse 25+ programming languages into a universal AST format.
Provides language-agnostic parsing with consistent node types and relationships.

FIX (Jan 7, 2025): Implemented proper AST-Grep queries to replace text-based fallback parsing
"""

import logging
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from ast_grep_py import SgRoot  # type: ignore[import-untyped]
except ImportError:
    SgRoot = None

from .cache_manager import HybridCacheManager, cached_method
from .redis_cache import RedisConfig

from .universal_graph import (
    NodeType,
    RelationshipType,
    UniversalLocation,
    UniversalNode,
    UniversalRelationship,
)
from .graph import RustworkxCodeGraph

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LanguageConfig:
    """Configuration for a specific programming language."""

    name: str
    extensions: tuple
    ast_grep_id: str
    comment_patterns: tuple
    string_patterns: tuple

    # Language-specific parsing rules
    function_patterns: tuple
    class_patterns: tuple
    variable_patterns: tuple
    import_patterns: tuple


class LanguageRegistry:
    """Registry of supported programming languages with their configurations."""

    def __init__(self, cache_manager: Optional[HybridCacheManager] = None):
        self.cache_manager = cache_manager
        self._supported_extensions_cache: Optional[Set[str]] = None

    LANGUAGES = {
        "javascript": LanguageConfig(
            name="JavaScript",
            extensions=(".js", ".mjs", ".jsx"),
            ast_grep_id="javascript",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'", "`"),
            function_patterns=("function", "=>", "async function"),
            class_patterns=("class",),
            variable_patterns=("var", "let", "const"),
            import_patterns=("import", "require", "export")
        ),
        "typescript": LanguageConfig(
            name="TypeScript",
            extensions=(".ts", ".tsx", ".d.ts"),
            ast_grep_id="typescript",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'", "`"),
            function_patterns=("function", "=>", "async function"),
            class_patterns=("class", "interface", "type"),
            variable_patterns=("var", "let", "const"),
            import_patterns=("import", "export", "declare")
        ),
        "python": LanguageConfig(
            name="Python",
            extensions=(".py", ".pyi", ".pyw"),
            ast_grep_id="python",
            comment_patterns=("#", '"""', "'''"),
            string_patterns=('"', "'", '"""', "'''"),
            function_patterns=("def", "async def", "lambda"),
            class_patterns=("class",),
            variable_patterns=("=", ":"),
            import_patterns=("import", "from", "import")
        ),
        "java": LanguageConfig(
            name="Java",
            extensions=(".java",),
            ast_grep_id="java",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"',),
            function_patterns=("public", "private", "protected", "static"),
            class_patterns=("class", "interface", "enum"),
            variable_patterns=("int", "String", "boolean", "double", "float"),
            import_patterns=("import", "package")
        ),
        "rust": LanguageConfig(
            name="Rust",
            extensions=(".rs",),
            ast_grep_id="rust",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("fn", "async fn"),
            class_patterns=("struct", "enum", "trait", "impl"),
            variable_patterns=("let", "const", "static"),
            import_patterns=("use", "mod", "extern")
        ),
        "go": LanguageConfig(
            name="Go",
            extensions=(".go",),
            ast_grep_id="go",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "`"),
            function_patterns=("func",),
            class_patterns=("type", "struct", "interface"),
            variable_patterns=("var", ":="),
            import_patterns=("import", "package")
        ),
        "cpp": LanguageConfig(
            name="C++",
            extensions=(".cpp", ".cc", ".cxx", ".hpp", ".h"),
            ast_grep_id="cpp",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("int", "void", "auto", "template"),
            class_patterns=("class", "struct", "namespace"),
            variable_patterns=("int", "double", "float", "char", "auto"),
            import_patterns=("#include", "using", "namespace")
        ),
        "c": LanguageConfig(
            name="C",
            extensions=(".c", ".h"),
            ast_grep_id="c",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("int", "void", "char", "float", "double"),
            class_patterns=("struct", "enum", "union"),
            variable_patterns=("int", "char", "float", "double", "static"),
            import_patterns=("#include", "#define")
        ),
        "csharp": LanguageConfig(
            name="C#",
            extensions=(".cs",),
            ast_grep_id="csharp",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("public", "private", "protected", "static"),
            class_patterns=("class", "interface", "struct", "enum", "record"),
            variable_patterns=("int", "string", "bool", "double", "var", "datetime", "float"),
            import_patterns=("using", "namespace")
        ),
        "php": LanguageConfig(
            name="PHP",
            extensions=(".php",),
            ast_grep_id="php",
            comment_patterns=("//", "/*", "*/", "#"),
            string_patterns=('"', "'"),
            function_patterns=("function", "public function", "private function"),
            class_patterns=("class", "interface", "trait"),
            variable_patterns=("$",),
            import_patterns=("require", "include", "use")
        ),
        "ruby": LanguageConfig(
            name="Ruby",
            extensions=(".rb",),
            ast_grep_id="ruby",
            comment_patterns=("#",),
            string_patterns=('"', "'"),
            function_patterns=("def", "class", "module"),
            class_patterns=("class", "module"),
            variable_patterns=("@", "@@", "$"),
            import_patterns=("require", "load", "include")
        ),
        "swift": LanguageConfig(
            name="Swift",
            extensions=(".swift",),
            ast_grep_id="swift",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"',),
            function_patterns=("func", "init"),
            class_patterns=("class", "struct", "enum", "protocol"),
            variable_patterns=("var", "let"),
            import_patterns=("import",)
        ),
        "kotlin": LanguageConfig(
            name="Kotlin",
            extensions=(".kt", ".kts"),
            ast_grep_id="kotlin",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("fun", "suspend fun"),
            class_patterns=("class", "interface", "object", "enum"),
            variable_patterns=("val", "var"),
            import_patterns=("import", "package")
        ),
        "scala": LanguageConfig(
            name="Scala",
            extensions=(".scala",),
            ast_grep_id="scala",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("def", "val", "var"),
            class_patterns=("class", "object", "trait", "case class"),
            variable_patterns=("val", "var"),
            import_patterns=("import", "package")
        ),
        "dart": LanguageConfig(
            name="Dart",
            extensions=(".dart",),
            ast_grep_id="dart",
            comment_patterns=("//", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("void", "int", "String", "double"),
            class_patterns=("class", "abstract class", "mixin"),
            variable_patterns=("var", "final", "const"),
            import_patterns=("import", "export", "library")
        ),
        "lua": LanguageConfig(
            name="Lua",
            extensions=(".lua",),
            ast_grep_id="lua",
            comment_patterns=("--", "--[[", "]]"),
            string_patterns=('"', "'"),
            function_patterns=("function", "local function"),
            class_patterns=("{}",),
            variable_patterns=("local",),
            import_patterns=("require", "dofile", "loadfile")
        ),
        "haskell": LanguageConfig(
            name="Haskell",
            extensions=(".hs", ".lhs"),
            ast_grep_id="haskell",
            comment_patterns=("--", "{-", "-}"),
            string_patterns=('"',),
            function_patterns=("::",),
            class_patterns=("data", "newtype", "class", "instance"),
            variable_patterns=("let", "where"),
            import_patterns=("import", "module")
        ),
        "elixir": LanguageConfig(
            name="Elixir",
            extensions=(".ex", ".exs"),
            ast_grep_id="elixir",
            comment_patterns=("#",),
            string_patterns=('"', "'"),
            function_patterns=("def", "defp", "defmacro"),
            class_patterns=("defmodule", "defprotocol", "defstruct"),
            variable_patterns=("@",),
            import_patterns=("import", "alias", "require")
        ),
        "erlang": LanguageConfig(
            name="Erlang",
            extensions=(".erl", ".hrl"),
            ast_grep_id="erlang",
            comment_patterns=("%",),
            string_patterns=('"',),
            function_patterns=("-export", "-spec"),
            class_patterns=("-module", "-record"),
            variable_patterns=("-define",),
            import_patterns=("-import", "-include")
        ),
        "r": LanguageConfig(
            name="R",
            extensions=(".r", ".R"),
            ast_grep_id="r",
            comment_patterns=("#",),
            string_patterns=('"', "'"),
            function_patterns=("function", "<-"),
            class_patterns=("setClass", "setMethod"),
            variable_patterns=("<-", "="),
            import_patterns=("library", "require", "source")
        ),
        "matlab": LanguageConfig(
            name="MATLAB",
            extensions=(".m",),
            ast_grep_id="matlab",
            comment_patterns=("%",),
            string_patterns=('"', "'"),
            function_patterns=("function",),
            class_patterns=("classdef",),
            variable_patterns=("=",),
            import_patterns=("import",)
        ),
        "perl": LanguageConfig(
            name="Perl",
            extensions=(".pl", ".pm"),
            ast_grep_id="perl",
            comment_patterns=("#",),
            string_patterns=('"', "'"),
            function_patterns=("sub",),
            class_patterns=("package",),
            variable_patterns=("$", "@", "%"),
            import_patterns=("use", "require")
        ),
        "sql": LanguageConfig(
            name="SQL",
            extensions=(".sql",),
            ast_grep_id="sql",
            comment_patterns=("--", "/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("CREATE FUNCTION", "CREATE PROCEDURE"),
            class_patterns=("CREATE TABLE", "CREATE VIEW"),
            variable_patterns=("DECLARE",),
            import_patterns=("USE", "IMPORT")
        ),
        "html": LanguageConfig(
            name="HTML",
            extensions=(".html", ".htm"),
            ast_grep_id="html",
            comment_patterns=("<!--", "-->"),
            string_patterns=('"', "'"),
            function_patterns=("<script>",),
            class_patterns=("class=",),
            variable_patterns=("id=",),
            import_patterns=("<link", "<script")
        ),
        "css": LanguageConfig(
            name="CSS",
            extensions=(".css",),
            ast_grep_id="css",
            comment_patterns=("/*", "*/"),
            string_patterns=('"', "'"),
            function_patterns=("@function",),
            class_patterns=(".",),
            variable_patterns=("--",),
            import_patterns=("@import", "@use")
        )
    }

    async def get_language_by_extension(self, file_path: Path) -> Optional[LanguageConfig]:
        """Get language configuration by file extension."""
        suffix = file_path.suffix.lower()
        for lang_config in self.LANGUAGES.values():
            if suffix in lang_config.extensions:
                return lang_config
        return None

    async def get_language_by_name(self, name: str) -> Optional[LanguageConfig]:
        """Get language configuration by name."""
        return self.LANGUAGES.get(name.lower())

    def get_all_languages(self) -> List[LanguageConfig]:
        """Get all supported language configurations."""
        return list(self.LANGUAGES.values())

    @property
    def supported_extensions(self) -> Set[str]:
        """Get all supported file extensions (synchronous)."""
        if self._supported_extensions_cache is None:
            extensions = set()
            for lang_config in self.LANGUAGES.values():
                extensions.update(lang_config.extensions)
            self._supported_extensions_cache = extensions
        return self._supported_extensions_cache

    @cached_method(ttl=86400, key_generator=lambda self: "supported_extensions")
    async def get_supported_extensions(self) -> Set[str]:
        """Get all supported file extensions with hybrid caching."""
        return self.supported_extensions


class ASTGrepPatterns:
    """Language-specific AST patterns for ast-grep queries."""
    
    # AST-Grep patterns for each language
    # Verified against ast-grep-py 0.39.0+ API
    # FIX (Oct 26, 2025): Added patterns for all 25 supported languages
    PATTERNS = {
        "python": {
            "function": "function_definition",
            "class": "class_definition",
            "import": "import_statement",
            "variable": "assignment",
            "call": "call",
        },
        "javascript": {
            "function": "function_declaration",
            "class": "class_declaration",
            "import": "import_statement",
            "variable": "variable_declarator",
            "call": "call_expression",
        },
        "typescript": {
            "function": "function_declaration",
            "class": "class_declaration",
            "import": "import_statement",
            "variable": "variable_declarator",
            "call": "call_expression",
        },
        "java": {
            "function": "method_declaration",
            "class": "class_declaration",
            "import": "import_declaration",
            "variable": "field_declaration",
            "call": "method_invocation",
        },
        "rust": {
            "function": "function_item",
            "class": "struct_item",
            "import": "use_declaration",
            "variable": "let_statement",
            "call": "call_expression",
        },
        "go": {
            "function": "function_declaration",
            "class": "type_spec",
            "import": "import_declaration",
            "variable": "var_declaration",
            "call": "call_expression",
        },
        "cpp": {
            "function": "function_definition",
            "class": "class_specifier",
            "import": "preproc_include",
            "variable": "declaration",
            "call": "call_expression",
        },
        "c": {
            "function": "function_definition",
            "class": "struct_specifier",
            "import": "preproc_include",
            "variable": "declaration",
            "call": "call_expression",
        },
        "csharp": {
            "function": "method_declaration",
            "class": "class_declaration",
            "import": "using_directive",
            "variable": "variable_declarator",
            "call": "invocation_expression",
        },
        "php": {
            "function": "function_definition",
            "class": "class_declaration",
            "import": "require_expression",
            "variable": "assignment",
            "call": "function_call_expression",
        },
        "ruby": {
            "function": "method",
            "class": "class_definition",
            "import": "require",
            "variable": "assignment",
            "call": "method_call",
        },
        "swift": {
            "function": "function_declaration",
            "class": "class_declaration",
            "import": "import_statement",
            "variable": "variable_declaration",
            "call": "function_call_expression",
        },
        "kotlin": {
            "function": "function_declaration",
            "class": "class_declaration",
            "import": "import_header",
            "variable": "property_declaration",
            "call": "call_expression",
        },
        "scala": {
            "function": "function_definition",
            "class": "class_definition",
            "import": "import_declaration",
            "variable": "val_definition",
            "call": "call_expression",
        },
        "dart": {
            "function": "function_declaration",
            "class": "class_declaration",
            "import": "import_or_export",
            "variable": "variable_declaration",
            "call": "method_invocation",
        },
        "lua": {
            "function": "function_definition",
            "class": "assignment_statement",
            "import": "require",
            "variable": "assignment_statement",
            "call": "function_call",
        },
        "haskell": {
            "function": "function",
            "class": "type_class_declaration",
            "import": "import_declaration",
            "variable": "let_binding",
            "call": "function_application",
        },
        "elixir": {
            "function": "definition",
            "class": "module",
            "import": "alias_or_require",
            "variable": "match_expression",
            "call": "call",
        },
        "erlang": {
            "function": "function_clause",
            "class": "attribute",
            "import": "attribute",
            "variable": "variable",
            "call": "call_expression",
        },
        "r": {
            "function": "function_definition",
            "class": "class_definition",
            "import": "library_call",
            "variable": "assignment",
            "call": "call",
        },
        "matlab": {
            "function": "function_definition",
            "class": "classdef_block",
            "import": "import_statement",
            "variable": "assignment",
            "call": "function_call",
        },
        "perl": {
            "function": "subroutine_declaration",
            "class": "package_declaration",
            "import": "use_statement",
            "variable": "assignment",
            "call": "function_call",
        },
        "sql": {
            "function": "create_function_statement",
            "class": "create_table_statement",
            "import": "use_statement",
            "variable": "declare_statement",
            "call": "function_call",
        },
        "html": {
            "function": "script_element",
            "class": "attribute_value",
            "import": "tag",
            "variable": "attribute_value",
            "call": "tag",
        },
        "css": {
            "function": "at_rule",
            "class": "class_selector",
            "import": "at_import",
            "variable": "custom_property",
            "call": "function_call",
        },
    }
    
    @classmethod
    def get_pattern(cls, language_id: str, node_type: str) -> Optional[str]:
        """Get AST pattern for a language and node type.
        
        Returns None for unsupported language/type combinations.
        Falls back to basic pattern matching if AST pattern not available.
        """
        patterns = cls.PATTERNS.get(language_id, {})
        return patterns.get(node_type)


class UniversalParser:
    """Universal parser supporting 25+ programming languages via ast-grep."""

    def __init__(self, redis_config: Optional[RedisConfig] = None, enable_redis_cache: bool = True):
        # Initialize cache manager first
        self.cache_manager: Optional[HybridCacheManager] = None
        self._cache_enabled = enable_redis_cache and redis_config is not None
        
        if self._cache_enabled:
            from .cache_manager import HybridCacheManager, CacheStrategy
            self.cache_manager = HybridCacheManager(
                redis_config=redis_config,
                strategy=CacheStrategy.HYBRID
            )
            
        # Initialize registry with cache manager
        self.registry = LanguageRegistry(self.cache_manager)
        self.graph = RustworkxCodeGraph()
            
        # Gitignore pattern caching - NEW: optimize the performance bottleneck
        self._gitignore_patterns: Optional[List[str]] = None
        self._gitignore_compiled: Optional[Any] = None  # pathspec.PathSpec when available
        self._project_root: Optional[Path] = None

        # Check if ast-grep is available
        if SgRoot is None:
            logger.warning("ast-grep-py not available. Multi-language parsing disabled.")
            self._ast_grep_available = False
        else:
            self._ast_grep_available = True
            logger.info("ast-grep available. Supporting %d languages.", len(self.registry.LANGUAGES))
    
    async def initialize_cache(self) -> bool:
        """Initialize the cache backend."""
        if self.cache_manager:
            success = await self.cache_manager.initialize()
            if success:
                logger.info("Redis cache backend initialized successfully")
            else:
                logger.warning("Redis cache backend initialization failed")
            return success
        return True
    
    async def cleanup_cache(self):
        """Cleanup cache resources."""
        if self.cache_manager:
            await self.cache_manager.close()

    async def is_supported_file(self, file_path: Path) -> bool:
        """Check if a file is supported for parsing."""
        supported_extensions = await self.registry.get_supported_extensions()
        return file_path.suffix.lower() in supported_extensions

    async def detect_language(self, file_path: Path) -> Optional[LanguageConfig]:
        """Detect the programming language of a file."""
        return await self.registry.get_language_by_extension(file_path)

    async def parse_file(self, file_path: Path) -> bool:
        """Parse a single file and add nodes to the graph with caching support."""
        if not self._ast_grep_available:
            logger.warning("ast-grep not available, skipping %s", file_path)
            return False

        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return False

        language_config = await self.detect_language(file_path)
        if not language_config:
            logger.debug("Unsupported file type: %s", file_path)
            return False

        # Check cache first if available
        if self.cache_manager and await self.cache_manager.is_file_cached(file_path):
            logger.debug(f"Loading cached data for {file_path}")
            return await self._load_cached_file_data(file_path)

        try:
            # Parse the file
            success = await self._parse_file_content(file_path, language_config)
            
            # Cache the results if successful
            if success and self.cache_manager:
                await self._cache_file_results(file_path)
            
            return success

        except Exception as e:
            logger.error("Error parsing %s: %s", file_path, e)
            return False
    
    async def _load_cached_file_data(self, file_path: Path) -> bool:
        """Load cached file data into the graph."""
        try:
            # Load cached nodes
            cached_nodes = await self.cache_manager.get_file_nodes(str(file_path))
            if cached_nodes:
                for node_dict in cached_nodes:
                    node = self._dict_to_node(node_dict)
                    self.graph.add_node(node)
            
            # Load cached relationships
            cached_rels = await self.cache_manager.get_file_relationships(str(file_path))
            if cached_rels:
                for rel_dict in cached_rels:
                    rel = self._dict_to_relationship(rel_dict)
                    self.graph.add_relationship(rel)
            
            # Track as processed
            self.graph.add_processed_file(str(file_path))
            
            logger.debug(f"Successfully loaded cached data for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading cached data for {file_path}: {e}")
            return False
    
    async def _cache_file_results(self, file_path: Path) -> bool:
        """Cache the parsing results for a file."""
        try:
            # Get nodes for this file
            file_nodes = [node for node in self.graph.nodes.values() 
                         if node.location.file_path == str(file_path)]
            
            # Get relationships for this file
            file_relationships = [rel for rel in self.graph.relationships.values()
                                if any(node.id in [rel.source_id, rel.target_id] for node in file_nodes)]
            
            # Cache nodes and relationships
            await self.cache_manager.set_file_nodes(str(file_path), file_nodes)
            await self.cache_manager.set_file_relationships(str(file_path), file_relationships)
            
            logger.debug(f"Successfully cached results for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching results for {file_path}: {e}")
            return False
    
    def _dict_to_node(self, node_dict: Dict) -> UniversalNode:
        """Convert dictionary back to UniversalNode."""
        location_dict = node_dict.get('location', {})
        location = UniversalLocation(
            file_path=location_dict.get('file_path', ''),
            start_line=location_dict.get('start_line', 1),
            end_line=location_dict.get('end_line'),
            language=location_dict.get('language', '')
        )
        
        return UniversalNode(
            id=node_dict['id'],
            name=node_dict['name'],
            node_type=NodeType(node_dict['node_type']),
            location=location,
            content=node_dict.get('content'),
            complexity=node_dict.get('complexity', 0),
            language=node_dict.get('language'),
            metadata=node_dict.get('metadata', {})
        )
    
    def _dict_to_relationship(self, rel_dict: Dict) -> UniversalRelationship:
        """Convert dictionary back to UniversalRelationship."""
        # Convert string to RelationshipType enum
        rel_type_str = rel_dict['relationship_type']
        try:
            relationship_type = RelationshipType(rel_type_str)
        except ValueError:
            # Fallback for malformed data
            logger.warning(f"Unknown relationship type: {rel_type_str}, using RelationshipType.CALLS")
            relationship_type = RelationshipType.CALLS
        
        return UniversalRelationship(
            id=rel_dict['id'],
            source_id=rel_dict['source_id'],
            target_id=rel_dict['target_id'],
            relationship_type=relationship_type,
            metadata=rel_dict.get('metadata', {})
        )
    
    async def _parse_file_content(self, file_path: Path, language_config: LanguageConfig) -> bool:
        """Parse file content using AST-Grep queries (FIXED: Jan 7, 2025)."""
        try:
            logger.debug(f"_parse_file_content START: {file_path}, language={language_config.ast_grep_id}")
            # Read file content with proper encoding detection
            content = self._read_file_with_encoding_detection(file_path)
            logger.debug(f"_parse_file_content: read {len(content)} bytes")

            # Parse with ast-grep
            if SgRoot is None:
                logger.error("ast-grep-py not available")
                return False
            
            logger.debug(f"_parse_file_content: creating SgRoot...")
            sg_root = SgRoot(content, language_config.ast_grep_id)
            logger.debug(f"_parse_file_content: SgRoot created")

            # Create file node
            file_node = self._create_file_node(file_path, language_config, content)
            self.graph.add_node(file_node)
            logger.debug(f"_parse_file_content: file node created")

            # Track processed file
            self.graph.add_processed_file(str(file_path))
            logger.debug(f"_parse_file_content: Added file to tracking: {file_path}")

            # Parse language-specific constructs using AST-Grep queries
            logger.debug(f"_parse_file_content: calling _parse_functions_ast...")
            functions_count = self._parse_functions_ast(sg_root, file_path, language_config)
            logger.debug(f"_parse_file_content: _parse_functions_ast returned {functions_count}")
            
            classes_count = self._parse_classes_ast(sg_root, file_path, language_config)
            logger.debug(f"_parse_file_content: _parse_classes_ast returned {classes_count}")
            
            imports_count = self._parse_imports_ast(sg_root, file_path, language_config)
            logger.debug(f"_parse_file_content: _parse_imports_ast returned {imports_count}")
            
            # Extract function calls AFTER functions are parsed (needed for call graph)
            calls_count = self._extract_function_calls_ast(sg_root, file_path, language_config)
            logger.debug(f"_parse_file_content: _extract_function_calls_ast returned {calls_count}")
            
            logger.debug(
                f"Successfully parsed {file_path} ({language_config.name}): "
                f"{functions_count} functions, {classes_count} classes, {imports_count} imports, {calls_count} calls"
            )
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

    def _parse_functions_ast(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> int:
        """Parse functions using AST-Grep queries (FIXED: Jan 7, 2025)."""
        count = 0
        try:
            # Try AST-Grep pattern first
            pattern = ASTGrepPatterns.get_pattern(language_config.ast_grep_id, "function")
            print(f"[TRACE] _parse_functions_ast START: pattern='{pattern}' for {language_config.ast_grep_id}")
            if pattern:
                try:
                    # CORRECTED API: Call root() to get the root node, then find_all with dict query
                    print(f"[TRACE] _parse_functions_ast: calling sg_root.root()...")
                    root_node = sg_root.root()
                    print(f"[TRACE] _parse_functions_ast: root_node returned, calling find_all...")
                    # BUG FIX (Oct 26, 2025): find_all() returns iterator, must convert to list
                    functions = list(root_node.find_all({"rule": {"kind": pattern}}))
                    print(f"[TRACE] _parse_functions_ast: find_all returned {len(functions)} results")
                    for func_node in functions:
                        try:
                            # Extract function name and location from AST node
                            func_name = self._extract_name_from_ast(func_node, language_config)
                            print(f"[TRACE] _parse_functions_ast: extracted name '{func_name}'")
                            if not func_name:
                                print(f"[TRACE] _parse_functions_ast: no name, skipping")
                                continue
                            
                            # FIXED: Use range().start and range().end instead of start() and end() methods
                            r = func_node.range()
                            start_pos = r.start
                            end_pos = r.end
                            start_line = start_pos.line
                            end_line = end_pos.line
                            
                            # Create function node
                            node = UniversalNode(
                                id=f"function:{file_path}:{func_name}:{start_line}",
                                name=func_name,
                                node_type=NodeType.FUNCTION,
                                location=UniversalLocation(
                                    file_path=str(file_path),
                                    start_line=start_line,
                                    end_line=end_line,
                                    language=language_config.name
                                ),
                                language=language_config.name,
                                complexity=self._calculate_complexity_from_ast(func_node),
                                metadata={"ast_pattern": pattern}
                            )
                            print(f"[TRACE] _parse_functions_ast: adding node {node.id}")
                            self.graph.add_node(node)
                            print(f"[TRACE] _parse_functions_ast: node added successfully")
                            
                            # Add contains relationship
                            rel = UniversalRelationship(
                                id=f"contains:{file_path}:{node.id}",
                                source_id=f"file:{file_path}",
                                target_id=node.id,
                                relationship_type=RelationshipType.CONTAINS
                            )
                            print(f"[TRACE] _parse_functions_ast: adding relationship {rel.id}")
                            self.graph.add_relationship(rel)
                            print(f"[TRACE] _parse_functions_ast: relationship added successfully")
                            count += 1
                            
                        except Exception as e:
                            print(f"[TRACE] _parse_functions_ast: ERROR processing function: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                            
                except Exception as e:
                    print(f"[TRACE] _parse_functions_ast: ERROR querying functions: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"[TRACE] _parse_functions_ast END: Found {count} functions")
            
        except Exception as e:
            print(f"[TRACE] _parse_functions_ast: OUTER ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        return count

    def _extract_function_calls_ast(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> int:
        """Extract function calls and create CALLS relationships.
        
        This method finds all function/method calls in the file and creates CALLS
        relationships from the calling function to the called function.
        """
        count = 0
        try:
            pattern = ASTGrepPatterns.get_pattern(language_config.ast_grep_id, "call")
            if not pattern:
                return count
            
            root_node = sg_root.root()
            calls = list(root_node.find_all({"rule": {"kind": pattern}}))
            
            for call_node in calls:
                try:
                    call_name = self._extract_name_from_ast(call_node, language_config)
                    if not call_name:
                        continue
                    
                    r = call_node.range()
                    call_line = r.start.line
                    
                    # Find the function that contains this call
                    containing_function = self._find_containing_function(
                        file_path, call_line, language_config
                    )
                    
                    if not containing_function:
                        continue
                    
                    # Look for a matching called function in our graph
                    called_nodes = self.graph.find_nodes_by_name(call_name, exact_match=False)
                    
                    for called_node in called_nodes:
                        if called_node.node_type != NodeType.FUNCTION:
                            continue
                        
                        rel = UniversalRelationship(
                            id=f"calls:{containing_function.id}:{called_node.id}:{call_line}",
                            source_id=containing_function.id,
                            target_id=called_node.id,
                            relationship_type=RelationshipType.CALLS,
                            metadata={"call_line": call_line}
                        )
                        self.graph.add_relationship(rel)
                        count += 1
                        
                except Exception as e:
                    logger.debug(f"Error extracting call: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"Error in _extract_function_calls_ast: {e}")
        
        return count

    def _find_containing_function(self, file_path: Path, line_number: int, language_config: LanguageConfig) -> Optional[UniversalNode]:
        """Find the function node that contains the given line number."""
        
        # Get all functions in this file
        functions_in_file = [
            node for node in self.graph.nodes.values()
            if (node.node_type == NodeType.FUNCTION and
                node.location.file_path == str(file_path))
        ]
        
        # Find the function that contains this line
        for func_node in functions_in_file:
            if func_node.location.start_line <= line_number <= func_node.location.end_line:
                return func_node
        
        return None

    def _parse_classes_ast(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> int:
        """Parse classes using AST-Grep queries (FIXED: Jan 7, 2025)."""
        count = 0
        try:
            # Try AST-Grep pattern first
            pattern = ASTGrepPatterns.get_pattern(language_config.ast_grep_id, "class")
            if pattern:
                try:
                    # CORRECTED API: Call root() to get the root node, then find_all with dict query
                    root_node = sg_root.root()
                    # BUG FIX (Oct 26, 2025): find_all() returns iterator, must convert to list
                    classes = list(root_node.find_all({"rule": {"kind": pattern}}))
                    for class_node in classes:
                        try:
                            # Extract class name and location from AST node
                            class_name = self._extract_name_from_ast(class_node, language_config)
                            if not class_name:
                                continue
                            
                            r = class_node.range()
                            start_pos = r.start
                            end_pos = r.end
                            start_line = start_pos.line
                            end_line = end_pos.line
                            
                            # Create class node
                            node = UniversalNode(
                                id=f"class:{file_path}:{class_name}:{start_line}",
                                name=class_name,
                                node_type=NodeType.CLASS,
                                location=UniversalLocation(
                                    file_path=str(file_path),
                                    start_line=start_line,
                                    end_line=end_line,
                                    language=language_config.name
                                ),
                                language=language_config.name,
                                line_count=end_line - start_line + 1,
                                metadata={"ast_pattern": pattern}
                            )
                            self.graph.add_node(node)
                            
                            # Add contains relationship
                            rel = UniversalRelationship(
                                id=f"contains:{file_path}:{node.id}",
                                source_id=f"file:{file_path}",
                                target_id=node.id,
                                relationship_type=RelationshipType.CONTAINS
                            )
                            self.graph.add_relationship(rel)
                            count += 1
                            
                        except Exception as e:
                            logger.debug(f"Error processing class node in {file_path}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error querying classes in {file_path}: {e}")
            
            logger.debug(f"Found {count} classes in {file_path} using AST-Grep")
            
        except Exception as e:
            logger.debug(f"Error parsing classes in {file_path}: {e}")
        
        return count

    def _parse_imports_ast(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> int:
        """Parse imports using AST-Grep queries (FIXED: Jan 7, 2025)."""
        count = 0
        try:
            # Try AST-Grep pattern first
            pattern = ASTGrepPatterns.get_pattern(language_config.ast_grep_id, "import")
            if pattern:
                try:
                    # CORRECTED API: Call root() to get the root node, then find_all with dict query
                    root_node = sg_root.root()
                    # BUG FIX (Oct 26, 2025): find_all() returns iterator, must convert to list
                    imports = list(root_node.find_all({"rule": {"kind": pattern}}))
                    for import_node in imports:
                        try:
                            # Extract import target from AST node
                            import_target = self._extract_import_target_from_ast(import_node, language_config)
                            if not import_target:
                                continue
                            
                            # FIXED: Use range().start instead of start() method
                            r = import_node.range()
                            start_pos = r.start
                            start_line = start_pos.line
                            
                            # Create import node
                            node = UniversalNode(
                                id=f"import:{file_path}:{import_target}:{start_line}",
                                name=import_target,
                                node_type=NodeType.IMPORT,
                                location=UniversalLocation(
                                    file_path=str(file_path),
                                    start_line=start_line,
                                    end_line=start_line,
                                    language=language_config.name
                                ),
                                language=language_config.name,
                                metadata={"ast_pattern": pattern}
                            )
                            self.graph.add_node(node)
                            
                            # Add import relationship
                            rel = UniversalRelationship(
                                id=f"imports:{file_path}:{node.id}",
                                source_id=f"file:{file_path}",
                                target_id=f"module:{import_target}",
                                relationship_type=RelationshipType.IMPORTS
                            )
                            self.graph.add_relationship(rel)
                            count += 1
                            
                        except Exception as e:
                            logger.debug(f"Error processing import node in {file_path}: {e}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Error querying imports in {file_path}: {e}")
            
            logger.debug(f"Found {count} imports in {file_path} using AST-Grep")
            
        except Exception as e:
            logger.debug(f"Error parsing imports in {file_path}: {e}")
        
        return count

    def _extract_name_from_ast(self, ast_node: Any, language_config: LanguageConfig) -> Optional[str]:
        """Extract name from AST node (generic extraction for different languages)."""
        try:
            # Try various methods to get the name
            node_text = ast_node.text()
            
            # Common patterns for extracting names:
            # def foo(): -> 'foo'
            # function bar() { -> 'bar'
            # class Baz { -> 'Baz'
            
            import re
            
            # Try function pattern first
            match = re.search(r'(?:def|function|func|fn)\s+(\w+)', node_text)
            if match:
                return match.group(1)
            
            # Try class pattern
            match = re.search(r'(?:class|struct|interface)\s+(\w+)', node_text)
            if match:
                return match.group(1)
            
            # Try to get first word after keywords
            for keyword in ['def', 'function', 'func', 'fn', 'class', 'struct', 'interface']:
                if keyword in node_text:
                    parts = node_text.split(keyword, 1)
                    if len(parts) > 1:
                        remaining = parts[1].strip()
                        match = re.search(r'^(\w+)', remaining)
                        if match:
                            return match.group(1)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting name from AST node: {e}")
            return None

    def _extract_import_target_from_ast(self, ast_node: Any, language_config: LanguageConfig) -> Optional[str]:
        """Extract import target from AST node."""
        try:
            node_text = ast_node.text()
            
            import re
            
            # Python: import foo or from foo import bar
            match = re.search(r'(?:import|from)\s+([.\w]+)', node_text)
            if match:
                target = match.group(1)
                # Clean up (remove 'import' if it's part of the pattern)
                if ' import' in target:
                    target = target.split(' import')[0]
                return target.strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting import target from AST node: {e}")
            return None

    def _calculate_complexity_from_ast(self, ast_node: Any) -> int:
        """Calculate cyclomatic complexity from AST node."""
        try:
            node_text = ast_node.text()
            
            # Count decision points
            complexity = 1
            decision_keywords = ['if', 'for', 'while', 'catch', '&&', '||', '?', 'switch', 'case']
            
            for keyword in decision_keywords:
                # Use word boundary for keywords
                import re
                pattern = rf'\b{re.escape(keyword)}\b' if keyword.isalnum() else re.escape(keyword)
                complexity += len(re.findall(pattern, node_text))
            
            return max(1, complexity)
            
        except Exception:
            return 1

    def _read_file_with_encoding_detection(self, file_path: Path) -> str:
        """Read file with proper encoding detection."""
        # Try common encodings in order of likelihood
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error reading {file_path} with {encoding}: {e}")
                continue

        # Last resort: read as binary and decode with errors='replace'
        try:
            return file_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise

    def _load_gitignore_patterns(self, project_root: Path) -> None:
        """Load and compile gitignore patterns once per project - PERFORMANCE OPTIMIZATION."""
        if self._project_root == project_root and self._gitignore_patterns is not None:
            return  # Already loaded for this project
        
        self._project_root = project_root
        
        # Prefer .graphignore if it exists, fallback to .gitignore
        graphignore_path = project_root / '.graphignore'
        gitignore_path = project_root / '.gitignore'
        
        ignore_path = graphignore_path if graphignore_path.exists() else gitignore_path
        
        if not ignore_path.exists():
            self._gitignore_patterns = []
            self._gitignore_compiled = None
            logger.debug(f"No .gitignore or .graphignore found at {project_root}")
            return
        
        try:
            # Try to use pathspec for proper gitignore handling
            try:
                import pathspec
                with open(ignore_path, 'r', encoding='utf-8') as f:
                    patterns = [line.strip() for line in f 
                               if line.strip() and not line.startswith('#')]
                
                self._gitignore_patterns = patterns
                self._gitignore_compiled = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
                logger.info(f"Loaded {len(patterns)} ignore patterns using pathspec from {ignore_path}")
                
            except ImportError:
                # Fallback to simple pattern matching if pathspec not available
                with open(ignore_path, 'r', encoding='utf-8') as f:
                    patterns = [line.strip() for line in f 
                               if line.strip() and not line.startswith('#')]
                
                self._gitignore_patterns = patterns
                self._gitignore_compiled = None
                logger.debug(f"Loaded {len(patterns)} ignore patterns using fallback from {ignore_path}")
                
        except Exception as e:
            logger.warning(f"Error loading ignore file from {ignore_path}: {e}")
            self._gitignore_patterns = []
            self._gitignore_compiled = None

    def _should_ignore_path(self, file_path: Path, project_root: Path) -> bool:
        """Check if path should be ignored (OPTIMIZED: cached patterns, proper gitignore support)."""
        # Load gitignore patterns if needed (only happens once per project)
        self._load_gitignore_patterns(project_root)
        
        # Always skip system/cache directories
        common_skip_dirs = {
            '__pycache__', '.git', '.svn', '.hg', '.bzr',
            '.pytest_cache', '.mypy_cache', '.tox', '.coverage',
            '.sass-cache', '.cache', '.DS_Store', '.idea', '.vscode', '.vs'
        }
        
        if any(part in common_skip_dirs for part in file_path.parts):
            return True
        
        # Check gitignore patterns using compiled pathspec if available
        if self._gitignore_compiled:
            try:
                relative_path = file_path.relative_to(project_root)
                return self._gitignore_compiled.match_file(str(relative_path))
            except ValueError:
                # Path is not relative to project root
                return False
        elif self._gitignore_patterns:
            # Fallback to simple pattern matching
            try:
                relative_path = file_path.relative_to(project_root)
                path_str = str(relative_path)
                path_parts = path_str.split('/')

                # Check against each gitignore pattern
                for pattern in self._gitignore_patterns:
                    if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_str, pattern + '/*'):
                        return True
                    # Handle directory patterns (e.g., "node_modules/")
                    if pattern.endswith('/'):
                        dir_name = pattern[:-1]
                        # Check if any path component matches the directory name
                        if dir_name in path_parts or path_str.startswith(dir_name + '/'):
                            return True
                        # Also check with wildcard patterns
                        if fnmatch.fnmatch(dir_name, dir_name):
                            for part in path_parts:
                                if fnmatch.fnmatch(part, dir_name):
                                    return True
                        
            except ValueError:
                # Path is not relative to project root
                pass
        
        return False

    async def parse_directory(self, directory: Path, recursive: bool = True) -> int:
        """Parse all supported files in a directory with OPTIMIZED gitignore-aware traversal."""
        if isinstance(directory, str):
            directory = Path(directory)
        if not directory.is_dir():
            logger.error("Not a directory: %s", directory)
            return 0

        logger.info(f"Starting optimized parse_directory for: {directory}")
        
        # Get supported extensions
        supported_extensions = await self.registry.get_supported_extensions()
        logger.info(f"Supported extensions: {list(supported_extensions)[:10]}...")
        
        # Use optimized traversal with directory pruning instead of rglob()
        if recursive:
            files_to_process = self._get_files_with_directory_pruning(directory, supported_extensions)
        else:
            # Non-recursive: check immediate directory only
            files_to_process = []
            for item in directory.iterdir():
                if (item.is_file() and 
                    not self._should_ignore_path(item, directory) and
                    item.suffix.lower() in supported_extensions):
                    
                    # Check file size
                    try:
                        if item.stat().st_size > 1024 * 1024:  # 1MB limit
                            logger.debug(f"Skipping large file: {item}")
                            continue
                    except OSError:
                        continue
                    
                    files_to_process.append(item)
        
        logger.info(f"Optimized traversal found {len(files_to_process)} files to process")
        
        # Parse the pre-filtered files
        parsed_count = 0
        for file_path in files_to_process:
            logger.debug(f"Parsing file: {file_path}")
            if await self.parse_file(file_path):
                parsed_count += 1
            else:
                logger.debug(f"Failed to parse: {file_path}")
            
            # Progress logging
            if parsed_count % 100 == 0 and parsed_count > 0:
                logger.info(f"Parsed {parsed_count} files successfully")

        logger.info(f"Optimized parsing complete: {parsed_count}/{len(files_to_process)} files parsed")
        return parsed_count
    
    def _get_files_with_directory_pruning(self, directory: Path, supported_extensions: Set[str]) -> List[Path]:
        """Get files using intelligent directory traversal that prunes ignored trees."""
        
        files = []
        skipped_dirs = set()
        
        def _walk_directory(current_dir: Path) -> None:
            """Recursively walk directory with intelligent pruning."""
            
            try:
                entries = list(current_dir.iterdir())
            except (PermissionError, OSError) as e:
                logger.debug(f"Cannot access directory {current_dir}: {e}")
                return
            
            # Separate files and directories for processing
            dir_files = []
            subdirs = []
            
            for entry in entries:
                if entry.is_file():
                    dir_files.append(entry)
                elif entry.is_dir():
                    subdirs.append(entry)
            
            # Process files in current directory
            for file_path in dir_files:
                # Skip if ignored
                if self._should_ignore_path(file_path, directory):
                    logger.debug(f"Skipping ignored file: {file_path}")
                    continue
                
                # Check if supported extension
                if file_path.suffix.lower() in supported_extensions:
                    # Check file size limit
                    try:
                        if file_path.stat().st_size > 1024 * 1024:  # 1MB
                            logger.debug(f"Skipping large file: {file_path}")
                            continue
                    except OSError:
                        continue
                    
                    files.append(file_path)
            
            # Process subdirectories with pruning
            for dir_path in subdirs:
                # OPTIMIZATION: Check if entire directory should be ignored
                if self._should_ignore_path(dir_path, directory):
                    # Log directory tree pruning (only once per tree)
                    if dir_path not in skipped_dirs:
                        logger.info(f"Pruning ignored directory tree: {dir_path}")
                        skipped_dirs.add(dir_path)
                    continue  # PRUNE: Skip entire subtree
                
                # Recursively process subdirectory
                _walk_directory(dir_path)
        
        # Start the optimized traversal
        logger.debug(f"Starting directory tree traversal from: {directory}")
        _walk_directory(directory)
        
        logger.info(f"Directory pruning results: {len(files)} files found, {len(skipped_dirs)} directories pruned")
        if skipped_dirs:
            logger.debug(f"Pruned directories: {sorted([str(d.relative_to(directory)) for d in skipped_dirs])}")
        
        return files

    async def get_parsing_statistics(self) -> Dict[str, Any]:
        """Get statistics about the parsed code."""
        stats = self.graph.get_statistics()
        supported_extensions = await self.registry.get_supported_extensions()
        stats.update({
            "supported_languages": len(self.registry.LANGUAGES),
            "supported_extensions": list(supported_extensions),
            "ast_grep_available": self._ast_grep_available
        })
        return stats
