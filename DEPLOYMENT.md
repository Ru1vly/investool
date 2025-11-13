# FinRisk AI Deployment Guide

Comprehensive guide for deploying the FinRisk AI Analyst system to production.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Checklist](#production-checklist)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

The FinRisk AI system consists of four main components:

```
┌─────────────────────────────────────────────────────────┐
│                    FinRisk AI API                       │
│  ┌─────────────────┐         ┌──────────────────┐      │
│  │  C++ Engine     │ ←──────→│   AI Core        │      │
│  │  (InvestTool)   │         │   (Gemini)       │      │
│  └─────────────────┘         └──────────────────┘      │
│         ↓                            ↓                  │
│  ┌──────────────────────────────────────────────┐      │
│  │           FastAPI REST API                   │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
                      ↓       ↓       ↓
        ┌─────────────┬───────┬───────┬─────────────┐
        ↓             ↓       ↓       ↓             ↓
  ┌──────────┐  ┌────────┐ ┌──────┐ ┌──────────┐
  │PostgreSQL│  │ Redis  │ │Neo4j │ │  Gemini  │
  │ +pgvector│  │(Cache) │ │(Graph)│ │   API    │
  └──────────┘  └────────┘ └──────┘ └──────────┘
```

**Components:**
- **FinRisk AI API**: FastAPI application with C++ calculation engine and AI orchestrator
- **PostgreSQL**: Primary database with pgvector extension for embeddings
- **Redis**: Caching and session management
- **Neo4j**: Knowledge graph for GraphRAG
- **Gemini API**: External AI service (requires API key)

---

## Prerequisites

### Required

- **Docker**: 20.10+
- **Docker Compose**: 2.0+ (for local development)
- **Kubernetes**: 1.24+ (for production)
- **kubectl**: Latest version
- **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Recommended

- **Ingress Controller**: nginx-ingress or traefik (for Kubernetes)
- **cert-manager**: For automatic SSL certificate management
- **Helm**: 3.0+ (for easier Kubernetes deployments)

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 50 GB

**Recommended:**
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 100+ GB SSD

---

## Quick Start

The fastest way to get started:

```bash
# 1. Clone repository
git clone https://github.com/Ru1vly/investool.git
cd investool

# 2. Create environment file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Build and run with Docker Compose
docker-compose up --build

# 4. Access API
open http://localhost:8000/docs
```

---

## Docker Deployment

### Build Docker Image

```bash
# Build the image
docker build -t finrisk-ai:latest .

# Verify build
docker images | grep finrisk-ai
```

### Run Single Container

```bash
# Run API only (requires external databases)
docker run -d \
  --name finrisk-api \
  -p 8000:8000 \
  -e GEMINI_API_KEY="your_api_key" \
  -e POSTGRES_HOST="your_postgres_host" \
  -e POSTGRES_PASSWORD="your_postgres_password" \
  -e REDIS_HOST="your_redis_host" \
  -e NEO4J_URI="bolt://your_neo4j_host:7687" \
  -e NEO4J_PASSWORD="your_neo4j_password" \
  finrisk-ai:latest

# View logs
docker logs -f finrisk-api

# Stop container
docker stop finrisk-api
docker rm finrisk-api
```

---

## Docker Compose Deployment

### Development Deployment

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Start all services
docker-compose up -d

# 3. View logs
docker-compose logs -f finrisk-api

# 4. Check health
curl http://localhost:8000/health

# 5. Access services
# API Docs:    http://localhost:8000/docs
# PostgreSQL:  postgresql://localhost:5432/finrisk_db
# Redis:       redis://localhost:6379
# Neo4j UI:    http://localhost:7474

# 6. Stop services
docker-compose down

# 7. Remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### Production Deployment

```bash
# 1. Create production environment
cp .env.production.example .env.production
# Edit .env.production with production values

# 2. Secure the file
chmod 600 .env.production

# 3. Start with production overrides
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.production \
  up -d

# 4. Scale API instances
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --scale finrisk-api=5

# 5. Monitor
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### Useful Commands

```bash
# Rebuild after code changes
docker-compose up --build

# View resource usage
docker-compose stats

# Execute commands in container
docker-compose exec finrisk-api bash

# View PostgreSQL data
docker-compose exec postgres psql -U finrisk_user -d finrisk_db

# Backup database
docker-compose exec postgres pg_dump -U finrisk_user finrisk_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U finrisk_user finrisk_db < backup.sql
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Verify Kubernetes cluster
kubectl cluster-info

# Install nginx-ingress (if not installed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml

# Install cert-manager (optional, for automatic TLS)
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

### Deploy to Kubernetes

#### Step 1: Build and Push Image

```bash
# Build image
docker build -t your-registry/finrisk-ai:1.0.0 .

# Push to registry (replace with your registry)
docker push your-registry/finrisk-ai:1.0.0

# Update image in kustomization.yaml
# Edit k8s/kustomization.yaml and update the image
```

#### Step 2: Create Secrets

```bash
# Create secrets from template
cp k8s/secrets.yaml.template k8s/secrets.yaml

# Base64 encode your secrets
echo -n 'your_gemini_api_key' | base64
echo -n 'your_postgres_password' | base64
echo -n 'your_neo4j_password' | base64

# Edit k8s/secrets.yaml and replace placeholders with encoded values
# IMPORTANT: Never commit secrets.yaml to git!

# Uncomment secrets.yaml in k8s/kustomization.yaml
```

#### Step 3: Deploy

```bash
# Deploy all resources
kubectl apply -k k8s/

# Verify deployment
kubectl get all -n finrisk-ai

# Check pod status
kubectl get pods -n finrisk-ai -w

# View logs
kubectl logs -n finrisk-ai -l app=finrisk-api -f

# Check services
kubectl get svc -n finrisk-ai
```

#### Step 4: Access Application

```bash
# Option 1: Port forward (development)
kubectl port-forward -n finrisk-ai svc/finrisk-api-service 8000:80

# Then visit: http://localhost:8000/docs

# Option 2: Ingress (production)
# Update k8s/ingress.yaml with your domain
# Access at: https://api.finrisk.example.com
```

### Update Deployment

```bash
# Build new version
docker build -t your-registry/finrisk-ai:1.0.1 .
docker push your-registry/finrisk-ai:1.0.1

# Update deployment
kubectl set image deployment/finrisk-api \
  finrisk-api=your-registry/finrisk-ai:1.0.1 \
  -n finrisk-ai

# Watch rollout
kubectl rollout status deployment/finrisk-api -n finrisk-ai

# Rollback if needed
kubectl rollout undo deployment/finrisk-api -n finrisk-ai
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment/finrisk-api --replicas=5 -n finrisk-ai

# Horizontal Pod Autoscaler (already configured in api-deployment.yaml)
kubectl get hpa -n finrisk-ai

# View autoscaler status
kubectl describe hpa finrisk-api-hpa -n finrisk-ai
```

### Maintenance Commands

```bash
# View all resources
kubectl get all -n finrisk-ai

# Describe resources
kubectl describe deployment/finrisk-api -n finrisk-ai
kubectl describe pod/finrisk-api-xxx -n finrisk-ai

# Execute commands in pod
kubectl exec -it -n finrisk-ai deployment/finrisk-api -- /bin/bash

# View logs
kubectl logs -n finrisk-ai -l app=finrisk-api --tail=100 -f

# Restart deployment
kubectl rollout restart deployment/finrisk-api -n finrisk-ai

# Delete all resources
kubectl delete -k k8s/
```

---

## Production Checklist

Before deploying to production, ensure:

### Security

- [ ] All default passwords changed to strong, unique values
- [ ] Secrets stored in secure secret management system (not files)
- [ ] HTTPS/TLS enabled with valid certificates
- [ ] CORS configured for specific domains (not `*`)
- [ ] Network policies applied to restrict traffic
- [ ] Container images scanned for vulnerabilities
- [ ] Non-root user configured in containers
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] API authentication/authorization implemented

