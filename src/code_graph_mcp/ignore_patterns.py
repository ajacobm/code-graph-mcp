"""
Ignore Patterns Management for Code Graph

Provides .graphignore-style pattern matching for:
- Excluding paths from analysis
- Filtering by language
- Configurable ignore patterns per project
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IgnoreConfig:
    """Configuration for ignore patterns."""
    
    path_patterns: List[str]
    language_filters: Optional[Set[str]] = None
    include_patterns: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.language_filters is None:
            self.language_filters = set()
        if self.include_patterns is None:
            self.include_patterns = []


class IgnorePatternsManager:
    """
    Manages .graphignore patterns and language filtering.
    
    Supports:
    - Standard glob patterns (*.min.js, node_modules/*, etc.)
    - Directory patterns (dist/, build/, etc.)
    - Language-specific filtering (only analyze C#, TypeScript, etc.)
    - Include patterns (whitelist overrides)
    """
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.patterns: List[str] = []
        self.compiled_patterns: List[re.Pattern] = []
        self.language_filters: Set[str] = set()
        self.include_patterns: List[str] = []
        self.include_compiled: List[re.Pattern] = []
        
        self._load_graphignore()
    
    def _load_graphignore(self) -> None:
        """Load patterns from .graphignore file if it exists."""
        graphignore_path = self.root_path / ".graphignore"
        
        if not graphignore_path.exists():
            logger.debug(f"No .graphignore found at {graphignore_path}")
            return
        
        try:
            with open(graphignore_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('language:'):
                    lang = line.split(':', 1)[1].strip()
                    self.language_filters.add(lang.lower())
                    logger.debug(f"Added language filter: {lang}")
                
                elif line.startswith('!'):
                    include_pattern = line[1:].strip()
                    self.include_patterns.append(include_pattern)
                    self.include_compiled.append(self._compile_pattern(include_pattern))
                    logger.debug(f"Added include pattern: {include_pattern}")
                
                else:
                    self.patterns.append(line)
                    self.compiled_patterns.append(self._compile_pattern(line))
                    logger.debug(f"Added ignore pattern: {line}")
            
            logger.info(
                f"Loaded .graphignore: {len(self.patterns)} patterns, "
                f"{len(self.language_filters)} language filters"
            )
        
        except Exception as e:
            logger.error(f"Error loading .graphignore: {e}")
    
    @staticmethod
    def _compile_pattern(pattern: str) -> re.Pattern:
        """Convert glob-style pattern to compiled regex."""
        regex_pattern = pattern.replace('.', r'\.')
        regex_pattern = regex_pattern.replace('*', '.*')
        regex_pattern = regex_pattern.replace('?', '.')
        
        if pattern.endswith('/'):
            regex_pattern = f"(^|/){regex_pattern}"
        else:
            regex_pattern = f"(^|/){regex_pattern}(?:/|$)"
        
        return re.compile(regex_pattern)
    
    def should_ignore_path(self, file_path: str) -> bool:
        """Check if a file path should be ignored."""
        if not file_path:
            return False
        
        path = str(file_path).replace('\\', '/')
        
        for include_pattern in self.include_compiled:
            if include_pattern.search(path):
                logger.debug(f"Path {file_path} included by whitelist pattern")
                return False
        
        for ignore_pattern in self.compiled_patterns:
            if ignore_pattern.search(path):
                logger.debug(f"Path {file_path} ignored by pattern")
                return True
        
        return False
    
    def should_analyze_language(self, language: str) -> bool:
        """Check if a language should be analyzed based on filters."""
        if not self.language_filters:
            return True
        
        return language.lower() in self.language_filters
    
    def add_pattern(self, pattern: str, include: bool = False) -> None:
        """Add a pattern at runtime."""
        if include:
            self.include_patterns.append(pattern)
            self.include_compiled.append(self._compile_pattern(pattern))
        else:
            self.patterns.append(pattern)
            self.compiled_patterns.append(self._compile_pattern(pattern))
    
    def add_language_filter(self, language: str) -> None:
        """Add a language filter at runtime."""
        self.language_filters.add(language.lower())
    
    def clear_language_filters(self) -> None:
        """Clear all language filters (analyze all languages)."""
        self.language_filters.clear()
    
    def get_config(self) -> IgnoreConfig:
        """Get current configuration as an IgnoreConfig object."""
        return IgnoreConfig(
            path_patterns=self.patterns,
            language_filters=self.language_filters.copy() if self.language_filters else None,
            include_patterns=self.include_patterns.copy()
        )
    
    @staticmethod
    def load_from_config(config: IgnoreConfig, root_path: str = ".") -> 'IgnorePatternsManager':
        """Create manager from IgnoreConfig object."""
        manager = IgnorePatternsManager(root_path)
        manager.patterns = config.path_patterns
        manager.compiled_patterns = [
            IgnorePatternsManager._compile_pattern(p) for p in config.path_patterns
        ]
        if config.language_filters:
            manager.language_filters = config.language_filters
        if config.include_patterns:
            manager.include_patterns = config.include_patterns
            manager.include_compiled = [
                IgnorePatternsManager._compile_pattern(p) for p in config.include_patterns
            ]
        return manager
