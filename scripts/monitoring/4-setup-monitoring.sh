#!/bin/bash
# ============================================================================
# Phase 4.4: Setup Monitoring & Alerting
#
# Sets up comprehensive monitoring for the FinRisk AI system including
# Prometheus metrics, logs aggregation, and basic alerting.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 4.4: Setup Monitoring & Alerting                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Configuration
# ============================================================================

NAMESPACE="${NAMESPACE:-finrisk-ai}"
MONITORING_NAMESPACE="${MONITORING_NAMESPACE:-monitoring}"

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
# Create Monitoring Namespace
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Setup Monitoring Namespace"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if kubectl get namespace "$MONITORING_NAMESPACE" &> /dev/null; then
    echo "✅ Monitoring namespace already exists"
else
    echo "Creating monitoring namespace..."
    kubectl create namespace "$MONITORING_NAMESPACE"
    echo "✅ Monitoring namespace created"
fi

echo ""

# ============================================================================
# Create ServiceMonitor for API
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Configure Prometheus ServiceMonitor"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Note: This requires Prometheus Operator to be installed."
echo "If you don't have Prometheus Operator, you can install it with Helm:"
echo "  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts"
echo "  helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring"
echo ""

read -p "Create ServiceMonitor? (y/n) [y]: " CREATE_SM
CREATE_SM=${CREATE_SM:-y}

if [ "$CREATE_SM" = "y" ]; then
    cat > /tmp/servicemonitor.yaml << 'EOF'
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: finrisk-api-monitor
  namespace: finrisk-ai
  labels:
    app: finrisk-ai
    release: prometheus
spec:
  selector:
    matchLabels:
      app: finrisk-api
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
EOF

    kubectl apply -f /tmp/servicemonitor.yaml 2>/dev/null && echo "✅ ServiceMonitor created" || echo "⚠️  ServiceMonitor creation failed (Prometheus Operator may not be installed)"
    rm /tmp/servicemonitor.yaml
fi

echo ""

# ============================================================================
# Create Basic Monitoring Dashboard Script
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Create Monitoring Dashboard"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cat > /tmp/monitor-dashboard.sh << 'SCRIPT'
#!/bin/bash
# Live monitoring dashboard for FinRisk AI

NAMESPACE="${1:-finrisk-ai}"

watch -n 2 "
echo '╔═══════════════════════════════════════════════════════════════╗'
echo '║         FinRisk AI - Live Monitoring Dashboard               ║'
echo '╚═══════════════════════════════════════════════════════════════╝'
echo ''
echo '═══ Pod Status ═══'
kubectl get pods -n $NAMESPACE -o wide | tail -n +2 | awk '{printf \"%-30s %-12s %s\\n\", \$1, \$3, \$7}'
echo ''
echo '═══ Resource Usage ═══'
kubectl top pods -n $NAMESPACE 2>/dev/null || echo 'Metrics not available'
echo ''
echo '═══ HPA Status ═══'
kubectl get hpa -n $NAMESPACE 2>/dev/null || echo 'No HPA configured'
echo ''
echo '═══ Recent Events ═══'
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -5
echo ''
echo 'Press Ctrl+C to exit'
"
SCRIPT

chmod +x /tmp/monitor-dashboard.sh
cp /tmp/monitor-dashboard.sh scripts/monitoring/monitor-dashboard.sh

echo "✅ Monitoring dashboard created: scripts/monitoring/monitor-dashboard.sh"
echo "   Run with: ./scripts/monitoring/monitor-dashboard.sh"
echo ""

# ============================================================================
# Create Log Aggregation Commands
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Setup Log Aggregation"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cat > scripts/monitoring/view-logs.sh << 'SCRIPT'
#!/bin/bash
# Aggregate and view logs from all FinRisk AI components

NAMESPACE="${1:-finrisk-ai}"
COMPONENT="${2:-all}"

case "$COMPONENT" in
    api)
        kubectl logs -n "$NAMESPACE" -l app=finrisk-api --tail=100 -f
        ;;
    postgres)
        kubectl logs -n "$NAMESPACE" -l app=postgres --tail=100 -f
        ;;
    redis)
        kubectl logs -n "$NAMESPACE" -l app=redis --tail=100 -f
        ;;
    neo4j)
        kubectl logs -n "$NAMESPACE" -l app=neo4j --tail=100 -f
        ;;
    all)
        echo "Showing logs from all components..."
        kubectl logs -n "$NAMESPACE" --all-containers=true --tail=50 -f
        ;;
    *)
        echo "Usage: $0 [namespace] [component]"
        echo "Components: api, postgres, redis, neo4j, all"
        exit 1
        ;;
esac
SCRIPT

chmod +x scripts/monitoring/view-logs.sh

echo "✅ Log viewer created: scripts/monitoring/view-logs.sh"
echo "   Usage: ./scripts/monitoring/view-logs.sh [namespace] [component]"
echo ""

# ============================================================================
# Create Alerting Rules (Simple)
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Create Alert Checking Script"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cat > scripts/monitoring/check-alerts.sh << 'SCRIPT'
#!/bin/bash
# Check for common alert conditions

NAMESPACE="${1:-finrisk-ai}"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║             FinRisk AI - Alert Checker                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

ALERTS=0

