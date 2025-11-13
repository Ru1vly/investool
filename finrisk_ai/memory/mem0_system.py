"""
Phase 2.1: Active Memory System (Mem0) for Hyper-Personalization

Implements hierarchical memory storage:
- Long-Term Memory: User preferences, risk profiles, terminology preferences
- Short-Term Memory: Recent reports, recently viewed assets
- Session Memory: Current conversation history
- Mem0^g (Graph Memory): Temporal reasoning and relationship tracking
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory storage"""
    LONG_TERM = "long_term"
    SHORT_TERM = "short_term"
    SESSION = "session"
    GRAPH = "graph"


@dataclass
class UserPreferences:
    """Long-term user preferences"""
    user_id: str
    risk_tolerance: str  # "conservative", "moderate", "aggressive"
    preferred_terminology: Dict[str, str]  # e.g., {"profit": "EBITDA"}
    reporting_style: str  # "detailed", "concise", "technical"
    favorite_metrics: List[str]  # e.g., ["Sharpe Ratio", "Sortino Ratio"]
    language: str = "en"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RecentActivity:
    """Short-term memory of recent activities"""
    activity_id: str
    user_id: str
    activity_type: str  # "report_generated", "asset_viewed", "calculation_run"
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionMessage:
    """Session-level conversation message"""
    message_id: str
    user_id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphMemoryNode:
    """Mem0^g - Graph-enhanced memory for temporal reasoning"""
    node_id: str
    user_id: str
    entity_type: str  # "asset", "metric", "event"
    entity_name: str
    timestamp: datetime
    data: Dict[str, Any]
    relationships: List[str] = field(default_factory=list)  # Connected node IDs


@dataclass
class UserContext:
    """Complete user context aggregated from all memory types"""
    preferences: UserPreferences
    history: List[RecentActivity]
    session_messages: List[SessionMessage]
    graph_context: List[GraphMemoryNode]
    temporal_insights: List[str]


