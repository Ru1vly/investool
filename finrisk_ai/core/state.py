"""
Phase 2.2: Agent State Definition

Defines the shared state object that all agents read from and write to.
This is the central data structure for the LangGraph workflow.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from finrisk_ai.rag.hybrid_search import Document
from finrisk_ai.rag.graph_rag import GraphNode
from finrisk_ai.memory.mem0_system import UserPreferences


@dataclass
class AgentState:
    """
    Central state for the multi-agent workflow.

    This state is shared across all agents and updated progressively
    as the workflow executes.
    """

    # ==================== Input ====================
    user_query: str
    user_id: str
    session_id: str

    # ==================== Data Agent ====================
    rag_context: List[Document] = field(default_factory=list)
    graph_rag_context: List[GraphNode] = field(default_factory=list)

    # ==================== Context Agent ====================
    user_preferences: Optional[UserPreferences] = None
    user_history: List[Dict[str, Any]] = field(default_factory=list)
    temporal_insights: List[str] = field(default_factory=list)

    # ==================== Calculation Agent ====================
    calculation_plan: str = ""
    calculation_results: Dict[str, float] = field(default_factory=dict)
    calculation_code: str = ""
    calculation_error: Optional[str] = None

    # ==================== Narrative Agent ====================
    macro_plan_json: Dict[str, Any] = field(default_factory=dict)
    final_report_text: str = ""
    chart_json: Dict[str, Any] = field(default_factory=dict)

    # ==================== Quality Agent ====================
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    retry_count: int = 0

    # ==================== Metadata ====================
    workflow_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "user_query": self.user_query,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "rag_context": [{"content": doc.content, "score": doc.score} for doc in self.rag_context],
            "graph_rag_context": [{"name": node.name, "description": node.description} for node in self.graph_rag_context],
            "user_preferences": self.user_preferences.__dict__ if self.user_preferences else None,
            "calculation_results": self.calculation_results,
            "final_report_text": self.final_report_text,
            "validation_passed": self.validation_passed,
            "validation_errors": self.validation_errors,
        }

    @classmethod
    def from_query(
        cls,
        user_query: str,
        user_id: str,
        session_id: str
    ) -> "AgentState":
        """
        Create initial state from user query.

        Args:
            user_query: User's question/request
            user_id: User identifier
            session_id: Session identifier

        Returns:
            AgentState initialized with query
        """
        return cls(
            user_query=user_query,
            user_id=user_id,
            session_id=session_id
        )
