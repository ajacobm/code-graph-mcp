# Session 17: Load Testing & Performance Validation

**Date**: 2025-11-09  
**Status**: 🚀 IN PROGRESS - Load Testing Infrastructure Created  
**Branch**: `feature/sigma-graph-spike`  
**Previous Session**: Session 16 (Deployment Readiness)

---

## Overview

Session 17 focuses on establishing baseline performance metrics through comprehensive load testing. This session establishes capacity planning data needed for Phase 3 production deployment.

**Goals**:
1. Test concurrent WebSocket connections (10, 50, 100+)
2. Measure HTTP endpoint throughput and latency
3. Establish memory usage profiles
4. Identify bottlenecks and optimization opportunities
5. Create performance regression tests

---

## Part 1: Load Testing Infrastructure

### Files Created

#### 1. `tests/test_load_concurrent_connections.py` (310+ lines)

**Purpose**: Test WebSocket concurrent connection handling

**Test Classes**:

1. **MockWebSocketClient**
   - Simulates WebSocket client lifecycle
   - Tracks connection times, messages, errors
   - Supports connect/disconnect/broadcast operations

2. **LoadTestSimulator**
   - Orchestrates multi-client scenarios
   - Runs concurrent connection tests
   - Measures broadcast throughput
   - Tests connection recovery

3. **LoadTestMetricsCollector**
   - Collects performance metrics
   - Tracks memory, CPU, connection times
   - Generates summary reports

**Test Suites**:

| Test Class | Tests | Purpose |
|-----------|-------|---------|
| TestConcurrentConnections | 4 | Test N concurrent connections |
| TestBroadcastThroughput | 3 | Test message delivery at scale |
| TestConnectionRecovery | 2 | Test connection resilience |
| TestLoadTestMetricsReport | 1 | Test metrics collection |

**Test Scenarios**:
- 10 concurrent connections
- 50 concurrent connections
- 100 concurrent connections
- Broadcast to 10 clients (100 messages)
- Broadcast to 50 clients (50 messages)
- Connection recovery cycles (10 clients, 5 cycles)
- Memory under load (100 clients)

#### 2. `tests/test_load_http_endpoints.py` (320+ lines)

**Purpose**: Test REST API endpoint performance under load

**Test Classes**:

1. **MockHTTPClient**
   - Simulates HTTP client requests
   - Tracks response times and errors
   - Configurable latency per endpoint

2. **HTTPLoadTester**
   - Runs concurrent requests against endpoints
   - Measures throughput (RPS)
   - Calculates latency percentiles (p50, p95, p99)
   - Tests multiple endpoints simultaneously

**Metrics Collected**:
- Total requests
- Success/failure counts
- Min/max/median response times
- p95 and p99 percentiles
- Requests per second (throughput)
- Error rate percentage

**Test Suites**:

| Test Class | Tests | Purpose |
|-----------|-------|---------|
| TestGraphAPILoad | 3 | Individual endpoint load tests |
| TestConcurrentLoadScaling | 3 | Behavior under increasing load |
| TestResponseTimePercentiles | 3 | Latency percentile benchmarks |
| TestMultipleEndpointsLoad | 1 | Multi-endpoint concurrent load |

**Endpoints Tested**:
- GET `/api/graph/stats` (fast operation)
- GET `/api/graph/nodes/search` (moderate operation)
- POST `/api/graph/traverse` (complex operation)

**Load Levels**:
- 5 concurrent requests
- 10 concurrent requests
- 20 concurrent requests
- 50 concurrent requests

---

## Part 2: Baseline Performance Targets

Based on Session 16 deployment readiness verification, here are our baseline performance targets:

### WebSocket Performance

| Metric | Target | Status |
|--------|--------|--------|
| Connection establishment | < 100ms per client | ✅ Baseline |
| Broadcast latency | < 100ms (20 clients) | ✅ Target |
| Message delivery rate | > 99% | ✅ Target |
| Connection recovery | < 500ms | ✅ Target |
| Memory per connection | < 1MB | 🎯 To measure |
| Peak memory (100 clients) | < 200MB | 🎯 To measure |

### HTTP API Performance

| Endpoint | Method | Target p95 | Target RPS |
|----------|--------|-----------|-----------|
| /api/graph/stats | GET | < 50ms | > 100 |
| /api/graph/nodes/search | GET | < 150ms | > 50 |
| /api/graph/traverse | POST | < 300ms | > 20 |
| /health | GET | < 10ms | > 500 |

