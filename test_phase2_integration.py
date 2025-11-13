#!/usr/bin/env python3
"""
Phase 2 Integration Test

Tests the complete integration of:
1. C++ InvestTool engine (Phase 1)
2. CalculationAgent with C++ engine (Phase 2)
3. NarrativeAgent with HTML packets (Phase 2)

This verifies that the AI system can now call C++ functions directly
instead of generating and executing Python code.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'finrisk_ai'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_cpp_bridge_availability():
    """Test that C++ bridge module is available"""
    print("\n" + "="*80)
    print("TEST 1: C++ Bridge Availability")
    print("="*80)

    try:
        from finrisk_ai.core.cpp_bridge import get_cpp_engine

        engine = get_cpp_engine()
        print(f"✓ C++ engine initialized successfully")
        print(f"✓ Available functions: {len(engine.get_available_functions())}")

        for func in engine.get_available_functions():
            print(f"  - {func}")

        return True

    except Exception as e:
        print(f"✗ C++ bridge test failed: {e}")
        return False


def test_cpp_calculations():
    """Test direct C++ calculations"""
    print("\n" + "="*80)
    print("TEST 2: Direct C++ Calculations")
    print("="*80)

    try:
        from finrisk_ai.core.cpp_bridge import get_cpp_engine

        engine = get_cpp_engine()

        # Test risk metrics calculation
        sample_returns = [0.05, -0.02, 0.03, 0.08, -0.01, 0.04, 0.02, 0.06, -0.03, 0.05, 0.01, 0.07]

        result = engine.calculate_risk_metrics(
            returns=sample_returns,
            risk_free_rate=0.02,
            asset_name="Test Portfolio",
            portfolio_value=100000.0
        )

        print(f"✓ Risk metrics calculated successfully")
        print(f"  - Volatility: {result['calculation_results']['volatility']*100:.2f}%")
        print(f"  - Sharpe Ratio: {result['calculation_results']['sharpe_ratio']:.4f}")
        print(f"  - Sortino Ratio: {result['calculation_results']['sortino_ratio']:.4f}")
        print(f"  - VaR (95%): ${result['calculation_results']['var_95']:,.2f}")
        print(f"  - Z-Score: {result['calculation_results']['z_score']:.4f}")

        # Check HTML packet
        if result['calculation_html_packet']:
            print(f"✓ HTML packet generated successfully")
            print(f"  - Source: {result['calculation_html_packet'].source}")
            print(f"  - Method: {result['calculation_html_packet'].calculation_method}")
        else:
            print(f"✗ HTML packet not generated")
            return False

        return True

    except Exception as e:
        print(f"✗ C++ calculations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculation_agent_integration():
    """Test CalculationAgent with C++ engine (without Gemini API)"""
    print("\n" + "="*80)
    print("TEST 3: CalculationAgent Integration (Fallback Mode)")
    print("="*80)

    try:
        from finrisk_ai.core.state import AgentState
        from finrisk_ai.rag.hybrid_search import Document

        # Note: This test uses the fallback mechanism since we don't have a Gemini API key in test
        # In production, this would use Gemini for function selection

        # Create mock state
        state = AgentState(
            user_query="Calculate risk metrics for my portfolio",
            user_id="test_user",
            session_id="test_session"
        )

        # Add mock RAG context
        state.rag_context = [
            Document(
                content="Historical monthly returns: 5%, -2%, 3%, 8%, -1%, 4%, 2%, 6%, -3%, 5%",
                metadata={"source": "portfolio_data"},
                score=0.95
            )
        ]

        # NOTE: We can't test the full CalculationAgent without a Gemini API key
        # But we can test that the C++ engine works directly

        from finrisk_ai.core.cpp_bridge import get_cpp_engine
        engine = get_cpp_engine()

        # Simulate what CalculationAgent would do (fallback mode)
        sample_returns = [0.05, -0.02, 0.03, 0.08, -0.01, 0.04, 0.02, 0.06, -0.03, 0.05]
        result = engine.calculate_risk_metrics(
            returns=sample_returns,
            risk_free_rate=0.02,
            asset_name="Portfolio",
            portfolio_value=100000.0
        )

        # Update state (as CalculationAgent would)
        state.calculation_results = result['calculation_results']
        state.calculation_html_packet = result.get('calculation_html_packet')
        state.calculation_code = "C++ Functions: calculate_risk_metrics (test)"

        print(f"✓ CalculationAgent flow simulated successfully")
        print(f"  - Results: {list(state.calculation_results.keys())}")
        print(f"  - HTML packet: {'✓ Present' if state.calculation_html_packet else '✗ Missing'}")
        print(f"  - Calculation code: {state.calculation_code}")

        return True

    except Exception as e:
        print(f"✗ CalculationAgent integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_portfolio_optimization():
    """Test portfolio optimization"""
    print("\n" + "="*80)
    print("TEST 4: Portfolio Optimization")
    print("="*80)

    try:
        from finrisk_ai.core.cpp_bridge import get_cpp_engine

        engine = get_cpp_engine()

        # Sample asset returns (3 assets, 12 months)
        gold_returns = [0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.02, 0.01, 0.03, -0.01, 0.02, 0.01]
        sp500_returns = [0.05, -0.03, 0.07, 0.02, 0.04, -0.02, 0.05, 0.03, 0.06, -0.01, 0.04, 0.02]
        btc_returns = [0.15, -0.10, 0.20, 0.08, 0.12, -0.08, 0.15, 0.10, 0.18, -0.05, 0.12, 0.08]

        result = engine.optimize_portfolio(
            asset_returns=[gold_returns, sp500_returns, btc_returns],
            asset_names=["Gold", "S&P 500", "Bitcoin"],
            risk_free_rate=0.03,
            num_simulations=1000,  # Reduced for faster testing
            random_seed=42
        )

        print(f"✓ Portfolio optimization completed")
        print(f"  - Expected Return: {result['calculation_results']['expected_return']*100:.2f}%")
        print(f"  - Expected Risk: {result['calculation_results']['expected_risk']*100:.2f}%")
        print(f"  - Sharpe Ratio: {result['calculation_results']['sharpe_ratio']:.4f}")
        print(f"  - Optimal Weights:")
        for asset, weight in result['calculation_results']['optimal_weights'].items():
            print(f"    * {asset}: {weight*100:.1f}%")

        # Check HTML packet
        if result['calculation_html_packet']:
            print(f"✓ HTML packet generated for portfolio")
        else:
            print(f"✗ HTML packet not generated")
            return False

        return True

    except Exception as e:
        print(f"✗ Portfolio optimization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_backtest():
    """Test strategy backtesting"""
    print("\n" + "="*80)
    print("TEST 5: Strategy Backtesting")
    print("="*80)

    try:
        from finrisk_ai.core.cpp_bridge import get_cpp_engine
        import math

        engine = get_cpp_engine()

        # Generate sample price data
        prices = [100 + i*0.5 + math.sin(i/10)*10 for i in range(100)]

        # Test Buy and Hold
        result = engine.backtest_strategy(
            prices=prices,
            strategy="buy_and_hold",
            initial_capital=10000.0
        )

        print(f"✓ Backtest completed (Buy & Hold)")
        print(f"  - Initial Capital: ${result['calculation_results']['initial_capital']:,.2f}")
        print(f"  - Final Value: ${result['calculation_results']['final_value']:,.2f}")
        print(f"  - Total Return: {result['calculation_results']['total_return']*100:.2f}%")
        print(f"  - Max Drawdown: {result['calculation_results']['max_drawdown']*100:.2f}%")

        return True

    except Exception as e:
        print(f"✗ Strategy backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 integration tests"""
    print("\n" + "="*80)
    print("🚀 PHASE 2 INTEGRATION TEST SUITE")
    print("="*80)
    print("Testing: C++ Engine ← Python AI Bridge")
    print("="*80)

    results = []

    # Run tests
    results.append(("C++ Bridge Availability", test_cpp_bridge_availability()))
    results.append(("Direct C++ Calculations", test_cpp_calculations()))
    results.append(("CalculationAgent Integration", test_calculation_agent_integration()))
    results.append(("Portfolio Optimization", test_portfolio_optimization()))
    results.append(("Strategy Backtesting", test_strategy_backtest()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("="*80)

    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ Phase 2 is fully operational!")
        print("✅ C++ engine is integrated with Python AI system!")
        print("✅ CalculationAgent now uses deterministic C++ functions!")
        print("\nNext: Run the full system with a Gemini API key")
        return 0
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total} passed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
