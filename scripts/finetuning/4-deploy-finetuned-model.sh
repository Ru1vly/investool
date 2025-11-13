#!/bin/bash
# ============================================================================
# Phase 3.4: Deploy Fine-Tuned Model with A/B Testing
#
# This script updates the Kubernetes deployment to use the fine-tuned model
# with A/B testing support.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 3.4: Deploy Fine-Tuned Model                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Configuration
# ============================================================================

NAMESPACE="${NAMESPACE:-finrisk-ai}"
AB_TEST_RATIO="${AB_TEST_RATIO:-50}"  # Percentage to route to fine-tuned model

# ============================================================================
# Check Prerequisites
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Checking Prerequisites"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found"
    exit 1
fi
echo "✅ kubectl found"

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi
echo "✅ Connected to cluster"

# Check namespace
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "❌ Namespace $NAMESPACE not found"
    exit 1
fi
echo "✅ Namespace exists"

echo ""

# ============================================================================
# Select Fine-Tuned Model
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Select Fine-Tuned Model"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# List available fine-tuning jobs
echo "Available fine-tuning jobs:"
echo ""

JOB_FILES=($(find training_data -name "finetuning_job_*.json" 2>/dev/null | sort -r))

if [ ${#JOB_FILES[@]} -eq 0 ]; then
    echo "No fine-tuning jobs found."
    echo ""
    read -p "Enter tuned model name manually: " TUNED_MODEL_NAME
else
    for i in "${!JOB_FILES[@]}"; do
        FILE=${JOB_FILES[$i]}
        MODEL_NAME=$(grep -o '"tuned_model_name":"[^"]*"' "$FILE" | cut -d'"' -f4)
        STATE=$(grep -o '"initial_state":"[^"]*"' "$FILE" | cut -d'"' -f4)
        CREATED=$(grep -o '"created_at":"[^"]*"' "$FILE" | cut -d'"' -f4)
        echo "  [$((i+1))] $MODEL_NAME"
        echo "      Created: $CREATED, Initial state: $STATE"
    done

    echo ""
    read -p "Select model number (or 0 to enter manually) [1]: " MODEL_NUM
    MODEL_NUM=${MODEL_NUM:-1}

    if [ "$MODEL_NUM" = "0" ]; then
        read -p "Enter tuned model name: " TUNED_MODEL_NAME
    elif [ "$MODEL_NUM" -ge 1 ] && [ "$MODEL_NUM" -le "${#JOB_FILES[@]}" ]; then
        FILE=${JOB_FILES[$((MODEL_NUM-1))]}
        TUNED_MODEL_NAME=$(grep -o '"tuned_model_name":"[^"]*"' "$FILE" | cut -d'"' -f4)
    else
        echo "❌ Invalid selection"
        exit 1
    fi
fi

if [ -z "$TUNED_MODEL_NAME" ]; then
    echo "❌ No model name provided"
    exit 1
fi

echo ""
echo "✅ Selected model: $TUNED_MODEL_NAME"
echo ""

# ============================================================================
# Verify Model Status
# ============================================================================

if [ ! -z "$GEMINI_API_KEY" ]; then
    echo "Verifying model status..."

    STATUS_RESPONSE=$(curl -s -X GET \
        "https://generativelanguage.googleapis.com/v1beta/${TUNED_MODEL_NAME}?key=$GEMINI_API_KEY")

    if command -v jq &> /dev/null; then
        STATE=$(echo "$STATUS_RESPONSE" | jq -r '.state')
        echo "Model state: $STATE"

        if [ "$STATE" != "ACTIVE" ]; then
            echo ""
            echo "⚠️  Warning: Model is not ACTIVE (current state: $STATE)"
            read -p "Continue anyway? (y/n): " CONTINUE
            if [ "$CONTINUE" != "y" ]; then
                echo "Deployment cancelled."
                exit 0
            fi
        else
            echo "✅ Model is ACTIVE and ready to use"
        fi
    fi

    echo ""
else
    echo "⚠️  GEMINI_API_KEY not set, skipping model verification"
    echo ""
fi

# ============================================================================
# Configure A/B Testing
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Configure A/B Testing"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "A/B testing routes a percentage of traffic to the fine-tuned model."
echo ""
echo "Options:"
echo "  • 0%   = Base model only (no fine-tuned model)"
echo "  • 50%  = Split traffic 50/50 (recommended for initial testing)"
echo "  • 100% = Fine-tuned model only"
echo ""

read -p "A/B test ratio (% to fine-tuned model) [$AB_TEST_RATIO]: " NEW_RATIO
AB_TEST_RATIO=${NEW_RATIO:-$AB_TEST_RATIO}

if [ "$AB_TEST_RATIO" -lt 0 ] || [ "$AB_TEST_RATIO" -gt 100 ]; then
    echo "❌ Invalid ratio. Must be 0-100."
    exit 1
fi

echo ""
echo "✅ A/B testing configured: ${AB_TEST_RATIO}% to fine-tuned model"
echo ""

# ============================================================================
# Update Kubernetes Secrets
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Update Kubernetes Secrets"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Updating secrets with fine-tuned model name..."

# Base64 encode the model name
TUNED_MODEL_B64=$(echo -n "$TUNED_MODEL_NAME" | base64)

# Check if secret exists
if ! kubectl get secret finrisk-secrets -n "$NAMESPACE" &> /dev/null; then
    echo "❌ Secret finrisk-secrets not found"
    exit 1
fi

# Patch the secret
kubectl patch secret finrisk-secrets -n "$NAMESPACE" \
    --type='json' \
    -p="[{\"op\":\"add\",\"path\":\"/data/FINETUNED_MODEL_NAME\",\"value\":\"$TUNED_MODEL_B64\"}]"

echo "✅ Secret updated with fine-tuned model name"
echo ""

# ============================================================================
# Update ConfigMap for A/B Testing
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Update ConfigMap"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Updating ConfigMap with A/B testing ratio..."

# Patch the configmap
kubectl patch configmap finrisk-config -n "$NAMESPACE" \
    --type='json' \
    -p="[
        {\"op\":\"add\",\"path\":\"/data/AB_TEST_ENABLED\",\"value\":\"true\"},
        {\"op\":\"add\",\"path\":\"/data/AB_TEST_FINETUNED_RATIO\",\"value\":\"$AB_TEST_RATIO\"}
    ]"

echo "✅ ConfigMap updated with A/B testing configuration"
echo ""

# ============================================================================
# Restart API Pods
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Restart API Pods"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Restarting API pods to apply changes..."

kubectl rollout restart deployment/finrisk-api -n "$NAMESPACE"

echo "Waiting for rollout to complete..."
kubectl rollout status deployment/finrisk-api -n "$NAMESPACE" --timeout=5m

echo "✅ API pods restarted successfully"
echo ""

# ============================================================================
# Verify Deployment
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Verify Deployment"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Get pod status
echo "Pod status:"
kubectl get pods -n "$NAMESPACE" -l app=finrisk-api

echo ""

# Check logs for confirmation
echo "Checking API logs for model configuration..."
API_POD=$(kubectl get pods -n "$NAMESPACE" -l app=finrisk-api -o jsonpath='{.items[0].metadata.name}')

if kubectl logs "$API_POD" -n "$NAMESPACE" --tail=50 | grep -i "model\|fine"; then
    echo ""
    echo "✅ Logs show model configuration"
else
    echo ""
    echo "⚠️  Could not find model configuration in logs"
fi

echo ""

# ============================================================================
# Test Endpoints
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Test A/B Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

read -p "Port-forward and test API? (y/n) [y]: " TEST_API
TEST_API=${TEST_API:-y}

if [ "$TEST_API" = "y" ]; then
    echo ""
    echo "Starting port-forward on localhost:8000..."
    echo "(Press Ctrl+C to stop)"
    echo ""

    # Kill any existing port-forward
    pkill -f "port-forward.*finrisk-api" 2>/dev/null || true

    # Start port-forward in background
    kubectl port-forward -n "$NAMESPACE" svc/finrisk-api-service 8000:80 &
    PF_PID=$!

    # Wait for port-forward to be ready
    sleep 3

    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "✅ API is healthy"
    else
        echo "⚠️  API health check returned unexpected response"
    fi

    echo ""
    echo "Test the API:"
    echo "  curl http://localhost:8000/health"
    echo "  curl http://localhost:8000/docs"
    echo ""
    echo "Check which model is used by making a request and inspecting response headers."
    echo ""
    echo "Port-forward running (PID: $PF_PID)"
    echo "Press Ctrl+C to stop"
    echo ""

    # Wait for user to stop
    wait $PF_PID
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Fine-Tuned Model Deployed!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
echo "  • Model: $TUNED_MODEL_NAME"
echo "  • A/B testing: ${AB_TEST_RATIO}% to fine-tuned model"
echo "  • ${AB_TEST_RATIO}% requests → Fine-tuned model"
echo "  • $((100-AB_TEST_RATIO))% requests → Base model"
echo ""
echo "Monitoring:"
echo "  • Watch logs: kubectl logs -f -n $NAMESPACE -l app=finrisk-api"
echo "  • Check pods: kubectl get pods -n $NAMESPACE"
echo "  • View config: kubectl get configmap finrisk-config -n $NAMESPACE -o yaml"
echo ""
echo "Next steps:"
echo "  1. Monitor A/B test results in logs and metrics"
echo "  2. Compare performance: fine-tuned vs base model"
echo "  3. Adjust ratio based on results"
echo "  4. When satisfied, set ratio to 100%"
echo "  5. Proceed to Phase 4: Scale & Monitor"
echo ""
