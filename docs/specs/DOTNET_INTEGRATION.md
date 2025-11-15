# .NET Core 8 + C# 13 Integration Guide

**Status**: Planning  
**Target**: .NET 8.0, C# 13, OpenAPI 3.1  
**Approach**: OpenAPI spec generation → NSwag client generation → Wrapper SDK

---

## Overview

This document outlines the strategy for integrating Code Graph MCP's Python backend with .NET applications using OpenAPI 3.1 specification and auto-generated C# clients.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Python FastAPI Backend (Port 8000)                         │
│  • Tree-sitter parsing                                      │
│  • rustworkx graph operations                               │
│  • Memgraph Cypher queries                                  │
│  • Redis CDC events                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ OpenAPI 3.1 Spec (auto-generated)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  NSwag Code Generator                                       │
│  • Reads openapi.json                                       │
│  • Generates C# DTOs + HttpClient wrapper                   │
│  • System.Text.Json serialization                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ GraphApiClient.g.cs (generated)
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  .NET SDK Wrapper (dotnet-sdk/)                             │
│  • CodeGraphMcp.Client - High-level API                     │
│  • CodeGraphMcp.Cli - Console app                           │
│  • CodeGraphMcp.Roslyn - C# parsing integration             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Enhanced OpenAPI Spec Generation

### 1.1 Enhance FastAPI Metadata

**File**: `src/code_graph_mcp/http/main.py`

