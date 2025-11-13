"""
Phase 5.6: Enhanced Orchestrator with Fine-Tuning Support

Extends the base orchestrator with:
- Training data collection
- Fine-tuned model integration
- Hybrid RAG + fine-tuning
- Performance evaluation
- A/B testing support
"""

import logging
from typing import Dict, Any, Optional
import random

from finrisk_ai.core.orchestrator import FinRiskOrchestrator
from finrisk_ai.finetuning.data_collector import TrainingDataCollector
from finrisk_ai.finetuning.model_manager import FineTunedModelManager
from finrisk_ai.finetuning.hybrid_system import HybridRAGFineTuning, AdaptiveHybridSystem
from finrisk_ai.rag.hybrid_search import VectorDatabase
from finrisk_ai.rag.graph_rag import GraphRAG
from finrisk_ai.memory.mem0_system import Mem0System

logger = logging.getLogger(__name__)


class FinRiskOrchestratorV2(FinRiskOrchestrator):
    """
    Enhanced orchestrator with Phase 5 capabilities.

    Adds:
    - Automatic training data collection
    - Fine-tuned model usage
    - Hybrid RAG + fine-tuning
    - A/B testing
    - Performance tracking
    """

    def __init__(
        self,
        gemini_api_key: str,
        vector_db: Optional[VectorDatabase] = None,
        graph_rag: Optional[GraphRAG] = None,
        mem0_system: Optional[Mem0System] = None,
        gemini_pro_model: str = "gemini-1.5-pro-latest",
        gemini_flash_model: str = "gemini-1.5-flash-latest",
        # Phase 5 parameters
        enable_data_collection: bool = True,
        data_collection_quality_threshold: float = 0.8,
        finetuned_model: Optional[str] = None,
        enable_finetuning: bool = False,
        enable_ab_testing: bool = False,
        ab_test_traffic_split: float = 0.5,  # 50% to fine-tuned model
    ):
        """
        Initialize enhanced orchestrator.

        Args:
            gemini_api_key: Gemini API key
            vector_db: Vector database
            graph_rag: GraphRAG system
            mem0_system: Mem0 memory system
            gemini_pro_model: Base Pro model
            gemini_flash_model: Base Flash model
            enable_data_collection: Collect training data
            data_collection_quality_threshold: Min quality for collection
            finetuned_model: Fine-tuned model name
            enable_finetuning: Use fine-tuned model
            enable_ab_testing: Enable A/B testing
            ab_test_traffic_split: % traffic to fine-tuned model
        """
        # Initialize base orchestrator
        super().__init__(
            gemini_api_key=gemini_api_key,
            vector_db=vector_db,
            graph_rag=graph_rag,
            mem0_system=mem0_system,
            gemini_pro_model=gemini_pro_model,
            gemini_flash_model=gemini_flash_model,
        )

        # Phase 5: Training data collection
        self.enable_data_collection = enable_data_collection
        if enable_data_collection:
            self.data_collector = TrainingDataCollector(
                quality_threshold=data_collection_quality_threshold
            )
            logger.info("Training data collection enabled")
        else:
            self.data_collector = None

        # Phase 5: Fine-tuned model management
        self.model_manager = FineTunedModelManager(
            gemini_api_key=gemini_api_key
        )

        # Phase 5: Hybrid RAG + Fine-tuning
        self.enable_finetuning = enable_finetuning and finetuned_model is not None
        if self.enable_finetuning:
            self.hybrid_system = HybridRAGFineTuning(
                gemini_api_key=gemini_api_key,
                base_model=gemini_pro_model,
                finetuned_model=finetuned_model,
                use_finetuned=True,
            )
            self.adaptive_system = AdaptiveHybridSystem(
                hybrid_system=self.hybrid_system
            )
            logger.info(f"Fine-tuned model enabled: {finetuned_model}")
        else:
            self.hybrid_system = None
            self.adaptive_system = None

        # Phase 5: A/B testing
        self.enable_ab_testing = enable_ab_testing
        self.ab_test_traffic_split = ab_test_traffic_split

        logger.info("FinRiskOrchestratorV2 initialized with Phase 5 capabilities")

    def generate_report(
        self,
        user_query: str,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Enhanced report generation with fine-tuning support.

        Workflow:
        1. Determine model to use (A/B testing)
        2. Generate report (base or hybrid approach)
        3. Collect training data (if enabled)
        4. Return results with metadata
        """
        logger.info(f"Generating report (V2) for user {user_id}: '{user_query}'")

        # A/B Testing: Decide which approach to use
        use_finetuned = self._should_use_finetuned()

        if use_finetuned and self.hybrid_system:
            # Use hybrid RAG + fine-tuning approach
            result = self._generate_with_hybrid(user_query, user_id, session_id)
            result["approach"] = "hybrid_rag_finetuning"
        else:
            # Use base orchestrator approach
            result = super().generate_report(user_query, user_id, session_id)
            result["approach"] = "base_rag_only"

        # Collect training data (if enabled and quality is sufficient)
        if self.enable_data_collection and self.data_collector:
            self._collect_training_example(
                user_query=user_query,
                user_id=user_id,
                session_id=session_id,
                result=result,
            )

        # Add Phase 5 metadata
        result["metadata"]["phase5_enabled"] = True
        result["metadata"]["finetuned_model_used"] = use_finetuned
        result["metadata"]["data_collection_enabled"] = self.enable_data_collection

        return result

    def _generate_with_hybrid(
        self,
        user_query: str,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Generate report using hybrid RAG + fine-tuning approach.

        This leverages the fine-tuned model's domain knowledge
        combined with RAG retrieval for best performance.
        """
        logger.info("Using hybrid RAG + fine-tuning approach")

        # Step 1: Retrieve RAG context (same as base)
        rag_docs = self.vector_db.search(user_query, top_k=10)
        graph_nodes = self.graph_rag.retrieve(user_query, max_depth=2)

        # Step 2: Get user context
        user_context = self.mem0.get_user_context(user_id, session_id)

        # Step 3: Construct prompt for hybrid system
        rag_context = [doc.content for doc in rag_docs]

        # Step 4: Generate using adaptive hybrid system
        response = self.adaptive_system.generate_adaptive(
            prompt=user_query,
            rag_retriever=self.vector_db,  # Pass retriever for adaptive retrieval
            user_context={
                "preferences": {
                    "risk_tolerance": user_context.preferences.risk_tolerance,
                    "reporting_style": user_context.preferences.reporting_style,
                }
            }
        )

        # Step 5: Extract calculation results (if any)
        # For now, use base orchestrator for calculations
        # In production, integrate C++ calculation extraction from hybrid response
        base_result = super().generate_report(user_query, user_id, session_id)

        # Combine results
        return {
            "final_report_text": response["text"],
            "calculation_results": base_result.get("calculation_results", {}),
            "chart_json": base_result.get("chart_json"),
            "metadata": {
                **base_result.get("metadata", {}),
                "hybrid_model_used": response["model_used"],
                "rag_context_count": response["rag_context_count"],
                "confidence": response.get("confidence", 1.0),
            }
        }

    def _should_use_finetuned(self) -> bool:
        """
        Determine whether to use fine-tuned model.

        Uses A/B testing if enabled, otherwise checks if fine-tuning is enabled.
        """
        if not self.enable_finetuning:
            return False

        if self.enable_ab_testing:
            # A/B test: random split based on traffic percentage
            return random.random() < self.ab_test_traffic_split

        # Always use fine-tuned if enabled and not A/B testing
        return True

    def _collect_training_example(
        self,
        user_query: str,
        user_id: str,
        session_id: str,
        result: Dict[str, Any],
    ):
        """
        Collect training example for future fine-tuning.

        Only collects high-quality examples that passed validation.
        """
        metadata = result.get("metadata", {})

        # Only collect if validation passed
        if not metadata.get("validation_passed", False):
            logger.debug("Skipping training data collection: validation failed")
            return

        # Get user context
        try:
            user_context = self.mem0.get_user_context(user_id, session_id)
            user_preferences = {
                "risk_tolerance": user_context.preferences.risk_tolerance,
                "reporting_style": user_context.preferences.reporting_style,
            }
        except Exception as e:
            logger.warning(f"Failed to get user context for training data: {e}")
            user_preferences = {}

        # Collect RAG context (simplified - would retrieve from state in production)
        rag_context = [
            f"Context about {user_query}"  # Placeholder
        ]

        # Calculate quality score
        quality_score = self._calculate_quality_score(result)

        # Collect example
        try:
            collected = self.data_collector.collect_example(
                user_query=user_query,
                rag_context=rag_context,
                user_preferences=user_preferences,
                calculation_task=user_query,  # Simplified
                calculation_selection=result.get("calculation_results", {}),
                calculation_results=result.get("calculation_results", {}),
                narrative_response=result["final_report_text"],
                quality_score=quality_score,
                user_id=user_id,
                session_id=session_id,
            )

            if collected:
                logger.info(f"Training example collected (quality={quality_score:.2f})")
        except Exception as e:
            logger.error(f"Failed to collect training example: {e}")

    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """
        Calculate quality score for training example.

        Based on:
        - Validation passed
        - Retry count (lower is better)
        - Report length (reasonable length is good)
        """
        score = 0.5  # Base score

        metadata = result.get("metadata", {})

        # Validation passed
        if metadata.get("validation_passed", False):
            score += 0.3

        # Low retry count
        retry_count = metadata.get("retry_count", 0)
        if retry_count == 0:
            score += 0.1
        elif retry_count == 1:
            score += 0.05

        # Reasonable report length
        report_text = result.get("final_report_text", "")
        word_count = len(report_text.split())
        if 100 <= word_count <= 1000:
            score += 0.1

        return min(1.0, score)

    def get_statistics(self) -> Dict[str, Any]:
        """Get Phase 5 statistics"""
        stats = {
            "phase5_enabled": True,
            "finetuning_enabled": self.enable_finetuning,
            "data_collection_enabled": self.enable_data_collection,
            "ab_testing_enabled": self.enable_ab_testing,
        }

        # Data collection stats
        if self.data_collector:
            stats["data_collection"] = self.data_collector.get_statistics()

        # Model management stats
        stats["model_management"] = self.model_manager.get_statistics()

        # Hybrid system info
        if self.hybrid_system:
            stats["hybrid_system"] = self.hybrid_system.get_model_info()

        return stats
