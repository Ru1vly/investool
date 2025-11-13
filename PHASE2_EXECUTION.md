# Phase 2 Execution Guide

**Step-by-step instructions for deploying FinRisk AI to production.**

---

## Prerequisites Check

Before starting, ensure you have:

- [ ] **Docker** installed (20.10+)
  ```bash
  docker --version
  # If not installed: https://docs.docker.com/get-docker/
  ```

- [ ] **kubectl** installed and configured
  ```bash
  kubectl version --client
  kubectl cluster-info
  # If not installed: https://kubernetes.io/docs/tasks/tools/
  ```

- [ ] **Kubernetes cluster** access (GKE, EKS, AKS, or local)
  ```bash
  kubectl get nodes
  # Should show your cluster nodes
  ```

- [ ] **Container registry** access (Docker Hub, GCR, ECR, etc.)
  ```bash
  # Docker Hub:
  docker login

  # GCR:
  gcloud auth configure-docker

  # ECR:
  aws ecr get-login-password | docker login --username AWS --password-stdin <registry>
  ```

- [ ] **Gemini API key** from https://makersuite.google.com/app/apikey

---

## Execution Steps

### Step 1: Setup Secrets (2 minutes)

Navigate to project root and run:

```bash
cd investool
./scripts/deployment/1-setup-secrets.sh
```

**What it will ask:**
1. Your Gemini API key
2. Confirm to proceed

**What it does automatically:**
- Generates strong passwords (32 chars)
- Base64 encodes all values
- Updates `k8s/secrets.yaml`
- Saves plaintext to `secrets.txt`

**Expected output:**
```
╔════════════════════════════════════════════════════════════════╗
║       FinRisk AI - Kubernetes Secrets Setup                   ║
╚════════════════════════════════════════════════════════════════╝

This script will:
  1. Prompt for your Gemini API key
  2. Generate strong passwords for databases
  3. Base64 encode all values
  4. Update k8s/secrets.yaml automatically

Continue? (y/n): y

═══════════════════════════════════════════════════════════════
  Step 1: Gemini API Key
═══════════════════════════════════════════════════════════════

Get your Gemini API key from:
  https://makersuite.google.com/app/apikey

Enter your Gemini API key: [your key here]

═══════════════════════════════════════════════════════════════
  Step 2: Generate Database Passwords
═══════════════════════════════════════════════════════════════

Generating strong passwords (32 characters)...
✅ Passwords generated

═══════════════════════════════════════════════════════════════
  Step 3: Save Secrets (IMPORTANT!)
═══════════════════════════════════════════════════════════════

⚠️  SAVE THESE PASSWORDS SECURELY!
Saving to: secrets.txt (KEEP THIS SECURE!)

✅ Secrets saved to secrets.txt (permissions: 600)

═══════════════════════════════════════════════════════════════
  Step 4: Update k8s/secrets.yaml
═══════════════════════════════════════════════════════════════

✅ Backup created: k8s/secrets.yaml.backup
✅ k8s/secrets.yaml updated

═══════════════════════════════════════════════════════════════
  ✅ Secrets Setup Complete!
═══════════════════════════════════════════════════════════════
```

**Important:**
- `secrets.txt` now contains your plaintext passwords
- Store it in a password manager, then delete the file
- Both `secrets.txt` and `k8s/secrets.yaml` are .gitignored

---

### Step 2: Build Docker Image (5-10 minutes)

```bash
./scripts/deployment/2-build-image.sh
```

**What it will ask:**
1. Container registry (e.g., `docker.io/yourname`, `gcr.io/project-id`)
2. Image name (default: `finrisk-ai`)
3. Version tag (default: `1.0.0`)
4. Test locally? (y/n)
5. Push to registry? (y/n)

