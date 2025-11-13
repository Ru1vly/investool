#!/bin/bash
# ============================================================================
# Phase 3.3: Create Gemini Fine-Tuning Job
#
# This script creates a fine-tuning job using the Google Generative AI API.
# Requires: GEMINI_API_KEY environment variable
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 3.3: Create Fine-Tuning Job                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Configuration
# ============================================================================

TRAINING_DATA_FILE="${TRAINING_DATA_FILE:-}"
BASE_MODEL="${BASE_MODEL:-gemini-1.5-flash-002}"
EPOCHS="${EPOCHS:-5}"
BATCH_SIZE="${BATCH_SIZE:-4}"
LEARNING_RATE="${LEARNING_RATE:-0.001}"

# ============================================================================
# Check Prerequisites
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Checking Prerequisites"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check API key
if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ GEMINI_API_KEY environment variable not set"
    echo ""
    echo "Set your API key:"
    echo "  export GEMINI_API_KEY='your-api-key'"
    echo ""
    echo "Get your key from: https://makersuite.google.com/app/apikey"
    exit 1
fi
echo "✅ Gemini API key found"

# Check curl
if ! command -v curl &> /dev/null; then
    echo "❌ curl not found. Please install curl."
    exit 1
fi
echo "✅ curl found"

# Check jq (optional but helpful)
if command -v jq &> /dev/null; then
    echo "✅ jq found (for JSON formatting)"
    HAS_JQ=true
else
    echo "⚠️  jq not found (optional, output will be less formatted)"
    HAS_JQ=false
fi

echo ""

