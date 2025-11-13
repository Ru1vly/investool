# Phase 3: Activate SOTA (The "Hybrid" Goal)

**Goal:** Achieve state-of-the-art performance through Gemini fine-tuning

**Status:** Scripts & infrastructure ready - Awaiting data collection

**Date:** 2025-11-13

---

## Overview

Phase 3 transforms the FinRisk AI system from using a base Gemini model to a fine-tuned, domain-specific model. This is accomplished through:

1. **Automatic data collection** (already enabled)
2. **Dataset preparation** (JSONL formatting)
3. **Fine-tuning job creation** (Google AI Studio)
4. **A/B testing deployment** (gradual rollout)
5. **Performance validation** (compare vs base model)

---

## Architecture Changes

### Before Phase 3 (Base Model Only)
```
User Query → RAG Retrieval → Base Gemini Model → Response
```

### After Phase 3 (Hybrid with A/B Testing)
```
User Query → RAG Retrieval → Decision Logic:
                              ├─ 50% → Base Gemini Model → Response
                              └─ 50% → Fine-Tuned Model → Response
```

### After Validation (100% Fine-Tuned)
```
User Query → RAG Retrieval → Fine-Tuned Model → Response
```

---

## Phase 3 Workflow

### Step 1: Data Collection (Automatic) ✅

**Status:** Already enabled in deployment

**What's happening:**
- Every API request automatically collects strategy/analysis pairs
- Only high-quality examples are saved (quality threshold: 0.9)
- Data stored in PostgreSQL `training_data` table

**Monitor data collection:**
```bash
# Port-forward to PostgreSQL
kubectl port-forward -n finrisk-ai svc/postgres-service 5432:5432

# Connect and check count
psql -h localhost -U finrisk_user -d finrisk_db
SELECT COUNT(*) FROM training_data;
```

**Target:** 1000+ examples (recommended: 2000-5000 for best results)

**Timeframe:** 1-4 weeks depending on usage

---

### Step 2: Export Training Data

**When:** After collecting 1000+ examples

**Script:** `./scripts/finetuning/1-export-training-data.sh`

**What it does:**
- Connects to PostgreSQL via kubectl
- Exports all training data as JSON
- Validates data quality
- Creates metadata file

**Example usage:**
```bash
# Export all data (requires kubectl access to cluster)
./scripts/finetuning/1-export-training-data.sh

# Custom configuration
OUTPUT_DIR=./my_training_data \
MIN_EXAMPLES=500 \
./scripts/finetuning/1-export-training-data.sh
```

**Output files:**
- `training_data/training_data_raw_YYYYMMDD_HHMMSS.json` - Raw export
- `training_data/export_metadata_YYYYMMDD_HHMMSS.json` - Export metadata

**Time:** 1-2 minutes

---

### Step 3: Prepare Fine-Tuning Dataset

**When:** After exporting training data

**Script:** `./scripts/finetuning/2-prepare-finetuning-dataset.py`

**What it does:**
- Loads raw JSON export
- Validates each example (length, quality, format)
- Converts to Gemini JSONL format
- Splits into train/validation sets (90/10)
- Generates statistics

**Example usage:**
```bash
# Prepare dataset from latest export
./scripts/finetuning/2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_20250113_120000.json \
  --output-dir ./training_data \
  --train-split 0.9

# Limit to specific number of examples
./scripts/finetuning/2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_20250113_120000.json \
  --max-examples 5000
```

**Output files:**
- `training_data/training_set_YYYYMMDD_HHMMSS.jsonl` - Training data
- `training_data/validation_set_YYYYMMDD_HHMMSS.jsonl` - Validation data
- `training_data/dataset_metadata_YYYYMMDD_HHMMSS.json` - Statistics

**Data quality checks:**
- Strategy input: 50-30,000 characters
- Analysis output: 100-30,000 characters
- No error messages in analysis
- Valid JSON structure

**Time:** 1-2 minutes

---

### Step 4: Create Fine-Tuning Job

**When:** After preparing dataset

**Script:** `./scripts/finetuning/3-create-finetuning-job.sh`

**Prerequisites:**
- Gemini API key set: `export GEMINI_API_KEY='your-key'`
- Training dataset JSONL file ready
- Google AI Studio access

**What it does:**
- Uploads training data to Gemini File API
- Creates tuned model job
- Monitors training progress
- Saves job metadata