class Mem0System:
    """
    Active Memory System for hyper-personalized financial analysis.

    Implements hierarchical memory with temporal reasoning capabilities.
    Based on Mem0^g architecture for tracking metrics over time.
    """

    def __init__(self, storage_backend: str = "in_memory"):
        """
        Initialize Mem0 system.

        Args:
            storage_backend: "in_memory", "sqlite", or "postgresql"
        """
        self.storage_backend = storage_backend

        # In-memory storage (in production, use database)
        self.long_term_memory: Dict[str, UserPreferences] = {}
        self.short_term_memory: Dict[str, List[RecentActivity]] = {}
        self.session_memory: Dict[str, List[SessionMessage]] = {}
        self.graph_memory: Dict[str, List[GraphMemoryNode]] = {}

        logger.info(f"Mem0System initialized with {storage_backend} backend")

    # ==================== Long-Term Memory ====================

    def create_user_preferences(
        self,
        user_id: str,
        risk_tolerance: str = "moderate",
        reporting_style: str = "detailed",
        preferred_terminology: Optional[Dict[str, str]] = None
    ) -> UserPreferences:
        """
        Create or update long-term user preferences.

        Args:
            user_id: Unique user identifier
            risk_tolerance: Risk tolerance level
            reporting_style: Preferred reporting style
            preferred_terminology: Terminology preferences

        Returns:
            UserPreferences object
        """
        prefs = UserPreferences(
            user_id=user_id,
            risk_tolerance=risk_tolerance,
            preferred_terminology=preferred_terminology or {},
            reporting_style=reporting_style,
            favorite_metrics=[]
        )

        self.long_term_memory[user_id] = prefs
        logger.info(f"Created preferences for user {user_id}")

        return prefs

    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get long-term preferences for a user"""
        return self.long_term_memory.get(user_id)

    def update_user_preferences(
        self,
        user_id: str,
        **updates
    ) -> UserPreferences:
        """
        Update specific user preferences.

        Args:
            user_id: User identifier
            **updates: Fields to update

        Returns:
            Updated UserPreferences
        """
        if user_id not in self.long_term_memory:
            raise ValueError(f"No preferences found for user {user_id}")

        prefs = self.long_term_memory[user_id]

        for key, value in updates.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        prefs.updated_at = datetime.now()
        logger.info(f"Updated preferences for user {user_id}: {updates}")

        return prefs

    # ==================== Short-Term Memory ====================

    def add_activity(
        self,
        user_id: str,
        activity_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> RecentActivity:
        """
        Add an activity to short-term memory.

        Args:
            user_id: User identifier
            activity_type: Type of activity
            content: Activity content/data
            metadata: Additional metadata

        Returns:
            RecentActivity object
        """
        activity = RecentActivity(
            activity_id=f"{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            activity_type=activity_type,
            content=content,
            metadata=metadata or {}
        )

        if user_id not in self.short_term_memory:
            self.short_term_memory[user_id] = []

        self.short_term_memory[user_id].append(activity)

        # Keep only last 7 days of activities
        cutoff = datetime.now() - timedelta(days=7)
        self.short_term_memory[user_id] = [
            act for act in self.short_term_memory[user_id]
            if act.timestamp > cutoff
        ]

        logger.debug(f"Added {activity_type} activity for user {user_id}")

        return activity

    def get_recent_activities(
        self,
        user_id: str,
        days: int = 7,
        activity_type: Optional[str] = None
    ) -> List[RecentActivity]:
        """
        Get recent activities for a user.

        Args:
            user_id: User identifier
            days: Number of days to look back
            activity_type: Filter by activity type (optional)

        Returns:
            List of recent activities
        """
        if user_id not in self.short_term_memory:
            return []

        cutoff = datetime.now() - timedelta(days=days)
        activities = [
            act for act in self.short_term_memory[user_id]
            if act.timestamp > cutoff
        ]

        if activity_type:
            activities = [act for act in activities if act.activity_type == activity_type]

        return sorted(activities, key=lambda x: x.timestamp, reverse=True)

    # ==================== Session Memory ====================

    def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionMessage:
        """
        Add a message to session memory.

        Args:
            user_id: User identifier
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            metadata: Additional metadata

        Returns:
            SessionMessage object
        """
        message = SessionMessage(
            message_id=f"{session_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )

        key = f"{user_id}_{session_id}"
        if key not in self.session_memory:
            self.session_memory[key] = []

        self.session_memory[key].append(message)

        return message

    def get_session_history(
        self,
        user_id: str,
        session_id: str
    ) -> List[SessionMessage]:
        """Get conversation history for a session"""
        key = f"{user_id}_{session_id}"
        return self.session_memory.get(key, [])

    # ==================== Graph Memory (Mem0^g) ====================

    def add_graph_memory(
        self,
        user_id: str,
        entity_type: str,
        entity_name: str,
        data: Dict[str, Any],
        relationships: Optional[List[str]] = None
    ) -> GraphMemoryNode:
        """
        Add a node to graph memory for temporal tracking.

        Example: Track Bitcoin metrics over time
        - Node 1: Bitcoin, Jan 2024, VaR=5000
        - Node 2: Bitcoin, Feb 2024, VaR=7000
        - Relationship: temporal_sequence

        Args:
            user_id: User identifier
            entity_type: Type of entity
            entity_name: Name of entity (e.g., "Bitcoin")
            data: Metrics/data for this timestamp
            relationships: Connected node IDs

        Returns:
            GraphMemoryNode object
        """
        node = GraphMemoryNode(
            node_id=f"{user_id}_{entity_name}_{datetime.now().timestamp()}",
            user_id=user_id,
            entity_type=entity_type,
            entity_name=entity_name,
            timestamp=datetime.now(),
            data=data,
            relationships=relationships or []
        )

        if user_id not in self.graph_memory:
            self.graph_memory[user_id] = []

        self.graph_memory[user_id].append(node)

        logger.debug(f"Added graph memory node for {entity_name}")

        return node

    def query_user_graph(
        self,
        user_id: str,
        entity_name: Optional[str] = None,
        days: int = 30
    ) -> List[GraphMemoryNode]:
        """
        Query graph memory for temporal context.

        Args:
            user_id: User identifier
            entity_name: Filter by entity name (optional)
            days: Number of days to look back

        Returns:
            List of graph memory nodes
        """
        if user_id not in self.graph_memory:
            return []

        cutoff = datetime.now() - timedelta(days=days)
        nodes = [
            node for node in self.graph_memory[user_id]
            if node.timestamp > cutoff
        ]

        if entity_name:
            nodes = [node for node in nodes if node.entity_name == entity_name]

        return sorted(nodes, key=lambda x: x.timestamp)

    def get_temporal_insights(
        self,
        user_id: str,
        entity_name: str
    ) -> List[str]:
        """
        Generate temporal insights from graph memory.

        Example: "Bitcoin VaR increased by 40% over the last month"

        Args:
            user_id: User identifier
            entity_name: Entity to analyze

        Returns:
            List of insight strings
        """
        nodes = self.query_user_graph(user_id, entity_name=entity_name, days=60)

        if len(nodes) < 2:
            return []

        insights = []

        # Compare first and last node
        first = nodes[0]
        last = nodes[-1]

        # Find common metrics
        common_metrics = set(first.data.keys()) & set(last.data.keys())

        for metric in common_metrics:
            if isinstance(first.data[metric], (int, float)) and isinstance(last.data[metric], (int, float)):
                old_value = first.data[metric]
                new_value = last.data[metric]

                if old_value != 0:
                    change_pct = ((new_value - old_value) / old_value) * 100
                    if abs(change_pct) > 10:  # Only report significant changes
                        direction = "increased" if change_pct > 0 else "decreased"
                        insights.append(
                            f"{entity_name} {metric} {direction} by {abs(change_pct):.1f}% "
                            f"from {first.timestamp.strftime('%Y-%m-%d')} to {last.timestamp.strftime('%Y-%m-%d')}"
                        )

        return insights

    # ==================== Unified Context Retrieval ====================

    def get_user_context(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> UserContext:
        """
        Get complete user context from all memory types.

        This is the main function used by agents to get user context.

        Args:
            user_id: User identifier
            session_id: Session identifier (for session memory)

        Returns:
            UserContext with all relevant memory
        """
        # Long-term preferences
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            # Create default preferences if none exist
            preferences = self.create_user_preferences(user_id)

        # Short-term history
        history = self.get_recent_activities(user_id, days=7)

        # Session messages
        session_messages = []
        if session_id:
            session_messages = self.get_session_history(user_id, session_id)

        # Graph context (temporal)
        graph_context = self.query_user_graph(user_id, days=30)

        # Generate temporal insights
        temporal_insights = []
        unique_entities = set(node.entity_name for node in graph_context)
        for entity in unique_entities:
            insights = self.get_temporal_insights(user_id, entity)
            temporal_insights.extend(insights)

        return UserContext(
            preferences=preferences,
            history=history,
            session_messages=session_messages,
            graph_context=graph_context,
            temporal_insights=temporal_insights
        )
