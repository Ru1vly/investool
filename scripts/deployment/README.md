# Deployment Scripts - Phase 2

Automated scripts for deploying FinRisk AI to production.

## Overview

These scripts guide you through Phase 2 of the production launch:
1. Setup Kubernetes secrets
2. Build Docker image
3. Deploy to Kubernetes
4. Validate deployment

## Quick Start

```bash
# Run scripts in order:
./scripts/deployment/1-setup-secrets.sh
./scripts/deployment/2-build-image.sh
./scripts/deployment/3-deploy-k8s.sh
./scripts/deployment/4-validate.sh
```

## Scripts

### 1-setup-secrets.sh

**Purpose:** Generate and configure Kubernetes secrets

**What it does:**
- Prompts for Gemini API key
- Generates strong passwords (32 characters)
- Base64 encodes all values
- Updates `k8s/secrets.yaml` automatically
- Saves plaintext passwords to `secrets.txt`

**Usage:**
```bash
./scripts/deployment/1-setup-secrets.sh
```

**Output:**
- `k8s/secrets.yaml` - Configured with base64-encoded secrets
- `secrets.txt` - Plaintext passwords (KEEP SECURE!)
- `k8s/secrets.yaml.backup` - Backup of original file

**Security:**
- Secrets are generated with `openssl rand -base64 32`
- `secrets.txt` is created with permissions 600
- Never commits secrets to git

---

### 2-build-image.sh

**Purpose:** Build production Docker image

**What it does:**
- Prompts for container registry
- Builds multi-stage Docker image (C++ + Python)
- Tags image with version and latest
- Tests image locally (optional)
- Pushes to registry (optional)

**Usage:**
```bash
./scripts/deployment/2-build-image.sh
```

**Interactive prompts:**
1. Container registry (e.g., `docker.io/username`, `gcr.io/project`)
2. Image name (default: `finrisk-ai`)
3. Version tag (default: `1.0.0`)
4. Test locally? (y/n)
5. Push to registry? (y/n)

**Build time:** ~5-10 minutes (includes C++ compilation)

**Output:**
- Docker image: `your-registry/finrisk-ai:1.0.0`
- Docker image: `your-registry/finrisk-ai:latest`
- `build-info.txt` - Build metadata

**Example:**
```bash
./scripts/deployment/2-build-image.sh

# Prompts:
Container registry: docker.io/mycompany
Image name: finrisk-ai
Version tag: 1.0.0

# Result:
Built: docker.io/mycompany/finrisk-ai:1.0.0
```

---

### 3-deploy-k8s.sh

**Purpose:** Deploy complete stack to Kubernetes

**What it does:**
- Validates prerequisites (kubectl, cluster, secrets)
- Uncomments `secrets.yaml` in kustomization
- Deploys all resources via `kubectl apply -k k8s/`
- Monitors pod startup (5 minute timeout)
- Shows deployment status
- Provides access information

**Usage:**
```bash
./scripts/deployment/3-deploy-k8s.sh
```

**Prerequisites:**
- kubectl installed and configured
- Connected to Kubernetes cluster
- Secrets configured (`1-setup-secrets.sh` run)
- Docker image pushed to registry

**What gets deployed:**
- Namespace: `finrisk-ai`
- ConfigMap: `finrisk-config`
- Secret: `finrisk-secrets`
- PostgreSQL (1 pod, 10Gi PVC)
- Redis (1 pod, 5Gi PVC)
- Neo4j (1 pod, 10Gi PVC)
- FinRisk API (3 pods, HPA 2-10)
- Ingress (NGINX)

**Deploy time:** ~2-3 minutes for all pods to start

**Output:**
- `deployment-info.txt` - Deployment metadata

---

### 4-validate.sh

**Purpose:** Comprehensive deployment validation

**What it does:**
- Runs 20 validation tests across 6 test suites
- Tests infrastructure, pods, services, API health, configuration
- Checks for common issues
- Generates validation report

**Usage:**
```bash
./scripts/deployment/4-validate.sh
```

**Test suites:**
1. **Infrastructure** (3 tests)
   - Namespace, ConfigMap, Secrets

2. **Pods** (4 tests)
   - PostgreSQL, Redis, Neo4j, API pods running

3. **Services** (4 tests)
   - All services available

4. **API Health** (6 tests)
   - Health endpoint, status, C++ engine, documentation

5. **Configuration** (2 tests)
   - Phase 5 settings, HPA

6. **Logs** (2 tests)
   - No crash loops, OrchestratorV2 active

**Exit codes:**
- `0` - All tests passed
- `1` - Some tests failed

**Output:**
- Console: Test results with ✅/❌
- `validation-report.txt` - Detailed validation report

**Example output:**
```
[1] Namespace exists... ✅ PASS
[2] ConfigMap deployed... ✅ PASS
[3] Secrets deployed... ✅ PASS
...
[20] OrchestratorV2 initialized... ✅ PASS

Total tests: 20
Passed: 20 ✅
Failed: 0 ❌
Pass rate: 100%

🎉 All validation tests passed!
```

---

## Complete Workflow

### Step-by-Step Deployment