**Example interaction:**
```
Container registry: docker.io/mycompany
Image name: finrisk-ai
Version tag: 1.0.0

═══════════════════════════════════════════════════════════════
  Build Configuration
═══════════════════════════════════════════════════════════════

  Registry: docker.io/mycompany
  Image name: finrisk-ai
  Version: 1.0.0

  Full image tag: docker.io/mycompany/finrisk-ai:1.0.0
  Latest tag: docker.io/mycompany/finrisk-ai:latest

Proceed with build? (y/n): y

Starting multi-stage build...
  Stage 1: C++ compilation (may take 5-10 minutes)
  Stage 2: Python application setup

[Docker build output...]

✅ Build completed in 487s

Test image locally before pushing? (y/n): y
Starting test container...
✅ Container is running
✅ Health endpoint responds

Push image to registry now? (y/n): y
Pushing images...
✅ Images pushed successfully

═══════════════════════════════════════════════════════════════
  ✅ Build Process Complete!
═══════════════════════════════════════════════════════════════

Image details:
  Full tag: docker.io/mycompany/finrisk-ai:1.0.0
  Latest tag: docker.io/mycompany/finrisk-ai:latest
```

**Build includes:**
- C++ InvestTool engine compilation (Phase 1)
- All Python dependencies
- FastAPI application
- Phase 5 fine-tuning framework
- Health checks and non-root user

---

### Step 2.5: Update Kustomization (Manual - 30 seconds)

Edit `k8s/kustomization.yaml`:

```bash
# Open editor
nano k8s/kustomization.yaml
# or
vim k8s/kustomization.yaml
```

Find this section (around line 32):

```yaml
images:
  - name: finrisk-ai
    newName: your-registry/finrisk-ai  # ← UPDATE THIS
    newTag: latest                      # ← AND THIS
```

Change to your actual registry and version:

```yaml
images:
  - name: finrisk-ai
    newName: docker.io/mycompany/finrisk-ai  # Your registry
    newTag: "1.0.0"                           # Your version
```

**Save and close.**

---

### Step 3: Deploy to Kubernetes (2-3 minutes)

```bash
./scripts/deployment/3-deploy-k8s.sh
```

**What it does:**
1. Validates kubectl and cluster connection
2. Checks secrets are configured
3. Uncomments `secrets.yaml` in kustomization
4. Deploys via `kubectl apply -k k8s/`
5. Monitors pod startup (5 min timeout)
6. Shows deployment status

**Expected output:**
```
╔════════════════════════════════════════════════════════════════╗
║       FinRisk AI - Kubernetes Deployment                      ║
╚════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
  Pre-flight Checks
═══════════════════════════════════════════════════════════════

✅ kubectl found: v1.28.0
✅ Connected to cluster: production-cluster
✅ k8s/ directory found
✅ Secrets configured
✅ kustomization.yaml configured

Resources to deploy:
  • Namespace - finrisk-ai
  • ConfigMap - finrisk-config
  • Secret - finrisk-secrets
  • Deployment - postgres
  • Service - postgres-service
  • PersistentVolumeClaim - postgres-pvc
  • Deployment - redis
  • Service - redis-service
  • PersistentVolumeClaim - redis-pvc
  • Deployment - neo4j
  • Service - neo4j-service
  • PersistentVolumeClaim - neo4j-data-pvc
  • Deployment - finrisk-api
  • Service - finrisk-api-service
  • HorizontalPodAutoscaler - finrisk-api-hpa
  • Ingress - finrisk-api-ingress

Proceed with deployment? (y/n): y

═══════════════════════════════════════════════════════════════
  Deploying to Kubernetes
═══════════════════════════════════════════════════════════════

Applying kustomization...
namespace/finrisk-ai created
configmap/finrisk-config created
secret/finrisk-secrets created
persistentvolumeclaim/postgres-pvc created
deployment.apps/postgres created
service/postgres-service created
[... more resources ...]

✅ Deployment initiated in 2s

═══════════════════════════════════════════════════════════════
  Monitoring Deployment
═══════════════════════════════════════════════════════════════

Checking namespace...
✅ Namespace: finrisk-ai

Waiting for pods to start (this may take 2-3 minutes)...

  Pods: 7/7 running, 0 pending, 0 failed
✅ All pods are running!

═══════════════════════════════════════════════════════════════
  ✅ Deployment Complete!
═══════════════════════════════════════════════════════════════

What was deployed:
  ✅ Namespace: finrisk-ai
  ✅ PostgreSQL with pgvector
  ✅ Redis for caching
  ✅ Neo4j for knowledge graph
  ✅ FinRisk API (3 replicas with HPA)
  ✅ Ingress for external access
```

