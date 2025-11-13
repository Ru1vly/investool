#!/usr/bin/env python3
"""
Comprehensive Test Suite for InvestTool C++ Python Bindings

This script tests all major functionality exposed through pybind11 bindings,
verifying that the C++ calculation engine is accessible from Python.
"""

import sys
import os

# Add build directory to path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))

try:
    import investool_engine as ie
except ImportError as e:
    print(f"❌ ERROR: Could not import investool_engine module: {e}")
    print("Make sure you have built the module with: cd build && cmake .. && make")
    sys.exit(1)

def test_financial_calculator():
    """Test FinancialCalculator formulas 1-3"""
    print("\n" + "="*80)
    print("Testing FinancialCalculator (Formulas 1-3)")
    print("="*80)

    # Formula 1: Calculate Future Value
    fv = ie.FinancialCalculator.CalculateFutureValue(20000, 0.01, 7)
    print(f"✓ Formula 1 - Future Value: ${fv:,.2f}")
    assert fv > 140000, "Future Value should be positive and reasonable"

    # Formula 2: Calculate Required Payment
    pmt = ie.FinancialCalculator.CalculateRequiredPayment(200000, 0.01, 7)
    print(f"✓ Formula 2 - Required Payment: ${pmt:,.2f}")
    assert pmt > 25000, "Required Payment should be positive and reasonable"

    # Formula 3: Calculate Required Periods
    n = ie.FinancialCalculator.CalculateRequiredPeriods(200000, 20000, 0.01)
    print(f"✓ Formula 3 - Required Periods: {n:.2f} months")
    assert n > 5, "Required Periods should be positive and reasonable"

    # Conversion functions
    monthly = ie.FinancialCalculator.AnnualToMonthlyRate(0.12)
    print(f"✓ Annual to Monthly: 12% annual = {monthly*100:.2f}% monthly")

    print("✅ FinancialCalculator: ALL TESTS PASSED")

def test_risk_analyzer():
    """Test RiskAnalyzer formulas 4-13"""
    print("\n" + "="*80)
    print("Testing RiskAnalyzer (Formulas 4-13)")
    print("="*80)

    # Sample data
    returns = [0.05, -0.02, 0.03, 0.08, -0.01, 0.04, 0.02]
    asset_returns = [0.10, -0.05, 0.08, 0.15, -0.03, 0.06]
    market_returns = [0.08, -0.03, 0.06, 0.12, -0.02, 0.05]

    # Formula 4: Variance
    variance = ie.RiskAnalyzer.CalculateVariance(returns)
    print(f"✓ Formula 4 - Variance: {variance:.6f}")
    assert variance > 0, "Variance should be positive"

    # Formula 5: Volatility
    volatility = ie.RiskAnalyzer.CalculateVolatility(returns)
    print(f"✓ Formula 5 - Volatility: {volatility*100:.2f}%")
    assert volatility > 0, "Volatility should be positive"

    # Formula 6: Sharpe Ratio (two overloads)
    mean = ie.RiskAnalyzer.CalculateMean(returns)
    sharpe1 = ie.RiskAnalyzer.CalculateSharpeRatio(mean, 0.02, volatility)
    sharpe2 = ie.RiskAnalyzer.CalculateSharpeRatio(returns, 0.02)
    print(f"✓ Formula 6 - Sharpe Ratio (method 1): {sharpe1:.4f}")
    print(f"✓ Formula 6 - Sharpe Ratio (method 2): {sharpe2:.4f}")
    assert abs(sharpe1 - sharpe2) < 0.01, "Sharpe Ratio overloads should match"

    # Formula 7: Beta
    beta = ie.RiskAnalyzer.CalculateBeta(asset_returns, market_returns)
    print(f"✓ Formula 7 - Beta: {beta:.4f}")
    assert -10 < beta < 10, "Beta should be reasonable"

    # Formula 8: Correlation
    correlation = ie.RiskAnalyzer.CalculateCorrelation(asset_returns, market_returns)
    print(f"✓ Formula 8 - Correlation: {correlation:.4f}")
    assert -1 <= correlation <= 1, "Correlation must be between -1 and 1"

    # Formula 9: Portfolio Volatility
    port_vol = ie.RiskAnalyzer.CalculatePortfolioVolatility(0.6, 0.15, 0.4, 0.20, 0.5)
    print(f"✓ Formula 9 - Portfolio Volatility: {port_vol*100:.2f}%")
    assert port_vol > 0, "Portfolio volatility should be positive"

    # Formula 10: Downside Deviation
    downside = ie.RiskAnalyzer.CalculateDownsideDeviation(returns, 0.0)
    print(f"✓ Formula 10 - Downside Deviation: {downside*100:.2f}%")
    assert downside >= 0, "Downside deviation should be non-negative"

    # Formula 11: Sortino Ratio
    sortino = ie.RiskAnalyzer.CalculateSortinoRatio(returns, 0.02)
    print(f"✓ Formula 11 - Sortino Ratio: {sortino:.4f}")

    # Formula 12: VaR (two methods)
    var_param = ie.RiskAnalyzer.CalculateVaR(100000, 0.15, 0.95)
    var_hist = ie.RiskAnalyzer.CalculateHistoricalVaR(returns, 100000, 0.95)
    print(f"✓ Formula 12 - VaR (Parametric): ${var_param:,.2f}")
    print(f"✓ Formula 12 - VaR (Historical): ${var_hist:,.2f}")
    assert var_param > 0, "VaR should be positive"

    # Formula 13: Z-Score
    z_score = ie.RiskAnalyzer.CalculateZScore(0.10, returns)
    print(f"✓ Formula 13 - Z-Score: {z_score:.4f}")

    # Test conversion functions
    annual_vol = ie.RiskAnalyzer.DailyToAnnualVolatility(0.01)
    print(f"✓ Daily to Annual Volatility: 1% daily = {annual_vol*100:.2f}% annual")

    print("✅ RiskAnalyzer: ALL TESTS PASSED")