# ============================================================================
# Select Training Data
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Select Training Data File"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ -z "$TRAINING_DATA_FILE" ]; then
    # List available JSONL files
    echo "Available training data files:"
    echo ""

    JSONL_FILES=($(find training_data -name "training_set_*.jsonl" 2>/dev/null | sort -r))

    if [ ${#JSONL_FILES[@]} -eq 0 ]; then
        echo "❌ No training data files found in training_data/"
        echo ""
        echo "Run first:"
        echo "  ./scripts/finetuning/1-export-training-data.sh"
        echo "  ./scripts/finetuning/2-prepare-finetuning-dataset.py --input training_data/training_data_raw_*.json"
        exit 1
    fi

    for i in "${!JSONL_FILES[@]}"; do
        FILE=${JSONL_FILES[$i]}
        SIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE" 2>/dev/null)
        LINES=$(wc -l < "$FILE" | xargs)
        echo "  [$((i+1))] $FILE"
        echo "      Size: ${SIZE} bytes, Examples: ${LINES}"
    done

    echo ""
    read -p "Select file number [1]: " FILE_NUM
    FILE_NUM=${FILE_NUM:-1}

    if [ "$FILE_NUM" -lt 1 ] || [ "$FILE_NUM" -gt "${#JSONL_FILES[@]}" ]; then
        echo "❌ Invalid selection"
        exit 1
    fi

    TRAINING_DATA_FILE="${JSONL_FILES[$((FILE_NUM-1))]}"
fi

if [ ! -f "$TRAINING_DATA_FILE" ]; then
    echo "❌ Training data file not found: $TRAINING_DATA_FILE"
    exit 1
fi

EXAMPLE_COUNT=$(wc -l < "$TRAINING_DATA_FILE" | xargs)
echo "✅ Selected: $TRAINING_DATA_FILE"
echo "   Examples: $EXAMPLE_COUNT"
echo ""

# ============================================================================
# Configure Fine-Tuning Parameters
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Fine-Tuning Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Current configuration:"
echo "  • Base model: $BASE_MODEL"
echo "  • Epochs: $EPOCHS"
echo "  • Batch size: $BATCH_SIZE"
echo "  • Learning rate: $LEARNING_RATE"
echo ""

read -p "Use these settings? (y/n) [y]: " USE_DEFAULTS
USE_DEFAULTS=${USE_DEFAULTS:-y}

if [ "$USE_DEFAULTS" != "y" ]; then
    read -p "Base model [$BASE_MODEL]: " NEW_BASE_MODEL
    BASE_MODEL=${NEW_BASE_MODEL:-$BASE_MODEL}

    read -p "Epochs [$EPOCHS]: " NEW_EPOCHS
    EPOCHS=${NEW_EPOCHS:-$EPOCHS}

    read -p "Batch size [$BATCH_SIZE]: " NEW_BATCH_SIZE
    BATCH_SIZE=${NEW_BATCH_SIZE:-$BATCH_SIZE}

    read -p "Learning rate [$LEARNING_RATE]: " NEW_LEARNING_RATE
    LEARNING_RATE=${NEW_LEARNING_RATE:-$LEARNING_RATE}
fi

echo ""
echo "✅ Configuration confirmed"
echo ""

# ============================================================================
# Upload Training Data to Google Cloud Storage (via Gemini API)
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Uploading Training Data"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Uploading $TRAINING_DATA_FILE to Gemini File API..."

# Upload file to Gemini File API
UPLOAD_RESPONSE=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/upload/v1beta/files?key=$GEMINI_API_KEY" \
    -H "X-Goog-Upload-Protocol: multipart" \
    -F "metadata={\"file\":{\"displayName\":\"FinRisk Training Data\"}};type=application/json" \
    -F "file=@$TRAINING_DATA_FILE;type=application/jsonl")

# Check for errors
if echo "$UPLOAD_RESPONSE" | grep -q '"error"'; then
    echo "❌ Upload failed:"
    if [ "$HAS_JQ" = true ]; then
        echo "$UPLOAD_RESPONSE" | jq .
    else
        echo "$UPLOAD_RESPONSE"
    fi
    exit 1
fi

# Extract file URI
if [ "$HAS_JQ" = true ]; then
    FILE_URI=$(echo "$UPLOAD_RESPONSE" | jq -r '.file.uri // .name')
    FILE_NAME=$(echo "$UPLOAD_RESPONSE" | jq -r '.file.name // .name')
else
    FILE_URI=$(echo "$UPLOAD_RESPONSE" | grep -o '"uri":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$FILE_URI" ]; then
        FILE_URI=$(echo "$UPLOAD_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    fi
    FILE_NAME=$FILE_URI
fi

if [ -z "$FILE_URI" ]; then
    echo "❌ Could not extract file URI from response"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

echo "✅ Training data uploaded"
echo "   File URI: $FILE_URI"
echo ""

# Wait for file to be processed
echo "Waiting for file to be processed..."
sleep 5

# ============================================================================
# Create Fine-Tuning Job
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Creating Fine-Tuning Job"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Create tuning job request
TUNING_REQUEST=$(cat <<EOF
{
  "display_name": "FinRisk AI Fine-Tuning",
  "base_model": "models/${BASE_MODEL}",
  "training_dataset": {
    "examples": {
      "examples": {
        "file_uri": "${FILE_URI}"
      }
    }
  },
  "tuning_parameters": {
    "epochs": ${EPOCHS},
    "batch_size": ${BATCH_SIZE},
    "learning_rate": ${LEARNING_RATE}
  }
}
EOF
)

echo "Creating fine-tuning job with parameters:"
echo "$TUNING_REQUEST" | ([ "$HAS_JQ" = true ] && jq . || cat)
echo ""

# Submit tuning job
TUNING_RESPONSE=$(curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/tunedModels?key=$GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$TUNING_REQUEST")

# Check for errors
if echo "$TUNING_RESPONSE" | grep -q '"error"'; then
    echo "❌ Fine-tuning job creation failed:"
    if [ "$HAS_JQ" = true ]; then
        echo "$TUNING_RESPONSE" | jq .
    else
        echo "$TUNING_RESPONSE"
    fi
    exit 1
fi

# Extract tuned model name
if [ "$HAS_JQ" = true ]; then
    TUNED_MODEL_NAME=$(echo "$TUNING_RESPONSE" | jq -r '.name')
    STATE=$(echo "$TUNING_RESPONSE" | jq -r '.state')
else
    TUNED_MODEL_NAME=$(echo "$TUNING_RESPONSE" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
    STATE=$(echo "$TUNING_RESPONSE" | grep -o '"state":"[^"]*"' | head -1 | cut -d'"' -f4)
fi

echo "✅ Fine-tuning job created successfully!"
echo ""
echo "Model name: $TUNED_MODEL_NAME"
echo "State: $STATE"
echo ""

# ============================================================================
# Save Job Information
# ============================================================================

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_INFO_FILE="training_data/finetuning_job_${TIMESTAMP}.json"

cat > "$JOB_INFO_FILE" << EOF
{
  "created_at": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "tuned_model_name": "$TUNED_MODEL_NAME",
  "base_model": "$BASE_MODEL",
  "training_data_file": "$TRAINING_DATA_FILE",
  "example_count": $EXAMPLE_COUNT,
  "parameters": {
    "epochs": $EPOCHS,
    "batch_size": $BATCH_SIZE,
    "learning_rate": $LEARNING_RATE
  },
  "file_uri": "$FILE_URI",
  "initial_state": "$STATE"
}
EOF

echo "Job information saved: $JOB_INFO_FILE"
echo ""

# ============================================================================
# Monitor Job Status
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Monitoring Fine-Tuning Job"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Fine-tuning can take 30 minutes to several hours."
echo ""
read -p "Monitor job status now? (y/n) [y]: " MONITOR
MONITOR=${MONITOR:-y}

if [ "$MONITOR" = "y" ]; then
    echo ""
    echo "Checking job status (Ctrl+C to stop monitoring)..."
    echo ""

    while true; do
        STATUS_RESPONSE=$(curl -s -X GET \
            "https://generativelanguage.googleapis.com/v1beta/${TUNED_MODEL_NAME}?key=$GEMINI_API_KEY")

        if [ "$HAS_JQ" = true ]; then
            CURRENT_STATE=$(echo "$STATUS_RESPONSE" | jq -r '.state')
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] State: $CURRENT_STATE"
        else
            CURRENT_STATE=$(echo "$STATUS_RESPONSE" | grep -o '"state":"[^"]*"' | cut -d'"' -f4)
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] State: $CURRENT_STATE"
        fi

        # Check if completed
        if [ "$CURRENT_STATE" = "ACTIVE" ]; then
            echo ""
            echo "🎉 Fine-tuning completed successfully!"
            echo ""
            echo "Tuned model: $TUNED_MODEL_NAME"
            echo ""
            break
        elif [ "$CURRENT_STATE" = "FAILED" ]; then
            echo ""
            echo "❌ Fine-tuning failed"
            if [ "$HAS_JQ" = true ]; then
                echo "$STATUS_RESPONSE" | jq .
            else
                echo "$STATUS_RESPONSE"
            fi
            exit 1
        fi

        sleep 60  # Check every minute
    done
fi

# ============================================================================
# Summary
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Fine-Tuning Job Created!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Tuned Model Name:"
echo "  $TUNED_MODEL_NAME"
echo ""
echo "Check status anytime with:"
echo "  curl -s \"https://generativelanguage.googleapis.com/v1beta/${TUNED_MODEL_NAME}?key=\$GEMINI_API_KEY\" | jq ."
echo ""
echo "Next steps:"
echo "  1. Wait for fine-tuning to complete (state: ACTIVE)"
echo "  2. Run: ./scripts/finetuning/4-deploy-finetuned-model.sh"
echo "  3. Update secrets with tuned model name"
echo "  4. Deploy with A/B testing enabled"
echo ""
