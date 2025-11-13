#!/bin/bash
# ============================================================================
# Phase 4.2: Performance Benchmarking
#
# Comprehensive performance testing for the FinRisk AI system.
# Tests throughput, latency, caching, and resource usage.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 4.2: Performance Benchmarking                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Configuration
# ============================================================================

NAMESPACE="${NAMESPACE:-finrisk-ai}"
BENCHMARK_DURATION="${BENCHMARK_DURATION:-60}"  # seconds
CONCURRENT_USERS="${CONCURRENT_USERS:-10}"
REQUESTS_PER_USER="${REQUESTS_PER_USER:-20}"
OUTPUT_DIR="${OUTPUT_DIR:-./benchmark_results}"

# ============================================================================
# Check Prerequisites
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Checking Prerequisites"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check curl
if ! command -v curl &> /dev/null; then
    echo "❌ curl not found"
    exit 1
fi
echo "✅ curl found"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    exit 1
fi
echo "✅ kubectl found"

# Check if ab (Apache Bench) is available
if command -v ab &> /dev/null; then
    echo "✅ Apache Bench (ab) found"
    HAS_AB=true
else
    echo "⚠️  Apache Bench (ab) not found (optional)"
    HAS_AB=false
fi

echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$OUTPUT_DIR/benchmark_${TIMESTAMP}.txt"

# ============================================================================
# Setup Port Forward
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Setup API Connection"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if port-forward is already running
if lsof -Pi :9999 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 9999 already in use"
    read -p "Kill existing process and continue? (y/n) [y]: " KILL_EXISTING
    KILL_EXISTING=${KILL_EXISTING:-y}
    if [ "$KILL_EXISTING" = "y" ]; then
        pkill -f "port-forward.*finrisk-api" 2>/dev/null || true
        sleep 2
    else
        echo "Using existing port-forward"
    fi
fi

if ! lsof -Pi :9999 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "Starting port-forward to API..."
    kubectl port-forward -n "$NAMESPACE" svc/finrisk-api-service 9999:80 >/dev/null 2>&1 &
    PF_PID=$!
    echo "Port-forward started (PID: $PF_PID)"

    # Wait for port-forward to be ready
    sleep 3
fi

# Test connection
if curl -s -f http://localhost:9999/health >/dev/null; then
    echo "✅ API connection established"
else
    echo "❌ Cannot connect to API"
    exit 1
fi

echo ""

# ============================================================================
# Test 1: Health Check Performance
# ============================================================================

echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "  Test 1: Health Check Performance" | tee -a "$REPORT_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "Running 100 health check requests..." | tee -a "$REPORT_FILE"

TOTAL_TIME=0
SUCCESS=0
FAILURE=0

for i in {1..100}; do
    START=$(date +%s%N)
    if curl -s -f http://localhost:9999/health >/dev/null 2>&1; then
        END=$(date +%s%N)
        DURATION=$(( (END - START) / 1000000 ))  # Convert to ms
        TOTAL_TIME=$((TOTAL_TIME + DURATION))
        SUCCESS=$((SUCCESS + 1))
    else
        FAILURE=$((FAILURE + 1))
    fi
done

AVG_TIME=$((TOTAL_TIME / SUCCESS))

echo "Results:" | tee -a "$REPORT_FILE"
echo "  • Successful: $SUCCESS/100" | tee -a "$REPORT_FILE"
echo "  • Failed: $FAILURE/100" | tee -a "$REPORT_FILE"
echo "  • Average latency: ${AVG_TIME}ms" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# ============================================================================
# Test 2: Cache Performance (Same Query)
# ============================================================================

echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "  Test 2: Cache Performance" | tee -a "$REPORT_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

TEST_QUERY="Analyze Apple stock performance for Q1 2024"

