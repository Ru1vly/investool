#!/bin/bash
# ============================================================================
# Phase 4.1: Activate Production Caching
#
# This script enables and optimizes Redis caching for production performance.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 4.1: Activate Production Caching                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Configuration
# ============================================================================

NAMESPACE="${NAMESPACE:-finrisk-ai}"
CACHE_TTL="${CACHE_TTL:-3600}"  # 1 hour default
CACHE_MAX_SIZE="${CACHE_MAX_SIZE:-1000}"  # Max cached items

# ============================================================================
# Check Prerequisites
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Checking Prerequisites"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    exit 1
fi
echo "✅ kubectl found"

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi
echo "✅ Connected to cluster"

# Check namespace
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "❌ Namespace $NAMESPACE not found"
    exit 1
fi
echo "✅ Namespace exists"

# Check Redis is running
REDIS_POD=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -z "$REDIS_POD" ]; then
    echo "❌ Redis pod not found"
    exit 1
fi

POD_STATUS=$(kubectl get pod "$REDIS_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
if [ "$POD_STATUS" != "Running" ]; then
    echo "❌ Redis pod is not running (status: $POD_STATUS)"
    exit 1
fi
echo "✅ Redis pod running: $REDIS_POD"

echo ""

# ============================================================================
# Configure Caching Parameters
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Configure Caching"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Current configuration:"
echo "  • Cache TTL: $CACHE_TTL seconds ($(($CACHE_TTL / 60)) minutes)"
echo "  • Max cached items: $CACHE_MAX_SIZE"
echo ""

read -p "Use these settings? (y/n) [y]: " USE_DEFAULTS
USE_DEFAULTS=${USE_DEFAULTS:-y}

if [ "$USE_DEFAULTS" != "y" ]; then
    read -p "Cache TTL in seconds [$CACHE_TTL]: " NEW_TTL
    CACHE_TTL=${NEW_TTL:-$CACHE_TTL}

    read -p "Max cached items [$CACHE_MAX_SIZE]: " NEW_MAX_SIZE
    CACHE_MAX_SIZE=${NEW_MAX_SIZE:-$CACHE_MAX_SIZE}
fi

echo ""
echo "✅ Configuration confirmed"
echo ""

# ============================================================================
# Update ConfigMap
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Update Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Updating ConfigMap with caching settings..."

# Patch the configmap
kubectl patch configmap finrisk-config -n "$NAMESPACE" \
    --type='json' \
    -p="[
        {\"op\":\"add\",\"path\":\"/data/ENABLE_CACHING\",\"value\":\"true\"},
        {\"op\":\"add\",\"path\":\"/data/CACHE_TTL\",\"value\":\"$CACHE_TTL\"},
        {\"op\":\"add\",\"path\":\"/data/CACHE_MAX_SIZE\",\"value\":\"$CACHE_MAX_SIZE\"},
        {\"op\":\"add\",\"path\":\"/data/CACHE_STRATEGY\",\"value\":\"lru\"}
    ]"

echo "✅ ConfigMap updated"
echo ""

# ============================================================================
# Optimize Redis Configuration
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Optimize Redis"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Applying Redis optimizations..."

# Set maxmemory policy (LRU eviction)
kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
echo "✅ Set eviction policy: allkeys-lru"

# Set maxmemory limit (1GB)
kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli CONFIG SET maxmemory 1gb
echo "✅ Set max memory: 1GB"

# Enable RDB snapshots for persistence
kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli CONFIG SET save "900 1 300 10 60 10000"
echo "✅ Enabled RDB persistence"

# Set connection timeout
kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli CONFIG SET timeout 300
echo "✅ Set connection timeout: 300s"

echo ""

# ============================================================================
# Test Redis Connection
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Test Redis"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Testing Redis connectivity..."

# Test SET/GET
TEST_KEY="finrisk:cache:test:$(date +%s)"
TEST_VALUE="cache_test_value"

kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli SET "$TEST_KEY" "$TEST_VALUE" EX 60 > /dev/null
RETRIEVED=$(kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli GET "$TEST_KEY")

if [ "$RETRIEVED" = "$TEST_VALUE" ]; then
    echo "✅ Redis read/write test passed"
    kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli DEL "$TEST_KEY" > /dev/null
else
    echo "❌ Redis test failed"
    exit 1
fi

# Get Redis stats
echo ""
echo "Redis statistics:"
kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli INFO stats | grep -E "(total_connections_received|total_commands_processed|keyspace_hits|keyspace_misses)"

echo ""

# ============================================================================
# Restart API Pods
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Restart API Pods"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Restarting API pods to enable caching..."

kubectl rollout restart deployment/finrisk-api -n "$NAMESPACE"

echo "Waiting for rollout to complete..."
kubectl rollout status deployment/finrisk-api -n "$NAMESPACE" --timeout=5m

echo "✅ API pods restarted"
echo ""

# ============================================================================
# Verify Caching is Active
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Verify Caching"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Wait a moment for pods to fully start
sleep 5

# Check API logs for caching initialization
API_POD=$(kubectl get pods -n "$NAMESPACE" -l app=finrisk-api -o jsonpath='{.items[0].metadata.name}')

echo "Checking API logs for caching messages..."
if kubectl logs "$API_POD" -n "$NAMESPACE" --tail=50 | grep -i "cach"; then
    echo ""
    echo "✅ Caching appears to be initialized"
else
    echo ""
    echo "⚠️  No caching messages found in logs (may still be initializing)"
fi

echo ""

# ============================================================================
# Cache Monitoring Commands
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Caching Activated!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
echo "  • Caching: ENABLED"
echo "  • TTL: $CACHE_TTL seconds ($(($CACHE_TTL / 60)) minutes)"
echo "  • Max size: $CACHE_MAX_SIZE items"
echo "  • Strategy: LRU (Least Recently Used)"
echo "  • Redis memory: 1GB"
echo ""
echo "Monitor caching:"
echo ""
echo "  # Redis statistics"
echo "  kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli INFO stats"
echo ""
echo "  # Current keys"
echo "  kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli KEYS 'finrisk:*'"
echo ""
echo "  # Cache hit rate"
echo "  kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli INFO stats | grep keyspace"
echo ""
echo "  # Memory usage"
echo "  kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli INFO memory | grep used_memory_human"
echo ""
echo "  # Watch keys in real-time"
echo "  kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli MONITOR"
echo ""
echo "Next steps:"
echo "  1. Make API requests to populate cache"
echo "  2. Monitor hit/miss ratio"
echo "  3. Adjust TTL if needed"
echo "  4. Run: ./scripts/monitoring/2-benchmark-performance.sh"
echo ""
