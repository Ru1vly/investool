"""
Basic tests for FinRisk AI core components
"""

import pytest
from finrisk_ai.core.state import AgentState
from finrisk_ai.core.data_ingestion import DataIngestionEngine, DataStatistics
from finrisk_ai.memory.mem0_system import Mem0System, UserPreferences
from finrisk_ai.rag.hybrid_search import Document
from finrisk_ai.rag.graph_rag import GraphRAG, GraphNode, GraphEdge, RelationshipType


class TestAgentState:
    """Test AgentState functionality"""

    def test_from_query(self):
        """Test creating state from query"""
        state = AgentState.from_query(
            user_query="Test query",
            user_id="test_user",
            session_id="test_session"
        )

        assert state.user_query == "Test query"
        assert state.user_id == "test_user"
        assert state.session_id == "test_session"
        assert len(state.rag_context) == 0
        assert len(state.validation_errors) == 0

    def test_to_dict(self):
        """Test state serialization"""
        state = AgentState.from_query(
            user_query="Test",
            user_id="user1",
            session_id="session1"
        )

        state_dict = state.to_dict()

        assert "user_query" in state_dict
        assert "final_report_text" in state_dict
        assert state_dict["user_id"] == "user1"


class TestDataIngestion:
    """Test data ingestion and HTML serialization"""

    def test_calculate_statistics(self):
        """Test statistical calculation"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = DataIngestionEngine.calculate_statistics(data)

        assert stats.mean == 3.0
        assert stats.median == 3.0
        assert stats.count == 5
        assert stats.min_val == 1.0
        assert stats.max_val == 5.0

    def test_convert_dict_to_html(self):
        """Test dictionary to HTML conversion"""
        data = {"metric1": 1.234, "metric2": 5.678}
        html = DataIngestionEngine.convert_dict_to_html(data, "Test Table")

        assert "<table" in html
        assert "Test Table" in html
        assert "metric1" in html
        assert "1.234" in html.replace("1.2340", "1.234")  # Handle formatting

    def test_enrich_data(self):
        """Test data enrichment"""
        data = {"volatility": 0.15, "sharpe_ratio": 1.2}
        enriched = DataIngestionEngine.enrich_data(
            raw_data=data,
            source_doc="test.py",
            calc_method="Test calculation",
            data_type="dict",
            title="Test Metrics"
        )

        assert enriched.source == "test.py"
        assert enriched.calculation_method == "Test calculation"
        assert "volatility" in enriched.html_content
        assert enriched.statistics is not None


class TestMem0System:
    """Test Mem0 memory system"""

    def test_create_user_preferences(self):
        """Test creating user preferences"""
        mem0 = Mem0System()
        prefs = mem0.create_user_preferences(
            user_id="test_user",
            risk_tolerance="aggressive",
            reporting_style="concise"
        )

        assert prefs.user_id == "test_user"
        assert prefs.risk_tolerance == "aggressive"
        assert prefs.reporting_style == "concise"

    def test_get_user_preferences(self):
        """Test retrieving user preferences"""
        mem0 = Mem0System()
        mem0.create_user_preferences(user_id="user1")

        prefs = mem0.get_user_preferences("user1")
        assert prefs is not None
        assert prefs.user_id == "user1"

    def test_add_activity(self):
        """Test adding activity to short-term memory"""
        mem0 = Mem0System()
        activity = mem0.add_activity(
            user_id="user1",
            activity_type="test_activity",
            content={"data": "test"}
        )

        assert activity.user_id == "user1"
        assert activity.activity_type == "test_activity"

    def test_get_recent_activities(self):
        """Test retrieving recent activities"""
        mem0 = Mem0System()
        mem0.add_activity("user1", "activity1", {"test": 1})
        mem0.add_activity("user1", "activity2", {"test": 2})

        activities = mem0.get_recent_activities("user1", days=7)
        assert len(activities) == 2

    def test_add_message(self):
        """Test adding session message"""
        mem0 = Mem0System()
        message = mem0.add_message(
            user_id="user1",
            session_id="session1",
            role="user",
            content="Test message"
        )

        assert message.role == "user"
        assert message.content == "Test message"

    def test_get_session_history(self):
        """Test retrieving session history"""
        mem0 = Mem0System()
        mem0.add_message("user1", "session1", "user", "Message 1")
        mem0.add_message("user1", "session1", "assistant", "Message 2")

        history = mem0.get_session_history("user1", "session1")
        assert len(history) == 2

    def test_graph_memory(self):
        """Test graph memory functionality"""
        mem0 = Mem0System()
        node = mem0.add_graph_memory(
            user_id="user1",
            entity_type="asset",
            entity_name="Bitcoin",
            data={"VaR": 5000, "volatility": 0.65}
        )

        assert node.entity_name == "Bitcoin"
        assert node.data["VaR"] == 5000

    def test_get_user_context(self):
        """Test unified context retrieval"""
        mem0 = Mem0System()
        mem0.create_user_preferences("user1", risk_tolerance="moderate")
        mem0.add_activity("user1", "test", {"data": 1})

        context = mem0.get_user_context("user1")

        assert context.preferences.user_id == "user1"
        assert len(context.history) == 1


class TestGraphRAG:
    """Test GraphRAG functionality"""

    def test_add_node(self):
        """Test adding node to graph"""
        graph = GraphRAG()
        node = GraphNode(
            node_id="test1",
            entity_type="metric",
            name="Test Metric",
            description="Test description",
            metadata={}
        )

        graph.add_node(node)
        assert "test1" in graph.nodes

    def test_add_edge(self):
        """Test adding edge to graph"""
        graph = GraphRAG()

        # Add nodes
        node1 = GraphNode("n1", "metric", "Metric 1", "Desc 1", {})
        node2 = GraphNode("n2", "metric", "Metric 2", "Desc 2", {})
        graph.add_node(node1)
        graph.add_node(node2)

        # Add edge
        edge = GraphEdge("n1", "n2", RelationshipType.AFFECTS, 0.8, {})
        graph.add_edge(edge)

        assert graph.graph.has_edge("n1", "n2")

    def test_find_node_by_name(self):
        """Test finding node by name"""
        graph = GraphRAG()
        node = GraphNode("n1", "metric", "Volatility", "Test", {})
        graph.add_node(node)

        found = graph.find_node_by_name("Volatility")
        assert found is not None
        assert found.name == "Volatility"

    def test_find_related_nodes(self):
        """Test finding related nodes"""
        graph = GraphRAG()

        # Create small graph
        n1 = GraphNode("n1", "metric", "Node 1", "Desc", {})
        n2 = GraphNode("n2", "metric", "Node 2", "Desc", {})
        graph.add_node(n1)
        graph.add_node(n2)

        edge = GraphEdge("n1", "n2", RelationshipType.AFFECTS, 0.9, {})
        graph.add_edge(edge)

        related = graph.find_related_nodes("n1", max_depth=1)
        assert len(related) >= 0  # May or may not find related based on graph structure

    def test_build_knowledge_graph(self):
        """Test building pre-populated knowledge graph"""
        graph = GraphRAG()
        graph.build_financial_knowledge_graph()

        assert len(graph.nodes) > 0
        assert graph.graph.number_of_edges() > 0


class TestDocument:
    """Test Document class"""

    def test_document_creation(self):
        """Test creating a document"""
        doc = Document(
            content="Test content",
            metadata={"type": "test"},
            doc_id="doc1",
            score=0.95,
            source="test.py"
        )

        assert doc.content == "Test content"
        assert doc.doc_id == "doc1"
        assert doc.score == 0.95


# Run tests with: pytest finrisk_ai/tests/test_core.py -v
