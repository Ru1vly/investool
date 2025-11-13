# Phase 3: Fine-Tuning Scripts

This directory contains scripts for implementing Phase 3: Activate SOTA (State-of-the-Art).

## Overview

Phase 3 transforms the FinRisk AI system to use a fine-tuned Gemini model instead of the base model, achieving domain-specific performance improvements.

## Scripts

### 1. Export Training Data
**File:** `1-export-training-data.sh`

**Purpose:** Export collected training data from PostgreSQL

**Prerequisites:**
- kubectl configured with cluster access
- PostgreSQL pod running in Kubernetes
- Training data collected (1000+ examples recommended)

**Usage:**
```bash
./1-export-training-data.sh

# With custom configuration
OUTPUT_DIR=./my_data MIN_EXAMPLES=500 ./1-export-training-data.sh
```

**Outputs:**
- `training_data/training_data_raw_YYYYMMDD_HHMMSS.json`
- `training_data/export_metadata_YYYYMMDD_HHMMSS.json`

**Time:** 1-2 minutes

---

### 2. Prepare Fine-Tuning Dataset
**File:** `2-prepare-finetuning-dataset.py`

**Purpose:** Convert raw JSON to Gemini JSONL format with validation

**Prerequisites:**
- Python 3.8+
- Raw training data export

**Usage:**
```bash
./2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_20250113_120000.json \
  --output-dir training_data \
  --train-split 0.9

# Limit examples
./2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_*.json \
  --max-examples 5000
```

**Options:**
- `--input`: Input JSON file from export (required)
- `--output-dir`: Output directory (default: ./training_data)
- `--max-examples`: Maximum examples to include
- `--train-split`: Train/validation split ratio (default: 0.9)

**Outputs:**
- `training_data/training_set_YYYYMMDD_HHMMSS.jsonl`
- `training_data/validation_set_YYYYMMDD_HHMMSS.jsonl`
- `training_data/dataset_metadata_YYYYMMDD_HHMMSS.json`

**Data Validation:**
- Strategy: 50-30,000 characters
- Analysis: 100-30,000 characters
- No error messages
- Valid JSON structure

**Time:** 1-2 minutes

---

### 3. Create Fine-Tuning Job
**File:** `3-create-finetuning-job.sh`

**Purpose:** Upload training data and create Gemini fine-tuning job

**Prerequisites:**
- Gemini API key: `export GEMINI_API_KEY='your-key'`
- Training dataset JSONL file
- curl and jq installed

**Usage:**
```bash
# Interactive mode (recommended)
export GEMINI_API_KEY='your-gemini-api-key'
./3-create-finetuning-job.sh

# With custom parameters
BASE_MODEL=gemini-1.5-flash-002 \
EPOCHS=10 \
BATCH_SIZE=8 \
LEARNING_RATE=0.0005 \
./3-create-finetuning-job.sh
```

**Configuration:**
- `BASE_MODEL`: Base model to fine-tune (default: gemini-1.5-flash-002)
- `EPOCHS`: Training epochs (default: 5)
- `BATCH_SIZE`: Batch size (default: 4)
- `LEARNING_RATE`: Learning rate (default: 0.001)

**Outputs:**
- Tuned model name: `tunedModels/finrisk-v1-XXXXX`
- `training_data/finetuning_job_YYYYMMDD_HHMMSS.json`

**Training Time:** 30 minutes to 3 hours

**Monitor Progress:**
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/tunedModels/YOUR_MODEL?key=$GEMINI_API_KEY" | jq '.state'
```

---

### 4. Deploy Fine-Tuned Model
**File:** `4-deploy-finetuned-model.sh`

**Purpose:** Deploy fine-tuned model with A/B testing

**Prerequisites:**
- kubectl configured with cluster access
- Fine-tuned model in ACTIVE state
- FinRisk AI deployed to Kubernetes

**Usage:**
```bash
# Interactive mode (recommended)
./4-deploy-finetuned-model.sh

# Custom A/B testing ratio
AB_TEST_RATIO=75 ./4-deploy-finetuned-model.sh
# 75% fine-tuned, 25% base model

# Production deployment (100% fine-tuned)
AB_TEST_RATIO=100 ./4-deploy-finetuned-model.sh
```

**A/B Testing Ratios:**
- **0%** - Base model only (disable fine-tuning)
- **25%** - Canary deployment
- **50%** - Full A/B test (recommended)
- **75%** - Shift traffic after validation
- **100%** - Full production

**Actions:**
- Updates Kubernetes secret with model name
- Configures A/B testing in ConfigMap
- Restarts API pods
- Validates deployment

**Time:** 2-3 minutes

---

## Workflow

### Complete Phase 3 Execution

```bash
# Prerequisites
export GEMINI_API_KEY='your-gemini-api-key'
cd /path/to/investool

# Step 1: Export training data (when 1000+ examples collected)
./scripts/finetuning/1-export-training-data.sh

# Step 2: Prepare JSONL dataset
./scripts/finetuning/2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_*.json

# Step 3: Create fine-tuning job
./scripts/finetuning/3-create-finetuning-job.sh

# Step 4: Wait for training to complete
# Check status: https://aistudio.google.com/app/apikey (Tuned Models section)
# Or via API:
curl -s "https://generativelanguage.googleapis.com/v1beta/tunedModels/YOUR_MODEL?key=$GEMINI_API_KEY" | jq '.state'