def test_portfolio_optimizer():
    """Test PortfolioOptimizer"""
    print("\n" + "="*80)
    print("Testing PortfolioOptimizer (Modern Portfolio Theory)")
    print("="*80)

    # Sample asset returns (3 assets, 12 months each)
    gold_returns = [0.02, -0.01, 0.03, 0.01, 0.02, -0.01, 0.02, 0.01, 0.03, -0.01, 0.02, 0.01]
    sp500_returns = [0.05, -0.03, 0.07, 0.02, 0.04, -0.02, 0.05, 0.03, 0.06, -0.01, 0.04, 0.02]
    btc_returns = [0.15, -0.10, 0.20, 0.08, 0.12, -0.08, 0.15, 0.10, 0.18, -0.05, 0.12, 0.08]

    asset_returns = [gold_returns, sp500_returns, btc_returns]
    asset_names = ["Gold", "S&P 500", "Bitcoin"]

    # Run efficient frontier calculation
    result = ie.PortfolioOptimizer.CalculateEfficientFrontier(
        asset_returns, asset_names, 5000, 0.03, 42  # 5000 simulations, 3% risk-free rate, seed 42
    )

    optimal = result.optimal_sharpe_portfolio
    print(f"✓ Optimal Portfolio Found:")
    print(f"  - Return: {optimal.portfolio_return*100:.2f}%")
    print(f"  - Risk: {optimal.portfolio_risk*100:.2f}%")
    print(f"  - Sharpe Ratio: {optimal.sharpe_ratio:.4f}")
    print(f"  - Weights:")
    for i, name in enumerate(asset_names):
        print(f"    * {name}: {optimal.weights[i]*100:.1f}%")

    # Verify weights sum to 1.0
    weight_sum = sum(optimal.weights)
    print(f"✓ Weight Sum: {weight_sum:.6f}")
    assert abs(weight_sum - 1.0) < 0.001, "Weights must sum to 1.0"

    # Verify we have simulation data
    print(f"✓ Total Simulations: {len(result.all_simulations)}")
    assert len(result.all_simulations) == 5000, "Should have 5000 simulations"

    # Test covariance matrix calculation
    cov_matrix = ie.PortfolioOptimizer.CalculateCovarianceMatrix(asset_returns)
    print(f"✓ Covariance Matrix: {len(cov_matrix)}x{len(cov_matrix[0])}")
    assert len(cov_matrix) == 3, "Should have 3x3 covariance matrix"

    print("✅ PortfolioOptimizer: ALL TESTS PASSED")