**Pods running:**
- 1 PostgreSQL pod
- 1 Redis pod
- 1 Neo4j pod
- 3 FinRisk API pods
- **Total: 6-7 pods**

---

### Step 4: Validate Deployment (1 minute)

```bash
./scripts/deployment/4-validate.sh
```

**What it does:**
- Runs 20 comprehensive tests
- Tests all infrastructure components
- Validates API health
- Checks Phase 5 configuration

**Expected output:**
```
╔════════════════════════════════════════════════════════════════╗
║       FinRisk AI - Deployment Validation                      ║
╚════════════════════════════════════════════════════════════════╝

Running comprehensive validation tests...

═══════════════════════════════════════════════════════════════
  Test Suite 1: Infrastructure
═══════════════════════════════════════════════════════════════

[1] Namespace exists... ✅ PASS
[2] ConfigMap deployed... ✅ PASS
[3] Secrets deployed... ✅ PASS

═══════════════════════════════════════════════════════════════
  Test Suite 2: Pods
═══════════════════════════════════════════════════════════════

[4] PostgreSQL pod running... ✅ PASS
[5] Redis pod running... ✅ PASS
[6] Neo4j pod running... ✅ PASS
[7] FinRisk API pods running... ✅ PASS
     (3/3 pods running)

═══════════════════════════════════════════════════════════════
  Test Suite 3: Services
═══════════════════════════════════════════════════════════════

[8] PostgreSQL service available... ✅ PASS
[9] Redis service available... ✅ PASS
[10] Neo4j service available... ✅ PASS
[11] FinRisk API service available... ✅ PASS

═══════════════════════════════════════════════════════════════
  Test Suite 4: API Health
═══════════════════════════════════════════════════════════════

Setting up port forward for testing...
[12] API health endpoint responds... ✅ PASS
[13] API reports healthy status... ✅ PASS
[14] C++ engine operational... ✅ PASS
[15] API documentation accessible... ✅ PASS
[16] OpenAPI specification available... ✅ PASS

═══════════════════════════════════════════════════════════════
  Test Suite 5: Configuration
═══════════════════════════════════════════════════════════════

[17] Data collection enabled... ✅ PASS
[18] Horizontal Pod Autoscaler configured... ✅ PASS

═══════════════════════════════════════════════════════════════
  Test Suite 6: Logs
═══════════════════════════════════════════════════════════════

[19] No pods in CrashLoopBackOff... ✅ PASS
[20] OrchestratorV2 initialized... ✅ PASS

═══════════════════════════════════════════════════════════════
  Validation Results
═══════════════════════════════════════════════════════════════

Total tests: 20
Passed: 20 ✅
Failed: 0 ❌

Pass rate: 100%

🎉 All validation tests passed!

✅ Deployment is healthy and ready for use

Next steps:
  1. Access API: kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80
  2. Test with: curl http://localhost:8000/health
  3. View docs: http://localhost:8000/docs
  4. Monitor logs: kubectl logs -n finrisk-ai -l app=finrisk-api -f
```

**Success criteria:** All 20 tests pass ✅

---

## Post-Deployment: Access Your API

### Local Access (Port Forwarding)

```bash
# Port forward to your machine
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80

# In another terminal:
# Test health endpoint
curl http://localhost:8000/health

# Access API documentation
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
```

### Test API

```bash
# Generate a financial analysis report
curl -X POST http://localhost:8000/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Calculate the Sharpe ratio for monthly returns of 5%, -2%, 3%, 8%, -1%, 4%",
    "user_id": "test_user_123",
    "session_id": "test_session_001"
  }'
```

**Expected response:**
```json
{
  "final_report_text": "Based on the analysis of your portfolio returns...",
  "calculation_results": {
    "sharpe_ratio": 1.42,
    "volatility": 0.0423,
    "variance": 0.00179
  },
  "chart_json": {...},
  "metadata": {
    "validation_passed": true,
    "approach": "base_rag_only"
  }
}
```

---

## Monitoring

### View Logs

