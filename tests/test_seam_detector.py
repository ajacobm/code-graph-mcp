"""Tests for cross-language seam detection."""

import pytest
from code_graph_mcp.seam_detector import SeamDetector


class TestSeamDetector:
    """Test cross-language seam detection."""
    
    def test_initialization(self):
        """Test detector initializes with patterns."""
        detector = SeamDetector()
        seams = detector.get_registered_seams()
        
        assert len(seams) > 0
        assert ("csharp", "node") in seams
        assert ("csharp", "sql") in seams
        assert ("typescript", "python") in seams
    
    def test_csharp_to_node_detection(self):
        """Test detecting C# calling Node.js."""
        detector = SeamDetector()
        
        code = """
        var client = new HttpClient();
        var response = await client.PostAsync("http://node-service:3000/api", content);
        """
        
        result = detector.detect_seams(
            "csharp", "node", code,
            "ProcessData", "NodeService"
        )
        
        assert result is True
    
    def test_csharp_to_sql_detection(self):
        """Test detecting C# calling SQL Server."""
        detector = SeamDetector()
        
        code = """
        using (SqlConnection conn = new SqlConnection(connString)) {
            SqlCommand cmd = new SqlCommand("SELECT * FROM Users", conn);
            SqlDataReader reader = cmd.ExecuteReader();
        }
        """
        
        result = detector.detect_seams(
            "csharp", "sql", code,
            "GetUsers", "UserRepository"
        )
        
        assert result is True
    
    def test_typescript_to_python_detection(self):
        """Test detecting TypeScript calling Python."""
        detector = SeamDetector()
        
        code = """
        const response = await fetch('http://api.example.com/python-service', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        """
        
        result = detector.detect_seams(
            "typescript", "python", code,
            "fetchData", "PythonAPI"
        )
        
        assert result is True
    
    def test_typescript_node_import_detection(self):
        """Test detecting TypeScript importing Node modules."""
        detector = SeamDetector()
        
        code = """
        import { HttpClient } from '@angular/common/http';
        import * as express from 'express';
        """
        
        result = detector.detect_seams(
            "typescript", "node", code,
            "App", "ExpressServer"
        )
        
        assert result is True
    
    def test_python_to_sql_detection(self):
        """Test detecting Python calling SQL."""
        detector = SeamDetector()
        
        code = """
        import psycopg2
        conn = psycopg2.connect("dbname=mydb user=postgres")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        """
        
        result = detector.detect_seams(
            "python", "sql", code,
            "get_users", "database"
        )
        
        assert result is True
    
    def test_no_seam_detected_same_language(self):
        """Test no seam detected for same language."""
        detector = SeamDetector()
        
        code = """
        function add(a, b) {
            return a + b;
        }
        """
        
        result = detector.detect_seams(
            "javascript", "javascript", code,
            "add", "math"
        )
        
        assert result is False
    
    def test_no_seam_unregistered_pair(self):
        """Test no seam detected for unregistered language pair."""
        detector = SeamDetector()
        
        code = """
        some code here
        """
        
        result = detector.detect_seams(
            "rust", "go", code,
            "func1", "func2"
        )
        
        assert result is False
    
    def test_add_custom_pattern(self):
        """Test adding custom seam patterns."""
        detector = SeamDetector()
        
        detector.add_pattern("rust", "go", r"ffi::.*call")
        
        code = """
        unsafe { ffi::go_function_call() }
        """
        
        result = detector.detect_seams(
            "rust", "go", code,
            "call_go", "golib"
        )
        
        assert result is True
    
    def test_case_insensitive_detection(self):
        """Test pattern matching is case insensitive."""
        detector = SeamDetector()
        
        code = """
        VAR CLIENT = NEW HTTPCLIENT();
        RESPONSE = AWAIT CLIENT.POSTASYNC("http://service", content);
        """
        
        result = detector.detect_seams(
            "csharp", "node", code,
            "Service", "API"
        )
        
        assert result is True
    
    def test_multi_language_architecture(self):
        """Test detecting multiple seams in complex code."""
        detector = SeamDetector()
        
        csharp_code = """
        var nodeClient = new HttpClient();
        var nodeResp = await nodeClient.PostAsync("http://node-service", data);
        
        var sqlConn = new SqlConnection(connString);
        var cmd = new SqlCommand("SELECT * FROM Users", sqlConn);
        """
        
        seam_to_node = detector.detect_seams(
            "csharp", "node", csharp_code,
            "Service", "NodeAPI"
        )
        
        seam_to_sql = detector.detect_seams(
            "csharp", "sql", csharp_code,
            "Service", "Database"
        )
        
        assert seam_to_node is True
        assert seam_to_sql is True
