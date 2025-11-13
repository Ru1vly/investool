# FinRisk AI - Production Launch Guide

**Complete step-by-step guide for deploying FinRisk AI to production**

This guide walks you through the 4-phase launch process from finalization to live deployment with SOTA performance.

---

## Prerequisites

- Docker 20.10+ installed
- Kubernetes cluster access (1.24+) with kubectl configured
- Container registry access (Docker Hub, GCR, ECR, etc.)
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Domain name configured (for production ingress)

---

## Phase 1: Finalize & Lock (Pre-Launch)

### Status: ✅ COMPLETE

The codebase has been finalized with:
- **C++ Integration Locked**: Only C++ based CalculationAgent remains (no Python code generation)
- **OrchestratorV2 Active**: Production API uses Phase 5 orchestrator with data collection enabled by default
- **Phase 5 Configuration**: All environment variables and configs updated

### Phase 1 Deliverables

✅ **CalculationAgent Finalized** (`finrisk_ai/agents/specialized_agents.py`)
- Only C++ engine execution method remains
- 100% deterministic calculations
- Zero execution risk

✅ **API Updated** (`finrisk_ai/api/main.py`)
- Uses `FinRiskOrchestratorV2` by default
- Data collection enabled by default
- Configurable via environment variables

✅ **Configuration Updated**:
- `.env.example` - Phase 5 variables added
- `docker-compose.yml` - Phase 5 environment variables
- `k8s/configmap.yaml` - Phase 5 settings

### Build Production Container

```bash
# Navigate to project root
cd /path/to/investool

# Build Docker image (multi-stage: C++ + Python)
docker build -t your-registry/finrisk-ai:1.0.0 .

# Example for Docker Hub
docker build -t yourusername/finrisk-ai:1.0.0 .

# Example for Google Container Registry
docker build -t gcr.io/your-project/finrisk-ai:1.0.0 .

# Tag as latest
docker tag your-registry/finrisk-ai:1.0.0 your-registry/finrisk-ai:latest

# Push to registry
docker push your-registry/finrisk-ai:1.0.0
docker push your-registry/finrisk-ai:latest
```

**Build Time:** ~5-10 minutes (includes C++ compilation)

---

## Phase 2: Deploy Infrastructure (The Launch)

### Step 2.1: Create Production Secrets

```bash
# Create real secrets file from template
cp k8s/secrets.yaml.template k8s/secrets.yaml

# Base64 encode your secrets
echo -n 'your_gemini_api_key_here' | base64
echo -n 'your_postgres_password' | base64
echo -n 'your_redis_password' | base64
echo -n 'your_neo4j_password' | base64

# Edit k8s/secrets.yaml and replace placeholders
# Example:
# GEMINI_API_KEY: QUl6YVN5QUJDMTIzLi4u
```

**IMPORTANT:** Never commit `k8s/secrets.yaml` to git!

### Step 2.2: Update Image in Kustomization

```bash
# Edit k8s/kustomization.yaml
# Update the images section:

images:
  - name: finrisk-ai
    newName: your-registry/finrisk-ai  # Your actual registry
    newTag: "1.0.0"
```

### Step 2.3: Deploy to Kubernetes

```bash
# Uncomment secrets in k8s/kustomization.yaml
# Line should be:  - secrets.yaml

# Deploy entire stack
kubectl apply -k k8s/

# Verify deployment
kubectl get all -n finrisk-ai

# Expected output:
# - 3 finrisk-api pods (running)
# - 1 postgres pod (running)
# - 1 redis pod (running)
# - 1 neo4j pod (running)
# - Services for each
# - Ingress configured
```

### Step 2.4: Monitor Deployment

```bash
# Watch pods come up
kubectl get pods -n finrisk-ai -w

# Check logs
kubectl logs -n finrisk-ai -l app=finrisk-api -f

# Look for:
# ✅ FinRiskOrchestratorV2 initialized successfully
# ✅ Data collection: ENABLED
# ✅ C++ engine available
# 🚀 FinRisk AI API ready to serve requests
```

### Step 2.5: Configure Ingress Domain

```bash
# Edit k8s/ingress.yaml
# Replace api.finrisk.example.com with your actual domain

# Example:
spec:
  tls:
  - hosts:
    - api.yourcompany.com
    secretName: finrisk-api-tls
  rules:
  - host: api.yourcompany.com

# Reapply
kubectl apply -f k8s/ingress.yaml
```

### Step 2.6: End-to-End Validation

```bash
# Port forward for testing (if ingress not ready)
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80

# Test health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "cpp_engine_available": true,
  "components": {
    "orchestrator": "operational",
    "cpp_engine": "operational",
    "vector_db": "operational",
    "graph_rag": "operational",
    "mem0_system": "operational"
  }
}

# Test API documentation
open http://localhost:8000/docs

# Test report generation
curl -X POST http://localhost:8000/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Calculate the Sharpe ratio for monthly returns of 5%, -2%, 3%, 8%",
    "user_id": "test_user",
    "session_id": "test_session"
  }'
```

