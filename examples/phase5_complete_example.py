#!/usr/bin/env python3
"""
Phase 5 Complete Example: Fine-Tuning & Hybrid RAG System

Demonstrates the full workflow from data collection to production deployment.

Usage:
    python3 examples/phase5_complete_example.py
"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from finrisk_ai.core.orchestrator_v2 import FinRiskOrchestratorV2
from finrisk_ai.finetuning import (
    TrainingDataCollector,
    FineTuningDataPreparator,
    FineTunedModelManager,
    HybridRAGFineTuning,
    PerformanceEvaluator
)


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def example_1_data_collection():
    """Example 1: Automatic Training Data Collection"""
    print_section("Example 1: Training Data Collection")

    # Initialize collector
    collector = TrainingDataCollector(
        storage_path="data/training_examples",
        quality_threshold=0.8,
        enable_privacy_filter=True,
    )

    print("Training data collector initialized")
    print(f"Storage: data/training_examples")
    print(f"Quality threshold: 0.8")

    # Simulate collecting examples
    example_data = {
        "user_query": "Calculate the Sharpe ratio for monthly returns of 5%, -2%, 3%, 8%",
        "rag_context": [
            "The Sharpe ratio measures risk-adjusted returns",
            "Formula: (Return - RiskFree) / StdDev"
        ],
        "user_preferences": {"risk_tolerance": "moderate", "reporting_style": "detailed"},
        "calculation_task": "Calculate Sharpe ratio",
        "calculation_selection": {"function": "calculate_sharpe_ratio"},
        "calculation_results": {"sharpe_ratio": 1.42, "volatility": 0.045},
        "narrative_response": "The Sharpe ratio of 1.42 indicates good risk-adjusted returns...",
        "quality_score": 0.95,
        "user_id": "demo_user_123",
        "session_id": "demo_session_abc",
    }

    collected = collector.collect_example(**example_data)

    print(f"\n✓ Example collected: {collected}")

    # Get statistics
    stats = collector.get_statistics()
    print(f"\nCollection Statistics:")
    print(f"  Total examples: {stats['total_examples']}")
    print(f"  Current batch: {stats['current_batch_size']}")
    print(f"  Avg quality: {stats['average_quality_score']:.2f}")

    # Export for fine-tuning
    if stats['total_examples'] >= 10:  # Need minimum examples
        count = collector.export_for_finetuning(
            output_path="data/finetuning/demo_training_data.jsonl",
            format="gemini",
            min_quality=0.9
        )
        print(f"\n✓ Exported {count} examples for fine-tuning")


def example_2_data_preparation():
    """Example 2: Prepare Data for Fine-Tuning"""
    print_section("Example 2: Data Preparation")

    # Check if training data exists
    import os
    if not os.path.exists("data/finetuning/demo_training_data.jsonl"):
        print("⚠️  Training data not found. Run example 1 first or collect more data.")
        return

    preparator = FineTuningDataPreparator(
        validation_split=0.1,
        random_seed=42,
        enable_augmentation=False
    )

    print("Data preparator initialized")
    print(f"Validation split: 10%")

    try:
        dataset = preparator.prepare_dataset(
            input_path="data/finetuning/demo_training_data.jsonl",
            output_dir="data/finetuning/prepared",
            min_examples=5  # Lower for demo
        )

        print(f"\n✓ Dataset prepared:")
        print(f"  Train examples: {dataset.train_size}")
        print(f"  Validation examples: {dataset.validation_size}")
        print(f"  Train path: {dataset.train_path}")
        print(f"  Validation path: {dataset.validation_path}")

        # Analyze dataset
        stats = preparator.analyze_dataset(dataset.train_path)
        print(f"\nDataset Statistics:")
        print(f"  Total examples: {stats['total_examples']}")
        print(f"  Avg input length: {stats['avg_input_length']:.0f} chars")
        print(f"  Avg output length: {stats['avg_output_length']:.0f} chars")
        print(f"  Vocabulary size: {stats['vocabulary_size']} words")

    except ValueError as e:
        print(f"⚠️  {e}")
        print("Collect more training examples before preparing dataset.")


def example_3_model_management():
    """Example 3: Model Management and Versioning"""
    print_section("Example 3: Model Management")

    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set. Skipping model management example.")
        return

    manager = FineTunedModelManager(
        gemini_api_key=api_key,
        models_registry_path="data/demo_models_registry.json"
    )

    print("Model manager initialized")

    # Register a demo model
    model = manager.register_model(
        model_name="tunedModels/demo-finrisk-v1",
        base_model="gemini-1.5-flash",
        training_examples_count=1500,
        description="Demo fine-tuned model for financial analysis",
        benchmark_score=0.95
    )

    print(f"\n✓ Model registered:")
    print(f"  Version ID: {model.version_id}")
    print(f"  Model name: {model.model_name}")
    print(f"  Status: {model.status}")
    print(f"  Traffic: {model.production_traffic_percentage}%")

    # Set traffic for A/B testing
    manager.set_traffic_split(model.version_id, traffic_percentage=50.0)
    print(f"\n✓ Traffic split updated to 50%")

    # List models
    models = manager.list_models()
    print(f"\nRegistered Models:")
    for m in models:
        print(f"  {m.version_id}: {m.status} ({m.production_traffic_percentage}% traffic)")

    # Get statistics
    stats = manager.get_statistics()
    print(f"\nModel Management Statistics:")
    print(f"  Total models: {stats['total_models']}")
    print(f"  Active models: {stats['active_models']}")
    print(f"  Traffic allocated: {stats['total_traffic_allocated']}%")


def example_4_hybrid_system():
    """Example 4: Hybrid RAG + Fine-Tuning"""
    print_section("Example 4: Hybrid RAG + Fine-Tuning")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set. Skipping hybrid system example.")
        return

    # Initialize hybrid system
    hybrid = HybridRAGFineTuning(
        gemini_api_key=api_key,
        base_model="gemini-1.5-flash-latest",
        finetuned_model="tunedModels/demo-finrisk-v1",  # Would be actual model
        use_finetuned=False,  # Set to False since model doesn't exist
        fallback_to_base=True
    )

    print("Hybrid RAG + Fine-Tuning system initialized")
    print(f"Using base model: gemini-1.5-flash-latest")

    # Demo RAG context
    rag_context = [
        "The Sharpe ratio measures risk-adjusted returns by comparing excess returns to volatility.",
        "A Sharpe ratio above 1.0 is considered good, above 2.0 is excellent.",
        "Formula: (Portfolio Return - Risk Free Rate) / Portfolio Standard Deviation"
    ]

    # Generate response
    print("\n📝 Generating response with RAG context...")
    prompt = "What is the Sharpe ratio and what does a value of 1.5 indicate?"

    try:
        response = hybrid.generate_with_rag(
            prompt=prompt,
            rag_context=rag_context,
            temperature=0.7
        )

        print(f"\n✓ Response generated:")
        print(f"  Model used: {response['model_used']}")
        print(f"  RAG context count: {response['rag_context_count']}")
        print(f"  Success: {response['success']}")
        print(f"\nResponse preview (first 200 chars):")
        print(f"  {response['text'][:200]}...")

    except Exception as e:
        print(f"⚠️  Generation failed: {e}")


def example_5_evaluation():
    """Example 5: Performance Evaluation"""
    print_section("Example 5: Performance Evaluation")

    evaluator = PerformanceEvaluator(
        test_cases_path="data/test_cases/benchmark_suite.json",
        baseline_score=0.75
    )

    print("Performance evaluator initialized")
    print(f"Baseline score: 75%")

    # Check if test cases exist
    import os
    if not os.path.exists("data/test_cases/benchmark_suite.json"):
        print("⚠️  Benchmark suite not found at data/test_cases/benchmark_suite.json")
        return

    print(f"\nTest cases loaded: {len(evaluator.test_cases)}")

    # Demo: Create a simple model callable
    def dummy_model(query):
        return {
            "text": f"This is a response to: {query}. The Sharpe ratio is approximately 1.5."
        }

    # Run evaluation on subset
    print("\n📊 Running benchmark evaluation (first 3 test cases)...")
    try:
        report = evaluator.evaluate_model(
            model_callable=dummy_model,
            model_name="demo_model",
            test_cases=evaluator.test_cases[:3],  # First 3 only
            rag_enabled=True,
            finetuned_enabled=False
        )

        print(f"\n✓ Evaluation complete:")
        print(f"  Tests run: {report.total_tests}")
        print(f"  Passed: {report.passed_tests}")
        print(f"  Failed: {report.failed_tests}")
        print(f"  Avg accuracy: {report.avg_accuracy:.2%}")
        print(f"  Avg relevance: {report.avg_relevance:.2%}")
        print(f"  Avg completeness: {report.avg_completeness:.2%}")
        print(f"  Avg latency: {report.avg_latency_ms:.1f}ms")
        print(f"  Improvement over baseline: {report.improvement_over_baseline:+.1f}%")

    except Exception as e:
        print(f"⚠️  Evaluation failed: {e}")


def example_6_orchestrator_v2():
    """Example 6: Enhanced Orchestrator with Phase 5"""
    print_section("Example 6: Enhanced Orchestrator (V2)")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY not set. Skipping orchestrator V2 example.")
        return

    # Initialize V2 orchestrator
    orch = FinRiskOrchestratorV2(
        gemini_api_key=api_key,
        enable_data_collection=True,
        data_collection_quality_threshold=0.9,
        finetuned_model=None,  # No fine-tuned model yet
        enable_finetuning=False,
        enable_ab_testing=False,
    )

    print("Enhanced Orchestrator V2 initialized")
    print(f"Data collection: ENABLED (threshold: 0.9)")
    print(f"Fine-tuning: DISABLED (no model available)")

    # Get statistics
    stats = orch.get_statistics()
    print(f"\nPhase 5 Statistics:")
    print(f"  Phase 5 enabled: {stats['phase5_enabled']}")
    print(f"  Fine-tuning enabled: {stats['finetuning_enabled']}")
    print(f"  Data collection enabled: {stats['data_collection_enabled']}")

    print("\n✓ Orchestrator V2 ready for production use!")
    print("  → Reports will automatically collect training data")
    print("  → Deploy fine-tuned models when ready")
    print("  → Enable A/B testing for gradual rollout")


def main():
    """Run all Phase 5 examples"""
    print("\n" + "=" * 80)
    print("  FinRisk AI - Phase 5: Fine-Tuning & Optimization Examples")
    print("  Complete workflow from data collection to production")
    print("=" * 80)

    # Create required directories
    import os
    os.makedirs("data/training_examples", exist_ok=True)
    os.makedirs("data/finetuning", exist_ok=True)
    os.makedirs("data/test_cases", exist_ok=True)

    # Run examples
    try:
        example_1_data_collection()
        example_2_data_preparation()
        example_3_model_management()
        example_4_hybrid_system()
        example_5_evaluation()
        example_6_orchestrator_v2()

        # Summary
        print_section("Summary")
        print("✓ All Phase 5 examples completed!")
        print("\nNext Steps:")
        print("  1. Deploy orchestrator V2 to production")
        print("  2. Collect 1000+ high-quality training examples")
        print("  3. Prepare data and create fine-tuning job")
        print("  4. Evaluate fine-tuned model on benchmark suite")
        print("  5. Deploy with A/B testing (10% → 50% → 100%)")
        print("  6. Monitor performance and iterate")
        print("\nTarget: Achieve 98% accuracy (+11% over RAG-only baseline)")

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
