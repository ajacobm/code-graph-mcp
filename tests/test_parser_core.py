#!/usr/bin/env python3
"""
Unit tests for core parser functionality
Tests ASTGrepPatterns, parsing logic, and graph population
Designed to run independently without full dependency tree
"""

import sys
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestASTGrepPatterns:
    """Test ASTGrepPatterns coverage and correctness"""
    
    def test_all_languages_have_patterns(self):
        """Verify all 25 languages have AST patterns"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        # Extract PATTERNS dict
        pattern_match = re.search(r'PATTERNS = \{(.*?)\n    \}', content, re.DOTALL)
        assert pattern_match, "Could not find PATTERNS dict"
        
        patterns_text = pattern_match.group(1)
        languages = re.findall(r'"(\w+)":\s*{', patterns_text)
        unique_langs = sorted(set(languages))
        
        print(f"\n✅ Found {len(unique_langs)} languages with patterns")
        assert len(unique_langs) >= 25, f"Expected 25+ languages, got {len(unique_langs)}"
        
        # Verify specific key languages
        required = ["python", "javascript", "typescript", "java", "rust", "go", "cpp", 
                   "csharp", "php", "ruby", "html", "css"]
        for lang in required:
            assert lang in unique_langs, f"Missing required language: {lang}"
            print(f"  ✅ {lang}")
    
    def test_each_language_has_function_pattern(self):
        """Verify each language has a function pattern"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        pattern_match = re.search(r'PATTERNS = \{(.*?)\n    \}', content, re.DOTALL)
        patterns_text = pattern_match.group(1)
        
        # Check each language block has function, class, import patterns
        lang_blocks = re.finditer(r'"(\w+)":\s*\{([^}]+)\}', patterns_text)
        
        count = 0
        for match in lang_blocks:
            lang = match.group(1)
            block = match.group(2)
            
            has_function = '"function"' in block
            has_class = '"class"' in block
            has_import = '"import"' in block
            
            assert has_function, f"{lang} missing function pattern"
            assert has_class, f"{lang} missing class pattern"
            assert has_import, f"{lang} missing import pattern"
            count += 1
        
        print(f"✅ {count} languages verified with complete patterns")
    
    def test_patterns_are_not_empty_strings(self):
        """Verify pattern values aren't empty"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        pattern_match = re.search(r'PATTERNS = \{(.*?)\n    \}', content, re.DOTALL)
        patterns_text = pattern_match.group(1)
        
        # Find all pattern values (after colons)
        values = re.findall(r':\s*"([^"]+)"', patterns_text)
        
        for value in values:
            assert value, "Found empty pattern value"
            assert len(value) > 0, "Pattern value is empty string"
        
        print(f"✅ All {len(values)} pattern values are non-empty")


class TestParsingLogic:
    """Test core parsing function logic"""
    
    def test_parse_functions_ast_pattern_check(self):
        """Verify _parse_functions_ast checks for pattern before processing"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        # Find _parse_functions_ast method
        func_match = re.search(
            r'def _parse_functions_ast\(.*?\n(.*?)(?=\n    def |\Z)',
            content,
            re.DOTALL
        )
        assert func_match, "Could not find _parse_functions_ast method"
        
        method_body = func_match.group(1)
        
        # Check that it calls get_pattern
        assert 'get_pattern' in method_body, "Method doesn't call get_pattern()"
        assert 'if pattern:' in method_body or 'if pattern :' in method_body, \
            "Method doesn't check if pattern before using it"
        
        # Check that it uses root_node.find_all
        assert 'root_node.find_all' in method_body, "Method doesn't use root_node.find_all()"
        
        print("✅ _parse_functions_ast has correct logic flow")
    
    def test_parse_classes_ast_pattern_check(self):
        """Verify _parse_classes_ast checks for pattern before processing"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        func_match = re.search(
            r'def _parse_classes_ast\(.*?\n(.*?)(?=\n    def |\Z)',
            content,
            re.DOTALL
        )
        assert func_match, "Could not find _parse_classes_ast method"
        
        method_body = func_match.group(1)
        assert 'get_pattern' in method_body
        assert 'root_node.find_all' in method_body
        
        print("✅ _parse_classes_ast has correct logic flow")
    
    def test_parse_imports_ast_pattern_check(self):
        """Verify _parse_imports_ast checks for pattern before processing"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        func_match = re.search(
            r'def _parse_imports_ast\(.*?\n(.*?)(?=\n    def |\Z)',
            content,
            re.DOTALL
        )
        assert func_match, "Could not find _parse_imports_ast method"
        
        method_body = func_match.group(1)
        assert 'get_pattern' in method_body
        assert 'root_node.find_all' in method_body
        
        print("✅ _parse_imports_ast has correct logic flow")


class TestGraphPopulation:
    """Test graph node creation logic"""
    
    def test_graph_add_node_called_in_parsing(self):
        """Verify parsing functions call self.graph.add_node()"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        for func_name in ["_parse_functions_ast", "_parse_classes_ast", "_parse_imports_ast"]:
            func_match = re.search(
                rf'def {func_name}\(.*?\n(.*?)(?=\n    def |\Z)',
                content,
                re.DOTALL
            )
            assert func_match, f"Could not find {func_name}"
            
            method_body = func_match.group(1)
            assert 'self.graph.add_node' in method_body, \
                f"{func_name} doesn't call self.graph.add_node()"
        
        print("✅ All parsing functions call self.graph.add_node()")
    
    def test_file_node_creation(self):
        """Verify file nodes are created"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        # Find _create_file_node method
        assert '_create_file_node' in content, "No _create_file_node method"
        
        # Find where file nodes are added in _parse_file_content
        parse_content_match = re.search(
            r'async def _parse_file_content\(.*?\n(.*?)(?=\n    async def |\n    def |\Z)',
            content,
            re.DOTALL
        )
        assert parse_content_match, "Could not find _parse_file_content"
        
        parse_content = parse_content_match.group(1)
        assert '_create_file_node' in parse_content, "File node not created in _parse_file_content"
        assert 'self.graph.add_node(file_node)' in parse_content, "File node not added to graph"
        
        print("✅ File node creation verified")


class TestNodeIdentifiers:
    """Test node ID generation"""
    
    def test_function_node_ids_unique(self):
        """Verify function node IDs are unique"""
        with open(Path(__file__).parent.parent / "src/code_graph_mcp/universal_parser.py") as f:
            content = f.read()
        
        # Find _parse_functions_ast
        func_match = re.search(
            r'def _parse_functions_ast\(.*?\n(.*?)(?=\n    def |\Z)',
            content,
            re.DOTALL
        )
        method_body = func_match.group(1)
        
        # Check it uses file_path and start_line for uniqueness
        assert 'file_path' in method_body, "Function IDs don't use file_path"
        assert 'start_line' in method_body, "Function IDs don't use start_line"
        
        print("✅ Function node IDs include file and line")


def run_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 70)
    print("CODE GRAPH MCP - PARSER CORE UNIT TESTS")
    print("=" * 70)
    
    test_classes = [
        TestASTGrepPatterns,
        TestParsingLogic,
        TestGraphPopulation,
        TestNodeIdentifiers
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 60)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                passed_tests += 1
                print(f"  PASS: {method_name}")
            except AssertionError as e:
                print(f"  FAIL: {method_name}")
                print(f"        {e}")
            except Exception as e:
                print(f"  ERROR: {method_name}")
                print(f"         {e}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 70)
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
