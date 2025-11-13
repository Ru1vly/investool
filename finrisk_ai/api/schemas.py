"""
Phase 3.1: API Schemas

Pydantic models for request/response validation and documentation.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class RiskTolerance(str, Enum):
    """User risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ReportingStyle(str, Enum):
    """Report generation styles"""
    CONCISE = "concise"
    DETAILED = "detailed"
    TECHNICAL = "technical"


# ============================================================================
# Request Models
# ============================================================================

class ReportRequest(BaseModel):
    """Request to generate a financial analysis report"""

    user_query: str = Field(
        ...,
        description="User's question or request",
        example="Analyze the risk profile of my portfolio and compare it to the S&P 500"
    )
    user_id: str = Field(
        ...,
        description="Unique user identifier",
        example="user_12345"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session identifier for conversation continuity",
        example="session_abc123"
    )

    @validator('user_query')
    def query_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('user_query cannot be empty')
        return v.strip()

    @validator('session_id', pre=True, always=True)
    def generate_session_id(cls, v, values):
        """Generate session ID if not provided"""
        if v is None and 'user_id' in values:
            import uuid
            return f"{values['user_id']}_session_{uuid.uuid4().hex[:8]}"
        return v

    class Config:
        schema_extra = {
            "example": {
                "user_query": "What is the Sharpe ratio of my portfolio and what does it mean?",
                "user_id": "user_12345",
                "session_id": "session_abc123"
            }
        }


class UserCreateRequest(BaseModel):
    """Request to create or update user preferences"""

    user_id: str = Field(
        ...,
        description="Unique user identifier",
        example="user_12345"
    )
    risk_tolerance: RiskTolerance = Field(
        default=RiskTolerance.MODERATE,
        description="User's risk tolerance level"
    )
    reporting_style: ReportingStyle = Field(
        default=ReportingStyle.DETAILED,
        description="Preferred report style"
    )

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_12345",
                "risk_tolerance": "moderate",
                "reporting_style": "detailed"
            }
        }


class DocumentIndexRequest(BaseModel):
    """Request to index documents into RAG system"""

    documents: List[Dict[str, Any]] = Field(
        ...,
        description="List of documents to index",
        example=[
            {
                "content": "The S&P 500 has returned an average of 10% annually over the past 50 years...",
                "metadata": {"source": "historical_data", "category": "market_returns"}
            }
        ]
    )

    @validator('documents')
    def documents_not_empty(cls, v):
        if not v:
            raise ValueError('documents list cannot be empty')
        return v

    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "content": "Portfolio diversification reduces risk through asset allocation.",
                        "metadata": {"source": "financial_basics", "topic": "diversification"}
                    },
                    {
                        "content": "The Sharpe Ratio measures risk-adjusted returns.",
                        "metadata": {"source": "risk_metrics", "topic": "performance"}
                    }
                ]
            }
        }


# ============================================================================
# Response Models
# ============================================================================

class CalculationResults(BaseModel):
    """Financial calculation results"""

    volatility: Optional[float] = Field(None, description="Portfolio volatility")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    var_95: Optional[float] = Field(None, description="Value at Risk (95%)")
    var_99: Optional[float] = Field(None, description="Value at Risk (99%)")
    beta: Optional[float] = Field(None, description="Beta vs market")
    z_score: Optional[float] = Field(None, description="Z-Score")

    # Allow additional fields
    class Config:
        extra = "allow"


class ReportMetadata(BaseModel):
    """Metadata about the report generation process"""

    validation_passed: bool = Field(..., description="Whether quality validation passed")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors if any")
    retry_count: int = Field(..., description="Number of retries for quality validation")
    rag_documents_retrieved: int = Field(..., description="Number of RAG documents used")
    graph_nodes_retrieved: int = Field(..., description="Number of graph nodes used")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "validation_passed": True,
                "validation_errors": [],
                "retry_count": 0,
                "rag_documents_retrieved": 5,
                "graph_nodes_retrieved": 10,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class ReportResponse(BaseModel):
    """Response containing the generated financial report"""

    final_report_text: str = Field(
        ...,
        description="The complete financial analyst report"
    )
    calculation_results: CalculationResults = Field(
        ...,
        description="Detailed calculation results from C++ engine"
    )
    chart_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Vega-Lite chart specification (if applicable)"
    )
    metadata: ReportMetadata = Field(
        ...,
        description="Metadata about the report generation process"
    )

    class Config:
        schema_extra = {
            "example": {
                "final_report_text": "# Portfolio Risk Analysis\n\nYour portfolio shows a Sharpe ratio of 1.45...",
                "calculation_results": {
                    "volatility": 0.15,
                    "sharpe_ratio": 1.45,
                    "sortino_ratio": 1.82,
                    "var_95": 5000.00
                },
                "chart_json": {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "mark": "bar",
                    "data": {"values": []}
                },
                "metadata": {
                    "validation_passed": True,
                    "validation_errors": [],
                    "retry_count": 0,
                    "rag_documents_retrieved": 5,
                    "graph_nodes_retrieved": 10,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }


class UserContextResponse(BaseModel):
    """Response containing user context from memory"""

    user_id: str
    risk_tolerance: str
    reporting_style: str
    recent_activities: List[Dict[str, Any]] = Field(default_factory=list)
    temporal_insights: List[str] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_12345",
                "risk_tolerance": "moderate",
                "reporting_style": "detailed",
                "recent_activities": [
                    {
                        "type": "report_generated",
                        "timestamp": "2024-01-15T10:00:00Z",
                        "content": {"query": "Analyze my portfolio"}
                    }
                ],
                "temporal_insights": [
                    "User consistently asks about risk metrics",
                    "User prefers detailed explanations"
                ]
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "User preferences updated successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input parameters",
                "detail": "user_query cannot be empty"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    cpp_engine_available: bool = Field(..., description="C++ engine availability")
    components: Dict[str, str] = Field(..., description="Component statuses")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "cpp_engine_available": True,
                "components": {
                    "orchestrator": "operational",
                    "cpp_engine": "operational",
                    "vector_db": "operational",
                    "graph_rag": "operational",
                    "mem0_system": "operational"
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
