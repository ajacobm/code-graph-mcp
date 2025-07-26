#!/usr/bin/env python3
"""
Test script to explore ast-grep capabilities and supported languages
"""

import ast_grep_py as ag

# Test basic functionality
def test_supported_languages():
    """Explore what languages ast-grep supports"""
    print("=== AST-GREP LANGUAGE EXPLORATION ===")

    # Test with different language files to see what works
    test_cases = [
        ("Python", "def hello():\n    print('world')", "python"),
        ("JavaScript", "function hello() {\n    console.log('world');\n}", "javascript"),
        ("TypeScript", "function hello(): void {\n    console.log('world');\n}", "typescript"),
        ("Java", "public class Hello {\n    public static void main(String[] args) {\n        System.out.println(\"world\");\n    }\n}", "java"),
        ("C", "#include <stdio.h>\nint main() {\n    printf(\"world\");\n    return 0;\n}", "c"),
        ("Rust", "fn main() {\n    println!(\"world\");\n}", "rust"),
        ("Go", "package main\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"world\")\n}", "go"),
    ]

    supported_languages = []

    for lang_name, code, lang_id in test_cases:
        try:
            print(f"\n--- Testing {lang_name} ---")
            root = ag.SgRoot(code, lang_id)
            root_node = root.root()
            print(f"✅ {lang_name}: Successfully parsed (root kind: {root_node.kind()})")
            supported_languages.append(lang_name)

            # Try to find patterns based on language
            if lang_name == "Python":
                nodes = root_node.find_all({"rule": {"kind": "function_definition"}})
            elif lang_name in ["JavaScript", "TypeScript"]:
                nodes = root_node.find_all({"rule": {"kind": "function_declaration"}})
            elif lang_name == "Java":
                nodes = root_node.find_all({"rule": {"kind": "method_declaration"}})
            else:
                nodes = []

            print(f"   Functions found: {len(nodes) if nodes else 0}")

        except Exception as e:
            print(f"❌ {lang_name}: Error - {e}")

    print("\n=== SUMMARY ===")
    print(f"Supported languages ({len(supported_languages)}): {', '.join(supported_languages)}")
    return supported_languages

def test_node_capabilities():
    """Test ast-grep node traversal and querying capabilities"""
    print("\n=== AST-GREP NODE CAPABILITIES ===")

    # Python example
    python_code = """
def calculate_complexity(node):
    '''Calculate cyclomatic complexity'''
    complexity = 1
    for child in node.children():
        if child.kind() in ['if_statement', 'while_statement']:
            complexity += 1
    return complexity

class CodeAnalyzer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.cache = {}
"""

    root = ag.SgRoot(python_code, "python")
    root_node = root.root()

    print("Root node:", root_node.kind())
    print("Child count:", len(root_node.children()))

    # Find function definitions
    functions = root_node.find_all({"rule": {"kind": "function_definition"}})
    print(f"Functions found: {len(functions)}")

    for func in functions:
        print(f"  - Function: {func.text()[:50]}...")
        print(f"    Kind: {func.kind()}")

    # Find class definitions
    classes = root_node.find_all({"rule": {"kind": "class_definition"}})
    print(f"Classes found: {len(classes)}")

    for cls in classes:
        print(f"  - Class: {cls.text()[:50]}...")

if __name__ == "__main__":
    supported_langs = test_supported_languages()
    test_node_capabilities()