# Step 5: Deploy with A/B testing
./scripts/finetuning/4-deploy-finetuned-model.sh

# Step 6: Monitor and adjust
kubectl logs -n finrisk-ai -l app=finrisk-api -f
```

---

## Output Directory Structure

```
training_data/
├── training_data_raw_20250113_120000.json      # Raw export
├── export_metadata_20250113_120000.json        # Export metadata
├── training_set_20250113_121500.jsonl          # Training JSONL
├── validation_set_20250113_121500.jsonl        # Validation JSONL
├── dataset_metadata_20250113_121500.json       # Dataset stats
└── finetuning_job_20250113_123000.json         # Job metadata
```

---

## Environment Variables

Phase 3 uses these Kubernetes environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_DATA_COLLECTION` | `true` | Auto-collect training data |
| `DATA_COLLECTION_QUALITY` | `0.9` | Quality threshold (0-1) |
| `ENABLE_FINETUNING` | `false` | Use fine-tuned model |
| `ENABLE_AB_TESTING` | `false` | Enable A/B testing |
| `AB_TEST_TRAFFIC_SPLIT` | `0.5` | % to fine-tuned (0-1) |
| `FINETUNED_MODEL_NAME` | (secret) | Model name from Google AI |

**Update ConfigMap:**
```bash
kubectl edit configmap finrisk-config -n finrisk-ai
kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

---

## Monitoring

### Check Data Collection

```bash
# Port-forward to PostgreSQL
kubectl port-forward -n finrisk-ai svc/postgres-service 5432:5432

# Check count
psql -h localhost -U finrisk_user -d finrisk_db -c "SELECT COUNT(*) FROM training_data;"

# View recent examples
psql -h localhost -U finrisk_user -d finrisk_db -c "SELECT id, LENGTH(strategy_input), LENGTH(analysis_output), created_at FROM training_data ORDER BY created_at DESC LIMIT 10;"
```

### Check Fine-Tuning Job Status

```bash
# Via API
curl -s "https://generativelanguage.googleapis.com/v1beta/tunedModels/YOUR_MODEL?key=$GEMINI_API_KEY" | jq '.state'

# Via Google AI Studio
# Visit: https://aistudio.google.com/app/apikey
# Click "Tuned Models" section
```

### Check A/B Testing

```bash
# View current configuration
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep -E "(AB_TEST|FINETUNING)"

# Check API logs
kubectl logs -n finrisk-ai -l app=finrisk-api | grep -i "model\|fine"

# Watch real-time
kubectl logs -n finrisk-ai -l app=finrisk-api -f
```

---

## Troubleshooting

### Issue: Not Enough Training Data

**Solution:** Wait longer or adjust threshold
```bash
# Lower quality threshold temporarily
kubectl patch configmap finrisk-config -n finrisk-ai \
  --type='json' \
  -p='[{"op":"replace","path":"/data/DATA_COLLECTION_QUALITY","value":"0.8"}]'

kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

### Issue: Fine-Tuning Job Fails

**Common causes:**
- Invalid JSONL format
- Examples too long (>30k chars)
- Too few examples (<100)
- API quota exceeded

**Solution:** Re-prepare dataset with stricter validation
```bash
./2-prepare-finetuning-dataset.py \
  --input training_data/training_data_raw_*.json \
  --max-examples 2000
```

### Issue: A/B Testing Not Working

**Solution:** Verify configuration
```bash
# Check both are enabled
kubectl get configmap finrisk-config -n finrisk-ai -o yaml | grep -E "(ENABLE_FINETUNING|ENABLE_AB_TESTING)"

# Should show:
# ENABLE_FINETUNING: "true"
# ENABLE_AB_TESTING: "true"

# If not, update and restart
kubectl patch configmap finrisk-config -n finrisk-ai \
  --type='json' \
  -p='[
    {"op":"replace","path":"/data/ENABLE_FINETUNING","value":"true"},
    {"op":"replace","path":"/data/ENABLE_AB_TESTING","value":"true"}
  ]'

kubectl rollout restart deployment/finrisk-api -n finrisk-ai
```

### Issue: Script Permission Denied

**Solution:** Make scripts executable
```bash
chmod +x scripts/finetuning/*.sh
chmod +x scripts/finetuning/*.py
```

---

## Best Practices

1. **Data Collection**
   - Aim for 2000-5000 examples for best results
   - Monitor quality regularly
   - Ensure diverse strategy types

2. **Fine-Tuning Parameters**
   - Start with defaults (5 epochs, batch size 4)
   - Use Flash model for faster/cheaper training
   - Increase epochs if model is underfitting

3. **Deployment Strategy**
   - Week 1: 25% fine-tuned (canary)
   - Week 2: 50% (full A/B test)
   - Week 3: 75% (after validation)
   - Week 4: 100% (if performance is better)

4. **Monitoring**
   - Watch logs for errors
   - Compare latency (base vs fine-tuned)
   - Track accuracy improvements
   - Monitor user feedback

---

## Cost

- **Fine-tuning:** Currently free during beta
- **Inference:** Same cost as base model
- **Storage:** Minimal (PostgreSQL only)

---

## Support

For detailed documentation, see: `PHASE3_GUIDE.md`

For issues:
1. Check logs: `kubectl logs -n finrisk-ai -l app=finrisk-api`
2. Review error messages in script output
3. Verify prerequisites are met
4. Consult troubleshooting section above

---

**Status:** ✅ All scripts ready for production use
**Last Updated:** 2025-11-13
