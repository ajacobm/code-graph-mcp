"""
Cross-Language Seam Detection

Detects and creates SEAM relationships between different language runtimes.
Examples:
- C# calling Node.js service
- Python calling Java service
- Angular TypeScript importing backend APIs
- .NET tier calling SQL Server procedures
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SeamPattern:
    """Pattern for detecting cross-language calls."""
    
    source_language: str
    target_language: str
    patterns: List[str]
    example: str


class SeamDetector:
    """
    Detects cross-language function calls and imports.
    
    Maintains patterns for common multi-language architectures:
    - .NET -> Node.js (via HTTP, gRPC, message queues)
    - Python -> Java (via subprocess, sockets)
    - TypeScript/Angular -> APIs (via fetch, axios)
    - C# -> SQL Server (via ADO.NET, EF)
    """
    
    def __init__(self):
        self.patterns: Dict[Tuple[str, str], List[re.Pattern]] = {}
        self._initialize_patterns()
    
    def _initialize_patterns(self) -> None:
        """Initialize common cross-language patterns."""
        
        seam_patterns = [
            SeamPattern(
                source_language="csharp",
                target_language="node",
                patterns=[
                    r'HttpClient',
                    r'PostAsync',
                    r'RestClient',
                    r'npm',
                    r'node.*service',
                ],
                example="C# calling Node.js microservice via HTTP"
            ),
            SeamPattern(
                source_language="csharp",
                target_language="sql",
                patterns=[
                    r'SqlConnection',
                    r'SqlCommand',
                    r'DbContext',
                    r'ExecuteReader',
                    r'ExecuteNonQuery',
                ],
                example="C# calling SQL Server via ADO.NET"
            ),
            SeamPattern(
                source_language="typescript",
                target_language="python",
                patterns=[
                    r'fetch',
                    r'axios',
                    r'XMLHttpRequest',
                    r'api',
                ],
                example="TypeScript calling Python backend API"
            ),
            SeamPattern(
                source_language="typescript",
                target_language="node",
                patterns=[
                    r'import.*from',
                    r'require',
                    r'@angular',
                    r'@nestjs',
                    r'express',
                ],
                example="Angular/TypeScript importing Node modules"
            ),
            SeamPattern(
                source_language="python",
                target_language="java",
                patterns=[
                    r'subprocess',
                    r'socket',
                    r'grpc',
                    r'requests',
                ],
                example="Python calling Java service"
            ),
            SeamPattern(
                source_language="python",
                target_language="sql",
                patterns=[
                    r'sqlite3',
                    r'psycopg2',
                    r'pymysql',
                    r'execute',
                ],
                example="Python calling SQL database"
            ),
        ]
        
        for pattern_def in seam_patterns:
            key = (pattern_def.source_language.lower(), pattern_def.target_language.lower())
            compiled = [re.compile(p, re.IGNORECASE) for p in pattern_def.patterns]
            self.patterns[key] = compiled
            logger.debug(
                f"Registered seam pattern: {pattern_def.source_language} -> "
                f"{pattern_def.target_language}"
            )
    
    def detect_seams(
        self,
        source_language: str,
        target_language: str,
        code_content: str,
        source_name: str,
        target_name: str
    ) -> bool:
        """
        Detect if code contains cross-language seams.
        
        Args:
            source_language: Language of calling code (e.g., 'csharp')
            target_language: Language being called (e.g., 'node')
            code_content: Code content to analyze
            source_name: Name of source element
            target_name: Name of target element
        
        Returns:
            True if a seam pattern is detected
        """
        source_lang = source_language.lower()
        target_lang = target_language.lower()
        key = (source_lang, target_lang)
        
        if key not in self.patterns:
            return False
        
        for pattern in self.patterns[key]:
            if pattern.search(code_content):
                logger.debug(
                    f"Detected seam: {source_name} ({source_lang}) -> "
                    f"{target_name} ({target_lang})"
                )
                return True
        
        return False
    
    def add_pattern(
        self,
        source_language: str,
        target_language: str,
        pattern: str
    ) -> None:
        """Add a custom seam detection pattern at runtime."""
        key = (source_language.lower(), target_language.lower())
        
        if key not in self.patterns:
            self.patterns[key] = []
        
        try:
            self.patterns[key].append(re.compile(pattern, re.IGNORECASE))
            logger.info(
                f"Added seam pattern: {source_language} -> {target_language}"
            )
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
    
    def get_registered_seams(self) -> List[Tuple[str, str]]:
        """Get all registered source->target language pairs."""
        return list(self.patterns.keys())