### Configuration

- [ ] `DEBUG=false` in production
- [ ] Logging level set to `warning` or `error`
- [ ] Database connection pooling configured
- [ ] Resource limits set for all containers
- [ ] Health checks configured
- [ ] Proper timezone settings
- [ ] Backup schedule configured
- [ ] Retention policies set

### Monitoring

- [ ] Logging centralized (ELK, CloudWatch, etc.)
- [ ] Metrics collection enabled (Prometheus)
- [ ] Error tracking configured (Sentry)
- [ ] Uptime monitoring enabled
- [ ] Alert rules configured
- [ ] Dashboard created

### Performance

- [ ] Database indexes created
- [ ] Query optimization performed
- [ ] Caching strategy implemented
- [ ] CDN configured for static assets
- [ ] Load testing completed
- [ ] Autoscaling configured

### Disaster Recovery

- [ ] Backup strategy implemented
- [ ] Backup restoration tested
- [ ] Database replication configured
- [ ] Disaster recovery plan documented
- [ ] Runbooks created

---

## Monitoring and Observability

### Health Checks

```bash
# Check API health
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
```

### Logs

```bash
# Docker Compose
docker-compose logs -f finrisk-api
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f neo4j

# Kubernetes
kubectl logs -n finrisk-ai -l app=finrisk-api -f
kubectl logs -n finrisk-ai -l app=postgres -f
```

