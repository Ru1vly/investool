"""
Complete Example: FinRisk AI Analyst System

Demonstrates the full workflow from setup to report generation.
"""

import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from finrisk_ai.core.orchestrator import FinRiskOrchestrator
from finrisk_ai.core.data_ingestion import DataIngestionEngine, CppFinancialDataAdapter
from finrisk_ai.rag.hybrid_search import Document
from finrisk_ai.rag.graph_rag import GraphRAG
from finrisk_ai.memory.mem0_system import Mem0System
from finrisk_ai.utils.production_optimizations import KVCache, ModelRouter


def main():
    """Main example workflow"""

    print("=" * 80)
    print("FinRisk AI Analyst - Complete Example")
    print("=" * 80)

    # ==================== 1. Initialize System ====================
    print("\n[1] Initializing FinRisk AI system...")

    # Get API key from environment
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "your_api_key_here")

    # Initialize orchestrator
    orchestrator = FinRiskOrchestrator(
        gemini_api_key=GEMINI_API_KEY,
        gemini_pro_model="gemini-1.5-pro-latest",
        gemini_flash_model="gemini-1.5-flash-latest"
    )

    print("✓ System initialized")

    # ==================== 2. Index Knowledge Base ====================
    print("\n[2] Indexing financial knowledge base...")

    # Example: Index financial concepts and formulas
    knowledge_documents = [
        Document(
            content="Value at Risk (VaR) is a statistical measure that quantifies the maximum expected loss "
                   "of a portfolio over a specific time period at a given confidence level. Formula: VaR = |μ - Z × σ|",
            metadata={"type": "formula", "id": "var"},
            doc_id="doc_var",
            source="ADVANCED_FORMULAS.md"
        ),
        Document(
            content="Sortino Ratio measures risk-adjusted return using only downside deviation. "
                   "Formula: Sortino = (R_p - R_f) / σ_d. Better than Sharpe for asymmetric returns.",
            metadata={"type": "formula", "id": "sortino"},
            doc_id="doc_sortino",
            source="ADVANCED_FORMULAS.md"
        ),
        Document(
            content="Modern Portfolio Theory (MPT) by Harry Markowitz optimizes portfolio allocation "
                   "to achieve maximum return for a given level of risk through diversification.",
            metadata={"type": "concept", "id": "mpt"},
            doc_id="doc_mpt",
            source="ADVANCED_FORMULAS.md"
        ),
        Document(
            content="Portfolio Volatility for two assets: σ_p = √[w_A² × σ_A² + w_B² × σ_B² + 2 × w_A × w_B × ρ_AB × σ_A × σ_B]. "
                   "Shows that diversification reduces risk when correlation < 1.",
            metadata={"type": "formula", "id": "portfolio_vol"},
            doc_id="doc_port_vol",
            source="ADVANCED_FORMULAS.md"
        ),
        Document(
            content="Z-Score measures how many standard deviations an observation is from the mean. "
                   "Formula: Z = (x - μ) / σ. Used for mean reversion trading. |Z| > 2 indicates extreme deviation.",
            metadata={"type": "formula", "id": "zscore"},
            doc_id="doc_zscore",
            source="ADVANCED_FORMULAS.md"
        )
    ]

    orchestrator.index_knowledge(knowledge_documents)
    print(f"✓ Indexed {len(knowledge_documents)} documents")

    # ==================== 3. Build Knowledge Graph ====================
    print("\n[3] Building financial knowledge graph...")

    orchestrator.build_knowledge_graph()
    print("✓ Knowledge graph built with standard financial relationships")

    # ==================== 4. Create User Profile ====================
    print("\n[4] Creating user profile...")

    USER_ID = "demo_user_001"
    SESSION_ID = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    orchestrator.create_user(
        user_id=USER_ID,
        risk_tolerance="moderate",
        reporting_style="detailed"
    )

    print(f"✓ Created user '{USER_ID}' with moderate risk tolerance")

    # ==================== 5. Simulate Historical Activity ====================
    print("\n[5] Adding historical user activity...")

    # Simulate viewing Bitcoin analysis
    orchestrator.mem0.add_activity(
        user_id=USER_ID,
        activity_type="asset_viewed",
        content={"asset": "Bitcoin", "timestamp": datetime.now().isoformat()}
    )

    # Simulate graph memory (tracking Bitcoin over time)
    orchestrator.mem0.add_graph_memory(
        user_id=USER_ID,
        entity_type="asset",
        entity_name="Bitcoin",
        data={"VaR_95": 5000, "Sortino": 0.8, "volatility": 0.65}
    )

    print("✓ Added sample historical data")

    # ==================== 6. Generate Financial Report ====================
    print("\n[6] Generating AI analyst report...")
    print("-" * 80)

    # Example query
    user_query = """
    Analyze a cryptocurrency portfolio with the following data:
    - Monthly returns: [0.15, -0.20, 0.30, -0.10, 0.25, -0.05, 0.10]
    - Portfolio value: $100,000
    - Risk-free rate: 2% annually

    Calculate:
    1. Volatility (annualized)
    2. Sortino Ratio
    3. Value at Risk (95% and 99% confidence)
    4. Z-Score for current volatility

    Provide a comprehensive risk assessment with recommendations.
    """

    print(f"\nQuery: {user_query[:100]}...\n")

    # Generate report
    result = orchestrator.generate_report(
        user_query=user_query,
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # ==================== 7. Display Results ====================
    print("\n[7] Results:")
    print("=" * 80)

    print("\n📊 CALCULATION RESULTS:")
    print("-" * 80)
    for metric, value in result["calculation_results"].items():
        print(f"  {metric:30s}: {value:,.4f}")

    print("\n📝 FINAL REPORT:")
    print("-" * 80)
    print(result["final_report_text"])

    print("\n📈 CHART SPECIFICATION:")
    print("-" * 80)
    if result["chart_json"]:
        import json
        print(json.dumps(result["chart_json"], indent=2))
    else:
        print("  (No chart generated)")

    print("\n🔍 METADATA:")
    print("-" * 80)
    metadata = result["metadata"]
    print(f"  Validation Passed: {'✓' if metadata['validation_passed'] else '✗'}")
    print(f"  Validation Errors: {len(metadata['validation_errors'])}")
    print(f"  Retry Count: {metadata['retry_count']}")
    print(f"  RAG Documents Retrieved: {metadata['rag_documents_retrieved']}")
    print(f"  Graph Nodes Retrieved: {metadata['graph_nodes_retrieved']}")

    # ==================== 8. Demonstrate Production Features ====================
    print("\n[8] Production Features Demo:")
    print("-" * 80)

    # Model routing
    task_types = ["quality_check", "code_generation", "narrative_generation"]
    print("\n  Model Routing:")
    for task in task_types:
        model = ModelRouter.select_model(task)
        cost = ModelRouter.estimate_cost(task, 1000, 500)
        print(f"    {task:25s} → {model:30s} (Est. cost: ${cost:.4f})")

    # Cache stats
    print("\n  KV Cache:")
    print("    Status: Enabled (requires Redis)")
    print("    Strategy: Cache static prompts (system instructions, preferences)")
    print("    Expected Hit Rate: 40-60% for repeated queries")

    print("\n" + "=" * 80)
    print("Example complete!")
    print("=" * 80)


def example_with_cpp_integration():
    """
    Example: Integrating with existing C++ InvestTool calculations.

    This shows how to use the C++ calculation results with the AI system.
    """
    print("\n" + "=" * 80)
    print("C++ InvestTool Integration Example")
    print("=" * 80)

    # Simulate C++ calculation results
    print("\n[C++ RiskAnalyzer] Calculating risk metrics...")

    # These would come from the C++ InvestTool
    cpp_results = {
        "variance": 0.0225,
        "volatility": 0.15,
        "sharpe_ratio": 1.2,
        "beta": 1.5
    }

    # Convert to enriched format
    enriched_data = CppFinancialDataAdapter.from_risk_metrics(
        variance=cpp_results["variance"],
        volatility=cpp_results["volatility"],
        sharpe_ratio=cpp_results["sharpe_ratio"],
        beta=cpp_results["beta"],
        asset_name="S&P 500"
    )

    print(f"✓ Enriched C++ data with metadata")
    print("\nEnriched HTML Output:")
    print("-" * 80)
    print(enriched_data.html_content)

    # Premium features example
    print("\n[C++ Premium Features] Advanced risk metrics...")

    premium_results = {
        "sortino_ratio": 1.8,
        "var_95": 15000,
        "var_99": 25000,
        "downside_deviation": 0.08,
        "z_score": 2.3
    }

    enriched_premium = CppFinancialDataAdapter.from_premium_features(
        sortino_ratio=premium_results["sortino_ratio"],
        var_95=premium_results["var_95"],
        var_99=premium_results["var_99"],
        downside_deviation=premium_results["downside_deviation"],
        z_score=premium_results["z_score"],
        asset_name="Crypto Portfolio",
        portfolio_value=100000
    )

    print(f"✓ Enriched premium calculation data")
    print("\nStatistics:")
    if enriched_premium.statistics:
        print(f"  Mean: {enriched_premium.statistics.mean:.4f}")
        print(f"  Median: {enriched_premium.statistics.median:.4f}")
        print(f"  Std: {enriched_premium.statistics.std:.4f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Run main example
    main()

    # Run C++ integration example
    example_with_cpp_integration()

    print("\n✨ All examples completed successfully!")
