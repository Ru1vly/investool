# Phase 4: Scale & Monitor (The "Business")

**Goal:** Production optimization, monitoring, and business-ready operations

**Status:** Scripts ready - Execute after Phase 2 deployment

**Date:** 2025-11-13

---

## Overview

Phase 4 transforms the FinRisk AI system from a deployed application to a production-grade, business-ready platform with:

1. **Production caching** (Redis optimization)
2. **Performance benchmarking** (comprehensive testing)
3. **Resource optimization** (HPA, limits, scaling)
4. **Monitoring & alerting** (observability)

---

## Architecture Enhancements

### Before Phase 4
```
User → API → AI Processing → Response
       ↓
  (No caching, basic resources, minimal monitoring)
```

### After Phase 4
```
User → API → Cache Check:
              ├─ HIT → Fast Response (< 50ms)
              └─ MISS → AI Processing → Cache Store → Response
       ↓
  Monitoring: Prometheus, Logs, Alerts
  Scaling: HPA (2-10 replicas based on load)
  Resources: Optimized limits & requests
```

---

## Phase 4 Workflow

### Step 1: Activate Production Caching

**When:** After Phase 2 deployment is validated

**Script:** `./scripts/monitoring/1-activate-caching.sh`

**What it does:**
- Enables Redis caching in ConfigMap
- Configures cache TTL (default: 1 hour)
- Sets eviction policy (LRU - Least Recently Used)
- Optimizes Redis memory (1GB max)
- Restarts API pods
- Validates caching is active

**Configuration:**
- **Cache TTL:** 3600 seconds (1 hour) - adjust based on data freshness needs
- **Max items:** 1000 - adjust based on memory
- **Strategy:** LRU (Least Recently Used)
- **Redis memory:** 1GB

**Usage:**
```bash
# Interactive mode (recommended)
./scripts/monitoring/1-activate-caching.sh

# Custom configuration
CACHE_TTL=7200 CACHE_MAX_SIZE=2000 \
./scripts/monitoring/1-activate-caching.sh
```

**Validation:**
```bash
# Check Redis stats
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli INFO stats

# Monitor cache hit rate
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli INFO stats | grep keyspace
```

**Expected results:**
- Cache enabled in ConfigMap
- Redis responding with PONG
- API logs show "Caching initialized"
- First duplicate request much faster than initial

**Time:** 2-3 minutes

---

### Step 2: Benchmark Performance

**When:** After caching is activated

**Script:** `./scripts/monitoring/2-benchmark-performance.sh`

**What it does:**
- Tests health endpoint latency (100 requests)
- Measures cache performance (same query twice)
- Simulates concurrent users (default: 10 users, 20 requests each)
- Analyzes resource usage
- Calculates Redis cache hit rate
- Optional: Apache Bench load testing
- Generates comprehensive report

**Usage:**
```bash
# Default benchmarks
./scripts/monitoring/2-benchmark-performance.sh

# Custom configuration
CONCURRENT_USERS=20 REQUESTS_PER_USER=50 BENCHMARK_DURATION=120 \
./scripts/monitoring/2-benchmark-performance.sh
```

**Output:**
- `benchmark_results/benchmark_YYYYMMDD_HHMMSS.txt` - Full report

**Key metrics:**
- **Health check latency:** < 100ms (good), < 50ms (excellent)
- **Cache speedup:** 50-90% faster on cache hits
- **Throughput:** > 5 req/s (acceptable), > 20 req/s (good)
- **Cache hit rate:** > 50% (good), > 80% (excellent)

**Interpretation:**
```
Good performance:
  • Health check: < 100ms
  • Cache hit rate: > 50%
  • Throughput: > 10 req/s
  • No errors or timeouts

Needs optimization:
  • Health check: > 200ms → Check API logs
  • Cache hit rate: < 30% → Increase TTL
  • Throughput: < 5 req/s → Scale replicas
```

**Time:** 2-5 minutes

---

### Step 3: Optimize Resources

**When:** After benchmarking identifies bottlenecks

**Script:** `./scripts/monitoring/3-optimize-resources.sh`

**What it does:**
- Analyzes current resource usage
- Adjusts API pod resources (CPU/memory)
- Configures HPA (Horizontal Pod Autoscaler)
- Optimizes database resources
- Reviews pod distribution across nodes

**Interactive Configuration:**

**API Resources:**
- Light workload: 250m CPU, 512Mi memory
- Medium workload: 500m CPU, 1Gi memory
- Heavy workload: 1000m CPU, 2Gi memory

