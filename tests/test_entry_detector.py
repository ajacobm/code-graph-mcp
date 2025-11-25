"""
Test cases for entry point detection service.
"""

import unittest
from unittest.mock import mock_open, patch
from src.codenav.entry_detector import EntryDetector, EntryPointCandidate

class TestEntryDetector(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.detector = EntryDetector()
    
    def test_language_detection(self):
        """Test language detection from file extensions."""
        test_cases = [
            ("main.py", "python"),
            ("app.js", "javascript"),
            ("server.ts", "typescript"),
            ("Main.java", "java"),
            ("Program.cs", "csharp"),
            ("main.go", "go"),
            ("lib.rs", "rust"),
            ("main.cpp", "cpp"),
            ("util.c", "c"),
            ("index.php", "php"),
            ("script.rb", "ruby"),
            ("app.kt", "kotlin"),
            ("main.swift", "swift"),
        ]
        
        for file_path, expected_language in test_cases:
            with self.subTest(file_path=file_path):
                detected = self.detector._detect_language_from_path(file_path)
                self.assertIsNotNone(detected)
                self.assertEqual(detected.value, expected_language)
    
    def test_python_entry_detection(self):
        """Test Python entry point detection."""
        nodes = [
            {
                'id': 'main_func',
                'name': 'main',
                'file_path': 'main.py',
                'line': 10,
                'complexity': 5,
            }
        ]
        
        file_contents = {
            'main.py': '''
def main():
    print("Hello World")

if __name__ == "__main__":
    main()
'''
        }
        
        candidates = self.detector.detect_entry_points(nodes, file_contents)
        
        # Should detect both main function and if-name-main pattern
        self.assertGreater(len(candidates), 0)
        
        # Check that high confidence patterns are detected
        high_confidence = [c for c in candidates if c.confidence_score >= 1.5]
        self.assertGreater(len(high_confidence), 0)
    
    def test_javascript_entry_detection(self):
        """Test JavaScript entry point detection."""
        nodes = [
            {
                'id': 'express_app',
                'name': 'app',
                'file_path': 'server.js',
                'line': 5,
                'complexity': 3,
            }
        ]
        
        file_contents = {
            'server.js': '''
const express = require('express');
const app = express();

app.listen(3000, () => {
    console.log('Server running');
});
'''
        }
        
        candidates = self.detector.detect_entry_points(nodes, file_contents)
        self.assertGreater(len(candidates), 0)
    
    def test_java_entry_detection(self):
        """Test Java entry point detection."""
        nodes = [
            {
                'id': 'main_method',
                'name': 'main',
                'file_path': 'Main.java',
                'line': 3,
                'complexity': 2,
            }
        ]
        
        file_contents = {
            'Main.java': '''
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
'''
        }
        
        candidates = self.detector.detect_entry_points(nodes, file_contents)
        self.assertGreater(len(candidates), 0)
        
        # Should have high confidence for main method
        main_candidates = [c for c in candidates if c.pattern_matched == "main_method"]
        self.assertGreater(len(main_candidates), 0)
        self.assertGreater(main_candidates[0].confidence_score, 2.0)
    
    def test_go_entry_detection(self):
        """Test Go entry point detection."""
        nodes = [
            {
                'id': 'main_func',
                'name': 'main',
                'file_path': 'main.go',
                'line': 3,
                'complexity': 1,
            }
        ]
        
        file_contents = {
            'main.go': '''
package main

func main() {
    println("Hello World")
}
'''
        }
        
        candidates = self.detector.detect_entry_points(nodes, file_contents)
        self.assertGreater(len(candidates), 0)
    
    def test_confidence_scoring(self):
        """Test confidence scoring logic."""
        # Test pattern with high priority and bonus
        pattern = self.detector.patterns['python'][0]  # main_function pattern
        complexity = 5
        score = self.detector._calculate_confidence_score(pattern, complexity)
        
        # Should be greater than base score due to bonuses
        self.assertGreater(score, 1.0)
        
        # Higher complexity should reduce confidence
        high_complexity_score = self.detector._calculate_confidence_score(pattern, 50)
        self.assertLess(high_complexity_score, score)
    
    def test_no_matches(self):
        """Test detection with no matching patterns."""
        nodes = [
            {
                'id': 'regular_func',
                'name': 'helper',
                'file_path': 'utils.py',
                'line': 5,
                'complexity': 1,
            }
        ]
        
        file_contents = {
            'utils.py': '''
def helper():
    return "nothing special"
'''
        }
        
        candidates = self.detector.detect_entry_points(nodes, file_contents)
        # Regular functions should not be detected as entry points
        self.assertEqual(len(candidates), 0)
    
    def test_get_language_patterns(self):
        """Test getting patterns for specific languages."""
        patterns = self.detector.get_language_patterns('python')
        self.assertGreater(len(patterns), 0)
        
        # Test case insensitive
        patterns2 = self.detector.get_language_patterns('PYTHON')
        self.assertEqual(len(patterns), len(patterns2))
        
        # Test unknown language
        unknown_patterns = self.detector.get_language_patterns('unknown')
        self.assertEqual(len(unknown_patterns), 0)

if __name__ == '__main__':
    unittest.main()