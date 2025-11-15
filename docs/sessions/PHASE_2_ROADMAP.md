# Phase 2: Real-Time Event Deployment & Validation Roadmap

**Status**: Ready to begin  
**Estimated Duration**: Sessions 19-22 (8-12 hours)  
**Blocker Status**: ✅ NONE - All Phase 1 components verified  
**Architecture**: Validated in Sessions 14-18  

---

## Phase 2 Overview

Deploy and validate the complete real-time event pipeline:
```
Code mutations (UniversalGraph)
    ↓
CDCManager (records events)
    ↓
Redis Streams (persistent) + Redis Pub/Sub (real-time)
    ↓
WebSocketConnectionManager (broadcast)
    ↓
/ws/events endpoint (validated in Session 18 ✅)
    ↓
Frontend EventsClient (auto-connect)
    ↓
Vue components (LiveStats, EventLog, AnalysisProgress)
    ↓
User sees real-time code analysis updates 🚀
```

---

## Session 19: Real-Time Event Integration Testing

### Objectives
1. Start full stack with live code analysis
2. Verify CDC events are published to Redis Streams
3. Verify WebSocket clients receive events
4. Test frontend components update in real-time
5. Document any issues found

### Test Plan

#### Part 1: Backend Event Flow Verification
```bash
# Start stack
compose.sh up
sleep 30

# Monitor Redis Streams
docker exec code-graph-mcp-redis-1 redis-cli XREAD COUNT 10 STREAMS graph-events 0

# Monitor Redis Pub/Sub
docker exec code-graph-mcp-redis-1 redis-cli SUBSCRIBE graph-events

# Trigger re-analysis
curl -X POST http://localhost:8000/api/graph/admin/reanalyze

# Verify events appear
```

#### Part 2: WebSocket Event Delivery
```bash
# Create simple WebSocket client to monitor events
python -c "
import asyncio
import websockets
import json

async def monitor():
    async with websockets.connect('ws://localhost:8000/ws/events') as ws:
        async for msg in ws:
            data = json.loads(msg)
            print(f'Event: {data[\"event_type\"]} - {data.get(\"data\", {}).get(\"name\", \"?\")}')

asyncio.run(monitor())
"

# In separate terminal:
curl -X POST http://localhost:8000/api/graph/admin/reanalyze
```

#### Part 3: Frontend Real-Time Updates
```bash
# Open browser to http://localhost:5173
# Navigate to EventLog tab
# Trigger re-analysis with Re-analyze button
# Watch for events appearing in real-time

# Test scenarios:
1. Initial graph load → EventLog shows node_added events
2. Click "Re-analyze" → AnalysisProgress bar shows 0-100%
3. Analysis completes → EventLog shows analysis_completed
4. LiveStats shows updated node count
5. Scroll EventLog → See all CDC events
```

### Success Criteria
- [ ] Redis Streams receiving events (xlen > 0)
- [ ] Redis Pub/Sub subscribers receiving events (non-zero count)
- [ ] WebSocket clients receiving JSON events
- [ ] Frontend EventLog component displays events
- [ ] LiveStats counters update in real-time
- [ ] AnalysisProgress bar progresses during analysis
- [ ] No console errors in browser

### Files to Check
- `src/code_graph_mcp/cdc_manager.py` - Event publishing
- `src/code_graph_mcp/websocket_server.py` - Broadcasting
- `frontend/src/composables/useEvents.ts` - Subscription
- `frontend/src/components/EventLog.vue` - Display

---

## Session 20: Load Testing with Real Events

### Objectives
1. Run load tests while generating CDC events
2. Measure event latency and throughput
3. Monitor resource usage under sustained load
4. Identify performance bottlenecks
5. Validate graceful degradation

### Test Scenarios

#### Scenario 1: Single Client Event Storm
```bash
# Start backend + monitor
compose.sh up

# Trigger analysis (generates 400-500+ CDC events)
curl -X POST http://localhost:8000/api/graph/admin/reanalyze

# Connect one WebSocket client + measure
python tests/test_live_load_websocket.py::TestLiveWebSocketLoad::test_single_connection -v -s

# Metrics to collect:
# - Events delivered
# - Latency distribution
# - Memory growth
```

