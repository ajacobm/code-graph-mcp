#!/usr/bin/env python3
"""
Comprehensive tests for the multi-language code graph transformation.
Tests the universal parser, graph structures, and language detection.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.code_graph_mcp.universal_parser import UniversalParser, LanguageRegistry
from src.code_graph_mcp.universal_graph import UniversalGraph, NodeType
from src.code_graph_mcp.universal_ast import UniversalASTAnalyzer
from src.code_graph_mcp.language_router import LanguageDetector, ProjectAnalyzer


class TestLanguageSupport:
    """Test multi-language support capabilities."""

    def test_language_registry_completeness(self):
        """Test that language registry supports 25+ languages."""
        registry = LanguageRegistry()

        assert registry.get_language_count() >= 25

        # Test specific languages are supported
        expected_languages = [
            'javascript', 'typescript', 'python', 'java', 'csharp',
            'cpp', 'c', 'rust', 'go', 'kotlin', 'scala', 'swift',
            'dart', 'ruby', 'php', 'elixir', 'elm', 'lua', 'html',
            'css', 'sql', 'yaml', 'json', 'xml', 'markdown'
        ]

        for lang in expected_languages:
            assert lang in registry.LANGUAGES, f"Missing language: {lang}"

    def test_file_extension_detection(self):
        """Test language detection by file extension."""
        registry = LanguageRegistry()

        test_cases = [
            ('.py', 'python'),
            ('.js', 'javascript'),
            ('.ts', 'typescript'),
            ('.java', 'java'),
            ('.rs', 'rust'),
            ('.go', 'go'),
            ('.cpp', 'cpp'),
            ('.html', 'html'),
            ('.css', 'css'),
            ('.json', 'json'),
        ]

        for ext, expected_lang in test_cases:
            file_path = Path(f"test{ext}")
            config = registry.get_language_by_extension(file_path)
            assert config is not None, f"No config found for {ext}"
            assert expected_lang in config.name.lower() or (expected_lang == 'cpp' and 'c++' in config.name.lower()), f"Wrong language for {ext}: got {config.name}"


class TestUniversalParser:
    """Test the universal parser with multiple languages."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary multi-language project."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create test files in different languages
        test_files = {
            'main.py': '''
def hello_world():
    """Say hello to the world."""
    print("Hello from Python!")

class Calculator:
    def add(self, a, b):
        return a + b
''',
            'app.js': '''
function helloWorld() {
    console.log("Hello from JavaScript!");
}

class Calculator {
    add(a, b) {
        return a + b;
    }
}
''',
            'Main.java': '''
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
    }

    public static class Calculator {
        public int add(int a, int b) {
            return a + b;
        }
    }
}
''',
            'hello.rs': '''
fn main() {
    println!("Hello from Rust!");
}

struct Calculator;

impl Calculator {
    fn add(&self, a: i32, b: i32) -> i32 {
        a + b
    }
}
'''
        }

        for filename, content in test_files.items():
            file_path = temp_dir / filename
            file_path.write_text(content)

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_single_file_parsing(self, temp_project):
        """Test parsing individual files in different languages."""
        parser = UniversalParser(temp_project)

        # Test Python file
        python_file = temp_project / 'main.py'
        python_graph = parser.parse_file(python_file)

        assert python_graph is not None
        assert len(python_graph.nodes) > 0
        assert 'python' in python_graph.languages

        # Check for functions and classes
        functions = python_graph.get_nodes_by_type(NodeType.FUNCTION)
        classes = python_graph.get_nodes_by_type(NodeType.CLASS)

        assert len(functions) >= 1  # hello_world and add methods
        assert len(classes) >= 1    # Calculator class

    def test_directory_parsing(self, temp_project):
        """Test parsing entire multi-language directory."""
        parser = UniversalParser(temp_project)

        combined_graph = parser.parse_directory()

        # Should have parsed multiple languages
        assert len(combined_graph.languages) >= 3  # Python, JavaScript, Java, Rust
        assert combined_graph.file_count >= 4

        # Should have nodes from all languages
        total_nodes = len(combined_graph.nodes)
        assert total_nodes > 10  # Multiple functions and classes across languages

        # Test language distribution
        assert 'python' in combined_graph.languages
        assert 'javascript' in combined_graph.languages
        assert 'java' in combined_graph.languages


