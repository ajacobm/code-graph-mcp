#!/usr/bin/env python3
"""
Optimized Directory Traversal with Gitignore Pruning

Replaces inefficient rglob() with intelligent tree traversal that
prunes entire directory subtrees when they match gitignore patterns.
"""

import os
import fnmatch
from pathlib import Path
from typing import Iterator, Set, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GitignoreDirectoryTraversal:
    """Efficient directory traversal that prunes ignored directories."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.gitignore_patterns: Optional[List[str]] = None
        self.gitignore_compiled: Optional[Any] = None
        self._load_gitignore_patterns()
        
        # Common directories to always skip
        self.always_skip_dirs = {
            '__pycache__', '.git', '.svn', '.hg', '.bzr',
            '.pytest_cache', '.mypy_cache', '.tox', '.coverage',
            '.sass-cache', '.cache', '.DS_Store', '.idea', '.vscode', '.vs',
            'node_modules', '.env', '.venv'
        }
        
        # Track skipped directories for logging
        self.skipped_dirs = set()
    
    def _load_gitignore_patterns(self) -> None:
        """Load and compile gitignore patterns."""
        gitignore_path = self.project_root / '.gitignore'
        
        if not gitignore_path.exists():
            self.gitignore_patterns = []
            self.gitignore_compiled = None
            logger.debug(f"No .gitignore found at {gitignore_path}")
            return
        
        try:
            # Try pathspec first (proper gitignore support)
            try:
                import pathspec
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    patterns = [line.strip() for line in f 
                               if line.strip() and not line.startswith('#')]
                
                self.gitignore_patterns = patterns
                self.gitignore_compiled = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
                logger.info(f"Loaded {len(patterns)} gitignore patterns using pathspec")
                
            except ImportError:
                # Fallback to fnmatch
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    patterns = [line.strip() for line in f 
                               if line.strip() and not line.startswith('#')]
                
                self.gitignore_patterns = patterns
                self.gitignore_compiled = None
                logger.info(f"Loaded {len(patterns)} gitignore patterns using fnmatch fallback")
                
        except Exception as e:
            logger.warning(f"Error loading .gitignore: {e}")
            self.gitignore_patterns = []
            self.gitignore_compiled = None
    
    def should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored (optimized version)."""
        
        # Always skip common system directories
        if any(part in self.always_skip_dirs for part in path.parts):
            return True
        
        try:
            relative_path = path.relative_to(self.project_root)
        except ValueError:
            # Path not relative to project root
            return False
        
        relative_str = str(relative_path)
        
        # Use compiled pathspec if available
        if self.gitignore_compiled:
            return self.gitignore_compiled.match_file(relative_str)
        
        # Fallback to fnmatch patterns
        if self.gitignore_patterns:
            for pattern in self.gitignore_patterns:
                # Handle directory patterns ending with /
                if pattern.endswith('/'):
                    pattern_dir = pattern[:-1]
                    if relative_str == pattern_dir or relative_str.startswith(pattern_dir + '/'):
                        return True
                
                # Handle file and general patterns
                if fnmatch.fnmatch(relative_str, pattern):
                    return True
                    
                # Handle patterns that should match directories
                if fnmatch.fnmatch(relative_str, pattern + '/*') or fnmatch.fnmatch(relative_str + '/', pattern):
                    return True
        
        return False
    
    def traverse_files(self, supported_extensions: Set[str]) -> Iterator[Path]:
        """
        Efficiently traverse files with directory pruning.
        
        This replaces the inefficient directory.rglob("*") approach with
        a custom traversal that skips entire directory trees when they
        match gitignore patterns.
        """
        
        def _walk_directory(current_dir: Path) -> Iterator[Path]:
            """Recursively walk directory with intelligent pruning."""
            
            try:
                # Get directory contents
                entries = list(current_dir.iterdir())
            except (PermissionError, OSError) as e:
                logger.debug(f"Cannot access directory {current_dir}: {e}")
                return
            
            # Separate files and directories
            files = []
            dirs = []
            
            for entry in entries:
                if entry.is_file():
                    files.append(entry)
                elif entry.is_dir():
                    dirs.append(entry)
            
            # Process files in current directory
            for file_path in files:
                # Check if the file should be ignored
                if self.should_ignore_path(file_path):
                    logger.debug(f"Skipping ignored file: {file_path}")
                    continue
                
                # Check if supported file type
                if file_path.suffix.lower() in supported_extensions:
                    # Check file size limit
                    try:
                        if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                            logger.debug(f"Skipping large file: {file_path}")
                            continue
                    except OSError:
                        continue
                    
                    yield file_path
            
            # Process subdirectories
            for dir_path in dirs:
                # Check if entire directory should be ignored
                if self.should_ignore_path(dir_path):
                    # Log only once per directory tree
                    if dir_path not in self.skipped_dirs:
                        logger.info(f"Skipping ignored directory tree: {dir_path}")
                        self.skipped_dirs.add(dir_path)
                    continue  # PRUNE: Skip entire subtree
                
                # Recursively process subdirectory
                yield from _walk_directory(dir_path)
        
        # Start traversal from project root
        total_files = 0
        for file_path in _walk_directory(self.project_root):
            total_files += 1
            if total_files % 100 == 0:
                logger.info(f"Discovered {total_files} files to process...")
            yield file_path
        
        # Log summary
        logger.info(f"Directory traversal complete: {total_files} files found, {len(self.skipped_dirs)} directories pruned")


