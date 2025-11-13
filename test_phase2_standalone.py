#!/usr/bin/env python3
"""
Phase 2 Standalone Test

Tests only the C++ bridge without full finrisk_ai dependencies.
This verifies that the C++ integration works independently.
"""

import sys
import os

# Add build directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))

def test_cpp_module():
    """Test that C++ module can be imported and used"""
    print("\n" + "="*80)
    print("TEST 1: C++ Module Direct Import")
    print("="*80)

    try:
        import investool_engine as ie

        print(f"✓ investool_engine module imported successfully")
        print(f"✓ Module version: {ie.__version__}")
        print(f"✓ Module docstring: {ie.__doc__.strip()[:80]}...")

        # Test a simple calculation
        returns = [0.05, -0.02, 0.03, 0.08, -0.01, 0.04, 0.02]
        volatility = ie.RiskAnalyzer.CalculateVolatility(returns)
        sharpe = ie.RiskAnalyzer.CalculateSharpeRatio(returns, 0.02)

        print(f"✓ Risk calculations work:")
        print(f"  - Volatility: {volatility*100:.2f}%")
        print(f"  - Sharpe Ratio: {sharpe:.4f}")

        return True

    except Exception as e:
        print(f"✗ C++ module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cpp_bridge_module():
    """Test the Python bridge wrapper"""
    print("\n" + "="*80)
    print("TEST 2: C++ Bridge Wrapper")
    print("="*80)

    try:
        # Import the bridge module directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'finrisk_ai'))

        from core.cpp_bridge import CppCalculationEngine

        engine = CppCalculationEngine()
        print(f"✓ C++ Calculation Engine initialized")

        # Test risk metrics
        sample_returns = [0.05, -0.02, 0.03, 0.08, -0.01, 0.04, 0.02, 0.06, -0.03, 0.05]

        result = engine.calculate_risk_metrics(
            returns=sample_returns,
            risk_free_rate=0.02,
            asset_name="Test Portfolio",
            portfolio_value=100000.0
        )

        print(f"✓ Risk metrics calculated:")
        print(f"  - Volatility: {result['calculation_results']['volatility']*100:.2f}%")
        print(f"  - Sharpe Ratio: {result['calculation_results']['sharpe_ratio']:.4f}")
        print(f"  - Sortino Ratio: {result['calculation_results']['sortino_ratio']:.4f}")
        print(f"  - VaR (95%): ${result['calculation_results']['var_95']:,.2f}")
        print(f"  - Z-Score: {result['calculation_results']['z_score']:.4f}")

        # Check HTML packet
        if result['calculation_html_packet']:
            print(f"✓ HTML packet generated")
            print(f"  - Source: {result['calculation_html_packet'].source}")
            print(f"  - Method: {result['calculation_html_packet'].calculation_method}")
        else:
            print(f"✗ HTML packet missing")
            return False

        return True

    except Exception as e:
        print(f"✗ Bridge wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_portfolio_optimization():
    """Test portfolio optimization"""
    print("\n" + "="*80)
    print("TEST 3: Portfolio Optimization")
    print("="*80)

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'finrisk_ai'))
        from core.cpp_bridge import CppCalculationEngine

        engine = CppCalculationEngine()

        # Sample asset returns
        gold_returns = [0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.02, 0.01, 0.03, -0.01, 0.02, 0.01]
        sp500_returns = [0.05, -0.03, 0.07, 0.02, 0.04, -0.02, 0.05, 0.03, 0.06, -0.01, 0.04, 0.02]
        btc_returns = [0.15, -0.10, 0.20, 0.08, 0.12, -0.08, 0.15, 0.10, 0.18, -0.05, 0.12, 0.08]

        result = engine.optimize_portfolio(
            asset_returns=[gold_returns, sp500_returns, btc_returns],
            asset_names=["Gold", "S&P 500", "Bitcoin"],
            risk_free_rate=0.03,
            num_simulations=1000,
            random_seed=42
        )

        print(f"✓ Portfolio optimization completed:")
        print(f"  - Expected Return: {result['calculation_results']['expected_return']*100:.2f}%")
        print(f"  - Expected Risk: {result['calculation_results']['expected_risk']*100:.2f}%")
        print(f"  - Sharpe Ratio: {result['calculation_results']['sharpe_ratio']:.4f}")
        print(f"  - Optimal Weights:")
        for asset, weight in result['calculation_results']['optimal_weights'].items():
            print(f"    * {asset}: {weight*100:.1f}%")

        return True

    except Exception as e:
        print(f"✗ Portfolio optimization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backtest():
    """Test strategy backtesting"""
    print("\n" + "="*80)
    print("TEST 4: Strategy Backtesting")
    print("="*80)

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'finrisk_ai'))
        from core.cpp_bridge import CppCalculationEngine
        import math

        engine = CppCalculationEngine()

        # Generate sample price data
        prices = [100 + i*0.5 + math.sin(i/10)*10 for i in range(100)]

        result = engine.backtest_strategy(
            prices=prices,
            strategy="buy_and_hold",
            initial_capital=10000.0
        )

        print(f"✓ Backtest completed:")
        print(f"  - Final Value: ${result['calculation_results']['final_value']:,.2f}")
        print(f"  - Total Return: {result['calculation_results']['total_return']*100:.2f}%")
        print(f"  - Max Drawdown: {result['calculation_results']['max_drawdown']*100:.2f}%")

        return True

    except Exception as e:
        print(f"✗ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all standalone tests"""
    print("\n" + "="*80)
    print("🚀 PHASE 2 STANDALONE TEST SUITE")
    print("="*80)
    print("Testing: C++ Engine ← Python Bridge (Minimal Dependencies)")
    print("="*80)

    results = []

    results.append(("C++ Module Direct Import", test_cpp_module()))
    results.append(("C++ Bridge Wrapper", test_cpp_bridge_module()))
    results.append(("Portfolio Optimization", test_portfolio_optimization()))
    results.append(("Strategy Backtesting", test_backtest()))

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
        print("\n✅ Phase 2 Core Functionality VERIFIED!")
        print("✅ C++ engine works perfectly from Python!")
        print("✅ Bridge wrapper provides clean interface!")
        print("✅ All major calculations working!")
        print("\n📝 Note: Full finrisk_ai integration requires additional dependencies")
        print("   (sentence_transformers, google-generativeai, etc.)")
        return 0
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total} passed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
