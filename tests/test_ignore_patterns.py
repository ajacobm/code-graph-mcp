"""Tests for ignore patterns management."""

import pytest
import tempfile
from pathlib import Path
from code_graph_mcp.ignore_patterns import (
    IgnorePatternsManager,
    IgnoreConfig
)


class TestIgnorePatternsManager:
    """Test ignore pattern matching and language filtering."""
    
    def test_default_initialization(self):
        """Test manager initializes without .graphignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = IgnorePatternsManager(tmpdir)
            assert manager.patterns == []
            assert manager.language_filters == set()
            assert manager.include_patterns == []
    
    def test_load_graphignore_patterns(self):
        """Test loading .graphignore file with patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text(
                "node_modules/\n"
                "*.min.js\n"
                "dist/\n"
                "build/\n"
            )
            
            manager = IgnorePatternsManager(tmpdir)
            assert len(manager.patterns) == 4
    
    def test_language_filters(self):
        """Test language filtering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text(
                "language: csharp\n"
                "language: typescript\n"
            )
            
            manager = IgnorePatternsManager(tmpdir)
            assert "csharp" in manager.language_filters
            assert "typescript" in manager.language_filters
            
            assert manager.should_analyze_language("csharp")
            assert manager.should_analyze_language("typescript")
            assert not manager.should_analyze_language("python")
    
    def test_include_patterns(self):
        """Test whitelist include patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text(
                "node_modules/\n"
                "!node_modules/@types/*\n"
            )
            
            manager = IgnorePatternsManager(tmpdir)
            
            assert manager.should_ignore_path("node_modules/lodash/index.js")
            assert not manager.should_ignore_path("node_modules/@types/node/index.d.ts")
    
    def test_path_pattern_matching(self):
        """Test glob pattern matching for file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text(
                "*.min.js\n"
                "dist/*\n"
                "node_modules/*\n"
            )
            
            manager = IgnorePatternsManager(tmpdir)
            
            assert manager.should_ignore_path("app.min.js")
            assert manager.should_ignore_path("src/app.min.js")
            assert manager.should_ignore_path("dist/index.html")
            assert manager.should_ignore_path("node_modules/react/package.json")
            
            assert not manager.should_ignore_path("app.js")
            assert not manager.should_ignore_path("src/index.ts")
    
    def test_runtime_pattern_addition(self):
        """Test adding patterns at runtime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = IgnorePatternsManager(tmpdir)
            
            manager.add_pattern("*.test.js")
            manager.add_pattern("coverage/*")
            
            assert manager.should_ignore_path("app.test.js")
            assert manager.should_ignore_path("coverage/index.html")
    
    def test_runtime_language_filter(self):
        """Test adding language filters at runtime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = IgnorePatternsManager(tmpdir)
            
            manager.add_language_filter("javascript")
            manager.add_language_filter("typescript")
            
            assert manager.should_analyze_language("javascript")
            assert manager.should_analyze_language("typescript")
            assert not manager.should_analyze_language("python")
    
    def test_clear_language_filters(self):
        """Test clearing language filters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text("language: csharp\n")
            
            manager = IgnorePatternsManager(tmpdir)
            assert "csharp" in manager.language_filters
            
            manager.clear_language_filters()
            assert manager.language_filters == set()
            assert manager.should_analyze_language("any_language")
    
    def test_config_serialization(self):
        """Test serializing and deserializing configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text(
                "node_modules/\n"
                "*.min.js\n"
                "language: typescript\n"
                "!node_modules/@types/*\n"
            )
            
            manager = IgnorePatternsManager(tmpdir)
            config = manager.get_config()
            
            assert isinstance(config, IgnoreConfig)
            assert len(config.path_patterns) == 2
            assert "typescript" in config.language_filters
            assert len(config.include_patterns) == 1
            
            manager2 = IgnorePatternsManager.load_from_config(config, tmpdir)
            assert manager2.patterns == manager.patterns
            assert manager2.language_filters == manager.language_filters
            assert manager2.include_patterns == manager.include_patterns
    
    def test_comments_in_graphignore(self):
        """Test that comments are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text(
                "# Comment\n"
                "node_modules/\n"
                "# Another comment\n"
                "*.min.js\n"
            )
            
            manager = IgnorePatternsManager(tmpdir)
            assert len(manager.patterns) == 2
    
    def test_empty_lines_ignored(self):
        """Test that empty lines are handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graphignore = Path(tmpdir) / ".graphignore"
            graphignore.write_text(
                "node_modules/\n"
                "\n"
                "*.min.js\n"
                "   \n"
                "dist/\n"
            )
            
            manager = IgnorePatternsManager(tmpdir)
            assert len(manager.patterns) == 3