**HPA Settings:**
- Min replicas: 2 (always have 2 pods)
- Max replicas: 10 (scale up to 10 under load)
- Target CPU: 70% (scale when CPU > 70%)

**Database Resources:**
- PostgreSQL: 250m-500m CPU, 512Mi-1Gi memory
- Redis: 100m-250m CPU, 256Mi-512Mi memory
- Neo4j: 250m-500m CPU, 512Mi-1Gi memory

**Usage:**
```bash
# Interactive mode
./scripts/monitoring/3-optimize-resources.sh

# The script will prompt for:
# - API resource adjustments
# - HPA configuration
# - Database optimization
```

**When to scale:**
- **Scale UP** if: CPU > 80%, Memory > 85%, or slow responses
- **Scale DOWN** if: Consistent low usage (< 30%) and fast responses

**Monitoring after changes:**
```bash
# Watch HPA scaling
kubectl get hpa -n finrisk-ai -w

# Monitor pod resources
watch kubectl top pods -n finrisk-ai

# Check for throttling or OOM
kubectl describe pods -n finrisk-ai
```

**Time:** 3-5 minutes

---

### Step 4: Setup Monitoring

**When:** After optimization is complete

**Script:** `./scripts/monitoring/4-setup-monitoring.sh`

**What it does:**
- Creates monitoring namespace
- Configures Prometheus ServiceMonitor
- Creates live monitoring dashboard
- Sets up log aggregation scripts
- Creates alert checking script
- Optional: Automated health check CronJob

**Tools created:**

1. **monitor-dashboard.sh** - Live monitoring dashboard
   ```bash
   ./scripts/monitoring/monitor-dashboard.sh
   # Shows: Pod status, resource usage, HPA, recent events
   # Refreshes every 2 seconds
   ```

2. **view-logs.sh** - Aggregate logs
   ```bash
   ./scripts/monitoring/view-logs.sh [namespace] [component]
   # Components: api, postgres, redis, neo4j, all
   ```

3. **check-alerts.sh** - Alert checker
   ```bash
   ./scripts/monitoring/check-alerts.sh
   # Checks: Pod status, crash loops, resource usage, errors, Redis health
   ```

**Usage:**
```bash
# Setup monitoring infrastructure
./scripts/monitoring/4-setup-monitoring.sh

# Run live dashboard
./scripts/monitoring/monitor-dashboard.sh

# View API logs
./scripts/monitoring/view-logs.sh finrisk-ai api

# Check for alerts
./scripts/monitoring/check-alerts.sh
```

**Prometheus Integration** (if installed):
```bash
# Port-forward to Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Visit http://localhost:9090 for metrics
```

**Recommended alerts:**
- Pod not running
- CrashLoopBackOff
- High CPU/memory usage (> 90%)
- High error rate (> 10 errors/min)
- Redis down
- Cache hit rate < 30%

**Time:** 5-10 minutes

---

## Complete Phase 4 Execution

**Prerequisites:**
- Phase 2 deployed and validated
- kubectl access to cluster
- Basic monitoring tools (curl, bc)

**Full workflow:**

```bash
cd investool

# Step 1: Activate caching (2-3 min)
./scripts/monitoring/1-activate-caching.sh

# Step 2: Benchmark performance (3-5 min)
./scripts/monitoring/2-benchmark-performance.sh

# Review benchmark report
cat benchmark_results/benchmark_*.txt

# Step 3: Optimize resources based on benchmarks (3-5 min)
./scripts/monitoring/3-optimize-resources.sh

# Step 4: Setup monitoring (5-10 min)
./scripts/monitoring/4-setup-monitoring.sh

# Step 5: Validate everything
./scripts/monitoring/check-alerts.sh
./scripts/monitoring/monitor-dashboard.sh
```

**Total time:** 15-25 minutes

---

## Monitoring Strategy

### Daily Monitoring

**Morning check:**
```bash
# Quick health check
./scripts/monitoring/check-alerts.sh

# Check overnight activity
kubectl logs -n finrisk-ai -l app=finrisk-api --since=12h | grep -i error
```

**Continuous:**
```bash
# Live dashboard (keep open during business hours)
./scripts/monitoring/monitor-dashboard.sh
```

### Weekly Tasks

1. **Review Performance:**
   ```bash
   ./scripts/monitoring/2-benchmark-performance.sh
   # Compare with previous week's results
   ```

2. **Check Resource Trends:**
   ```bash
   kubectl top pods -n finrisk-ai
   # Look for trends: increasing memory, CPU patterns
   ```

3. **Review Cache Effectiveness:**
   ```bash
   REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli INFO stats
   # Target: > 50% hit rate
   ```

