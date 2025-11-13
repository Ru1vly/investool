"""
FinRisk AI Analyst - Advanced Multi-Agent Financial Analysis System

A state-of-the-art AI analyst report generator powered by Google's Gemini,
implementing 2024-2025 best practices with LangGraph orchestration,
Advanced RAG pipeline, and Active Memory (Mem0) for hyper-personalization.

Architecture:
- Phase 1: Data & Retrieval Infrastructure (RAG + GraphRAG)
- Phase 2: Memory & Agent Orchestration (LangGraph + Mem0)
- Phase 3: Specialized Agents (Data, Context, Calculation, Narrative, Quality)
- Phase 4: Production Optimizations (KV Caching, Model Tiering)
"""

__version__ = "1.0.0"
__author__ = "FinRisk AI Team"

from finrisk_ai.core.orchestrator import FinRiskOrchestrator
from finrisk_ai.core.state import AgentState

__all__ = ["FinRiskOrchestrator", "AgentState"]
