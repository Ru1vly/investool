# Phase 4: Monitoring & Optimization Scripts

This directory contains scripts for Phase 4: Scale & Monitor (The "Business").

## Overview

Phase 4 provides production-ready tools for:
- **Performance optimization** (caching, resources, scaling)
- **Comprehensive monitoring** (dashboards, logs, alerts)
- **Business operations** (reliability, observability, cost optimization)

---

## Scripts

### 1. Activate Production Caching
**File:** `1-activate-caching.sh`

**Purpose:** Enable and optimize Redis caching for production performance

**Prerequisites:**
- kubectl configured with cluster access
- Redis pod running in Kubernetes
- Phase 2 deployed

**Usage:**
```bash
# Interactive mode (recommended)
./1-activate-caching.sh

# Custom configuration
CACHE_TTL=7200 CACHE_MAX_SIZE=2000 ./1-activate-caching.sh
```

**Configuration:**
- `CACHE_TTL`: Cache time-to-live in seconds (default: 3600 = 1 hour)
- `CACHE_MAX_SIZE`: Maximum cached items (default: 1000)
- `NAMESPACE`: Kubernetes namespace (default: finrisk-ai)

**Actions:**
- Updates ConfigMap with caching settings
- Configures Redis (LRU eviction, 1GB memory, persistence)
- Tests Redis connectivity
- Restarts API pods
- Validates caching is active

**Time:** 2-3 minutes

---

### 2. Benchmark Performance
**File:** `2-benchmark-performance.sh`

**Purpose:** Comprehensive performance testing and reporting

**Prerequisites:**
- kubectl configured
- API deployed and accessible
- curl installed
- Optional: ab (Apache Bench) for advanced testing

**Usage:**
```bash
# Default benchmarks
./2-benchmark-performance.sh

# Custom load test
CONCURRENT_USERS=20 REQUESTS_PER_USER=50 \
BENCHMARK_DURATION=120 \
./2-benchmark-performance.sh
```

**Configuration:**
- `CONCURRENT_USERS`: Number of concurrent users (default: 10)
- `REQUESTS_PER_USER`: Requests per user (default: 20)
- `BENCHMARK_DURATION`: Test duration (default: 60s)
- `OUTPUT_DIR`: Report directory (default: ./benchmark_results)

**Tests Performed:**
1. **Health Check Performance** (100 requests)
   - Average latency
   - Success rate

2. **Cache Performance** (same query twice)
   - First request (cache miss)
   - Second request (cache hit)
   - Speedup percentage

3. **Concurrent Users** (load test)
   - Total requests
   - Duration
   - Throughput (req/s)

4. **Resource Usage**
   - Pod CPU/memory
   - Current utilization

5. **Redis Cache Statistics**
   - Keyspace hits/misses
   - Hit rate percentage
   - Memory usage

6. **Apache Bench** (if installed)
   - Advanced load testing
   - Percentile latencies

**Output:**
- `benchmark_results/benchmark_YYYYMMDD_HHMMSS.txt`

**Interpretation:**
```
Good Performance:
  • Health check: < 100ms
  • Cache speedup: > 50%
  • Throughput: > 10 req/s
  • Cache hit rate: > 50%

Needs Attention:
  • Health check: > 200ms
  • Cache speedup: < 20%
  • Throughput: < 5 req/s
  • Cache hit rate: < 30%
```

**Time:** 2-5 minutes

---

### 3. Optimize Resources
**File:** `3-optimize-resources.sh`

**Purpose:** Analyze and optimize Kubernetes resource allocation

**Prerequisites:**
- kubectl configured
- metrics-server installed (optional but recommended)

**Usage:**
```bash
# Interactive mode (prompts for each optimization)
./3-optimize-resources.sh
```

**Features:**

1. **Resource Analysis:**
   - Current pod resource usage
   - Deployment resource requests/limits
   - HPA status

2. **API Optimization:**
   - Adjust CPU/memory requests
   - Adjust CPU/memory limits
   - Recommendations based on workload

3. **HPA Configuration:**
   - Min/max replicas
   - Target CPU utilization
   - Create HPA if not exists

4. **Database Optimization:**
   - PostgreSQL resources
   - Redis resources
   - Neo4j resources

5. **Pod Distribution:**
   - View pods across nodes
   - Node resource availability

**Resource Recommendations:**
```
API Pod Sizing:
  Light:  250m CPU, 512Mi memory
  Medium: 500m CPU, 1Gi memory
  Heavy:  1000m CPU, 2Gi memory

HPA Settings:
  Development: 1-3 replicas, 80% target
  Staging:     2-5 replicas, 75% target
  Production:  3-10 replicas, 70% target

Database Sizing:
  PostgreSQL: 250m-500m CPU, 512Mi-1Gi memory
  Redis:      100m-250m CPU, 256Mi-512Mi memory
  Neo4j:      250m-500m CPU, 512Mi-1Gi memory
```

