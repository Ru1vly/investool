# FinRisk AI - Complete Deployment Guide

**From Zero to Production: A Complete Step-by-Step Guide**

**Version:** 1.0
**Date:** 2025-11-13
**Estimated Time:** 2-4 hours for initial deployment

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites & Requirements](#prerequisites--requirements)
3. [Phase 1: Pre-Deployment Preparation](#phase-1-pre-deployment-preparation)
4. [Phase 2: Deploy Infrastructure](#phase-2-deploy-infrastructure)
5. [Phase 3: Activate SOTA Fine-Tuning](#phase-3-activate-sota-fine-tuning)
6. [Phase 4: Scale & Monitor](#phase-4-scale--monitor)
7. [Verification & Testing](#verification--testing)
8. [Finalization Checklist](#finalization-checklist)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance & Operations](#maintenance--operations)

---

## Overview

This guide will help you deploy the FinRisk AI system from scratch to production.

**Architecture:**
- **C++ Calculation Engine** (13+ financial formulas)
- **Multi-Agent AI System** (Gemini 1.5)
- **RAG System** (Vector + Graph databases)
- **FastAPI REST API**
- **Kubernetes Deployment**
- **Production Caching** (Redis)
- **Fine-Tuning Pipeline** (Optional, Phase 3)
- **Monitoring & Alerting** (Phase 4)

**Timeline:**
- Initial deployment: 2-4 hours
- Full production setup: 1 day
- Fine-tuning ready: 2-8 weeks (data collection)

---

## Prerequisites & Requirements

### Required Tools

1. **Docker** (v20.10+)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Verify
   docker --version
   docker ps
   ```

2. **kubectl** (v1.24+)
   ```bash
   # Install kubectl
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl
   sudo mv kubectl /usr/local/bin/

   # Verify
   kubectl version --client
   ```

3. **Kubernetes Cluster**
   - Local: Docker Desktop, Minikube, or Kind
   - Cloud: GKE, EKS, AKS, or DigitalOcean
   - Minimum: 4 CPU, 8GB RAM, 50GB storage

   ```bash
   # Verify cluster access
   kubectl cluster-info
   kubectl get nodes
   ```

4. **Container Registry** (one of):
   - Docker Hub (free: hub.docker.com)
   - Google Container Registry (GCR)
   - AWS Elastic Container Registry (ECR)
   - GitHub Container Registry (GHCR)

   ```bash
   # Login to your registry
   docker login  # For Docker Hub
   # OR
   docker login ghcr.io  # For GitHub
   ```

5. **Gemini API Key** (Required)
   - Get from: https://makersuite.google.com/app/apikey
   - Free tier available
   - Required for AI functionality

### Optional Tools

6. **Apache Bench** (for benchmarking)
   ```bash
   sudo apt-get install apache2-utils  # Ubuntu/Debian
   # OR
   brew install httpie  # macOS
   ```

7. **jq** (JSON processing)
   ```bash
   sudo apt-get install jq  # Ubuntu/Debian
   # OR
   brew install jq  # macOS
   ```

8. **Prometheus + Grafana** (for monitoring)
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring
   ```

### System Requirements

**Kubernetes Cluster Sizing:**

| Environment | Nodes | CPU | Memory | Storage |
|-------------|-------|-----|--------|---------|
| Development | 1 | 4 cores | 8 GB | 50 GB |
| Staging | 2 | 8 cores | 16 GB | 100 GB |
| Production | 3+ | 16+ cores | 32+ GB | 200+ GB |

**Resource Allocation:**

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| API (per pod) | 500m | 1000m | 1Gi | 2Gi |
| PostgreSQL | 250m | 500m | 512Mi | 1Gi |
| Redis | 100m | 250m | 256Mi | 512Mi |
| Neo4j | 250m | 500m | 512Mi | 1Gi |

**Total (minimum):**
- CPU: 2.2 cores (4 cores recommended)
- Memory: 4.5 GB (8 GB recommended)
- Storage: 50 GB (100 GB recommended)

---

## Phase 1: Pre-Deployment Preparation

**Goal:** Prepare codebase and configuration for deployment

**Time:** 15-30 minutes

### Step 1.1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/Ru1vly/investool.git
cd investool

# Checkout the deployment branch
git checkout claude/phase3-activate-sota-011CV52LokwBFCmJGcjfztFt
```

### Step 1.2: Verify File Structure

```bash
# Check that all files are present
ls -la

# Expected structure:
# ├── Dockerfile
# ├── CMakeLists.txt
# ├── bindings.cpp
# ├── finrisk_ai/
# ├── k8s/
# ├── scripts/
# │   ├── deployment/
# │   ├── finetuning/
# │   └── monitoring/
# ├── PHASE2_EXECUTION.md
# ├── PHASE3_GUIDE.md
# ├── PHASE4_GUIDE.md
# └── DEPLOYMENT_GUIDE.md (this file)
```

### Step 1.3: Verify Scripts are Executable

```bash
# Make all scripts executable
chmod +x scripts/deployment/*.sh
chmod +x scripts/finetuning/*.sh
chmod +x scripts/monitoring/*.sh

# Verify
ls -la scripts/deployment/
ls -la scripts/finetuning/
ls -la scripts/monitoring/
```

### Step 1.4: Review Configuration

```bash
# Review Kubernetes manifests
cat k8s/kustomization.yaml
cat k8s/configmap.yaml
cat k8s/secrets.yaml  # Template only
```

**✅ Phase 1 Complete:** Repository ready for deployment

---

## Phase 2: Deploy Infrastructure

**Goal:** Deploy the FinRisk AI system to Kubernetes

**Time:** 1-2 hours

**Prerequisites:**
- ✅ Docker installed and running
- ✅ kubectl configured with cluster
- ✅ Container registry access
- ✅ Gemini API key ready

### Step 2.1: Setup Secrets

**Time:** 2-3 minutes

```bash
cd investool

# Run the secrets setup script
./scripts/deployment/1-setup-secrets.sh
```

**Interactive Prompts:**
1. Enter your Gemini API key
2. Script will generate database passwords automatically
3. Script will update `k8s/secrets.yaml` with base64-encoded values

**Output:**
- `secrets.txt` - Plaintext backup (KEEP SECURE!)
- `k8s/secrets.yaml` - Updated with secrets
- `k8s/secrets.yaml.backup` - Original template

**⚠️ CRITICAL:** Save `secrets.txt` to your password manager and delete the file:
```bash
# After saving to password manager
shred -u secrets.txt
```

### Step 2.2: Build Docker Image

**Time:** 5-10 minutes

```bash
# Run the build script
./scripts/deployment/2-build-image.sh
```

**Interactive Prompts:**
1. Container registry (e.g., `docker.io/yourusername`)
2. Image name (default: `finrisk-ai`)
3. Version tag (default: `1.0.0`)
4. Test locally? (recommended: `y`)
5. Push to registry? (required: `y`)

**Output:**
- Docker image built with C++ + Python
- Image pushed to registry
- `build-info.txt` - Build metadata

**Example:**
```bash
# Registry: docker.io/yourusername
# Image: finrisk-ai
# Version: 1.0.0
# Full image: docker.io/yourusername/finrisk-ai:1.0.0
```

### Step 2.3: Update Kustomization

**Manual step - Edit the image reference**

```bash
# Edit k8s/kustomization.yaml
nano k8s/kustomization.yaml
# OR
vim k8s/kustomization.yaml
```

**Find and update lines 32-35:**
```yaml
images:
  - name: finrisk-ai
    newName: docker.io/yourusername/finrisk-ai  # YOUR REGISTRY
    newTag: "1.0.0"  # YOUR VERSION
```

**Save and exit**

### Step 2.4: Deploy to Kubernetes

**Time:** 2-3 minutes

```bash
# Run the deployment script
./scripts/deployment/3-deploy-k8s.sh
```

**What it does:**
1. Verifies kubectl and cluster access
2. Checks secrets are configured
3. Applies Kubernetes manifests via Kustomize
4. Monitors pod startup (5-minute timeout)
5. Shows deployment status

**Expected output:**
```
✅ All pods are running!

Deployment Summary:
  • Namespace: finrisk-ai
  • Pods: 4/4 running
  • Services: 4 created
  • HPA: Active (2-10 replicas)
```

### Step 2.5: Validate Deployment

**Time:** 1-2 minutes

```bash
# Run the validation script
./scripts/deployment/4-validate.sh
```

**Tests performed (20 tests):**
1. Infrastructure (namespace, configmap, secrets)
2. Pod health (all pods running)
3. Service availability (all services accessible)
4. API health check
5. C++ engine operational
6. Phase 5 configuration
7. No crash loops
8. OrchestratorV2 initialization

**Success criteria:**
```
✅ 20/20 tests passed

Validation Report saved: validation-report.txt
```

**If tests fail:**
1. Check the validation report
2. Review pod logs: `kubectl logs -n finrisk-ai <pod-name>`
3. See troubleshooting section

### Step 2.6: Access the API

```bash
# Port-forward to access API locally
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80

# In another terminal, test the API
curl http://localhost:8000/health

# Visit the API documentation
# Open browser: http://localhost:8000/docs
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "cpp_engine_available": true,
  "timestamp": "2025-11-13T12:00:00Z"
}
```

**✅ Phase 2 Complete:** System deployed and validated

---

## Phase 3: Activate SOTA Fine-Tuning

**Goal:** Achieve state-of-the-art performance through fine-tuning

**Time:** 2-8 weeks (mostly waiting for data collection)

**Prerequisites:**
- ✅ Phase 2 deployed and validated
- ⏳ 1000+ training examples collected

### Step 3.1: Monitor Data Collection

**Data collection is automatic** once deployed. Check progress weekly:

```bash
# Port-forward to PostgreSQL
kubectl port-forward -n finrisk-ai svc/postgres-service 5432:5432

# In another terminal, check data count
psql -h localhost -U finrisk_user -d finrisk_db -c "SELECT COUNT(*) FROM training_data;"
```

**Target:** 1000+ examples (2000-5000 recommended)

**Timeline:**
- Low usage: 4-8 weeks
- Medium usage: 2-4 weeks
- High usage: 1-2 weeks

### Step 3.2: Export Training Data

**When:** Count >= 1000 examples

```bash
# Export data from PostgreSQL
./scripts/finetuning/1-export-training-data.sh
```

**Output:**
- `training_data/training_data_raw_YYYYMMDD_HHMMSS.json`
- `training_data/export_metadata_YYYYMMDD_HHMMSS.json`

**Time:** 1-2 minutes

### Step 3.3: Prepare Fine-Tuning Dataset

```bash
# Convert to JSONL format
./scripts/finetuning/2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_*.json \
  --output-dir training_data \
  --train-split 0.9
```

**Output:**
- `training_data/training_set_YYYYMMDD_HHMMSS.jsonl`
- `training_data/validation_set_YYYYMMDD_HHMMSS.jsonl`
- `training_data/dataset_metadata_YYYYMMDD_HHMMSS.json`

**Time:** 1-2 minutes

### Step 3.4: Create Fine-Tuning Job

```bash
# Set your Gemini API key
export GEMINI_API_KEY='your-gemini-api-key-here'

# Create tuning job
./scripts/finetuning/3-create-finetuning-job.sh
```

**Interactive prompts:**
1. Select training data file
2. Configure hyperparameters (or use defaults)
3. Confirm and create job

**Output:**
- Tuned model name: `tunedModels/finrisk-v1-XXXXX`
- `training_data/finetuning_job_YYYYMMDD_HHMMSS.json`

**Training time:** 30 minutes to 3 hours

**Monitor progress:**
```bash
# Check status
curl -s "https://generativelanguage.googleapis.com/v1beta/tunedModels/YOUR_MODEL?key=$GEMINI_API_KEY" | jq '.state'

# States: CREATING → ACTIVE (success) | FAILED (error)
```

### Step 3.5: Deploy Fine-Tuned Model

**When:** Model state = ACTIVE

```bash
# Deploy with A/B testing (50% traffic)
./scripts/finetuning/4-deploy-finetuned-model.sh
```

**Interactive prompts:**
1. Select fine-tuned model
2. Configure A/B testing ratio (default: 50%)
3. Confirm deployment

**What it does:**
- Updates Kubernetes secrets with model name
- Configures A/B testing in ConfigMap
- Restarts API pods
- Validates deployment

**Time:** 2-3 minutes

### Step 3.6: Monitor and Adjust

```bash
# View API logs for model usage
kubectl logs -n finrisk-ai -l app=finrisk-api -f

# Check both models are being used
# Look for: "Using base model" and "Using fine-tuned model"
```

**Gradual rollout:**
```bash
# Week 1: 25% fine-tuned
AB_TEST_RATIO=25 ./scripts/finetuning/4-deploy-finetuned-model.sh

# Week 2: 50% fine-tuned (if performing well)
AB_TEST_RATIO=50 ./scripts/finetuning/4-deploy-finetuned-model.sh

# Week 3: 75% fine-tuned (if validated)
AB_TEST_RATIO=75 ./scripts/finetuning/4-deploy-finetuned-model.sh

# Week 4: 100% fine-tuned (production)
AB_TEST_RATIO=100 ./scripts/finetuning/4-deploy-finetuned-model.sh
```

**✅ Phase 3 Complete:** Fine-tuned model deployed with A/B testing

---

## Phase 4: Scale & Monitor

**Goal:** Production-grade operations and monitoring

**Time:** 15-25 minutes

**Prerequisites:**
- ✅ Phase 2 deployed

### Step 4.1: Activate Caching

```bash
# Enable Redis caching
./scripts/monitoring/1-activate-caching.sh
```

**Configuration (prompts):**
- Cache TTL: 3600 seconds (1 hour)
- Max cached items: 1000

**What it does:**
- Updates ConfigMap with caching settings
- Configures Redis (LRU, 1GB memory, persistence)
- Restarts API pods
- Validates caching

**Time:** 2-3 minutes

### Step 4.2: Benchmark Performance

```bash
# Run comprehensive benchmarks
./scripts/monitoring/2-benchmark-performance.sh
```

**Tests:**
1. Health check performance (100 requests)
2. Cache effectiveness (same query twice)
3. Concurrent users (10 users, 20 requests each)
4. Resource usage
5. Redis cache statistics
6. Optional: Apache Bench

**Output:**
- `benchmark_results/benchmark_YYYYMMDD_HHMMSS.txt`

**Review results:**
```bash
cat benchmark_results/benchmark_*.txt
```

**Time:** 3-5 minutes

### Step 4.3: Optimize Resources

```bash
# Interactive resource optimization
./scripts/monitoring/3-optimize-resources.sh
```

**Optimizes:**
1. API pod resources (CPU/memory)
2. HPA configuration (min/max replicas, target CPU)
3. Database resources
4. Pod distribution

**Time:** 3-5 minutes

### Step 4.4: Setup Monitoring

```bash
# Setup monitoring infrastructure
./scripts/monitoring/4-setup-monitoring.sh
```

**Creates:**
1. Monitoring namespace
2. Prometheus ServiceMonitor (optional)
3. Live dashboard script
4. Log viewer script
5. Alert checker script
6. Automated health check CronJob (optional)

**Time:** 5-10 minutes

### Step 4.5: Use Monitoring Tools

```bash
# Live monitoring dashboard
./scripts/monitoring/monitor-dashboard.sh

# View logs (in another terminal)
./scripts/monitoring/view-logs.sh finrisk-ai api

# Check alerts (in another terminal)
./scripts/monitoring/check-alerts.sh
```

**✅ Phase 4 Complete:** Production monitoring active

---

## Verification & Testing

### Quick Health Check

```bash
# Check all pods are running
kubectl get pods -n finrisk-ai

# Expected output: All pods in Running state
# NAME                           READY   STATUS    RESTARTS
# finrisk-api-xxx                1/1     Running   0
# postgres-xxx                   1/1     Running   0
# redis-xxx                      1/1     Running   0
# neo4j-xxx                      1/1     Running   0
```

### API Functionality Test

```bash
# Port-forward
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80

# Test health endpoint
curl http://localhost:8000/health | jq .

# Test API endpoint (in another terminal)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "Analyze Tesla stock performance",
    "user_id": "test_user",
    "session_id": "test_session"
  }' | jq .
```

**Expected:** JSON response with analysis

### Cache Verification

```bash
# Check Redis is working
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli PING

# Expected: PONG

# Check cache stats
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli INFO stats | grep keyspace
```

### HPA Verification

```bash
# Check HPA status
kubectl get hpa -n finrisk-ai

# Expected: finrisk-api-hpa showing current/desired replicas
```

### Data Collection Verification

```bash
# Check training data is being collected
kubectl port-forward -n finrisk-ai svc/postgres-service 5432:5432

# In another terminal
psql -h localhost -U finrisk_user -d finrisk_db -c "SELECT COUNT(*) FROM training_data;"

# Expected: Count > 0 (if API has been used)
```

---

## Finalization Checklist

### Security Checklist

- [ ] **Secrets secured**
  - [ ] `secrets.txt` saved to password manager
  - [ ] `secrets.txt` deleted from filesystem
  - [ ] `k8s/secrets.yaml` never committed to git (.gitignore verified)
  - [ ] Gemini API key kept private

- [ ] **Network security**
  - [ ] Ingress configured with TLS (if production)
  - [ ] Network policies applied (if required)
  - [ ] Firewall rules configured

- [ ] **Access control**
  - [ ] RBAC configured for cluster access
  - [ ] Service accounts properly configured
  - [ ] Secrets access restricted

### Deployment Checklist

- [ ] **Phase 2: Infrastructure**
  - [ ] All pods running (4/4)
  - [ ] All services created
  - [ ] Validation: 20/20 tests passed
  - [ ] API accessible and responding
  - [ ] C++ engine operational

- [ ] **Phase 4: Monitoring**
  - [ ] Caching enabled and working
  - [ ] Benchmarks completed
  - [ ] Resources optimized
  - [ ] Monitoring tools installed
  - [ ] Alert checker running

- [ ] **Phase 3: Fine-Tuning** (Optional, after data collection)
  - [ ] 1000+ training examples collected
  - [ ] Fine-tuning job created and completed
  - [ ] Fine-tuned model deployed with A/B testing
  - [ ] Performance validated

### Operations Checklist

- [ ] **Documentation reviewed**
  - [ ] DEPLOYMENT_GUIDE.md (this file)
  - [ ] PHASE2_EXECUTION.md
  - [ ] PHASE3_GUIDE.md
  - [ ] PHASE4_GUIDE.md

- [ ] **Monitoring setup**
  - [ ] Dashboard accessible
  - [ ] Logs viewable
  - [ ] Alerts configured
  - [ ] Prometheus/Grafana integrated (optional)

- [ ] **Backup & Recovery**
  - [ ] Database backup strategy defined
  - [ ] Secrets backed up securely
  - [ ] Disaster recovery plan documented

- [ ] **Performance baselines**
  - [ ] Initial benchmarks recorded
  - [ ] Resource usage documented
  - [ ] SLAs defined (if applicable)

### Business Readiness Checklist

- [ ] **API ready for users**
  - [ ] External access configured (Ingress)
  - [ ] API documentation accessible
  - [ ] Authentication/authorization (if required)
  - [ ] Rate limiting configured

- [ ] **Monitoring & Alerting**
  - [ ] Dashboards shared with team
  - [ ] Alert notifications configured (Slack, PagerDuty)
  - [ ] On-call rotation defined
  - [ ] Incident response process documented

- [ ] **Cost Management**
  - [ ] Resource costs calculated
  - [ ] Scaling limits configured
  - [ ] Cost alerts set up

- [ ] **Compliance**
  - [ ] Data privacy requirements met
  - [ ] Logging/audit trails enabled
  - [ ] Terms of service defined

---

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

**Symptoms:**
```
kubectl get pods -n finrisk-ai
# Shows: CrashLoopBackOff or ImagePullBackOff
```

**Solutions:**
```bash
# Check pod logs
kubectl describe pod <pod-name> -n finrisk-ai
kubectl logs <pod-name> -n finrisk-ai

# Common causes:
# - ImagePullBackOff: Wrong image name/registry, not pushed
# - CrashLoopBackOff: Missing secrets, wrong config, app error

# Verify secrets
kubectl get secret finrisk-secrets -n finrisk-ai -o yaml

# Verify image exists
docker pull your-registry/finrisk-ai:1.0.0
```

#### 2. Validation Tests Failing

**Symptoms:**
```
./scripts/deployment/4-validate.sh
# Shows: X/20 tests failed
```

**Solutions:**
```bash
# Check which tests failed
cat validation-report.txt

# Most common: C++ engine not available
# Fix: Check API logs
kubectl logs -n finrisk-ai -l app=finrisk-api

# Secrets not configured
# Fix: Re-run secrets setup
./scripts/deployment/1-setup-secrets.sh
```

#### 3. Cannot Connect to API

**Symptoms:**
```
curl http://localhost:8000/health
# Shows: Connection refused
```

**Solutions:**
```bash
# Check port-forward is running
ps aux | grep port-forward

# Check API pod is running
kubectl get pods -n finrisk-ai -l app=finrisk-api

# Check service exists
kubectl get svc -n finrisk-ai finrisk-api-service

# Restart port-forward
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80
```

#### 4. High Memory Usage / OOM Kills

**Symptoms:**
```
kubectl get pods -n finrisk-ai
# Shows: Pods restarting frequently
kubectl describe pod <pod-name> -n finrisk-ai
# Shows: OOMKilled
```

**Solutions:**
```bash
# Increase memory limits
./scripts/monitoring/3-optimize-resources.sh
# Choose "Heavy" workload option

# Or manually
kubectl patch deployment finrisk-api -n finrisk-ai --type='json' -p='[
  {"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"3Gi"}
]'
```

#### 5. Slow API Responses

**Symptoms:**
- API responds but takes > 2 seconds

**Solutions:**
```bash
# Check if caching is enabled
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep ENABLE_CACHING

# Enable if not active
./scripts/monitoring/1-activate-caching.sh

# Scale up replicas
kubectl scale deployment finrisk-api -n finrisk-ai --replicas=5

# Run benchmarks to identify bottleneck
./scripts/monitoring/2-benchmark-performance.sh
```

#### 6. Database Connection Errors

**Symptoms:**
- API logs show "Cannot connect to database"

**Solutions:**
```bash
# Check database pods
kubectl get pods -n finrisk-ai -l app=postgres

# Check secrets
kubectl get secret finrisk-secrets -n finrisk-ai -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d

# Restart database
kubectl rollout restart deployment/postgres -n finrisk-ai
```

---

## Maintenance & Operations

### Daily Tasks

**Morning Check (5 minutes):**
```bash
# Run alert checker
./scripts/monitoring/check-alerts.sh

# Check pod status
kubectl get pods -n finrisk-ai

# Review overnight logs
kubectl logs -n finrisk-ai -l app=finrisk-api --since=12h | grep -i error
```

### Weekly Tasks

**Performance Review (15 minutes):**
```bash
# Run benchmarks
./scripts/monitoring/2-benchmark-performance.sh

# Compare with previous week
diff benchmark_results/benchmark_LAST_WEEK.txt \
     benchmark_results/benchmark_THIS_WEEK.txt

# Review resource usage
kubectl top pods -n finrisk-ai
kubectl top nodes

# Check cache effectiveness
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai $REDIS_POD -- redis-cli INFO stats
```

**Data Collection Check (5 minutes):**
```bash
# Check training data count
kubectl port-forward -n finrisk-ai svc/postgres-service 5432:5432 &
psql -h localhost -U finrisk_user -d finrisk_db -c "SELECT COUNT(*) FROM training_data;"
```

### Monthly Tasks

**Capacity Planning (30 minutes):**
- Review HPA max replica usage
- Check if thresholds need adjustment
- Plan for growth

**Cost Review (30 minutes):**
- Review resource requests vs actual usage
- Right-size pods if over-provisioned
- Consider reserved instances/committed use

**Security Updates (1 hour):**
- Update dependencies
- Rotate secrets
- Review access logs
- Check for CVEs

### Quarterly Tasks

**Architecture Review (2-4 hours):**
- Review system performance trends
- Evaluate new features
- Plan major upgrades
- Review disaster recovery plan

**Fine-Tuning Refresh (if using Phase 3):**
- Export latest training data (more examples)
- Retrain model with fresh data
- Deploy updated fine-tuned model

---

## Quick Reference Commands

### Deployment

```bash
# Full deployment from scratch
cd investool
./scripts/deployment/1-setup-secrets.sh
./scripts/deployment/2-build-image.sh
# Edit k8s/kustomization.yaml with your image
./scripts/deployment/3-deploy-k8s.sh
./scripts/deployment/4-validate.sh
```

### Monitoring

```bash
# Daily monitoring
./scripts/monitoring/check-alerts.sh
./scripts/monitoring/monitor-dashboard.sh

# View logs
./scripts/monitoring/view-logs.sh finrisk-ai api

# Performance
./scripts/monitoring/2-benchmark-performance.sh
```

### Troubleshooting

```bash
# Check everything
kubectl get all -n finrisk-ai

# Pod details
kubectl describe pod <pod-name> -n finrisk-ai
kubectl logs <pod-name> -n finrisk-ai

# Restart
kubectl rollout restart deployment/finrisk-api -n finrisk-ai

# Scale
kubectl scale deployment finrisk-api -n finrisk-ai --replicas=5
```

### Access

```bash
# API
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80

# PostgreSQL
kubectl port-forward -n finrisk-ai svc/postgres-service 5432:5432

# Redis
REDIS_POD=$(kubectl get pods -n finrisk-ai -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n finrisk-ai -it $REDIS_POD -- redis-cli
```

---

## Additional Resources

### Documentation

- **PHASE2_EXECUTION.md** - Detailed Phase 2 deployment guide
- **PHASE2_STATUS.md** - Phase 2 status and next actions
- **PHASE3_GUIDE.md** - Complete fine-tuning guide
- **PHASE4_GUIDE.md** - Monitoring and optimization guide
- **scripts/deployment/README.md** - Deployment scripts documentation
- **scripts/finetuning/README.md** - Fine-tuning scripts documentation
- **scripts/monitoring/README.md** - Monitoring scripts documentation

### External Links

- **Gemini API:** https://makersuite.google.com/app/apikey
- **Kubernetes Docs:** https://kubernetes.io/docs/
- **Docker Hub:** https://hub.docker.com/
- **Prometheus:** https://prometheus.io/
- **Grafana:** https://grafana.com/

### Support

For issues or questions:
1. Check troubleshooting section above
2. Review relevant phase guide
3. Check pod logs: `kubectl logs -n finrisk-ai <pod-name>`
4. Review GitHub issues: https://github.com/Ru1vly/investool/issues

---

## Summary

### What You've Deployed

✅ **Complete FinRisk AI System:**
- C++ calculation engine (13+ formulas)
- Multi-agent AI system (Gemini 1.5)
- RAG system (Vector + Graph databases)
- FastAPI REST API
- Production-ready Kubernetes deployment

✅ **Phase 2 - Infrastructure:**
- All services deployed and running
- Secrets configured securely
- 20-test validation passed

✅ **Phase 4 - Monitoring:**
- Redis caching enabled
- Performance benchmarked
- Resources optimized
- Monitoring dashboards active

⏳ **Phase 3 - Fine-Tuning:**
- Data collection automatic
- Scripts ready to execute
- Waiting for 1000+ examples

### Success Criteria

Your deployment is successful when:

- [ ] All pods running (4/4)
- [ ] Validation: 20/20 tests passed
- [ ] API responds to health checks
- [ ] API can process analysis requests
- [ ] Caching enabled (> 50% hit rate)
- [ ] Monitoring tools working
- [ ] No critical alerts

### Next Steps

1. **Monitor operations** (daily checks)
2. **Optimize performance** (weekly reviews)
3. **Collect training data** (automatic, 1-4 weeks)
4. **Execute Phase 3** (when 1000+ examples ready)
5. **Scale as needed** (based on usage)

---

**Deployment Status:** ✅ Production-Ready
**Last Updated:** 2025-11-13
**Version:** 1.0

**Congratulations! Your FinRisk AI system is now deployed and operational!** 🎉

---
