# FinRisk AI Analyst API Documentation

## Overview

Production-ready REST API for the FinRisk AI Analyst system, combining:
- **C++ Calculation Engine** (InvestTool - 13+ formulas)
- **Multi-Agent AI System** (Gemini 1.5 Pro + Flash)
- **Memory & Personalization** (Mem0)
- **Advanced RAG** (Hybrid Search + GraphRAG)

**Base URL**: `http://localhost:8000` (development)

**Documentation**: `http://localhost:8000/docs` (interactive Swagger UI)

---

## Quick Start

### 1. Start the Server

#### Option A: Using Python directly
```bash
cd /path/to/investool
export GEMINI_API_KEY="your_api_key_here"
python3 -m finrisk_ai.api.main
```

#### Option B: Using uvicorn
```bash
cd /path/to/investool
export GEMINI_API_KEY="your_api_key_here"
uvicorn finrisk_ai.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Interactive docs
open http://localhost:8000/docs

# Run test suite
python3 test_api_client.py
```

---

## API Endpoints

### 1. Health Check

**GET** `/health`

Check API health and component status.

**Response:**
```json
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
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Generate Report

**POST** `/v1/report`

Generate a personalized financial analysis report.

**Request Body:**
```json
{
  "user_query": "Analyze my portfolio risk and compare to S&P 500",
  "user_id": "user_12345",
  "session_id": "session_abc"  // Optional
}
```

**Response:**
```json
{
  "final_report_text": "# Portfolio Risk Analysis\n\n Your portfolio shows...",
  "calculation_results": {
    "volatility": 0.15,
    "sharpe_ratio": 1.45,
    "sortino_ratio": 1.82,
    "var_95": 5000.00,
    "beta": 1.12,
    "z_score": 0.85
  },
  "chart_json": {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "mark": "bar",
    "data": {...}
  },
  "metadata": {
    "validation_passed": true,
    "validation_errors": [],
    "retry_count": 0,
    "rag_documents_retrieved": 5,
    "graph_nodes_retrieved": 10,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Workflow:**
1. **Data Agent**: Retrieves context from RAG and GraphRAG
2. **Context Agent**: Fetches user preferences and history
3. **Calculation Agent**: Gemini selects functions → C++ executes
4. **Narrative Agent**: Gemini interprets results → Generates report
5. **Quality Agent**: Validates accuracy → Checks for hallucinations

**Example:**
```bash
curl -X POST http://localhost:8000/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Calculate Sharpe ratio for monthly returns of 5%, -2%, 3%, 8%",
    "user_id": "user_123"
  }'
```

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/report",
    json={
        "user_query": "What is my portfolio's risk profile?",
        "user_id": "user_123"
    }
)

result = response.json()
print(result["final_report_text"])
```

---

### 3. Create/Update User

**POST** `/v1/user`

Create or update user preferences for personalization.

**Request Body:**
```json
{
  "user_id": "user_12345",
  "risk_tolerance": "moderate",     // "conservative", "moderate", "aggressive"
  "reporting_style": "detailed"     // "concise", "detailed", "technical"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User user_12345 preferences updated successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/user \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "risk_tolerance": "aggressive",
    "reporting_style": "technical"
  }'
```

---

### 4. Get User Context

**GET** `/v1/user/{user_id}/context`

Retrieve user preferences, history, and temporal insights.

**Response:**
```json
{
  "user_id": "user_12345",
  "risk_tolerance": "moderate",
  "reporting_style": "detailed",
  "recent_activities": [
    {
      "type": "report_generated",
      "timestamp": "2024-01-15T10:00:00Z",
      "content": {"query": "Analyze portfolio"}
    }
  ],
  "temporal_insights": [
    "User consistently asks about risk metrics",
    "User prefers detailed explanations"
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/v1/user/user_123/context
```

---

### 5. Index Knowledge

**POST** `/v1/knowledge/index`

Index documents into the RAG system for knowledge retrieval.

**Request Body:**
```json
{
  "documents": [
    {
      "content": "The S&P 500 has returned 10% annually over 50 years...",
      "metadata": {"source": "historical_data", "category": "returns"}
    },
    {
      "content": "Diversification reduces portfolio risk...",
      "metadata": {"source": "investment_basics", "category": "risk"}
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully indexed 2 documents"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/knowledge/index \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "content": "Beta measures an asset'\''s volatility relative to the market.",
        "metadata": {"source": "finance_101", "topic": "beta"}
      }
    ]
  }'
```

---

## Architecture

### System Flow

```
Client Request (HTTP)
       ↓
FastAPI Application
       ↓
FinRiskOrchestrator (Singleton)
       ↓
┌──────────────────────────────────────────┐
│  Multi-Agent Workflow (LangGraph)        │
│                                          │
│  1. DataAgent → RAG + GraphRAG          │
│  2. ContextAgent → Mem0 (preferences)   │
│  3. CalculationAgent → C++ Engine       │
│  4. NarrativeAgent → Gemini (interpret) │
│  5. QualityAgent → Validation           │
└──────────────────────────────────────────┘
       ↓
JSON Response
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| **API Framework** | FastAPI (async Python) |
| **Validation** | Pydantic |
| **AI Models** | Gemini 1.5 Pro + Flash |
| **Calculation Engine** | InvestTool C++ (pybind11) |
| **Memory** | Mem0 (user preferences, history) |
| **RAG** | Sentence Transformers + PostgreSQL pgvector |
| **Graph** | Neo4j (GraphRAG) |
| **Orchestration** | LangGraph |

---

## Configuration

### Environment Variables

```bash
# Required
export GEMINI_API_KEY="your_gemini_api_key"

# Optional (with defaults)
export GEMINI_PRO_MODEL="gemini-1.5-pro-latest"
export GEMINI_FLASH_MODEL="gemini-1.5-flash-latest"

# Production (optional)
export REDIS_URL="redis://localhost:6379"
export POSTGRES_URL="postgresql://user:pass@localhost:5432/finrisk"
export NEO4J_URL="bolt://localhost:7687"
```

### Production Deployment

#### Docker

```dockerfile
FROM python:3.11-slim

# Install C++ dependencies
RUN apt-get update && apt-get install -y \
    cmake g++ build-essential git

WORKDIR /app

# Copy project
COPY . .

# Build C++ module
RUN cd build && cmake .. && make

# Install Python dependencies
RUN pip install -r finrisk_ai/requirements.txt

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "finrisk_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t finrisk-ai .
docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY finrisk-ai
```

#### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: finrisk-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: finrisk-ai
  template:
    metadata:
      labels:
        app: finrisk-ai
    spec:
      containers:
      - name: api
        image: finrisk-ai:latest
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: finrisk-secrets
              key: gemini-api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: finrisk-ai-service
spec:
  selector:
    app: finrisk-ai
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Report generated successfully |
| 201 | Created | User created, knowledge indexed |
| 422 | Validation Error | Invalid input parameters |
| 404 | Not Found | User not found |
| 500 | Internal Error | Unexpected server error |
| 503 | Service Unavailable | Orchestrator not initialized, API key missing |

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid input parameters",
  "detail": "user_query cannot be empty"
}
```

---

## Performance

### Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Health Check | <10ms | Simple status check |
| User Creation | <100ms | Memory write |
| Knowledge Indexing | ~50ms/doc | Embedding + storage |
| Report Generation | 10-30s | Full AI workflow |

### Optimization Tips

1. **Caching**: Use Redis for LLM response caching (Phase 4)
2. **Batch Processing**: Index documents in batches
3. **Async**: All endpoints are async-ready
4. **Horizontal Scaling**: Deploy multiple API instances with load balancer
5. **C++ Speed**: Calculations are native C++ (microseconds)

---

## Testing

### Manual Testing

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Create user
curl -X POST http://localhost:8000/v1/user \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "risk_tolerance": "moderate"}'

# 3. Generate report
curl -X POST http://localhost:8000/v1/report \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Calculate Sharpe ratio", "user_id": "test_user"}'
```

### Automated Testing

```bash
# Run full test suite
python3 test_api_client.py

# Output:
# ✅ PASS: Health Check
# ✅ PASS: User Creation
# ✅ PASS: Knowledge Indexing
# ✅ PASS: Report Generation
# ✅ PASS: User Context Retrieval
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class FinRiskUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def generate_report(self):
        self.client.post("/v1/report", json={
            "user_query": "Calculate Sharpe ratio",
            "user_id": "load_test_user"
        })
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

---

## Security

### Best Practices

1. **API Key Management**
   - Store `GEMINI_API_KEY` in environment variables
   - Use secrets management in production (AWS Secrets Manager, HashiCorp Vault)

2. **CORS Configuration**
   - Configure `allow_origins` properly in production
   - Don't use `["*"]` in production

3. **Rate Limiting**
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter

   @app.post("/v1/report")
   @limiter.limit("10/minute")
   async def generate_report(...):
       ...
   ```

4. **Authentication**
   - Add JWT authentication for production
   - Implement user-based API keys

---

## Monitoring & Logging

### Application Logs

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('finrisk_api.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics (Phase 4)

```python
from prometheus_client import Counter, Histogram

report_requests = Counter('report_requests_total', 'Total report requests')
report_duration = Histogram('report_duration_seconds', 'Report generation time')
```

---

## Troubleshooting

### Common Issues

#### 1. "GEMINI_API_KEY not configured"

**Solution:**
```bash
export GEMINI_API_KEY="your_key_here"
# Restart server
```

#### 2. "C++ engine not available"

**Solution:**
```bash
cd investool/build
cmake ..
make
```

#### 3. "Orchestrator not initialized"

**Cause**: Server still starting up

**Solution**: Wait a few seconds, retry request

#### 4. "Connection refused"

**Cause**: Server not running

**Solution**:
```bash
python3 -m finrisk_ai.api.main
```

---

## Support

- **Documentation**: http://localhost:8000/docs (Swagger UI)
- **GitHub**: https://github.com/Ru1vly/investool
- **Logs**: Check console output for errors

---

## Version History

### v1.0.0 (Current)

- ✅ Complete REST API with 5 endpoints
- ✅ Multi-agent AI workflow
- ✅ C++ calculation engine integration
- ✅ Memory and personalization
- ✅ Advanced RAG system
- ✅ Auto-generated documentation
- ✅ Comprehensive error handling

### Roadmap

- **v1.1.0**: Redis caching, rate limiting
- **v1.2.0**: WebSocket support for streaming
- **v1.3.0**: Fine-tuned models (Phase 5)
- **v2.0.0**: Real-time market data integration

---

**Status**: ✅ Production Ready (Phase 3 Complete)