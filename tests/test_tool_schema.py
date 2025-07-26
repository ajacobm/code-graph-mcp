#!/usr/bin/env python3
"""
Test what our tools actually look like when serialized to JSON
"""

import json
import mcp.types as types

# Create one of our tools
tool = types.Tool(
    name="complexity_analysis",
    description="Analyze code complexity and refactoring opportunities",
    inputSchema={
        "type": "object",
        "properties": {
            "threshold": {
                "type": "integer",
                "description": "Minimum complexity threshold to report",
                "default": 10,
            }
        },
    },
)

print("Our tool as dict:")
print(json.dumps(tool.model_dump(), indent=2))

print("\nOur tool JSON schema:")
print(json.dumps(tool.model_json_schema(), indent=2))