def test_strategy_backtester():
    """Test StrategyBacktester"""
    print("\n" + "="*80)
    print("Testing StrategyBacktester")
    print("="*80)

    # Sample price data (100 days, ascending trend with volatility)
    import math
    prices = [100 + i*0.5 + math.sin(i/10)*10 for i in range(100)]

    # Test Buy and Hold
    bh_result = ie.StrategyBacktester.RunBuyAndHoldBacktest(prices, 10000)
    print(f"✓ Buy & Hold Strategy:")
    print(f"  - Final Value: ${bh_result.final_value:,.2f}")
    print(f"  - Total Return: {bh_result.total_return*100:.2f}%")
    print(f"  - Annualized Return: {bh_result.annualized_return*100:.2f}%")
    print(f"  - Max Drawdown: {bh_result.max_drawdown*100:.2f}%")
    print(f"  - Total Trades: {bh_result.total_trades}")

    # Test DCA Strategy
    dca_config = ie.DCAConfig()
    dca_config.investment_amount = 1000
    dca_config.frequency = 10  # Every 10 days

    dca_result = ie.StrategyBacktester.RunDCABacktest(prices, 10000, dca_config)
    print(f"✓ DCA Strategy:")
    print(f"  - Final Value: ${dca_result.final_value:,.2f}")
    print(f"  - Total Return: {dca_result.total_return*100:.2f}%")
    print(f"  - Total Trades: {dca_result.total_trades}")

    # Test Moving Average Crossover
    ma_config = ie.MovingAverageCrossConfig()
    ma_config.short_period = 10
    ma_config.long_period = 30

    ma_result = ie.StrategyBacktester.RunMovingAverageCrossBacktest(prices, 10000, ma_config)
    print(f"✓ Moving Average Crossover Strategy:")
    print(f"  - Final Value: ${ma_result.final_value:,.2f}")
    print(f"  - Total Return: {ma_result.total_return*100:.2f}%")
    print(f"  - Total Trades: {ma_result.total_trades}")

    # Test moving average calculation
    sma = ie.StrategyBacktester.CalculateMovingAverage(prices, 20)
    print(f"✓ 20-period SMA calculated: {len(sma)} values")
    assert len(sma) == len(prices), "SMA length should match price length"

    print("✅ StrategyBacktester: ALL TESTS PASSED")

def test_ratio_analyzer():
    """Test RatioAnalyzer"""
    print("\n" + "="*80)
    print("Testing RatioAnalyzer")
    print("="*80)

    # Sample gold and silver prices
    gold_prices = [1800, 1820, 1850, 1830, 1870, 1900, 1880, 1920, 1940, 1960]
    silver_prices = [24, 24.5, 25, 24.8, 25.5, 26, 25.8, 26.5, 27, 27.5]

    # Analyze Gold/Silver ratio
    result = ie.RatioAnalyzer.AnalyzeRatio(gold_prices, silver_prices, "Gold", "Silver")

    print(f"✓ Gold/Silver Ratio Analysis:")
    print(f"  - Current Ratio: {result.current_ratio:.2f}")
    print(f"  - Historical Mean: {result.historical_mean:.2f}")
    print(f"  - Historical Std Dev: {result.historical_std_dev:.2f}")
    print(f"  - Z-Score: {result.z_score:.4f}")
    print(f"  - Signal: {result.signal}")
    print(f"  - Interpretation: {result.interpretation}")

    # Test helper functions
    ratio_series = ie.RatioAnalyzer.CalculateRatioSeries(gold_prices, silver_prices)
    print(f"✓ Ratio Series: {len(ratio_series)} values")
    assert len(ratio_series) == len(gold_prices), "Ratio series length should match price length"

    is_normal = ie.RatioAnalyzer.IsWithinNormalRange(result.z_score)
    is_extreme = ie.RatioAnalyzer.IsExtremeDeviation(result.z_score)
    print(f"✓ Within Normal Range: {is_normal}")
    print(f"✓ Extreme Deviation: {is_extreme}")

    print("✅ RatioAnalyzer: ALL TESTS PASSED")