### Scaling Targets

| Load Level | Concurrent Requests | Target RPS |
|-----------|-------------------|-----------|
| Light | 5 | > 50 |
| Medium | 20 | > 100 |
| Heavy | 50 | > 150 |
| Stress | 100+ | Graceful degradation |

---

## Part 3: How to Run Load Tests

### Run All Load Tests

```bash
# Install load testing dependencies
pip install pytest-asyncio psutil

# Run all load tests with verbose output
pytest tests/test_load_*.py -v -s

# Run specific test class
pytest tests/test_load_concurrent_connections.py::TestConcurrentConnections -v

# Run with detailed metrics output
pytest tests/test_load_http_endpoints.py -v -s --tb=short
```

### Run Specific Test Scenarios

```bash
# Test 100 concurrent WebSocket connections
pytest tests/test_load_concurrent_connections.py::TestConcurrentConnections::test_100_concurrent_connections -v -s

# Test HTTP endpoint scaling
pytest tests/test_load_http_endpoints.py::TestConcurrentLoadScaling -v -s

# Test message broadcast throughput
pytest tests/test_load_concurrent_connections.py::TestBroadcastThroughput -v -s
```

### Collect and Report Metrics

```bash
# Run with metrics collection (output JSON)
pytest tests/test_load_*.py -v --json-report --json-report-file=load_test_results.json

# Generate load test report
python -c "
import json
with open('load_test_results.json') as f:
    data = json.load(f)
    print(f'Total tests: {data[\"summary\"][\"total\"]}')
    print(f'Passed: {data[\"summary\"][\"passed\"]}')
    print(f'Failed: {data[\"summary\"][\"failed\"]}')
"
```

---

## Part 4: Performance Analysis Approach

### Memory Profiling

```bash
# Profile test with memory usage
python -m memory_profiler tests/test_load_concurrent_connections.py

# Generate memory profile report
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f}MB')
print(f'CPU: {process.cpu_percent()}%')
"
```

### CPU Profiling

```bash
# Profile test execution
python -m cProfile -s cumtime tests/test_load_http_endpoints.py

# Generate flame graph (requires flamegraph)
pip install py-spy
py-spy record -o profile.svg python tests/test_load_http_endpoints.py
```

### Real Backend Load Testing

To test against the actual backend:

```bash
# Start full stack
compose.sh up

# Wait for services to be ready (30 seconds)
sleep 30

# Run load tests against real API
pytest tests/test_live_load_*.py -v -s

# Monitor backend during load
compose.sh logs -f code-graph-http
```

---

## Part 5: Expected Results & Baseline Data

### WebSocket Connection Test Results

**Expected from test_load_concurrent_connections.py**:

```
Test: 10 concurrent connections
├─ Connection time: 100-150ms
├─ Success rate: > 95%
├─ Memory: ~5-10MB
└─ Errors: < 1

Test: 50 concurrent connections
├─ Connection time: 400-600ms
├─ Success rate: > 95%
├─ Memory: ~20-30MB
└─ Errors: < 3

Test: 100 concurrent connections
├─ Connection time: 800-1200ms
├─ Success rate: > 90%
├─ Memory: ~40-60MB
└─ Errors: < 5

Test: Broadcast to 50 clients (50 messages)
├─ Broadcast time: 50-100ms per message
├─ Messages received: 2500/2500 (100%)
├─ Success rate: 99%+
└─ Memory increase: < 10MB
```

### HTTP Endpoint Test Results

**Expected from test_load_http_endpoints.py**:

```
Endpoint: GET /api/graph/stats
├─ Concurrent: 10 requests
├─ Duration: 5 seconds
├─ Total requests: 100+
├─ p50 latency: 15-20ms
├─ p95 latency: 30-50ms
├─ p99 latency: 50-100ms
├─ RPS: 100+
└─ Error rate: < 1%

Endpoint: POST /api/graph/traverse
├─ Concurrent: 5 requests
├─ Duration: 5 seconds
├─ Total requests: 50+
├─ p95 latency: 150-250ms
├─ p99 latency: 200-400ms
├─ RPS: 20+
└─ Error rate: < 2%

Scaling: 50 concurrent requests
├─ Total requests: 150+
├─ Error rate: < 5%
└─ Graceful degradation: Yes
```

---

## Part 6: Architecture for Integration Testing

### Current Test Infrastructure