**Monitoring After Changes:**
```bash
# Watch HPA
kubectl get hpa -n finrisk-ai -w

# Monitor resources
watch kubectl top pods -n finrisk-ai

# Check for issues
kubectl describe pods -n finrisk-ai
```

**Time:** 3-5 minutes

---

### 4. Setup Monitoring
**File:** `4-setup-monitoring.sh`

**Purpose:** Configure comprehensive monitoring and alerting

**Prerequisites:**
- kubectl configured
- Optional: Prometheus Operator for ServiceMonitor

**Usage:**
```bash
# Setup all monitoring tools
./4-setup-monitoring.sh
```

**Creates:**

1. **Monitoring Namespace**
   - Separate namespace for monitoring tools

2. **Prometheus ServiceMonitor**
   - Scrapes metrics from API pods
   - Requires Prometheus Operator

3. **Live Dashboard** (`monitor-dashboard.sh`)
   - Real-time monitoring
   - Refreshes every 2 seconds
   - Shows: Pods, resources, HPA, events

4. **Log Viewer** (`view-logs.sh`)
   - Aggregate logs from components
   - Filter by component (api, postgres, redis, neo4j, all)

5. **Alert Checker** (`check-alerts.sh`)
   - Automated health checks
   - Detects common issues
   - Exit codes for automation

6. **Optional: Automated Health Check**
   - CronJob running every 5 minutes
   - Checks system health
   - Can integrate with alerting

**Time:** 5-10 minutes

---

## Helper Scripts

### monitor-dashboard.sh
**Created by:** `4-setup-monitoring.sh`

**Purpose:** Live monitoring dashboard

**Usage:**
```bash
./monitor-dashboard.sh [namespace]
```

**Shows:**
- Pod status (name, phase, node)
- Resource usage (CPU, memory)
- HPA status (current, desired, min, max)
- Recent events

**Updates:** Every 2 seconds

**Exit:** Press Ctrl+C

---

### view-logs.sh
**Created by:** `4-setup-monitoring.sh`

**Purpose:** Aggregate and view logs

**Usage:**
```bash
./view-logs.sh [namespace] [component]

# Examples:
./view-logs.sh finrisk-ai api        # API logs
./view-logs.sh finrisk-ai postgres   # PostgreSQL logs
./view-logs.sh finrisk-ai redis      # Redis logs
./view-logs.sh finrisk-ai neo4j      # Neo4j logs
./view-logs.sh finrisk-ai all        # All components
```

**Options:**
- `namespace`: Kubernetes namespace (default: finrisk-ai)
- `component`: Component to view (default: all)

**Features:**
- Follows logs in real-time (-f)
- Shows last 100 lines by default
- All containers included

---

### check-alerts.sh
**Created by:** `4-setup-monitoring.sh`

**Purpose:** Check for common alert conditions

**Usage:**
```bash
./check-alerts.sh [namespace]
```

**Checks:**
1. **Pod Status** - Pods not running
2. **CrashLoopBackOff** - Crash loop detection
3. **Resource Usage** - High CPU/memory (> 80%)
4. **Error Rate** - Recent errors in logs
5. **Redis Health** - Redis connectivity

**Exit Codes:**
- `0`: All checks passed
- `1`: One or more alerts detected

**Integration:**
```bash
# Run in cron
*/5 * * * * /path/to/check-alerts.sh && echo "OK" || send_alert.sh

# Run before deployment
./check-alerts.sh || { echo "System unhealthy"; exit 1; }
```

---

## Workflow

### Initial Setup (One-time)

```bash
cd investool/scripts/monitoring

# 1. Activate caching
./1-activate-caching.sh

# 2. Benchmark baseline
./2-benchmark-performance.sh
cat ../../benchmark_results/benchmark_*.txt

# 3. Optimize resources
./3-optimize-resources.sh

# 4. Setup monitoring
./4-setup-monitoring.sh
```

**Total time:** 15-25 minutes

---

### Daily Operations

**Morning Check:**
```bash
# Check for alerts
./check-alerts.sh

# Quick health view
kubectl get all -n finrisk-ai
```

**During Business Hours:**
```bash
# Keep dashboard open
./monitor-dashboard.sh
```

**Troubleshooting:**
```bash
# View API logs
./view-logs.sh finrisk-ai api

# Check specific pod
kubectl describe pod <pod-name> -n finrisk-ai
```

---

### Weekly Tasks

**Performance Review:**
```bash
# Run benchmarks
./2-benchmark-performance.sh

# Compare with previous results
diff benchmark_results/benchmark_LAST_WEEK.txt \
     benchmark_results/benchmark_THIS_WEEK.txt
```

**Resource Review:**
```bash
# Check trends
kubectl top pods -n finrisk-ai
kubectl top nodes

# Review HPA behavior
kubectl describe hpa finrisk-api-hpa -n finrisk-ai
```

