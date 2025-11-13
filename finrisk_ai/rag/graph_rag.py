"""
Phase 1.2: GraphRAG for Interconnected Financial Data

Tracks relationships between entities (e.g., "Interest Rate affects Housing Starts")
and provides structural context for complex financial queries.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import networkx as nx
import logging

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between financial entities"""
    AFFECTS = "affects"
    CORRELATES_WITH = "correlates_with"
    COMPONENT_OF = "component_of"
    DERIVED_FROM = "derived_from"
    INVERSE_OF = "inverse_of"
    CAUSES = "causes"
    INFLUENCES = "influences"


@dataclass
class GraphNode:
    """Represents an entity in the financial knowledge graph"""
    node_id: str
    entity_type: str  # e.g., "metric", "asset", "economic_indicator"
    name: str
    description: str
    metadata: Dict[str, Any]


@dataclass
class GraphEdge:
    """Represents a relationship between entities"""
    source_id: str
    target_id: str
    relationship: RelationshipType
    weight: float  # Strength of relationship (0-1)
    metadata: Dict[str, Any]


@dataclass
class GraphContext:
    """Context retrieved from GraphRAG"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    paths: List[List[str]]  # Paths between nodes
    subgraph_description: str


class GraphRAG:
    """
    GraphRAG implementation for financial knowledge.

    Maintains a knowledge graph of financial entities and their relationships.
    Provides structural context that pure vector search cannot capture.

    Example:
        "How does Interest Rate affect Housing Starts?"
        GraphRAG can retrieve:
        - Interest Rate (node)
        - Housing Starts (node)
        - Interest Rate → affects → Mortgage Rates → affects → Housing Starts (path)
    """

    def __init__(self):
        """Initialize GraphRAG with an empty knowledge graph"""
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        logger.info("GraphRAG initialized")

    def add_node(self, node: GraphNode) -> None:
        """
        Add a node to the knowledge graph.

        Args:
            node: GraphNode to add
        """
        self.nodes[node.node_id] = node
        self.graph.add_node(
            node.node_id,
            entity_type=node.entity_type,
            name=node.name,
            description=node.description,
            **node.metadata
        )

    def add_edge(self, edge: GraphEdge) -> None:
        """
        Add a relationship edge to the knowledge graph.

        Args:
            edge: GraphEdge to add
        """
        self.graph.add_edge(
            edge.source_id,
            edge.target_id,
            relationship=edge.relationship.value,
            weight=edge.weight,
            **edge.metadata
        )

    def find_node_by_name(self, name: str) -> Optional[GraphNode]:
        """Find node by entity name (case-insensitive)"""
        for node in self.nodes.values():
            if node.name.lower() == name.lower():
                return node
        return None

    def find_related_nodes(
        self,
        node_id: str,
        relationship_type: Optional[RelationshipType] = None,
        max_depth: int = 2
    ) -> List[GraphNode]:
        """
        Find nodes related to a given node.

        Args:
            node_id: Source node ID
            relationship_type: Filter by relationship type (optional)
            max_depth: Maximum search depth

        Returns:
            List of related nodes
        """
        if node_id not in self.graph:
            return []

        related_ids: Set[str] = set()

        # BFS to find related nodes up to max_depth
        queue = [(node_id, 0)]
        visited = {node_id}

        while queue:
            current_id, depth = queue.pop(0)

            if depth >= max_depth:
                continue

            # Get neighbors
            for neighbor in self.graph.neighbors(current_id):
                if neighbor in visited:
                    continue

                # Check relationship type filter
                edge_data = self.graph[current_id][neighbor]
                if relationship_type and edge_data['relationship'] != relationship_type.value:
                    continue

                related_ids.add(neighbor)
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))

        return [self.nodes[nid] for nid in related_ids if nid in self.nodes]

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_paths: int = 3
    ) -> List[List[str]]:
        """
        Find paths between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_paths: Maximum number of paths to return

        Returns:
            List of paths (each path is a list of node IDs)
        """
        if source_id not in self.graph or target_id not in self.graph:
            return []

        try:
            # Find all simple paths
            all_paths = list(nx.all_simple_paths(
                self.graph,
                source_id,
                target_id,
                cutoff=4  # Maximum path length
            ))

            # Return top paths (shortest first)
            return sorted(all_paths, key=len)[:max_paths]
        except nx.NetworkXNoPath:
            return []

    def query(
        self,
        query: str,
        max_nodes: int = 10
    ) -> GraphContext:
        """
        Query the knowledge graph for relevant context.

        Args:
            query: Natural language query
            max_nodes: Maximum nodes to return

        Returns:
            GraphContext with relevant nodes, edges, and paths
        """
        logger.info(f"GraphRAG query: '{query}'")

        # Extract potential entity mentions from query
        # In production, use NER (Named Entity Recognition)
        query_tokens = query.lower().split()

        # Find matching nodes
        matching_nodes = []
        for node in self.nodes.values():
            # Simple keyword matching (can be improved with NER)
            if any(token in node.name.lower() for token in query_tokens):
                matching_nodes.append(node)

        # Limit to top matches
        matching_nodes = matching_nodes[:max_nodes]

        # Find edges between matching nodes
        relevant_edges = []
        paths = []

        for i, node1 in enumerate(matching_nodes):
            for node2 in matching_nodes[i+1:]:
                # Find paths between these nodes
                node_paths = self.find_paths(node1.node_id, node2.node_id, max_paths=2)
                paths.extend(node_paths)

                # Get direct edges
                if self.graph.has_edge(node1.node_id, node2.node_id):
                    edge_data = self.graph[node1.node_id][node2.node_id]
                    relevant_edges.append(GraphEdge(
                        source_id=node1.node_id,
                        target_id=node2.node_id,
                        relationship=RelationshipType(edge_data['relationship']),
                        weight=edge_data['weight'],
                        metadata={}
                    ))

        # Create subgraph description
        description = self._create_subgraph_description(matching_nodes, relevant_edges, paths)

        return GraphContext(
            nodes=matching_nodes,
            edges=relevant_edges,
            paths=paths,
            subgraph_description=description
        )

    def _create_subgraph_description(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        paths: List[List[str]]
    ) -> str:
        """Create human-readable description of subgraph"""

        description_parts = []

        # Describe nodes
        if nodes:
            node_names = [node.name for node in nodes]
            description_parts.append(f"Relevant entities: {', '.join(node_names)}")

        # Describe relationships
        if edges:
            edge_descriptions = []
            for edge in edges[:5]:  # Limit to 5 edges
                source_name = self.nodes[edge.source_id].name
                target_name = self.nodes[edge.target_id].name
                edge_descriptions.append(
                    f"{source_name} {edge.relationship.value} {target_name}"
                )
            description_parts.append(
                f"Relationships: {'; '.join(edge_descriptions)}"
            )

        # Describe paths
        if paths:
            path_descriptions = []
            for path in paths[:3]:  # Limit to 3 paths
                path_names = [self.nodes[nid].name for nid in path if nid in self.nodes]
                path_descriptions.append(" → ".join(path_names))
            description_parts.append(
                f"Connection paths: {'; '.join(path_descriptions)}"
            )

        return ". ".join(description_parts) if description_parts else "No relevant context found"

    def build_financial_knowledge_graph(self) -> None:
        """
        Build a pre-populated knowledge graph with common financial relationships.

        This is a starter graph - in production, this would be populated from:
        - Financial ontologies
        - Academic research
        - Market data relationships
        """
        logger.info("Building financial knowledge graph...")

        # Risk Metrics
        self.add_node(GraphNode(
            node_id="var",
            entity_type="metric",
            name="Value at Risk (VaR)",
            description="Maximum expected loss at a confidence level",
            metadata={"formula": "Formula 12", "category": "risk"}
        ))

        self.add_node(GraphNode(
            node_id="volatility",
            entity_type="metric",
            name="Volatility",
            description="Standard deviation of returns",
            metadata={"formula": "Formula 5", "category": "risk"}
        ))

        self.add_node(GraphNode(
            node_id="sortino",
            entity_type="metric",
            name="Sortino Ratio",
            description="Risk-adjusted return using downside deviation",
            metadata={"formula": "Formula 11", "category": "performance"}
        ))

        self.add_node(GraphNode(
            node_id="sharpe",
            entity_type="metric",
            name="Sharpe Ratio",
            description="Risk-adjusted return using total volatility",
            metadata={"formula": "Formula 6", "category": "performance"}
        ))

        # Economic Indicators
        self.add_node(GraphNode(
            node_id="interest_rate",
            entity_type="economic_indicator",
            name="Interest Rate",
            description="Federal Reserve interest rate",
            metadata={"category": "monetary_policy"}
        ))

        self.add_node(GraphNode(
            node_id="inflation",
            entity_type="economic_indicator",
            name="Inflation",
            description="Rate of price increases",
            metadata={"category": "economic"}
        ))

        # Assets
        self.add_node(GraphNode(
            node_id="bonds",
            entity_type="asset",
            name="Bonds",
            description="Fixed income securities",
            metadata={"category": "fixed_income"}
        ))

        self.add_node(GraphNode(
            node_id="stocks",
            entity_type="asset",
            name="Stocks",
            description="Equity securities",
            metadata={"category": "equity"}
        ))

        # Relationships
        self.add_edge(GraphEdge(
            source_id="volatility",
            target_id="var",
            relationship=RelationshipType.COMPONENT_OF,
            weight=0.9,
            metadata={"description": "Volatility is a key input to VaR calculation"}
        ))

        self.add_edge(GraphEdge(
            source_id="volatility",
            target_id="sharpe",
            relationship=RelationshipType.COMPONENT_OF,
            weight=1.0,
            metadata={"description": "Sharpe Ratio uses total volatility"}
        ))

        self.add_edge(GraphEdge(
            source_id="interest_rate",
            target_id="bonds",
            relationship=RelationshipType.AFFECTS,
            weight=0.95,
            metadata={"description": "Interest rates inversely affect bond prices"}
        ))

        self.add_edge(GraphEdge(
            source_id="interest_rate",
            target_id="inflation",
            relationship=RelationshipType.INFLUENCES,
            weight=0.85,
            metadata={"description": "Central banks use rates to control inflation"}
        ))

        self.add_edge(GraphEdge(
            source_id="inflation",
            target_id="stocks",
            relationship=RelationshipType.AFFECTS,
            weight=0.7,
            metadata={"description": "Inflation affects corporate earnings and valuations"}
        ))

        logger.info(f"Knowledge graph built: {len(self.nodes)} nodes, {self.graph.number_of_edges()} edges")