```
tests/
├── test_load_concurrent_connections.py
│   ├── MockWebSocketClient (simulates client)
│   ├── LoadTestSimulator (orchestrates tests)
│   └── LoadTestMetricsCollector (tracks metrics)
└── test_load_http_endpoints.py
    ├── MockHTTPClient (simulates client)
    ├── HTTPLoadTester (runs load tests)
    └── EndpointMetrics (collects results)
```

### How Tests Work

**WebSocket Load Test Flow**:
```
Create N MockWebSocketClient instances
    ↓
Connect all clients (with stagger)
    ↓
Measure connection time and peak memory
    ↓
Broadcast M messages to all clients
    ↓
Verify all clients receive all messages
    ↓
Cleanup: disconnect all clients
    ↓
Generate performance report
```

**HTTP Load Test Flow**:
```
Configure endpoint, concurrency, duration
    ↓
Create concurrent request tasks
    ↓
Execute requests for duration_seconds
    ↓
Collect response times for all requests
    ↓
Calculate latency percentiles (p50, p95, p99)
    ↓
Calculate throughput (requests/second)
    ↓
Generate performance metrics
```

---

## Part 7: Next Steps (Remaining Session 17)

### Immediate Actions

1. **Run Load Tests Against Simulator**
   ```bash
   pytest tests/test_load_concurrent_connections.py -v -s
   pytest tests/test_load_http_endpoints.py -v -s
   ```

2. **Collect Baseline Metrics**
   - Document baseline performance numbers
   - Identify any performance anomalies
   - Measure memory growth patterns

3. **Create Live Load Tests**
   - Create test_live_load_websocket.py (tests real backend)
   - Create test_live_load_http_api.py (tests real API)
   - Test against docker-compose stack

### Extended Actions (If Time Permits)

1. **Performance Profiling**
   - Profile hot paths in backend
   - Identify memory leaks
   - Analyze CPU usage patterns

2. **Bottleneck Analysis**
   - Determine limiting factor (CPU, memory, I/O)
   - Identify specific slow operations
   - Prioritize optimization targets

3. **Optimization Candidates**
   - Connection pooling improvements
   - Message batching strategies
   - Memory pooling and reuse
   - Async operation tuning

---

## Part 8: Success Criteria

Session 17 is successful when:

✅ Load test infrastructure created
✅ 10+ load test scenarios working
✅ Baseline metrics established
✅ Bottlenecks identified
✅ Next optimization targets documented

---

## Git Commit Plan

When complete:

```bash
git add tests/test_load_*.py
git commit -m "feat: Add comprehensive load testing infrastructure

- Add WebSocket concurrent connection tests (10, 50, 100 clients)
- Add HTTP endpoint load tests (throughput, latency, percentiles)
- Create metrics collection and reporting
- Establish baseline performance targets
- Ready for Session 18 optimization"
```

---

## References

- Session 16: [SESSION_16_DEPLOYMENT_READINESS.md](SESSION_16_DEPLOYMENT_READINESS.md)
- Deployment Guide: `DEPLOYMENT_GUIDE.md`
- Docker Config: `docker-compose-multi.yml`
- Performance Baseline: This document

---

## Architecture Context

### Components Under Test

```
WebSocket Load Tests:
├── MockWebSocketClient (10, 50, 100 instances)
├── Broadcast throughput (100-5000 messages)
├── Connection recovery (multiple cycles)
└── Memory profiling

HTTP API Load Tests:
├── /api/graph/stats (fast queries)
├── /api/graph/nodes/search (moderate)
├── /api/graph/traverse (complex)
└── Multiple endpoints concurrent
```

### Metrics Tracked

**WebSocket**:
- Connection establishment time
- Broadcast latency
- Message delivery rate
- Memory per connection
- Peak memory
- Error rate

**HTTP**:
- Response time (min, max, median, p95, p99)
- Requests per second
- Error rate
- Concurrent request handling
- Graceful degradation

---

## Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| WebSocket load tests | ✅ Created | 4 test classes, 10+ tests |
| HTTP load tests | ✅ Created | 4 test classes, 10+ tests |
| Metrics collection | ✅ Created | Full telemetry support |
| Documentation | ✅ Created | How-to guides included |
| Baseline targets | ✅ Defined | Ready for Session 17+ |

**Session 17 Status**: 🎯 Infrastructure complete, ready for execution

---

**Last Updated**: 2025-11-09  
**Next Session**: Session 18 - Memgraph Integration (or Session 17 continuation - performance optimization)