class TestLanguageDetection:
    """Test intelligent language detection."""

    def test_extension_detection(self):
        """Test detection by file extension."""
        detector = LanguageDetector()

        test_cases = [
            ('test.py', 'Python'),
            ('app.js', 'JavaScript'),
            ('Main.java', 'Java'),
            ('hello.rs', 'Rust'),
            ('main.go', 'Go'),
        ]

        for filename, expected_lang in test_cases:
            file_path = Path(filename)
            config = detector.detect_file_language(file_path)
            assert config is not None
            assert expected_lang.lower() in config.name.lower()

    def test_content_signature_detection(self):
        """Test detection by content patterns."""
        detector = LanguageDetector()

        # Test Python content
        python_content = '''
def main():
    import os
    print("Hello Python")
    if __name__ == "__main__":
        main()
'''

        detected = detector._detect_by_content_signatures(python_content)
        assert detected == 'python'

        # Test JavaScript content
        js_content = '''
function main() {
    const message = "Hello JavaScript";
    console.log(message);
}
module.exports = main;
'''

        detected = detector._detect_by_content_signatures(js_content)
        assert detected == 'javascript'


class TestUniversalGraph:
    """Test universal graph structures work across languages."""

    def test_node_creation(self):
        """Test creating universal nodes for different languages."""
        from src.code_graph_mcp.universal_graph import UniversalNode, SourceLocation

        # Create nodes for different languages
        python_node = UniversalNode(
            id="py_func_1",
            node_type=NodeType.FUNCTION,
            name="calculate",
            qualified_name="math.calculate",
            location=SourceLocation(Path("test.py"), 1, 1, 10, 1),
            language="python",
            raw_kind="function_definition"
        )

        js_node = UniversalNode(
            id="js_func_1",
            node_type=NodeType.FUNCTION,
            name="calculate",
            qualified_name="math.calculate",
            location=SourceLocation(Path("test.js"), 1, 1, 10, 1),
            language="javascript",
            raw_kind="function_declaration"
        )

        # Both should have same universal type despite different raw kinds
        assert python_node.node_type == js_node.node_type
        assert python_node.node_type == NodeType.FUNCTION

    def test_graph_multi_language_operations(self):
        """Test graph operations work across multiple languages."""
        from src.code_graph_mcp.universal_graph import UniversalNode, SourceLocation

        graph = UniversalGraph()

        # Add nodes from different languages
        languages = ['python', 'javascript', 'java', 'rust']
        for i, lang in enumerate(languages):
            node = UniversalNode(
                id=f"{lang}_node_{i}",
                node_type=NodeType.FUNCTION,
                name=f"func_{i}",
                qualified_name=f"module.func_{i}",
                location=SourceLocation(Path(f"test.{lang[:2]}"), 1, 1, 5, 1),
                language=lang,
                raw_kind="function"
            )
            graph.add_node(node)

        # Test multi-language queries
        assert len(graph.languages) == 4
        assert graph.get_nodes_by_language('python')
        assert graph.get_nodes_by_language('javascript')
        assert len(graph.get_nodes_by_type(NodeType.FUNCTION)) == 4