```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    """Enhanced OpenAPI schema with detailed metadata"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Code Graph MCP API",
        version="1.0.0",
        description="""
# Code Graph MCP HTTP API

Graph-based code analysis powered by Tree-sitter, rustworkx, and Memgraph.

## Features
- **Multi-language parsing** (Python, JavaScript, TypeScript, Rust, Go, C#, Java)
- **Real-time CDC events** via Redis Streams + WebSocket
- **Hybrid querying** (rustworkx for simple, Memgraph Cypher for complex)
- **MCP Resources** with pre-built Cypher patterns

## Authentication
Currently no authentication required. Add Bearer token support in production.

## Rate Limiting
No rate limits in development. Recommended: 1000 req/min per client.
        """,
        routes=app.routes,
        tags=[
            {"name": "graph", "description": "Graph data operations (nodes, relationships, queries)"},
            {"name": "analysis", "description": "Code analysis and parsing"},
            {"name": "memgraph", "description": "Memgraph Cypher integration"},
            {"name": "websocket", "description": "Real-time CDC event subscriptions"}
        ],
        contact={
            "name": "Code Graph MCP",
            "url": "https://github.com/ajacobm/code-graph-mcp"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    )
    
    # Add OpenAPI extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://github.com/ajacobm/code-graph-mcp/blob/main/docs/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

### 1.2 Export Script

**File**: `scripts/export_openapi.py`

```python
#!/usr/bin/env python3
"""Export OpenAPI 3.1 spec from FastAPI server"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_graph_mcp.http.main import app

def export_openapi(output_path: Path):
    """Export OpenAPI spec to JSON file"""
    spec = app.openapi()
    
    # Pretty print JSON
    with output_path.open("w") as f:
        json.dump(spec, f, indent=2)
    
    print(f"✅ OpenAPI spec exported to: {output_path}")
    print(f"   Version: {spec['info']['version']}")
    print(f"   Title: {spec['info']['title']}")
    print(f"   Endpoints: {len(spec['paths'])}")
    print(f"   Schemas: {len(spec.get('components', {}).get('schemas', {}))}")

if __name__ == "__main__":
    output = Path(__file__).parent.parent / "openapi.json"
    export_openapi(output)
    print(f"\n🎯 Next: Run 'nswag openapi2csclient' to generate C# client")
```

**Usage**:
```bash
python scripts/export_openapi.py
```

---

## Step 2: NSwag Client Generation

### 2.1 Install NSwag CLI

```bash
# Global install
dotnet tool install -g NSwag.ConsoleCore

# Verify
nswag version
```

### 2.2 NSwag Configuration

**File**: `dotnet-sdk/nswag.json`

```json
{
  "runtime": "Net80",
  "defaultVariables": null,
  "documentGenerator": {
    "fromDocument": {
      "url": "../openapi.json",
      "output": null
    }
  },
  "codeGenerators": {
    "openApiToCSharpClient": {
      "clientBaseClass": null,
      "configurationClass": null,
      "generateClientClasses": true,
      "generateClientInterfaces": true,
      "clientBaseInterface": null,
      "injectHttpClient": true,
      "disposeHttpClient": false,
      "protectedMethods": [],
      "generateExceptionClasses": true,
      "exceptionClass": "GraphApiException",
      "wrapDtoExceptions": true,
      "useHttpClientCreationMethod": false,
      "httpClientType": "System.Net.Http.HttpClient",
      "useHttpRequestMessageCreationMethod": false,
      "useBaseUrl": false,
      "generateBaseUrlProperty": true,
      "generateSyncMethods": false,
      "generatePrepareRequestAndProcessResponseAsAsyncMethods": false,
      "exposeJsonSerializerSettings": false,
      "clientClassAccessModifier": "public",
      "typeAccessModifier": "public",
      "generateContractsOutput": false,
      "contractsNamespace": null,
      "contractsOutputFilePath": null,
      "parameterDateTimeFormat": "s",
      "parameterDateFormat": "yyyy-MM-dd",
      "generateUpdateJsonSerializerSettingsMethod": true,
      "useRequestAndResponseSerializationSettings": false,
      "serializeTypeInformation": false,
      "queryNullValue": "",
      "className": "{controller}Client",
      "operationGenerationMode": "MultipleClientsFromOperationId",
      "additionalNamespaceUsages": [],
      "additionalContractNamespaceUsages": [],
      "generateOptionalParameters": true,
      "generateJsonMethods": false,
      "enforceFlagEnums": false,
      "parameterArrayType": "System.Collections.Generic.ICollection",
      "parameterDictionaryType": "System.Collections.Generic.IDictionary",
      "responseArrayType": "System.Collections.Generic.ICollection",
      "responseDictionaryType": "System.Collections.Generic.IDictionary",
      "wrapResponses": false,
      "wrapResponseMethods": [],
      "generateResponseClasses": true,
      "responseClass": "SwaggerResponse",
      "namespace": "CodeGraphMcp.Client.Generated",
      "requiredPropertiesMustBeDefined": true,
      "dateType": "System.DateTimeOffset",
      "jsonConverters": null,
      "anyType": "object",
      "dateTimeType": "System.DateTimeOffset",
      "timeType": "System.TimeSpan",
      "timeSpanType": "System.TimeSpan",
      "arrayType": "System.Collections.Generic.ICollection",
      "arrayInstanceType": "System.Collections.ObjectModel.Collection",
      "dictionaryType": "System.Collections.Generic.IDictionary",
      "dictionaryInstanceType": "System.Collections.Generic.Dictionary",
      "arrayBaseType": "System.Collections.ObjectModel.Collection",
      "dictionaryBaseType": "System.Collections.Generic.Dictionary",
      "classStyle": "Record",
      "jsonLibrary": "SystemTextJson",
      "generateDefaultValues": true,
      "generateDataAnnotations": true,
      "excludedTypeNames": [],
      "excludedParameterNames": [],
      "handleReferences": false,
      "generateImmutableArrayProperties": false,
      "generateImmutableDictionaryProperties": false,
      "jsonSerializerSettingsTransformationMethod": null,
      "inlineNamedArrays": false,
      "inlineNamedDictionaries": false,
      "inlineNamedTuples": true,
      "inlineNamedAny": false,
      "generateDtoTypes": true,
      "generateOptionalPropertiesAsNullable": false,
      "generateNullableReferenceTypes": true,
      "templateDirectory": null,
      "typeNameGeneratorType": null,
      "propertyNameGeneratorType": null,
      "enumNameGeneratorType": null,
      "serviceHost": null,
      "serviceSchemes": null,
      "output": "CodeGraphMcp.Client/Generated/GraphApiClient.g.cs",
      "newLineBehavior": "Auto"
    }
  }
}
```

### 2.3 Generate Client

```bash
cd dotnet-sdk
nswag run nswag.json
```

**Output**: `dotnet-sdk/CodeGraphMcp.Client/Generated/GraphApiClient.g.cs`

---

## Step 3: .NET SDK Project Structure

```
dotnet-sdk/
├── nswag.json                          # NSwag configuration
├── CodeGraphMcp.sln                    # Solution file
├── CodeGraphMcp.Client/
│   ├── CodeGraphMcp.Client.csproj
│   ├── GraphClient.cs                  # High-level wrapper
│   ├── GraphClientExtensions.cs        # Convenience methods
│   ├── Models/                         # Additional DTOs
│   └── Generated/
│       └── GraphApiClient.g.cs         # NSwag generated (DO NOT EDIT)
├── CodeGraphMcp.Cli/
│   ├── CodeGraphMcp.Cli.csproj
│   ├── Program.cs                      # Console app
│   └── Commands/                       # CLI commands
│       ├── AnalyzeCommand.cs
│       ├── QueryCommand.cs
│       └── StatsCommand.cs
├── CodeGraphMcp.Roslyn/
│   ├── CodeGraphMcp.Roslyn.csproj
│   ├── CSharpAnalyzer.cs               # Roslyn integration
│   └── SyntaxTreeExtractor.cs
└── CodeGraphMcp.Tests/
    ├── CodeGraphMcp.Tests.csproj
    ├── GraphClientTests.cs
    └── IntegrationTests.cs
```

---

## Step 4: High-Level C# Wrapper

**File**: `dotnet-sdk/CodeGraphMcp.Client/GraphClient.cs`

```csharp
using System.Net.Http.Json;
using System.Runtime.CompilerServices;
using CodeGraphMcp.Client.Generated;

namespace CodeGraphMcp.Client;

/// <summary>
/// High-level client for Code Graph MCP API with C# 13 features
/// </summary>
public sealed class GraphClient(HttpClient httpClient) : IDisposable
{
    private readonly IGraphClient _client = new GraphClient(httpClient);
    private readonly HttpClient _http = httpClient;

    /// <summary>
    /// Get graph statistics (nodes, relationships, languages)
    /// </summary>
    public async Task<GraphStats?> GetStatsAsync(CancellationToken ct = default)
    {
        try
        {
            return await _client.Graph_statsAsync(ct);
        }
        catch (GraphApiException ex)
        {
            Console.WriteLine($"API Error: {ex.Message}");
            return null;
        }
    }

    /// <summary>
    /// Search nodes by query string with collection expressions
    /// </summary>
    public async Task<Node[]> SearchNodesAsync(
        string query, 
        int limit = 100, 
        CancellationToken ct = default)
    {
        var response = await _client.Graph_nodes_searchAsync(query, limit, ct);
        return response?.Results?.ToArray() ?? [];
    }

    /// <summary>
    /// Execute Cypher query via MCP Resources
    /// </summary>
    public async Task<CypherResult> ExecuteCypherAsync(
        string pattern, 
        Dictionary<string, object>? parameters = null,
        CancellationToken ct = default)
    {
        var request = new CypherRequest 
        { 
            Pattern = pattern,
            Parameters = parameters ?? []
        };
        
        return await _client.Memgraph_cypherAsync(request, ct);
    }

    /// <summary>
    /// Stream CDC events from Redis (async enumerable)
    /// </summary>
    public async IAsyncEnumerable<GraphEvent> SubscribeToCdcEventsAsync(
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        // WebSocket or SSE connection
        using var response = await _http.GetAsync(
            "/ws/graph/events", 
            HttpCompletionOption.ResponseHeadersRead, 
            ct);
        
        response.EnsureSuccessStatusCode();
        
        await using var stream = await response.Content.ReadAsStreamAsync(ct);
        
        await foreach (var evt in JsonSerializer.DeserializeAsyncEnumerable<GraphEvent>(
            stream, 
            cancellationToken: ct))
        {
            if (evt is not null)
                yield return evt;
        }
    }

    /// <summary>
    /// Batch analyze multiple files
    /// </summary>
    public async Task<AnalysisResult[]> AnalyzeFilesAsync(
        IEnumerable<string> filePaths,
        IProgress<double>? progress = null,
        CancellationToken ct = default)
    {
        var files = filePaths.ToArray();
        var results = new List<AnalysisResult>();
        
        for (int i = 0; i < files.Length; i++)
        {
            var result = await _client.Analysis_fileAsync(
                new AnalyzeFileRequest { Path = files[i] }, 
                ct);
            
            results.Add(result);
            progress?.Report((double)(i + 1) / files.Length);
        }
        
        return [.. results];
    }

    public void Dispose() => _http?.Dispose();
}
```

---

## Step 5: C# 13 Features Showcase

### Primary Constructors
```csharp
public sealed class GraphClient(HttpClient httpClient, ILogger<GraphClient> logger)
{
    private readonly HttpClient _http = httpClient;
    private readonly ILogger _log = logger;
    
    // No need for explicit constructor body
}
```

### Collection Expressions
```csharp
// Old way
return response?.Results?.ToArray() ?? new Node[0];

// C# 13 way
return response?.Results?.ToArray() ?? [];
```

### Required Properties
```csharp
public record GraphStats
{
    public required int TotalNodes { get; init; }
    public required int TotalRelationships { get; init; }
    public required string[] Languages { get; init; }
}
```

### Alias Any Type (C# 12+)
```csharp
using GraphEvent = (string Type, string Data, DateTimeOffset Timestamp);

// Use as tuple
GraphEvent evt = ("NodeAdded", "{...}", DateTimeOffset.Now);
```

---

## Step 6: Dependency Injection Setup

**File**: `dotnet-sdk/CodeGraphMcp.Cli/Program.cs`

```csharp
using CodeGraphMcp.Client;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var builder = Host.CreateApplicationBuilder(args);

// Register GraphClient with HttpClient factory
builder.Services.AddHttpClient<GraphClient>(client =>
{
    client.BaseAddress = new Uri(
        builder.Configuration["GraphMcp:BaseUrl"] 
        ?? "http://localhost:8000");
    client.Timeout = TimeSpan.FromSeconds(30);
})
.AddStandardResilienceHandler(); // Polly retry/circuit breaker

// Add logging
builder.Logging.AddConsole();

var host = builder.Build();

// Example: Fetch graph stats
var graphClient = host.Services.GetRequiredService<GraphClient>();
var stats = await graphClient.GetStatsAsync();

if (stats is not null)
{
    Console.WriteLine($"📊 Graph Statistics:");
    Console.WriteLine($"   Nodes: {stats.TotalNodes}");
    Console.WriteLine($"   Relationships: {stats.TotalRelationships}");
    Console.WriteLine($"   Languages: {string.Join(", ", stats.Languages)}");
}

await host.RunAsync();
```

---

## Step 7: Roslyn Integration (C# Parsing)

**File**: `dotnet-sdk/CodeGraphMcp.Roslyn/CSharpAnalyzer.cs`

```csharp
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace CodeGraphMcp.Roslyn;

/// <summary>
/// Extracts AST from C# code and sends to Python MCP server
/// </summary>
public class CSharpAnalyzer(GraphClient graphClient)
{
    private readonly GraphClient _client = graphClient;

    public async Task<AnalysisResult> AnalyzeCSharpFileAsync(
        string filePath, 
        CancellationToken ct = default)
    {
        var code = await File.ReadAllTextAsync(filePath, ct);
        var tree = CSharpSyntaxTree.ParseText(code);
        var root = await tree.GetRootAsync(ct);

        // Extract classes, methods, fields
        var classes = root.DescendantNodes()
            .OfType<ClassDeclarationSyntax>()
            .Select(c => new NodeDto
            {
                Name = c.Identifier.Text,
                Type = "Class",
                File = filePath,
                Language = "CSharp"
            })
            .ToArray();

        var methods = root.DescendantNodes()
            .OfType<MethodDeclarationSyntax>()
            .Select(m => new NodeDto
            {
                Name = m.Identifier.Text,
                Type = "Method",
                File = filePath,
                Language = "CSharp"
            })
            .ToArray();

        // Send to Python backend
        return await _client.AnalyzeExtractedAstAsync(
            new AstPayload { Nodes = [..classes, ..methods] },
            ct);
    }
}
```

---

## Step 8: Optional Flurl Integration

If you want Flurl for advanced scenarios:

**File**: `dotnet-sdk/CodeGraphMcp.Client/GraphClientFlurlExtensions.cs`

```csharp
using Flurl.Http;

namespace CodeGraphMcp.Client.Extensions;

public static class GraphClientFlurlExtensions
{
    /// <summary>
    /// Execute custom Cypher with Flurl flexibility
    /// </summary>
    public static async Task<T> ExecuteCustomCypherAsync<T>(
        this GraphClient client,
        string cypherQuery,
        object? parameters = null,
        CancellationToken ct = default)
    {
        return await client.BaseUrl
            .AppendPathSegment("api/memgraph/cypher")
            .WithTimeout(30)
            .PostJsonAsync(new 
            { 
                query = cypherQuery, 
                parameters 
            }, cancellationToken: ct)
            .ReceiveJson<T>();
    }
}
```

---

## Step 9: Build & Test

### 9.1 Project File

**File**: `dotnet-sdk/CodeGraphMcp.Client/CodeGraphMcp.Client.csproj`

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <LangVersion>13.0</LangVersion>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>

  <ItemGroup>
    <!-- System packages -->
    <PackageReference Include="System.Text.Json" Version="8.0.0" />
    
    <!-- NSwag runtime -->
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
    
    <!-- Optional: Flurl for advanced scenarios -->
    <PackageReference Include="Flurl.Http" Version="4.0.2" />
    
    <!-- Polly for resilience -->
    <PackageReference Include="Microsoft.Extensions.Http.Resilience" Version="8.0.0" />
  </ItemGroup>

  <!-- Auto-regenerate client on build -->
  <Target Name="NSwagGenerate" BeforeTargets="CoreCompile" Condition="'$(Configuration)' == 'Debug'">
    <Exec Command="nswag run ../nswag.json" WorkingDirectory="$(ProjectDir)" />
  </Target>
</Project>
```

### 9.2 Build

```bash
cd dotnet-sdk
dotnet build
```

### 9.3 Test

```bash
dotnet test
```

---

## Step 10: Example Usage

```csharp
using CodeGraphMcp.Client;

// Create client
using var httpClient = new HttpClient { BaseAddress = new Uri("http://localhost:8000") };
using var client = new GraphClient(httpClient);

// Get stats
var stats = await client.GetStatsAsync();
Console.WriteLine($"Total nodes: {stats?.TotalNodes}");

// Search nodes
var nodes = await client.SearchNodesAsync("MyFunction");
foreach (var node in nodes)
{
    Console.WriteLine($"  {node.Name} ({node.Type})");
}

// Execute Cypher
var cypherResult = await client.ExecuteCypherAsync(
    "MATCH (f:Function) RETURN f.name LIMIT 10");

// Stream CDC events
await foreach (var evt in client.SubscribeToCdcEventsAsync())
{
    Console.WriteLine($"Event: {evt.Type} - {evt.Data}");
}
```

---

## Recommendations

### ✅ Use NSwag (Not Swagger Codegen)
- Better C# 13 support
- System.Text.Json native
- Actively maintained
- Record types support

### ✅ Stick with Generated Client for Core API
- Type safety from OpenAPI spec
- Auto-updates when API changes
- IntelliSense support

### ✅ Add Flurl Only for Edge Cases
- Batch uploads
- Dynamic endpoints
- Custom retry logic

### ✅ Use Polly for Resilience
- Circuit breaker for Memgraph
- Retry for transient failures
- Timeout policies

---

## Future Enhancements

1. **Blazor UI** - Interactive graph visualization (alternative to Jupyter)
2. **gRPC Service** - High-performance streaming for CDC events
3. **Source Generators** - Generate C# models from Python dataclasses
4. **Native AOT** - Compile to native binary for faster startup
5. **SignalR Hub** - Real-time updates for multiple clients

---

## References

- [NSwag Documentation](https://github.com/RicoSuter/NSwag)
- [FastAPI OpenAPI](https://fastapi.tiangolo.com/advanced/extending-openapi/)
- [C# 13 Features](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-13)
- [.NET 8 Performance](https://devblogs.microsoft.com/dotnet/performance-improvements-in-net-8/)
- [Flurl Documentation](https://flurl.dev/)
