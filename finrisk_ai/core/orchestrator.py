"""
Phase 2.2: LangGraph Orchestrator

Main orchestration engine that coordinates all specialized agents.
Implements the complete multi-agent workflow with conditional routing.
"""

from typing import Dict, Any, Optional
import logging
from langgraph.graph import StateGraph, END

from finrisk_ai.core.state import AgentState
from finrisk_ai.agents.specialized_agents import (
    DataAgent,
    ContextAgent,
    CalculationAgent,
    NarrativeAgent,
    QualityAgent,
    check_quality_gate
)
from finrisk_ai.rag.hybrid_search import VectorDatabase
from finrisk_ai.rag.graph_rag import GraphRAG
from finrisk_ai.memory.mem0_system import Mem0System

logger = logging.getLogger(__name__)


class FinRiskOrchestrator:
    """
    Main orchestrator for the FinRisk AI Analyst system.

    Coordinates all agents using LangGraph for stateful workflow management.

    Workflow:
    1. Data Agent → Fetch RAG and GraphRAG context
    2. Context Agent → Fetch user memory and preferences
    3. Calculation Agent → Execute financial calculations
    4. Narrative Agent → Generate personalized report
    5. Quality Agent → Validate report
    6. Conditional → Pass or retry
    """

    def __init__(
        self,
        gemini_api_key: str,
        vector_db: Optional[VectorDatabase] = None,
        graph_rag: Optional[GraphRAG] = None,
        mem0_system: Optional[Mem0System] = None,
        gemini_pro_model: str = "gemini-1.5-pro-latest",
        gemini_flash_model: str = "gemini-1.5-flash-latest"
    ):
        """
        Initialize FinRisk Orchestrator.

        Args:
            gemini_api_key: Google Gemini API key
            vector_db: Vector database (creates new if None)
            graph_rag: GraphRAG system (creates new if None)
            mem0_system: Mem0 memory system (creates new if None)
            gemini_pro_model: Gemini Pro model name
            gemini_flash_model: Gemini Flash model name
        """
        logger.info("Initializing FinRiskOrchestrator...")

        # Initialize components
        self.vector_db = vector_db or VectorDatabase()
        self.graph_rag = graph_rag or GraphRAG()
        self.mem0 = mem0_system or Mem0System()

        # Initialize agents
        self.data_agent = DataAgent(self.vector_db, self.graph_rag)
        self.context_agent = ContextAgent(self.mem0)
        self.calculation_agent = CalculationAgent(gemini_api_key, gemini_pro_model)
        self.narrative_agent = NarrativeAgent(gemini_api_key, gemini_pro_model)
        self.quality_agent = QualityAgent(gemini_api_key, gemini_flash_model)

        # Build LangGraph workflow
        self.workflow = self._build_workflow()

        logger.info("FinRiskOrchestrator initialized successfully")

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with all agents and conditional routing.

        Returns:
            Compiled StateGraph
        """
        logger.info("Building LangGraph workflow...")

        # Create workflow with AgentState
        workflow = StateGraph(AgentState)

        # Define agent nodes
        workflow.add_node("data_agent", self._data_agent_node)
        workflow.add_node("context_agent", self._context_agent_node)
        workflow.add_node("calculation_agent", self._calculation_agent_node)
        workflow.add_node("narrative_agent", self._narrative_agent_node)
        workflow.add_node("quality_agent", self._quality_agent_node)

        # Define the flow (edges)
        workflow.set_entry_point("data_agent")

        # Sequential flow (could be parallelized in production)
        workflow.add_edge("data_agent", "context_agent")
        workflow.add_edge("context_agent", "calculation_agent")
        workflow.add_edge("calculation_agent", "narrative_agent")
        workflow.add_edge("narrative_agent", "quality_agent")

        # Conditional routing from quality agent
        workflow.add_conditional_edges(
            "quality_agent",
            check_quality_gate,
            {
                "pass": END,  # Validation passed → end workflow
                "fail": "narrative_agent"  # Validation failed → retry narrative
            }
        )

        # Compile the graph
        compiled_workflow = workflow.compile()

        logger.info("LangGraph workflow compiled")

        return compiled_workflow

    # ==================== Agent Node Wrappers ====================

    def _data_agent_node(self, state: AgentState) -> AgentState:
        """Data Agent node wrapper"""
        logger.info("→ Executing Data Agent")
        updates = self.data_agent.execute(state)

        # Update state
        for key, value in updates.items():
            setattr(state, key, value)

        return state

    def _context_agent_node(self, state: AgentState) -> AgentState:
        """Context Agent node wrapper"""
        logger.info("→ Executing Context Agent")
        updates = self.context_agent.execute(state)

        for key, value in updates.items():
            setattr(state, key, value)

        return state

    def _calculation_agent_node(self, state: AgentState) -> AgentState:
        """Calculation Agent node wrapper"""
        logger.info("→ Executing Calculation Agent")
        updates = self.calculation_agent.execute(state)

        for key, value in updates.items():
            setattr(state, key, value)

        return state

    def _narrative_agent_node(self, state: AgentState) -> AgentState:
        """Narrative Agent node wrapper"""
        logger.info("→ Executing Narrative Agent")
        updates = self.narrative_agent.execute(state)

        for key, value in updates.items():
            setattr(state, key, value)

        return state

    def _quality_agent_node(self, state: AgentState) -> AgentState:
        """Quality Agent node wrapper"""
        logger.info("→ Executing Quality Agent")
        updates = self.quality_agent.execute(state)

        for key, value in updates.items():
            setattr(state, key, value)

        return state

    # ==================== Public API ====================

    def generate_report(
        self,
        user_query: str,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Main entry point: Generate a financial analyst report.

        Args:
            user_query: User's question/request
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Dict containing:
            - final_report_text: The generated report
            - calculation_results: Calculation outputs
            - chart_json: Vega-Lite chart specification
            - metadata: Workflow metadata
        """
        logger.info(f"Generating report for user {user_id}: '{user_query}'")

        # Create initial state
        initial_state = AgentState.from_query(
            user_query=user_query,
            user_id=user_id,
            session_id=session_id
        )

        # Execute workflow
        final_state = self.workflow.invoke(initial_state)

        # Save report to memory
        self.mem0.add_activity(
            user_id=user_id,
            activity_type="report_generated",
            content={
                "query": user_query,
                "report": final_state.final_report_text[:500],  # Truncate for storage
                "metrics": final_state.calculation_results
            }
        )

        # Save assistant response to session
        self.mem0.add_message(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=final_state.final_report_text
        )

        # Return results
        return {
            "final_report_text": final_state.final_report_text,
            "calculation_results": final_state.calculation_results,
            "chart_json": final_state.chart_json,
            "metadata": {
                "validation_passed": final_state.validation_passed,
                "validation_errors": final_state.validation_errors,
                "retry_count": final_state.retry_count,
                "rag_documents_retrieved": len(final_state.rag_context),
                "graph_nodes_retrieved": len(final_state.graph_rag_context)
            }
        }

    def index_knowledge(self, documents: list) -> None:
        """
        Index documents into the RAG system.

        Args:
            documents: List of Document objects to index
        """
        logger.info(f"Indexing {len(documents)} documents...")
        self.data_agent.vector_db.search_engine.index_documents(documents)
        logger.info("Indexing complete")

    def build_knowledge_graph(self) -> None:
        """Build the financial knowledge graph with standard relationships"""
        logger.info("Building knowledge graph...")
        self.graph_rag.build_financial_knowledge_graph()
        logger.info("Knowledge graph built")

    def create_user(
        self,
        user_id: str,
        risk_tolerance: str = "moderate",
        reporting_style: str = "detailed"
    ) -> None:
        """
        Create a new user with preferences.

        Args:
            user_id: Unique user identifier
            risk_tolerance: "conservative", "moderate", or "aggressive"
            reporting_style: "concise", "detailed", or "technical"
        """
        self.mem0.create_user_preferences(
            user_id=user_id,
            risk_tolerance=risk_tolerance,
            reporting_style=reporting_style
        )
        logger.info(f"Created user {user_id} with {risk_tolerance} risk tolerance")