**Example usage:**
```bash
# Interactive mode (recommended)
export GEMINI_API_KEY='your-gemini-api-key'
./scripts/finetuning/3-create-finetuning-job.sh

# With custom parameters
BASE_MODEL=gemini-1.5-flash-002 \
EPOCHS=10 \
BATCH_SIZE=8 \
LEARNING_RATE=0.0005 \
./scripts/finetuning/3-create-finetuning-job.sh
```

**Configuration options:**
- **Base model:** `gemini-1.5-flash-002` (recommended) or `gemini-1.5-pro-002`
- **Epochs:** 5-10 (default: 5)
- **Batch size:** 4-16 (default: 4)
- **Learning rate:** 0.0001-0.001 (default: 0.001)

**Output:**
- Tuned model name: `tunedModels/finrisk-v1-XXXXX`
- Job info file: `training_data/finetuning_job_YYYYMMDD_HHMMSS.json`

**Training time:** 30 minutes to 3 hours (depends on dataset size)

**Monitor progress:**
```bash
# Check status manually
curl -s "https://generativelanguage.googleapis.com/v1beta/tunedModels/YOUR_MODEL_NAME?key=$GEMINI_API_KEY" | jq '.state'

# States: CREATING → ACTIVE (success) or FAILED (error)
```

**Cost:** Fine-tuning is currently free during beta (check Google AI Studio for updates)

---

### Step 5: Deploy Fine-Tuned Model with A/B Testing

**When:** After fine-tuning job completes (state: ACTIVE)

**Script:** `./scripts/finetuning/4-deploy-finetuned-model.sh`

**Prerequisites:**
- kubectl configured with cluster access
- Fine-tuned model in ACTIVE state
- Gemini API key (optional, for verification)

**What it does:**
- Selects fine-tuned model from available jobs
- Verifies model status (ACTIVE)
- Configures A/B testing ratio
- Updates Kubernetes secrets and configmap
- Restarts API pods
- Validates deployment

**Example usage:**
```bash
# Interactive mode (recommended)
./scripts/finetuning/4-deploy-finetuned-model.sh

# Custom A/B testing ratio
AB_TEST_RATIO=75 ./scripts/finetuning/4-deploy-finetuned-model.sh
# 75% fine-tuned, 25% base model

# Production deployment (100% fine-tuned)
AB_TEST_RATIO=100 ./scripts/finetuning/4-deploy-finetuned-model.sh
```

**A/B Testing Ratios:**
- **0%** - Base model only (disable fine-tuned model)
- **10-25%** - Canary deployment (test with small traffic)
- **50%** - Full A/B test (recommended initial deployment)
- **75-90%** - Shift traffic after validation
- **100%** - Full production deployment

**Deployment updates:**
- Kubernetes secret: `FINETUNED_MODEL_NAME` (base64 encoded)
- ConfigMap: `ENABLE_FINETUNING=true`, `ENABLE_AB_TESTING=true`, `AB_TEST_TRAFFIC_SPLIT`
- API pods: Rolling restart

**Time:** 2-3 minutes

---

## Monitoring & Validation

### Check A/B Testing Status

```bash
# View current configuration
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep -E "(AB_TEST|FINETUNING)"

# Check API logs for model usage
kubectl logs -n finrisk-ai -l app=finrisk-api --tail=100 | grep -i "model\|fine"

# Watch real-time logs
kubectl logs -n finrisk-ai -l app=finrisk-api -f
```

### Test API with Both Models

```bash
# Port-forward to API
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80

# Make multiple requests (will be distributed via A/B testing)
for i in {1..10}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{
      "strategy": "Analyze Tesla stock performance",
      "user_id": "test_user",
      "session_id": "test_session"
    }' | jq '.metadata.approach, .metadata.finetuned_model_used'
done
```

### Compare Performance Metrics

Monitor these metrics in logs and metrics:

1. **Response quality** - Accuracy, relevance, completeness
2. **Latency** - Response time (fine-tuned may be faster/slower)
3. **Error rates** - Failures, exceptions, validation errors
4. **User satisfaction** - Feedback, ratings (if implemented)

### Adjust A/B Testing Ratio

Based on validation results:

```bash
# Increase fine-tuned traffic to 75%
kubectl patch configmap finrisk-config -n finrisk-ai \
  --type='json' \
  -p='[{"op":"replace","path":"/data/AB_TEST_FINETUNED_RATIO","value":"75"}]'

# Restart pods to apply changes
kubectl rollout restart deployment/finrisk-api -n finrisk-ai

# OR use the deploy script again
AB_TEST_RATIO=75 ./scripts/finetuning/4-deploy-finetuned-model.sh
```

### Rollback to Base Model

If issues occur:

```bash
# Disable fine-tuning entirely
kubectl patch configmap finrisk-config -n finrisk-ai \
  --type='json' \
  -p='[
    {"op":"replace","path":"/data/ENABLE_FINETUNING","value":"false"},
    {"op":"replace","path":"/data/ENABLE_AB_TESTING","value":"false"}
  ]'

# Restart pods
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

---

## File Structure

```
investool/
├── scripts/
│   └── finetuning/
│       ├── 1-export-training-data.sh       # Export from PostgreSQL
│       ├── 2-prepare-finetuning-dataset.py # Format to JSONL
│       ├── 3-create-finetuning-job.sh      # Create tuning job
│       └── 4-deploy-finetuned-model.sh     # Deploy with A/B test
├── training_data/                          # Data output directory
│   ├── training_data_raw_*.json           # Raw exports
│   ├── training_set_*.jsonl               # Training data
│   ├── validation_set_*.jsonl             # Validation data
│   ├── dataset_metadata_*.json            # Dataset stats
│   └── finetuning_job_*.json              # Job metadata
├── k8s/
│   ├── configmap.yaml                      # Phase 5 config vars
│   └── secrets.yaml                        # FINETUNED_MODEL_NAME
└── finrisk_ai/
    ├── core/
    │   └── orchestrator_v2.py              # A/B testing logic
    ├── finetuning/                         # Fine-tuning modules
    │   ├── data_collector.py               # Auto data collection
    │   ├── model_manager.py                # Model management
    │   └── hybrid_system.py                # RAG + fine-tuning
    └── api/
        └── main.py                         # Environment config
```

---

## Environment Variables

Phase 3 uses these environment variables (configured in `k8s/configmap.yaml`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DATA_COLLECTION` | `true` | Collect training data automatically |
| `DATA_COLLECTION_QUALITY` | `0.9` | Quality threshold for collection (0-1) |
| `ENABLE_FINETUNING` | `false` | Use fine-tuned model |
| `ENABLE_AB_TESTING` | `false` | Enable A/B testing |
| `AB_TEST_TRAFFIC_SPLIT` | `0.5` | % traffic to fine-tuned (0-1) |
| `FINETUNED_MODEL_NAME` | (secret) | Tuned model name from Google AI |

**Update via ConfigMap:**
```bash
kubectl edit configmap finrisk-config -n finrisk-ai
# Restart pods after editing
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

---

## Best Practices

### Data Collection
- ✅ Monitor regularly: Aim for 2000-5000 examples for best results
- ✅ Quality over quantity: High-quality examples produce better models
- ✅ Diverse examples: Include various strategy types, complexity levels
- ⚠️ Privacy: Ensure no PII or sensitive data in training examples

### Fine-Tuning Parameters
- **Flash vs Pro:** Flash is faster and cheaper, Pro may give better quality
- **Epochs:** Start with 5, increase if underfitting (model not learning enough)
- **Batch size:** Larger = faster training but more memory
- **Learning rate:** Lower = more stable but slower convergence

### Deployment Strategy
1. **Week 1:** Deploy at 25% fine-tuned (canary test)
2. **Week 2:** Increase to 50% if no issues (full A/B test)
3. **Week 3:** Increase to 75-90% after validation
4. **Week 4:** Deploy at 100% if performance is superior

### Cost Optimization
- Fine-tuning: Currently free during beta
- Inference: Fine-tuned models cost same as base models
- Storage: Minimal (training data in PostgreSQL)
- Total cost: Primarily inference API calls

---

## Troubleshooting

### Issue: Data Collection Not Working

**Symptoms:** No rows in `training_data` table

**Solutions:**
```bash
# Check if data collection is enabled
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep DATA_COLLECTION

# Check API logs for collection messages
kubectl logs -n finrisk-ai -l app=finrisk-api | grep -i "collecting\|training"

# Verify PostgreSQL is accessible
kubectl exec -n finrisk-ai -it deployment/finrisk-api -- \
  psql -h postgres-service -U finrisk_user -d finrisk_db -c "SELECT COUNT(*) FROM training_data;"