**Success Criteria:**
- ✅ All pods running
- ✅ Health endpoint returns "healthy"
- ✅ Report generation works end-to-end
- ✅ C++ calculations execute correctly
- ✅ API docs accessible

---

## Phase 3: Activate SOTA (Hybrid Goal)

### Step 3.1: Confirm Data Collection Active

Data collection is **enabled by default** in the production configuration.

```bash
# Check orchestrator logs
kubectl logs -n finrisk-ai -l app=finrisk-api | grep "Data collection"

# Look for:
# ✅ Data collection: ENABLED
# ✓ Training example collected (quality=0.95)
```

### Step 3.2: Monitor Training Data Collection

```bash
# SSH into a pod
kubectl exec -it -n finrisk-ai deployment/finrisk-api -- /bin/bash

# Check collection statistics
python3 -c "
from finrisk_ai.finetuning import TrainingDataCollector
collector = TrainingDataCollector()
stats = collector.get_statistics()
print(f'Total examples: {stats[\"total_examples\"]}')
print(f'Avg quality: {stats[\"average_quality_score\"]:.2f}')
"

# List collected batches
ls -lh data/training_examples/
```

**Target:** Collect 1000+ high-quality examples over 2-4 weeks.

### Step 3.3: Export and Prepare Data

Once you have 1000+ examples:

```bash
# SSH into pod
kubectl exec -it -n finrisk-ai deployment/finrisk-api -- /bin/bash

# Export for fine-tuning
python3 <<EOF
from finrisk_ai.finetuning import TrainingDataCollector

collector = TrainingDataCollector()
count = collector.export_for_finetuning(
    output_path="data/finetuning/training_data.jsonl",
    format="gemini",
    min_quality=0.9
)
print(f"Exported {count} examples")
EOF

# Prepare dataset
python3 <<EOF
from finrisk_ai.finetuning import FineTuningDataPreparator

preparator = FineTuningDataPreparator(validation_split=0.1)
dataset = preparator.prepare_dataset(
    input_path="data/finetuning/training_data.jsonl",
    output_dir="data/finetuning/prepared",
    min_examples=1000
)
print(f"Train: {dataset.train_size}, Val: {dataset.validation_size}")
EOF
```

### Step 3.4: Create Fine-Tuning Job

**IMPORTANT:** Gemini fine-tuning API is in limited preview. Apply for access at https://ai.google.dev/

```python
from finrisk_ai.finetuning import FineTunedModelManager
import os

manager = FineTunedModelManager(
    gemini_api_key=os.getenv("GEMINI_API_KEY")
)

job = manager.create_finetuning_job(
    base_model="gemini-1.5-flash",
    train_dataset_path="data/finetuning/prepared/train.jsonl",
    validation_dataset_path="data/finetuning/prepared/validation.jsonl",
    epochs=3
)

print(f"Fine-tuning job created: {job.job_id}")
print("Monitor progress in Google AI Studio")
```

**Wait Time:** Hours to days depending on dataset size.

### Step 3.5: Deploy Fine-Tuned Model

Once fine-tuning is complete:

```bash
# Get tuned model name from Gemini API
# Example: tunedModels/finrisk-v1-abc123

# Update ConfigMap
kubectl edit configmap finrisk-config -n finrisk-ai

# Set:
ENABLE_FINETUNING: "true"
# (FINETUNED_MODEL_NAME is added to secrets)

# Add model name to secrets
kubectl edit secret finrisk-secrets -n finrisk-ai

# Add (base64 encoded):
FINETUNED_MODEL_NAME: <base64_of_tunedModels/finrisk-v1-abc123>

# Restart pods to pick up new config
kubectl rollout restart deployment/finrisk-api -n finrisk-ai

# Verify fine-tuned model is active
kubectl logs -n finrisk-ai -l app=finrisk-ai | grep "Fine-tuning"

# Look for:
# ✅ Fine-tuning: ENABLED
# ✅ Fine-tuned model: tunedModels/finrisk-v1-abc123
```

### Step 3.6: Enable A/B Testing (Gradual Rollout)

```bash
# Start with 10% traffic to fine-tuned model
kubectl edit configmap finrisk-config -n finrisk-ai

# Set:
ENABLE_AB_TESTING: "true"
AB_TEST_TRAFFIC_SPLIT: "0.1"  # 10% to fine-tuned model

# Restart
kubectl rollout restart deployment/finrisk-api -n finrisk-ai

# Monitor metrics for 24-48 hours
# If metrics look good, increase gradually:
# 0.1 -> 0.3 -> 0.5 -> 1.0 (100%)
```

---

## Phase 4: Scale & Monitor (The Business)

### Step 4.1: Run Benchmarks

```bash
# Download benchmark results
kubectl cp finrisk-ai/finrisk-api-xxx:/app/data/reports/benchmark.json ./benchmark.json

# Run evaluation
python3 examples/phase5_complete_example.py

# Or manually:
python3 <<EOF
from finrisk_ai.finetuning import PerformanceEvaluator

evaluator = PerformanceEvaluator(
    test_cases_path="data/test_cases/benchmark_suite.json"
)

# Benchmark current system
# ... (see FINETUNING.md for full example)
EOF
```