**Cache Review:**
```bash
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli INFO stats

# Target: > 50% hit rate
```

---

## Environment Variables

All scripts support these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NAMESPACE` | `finrisk-ai` | Kubernetes namespace |
| `CACHE_TTL` | `3600` | Cache TTL in seconds (1 hour) |
| `CACHE_MAX_SIZE` | `1000` | Max cached items |
| `CONCURRENT_USERS` | `10` | Benchmark concurrent users |
| `REQUESTS_PER_USER` | `20` | Requests per user in benchmark |
| `BENCHMARK_DURATION` | `60` | Benchmark duration (seconds) |
| `OUTPUT_DIR` | `./benchmark_results` | Benchmark output directory |
| `MONITORING_NAMESPACE` | `monitoring` | Monitoring tools namespace |

**Example:**
```bash
NAMESPACE=finrisk-prod \
CACHE_TTL=7200 \
./1-activate-caching.sh
```

---

## Monitoring Metrics

### Key Metrics to Track

**Performance:**
- API latency (p50, p95, p99)
- Throughput (requests/second)
- Error rate (errors/minute)
- Cache hit rate (%)

**Resources:**
- CPU utilization (%)
- Memory utilization (%)
- Pod count
- HPA scaling events

**Business:**
- Active users
- API calls per user
- Data collection rate
- Fine-tuning usage (Phase 3)

### Prometheus Queries

If Prometheus is installed:

```promql
# API request rate
rate(http_requests_total[5m])

# API latency (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Cache hit rate
rate(redis_keyspace_hits_total[5m]) /
(rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))

# Pod CPU usage
container_cpu_usage_seconds_total{namespace="finrisk-ai"}

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```

---

## Troubleshooting

### Issue: Script Won't Run

**Solution:**
```bash
# Make executable
chmod +x scripts/monitoring/*.sh

# Check permissions
ls -la scripts/monitoring/
```

### Issue: kubectl Not Found

**Solution:**
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

### Issue: Metrics Not Available

**Symptoms:**
```
⚠️  Metrics not available (metrics-server may not be installed)
```

**Solution:**
```bash
# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify
kubectl get deployment metrics-server -n kube-system

# Wait a minute, then test
kubectl top nodes
kubectl top pods -n finrisk-ai
```

### Issue: Port Forward Fails

**Symptoms:**
```
error: unable to forward port because pod is not running
```

**Solution:**
```bash
# Check pod status
kubectl get pods -n finrisk-ai

# If pod not running, check logs
kubectl describe pod <pod-name> -n finrisk-ai
kubectl logs <pod-name> -n finrisk-ai

# Restart if needed
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

### Issue: Redis Commands Fail

**Solution:**
```bash
# Check Redis pod
kubectl get pods -n finrisk-ai -l app=redis

# Test connectivity
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli PING

# Check logs if failing
kubectl logs -n finrisk-ai $REDIS_POD
```

---

## Integration Examples

### Slack Notifications

Add to `check-alerts.sh`:
```bash
# At end of script
if [ $ALERTS -gt 0 ]; then
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
      -H 'Content-Type: application/json' \
      -d "{\"text\":\"🚨 FinRisk AI: $ALERTS alerts detected\"}"
fi
```

### PagerDuty Integration

```bash
# Create incident on critical alerts
if [ $ALERTS -gt 2 ]; then
    curl -X POST https://api.pagerduty.com/incidents \
      -H "Authorization: Token token=YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "incident": {
          "type": "incident",
          "title": "FinRisk AI: Critical alerts",
          "service": {"id": "YOUR_SERVICE_ID", "type": "service_reference"},
          "urgency": "high"
        }
      }'
fi
```

### Grafana Dashboard

Import metrics with ServiceMonitor, then create dashboard with:
- API request rate
- Latency percentiles
- Error rate
- Cache hit rate
- Pod resource usage
- HPA scaling

---

## Best Practices

1. **Run check-alerts.sh regularly**
   - Every 5 minutes via cron
   - Before deployments
   - After configuration changes

2. **Benchmark weekly**
   - Compare trends
   - Identify performance degradation early
   - Document baselines

3. **Review resources monthly**
   - Right-size pods
   - Adjust HPA settings
   - Plan capacity

4. **Monitor cache effectiveness**
   - Target: > 50% hit rate
   - Adjust TTL based on data freshness needs
   - Balance performance vs freshness

5. **Keep historical data**
   - Save benchmark reports
   - Track metrics over time
   - Support capacity planning

---

## Support

For detailed documentation: `PHASE4_GUIDE.md`

For issues:
1. Check script output for error messages
2. Verify prerequisites are met
3. Review troubleshooting section
4. Check pod logs: `kubectl logs -n finrisk-ai <pod>`

---

**Status:** ✅ All scripts production-ready
**Last Updated:** 2025-11-13
**Phase:** 4 - Scale & Monitor (The "Business")