def get_files_respecting_gitignore(
    directory: Path, 
    supported_extensions: Set[str],
    max_file_size: int = 1024 * 1024  # 1MB default
) -> List[Path]:
    """
    Get all files in directory respecting gitignore, with directory pruning.
    
    This is a much more efficient alternative to:
    ```python
    files = []
    for path in directory.rglob("*"):
        if path.is_file() and not should_ignore_path(path):
            files.append(path)
    ```
    
    Instead it prunes entire directory trees when they match gitignore patterns.
    """
    
    traversal = GitignoreDirectoryTraversal(directory)
    files = list(traversal.traverse_files(supported_extensions))
    
    logger.info(f"Found {len(files)} files to process (after gitignore pruning)")
    return files


# Drop-in replacement for existing parse_directory method
async def optimized_parse_directory_replacement(
    parser,  # UniversalParser instance
    directory: Path, 
    recursive: bool = True
) -> int:
    """
    Optimized replacement for parse_directory method.
    
    This version uses intelligent directory traversal instead of
    the inefficient rglob() + individual ignore checks.
    """
    
    if not directory.is_dir():
        logger.error("Not a directory: %s", directory)
        return 0

    logger.info(f"Starting optimized parse_directory for: {directory}")
    
    # Get supported extensions
    supported_extensions = await parser.registry.get_supported_extensions()
    logger.info(f"Supported extensions: {list(supported_extensions)[:10]}...")
    
    # Use optimized traversal instead of rglob()
    if recursive:
        # NEW: Efficient traversal with directory pruning
        traversal = GitignoreDirectoryTraversal(directory)
        files_to_process = list(traversal.traverse_files(supported_extensions))
    else:
        # Non-recursive: just check immediate directory
        files_to_process = []
        for item in directory.iterdir():
            if (item.is_file() and 
                not parser._should_ignore_path(item, directory) and
                item.suffix.lower() in supported_extensions):
                files_to_process.append(item)
    
    logger.info(f"Efficient traversal found {len(files_to_process)} files to process")
    
    # Parse the discovered files
    parsed_count = 0
    for file_path in files_to_process:
        logger.debug(f"Parsing file: {file_path}")
        if await parser.parse_file(file_path):
            parsed_count += 1
        else:
            logger.debug(f"Failed to parse: {file_path}")
        
        # Progress logging
        if parsed_count % 100 == 0 and parsed_count > 0:
            logger.info(f"Parsed {parsed_count} files successfully")

    logger.info(f"Optimized parsing complete: {parsed_count}/{len(files_to_process)} files parsed successfully")
    return parsed_count


if __name__ == "__main__":
    # Test the optimized traversal
    import asyncio
    from pathlib import Path
    
    async def test_traversal():
        directory = Path(".")
        extensions = {".py", ".js", ".ts", ".java"}
        
        print("Testing optimized directory traversal...")
        
        # Test 1: Basic traversal
        traversal = GitignoreDirectoryTraversal(directory)
        files = list(traversal.traverse_files(extensions))
        
        print(f"Found {len(files)} files")
        print(f"Skipped {len(traversal.skipped_dirs)} directory trees")
        
        if traversal.skipped_dirs:
            print("Skipped directories:")
            for skipped in sorted(traversal.skipped_dirs):
                print(f"  - {skipped}")
        
        print("\nFirst 10 files:")
        for file_path in files[:10]:
            print(f"  - {file_path}")
    
    asyncio.run(test_traversal())