### Metrics

```bash
# Prometheus metrics (if enabled)
curl http://localhost:8000/metrics

# Container stats
docker stats

# Kubernetes metrics
kubectl top pods -n finrisk-ai
kubectl top nodes
```

---

## Troubleshooting

### Common Issues

#### Issue: Container won't start

```bash
# Check logs
docker-compose logs finrisk-api

# Common causes:
# - Missing GEMINI_API_KEY
# - Database connection failed
# - Port already in use

# Solutions:
# - Verify .env file exists and has GEMINI_API_KEY
# - Check database is running: docker-compose ps
# - Check port availability: lsof -i :8000
```

#### Issue: API returns 503 Service Unavailable

```bash
# Check orchestrator initialization
docker-compose logs finrisk-api | grep "orchestrator"

# Check database connections
docker-compose exec finrisk-api python3 -c "
from finrisk_ai.core.orchestrator import FinRiskOrchestrator
import os
orch = FinRiskOrchestrator(gemini_api_key=os.getenv('GEMINI_API_KEY'))
print('Orchestrator initialized successfully')
"
```

#### Issue: C++ engine not available

```bash
# Verify module exists
docker-compose exec finrisk-api ls -la /app/build/

# Test import
docker-compose exec finrisk-api python3 -c "
import investool_engine as ie
print('C++ engine available')
print(ie.RiskAnalyzer.CalculateVolatility([0.01, -0.02, 0.03]))
"
```

#### Issue: Database connection error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U finrisk_user -d finrisk_db

# Check credentials
docker-compose exec finrisk-api env | grep POSTGRES
```

#### Issue: Kubernetes pod crash looping

```bash
# Check pod logs
kubectl logs -n finrisk-ai <pod-name>

# Check pod events
kubectl describe pod -n finrisk-ai <pod-name>

# Common issues:
# - Secrets not created
# - Image pull failed
# - Init containers failed

# Verify secrets
kubectl get secrets -n finrisk-ai
kubectl describe secret finrisk-secrets -n finrisk-ai
```

### Debug Mode

```bash
# Enable debug mode (development only!)
# In .env:
DEBUG=true
LOG_LEVEL=debug

# Restart services
docker-compose restart finrisk-api

# View detailed logs
docker-compose logs -f finrisk-api
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Kubernetes
kubectl top pods -n finrisk-ai
kubectl top nodes

# Database performance
docker-compose exec postgres psql -U finrisk_user -d finrisk_db -c "
SELECT pid, query, state, wait_event_type
FROM pg_stat_activity
WHERE state != 'idle';
"

# Redis stats
docker-compose exec redis redis-cli INFO stats
```

---

## Support

For issues and questions:

- **Issues**: https://github.com/Ru1vly/investool/issues
- **Documentation**: See `API_DOCUMENTATION.md` and `PYTHON_BRIDGE.md`
- **Architecture**: See Phase 1-4 implementation documentation

---

## License

See LICENSE file for details.