```bash
# All API logs
kubectl logs -n finrisk-ai -l app=finrisk-api -f

# Specific pod
kubectl logs -n finrisk-ai <pod-name> -f

# Look for:
# ✅ FinRiskOrchestratorV2 initialized successfully
# ✅ Data collection: ENABLED
# ✅ C++ engine available
# 🚀 FinRisk AI API ready to serve requests
```

### Monitor Pods

```bash
# Watch pod status
kubectl get pods -n finrisk-ai -w

# Check resource usage
kubectl top pods -n finrisk-ai

# Check HPA status
kubectl get hpa -n finrisk-ai
```

### Check Data Collection

```bash
# SSH into a pod
kubectl exec -it -n finrisk-ai deployment/finrisk-api -- /bin/bash

# Check training data
ls -lh data/training_examples/

# Get collection stats
python3 -c "
from finrisk_ai.finetuning import TrainingDataCollector
collector = TrainingDataCollector()
stats = collector.get_statistics()
print(f'Examples collected: {stats[\"total_examples\"]}')
print(f'Avg quality: {stats[\"average_quality_score\"]:.2f}')
"
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n finrisk-ai

# Describe pod to see error
kubectl describe pod -n finrisk-ai <pod-name>

# Check events
kubectl get events -n finrisk-ai --sort-by='.lastTimestamp'

# Common issues:
# - Image pull errors: Check registry access
# - Pending: Check node resources (kubectl top nodes)
# - CrashLoopBackOff: Check logs (kubectl logs -n finrisk-ai <pod-name>)
```

### API Not Responding

```bash
# Check API pod logs
kubectl logs -n finrisk-ai -l app=finrisk-api --tail=100

# Common issues:
# - Missing GEMINI_API_KEY: Check secrets
# - Database connection failed: Check postgres pod
# - C++ engine not available: Check Docker build
```

### Validation Tests Fail

```bash
# Re-run with verbose output
./scripts/deployment/4-validate.sh

# Check specific component:
kubectl get all -n finrisk-ai
kubectl logs -n finrisk-ai -l app=finrisk-api
kubectl describe deployment finrisk-api -n finrisk-ai
```

---

## Success Checklist

- [ ] All 20 validation tests pass
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] C++ engine available: `"cpp_engine_available": true`
- [ ] OrchestratorV2 initialized (check logs)
- [ ] Data collection enabled (check logs)
- [ ] API documentation accessible at `/docs`
- [ ] Report generation works end-to-end
- [ ] No pods in CrashLoopBackOff
- [ ] HPA configured and monitoring

---

## Next Steps (Phase 3)

Once deployment is validated:

1. **Configure Production Access:**
   - Update `k8s/ingress.yaml` with your domain
   - Configure DNS A record to cluster IP
   - Setup TLS certificate (cert-manager or manual)

2. **Monitor Data Collection:**
   - System automatically collects training data
   - Target: 1000+ high-quality examples
   - Check periodically: `kubectl exec ... python3 -c "from finrisk_ai.finetuning import TrainingDataCollector; ..."`

3. **Proceed to Phase 3:**
   - Follow `PRODUCTION_LAUNCH.md` Section: Phase 3
   - After 1000+ examples: Export and prepare data
   - Create fine-tuning job with Gemini API
   - Deploy fine-tuned model
   - Enable A/B testing
   - Achieve 98% accuracy target

---

## Quick Reference

```bash
# Deployment
./scripts/deployment/1-setup-secrets.sh      # 2 min
./scripts/deployment/2-build-image.sh        # 5-10 min
# Edit k8s/kustomization.yaml (manual)       # 30 sec
./scripts/deployment/3-deploy-k8s.sh         # 2-3 min
./scripts/deployment/4-validate.sh           # 1 min

# Access
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80
curl http://localhost:8000/health
open http://localhost:8000/docs

# Monitor
kubectl get pods -n finrisk-ai -w
kubectl logs -n finrisk-ai -l app=finrisk-api -f
kubectl top pods -n finrisk-ai

# Manage
kubectl scale deployment finrisk-api --replicas=5 -n finrisk-ai
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
kubectl delete -k k8s/  # Delete everything
```

---

**Total Deployment Time: 10-16 minutes**

**Status after Phase 2:** Production-ready system with automatic data collection enabled, ready for Phase 3 fine-tuning! 🚀