#### Scenario 2: 10 Concurrent Clients
```bash
# Connect 10 WebSocket clients
# Trigger analysis
# Measure concurrent event delivery

pytest tests/test_live_load_websocket.py::TestLiveWebSocketLoad::test_10_concurrent_connections -v -s

# Monitor:
# - CPU usage: docker stats
# - Memory: docker exec ... free -m
# - Event queue depth: XLEN graph-events
```

#### Scenario 3: Sustained Analysis Load
```bash
# Run 5 re-analyses in sequence
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/graph/admin/reanalyze
  sleep 30  # Wait for analysis
done

# Monitor:
# - Total events processed
# - Average latency per event
# - Memory leak detection (should be stable)
```

### Success Criteria
- [ ] All events delivered to connected clients
- [ ] Latency <50ms (p95)
- [ ] Memory stable (no leaks)
- [ ] CPU < 80% during sustained load
- [ ] Zero message loss
- [ ] Graceful handling of disconnects/reconnects

---

## Session 21: Frontend E2E Testing with Real Events

### Objectives
1. Playwright tests for real-time UI updates
2. Test all real-time components (LiveStats, EventLog, AnalysisProgress)
3. Test reconnection scenarios
4. Test event filtering
5. Validate responsive UI during updates

### Test Suite: test_realtime_e2e.py

```python
# Key test scenarios:
def test_livestats_updates_during_analysis()
def test_eventlog_displays_events_in_realtime()
def test_analysisprogress_bar_progresses()
def test_websocket_reconnects_on_disconnect()
def test_event_filtering_works()
def test_ui_responsive_during_event_flood()
def test_cleared_events_dont_reappear()
```

### Test Flow

```bash
# Start stack + frontend
compose.sh up
sleep 30

# Run E2E tests with Playwright
pytest tests/playwright/test_realtime_e2e.py -v -s

# Playwright will:
1. Load frontend
2. Connect WebSocket (visible in DevTools)
3. Trigger analysis
4. Monitor component updates
5. Assert events visible
6. Disconnect/reconnect
7. Verify recovery
```

### Success Criteria
- [ ] 10/10 E2E tests passing
- [ ] LiveStats node count updates
- [ ] EventLog shows all events
- [ ] AnalysisProgress reaches 100%
- [ ] Reconnection after network failure
- [ ] Event filtering functional
- [ ] UI remains responsive

---

## Session 22: Performance Optimization & Documentation

### Objectives
1. Optimize hot paths if needed
2. Document performance characteristics
3. Create production deployment guide
4. Validate against all targets
5. Merge Phase 1 to main branch

### Performance Checklist

#### If Exceeding Targets ✅
- Document as-is
- No changes needed
- Ready for production

#### If Approaching Limits
- [ ] Implement event batching (group CDC events before broadcast)
- [ ] Add message compression (reduce WebSocket payload)
- [ ] Connection pooling to Redis
- [ ] Query result caching

#### If Below Targets
- [ ] Profile hot paths (CPU profiler)
- [ ] Analyze memory allocations
- [ ] Check for synchronous blocking
- [ ] Review event queue design

### Documentation Tasks
- [ ] Update DEPLOYMENT_GUIDE.md with Phase 2 results
- [ ] Add WebSocket performance benchmarks
- [ ] Document CDC event volume expectations
- [ ] Create scaling recommendations
- [ ] Add operational monitoring guide

### Merge Readiness Checklist
- [ ] All Phase 1-2 tests passing
- [ ] Code review completed
- [ ] Documentation complete
- [ ] Performance targets met
- [ ] Docker images built and tagged
- [ ] CHANGELOG.md updated
- [ ] Branch protection rules satisfied

---

## Testing Strategy

### Mock Tests (Fast, Always Run)
```bash
pytest tests/test_load_concurrent_connections.py -v
pytest tests/test_load_http_endpoints.py -v
```

### Live Backend Tests (Real Environment)
```bash
compose.sh up
pytest tests/test_live_load_http.py -v -s
pytest tests/test_live_load_websocket.py -v -s
```