```bash
# Step 1: Navigate to project root
cd /path/to/investool

# Step 2: Setup secrets (interactive)
./scripts/deployment/1-setup-secrets.sh
# Prompts for Gemini API key
# Generates passwords automatically
# Updates k8s/secrets.yaml

# Step 3: Build image (interactive)
./scripts/deployment/2-build-image.sh
# Enter registry: docker.io/mycompany
# Enter image name: finrisk-ai
# Enter version: 1.0.0
# Test locally: y
# Push to registry: y

# Step 4: Update kustomization (manual)
# Edit k8s/kustomization.yaml:
# Change: newName: your-registry/finrisk-ai
# To: newName: docker.io/mycompany/finrisk-ai

# Step 5: Deploy to Kubernetes
./scripts/deployment/3-deploy-k8s.sh
# Validates prerequisites
# Deploys stack
# Monitors startup

# Step 6: Validate deployment
./scripts/deployment/4-validate.sh
# Runs 20 tests
# Reports pass/fail
```

### Total Time

- Secrets setup: ~2 minutes
- Build image: ~5-10 minutes
- Deploy to K8s: ~2-3 minutes
- Validation: ~1 minute

**Total: ~10-16 minutes** from start to validated production deployment

---

## Troubleshooting

### Script Fails: "kubectl not found"

```bash
# Install kubectl
# macOS:
brew install kubectl

# Linux:
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Script Fails: "Cannot connect to cluster"

```bash
# Check kubeconfig
kubectl cluster-info

# If not configured, set KUBECONFIG:
export KUBECONFIG=/path/to/kubeconfig

# Or for GKE:
gcloud container clusters get-credentials <cluster-name>

# Or for EKS:
aws eks update-kubeconfig --name <cluster-name>
```

### Build Fails: "Docker not found"

```bash
# Install Docker
# Visit: https://docs.docker.com/get-docker/

# Start Docker daemon
sudo systemctl start docker  # Linux
open -a Docker  # macOS
```

### Pods Stuck in Pending

```bash
# Check node resources
kubectl top nodes

# Check PVC status
kubectl get pvc -n finrisk-ai

# Describe pod to see error
kubectl describe pod -n finrisk-ai <pod-name>

# Common causes:
# - Insufficient cluster resources
# - PVC provisioning issues
# - Image pull errors
```

### Validation Tests Fail

```bash
# View detailed pod status
kubectl get pods -n finrisk-ai

# Check specific pod logs
kubectl logs -n finrisk-ai <pod-name>

# Check events
kubectl get events -n finrisk-ai --sort-by='.lastTimestamp'

# Common issues:
# - Missing GEMINI_API_KEY in secrets
# - Image tag mismatch in kustomization
# - Network policies blocking traffic
```

---

## Files Generated

After running all scripts:

```
investool/
├── secrets.txt                    # Plaintext passwords (KEEP SECURE!)
├── build-info.txt                 # Docker build metadata
├── deployment-info.txt            # Kubernetes deployment metadata
├── validation-report.txt          # Validation test results
└── k8s/
    ├── secrets.yaml               # Configured secrets (NEVER COMMIT!)
    └── secrets.yaml.backup        # Original template backup
```

**Security:**
- `secrets.txt` - Contains plaintext passwords. Store in password manager, then delete.
- `k8s/secrets.yaml` - Contains base64-encoded secrets. Already in .gitignore.
- Both files should NEVER be committed to git!

---

## Manual Deployment (Without Scripts)

If you prefer manual deployment:

### 1. Setup Secrets

```bash
# Generate passwords
POSTGRES_PWD=$(openssl rand -base64 32)
REDIS_PWD=$(openssl rand -base64 32)
NEO4J_PWD=$(openssl rand -base64 32)

# Base64 encode
echo -n "your_gemini_key" | base64
echo -n "$POSTGRES_PWD" | base64
echo -n "$REDIS_PWD" | base64
echo -n "$NEO4J_PWD" | base64

# Edit k8s/secrets.yaml and replace placeholders
```

### 2. Build Image

```bash
docker build -t your-registry/finrisk-ai:1.0.0 .
docker push your-registry/finrisk-ai:1.0.0
```

### 3. Update Kustomization

```bash
# Edit k8s/kustomization.yaml
# Uncomment: - secrets.yaml
# Update image: newName: your-registry/finrisk-ai
```

### 4. Deploy

```bash
kubectl apply -k k8s/
kubectl get pods -n finrisk-ai -w
```

### 5. Validate

```bash
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80
curl http://localhost:8000/health
```

---

## Next Steps After Deployment

Once validation passes:

1. **Configure Ingress Domain:**
   - Update `k8s/ingress.yaml` with your domain
   - Configure DNS A record
   - Setup TLS certificate (cert-manager or manual)

2. **Monitor Production:**
   - `kubectl logs -n finrisk-ai -l app=finrisk-api -f`
   - `kubectl get hpa -n finrisk-ai -w`
   - `kubectl top pods -n finrisk-ai`

3. **Proceed to Phase 3:**
   - Follow `PRODUCTION_LAUNCH.md` for Phase 3 (Activate SOTA)
   - System will automatically collect training data
   - After 1000+ examples, create fine-tuning job

---

## Support

- **Documentation:** See `PRODUCTION_LAUNCH.md`, `DEPLOYMENT.md`
- **Issues:** https://github.com/Ru1vly/investool/issues
- **Kubernetes:** https://kubernetes.io/docs/

---

**Created for Phase 2: Deploy Infrastructure**