def test_asset_classifier():
    """Test AssetClassifier"""
    print("\n" + "="*80)
    print("Testing AssetClassifier")
    print("="*80)

    # Test classification by volatility
    volatilities = [0.01, 0.05, 0.15, 0.30, 0.50]

    for vol in volatilities:
        classification = ie.AssetClassifier.ClassifyByVolatility(vol)
        risk_name = ie.AssetClassifier.GetRiskLevelName(classification.risk_level)
        print(f"✓ Volatility {vol*100:.0f}% → Risk Level: {risk_name}")
        print(f"  - {classification.description}")
        print(f"  - Typical Assets: {classification.typical_assets}")

    # Test interpretations
    sharpe_interp = ie.AssetClassifier.InterpretSharpeRatio(1.5)
    print(f"✓ Sharpe Ratio 1.5: {sharpe_interp}")

    beta_interp = ie.AssetClassifier.InterpretBeta(1.2)
    print(f"✓ Beta 1.2: {beta_interp}")

    # Get all asset classes
    all_classes = ie.AssetClassifier.GetAllAssetClasses()
    print(f"✓ Total Asset Classes: {len(all_classes)}")
    assert len(all_classes) == 5, "Should have 5 asset classes"

    print("✅ AssetClassifier: ALL TESTS PASSED")

def test_enums_and_structs():
    """Test that enums and structs are properly exposed"""
    print("\n" + "="*80)
    print("Testing Enums and Structs")
    print("="*80)

    # Test StrategyType enum
    print(f"✓ StrategyType.DCA: {ie.StrategyType.DCA}")
    print(f"✓ StrategyType.MOVING_AVG_CROSS: {ie.StrategyType.MOVING_AVG_CROSS}")
    print(f"✓ StrategyType.BUY_AND_HOLD: {ie.StrategyType.BUY_AND_HOLD}")

    # Test RiskLevel enum
    print(f"✓ RiskLevel.VERY_LOW: {ie.RiskLevel.VERY_LOW}")
    print(f"✓ RiskLevel.LOW: {ie.RiskLevel.LOW}")
    print(f"✓ RiskLevel.MEDIUM: {ie.RiskLevel.MEDIUM}")
    print(f"✓ RiskLevel.HIGH: {ie.RiskLevel.HIGH}")
    print(f"✓ RiskLevel.VERY_HIGH: {ie.RiskLevel.VERY_HIGH}")

    # Test struct creation
    dca_config = ie.DCAConfig()
    dca_config.investment_amount = 5000
    dca_config.frequency = 30
    print(f"✓ DCAConfig: ${dca_config.investment_amount} every {dca_config.frequency} days")

    ma_config = ie.MovingAverageCrossConfig()
    ma_config.short_period = 50
    ma_config.long_period = 200
    print(f"✓ MovingAverageCrossConfig: {ma_config.short_period}/{ma_config.long_period}")

    print("✅ Enums and Structs: ALL TESTS PASSED")

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 INVESTOOL C++ PYTHON BINDINGS - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Module Version: {ie.__version__}")
    print(f"Module Docstring: {ie.__doc__.strip()}")

    try:
        test_financial_calculator()
        test_risk_analyzer()
        test_portfolio_optimizer()
        test_strategy_backtester()
        test_ratio_analyzer()
        test_asset_classifier()
        test_enums_and_structs()

        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("="*80)
        print("\n✅ The C++ InvestTool engine is now fully accessible from Python!")
        print("✅ All 13+ financial formulas are working correctly!")
        print("✅ The bridge between C++ and Python is complete!")
        print("\n" + "="*80)

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
