#!/bin/bash
# ============================================================================
# Phase 2: Production Deployment - Quick Start Script
# ============================================================================
#
# This script provides a quick way to execute all Phase 2 steps in sequence.
# Run this on a machine with Docker, kubectl, and Kubernetes cluster access.
#
# Prerequisites:
#   - Docker installed and running
#   - kubectl configured with cluster access
#   - Container registry authentication set up
#   - Gemini API key ready
#
# Usage:
#   1. Review this script
#   2. Make it executable: chmod +x PHASE2_QUICKSTART.sh
#   3. Run: ./PHASE2_QUICKSTART.sh
#
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Phase 2: Production Deployment - Quick Start            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Step 0: Update Gemini API Key
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Step 0: Update Gemini API Key"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  CRITICAL: The Gemini API key is currently set to PLACEHOLDER"
echo ""
echo "Get your API key from: https://makersuite.google.com/app/apikey"
echo ""

read -sp "Enter your Gemini API key: " GEMINI_KEY
echo ""

if [ -z "$GEMINI_KEY" ]; then
    echo "❌ Error: Gemini API key is required"
    exit 1
fi

# Update secrets.txt
sed -i "s|PLACEHOLDER_REPLACE_WITH_ACTUAL_KEY|$GEMINI_KEY|" secrets.txt
echo "✅ Updated secrets.txt"

# Update k8s/secrets.yaml
GEMINI_B64=$(echo -n "$GEMINI_KEY" | base64)
sed -i "s|UExBQ0VIT0xERVJfUkVQTEFDRV9XSVRIX0FDVFVBTF9LRVk=|$GEMINI_B64|" k8s/secrets.yaml
echo "✅ Updated k8s/secrets.yaml"

echo ""
echo "✅ Gemini API key configured!"
echo ""
sleep 2

# ============================================================================
# Step 1: Build Docker Image
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Step 1: Build Production Docker Image"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "This will build the production image with C++ engine + Python AI"
echo "Estimated time: 5-10 minutes"
echo ""

read -p "Continue with image build? (y/n): " BUILD
if [ "$BUILD" != "y" ]; then
    echo "Skipping image build. Run manually: ./scripts/deployment/2-build-image.sh"
else
    ./scripts/deployment/2-build-image.sh

    echo ""
    echo "✅ Docker image built successfully!"
    echo ""

    # Prompt to update kustomization.yaml
    echo "⚠️  IMPORTANT: Update k8s/kustomization.yaml with your image details"
    echo ""
    echo "Edit the 'images' section (lines 32-35) with your registry/image/tag"
    echo ""
    read -p "Press Enter after you've updated kustomization.yaml..."
fi

echo ""
sleep 2

# ============================================================================
# Step 2: Deploy to Kubernetes
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Step 2: Deploy to Kubernetes"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "This will deploy the complete FinRisk AI stack to your cluster"
echo "Estimated time: 2-3 minutes"
echo ""

read -p "Continue with deployment? (y/n): " DEPLOY
if [ "$DEPLOY" != "y" ]; then
    echo "Skipping deployment. Run manually: ./scripts/deployment/3-deploy-k8s.sh"
else
    ./scripts/deployment/3-deploy-k8s.sh

    echo ""
    echo "✅ Deployment complete!"
    echo ""
fi

echo ""
sleep 2

# ============================================================================
# Step 3: Validate Deployment
# ============================================================================

echo "═══════════════════════════════════════════════════════════════"
echo "  Step 3: Validate Deployment"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "This will run 20 comprehensive validation tests"
echo "Estimated time: 1 minute"
echo ""

read -p "Continue with validation? (y/n): " VALIDATE
if [ "$VALIDATE" != "y" ]; then
    echo "Skipping validation. Run manually: ./scripts/deployment/4-validate.sh"
else
    ./scripts/deployment/4-validate.sh

    VALIDATION_RESULT=$?

    if [ $VALIDATION_RESULT -eq 0 ]; then
        echo ""
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║                                                                ║"
        echo "║           🎉 PHASE 2 DEPLOYMENT SUCCESSFUL! 🎉                 ║"
        echo "║                                                                ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "All validation tests passed! Your FinRisk AI system is live."
        echo ""
        echo "Access the API:"
        echo "  kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80"
        echo "  http://localhost:8000/docs"
        echo ""
        echo "Next steps:"
        echo "  • Test the API with sample requests"
        echo "  • Monitor logs: kubectl logs -n finrisk-ai -l app=finrisk-api -f"
        echo "  • Watch metrics: kubectl top pods -n finrisk-ai"
        echo "  • Proceed to Phase 3: Activate SOTA fine-tuning"
        echo ""
    else
        echo ""
        echo "⚠️  Some validation tests failed"
        echo ""
        echo "Check the validation report for details."
        echo "See troubleshooting: scripts/deployment/README.md"
        echo ""
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Phase 2 Quick Start Complete"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "For detailed documentation, see:"
echo "  • PHASE2_STATUS.md - Complete status report"
echo "  • PHASE2_EXECUTION.md - Detailed execution guide"
echo "  • scripts/deployment/README.md - Script documentation"
echo ""