### E2E Tests (Full User Flow)
```bash
compose.sh up
pytest tests/playwright/test_realtime_e2e.py -v -s
```

### Continuous Monitoring
```bash
# Terminal 1: Stack logs
compose.sh logs -f code-graph-http

# Terminal 2: Redis monitoring
docker exec code-graph-mcp-redis-1 redis-cli MONITOR

# Terminal 3: Resource usage
watch 'docker stats code-graph-mcp-code-graph-http-1'
```

---

## Known Issues & Mitigations

### Issue 1: CDC Event Volume
**Risk**: Analysis might generate thousands of events, overwhelming clients
**Mitigation**: Implement event batching/throttling
**Test**: Measure event count during full-stack analysis

### Issue 2: WebSocket Connection Limits
**Risk**: 100+ concurrent connections might hit OS limits
**Mitigation**: Check `ulimit -n`, adjust if needed
**Test**: Run 100 concurrent connection test

### Issue 3: Memory Leaks
**Risk**: Long-running connections might leak memory
**Mitigation**: Implement connection timeout, dead connection cleanup
**Test**: 24-hour continuous monitoring

### Issue 4: Network Instability
**Risk**: Clients in poor network might flood server with reconnect attempts
**Mitigation**: Exponential backoff already implemented in EventsClient
**Test**: Simulate network failures in test

---

## Files to Create/Modify

### New Files
- `tests/playwright/test_realtime_e2e.py` (200+ lines)
- `docs/PHASE_2_PERFORMANCE_REPORT.md` (comprehensive metrics)
- `docs/WEBSOCKET_SCALING_GUIDE.md` (operational guide)

### Modify
- `DEPLOYMENT_GUIDE.md` - Add Phase 2 section
- `CHANGELOG.md` - Document Phase 2 features
- `docs/sessions/current/PHASE_2_SUMMARY.md` - Final report

---

## Success Metrics (End of Phase 2)

| Metric | Target | Status |
|--------|--------|--------|
| All tests passing | 100% | TBD |
| HTTP throughput | 361 req/s | Validated ✅ |
| WebSocket success | 100% | Validated ✅ |
| Event latency p95 | <50ms | TBD |
| Memory stable | <growth | TBD |
| E2E tests | 10/10 | TBD |
| Documentation | Complete | TBD |
| Ready for production | Yes | TBD |

---

## Timeline Estimate

| Session | Duration | Tasks |
|---------|----------|-------|
| 19 | 2-3h | Event integration testing |
| 20 | 2-3h | Load testing with events |
| 21 | 2-3h | E2E Playwright tests |
| 22 | 1-2h | Optimization + merge |
| **Total** | **8-11h** | **Phase 2 complete** |

---

## Communication Checklist

Before each session:
- [ ] Review previous session results
- [ ] Check cortex memory for context
- [ ] Read relevant doc files
- [ ] Verify Docker stack healthy

During each session:
- [ ] Update CRUSH.md with progress
- [ ] Save findings to cortex
- [ ] Commit frequently (clean history)
- [ ] Document blockers

After each session:
- [ ] Update docs/sessions/current/SESSION_XX.md
- [ ] Link in CRUSH.md
- [ ] Push to cortex memory
- [ ] Prepare for next session

---

## Next Steps

1. **Now**: Phase 1 ✅ complete, documented, tested
2. **Session 19**: Start Phase 2 event integration testing
3. **Sessions 20-21**: Validation and E2E testing
4. **Session 22**: Optimization and production merge
5. **Phase 3**: Memgraph integration + advanced features

---

**Status**: Ready to begin Phase 2 whenever you want! 🚀

**Phase 1 Completion**: Sessions 1-18  
**Phase 1 Branch**: feature/sigma-graph-spike  
**Phase 1 Commits**: 9ba6c91 (latest)  
**Phase 2 Start**: Session 19 (when ready)

---

**Last Updated**: 2025-11-09  
**Next Document**: SESSION_19_REALTIME_INTEGRATION.md (when session begins)