# Check for pods not running
echo "Checking pod status..."
NOT_RUNNING=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
if [ "$NOT_RUNNING" -gt 0 ]; then
    echo "🚨 ALERT: $NOT_RUNNING pods not in Running state"
    kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running
    ALERTS=$((ALERTS + 1))
else
    echo "✅ All pods running"
fi
echo ""

# Check for crashlooping pods
echo "Checking for CrashLoopBackOff..."
CRASH_LOOPS=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[?(@.status.containerStatuses[*].state.waiting.reason=="CrashLoopBackOff")].metadata.name}' 2>/dev/null)
if [ ! -z "$CRASH_LOOPS" ]; then
    echo "🚨 ALERT: CrashLoopBackOff detected: $CRASH_LOOPS"
    ALERTS=$((ALERTS + 1))
else
    echo "✅ No crash loops"
fi
echo ""

# Check resource usage (if metrics available)
echo "Checking resource usage..."
if kubectl top pods -n "$NAMESPACE" &>/dev/null; then
    HIGH_CPU=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '{if($2 ~ /[0-9]+m/ && $2+0 > 800) print $1}')
    if [ ! -z "$HIGH_CPU" ]; then
        echo "⚠️  WARNING: High CPU usage on: $HIGH_CPU"
        ALERTS=$((ALERTS + 1))
    else
        echo "✅ CPU usage normal"
    fi
else
    echo "⚠️  Metrics not available"
fi
echo ""

# Check for recent errors in logs
echo "Checking for recent errors..."
ERROR_COUNT=$(kubectl logs -n "$NAMESPACE" -l app=finrisk-api --tail=100 --since=5m 2>/dev/null | grep -i "error\|exception\|fatal" | wc -l)
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "⚠️  WARNING: $ERROR_COUNT errors in last 5 minutes"
    ALERTS=$((ALERTS + 1))
else
    echo "✅ Error rate normal ($ERROR_COUNT errors)"
fi
echo ""

# Check Redis connectivity
echo "Checking Redis..."
REDIS_POD=$(kubectl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ ! -z "$REDIS_POD" ]; then
    if kubectl exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli PING 2>/dev/null | grep -q PONG; then
        echo "✅ Redis responding"
    else
        echo "🚨 ALERT: Redis not responding"
        ALERTS=$((ALERTS + 1))
    fi
else
    echo "⚠️  Redis pod not found"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
if [ $ALERTS -eq 0 ]; then
    echo "✅ All checks passed - System healthy"
else
    echo "🚨 $ALERTS alerts detected - Review above"
fi
echo "═══════════════════════════════════════════════════════════════"
SCRIPT

chmod +x scripts/monitoring/check-alerts.sh

echo "✅ Alert checker created: scripts/monitoring/check-alerts.sh"
echo ""

# ============================================================================
# Create Monitoring Cron Job
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Setup Automated Monitoring"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cat > /tmp/monitoring-cronjob.yaml << 'EOF'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: finrisk-health-check
  namespace: finrisk-ai
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: default
          containers:
          - name: health-checker
            image: bitnami/kubectl:latest
            command:
            - /bin/bash
            - -c
            - |
              echo "Running health check..."
              kubectl get pods -n finrisk-ai
              # Add your health check logic here
          restartPolicy: OnFailure
EOF

read -p "Create automated health check CronJob? (y/n) [n]: " CREATE_CRON
CREATE_CRON=${CREATE_CRON:-n}

if [ "$CREATE_CRON" = "y" ]; then
    kubectl apply -f /tmp/monitoring-cronjob.yaml 2>/dev/null && echo "✅ Health check CronJob created" || echo "⚠️  CronJob creation failed"
fi

rm /tmp/monitoring-cronjob.yaml

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Monitoring Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Available monitoring tools:"
echo ""
echo "  1. Live Dashboard:"
echo "     ./scripts/monitoring/monitor-dashboard.sh"
echo ""
echo "  2. View Logs:"
echo "     ./scripts/monitoring/view-logs.sh [namespace] [component]"
echo "     Components: api, postgres, redis, neo4j, all"
echo ""
echo "  3. Check Alerts:"
echo "     ./scripts/monitoring/check-alerts.sh"
echo ""
echo "  4. Manual checks:"
echo "     kubectl get all -n $NAMESPACE"
echo "     kubectl top pods -n $NAMESPACE"
echo "     kubectl logs -n $NAMESPACE -l app=finrisk-api -f"
echo ""

if [ "$CREATE_SM" = "y" ]; then
    echo "  5. Prometheus (if installed):"
    echo "     kubectl port-forward -n $MONITORING_NAMESPACE svc/prometheus-kube-prometheus-prometheus 9090:9090"
    echo "     Visit: http://localhost:9090"
    echo ""
fi

echo "Recommendations:"
echo "  • Run check-alerts.sh regularly (or via cron)"
echo "  • Setup external alerting (PagerDuty, Slack, etc.)"
echo "  • Configure log forwarding (ELK, Loki, etc.)"
echo "  • Monitor business metrics (API latency, cache hit rate)"
echo ""
echo "Next steps:"
echo "  • Review all Phase 4 scripts"
echo "  • Setup custom alerting based on your needs"
echo "  • Integrate with your existing monitoring stack"
echo ""
