#!/usr/bin/env python3
"""Simple test file to trigger analysis."""

def hello_world():
    \"\"\"Simple function for testing.\"\"\"
    return "Hello, World!"

class TestClass:
    \"\"\"Simple test class.\"\"\"
    
    def __init__(self, name: str):
        self.name = name
    
    def greet(self) -> str:
        \"\"\"Return a greeting.\"\"\"
        return f"Hello, {self.name}!"

if __name__ == "__main__":
    test = TestClass("Code Graph MCP")
    print(test.greet())