"""
Entry Point Detection Service

Intelligent detection of entry points across 11+ programming languages using
pattern matching and language-specific heuristics.
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from .universal_graph import NodeType

class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    C = "c"
    PHP = "php"
    RUBY = "ruby"
    KOTLIN = "kotlin"
    SWIFT = "swift"

@dataclass
class EntryPointPattern:
    """Represents a pattern for detecting entry points in code."""
    name: str
    patterns: List[str]
    priority: int = 0  # Higher priority means more likely to be an entry point
    score_bonus: float = 1.0

@dataclass
class EntryPointCandidate:
    """Represents a potential entry point with scoring."""
    node_id: str
    file_path: str
    name: str
    language: str
    line_number: int
    pattern_matched: str
    confidence_score: float
    complexity: int = 0

class EntryDetector:
    """Service for detecting entry points in codebases."""
    
    # Stdlib modules to filter out
    STDLIB_MODULES = {
        # Python
        're', 'sys', 'os', 'io', 'time', 'datetime', 'json', 'pickle', 'csv',
        'logging', 'asyncio', 'threading', 'subprocess', 'socket', 'http',
        'urllib', 'requests', 'pathlib', 'collections', 'itertools', 'functools',
        'math', 'random', 'statistics', 'decimal', 'fractions', 'cmath',
        'typing', 'abc', 'contextlib', 'weakref', 'types', 'copy', 'pprint',
        'enum', 'graphlib', 'dataclasses', 'inspect', 'traceback', 'gc', 'sys',
        'builtins', 'warnings', 'contextlib', 'atexit', 'signal', 'mmap',
        'select', 'fcntl', 'termios', 'tty', 'pty', 'stat', 'crypt', 'grp',
        'pwd', 'spwd', 'getopt', 'argparse', 'shlex', 'cmd', 'shutil', 'tempfile',
        'glob', 'fnmatch', 'linecache', 'fileinput', 'difflib', 'textwrap',
        'string', 'stringprep', 'readline', 'rlcompleter', 'gzip', 'bz2',
        'lzma', 'zlib', 'tarfile', 'zipfile', 'configparser', 'tomllib',
        'netrc', 'xdrlib', 'plistlib', 'html', 'xml', 'ftplib', 'poplib',
        'imaplib', 'smtplib', 'smtpd', 'telnetlib', 'uuid', 'socketserver',
        'email', 'mailbox', 'mimetypes', 'base64', 'binhex', 'binascii', 'quopri',
        'uu', 'hashlib', 'hmac', 'secrets', 'ssl', 'sqlite3', 'dbm', 'shelve',
        'marshal', 'sqlite', 'multiprocessing', 'concurrent', 'unittest', 'doctest',
        'pdb', 'cProfile', 'profile', 'pstats', 'trace', 'timeit', 'distutils',
        'setuptools', 'pip', 'venv', 'zipapp', 'abc', '__main__',
    }
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.language_extensions = self._initialize_extensions()
    
    def _initialize_extensions(self) -> Dict[Language, Set[str]]:
        """Initialize file extensions for each language."""
        return {
            Language.PYTHON: {'.py'},
            Language.JAVASCRIPT: {'.js'},
            Language.TYPESCRIPT: {'.ts'},
            Language.JAVA: {'.java'},
            Language.CSHARP: {'.cs'},
            Language.GO: {'.go'},
            Language.RUST: {'.rs'},
            Language.CPP: {'.cpp', '.cxx', '.cc'},
            Language.C: {'.c', '.h'},
            Language.PHP: {'.php'},
            Language.RUBY: {'.rb'},
            Language.KOTLIN: {'.kt'},
            Language.SWIFT: {'.swift'},
        }
    
    def _initialize_patterns(self) -> Dict[Language, List[EntryPointPattern]]:
        """Initialize entry point detection patterns for each language."""
        patterns = {
            Language.PYTHON: [
                EntryPointPattern(
                    "main_function",
                    [r"def\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "if_name_main",
                    [r"if\s+__name__\s*==\s*['\"]__main__['\"]"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "flask_app_run",
                    [r"app\s*\.\s*run\s*\("],
                    priority=8,
                    score_bonus=1.5
                ),
                EntryPointPattern(
                    "django_manage",
                    [r"manage\.py"],
                    priority=7,
                    score_bonus=1.3
                ),
                EntryPointPattern(
                    "fastapi_app",
                    [r"app\s*=\s*FastAPI\s*\("],
                    priority=6,
                    score_bonus=1.2
                ),
            ],
            
            Language.JAVASCRIPT: [
                EntryPointPattern(
                    "npm_main",
                    [r'"main"\s*:\s*".*?"'],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "index_js",
                    [r"index\.js"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "express_server",
                    [r"express\s*\(\s*\)", r"app\s*\.\s*listen\s*\("],
                    priority=8,
                    score_bonus=1.5
                ),
                EntryPointPattern(
                    "node_entry",
                    [r"process\.argv", r"require\s*\(\s*['\"]http['\"]\s*\)"],
                    priority=7,
                    score_bonus=1.3
                ),
            ],
            
            Language.TYPESCRIPT: [
                EntryPointPattern(
                    "npm_main",
                    [r'"main"\s*:\s*".*?"'],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "index_ts",
                    [r"index\.ts"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "nestjs_entry",
                    [r"@nestjs/core", r"nest start"],
                    priority=8,
                    score_bonus=1.5
                ),
                EntryPointPattern(
                    "express_ts",
                    [r"express\s*\(\s*\)", r"app\s*\.\s*listen\s*\("],
                    priority=7,
                    score_bonus=1.3
                ),
            ],
            
            Language.JAVA: [
                EntryPointPattern(
                    "main_method",
                    [r"public\s+static\s+void\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "spring_boot",
                    [r"@SpringBootApplication", r"SpringApplication\.run"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "servlet_init",
                    [r"extends HttpServlet", r"init\s*\(\s*ServletConfig"],
                    priority=8,
                    score_bonus=1.5
                ),
            ],
            
            Language.CSHARP: [
                EntryPointPattern(
                    "main_method",
                    [r"static\s+void\s+Main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "aspnet_core",
                    [r"UseStartup<", r"WebHost\.CreateDefaultBuilder"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "console_app",
                    [r"Console\.WriteLine"],
                    priority=8,
                    score_bonus=1.3
                ),
            ],
            
            Language.GO: [
                EntryPointPattern(
                    "main_function",
                    [r"func\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "package_main",
                    [r"package main"],
                    priority=9,
                    score_bonus=1.5
                ),
                EntryPointPattern(
                    "http_server",
                    [r"http\.ListenAndServe"],
                    priority=8,
                    score_bonus=1.3
                ),
            ],
            
            Language.RUST: [
                EntryPointPattern(
                    "main_function",
                    [r"fn\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "cargo_toml",
                    [r"Cargo\.toml"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "rocket_entry",
                    [r"#[rocket::launch]", r"rocket::build"],
                    priority=8,
                    score_bonus=1.5
                ),
            ],
            
            Language.CPP: [
                EntryPointPattern(
                    "main_function",
                    [r"int\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "cpp_cli",
                    [r"argc", r"argv"],
                    priority=9,
                    score_bonus=1.5
                ),
            ],
            
            Language.C: [
                EntryPointPattern(
                    "main_function",
                    [r"int\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "c_cli",
                    [r"argc", r"argv"],
                    priority=9,
                    score_bonus=1.5
                ),
            ],
            
            Language.PHP: [
                EntryPointPattern(
                    "cli_script",
                    [r"\$_SERVER\['argv'\]", r"\$argc"],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "web_entry",
                    [r"\$_GET", r"\$_POST", r"apache_request_headers"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "php_cli",
                    [r"php_cli", r"cli\."],
                    priority=8,
                    score_bonus=1.3
                ),
            ],
            
            Language.RUBY: [
                EntryPointPattern(
                    "ruby_script",
                    [r"__FILE__\s*==\s*\$0"],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "rack_app",
                    [r"run\s+.*App", r"config\.ru"],
                    priority=9,
                    score_bonus=1.8
                ),
                EntryPointPattern(
                    "rails_entry",
                    [r"rails\s+server"],
                    priority=8,
                    score_bonus=1.5
                ),
            ],
            
            Language.KOTLIN: [
                EntryPointPattern(
                    "main_function",
                    [r"fun\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "ktor_app",
                    [r"io\.ktor\.server\.application"],
                    priority=9,
                    score_bonus=1.8
                ),
            ],
            
            Language.SWIFT: [
                EntryPointPattern(
                    "main_function",
                    [r"func\s+main\s*\("],
                    priority=10,
                    score_bonus=2.0
                ),
                EntryPointPattern(
                    "swift_ui",
                    [r"struct\s+.*App", r"@main"],
                    priority=9,
                    score_bonus=1.8
                ),
            ],
        }
        
        return patterns
    
    def detect_entry_points(self, nodes: List[Dict], file_contents: Dict[str, str]) -> List[EntryPointCandidate]:
        """
        Detect entry points in the provided nodes and file contents.
        
        Args:
            nodes: List of node dictionaries with file_path and other metadata
            file_contents: Dictionary mapping file paths to their contents
            
        Returns:
            List of EntryPointCandidate objects sorted by confidence score
        """
        candidates = []
        
        # Group nodes by file for efficient processing
        nodes_by_file = {}
        for node in nodes:
            file_path = node.get('file_path', '')
            if file_path:
                if file_path not in nodes_by_file:
                    nodes_by_file[file_path] = []
                nodes_by_file[file_path].append(node)
        
        # Check each file for entry point patterns
        for file_path, file_nodes in nodes_by_file.items():
            if file_path not in file_contents:
                continue
            
            file_content = file_contents[file_path]
            language = self._detect_language_from_path(file_path)
            
            if language and language in self.patterns:
                # Check for language-specific patterns
                for pattern in self.patterns[language]:
                    for regex_pattern in pattern.patterns:
                        matches = re.finditer(regex_pattern, file_content, re.MULTILINE)
                        for match in matches:
                            # Create entry point candidate for each matching node
                            for node in file_nodes:
                                # Use line number to associate match with node if available
                                node_line = node.get('line', 0)
                                match_line = file_content[:match.start()].count('\n') + 1
                                
                                # If we can't determine line numbers, associate with all nodes in file
                                if node_line == 0 or abs(node_line - match_line) <= 10:
                                    candidate = EntryPointCandidate(
                                        node_id=node['id'],
                                        file_path=file_path,
                                        name=node.get('name', 'unknown'),
                                        language=language.value,
                                        line_number=node_line,
                                        pattern_matched=pattern.name,
                                        confidence_score=self._calculate_confidence_score(
                                            pattern, node.get('complexity', 0)
                                        ),
                                        complexity=node.get('complexity', 0)
                                    )
                                    candidates.append(candidate)
        
        # Filter out stdlib modules
        candidates = [c for c in candidates if not self._is_stdlib_module(c.name)]
        
        # Sort by confidence score (descending)
        candidates.sort(key=lambda c: c.confidence_score, reverse=True)
        return candidates
    
    def _detect_language_from_path(self, file_path: str) -> Language | None:
        """Detect language from file extension."""
        for language, extensions in self.language_extensions.items():
            for ext in extensions:
                if file_path.endswith(ext):
                    return language
        return None
    
    def _is_stdlib_module(self, node_name: str) -> bool:
        """Check if a node is a stdlib module that should be filtered."""
        base_name = node_name.split('.')[0] if '.' in node_name else node_name
        return base_name.lower() in self.STDLIB_MODULES
    
    def _calculate_confidence_score(self, pattern: EntryPointPattern, complexity: int) -> float:
        """Calculate confidence score for an entry point candidate."""
        base_score = 1.0
        priority_bonus = pattern.priority * 0.1
        complexity_penalty = min(complexity * 0.01, 0.5)  # Higher complexity = lower confidence
        return base_score + pattern.score_bonus + priority_bonus - complexity_penalty
    
    def get_language_patterns(self, language: str) -> List[EntryPointPattern]:
        """Get entry point patterns for a specific language."""
        lang_enum = None
        for lang in Language:
            if lang.value.lower() == language.lower():
                lang_enum = lang
                break
        
        if lang_enum and lang_enum in self.patterns:
            return self.patterns[lang_enum]
        return []