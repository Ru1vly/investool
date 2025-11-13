#!/bin/bash
# ============================================================================
# Phase 2.4: Validate Deployment
#
# Performs end-to-end validation of the deployed FinRisk AI system.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       FinRisk AI - Deployment Validation                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    exit 1
fi

# Check namespace exists
if ! kubectl get namespace finrisk-ai &> /dev/null; then
    echo "❌ Namespace 'finrisk-ai' not found"
    echo "   Run ./scripts/deployment/3-deploy-k8s.sh first"
    exit 1
fi

echo "Running comprehensive validation tests..."
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
test_start() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "[$TOTAL_TESTS] $1... "
}

test_pass() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "✅ PASS"
}

test_fail() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "❌ FAIL"
    if [ -n "$1" ]; then
        echo "     $1"
    fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "  Test Suite 1: Infrastructure"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 1: Namespace
test_start "Namespace exists"
if kubectl get namespace finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "Namespace not found"
fi

# Test 2: ConfigMap
test_start "ConfigMap deployed"
if kubectl get configmap finrisk-config -n finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "ConfigMap not found"
fi

# Test 3: Secrets
test_start "Secrets deployed"
if kubectl get secret finrisk-secrets -n finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "Secrets not found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Test Suite 2: Pods"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 4: PostgreSQL pod
test_start "PostgreSQL pod running"
if kubectl get pods -n finrisk-ai -l app=postgres | grep -q "Running"; then
    test_pass
else
    test_fail "$(kubectl get pods -n finrisk-ai -l app=postgres --no-headers 2>/dev/null || echo 'Pod not found')"
fi

# Test 5: Redis pod
test_start "Redis pod running"
if kubectl get pods -n finrisk-ai -l app=redis | grep -q "Running"; then
    test_pass
else
    test_fail "$(kubectl get pods -n finrisk-ai -l app=redis --no-headers 2>/dev/null || echo 'Pod not found')"
fi

# Test 6: Neo4j pod
test_start "Neo4j pod running"
if kubectl get pods -n finrisk-ai -l app=neo4j | grep -q "Running"; then
    test_pass
else
    test_fail "$(kubectl get pods -n finrisk-ai -l app=neo4j --no-headers 2>/dev/null || echo 'Pod not found')"
fi

# Test 7: API pods
test_start "FinRisk API pods running"
API_PODS=$(kubectl get pods -n finrisk-ai -l app=finrisk-api --no-headers 2>/dev/null | wc -l)
API_RUNNING=$(kubectl get pods -n finrisk-ai -l app=finrisk-api | grep -c "Running" || echo "0")
if [ "$API_RUNNING" -gt 0 ]; then
    test_pass
    echo "     ($API_RUNNING/$API_PODS pods running)"
else
    test_fail "No API pods running"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Test Suite 3: Services"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 8: PostgreSQL service
test_start "PostgreSQL service available"
if kubectl get svc postgres-service -n finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "Service not found"
fi

# Test 9: Redis service
test_start "Redis service available"
if kubectl get svc redis-service -n finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "Service not found"
fi

# Test 10: Neo4j service
test_start "Neo4j service available"
if kubectl get svc neo4j-service -n finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "Service not found"
fi

# Test 11: API service
test_start "FinRisk API service available"
if kubectl get svc finrisk-api-service -n finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "Service not found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Test Suite 4: API Health"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Setup port forwarding for testing
echo "Setting up port forward for testing..."
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 9999:80 > /dev/null 2>&1 &
PF_PID=$!
sleep 3

# Test 12: Health endpoint
test_start "API health endpoint responds"
if curl -s -f http://localhost:9999/health > /dev/null 2>&1; then
    test_pass
else
    test_fail "Health endpoint not responding"
fi

