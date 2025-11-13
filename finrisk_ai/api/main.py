"""
Phase 3.2: FastAPI Application

Production-ready REST API for the FinRisk AI Analyst system.

Exposes the unified C++ + AI system via HTTP endpoints:
- POST /v1/report - Generate financial analysis reports
- POST /v1/user - Create/update user preferences
- GET /v1/user/{user_id}/context - Get user context
- POST /v1/knowledge/index - Index documents into RAG
- GET /health - Health check

Architecture:
- FastAPI framework for async performance
- Pydantic for request/response validation
- Singleton orchestrator for efficiency
- Proper error handling and logging
- CORS enabled for web clients
- Auto-generated OpenAPI documentation
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from finrisk_ai.api.schemas import (
    ReportRequest,
    ReportResponse,
    UserCreateRequest,
    UserContextResponse,
    DocumentIndexRequest,
    SuccessResponse,
    ErrorResponse,
    HealthResponse,
    CalculationResults,
    ReportMetadata
)
from finrisk_ai.core.orchestrator_v2 import FinRiskOrchestratorV2
from finrisk_ai.rag.hybrid_search import Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Global State (Singleton Orchestrator)
# ============================================================================

# Orchestrator instance (initialized on startup) - Using V2 with Phase 5 capabilities
orchestrator: Optional[FinRiskOrchestratorV2] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Startup:
    - Initialize orchestrator as singleton
    - Validate C++ engine availability
    - Load configuration

    Shutdown:
    - Cleanup resources
    """
    global orchestrator

    logger.info("🚀 Starting FinRisk AI API...")

    # Get Gemini API key from environment
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning(
            "⚠️  GEMINI_API_KEY not set. API will be available but report generation will fail. "
            "Set GEMINI_API_KEY environment variable."
        )

    try:
        # Initialize orchestrator V2 (Phase 5: with fine-tuning capabilities)
        logger.info("Initializing FinRiskOrchestratorV2 (Phase 5)...")

        # Phase 5 configuration from environment
        enable_data_collection = os.getenv("ENABLE_DATA_COLLECTION", "true").lower() == "true"
        enable_finetuning = os.getenv("ENABLE_FINETUNING", "false").lower() == "true"
        finetuned_model = os.getenv("FINETUNED_MODEL_NAME")
        enable_ab_testing = os.getenv("ENABLE_AB_TESTING", "false").lower() == "true"
        ab_test_split = float(os.getenv("AB_TEST_TRAFFIC_SPLIT", "0.5"))

        orchestrator = FinRiskOrchestratorV2(
            gemini_api_key=gemini_api_key or "dummy_key_for_health_check",
            gemini_pro_model=os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro-latest"),
            gemini_flash_model=os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash-latest"),
            # Phase 5 settings
            enable_data_collection=enable_data_collection,
            data_collection_quality_threshold=float(os.getenv("DATA_COLLECTION_QUALITY", "0.9")),
            finetuned_model=finetuned_model,
            enable_finetuning=enable_finetuning,
            enable_ab_testing=enable_ab_testing,
            ab_test_traffic_split=ab_test_split,
        )

        logger.info("✅ FinRiskOrchestratorV2 initialized successfully")
        logger.info(f"   → Data collection: {'ENABLED' if enable_data_collection else 'DISABLED'}")
        logger.info(f"   → Fine-tuning: {'ENABLED' if enable_finetuning else 'DISABLED'}")
        if finetuned_model:
            logger.info(f"   → Fine-tuned model: {finetuned_model}")
        if enable_ab_testing:
            logger.info(f"   → A/B testing: {ab_test_split*100:.0f}% to fine-tuned model")
        logger.info("✅ C++ engine available" if _check_cpp_engine() else "⚠️  C++ engine not available")
        logger.info("🚀 FinRisk AI API ready to serve requests")

    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator: {e}")
        logger.warning("API will start but requests may fail")

    yield  # Server is running

    # Cleanup on shutdown
    logger.info("🛑 Shutting down FinRisk AI API...")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="FinRisk AI Analyst API",
    description="""
    Production-grade Financial Analysis API powered by C++ calculation engine
    and Gemini AI.

    **Features:**
    - 🎯 13+ Financial Formulas (Volatility, Sharpe, Sortino, VaR, Beta, etc.)
    - 🤖 Multi-Agent AI System (Data, Context, Calculation, Narrative, Quality)
    - 💾 Memory & Personalization (Mem0 system)
    - 🔍 Advanced RAG (Hybrid Search + GraphRAG)
    - ⚡ Native C++ Performance (100% deterministic calculations)

    **Architecture:**
    - C++ Engine: InvestTool (formulas 1-13)
    - AI Core: Gemini 1.5 (Pro + Flash)
    - Memory: Mem0 (user preferences, history)
    - RAG: Vector DB + Knowledge Graph
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================================================
# Middleware
# ============================================================================

# CORS - Enable for web/mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid input parameters",
            "detail": str(exc)
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": str(exc) if os.getenv("DEBUG") else None
        }
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _check_orchestrator():
    """Check if orchestrator is initialized"""
    if orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized. Service is starting up."
        )
    return orchestrator


def _check_cpp_engine() -> bool:
    """Check if C++ engine is available"""
    try:
        from finrisk_ai.core.cpp_bridge import CPP_ENGINE_AVAILABLE
        return CPP_ENGINE_AVAILABLE
    except:
        return False


def _check_gemini_api_key():
    """Check if Gemini API key is set"""
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY not configured. Cannot generate reports."
        )


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/",
         summary="API Root",
         description="Get API information and available endpoints")
async def root():
    """API root endpoint"""
    return {
        "name": "FinRisk AI Analyst API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "generate_report": "POST /v1/report",
            "create_user": "POST /v1/user",
            "get_user_context": "GET /v1/user/{user_id}/context",
            "index_knowledge": "POST /v1/knowledge/index",
            "health_check": "GET /health",
            "documentation": "GET /docs"
        },
        "architecture": "C++ Engine (InvestTool) + AI Core (Gemini) + Memory (Mem0) + RAG"
    }


@app.get("/health",
         response_model=HealthResponse,
         summary="Health Check",
         description="Check API health and component status")
async def health_check():
    """
    Health check endpoint.

    Returns service health, version, and component statuses.
    """
    components = {
        "orchestrator": "operational" if orchestrator else "not_initialized",
        "cpp_engine": "operational" if _check_cpp_engine() else "not_available",
        "vector_db": "operational" if orchestrator and orchestrator.vector_db else "not_initialized",
        "graph_rag": "operational" if orchestrator and orchestrator.graph_rag else "not_initialized",
        "mem0_system": "operational" if orchestrator and orchestrator.mem0 else "not_initialized"
    }

    # Determine overall status
    all_operational = all(status == "operational" for status in components.values())
    status_value = "healthy" if all_operational else "degraded"

    return HealthResponse(
        status=status_value,
        version="1.0.0",
        cpp_engine_available=_check_cpp_engine(),
        components=components
    )


@app.post("/v1/report",
          response_model=ReportResponse,
          summary="Generate Financial Report",
          description="Generate a personalized financial analysis report using the multi-agent AI system",
          status_code=status.HTTP_200_OK)
async def generate_report(request: ReportRequest):
    """
    Generate a financial analysis report.

    **Flow:**
    1. Data Agent: Retrieves context from RAG and GraphRAG
    2. Context Agent: Fetches user preferences and history from Mem0
    3. Calculation Agent: Executes C++ calculations (Gemini selects functions)
    4. Narrative Agent: Generates personalized narrative (Gemini interprets results)
    5. Quality Agent: Validates report accuracy (Gemini checks for hallucinations)

    **Input:**
    - `user_query`: The user's question or request
    - `user_id`: User identifier for personalization
    - `session_id`: Optional session ID for conversation continuity

    **Output:**
    - `final_report_text`: The complete analysis report (Markdown)
    - `calculation_results`: All calculation outputs from C++ engine
    - `chart_json`: Vega-Lite chart specification (if applicable)
    - `metadata`: Workflow metadata (validation, retries, etc.)

    **Example:**
    ```json
    {
      "user_query": "Analyze my portfolio risk and compare to S&P 500",
      "user_id": "user_12345",
      "session_id": "session_abc"
    }
    ```
    """
    logger.info(f"Report request from user {request.user_id}: '{request.user_query}'")

    # Check prerequisites
    orch = _check_orchestrator()
    _check_gemini_api_key()

    try:
        # Generate report using orchestrator
        result = orch.generate_report(
            user_query=request.user_query,
            user_id=request.user_id,
            session_id=request.session_id
        )

        # Format response
        return ReportResponse(
            final_report_text=result["final_report_text"],
            calculation_results=CalculationResults(**result["calculation_results"]),
            chart_json=result.get("chart_json"),
            metadata=ReportMetadata(**result["metadata"])
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@app.post("/v1/user",
          response_model=SuccessResponse,
          summary="Create/Update User",
          description="Create or update user preferences for personalization",
          status_code=status.HTTP_201_CREATED)
async def create_user(request: UserCreateRequest):
    """
    Create or update user preferences.

    **Preferences:**
    - `risk_tolerance`: "conservative", "moderate", or "aggressive"
    - `reporting_style`: "concise", "detailed", or "technical"

    These preferences are used by the AI to personalize reports.

    **Example:**
    ```json
    {
      "user_id": "user_12345",
      "risk_tolerance": "moderate",
      "reporting_style": "detailed"
    }
    ```
    """
    logger.info(f"Creating/updating user {request.user_id}")

    orch = _check_orchestrator()

    try:
        orch.create_user(
            user_id=request.user_id,
            risk_tolerance=request.risk_tolerance.value,
            reporting_style=request.reporting_style.value
        )

        return SuccessResponse(
            success=True,
            message=f"User {request.user_id} preferences updated successfully"
        )

    except Exception as e:
        logger.error(f"User creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@app.get("/v1/user/{user_id}/context",
         response_model=UserContextResponse,
         summary="Get User Context",
         description="Retrieve user preferences, history, and temporal insights from memory")
async def get_user_context(user_id: str):
    """
    Get user context from memory system.

    Returns:
    - User preferences (risk tolerance, reporting style)
    - Recent activities (past reports, interactions)
    - Temporal insights (patterns, trends)

    **Example:**
    ```
    GET /v1/user/user_12345/context
    ```
    """
    logger.info(f"Fetching context for user {user_id}")

    orch = _check_orchestrator()

    try:
        # Fetch user context from Mem0
        context = orch.mem0.get_user_context(
            user_id=user_id,
            session_id=None  # Get global context, not session-specific
        )

        return UserContextResponse(
            user_id=user_id,
            risk_tolerance=context.preferences.risk_tolerance,
            reporting_style=context.preferences.reporting_style,
            recent_activities=[
                {
                    "type": act.activity_type,
                    "timestamp": act.timestamp.isoformat(),
                    "content": act.content
                }
                for act in context.history[:10]  # Last 10 activities
            ],
            temporal_insights=context.temporal_insights
        )

    except Exception as e:
        logger.error(f"Failed to fetch user context: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found or context unavailable"
        )


@app.post("/v1/knowledge/index",
          response_model=SuccessResponse,
          summary="Index Knowledge",
          description="Index documents into the RAG system for knowledge retrieval",
          status_code=status.HTTP_201_CREATED)
async def index_knowledge(request: DocumentIndexRequest):
    """
    Index documents into the RAG system.

    Documents will be:
    1. Embedded using sentence transformers
    2. Stored in vector database
    3. Made available for retrieval during report generation

    **Example:**
    ```json
    {
      "documents": [
        {
          "content": "The S&P 500 has returned 10% annually over 50 years...",
          "metadata": {"source": "historical_data", "category": "returns"}
        }
      ]
    }
    ```
    """
    logger.info(f"Indexing {len(request.documents)} documents")

    orch = _check_orchestrator()

    try:
        # Convert to Document objects
        docs = [
            Document(
                content=doc["content"],
                metadata=doc.get("metadata", {}),
                score=1.0  # Default score for indexed docs
            )
            for doc in request.documents
        ]

        # Index documents
        orch.index_knowledge(docs)

        return SuccessResponse(
            success=True,
            message=f"Successfully indexed {len(docs)} documents"
        )

    except Exception as e:
        logger.error(f"Document indexing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index documents: {str(e)}"
        )


# ============================================================================
# Main Entry Point (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "finrisk_ai.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload in development
        log_level="info"
    )