4. **Analyze Logs for Patterns:**
   ```bash
   kubectl logs -n finrisk-ai -l app=finrisk-api --since=7d | grep -i "error\|warning" | sort | uniq -c | sort -rn
   ```

### Monthly Tasks

1. **Capacity Planning:**
   - Review max replica usage
   - Check if HPA thresholds are appropriate
   - Plan for growth

2. **Cost Optimization:**
   - Review resource requests vs actual usage
   - Right-size pods if over-provisioned
   - Consider reserved instances

3. **Security Updates:**
   - Update dependencies
   - Rotate secrets
   - Review access logs

---

## Performance Tuning

### Cache Optimization

**If cache hit rate < 50%:**
```bash
# Increase TTL
kubectl patch configmap finrisk-config -n finrisk-ai \
  --type='json' \
  -p='[{"op":"replace","path":"/data/CACHE_TTL","value":"7200"}]'

# Restart API pods
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

**If memory pressure:**
```bash
# Reduce TTL or max size
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli CONFIG SET maxmemory 2gb
```

### Scaling Optimization

**If frequent scaling (flapping):**
```bash
# Increase stabilization window
kubectl patch hpa finrisk-api-hpa -n finrisk-ai --type='json' -p='[
  {"op":"add","path":"/spec/behavior","value":{
    "scaleDown":{"stabilizationWindowSeconds":300},
    "scaleUp":{"stabilizationWindowSeconds":60}
  }}
]'
```

**If slow to scale:**
```bash
# Decrease target CPU threshold
kubectl patch hpa finrisk-api-hpa -n finrisk-ai --type='json' -p='[
  {"op":"replace","path":"/spec/targetCPUUtilizationPercentage","value":60}
]'
```

### Latency Optimization

**If API slow (> 200ms):**
1. Check C++ engine performance
2. Review Gemini API latency
3. Optimize database queries
4. Increase cache TTL
5. Add more replicas

**If database slow:**
```bash
# Check PostgreSQL stats
POSTGRES_POD=$(kubectl get pods -n finrisk-ai -l app=postgres -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $POSTGRES_POD -- psql -U finrisk_user -d finrisk_db -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

---

## Alerting Rules

### Critical Alerts (Immediate action)

1. **All pods down**
   - Action: Check cluster, restart deployment
   - Command: `kubectl get pods -n finrisk-ai`

2. **CrashLoopBackOff**
   - Action: Check logs, fix configuration
   - Command: `kubectl logs -n finrisk-ai <pod-name>`

3. **Redis down**
   - Action: Restart Redis, check persistence
   - Command: `kubectl rollout restart deployment/redis -n finrisk-ai`

### Warning Alerts (Monitor and plan)

1. **High error rate (> 10 errors/min)**
   - Action: Review logs, identify root cause
   - May indicate: API bugs, Gemini API issues, resource constraints

2. **Low cache hit rate (< 30%)**
   - Action: Increase TTL, review cache strategy
   - May indicate: High query diversity, TTL too short

3. **Resource usage > 85%**
   - Action: Scale replicas or increase resources
   - Plan: Capacity planning, optimize code

4. **HPA at max replicas**
   - Action: Increase max replicas or optimize performance
   - Indicates: Need for more capacity

---

## Troubleshooting

### Issue: Caching Not Working

**Symptoms:**
- No speed improvement on duplicate queries
- Cache hit rate = 0%

**Solutions:**
```bash
# Check caching is enabled
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep ENABLE_CACHING

# Check Redis
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli PING

# Check API logs
kubectl logs -n finrisk-ai -l app=finrisk-api | grep -i cache

# Restart API if needed
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

### Issue: High Latency

**Symptoms:**
- API responses > 2 seconds
- Benchmark shows slow performance

**Solutions:**
```bash
# Check resource usage
kubectl top pods -n finrisk-ai

# Check for throttling
kubectl describe pods -n finrisk-ai | grep -i "throttl\|oom"

# Scale up
kubectl scale deployment finrisk-api -n finrisk-ai --replicas=5

# Or increase resources
./scripts/monitoring/3-optimize-resources.sh
```

### Issue: OOM Kills

**Symptoms:**
- Pods restarting frequently
- "OOMKilled" in pod status

**Solutions:**
```bash
# Check memory usage
kubectl top pods -n finrisk-ai

# Increase memory limits
kubectl patch deployment finrisk-api -n finrisk-ai --type='json' -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"3Gi"}
]'

