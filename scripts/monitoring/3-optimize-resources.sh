#!/bin/bash
# ============================================================================
# Phase 4.3: Resource Optimization
#
# Analyzes current resource usage and adjusts HPA, resource limits, and
# scaling parameters for optimal performance.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 4.3: Resource Optimization                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Configuration
# ============================================================================

NAMESPACE="${NAMESPACE:-finrisk-ai}"

# ============================================================================
# Check Prerequisites
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Checking Prerequisites"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    exit 1
fi
echo "✅ kubectl found"

if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to cluster"
    exit 1
fi
echo "✅ Connected to cluster"

echo ""

# ============================================================================
# Analyze Current Resource Usage
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Current Resource Usage"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Pod resource usage:"
kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "⚠️  Metrics not available (install metrics-server)"

echo ""
echo "Current deployments:"
kubectl get deployments -n "$NAMESPACE" -o custom-columns=NAME:.metadata.name,REPLICAS:.spec.replicas,READY:.status.readyReplicas,CPU-REQ:.spec.template.spec.containers[0].resources.requests.cpu,MEM-REQ:.spec.template.spec.containers[0].resources.requests.memory

echo ""
echo "HPA status:"
kubectl get hpa -n "$NAMESPACE" 2>/dev/null || echo "No HPA configured"

echo ""

# ============================================================================
# Optimize API Deployment
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Optimize API Deployment"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Current API configuration:"
kubectl get deployment finrisk-api -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' | xargs -I {} echo "  • Replicas: {}"
kubectl get deployment finrisk-api -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].resources.requests.cpu}' | xargs -I {} echo "  • CPU request: {}"
kubectl get deployment finrisk-api -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}' | xargs -I {} echo "  • Memory request: {}"
kubectl get deployment finrisk-api -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].resources.limits.cpu}' | xargs -I {} echo "  • CPU limit: {}"
kubectl get deployment finrisk-api -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}' | xargs -I {} echo "  • Memory limit: {}"

echo ""
read -p "Adjust API resources? (y/n) [n]: " ADJUST_API
ADJUST_API=${ADJUST_API:-n}

if [ "$ADJUST_API" = "y" ]; then
    echo ""
    echo "Recommended values based on workload:"
    echo "  • Light: 250m CPU, 512Mi memory"
    echo "  • Medium: 500m CPU, 1Gi memory"
    echo "  • Heavy: 1000m CPU, 2Gi memory"
    echo ""

    read -p "CPU request (e.g., 500m) [500m]: " CPU_REQ
    CPU_REQ=${CPU_REQ:-500m}

    read -p "Memory request (e.g., 1Gi) [1Gi]: " MEM_REQ
    MEM_REQ=${MEM_REQ:-1Gi}

    read -p "CPU limit (e.g., 1000m) [1000m]: " CPU_LIMIT
    CPU_LIMIT=${CPU_LIMIT:-1000m}

    read -p "Memory limit (e.g., 2Gi) [2Gi]: " MEM_LIMIT
    MEM_LIMIT=${MEM_LIMIT:-2Gi}

    echo ""
    echo "Updating API deployment..."

    kubectl patch deployment finrisk-api -n "$NAMESPACE" --type='json' -p="[
        {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/requests/cpu\",\"value\":\"$CPU_REQ\"},
        {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/requests/memory\",\"value\":\"$MEM_REQ\"},
        {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/limits/cpu\",\"value\":\"$CPU_LIMIT\"},
        {\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/resources/limits/memory\",\"value\":\"$MEM_LIMIT\"}
    ]"

    echo "✅ API resources updated"
    echo ""
fi

# ============================================================================
# Optimize HPA
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Optimize HPA (Horizontal Pod Autoscaler)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

HPA_EXISTS=$(kubectl get hpa finrisk-api-hpa -n "$NAMESPACE" 2>/dev/null && echo "yes" || echo "no")

if [ "$HPA_EXISTS" = "yes" ]; then
    echo "Current HPA configuration:"
    kubectl get hpa finrisk-api-hpa -n "$NAMESPACE" -o jsonpath='{.spec.minReplicas}' | xargs -I {} echo "  • Min replicas: {}"
    kubectl get hpa finrisk-api-hpa -n "$NAMESPACE" -o jsonpath='{.spec.maxReplicas}' | xargs -I {} echo "  • Max replicas: {}"
    kubectl get hpa finrisk-api-hpa -n "$NAMESPACE" -o jsonpath='{.spec.targetCPUUtilizationPercentage}' | xargs -I {} echo "  • Target CPU: {}%"

    echo ""
    read -p "Adjust HPA settings? (y/n) [n]: " ADJUST_HPA
    ADJUST_HPA=${ADJUST_HPA:-n}

    if [ "$ADJUST_HPA" = "y" ]; then
        echo ""
        read -p "Min replicas [2]: " MIN_REPLICAS
        MIN_REPLICAS=${MIN_REPLICAS:-2}

        read -p "Max replicas [10]: " MAX_REPLICAS
        MAX_REPLICAS=${MAX_REPLICAS:-10}

        read -p "Target CPU utilization % [70]: " TARGET_CPU
        TARGET_CPU=${TARGET_CPU:-70}

        echo ""
        echo "Updating HPA..."

        kubectl patch hpa finrisk-api-hpa -n "$NAMESPACE" --type='json' -p="[
            {\"op\":\"replace\",\"path\":\"/spec/minReplicas\",\"value\":$MIN_REPLICAS},
            {\"op\":\"replace\",\"path\":\"/spec/maxReplicas\",\"value\":$MAX_REPLICAS},
            {\"op\":\"replace\",\"path\":\"/spec/targetCPUUtilizationPercentage\",\"value\":$TARGET_CPU}
        ]"

        echo "✅ HPA updated"
        echo ""
    fi
else
    echo "HPA not found. Creating new HPA..."
    echo ""

    read -p "Create HPA? (y/n) [y]: " CREATE_HPA
    CREATE_HPA=${CREATE_HPA:-y}

    if [ "$CREATE_HPA" = "y" ]; then
        kubectl autoscale deployment finrisk-api -n "$NAMESPACE" \
            --min=2 --max=10 --cpu-percent=70

        echo "✅ HPA created"
        echo ""
    fi
fi

# ============================================================================
# Optimize Database Resources
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Optimize Database Resources"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "PostgreSQL:"
kubectl get deployment postgres -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].resources}' 2>/dev/null | grep -q "." && echo "  ✅ Resources configured" || echo "  ⚠️  No resource limits set"

echo ""
echo "Redis:"
kubectl get deployment redis -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].resources}' 2>/dev/null | grep -q "." && echo "  ✅ Resources configured" || echo "  ⚠️  No resource limits set"

echo ""
echo "Neo4j:"
kubectl get deployment neo4j -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].resources}' 2>/dev/null | grep -q "." && echo "  ✅ Resources configured" || echo "  ⚠️  No resource limits set"

