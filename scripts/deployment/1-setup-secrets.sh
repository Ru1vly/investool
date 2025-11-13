#!/bin/bash
# ============================================================================
# Phase 2.1: Setup Kubernetes Secrets
#
# This script helps you generate and configure secrets for FinRisk AI.
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       FinRisk AI - Kubernetes Secrets Setup                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if secrets.yaml exists
if [ ! -f "k8s/secrets.yaml" ]; then
    echo "❌ Error: k8s/secrets.yaml not found"
    echo "   Run this script from the project root directory"
    exit 1
fi

# Check if secrets are already configured
if ! grep -q "<REPLACE_WITH_BASE64" k8s/secrets.yaml; then
    echo "⚠️  Secrets appear to be already configured in k8s/secrets.yaml"
    read -p "   Continue anyway? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "This script will:"
echo "  1. Prompt for your Gemini API key"
echo "  2. Generate strong passwords for databases"
echo "  3. Base64 encode all values"
echo "  4. Update k8s/secrets.yaml automatically"
echo ""
read -p "Continue? (y/n): " START
if [ "$START" != "y" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 1: Gemini API Key"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Get your Gemini API key from:"
echo "  https://makersuite.google.com/app/apikey"
echo ""
read -sp "Enter your Gemini API key: " GEMINI_KEY
echo ""

if [ -z "$GEMINI_KEY" ]; then
    echo "❌ Error: Gemini API key is required"
    exit 1
fi

GEMINI_B64=$(echo -n "$GEMINI_KEY" | base64)

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 2: Generate Database Passwords"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Generating strong passwords (32 characters)..."

# Check if openssl is available
if ! command -v openssl &> /dev/null; then
    echo "⚠️  openssl not found. Using fallback password generation."
    POSTGRES_PWD="finrisk_postgres_$(date +%s)_$(openssl rand -hex 16 2>/dev/null || echo $(head -c 16 /dev/urandom | base64 | tr -d /=+))"
    REDIS_PWD="finrisk_redis_$(date +%s)_$(openssl rand -hex 16 2>/dev/null || echo $(head -c 16 /dev/urandom | base64 | tr -d /=+))"
    NEO4J_PWD="finrisk_neo4j_$(date +%s)_$(openssl rand -hex 16 2>/dev/null || echo $(head -c 16 /dev/urandom | base64 | tr -d /=+))"
else
    POSTGRES_PWD=$(openssl rand -base64 32)
    REDIS_PWD=$(openssl rand -base64 32)
    NEO4J_PWD=$(openssl rand -base64 32)
fi

# Base64 encode passwords
POSTGRES_B64=$(echo -n "$POSTGRES_PWD" | base64)
REDIS_B64=$(echo -n "$REDIS_PWD" | base64)
NEO4J_B64=$(echo -n "$NEO4J_PWD" | base64)

echo "✅ Passwords generated"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 3: Save Secrets (IMPORTANT!)"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  SAVE THESE PASSWORDS SECURELY! You'll need them for:"
echo "   - Database administration"
echo "   - Troubleshooting"
echo "   - Backup/restore operations"
echo ""
echo "Saving to: secrets.txt (KEEP THIS SECURE!)"
echo ""

cat > secrets.txt << EOF
# FinRisk AI Production Secrets
# Generated: $(date)
# KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT!

GEMINI_API_KEY=$GEMINI_KEY

POSTGRES_USER=finrisk_user
POSTGRES_DB=finrisk_db
POSTGRES_PASSWORD=$POSTGRES_PWD

REDIS_PASSWORD=$REDIS_PWD

NEO4J_USER=neo4j
NEO4J_PASSWORD=$NEO4J_PWD

# Connection strings:
# PostgreSQL: postgresql://finrisk_user:$POSTGRES_PWD@postgres-service:5432/finrisk_db
# Redis: redis://redis-service:6379 (password: $REDIS_PWD)
# Neo4j: bolt://neo4j:$NEO4J_PWD@neo4j-service:7687
EOF

chmod 600 secrets.txt
echo "✅ Secrets saved to secrets.txt (permissions: 600)"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 4: Update k8s/secrets.yaml"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Backup original
cp k8s/secrets.yaml k8s/secrets.yaml.backup
echo "✅ Backup created: k8s/secrets.yaml.backup"

# Update secrets.yaml
sed -i.bak \
    -e "s|<REPLACE_WITH_BASE64_ENCODED_GEMINI_KEY>|$GEMINI_B64|" \
    -e "s|<REPLACE_WITH_BASE64_ENCODED_POSTGRES_PASSWORD>|$POSTGRES_B64|" \
    -e "s|<REPLACE_WITH_BASE64_ENCODED_REDIS_PASSWORD>|$REDIS_B64|" \
    -e "s|<REPLACE_WITH_BASE64_ENCODED_NEO4J_PASSWORD>|$NEO4J_B64|" \
    k8s/secrets.yaml

rm k8s/secrets.yaml.bak
echo "✅ k8s/secrets.yaml updated"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Step 5: Verification"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Verify no placeholders remain
if grep -q "<REPLACE_WITH_BASE64" k8s/secrets.yaml; then
    echo "⚠️  Warning: Some placeholders still exist in secrets.yaml"
    echo "   Please review and update manually"
else
    echo "✅ All secrets configured successfully"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Secrets Setup Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "What was done:"
echo "  ✅ Generated strong passwords"
echo "  ✅ Base64 encoded all values"
echo "  ✅ Updated k8s/secrets.yaml"
echo "  ✅ Saved plaintext passwords to secrets.txt"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "  1. secrets.txt contains plaintext passwords - KEEP SECURE!"
echo "  2. Store secrets.txt in a password manager"
echo "  3. NEVER commit secrets.txt or k8s/secrets.yaml to git"
echo "  4. k8s/secrets.yaml.backup contains old values - delete after verification"
echo ""
echo "Next steps:"
echo "  1. Review k8s/secrets.yaml to verify all secrets are set"
echo "  2. Run: ./scripts/deployment/2-build-image.sh"
echo ""