# Check for memory leaks in logs
kubectl logs -n finrisk-ai -l app=finrisk-api | grep -i "memory\|leak"
```

### Issue: HPA Not Scaling

**Symptoms:**
- High load but no new pods
- HPA shows "unknown" metrics

**Solutions:**
```bash
# Check HPA status
kubectl describe hpa finrisk-api-hpa -n finrisk-ai

# Check metrics-server
kubectl get deployment metrics-server -n kube-system

# Install metrics-server if missing
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Manually scale if urgent
kubectl scale deployment finrisk-api -n finrisk-ai --replicas=10
```

---

## Cost Optimization

### Resource Right-Sizing

**Check actual vs requested:**
```bash
# Get current requests
kubectl get pods -n finrisk-ai -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].resources.requests}{"\n"}{end}'

# Compare with actual usage
kubectl top pods -n finrisk-ai

# If actual < 50% of requests, reduce requests
```

**Recommended ratios:**
- CPU: Actual should be 50-80% of request
- Memory: Actual should be 60-90% of request

### Caching Strategy

**Aggressive caching (lower costs):**
- TTL: 2-4 hours
- Max size: 5000+
- Trade-off: Less fresh data

**Conservative caching (fresher data):**
- TTL: 30-60 minutes
- Max size: 1000-2000
- Trade-off: More API calls

### Scaling Strategy

**Cost-optimized:**
- Min replicas: 1-2
- Max replicas: 5-8
- Target CPU: 75-85%

**Performance-optimized:**
- Min replicas: 3-5
- Max replicas: 15-20
- Target CPU: 60-70%

---

## Integration with External Tools

### Prometheus + Grafana

```bash
# Install with Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Default: admin / prom-operator
```

### ELK Stack (Logging)

```bash
# Forward logs to Elasticsearch
kubectl logs -n finrisk-ai -l app=finrisk-api -f | \
  logstash -e 'input{stdin{}} output{elasticsearch{hosts=>["localhost:9200"]}}'
```

### PagerDuty / Slack Alerts

Integrate with check-alerts.sh:
```bash
# In check-alerts.sh, add at end:
if [ $ALERTS -gt 0 ]; then
    curl -X POST https://hooks.slack.com/YOUR_WEBHOOK \
      -d "{\"text\":\"🚨 FinRisk AI: $ALERTS alerts detected\"}"
fi
```

---

## Success Criteria

Phase 4 is successful when:

- ✅ Caching active with > 50% hit rate
- ✅ API latency < 500ms (p95)
- ✅ Throughput > 10 requests/second
- ✅ HPA scaling works (tested under load)
- ✅ No OOM kills or CrashLoops for 7 days
- ✅ Monitoring dashboards operational
- ✅ Alerts configured and tested
- ✅ Resource usage optimized (< 80% of limits)

---

## Timeline

| Task | Duration | When |
|------|----------|------|
| Activate caching | 2-3 min | After Phase 2 deployment |
| Benchmark performance | 3-5 min | After caching |
| Optimize resources | 3-5 min | After benchmarking |
| Setup monitoring | 5-10 min | After optimization |
| Validation & tuning | 1-2 hours | Ongoing |
| **Total initial setup** | **15-25 min** | **Day 1** |
| Ongoing monitoring | Daily | Continuous |

---

## Next Steps

After Phase 4 completion:

1. **Continuous Optimization:**
   - Weekly benchmarks
   - Monthly resource reviews
   - Quarterly architecture reviews

2. **Advanced Features:**
   - Multi-region deployment
   - Advanced caching strategies
   - Custom business metrics
   - ML-based autoscaling

3. **Business Integration:**
   - Usage analytics
   - Customer dashboards
   - SLA monitoring
   - Cost attribution

---

## Quick Reference

```bash
# Phase 4 complete workflow
cd investool

# 1. Enable caching
./scripts/monitoring/1-activate-caching.sh

# 2. Run benchmarks
./scripts/monitoring/2-benchmark-performance.sh
cat benchmark_results/benchmark_*.txt

# 3. Optimize resources
./scripts/monitoring/3-optimize-resources.sh

# 4. Setup monitoring
./scripts/monitoring/4-setup-monitoring.sh

# 5. Daily monitoring
./scripts/monitoring/check-alerts.sh
./scripts/monitoring/monitor-dashboard.sh

# 6. View logs
./scripts/monitoring/view-logs.sh finrisk-ai api
```

---

**Phase 4 Status:** ✅ Ready to Execute
**Prerequisites:** Phase 2 deployed
**Documentation:** Complete
**Scripts:** All production-ready

---

*For detailed script documentation, see: scripts/monitoring/README.md*