echo "Testing cache with repeated queries..." | tee -a "$REPORT_FILE"
echo "Query: $TEST_QUERY" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# First request (cache miss)
echo "Request 1 (cache miss):" | tee -a "$REPORT_FILE"
START=$(date +%s%N)
curl -s -X POST http://localhost:9999/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d "{\"strategy\":\"$TEST_QUERY\",\"user_id\":\"benchmark_user\",\"session_id\":\"bench_session\"}" \
    -o /dev/null 2>&1
END=$(date +%s%N)
FIRST_REQUEST=$(( (END - START) / 1000000 ))
echo "  Latency: ${FIRST_REQUEST}ms" | tee -a "$REPORT_FILE"

sleep 1

# Second request (cache hit)
echo "Request 2 (cache hit):" | tee -a "$REPORT_FILE"
START=$(date +%s%N)
curl -s -X POST http://localhost:9999/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d "{\"strategy\":\"$TEST_QUERY\",\"user_id\":\"benchmark_user\",\"session_id\":\"bench_session\"}" \
    -o /dev/null 2>&1
END=$(date +%s%N)
SECOND_REQUEST=$(( (END - START) / 1000000 ))
echo "  Latency: ${SECOND_REQUEST}ms" | tee -a "$REPORT_FILE"

if [ $SECOND_REQUEST -lt $FIRST_REQUEST ]; then
    SPEEDUP=$(( (FIRST_REQUEST - SECOND_REQUEST) * 100 / FIRST_REQUEST ))
    echo "  Cache speedup: ${SPEEDUP}% faster" | tee -a "$REPORT_FILE"
else
    echo "  ⚠️  No speedup detected (cache may not be active)" | tee -a "$REPORT_FILE"
fi

echo "" | tee -a "$REPORT_FILE"

# ============================================================================
# Test 3: Concurrent Users Test
# ============================================================================

echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "  Test 3: Concurrent Users ($CONCURRENT_USERS users)" | tee -a "$REPORT_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "Running concurrent requests..." | tee -a "$REPORT_FILE"

CONCURRENT_START=$(date +%s)

# Launch concurrent requests
for i in $(seq 1 $CONCURRENT_USERS); do
    (
        for j in $(seq 1 $REQUESTS_PER_USER); do
            curl -s -X POST http://localhost:9999/api/v1/analyze \
                -H "Content-Type: application/json" \
                -d "{\"strategy\":\"Test query $i-$j\",\"user_id\":\"user_$i\",\"session_id\":\"session_$i\"}" \
                -o /dev/null 2>&1
        done
    ) &
done

# Wait for all to complete
wait

CONCURRENT_END=$(date +%s)
CONCURRENT_DURATION=$((CONCURRENT_END - CONCURRENT_START))
TOTAL_REQUESTS=$((CONCURRENT_USERS * REQUESTS_PER_USER))
THROUGHPUT=$(echo "scale=2; $TOTAL_REQUESTS / $CONCURRENT_DURATION" | bc)

echo "Results:" | tee -a "$REPORT_FILE"
echo "  • Total requests: $TOTAL_REQUESTS" | tee -a "$REPORT_FILE"
echo "  • Duration: ${CONCURRENT_DURATION}s" | tee -a "$REPORT_FILE"
echo "  • Throughput: ${THROUGHPUT} requests/sec" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# ============================================================================
# Test 4: Resource Usage
# ============================================================================

echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "  Test 4: Resource Usage" | tee -a "$REPORT_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "Current resource usage:" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Get pod resource usage
kubectl top pods -n "$NAMESPACE" 2>/dev/null | tee -a "$REPORT_FILE" || echo "⚠️  Metrics not available (metrics-server may not be installed)" | tee -a "$REPORT_FILE"

echo "" | tee -a "$REPORT_FILE"

# ============================================================================
# Test 5: Redis Cache Statistics
# ============================================================================

echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "  Test 5: Redis Cache Statistics" | tee -a "$REPORT_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

