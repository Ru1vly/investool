#!/bin/bash
# ============================================================================
# Phase 3.1: Export Training Data from PostgreSQL
#
# This script exports collected strategy/analysis pairs from the database
# for use in fine-tuning the Gemini model.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 3.1: Export Training Data                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Configuration
# ============================================================================

OUTPUT_DIR="${OUTPUT_DIR:-./training_data}"
MIN_EXAMPLES="${MIN_EXAMPLES:-1000}"
NAMESPACE="${NAMESPACE:-finrisk-ai}"
POD_SELECTOR="${POD_SELECTOR:-app=postgres}"

# ============================================================================
# Check Prerequisites
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Checking Prerequisites"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi
echo "✅ kubectl found"

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi
echo "✅ Connected to cluster: $(kubectl config current-context)"

# Check namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "❌ Namespace $NAMESPACE not found"
    exit 1
fi
echo "✅ Namespace $NAMESPACE exists"

# Check PostgreSQL pod is running
POSTGRES_POD=$(kubectl get pods -n "$NAMESPACE" -l "$POD_SELECTOR" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -z "$POSTGRES_POD" ]; then
    echo "❌ PostgreSQL pod not found"
    exit 1
fi

POD_STATUS=$(kubectl get pod "$POSTGRES_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
if [ "$POD_STATUS" != "Running" ]; then
    echo "❌ PostgreSQL pod is not running (status: $POD_STATUS)"
    exit 1
fi
echo "✅ PostgreSQL pod running: $POSTGRES_POD"

# Load database password from secrets
echo ""
echo "Loading database credentials from secrets..."
DB_PASSWORD=$(kubectl get secret finrisk-secrets -n "$NAMESPACE" -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Could not retrieve database password from secrets"
    exit 1
fi
echo "✅ Database credentials loaded"

echo ""

# ============================================================================
# Check Data Availability
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Checking Data Availability"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Count total examples
TOTAL_COUNT=$(kubectl exec -n "$NAMESPACE" "$POSTGRES_POD" -- \
    psql -U finrisk_user -d finrisk_db -t -c \
    "SELECT COUNT(*) FROM training_data;" 2>/dev/null | xargs)

echo "Total examples collected: $TOTAL_COUNT"

if [ "$TOTAL_COUNT" -lt "$MIN_EXAMPLES" ]; then
    echo ""
    echo "⚠️  Warning: Only $TOTAL_COUNT examples available"
    echo "   Recommended minimum: $MIN_EXAMPLES examples"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Export cancelled. Wait for more data to be collected."
        exit 0
    fi
fi

# Show data quality statistics
echo ""
echo "Data quality statistics:"
kubectl exec -n "$NAMESPACE" "$POSTGRES_POD" -- \
    psql -U finrisk_user -d finrisk_db -c \
    "SELECT
        COUNT(*) as total,
        AVG(LENGTH(strategy_input)) as avg_strategy_length,
        AVG(LENGTH(analysis_output)) as avg_analysis_length,
        MIN(created_at) as earliest,
        MAX(created_at) as latest
    FROM training_data;"

echo ""

# ============================================================================
# Export Data
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Exporting Data"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo "Output directory: $OUTPUT_DIR"

# Export timestamp
EXPORT_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RAW_FILE="$OUTPUT_DIR/training_data_raw_${EXPORT_TIMESTAMP}.json"

echo "Exporting to: $RAW_FILE"
echo ""

# Export data as JSON
kubectl exec -n "$NAMESPACE" "$POSTGRES_POD" -- \
    psql -U finrisk_user -d finrisk_db -t -A -c \
    "SELECT json_agg(row_to_json(t))
    FROM (
        SELECT
            id,
            strategy_input,
            analysis_output,
            model_used,
            execution_time_ms,
            created_at
        FROM training_data
        ORDER BY created_at DESC
    ) t;" > "$RAW_FILE"

if [ ! -f "$RAW_FILE" ] || [ ! -s "$RAW_FILE" ]; then
    echo "❌ Export failed - no data written"
    exit 1
fi

EXPORTED_SIZE=$(stat -f%z "$RAW_FILE" 2>/dev/null || stat -c%s "$RAW_FILE" 2>/dev/null)
echo "✅ Exported $TOTAL_COUNT examples (${EXPORTED_SIZE} bytes)"

# ============================================================================
# Data Validation
# ============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Validating Export"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check JSON validity
if command -v python3 &> /dev/null; then
    if python3 -c "import json; json.load(open('$RAW_FILE'))" 2>/dev/null; then
        echo "✅ JSON format valid"
    else
        echo "❌ Invalid JSON format"
        exit 1
    fi
else
    echo "⚠️  Python3 not found, skipping JSON validation"
fi

# Create metadata file
METADATA_FILE="$OUTPUT_DIR/export_metadata_${EXPORT_TIMESTAMP}.json"
cat > "$METADATA_FILE" << EOF
{
  "export_timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "total_examples": $TOTAL_COUNT,
  "raw_file": "$(basename $RAW_FILE)",
  "namespace": "$NAMESPACE",
  "postgres_pod": "$POSTGRES_POD",
  "min_examples_recommended": $MIN_EXAMPLES,
  "export_size_bytes": $EXPORTED_SIZE
}
EOF
echo "✅ Metadata saved: $METADATA_FILE"

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Export Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Exported Files:"
echo "  • $RAW_FILE (${EXPORTED_SIZE} bytes)"
echo "  • $METADATA_FILE"
echo ""
echo "Statistics:"
echo "  • Total examples: $TOTAL_COUNT"
echo "  • Export timestamp: $EXPORT_TIMESTAMP"
echo ""
echo "Next steps:"
echo "  1. Review exported data for quality"
echo "  2. Run: ./scripts/finetuning/2-prepare-finetuning-dataset.py"
echo "  3. This will create JSONL format for Gemini fine-tuning"
echo ""