class TestUniversalASTAnalyzer:
    """Test cross-language AST analysis capabilities."""

    @pytest.fixture
    def sample_graph(self):
        """Create a sample multi-language graph."""
        from src.code_graph_mcp.universal_graph import UniversalNode, SourceLocation

        graph = UniversalGraph()

        # Add some test nodes
        for i in range(5):
            node = UniversalNode(
                id=f"func_{i}",
                node_type=NodeType.FUNCTION,
                name=f"function_{i}",
                qualified_name=f"module.function_{i}",
                location=SourceLocation(Path("test.py"), i, 1, i+5, 1),
                language="python",
                raw_kind="function_definition",
                complexity=i * 3 + 1,  # Varying complexity
                line_count=i * 10 + 5   # Varying size
            )
            graph.add_node(node)

        return graph

    def test_code_smell_detection(self, sample_graph):
        """Test cross-language code smell detection."""
        from src.code_graph_mcp.universal_parser import UniversalParser

        parser = UniversalParser(Path("."))
        analyzer = UniversalASTAnalyzer(parser)

        smells = analyzer.detect_code_smells(sample_graph)

        # Should detect different types of smells
        assert 'long_functions' in smells
        assert 'complex_functions' in smells
        assert 'large_classes' in smells

        # Should have some complex functions (complexity > 15)
        complex_funcs = [node for node in sample_graph.nodes.values() if node.complexity > 15]
        assert len(smells['complex_functions']) == len(complex_funcs)

    def test_maintainability_calculation(self, sample_graph):
        """Test maintainability index calculation."""
        from src.code_graph_mcp.universal_parser import UniversalParser

        parser = UniversalParser(Path("."))
        analyzer = UniversalASTAnalyzer(parser)

        maintainability = analyzer.calculate_maintainability_index(sample_graph)

        # Should return a score between 0 and 100
        assert 0 <= maintainability <= 100
        assert isinstance(maintainability, float)


class TestProjectAnalysis:
    """Test project-level multi-language analysis."""

    @pytest.fixture
    def complex_project(self):
        """Create a complex multi-language project structure."""
        temp_dir = Path(tempfile.mkdtemp())

        # Create directory structure
        (temp_dir / 'src').mkdir()
        (temp_dir / 'tests').mkdir()
        (temp_dir / 'docs').mkdir()

        # Create files
        files = {
            'package.json': '{"name": "test", "dependencies": {"react": "^18.0.0"}}',
            'src/main.py': 'def main(): pass',
            'src/app.js': 'function app() {}',
            'src/Main.java': 'public class Main {}',
            'tests/test_main.py': 'def test_main(): assert True',
            'docs/README.md': '# Test Project',
            '.github/workflows/ci.yml': 'name: CI'
        }

        for filepath, content in files.items():
            full_path = temp_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_project_analysis(self, complex_project):
        """Test comprehensive project analysis."""
        analyzer = ProjectAnalyzer()
        profile = analyzer.analyze_project(complex_project)

        # Should detect multiple languages
        assert len(profile.languages) >= 3
        assert 'python' in profile.languages
        assert 'javascript' in profile.languages
        assert 'java' in profile.languages

        # Should detect frameworks
        assert 'react' in profile.framework_hints or 'npm' in profile.framework_hints

        # Should detect project structure
        assert profile.has_tests
        assert profile.has_documentation
        assert profile.has_ci_config

        # Should have reasonable confidence
        assert profile.confidence_score > 0.5


def test_integration_end_to_end():
    """Integration test of the entire multi-language pipeline."""
    # Create temporary project
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Create multi-language files
        files = {
            'main.py': 'def hello(): print("Python")',
            'app.js': 'function hello() { console.log("JS"); }',
            'Main.java': 'class Main { void hello() { System.out.println("Java"); } }'
        }

        for filename, content in files.items():
            (temp_dir / filename).write_text(content)

        # Test complete pipeline
        parser = UniversalParser(temp_dir)
        graph = parser.parse_directory()

        # Verify multi-language support works end-to-end
        assert len(graph.languages) >= 3
        assert len(graph.nodes) >= 6  # 3 files * ~2 nodes each

        # Test analysis
        analyzer = UniversalASTAnalyzer(parser)
        functions = graph.get_nodes_by_type(NodeType.FUNCTION)

        if functions:
            result = analyzer.analyze_function(functions[0])
            assert result.node is not None
            assert result.complexity >= 1

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