REDIS_POD=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ ! -z "$REDIS_POD" ]; then
    echo "Redis cache statistics:" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"

    # Get cache stats
    kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli INFO stats 2>/dev/null | grep -E "(keyspace_hits|keyspace_misses|total_commands_processed)" | tee -a "$REPORT_FILE"

    echo "" | tee -a "$REPORT_FILE"

    # Calculate hit rate
    HITS=$(kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli INFO stats 2>/dev/null | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
    MISSES=$(kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli INFO stats 2>/dev/null | grep keyspace_misses | cut -d: -f2 | tr -d '\r')

    if [ ! -z "$HITS" ] && [ ! -z "$MISSES" ] && [ $((HITS + MISSES)) -gt 0 ]; then
        HIT_RATE=$(echo "scale=2; $HITS * 100 / ($HITS + $MISSES)" | bc)
        echo "Cache hit rate: ${HIT_RATE}%" | tee -a "$REPORT_FILE"
    fi

    echo "" | tee -a "$REPORT_FILE"

    # Get memory usage
    echo "Redis memory usage:" | tee -a "$REPORT_FILE"
    kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli INFO memory 2>/dev/null | grep -E "(used_memory_human|maxmemory_human)" | tee -a "$REPORT_FILE"
else
    echo "⚠️  Redis pod not found" | tee -a "$REPORT_FILE"
fi

echo "" | tee -a "$REPORT_FILE"

# ============================================================================
# Test 6: Apache Bench (if available)
# ============================================================================

if [ "$HAS_AB" = true ]; then
    echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
    echo "  Test 6: Apache Bench Load Test" | tee -a "$REPORT_FILE"
    echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"

    echo "Running Apache Bench (100 requests, 10 concurrent)..." | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"

    ab -n 100 -c 10 -q http://localhost:9999/health 2>&1 | grep -E "(Requests per second|Time per request|Transfer rate|Percentage of the requests)" | tee -a "$REPORT_FILE"

    echo "" | tee -a "$REPORT_FILE"
fi

# ============================================================================
# Summary
# ============================================================================

echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "  ✅ Benchmark Complete!" | tee -a "$REPORT_FILE"
echo "═══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "Report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "Summary:" | tee -a "$REPORT_FILE"
echo "  • Health check latency: ${AVG_TIME}ms" | tee -a "$REPORT_FILE"
echo "  • Cache performance: ${FIRST_REQUEST}ms → ${SECOND_REQUEST}ms" | tee -a "$REPORT_FILE"
echo "  • Throughput: ${THROUGHPUT} req/s" | tee -a "$REPORT_FILE"
if [ ! -z "$HIT_RATE" ]; then
    echo "  • Cache hit rate: ${HIT_RATE}%" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

echo "Recommendations:" | tee -a "$REPORT_FILE"
if [ $AVG_TIME -gt 100 ]; then
    echo "  ⚠️  High health check latency (>${AVG_TIME}ms) - check API performance" | tee -a "$REPORT_FILE"
fi
if [ ! -z "$HIT_RATE" ] && [ $(echo "$HIT_RATE < 50" | bc) -eq 1 ]; then
    echo "  ⚠️  Low cache hit rate (<50%) - increase TTL or check cache strategy" | tee -a "$REPORT_FILE"
fi
if [ $(echo "$THROUGHPUT < 5" | bc) -eq 1 ]; then
    echo "  ⚠️  Low throughput (<5 req/s) - consider scaling or optimization" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

echo "Next steps:" | tee -a "$REPORT_FILE"
echo "  1. Review full report: cat $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "  2. Adjust resources if needed: ./scripts/monitoring/3-optimize-resources.sh" | tee -a "$REPORT_FILE"
echo "  3. Setup monitoring: ./scripts/monitoring/4-setup-monitoring.sh" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Cleanup port-forward if we started it
if [ ! -z "$PF_PID" ]; then
    kill $PF_PID 2>/dev/null || true
fi
