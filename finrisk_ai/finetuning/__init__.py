"""
Fine-Tuning Module for FinRisk AI

Implements Phase 5: Fine-Tuning & Optimization for SOTA performance.

Components:
- Data Collection: Capture training examples from production
- Data Preparation: Format for Gemini fine-tuning
- Fine-Tuning Management: Create and manage fine-tuning jobs
- Hybrid RAG: Combine retrieval with fine-tuned models
- Evaluation: Benchmark and measure improvements
"""

from finrisk_ai.finetuning.data_collector import TrainingDataCollector
from finrisk_ai.finetuning.data_preparation import FineTuningDataPreparator
from finrisk_ai.finetuning.model_manager import FineTunedModelManager
from finrisk_ai.finetuning.hybrid_system import HybridRAGFineTuning
from finrisk_ai.finetuning.evaluator import PerformanceEvaluator

__all__ = [
    "TrainingDataCollector",
    "FineTuningDataPreparator",
    "FineTunedModelManager",
    "HybridRAGFineTuning",
    "PerformanceEvaluator",
]