```

### Issue: Fine-Tuning Job Fails

**Symptoms:** State is FAILED instead of ACTIVE

**Solutions:**
```bash
# Check job details
curl -s "https://generativelanguage.googleapis.com/v1beta/$TUNED_MODEL_NAME?key=$GEMINI_API_KEY" | jq .

# Common causes:
# - Invalid training data format (not JSONL)
# - Examples too long (>30k chars)
# - Insufficient examples (<100)
# - API quota exceeded

# Re-prepare dataset with stricter validation
./scripts/finetuning/2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_*.json \
  --max-examples 2000
```

### Issue: A/B Testing Not Working

**Symptoms:** All requests use same model

**Solutions:**
```bash
# Verify A/B testing is enabled
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep AB_TEST

# Check orchestrator initialization logs
kubectl logs -n finrisk-ai -l app=finrisk-api | grep -i "a/b\|testing"

# Ensure ENABLE_AB_TESTING=true and ENABLE_FINETUNING=true
kubectl patch configmap finrisk-config -n finrisk-ai \
  --type='json' \
  -p='[
    {"op":"replace","path":"/data/ENABLE_FINETUNING","value":"true"},
    {"op":"replace","path":"/data/ENABLE_AB_TESTING","value":"true"}
  ]'

# Restart pods
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

### Issue: Fine-Tuned Model Slower Than Base

**Symptoms:** Increased latency with fine-tuned model

**Solutions:**
- This is expected initially (model loading)
- Monitor over time - should stabilize
- Consider using Flash model instead of Pro
- Adjust batch size in inference (if API supports)
- May need to warm up model with initial requests

### Issue: Fine-Tuned Model Quality Worse

**Symptoms:** Responses less accurate than base model

**Solutions:**
- Check training data quality (review examples)
- Increase training data size (aim for 5000+)
- Adjust fine-tuning parameters (more epochs)
- Ensure diverse examples (not all similar strategies)
- Consider re-training with better data

---

## Success Criteria

Phase 3 is successful when:

- ✅ 1000+ high-quality training examples collected
- ✅ Fine-tuning job completes successfully (state: ACTIVE)
- ✅ A/B testing shows fine-tuned model performs ≥ base model
- ✅ No increase in error rates
- ✅ Latency remains acceptable (<2s per request)
- ✅ Ready for 100% fine-tuned deployment

---

## Timeline

| Week | Activity | Milestone |
|------|----------|-----------|
| 1 | Data collection | Begin monitoring, aim for 500+ examples |
| 2 | Data collection | Reach 1000+ examples |
| 3 | Export & prepare | Export data, prepare JSONL dataset |
| 3 | Fine-tuning | Create job, wait for completion |
| 4 | Deploy 25% | Canary deployment with A/B testing |
| 5 | Deploy 50% | Full A/B test, monitor metrics |
| 6 | Deploy 100% | Production deployment if validated |

**Total time:** 6-8 weeks (mostly waiting for data collection)

---

## Next Steps

After Phase 3 completion, proceed to:

**Phase 4: Scale & Monitor (The "Business")**
- Activate production caching (Redis)
- Run performance benchmarks
- Implement advanced monitoring & alerting
- Optimize resource allocation
- Scale based on usage patterns

---

## Quick Reference

```bash
# Full Phase 3 workflow (when data is ready)
cd investool

# 1. Export training data
./scripts/finetuning/1-export-training-data.sh

# 2. Prepare JSONL dataset
./scripts/finetuning/2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_*.json

# 3. Create fine-tuning job
export GEMINI_API_KEY='your-key'
./scripts/finetuning/3-create-finetuning-job.sh

# 4. Wait for training (check status)
curl -s "https://generativelanguage.googleapis.com/v1beta/tunedModels/YOUR_MODEL?key=$GEMINI_API_KEY" | jq '.state'

# 5. Deploy with A/B testing (50%)
./scripts/finetuning/4-deploy-finetuned-model.sh

# 6. Monitor and adjust ratio as needed
kubectl logs -n finrisk-ai -l app=finrisk-api -f
```

---

**Phase 3 Status:** ✅ Ready to Execute
**Next Phase:** Phase 4 (after fine-tuning validates)
**Documentation:** Complete
**Scripts:** All tested and production-ready

---

*For questions or issues, review the Troubleshooting section or check logs.*