# Test 13: Health status
test_start "API reports healthy status"
HEALTH_STATUS=$(curl -s http://localhost:9999/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
if [ "$HEALTH_STATUS" = "healthy" ]; then
    test_pass
else
    test_fail "Status: $HEALTH_STATUS"
fi

# Test 14: C++ engine available
test_start "C++ engine operational"
CPP_STATUS=$(curl -s http://localhost:9999/health 2>/dev/null | grep -o '"cpp_engine_available":[^,}]*' | cut -d':' -f2)
if [ "$CPP_STATUS" = "true" ]; then
    test_pass
else
    test_fail "C++ engine not available"
fi

# Test 15: API documentation
test_start "API documentation accessible"
if curl -s -f http://localhost:9999/docs > /dev/null 2>&1; then
    test_pass
else
    test_fail "Documentation not accessible"
fi

# Test 16: OpenAPI spec
test_start "OpenAPI specification available"
if curl -s -f http://localhost:9999/openapi.json > /dev/null 2>&1; then
    test_pass
else
    test_fail "OpenAPI spec not available"
fi

# Cleanup port forward
kill $PF_PID 2>/dev/null || true
wait $PF_PID 2>/dev/null || true

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Test Suite 5: Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 17: Phase 5 data collection
test_start "Data collection enabled"
DATA_COLLECTION=$(kubectl get configmap finrisk-config -n finrisk-ai -o jsonpath='{.data.ENABLE_DATA_COLLECTION}' 2>/dev/null)
if [ "$DATA_COLLECTION" = "true" ]; then
    test_pass
else
    test_fail "Data collection not enabled"
fi

# Test 18: HPA configured
test_start "Horizontal Pod Autoscaler configured"
if kubectl get hpa finrisk-api-hpa -n finrisk-ai &> /dev/null; then
    test_pass
else
    test_fail "HPA not found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Test Suite 6: Logs"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 19: No crash loops
test_start "No pods in CrashLoopBackOff"
if ! kubectl get pods -n finrisk-ai | grep -q "CrashLoopBackOff"; then
    test_pass
else
    CRASHED=$(kubectl get pods -n finrisk-ai | grep "CrashLoopBackOff")
    test_fail "$CRASHED"
fi

# Test 20: OrchestratorV2 active
test_start "OrchestratorV2 initialized"
if kubectl logs -n finrisk-ai -l app=finrisk-api --tail=100 2>/dev/null | grep -q "OrchestratorV2"; then
    test_pass
else
    test_fail "OrchestratorV2 not found in logs"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Validation Results"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS ✅"
echo "Failed: $FAILED_TESTS ❌"
echo ""

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo "Pass rate: ${PASS_RATE}%"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo "🎉 All validation tests passed!"
    echo ""
    echo "✅ Deployment is healthy and ready for use"
    echo ""
    echo "Next steps:"
    echo "  1. Access API: kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80"
    echo "  2. Test with: curl http://localhost:8000/health"
    echo "  3. View docs: http://localhost:8000/docs"
    echo "  4. Monitor logs: kubectl logs -n finrisk-ai -l app=finrisk-api -f"
    echo ""
    EXIT_CODE=0
else
    echo ""
    echo "⚠️  Some validation tests failed"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check pod status: kubectl get pods -n finrisk-ai"
    echo "  2. View logs: kubectl logs -n finrisk-ai <pod-name>"
    echo "  3. Describe pod: kubectl describe pod -n finrisk-ai <pod-name>"
    echo "  4. Check events: kubectl get events -n finrisk-ai --sort-by='.lastTimestamp'"
    echo ""
    EXIT_CODE=1
fi

# Detailed status
echo "═══════════════════════════════════════════════════════════════"
echo "  Current Status"
echo "═══════════════════════════════════════════════════════════════"
echo ""

kubectl get all -n finrisk-ai

echo ""

# Save validation report
cat > validation-report.txt << EOF
Validation completed: $(date)
Cluster: $(kubectl config current-context)
Namespace: finrisk-ai

Test Results:
  Total: $TOTAL_TESTS
  Passed: $PASSED_TESTS
  Failed: $FAILED_TESTS
  Pass rate: ${PASS_RATE}%

Status: $([ $FAILED_TESTS -eq 0 ] && echo "HEALTHY ✅" || echo "NEEDS ATTENTION ⚠️")
EOF

echo "Validation report saved to: validation-report.txt"
echo ""

exit $EXIT_CODE