**Target Metrics:**
- Accuracy: 98% (+11% over RAG-only)
- Relevance: 96%
- Consistency: 99%
- Latency: <2.5s

### Step 4.2: Monitor Production

```bash
# View metrics
kubectl top pods -n finrisk-ai
kubectl top nodes

# Check HPA status
kubectl get hpa -n finrisk-ai

# View logs
kubectl logs -n finrisk-ai -l app=finrisk-api -f | grep "ENABLED\|quality\|approach"

# Look for:
# ✓ Training example collected (quality=0.95)
# approach used: hybrid_rag_finetuning
```

### Step 4.3: Cost Optimization

Enable Redis caching (already configured):

```bash
# Verify Redis is connected
kubectl logs -n finrisk-ai -l app=finrisk-api | grep -i redis

# Monitor cache hits
kubectl exec -it -n finrisk-ai deployment/redis -- redis-cli INFO stats | grep hits
```

**Expected savings:** 70-80% reduction in Gemini API calls through caching.

### Step 4.4: Scale Based on Load

```bash
# Manual scaling
kubectl scale deployment/finrisk-api --replicas=10 -n finrisk-ai

# HPA is already configured:
# - Min: 2 replicas
# - Max: 10 replicas
# - Target CPU: 70%
# - Target Memory: 80%

# Monitor autoscaling
kubectl get hpa -n finrisk-ai -w
```

---

## Monitoring Checklist

Daily:
- [ ] Check pod health: `kubectl get pods -n finrisk-ai`
- [ ] Review error logs: `kubectl logs -n finrisk-ai -l app=finrisk-api --tail=100 | grep ERROR`
- [ ] Verify data collection: Check training example counts

Weekly:
- [ ] Review training data quality scores
- [ ] Monitor API latency and error rates
- [ ] Check database storage usage
- [ ] Review HPA scaling events

Monthly:
- [ ] Export training data for fine-tuning
- [ ] Run full benchmark suite
- [ ] Review and optimize costs
- [ ] Plan next fine-tuning cycle

---

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod -n finrisk-ai <pod-name>
kubectl logs -n finrisk-ai <pod-name>

# Common issues:
# - Image pull error: Check registry access
# - CrashLoopBackOff: Check GEMINI_API_KEY is set
# - Init containers failing: Check database connectivity
```

### C++ Engine Not Available

```bash
# Check if module exists in container
kubectl exec -it -n finrisk-ai deployment/finrisk-api -- ls -la /app/build/

# Should see: investool_engine.cpython-311-x86_64-linux-gnu.so

# If missing, rebuild Docker image with:
docker build --no-cache -t your-registry/finrisk-ai:1.0.1 .
```

### Data Collection Not Working

```bash
# Check orchestrator V2 is active
kubectl logs -n finrisk-ai -l app=finrisk-api | grep "OrchestratorV2"

# Check data collection enabled
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep DATA_COLLECTION

# Should show: ENABLE_DATA_COLLECTION: "true"
```

### Fine-Tuned Model Not Loading

```bash
# Check secrets
kubectl get secret finrisk-secrets -n finrisk-ai -o yaml

# Verify FINETUNED_MODEL_NAME is set
# Verify ENABLE_FINETUNING: "true" in ConfigMap

# Check logs for error
kubectl logs -n finrisk-ai -l app=finrisk-api | grep -i "fine"
```

---

## Success Metrics

### Phase 2 Success (Deployment)
- ✅ All 4 services running (API, PostgreSQL, Redis, Neo4j)
- ✅ Health endpoint returns "healthy"
- ✅ End-to-end report generation works
- ✅ C++ engine operational

### Phase 3 Success (SOTA Activation)
- ✅ 1000+ training examples collected
- ✅ Fine-tuned model deployed
- ✅ A/B testing active
- ✅ 98% accuracy target achieved

### Phase 4 Success (Production)
- ✅ <2.5s average latency
- ✅ 99.9% uptime
- ✅ Autoscaling functional
- ✅ Costs optimized with caching

---

## Next Steps

After successful deployment:

1. **Week 1-4:** Collect training data (target: 1000+ examples)
2. **Week 5:** Export data and create fine-tuning job
3. **Week 6:** Deploy fine-tuned model with A/B testing (10% traffic)
4. **Week 7:** Gradually increase traffic (30% → 50% → 100%)
5. **Week 8+:** Monitor, collect new data, plan next fine-tuning cycle

**Quarterly:** Retrain model with accumulated data for continuous improvement.

---

## Support

- **Documentation:** See `DEPLOYMENT.md`, `FINETUNING.md`, `API_DOCUMENTATION.md`
- **Issues:** https://github.com/Ru1vly/investool/issues
- **Gemini API:** https://ai.google.dev/

---

**Status: Ready for Production Launch! 🚀**
