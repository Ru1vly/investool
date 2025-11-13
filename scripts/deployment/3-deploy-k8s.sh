#!/bin/bash
# ============================================================================
# Phase 2.3: Deploy to Kubernetes
#
# Deploys the complete FinRisk AI stack to Kubernetes.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       FinRisk AI - Kubernetes Deployment                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "This script will deploy the complete FinRisk AI stack:"
echo "  • Namespace: finrisk-ai"
echo "  • ConfigMap with application settings"
echo "  • Secrets (API keys, passwords)"
echo "  • PostgreSQL (with pgvector)"
echo "  • Redis (caching)"
echo "  • Neo4j (knowledge graph)"
echo "  • FinRisk API (3 replicas)"
echo "  • Ingress (NGINX)"
echo ""

# Pre-flight checks
echo "═══════════════════════════════════════════════════════════════"
echo "  Pre-flight Checks"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed"
    echo "   Install from: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi
echo "✅ kubectl found: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    echo "   Check your kubeconfig and cluster status"
    exit 1
fi
echo "✅ Connected to cluster: $(kubectl config current-context)"

# Check k8s directory
if [ ! -d "k8s" ]; then
    echo "❌ Error: k8s/ directory not found"
    echo "   Run this script from the project root"
    exit 1
fi
echo "✅ k8s/ directory found"

# Check secrets.yaml
if [ ! -f "k8s/secrets.yaml" ]; then
    echo "❌ Error: k8s/secrets.yaml not found"
    echo "   Run: ./scripts/deployment/1-setup-secrets.sh first"
    exit 1
fi

# Check if secrets are configured
if grep -q "<REPLACE_WITH_BASE64" k8s/secrets.yaml; then
    echo "❌ Error: k8s/secrets.yaml contains placeholders"
    echo "   Run: ./scripts/deployment/1-setup-secrets.sh to configure secrets"
    exit 1
fi
echo "✅ Secrets configured"

# Check kustomization.yaml
if [ ! -f "k8s/kustomization.yaml" ]; then
    echo "❌ Error: k8s/kustomization.yaml not found"
    exit 1
fi

# Check if secrets.yaml is uncommented in kustomization
if ! grep -q "^  - secrets.yaml" k8s/kustomization.yaml; then
    echo "⚠️  Warning: secrets.yaml is commented out in kustomization.yaml"
    read -p "   Uncomment it now? (y/n): " UNCOMMENT
    if [ "$UNCOMMENT" = "y" ]; then
        sed -i 's|^  # - secrets.yaml|  - secrets.yaml|' k8s/kustomization.yaml
        echo "✅ secrets.yaml uncommented"
    else
        echo "❌ Aborted. Please uncomment secrets.yaml in k8s/kustomization.yaml"
        exit 1
    fi
fi
echo "✅ kustomization.yaml configured"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Deployment Configuration"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Show what will be deployed
echo "Resources to deploy:"
kubectl kustomize k8s/ | grep -E "^kind:|  name:" | paste - - | sed 's/kind: /  • /' | sed 's/  name: / - /'

echo ""
read -p "Proceed with deployment? (y/n): " PROCEED
if [ "$PROCEED" != "y" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Deploying to Kubernetes"
echo "═══════════════════════════════════════════════════════════════"
echo ""

DEPLOY_START=$(date +%s)

# Apply kustomization
echo "Applying kustomization..."
kubectl apply -k k8s/

DEPLOY_END=$(date +%s)
DEPLOY_TIME=$((DEPLOY_END - DEPLOY_START))

echo ""
echo "✅ Deployment initiated in ${DEPLOY_TIME}s"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Monitoring Deployment"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Wait for namespace
echo "Checking namespace..."
if kubectl get namespace finrisk-ai &> /dev/null; then
    echo "✅ Namespace: finrisk-ai"
else
    echo "❌ Namespace creation failed"
    exit 1
fi

echo ""
echo "Waiting for pods to start (this may take 2-3 minutes)..."
echo ""

# Monitor pod status
TIMEOUT=300  # 5 minutes
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    # Get pod status
    TOTAL=$(kubectl get pods -n finrisk-ai --no-headers 2>/dev/null | wc -l)
    RUNNING=$(kubectl get pods -n finrisk-ai --no-headers 2>/dev/null | grep -c "Running" || echo "0")
    PENDING=$(kubectl get pods -n finrisk-ai --no-headers 2>/dev/null | grep -c "Pending\|ContainerCreating" || echo "0")
    FAILED=$(kubectl get pods -n finrisk-ai --no-headers 2>/dev/null | grep -cE "Error|CrashLoopBackOff|ImagePullBackOff" || echo "0")

    echo -ne "\r  Pods: $RUNNING/$TOTAL running, $PENDING pending, $FAILED failed   "

    # Check if all are running
    if [ "$TOTAL" -gt 0 ] && [ "$RUNNING" -eq "$TOTAL" ]; then
        echo ""
        echo "✅ All pods are running!"
        break
    fi

    # Check for failures
    if [ "$FAILED" -gt 0 ]; then
        echo ""
        echo "⚠️  Some pods have failed. Showing status:"
        kubectl get pods -n finrisk-ai
        echo ""
        echo "Check logs with:"
        echo "  kubectl logs -n finrisk-ai <pod-name>"
        break
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo ""
    echo "⚠️  Timeout waiting for pods to start"
    echo "Current status:"
    kubectl get pods -n finrisk-ai
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Deployment Status"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Show all resources
kubectl get all -n finrisk-ai

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Service Endpoints"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Show services
kubectl get svc -n finrisk-ai

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Access Information"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "To access the API locally:"
echo "  kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80"
echo "  Then visit: http://localhost:8000/docs"
echo ""

# Check ingress
if kubectl get ingress -n finrisk-ai &> /dev/null; then
    INGRESS_HOST=$(kubectl get ingress -n finrisk-ai -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null || echo "")
    if [ -n "$INGRESS_HOST" ]; then
        echo "Ingress configured for: https://$INGRESS_HOST"
        echo "  (Requires DNS configuration and TLS certificate)"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Deployment Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "What was deployed:"
echo "  ✅ Namespace: finrisk-ai"
echo "  ✅ PostgreSQL with pgvector"
echo "  ✅ Redis for caching"
echo "  ✅ Neo4j for knowledge graph"
echo "  ✅ FinRisk API (3 replicas with HPA)"
echo "  ✅ Ingress for external access"
echo ""
echo "Next steps:"
echo "  1. Run validation script:"
echo "     ./scripts/deployment/4-validate.sh"
echo ""
echo "  2. View logs:"
echo "     kubectl logs -n finrisk-ai -l app=finrisk-api -f"
echo ""
echo "  3. Monitor pods:"
echo "     kubectl get pods -n finrisk-ai -w"
echo ""

# Save deployment info
cat > deployment-info.txt << EOF
Deployment completed: $(date)
Cluster: $(kubectl config current-context)
Namespace: finrisk-ai
Pods: $TOTAL
Status: $RUNNING running, $PENDING pending, $FAILED failed
EOF

echo "Deployment info saved to: deployment-info.txt"
echo ""