echo ""
read -p "Optimize database resources? (y/n) [n]: " OPTIMIZE_DB
OPTIMIZE_DB=${OPTIMIZE_DB:-n}

if [ "$OPTIMIZE_DB" = "y" ]; then
    echo ""
    echo "Applying standard database resource limits..."

    # PostgreSQL
    kubectl patch deployment postgres -n "$NAMESPACE" --type='json' -p='[
        {"op":"add","path":"/spec/template/spec/containers/0/resources","value":{
            "requests":{"cpu":"250m","memory":"512Mi"},
            "limits":{"cpu":"500m","memory":"1Gi"}
        }}
    ]' 2>/dev/null && echo "✅ PostgreSQL optimized" || echo "⚠️  PostgreSQL optimization failed"

    # Redis
    kubectl patch deployment redis -n "$NAMESPACE" --type='json' -p='[
        {"op":"add","path":"/spec/template/spec/containers/0/resources","value":{
            "requests":{"cpu":"100m","memory":"256Mi"},
            "limits":{"cpu":"250m","memory":"512Mi"}
        }}
    ]' 2>/dev/null && echo "✅ Redis optimized" || echo "⚠️  Redis optimization failed"

    # Neo4j
    kubectl patch deployment neo4j -n "$NAMESPACE" --type='json' -p='[
        {"op":"add","path":"/spec/template/spec/containers/0/resources","value":{
            "requests":{"cpu":"250m","memory":"512Mi"},
            "limits":{"cpu":"500m","memory":"1Gi"}
        }}
    ]' 2>/dev/null && echo "✅ Neo4j optimized" || echo "⚠️  Neo4j optimization failed"

    echo ""
fi

# ============================================================================
# Node Affinity & Pod Distribution
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Pod Distribution"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Current pod distribution across nodes:"
kubectl get pods -n "$NAMESPACE" -o wide | awk 'NR==1{print $1,$7} NR>1{print $1,$7}' | column -t

echo ""
echo "Node resource availability:"
kubectl top nodes 2>/dev/null || echo "⚠️  Node metrics not available"

echo ""

# ============================================================================
# Summary & Recommendations
# ============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Resource Optimization Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Current configuration:"
echo ""
echo "API:"
kubectl get deployment finrisk-api -n "$NAMESPACE" -o jsonpath='  • Replicas: {.spec.replicas}{"\n"}  • CPU: {.spec.template.spec.containers[0].resources.requests.cpu} / {.spec.template.spec.containers[0].resources.limits.cpu}{"\n"}  • Memory: {.spec.template.spec.containers[0].resources.requests.memory} / {.spec.template.spec.containers[0].resources.limits.memory}{"\n"}'

echo ""
if [ "$HPA_EXISTS" = "yes" ] || [ "$CREATE_HPA" = "y" ]; then
    echo "HPA:"
    kubectl get hpa finrisk-api-hpa -n "$NAMESPACE" -o jsonpath='  • Min/Max: {.spec.minReplicas}-{.spec.maxReplicas} replicas{"\n"}  • Target CPU: {.spec.targetCPUUtilizationPercentage}%{"\n"}'
fi

echo ""
echo "Recommendations:"
echo "  1. Monitor resource usage after changes"
echo "  2. Adjust HPA thresholds based on traffic patterns"
echo "  3. Consider node auto-scaling for large workloads"
echo "  4. Review logs for OOM kills or CPU throttling"
echo ""
echo "Monitor resources:"
echo "  kubectl top pods -n $NAMESPACE"
echo "  kubectl top nodes"
echo "  kubectl get hpa -n $NAMESPACE -w"
echo ""
echo "Next steps:"
echo "  1. Run benchmarks: ./scripts/monitoring/2-benchmark-performance.sh"
echo "  2. Setup monitoring: ./scripts/monitoring/4-setup-monitoring.sh"
echo ""
