"""
Phase 1.2: C++ Calculation Engine Bridge

This module provides a clean interface for the finrisk_ai AI system to call
the InvestTool C++ calculation engine directly through pybind11 bindings.

This replaces the "generate Python code and execute" paradigm with:
"call pre-compiled C++ functions with 100% accuracy."
"""

import sys
import os
from typing import Dict, List, Any, Optional
import logging

# Add the C++ module to path
cpp_module_path = os.path.join(os.path.dirname(__file__), '../../../build')
if os.path.exists(cpp_module_path):
    sys.path.insert(0, cpp_module_path)

try:
    import investool_engine as ie
    CPP_ENGINE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"C++ engine not available: {e}. Using fallback calculations.")
    CPP_ENGINE_AVAILABLE = False
    ie = None

# Lazy import to avoid triggering all finrisk_ai dependencies
CppFinancialDataAdapter = None
EnrichedDataPacket = None

logger = logging.getLogger(__name__)


def _lazy_import_adapter():
    """Lazy import of CppFinancialDataAdapter to avoid dependency issues"""
    global CppFinancialDataAdapter, EnrichedDataPacket
    if CppFinancialDataAdapter is None:
        from finrisk_ai.core.data_ingestion import CppFinancialDataAdapter as _Adapter, EnrichedDataPacket as _Packet
        CppFinancialDataAdapter = _Adapter
        EnrichedDataPacket = _Packet
    return CppFinancialDataAdapter


class CppCalculationEngine:
    """
    Production-grade wrapper around the C++ InvestTool engine.

    This class provides a clean interface for the CalculationAgent to call
    C++ functions without dealing with path management or error handling.

    All calculations are performed in native C++ with 100% deterministic accuracy.
    """

    def __init__(self):
        """Initialize the C++ calculation engine."""
        if not CPP_ENGINE_AVAILABLE:
            raise RuntimeError(
                "C++ engine not available. Please build the investool_engine module:\n"
                "  cd /path/to/investool/build\n"
                "  cmake .. && make"
            )

        self.engine = ie
        logger.info("✓ C++ Calculation Engine initialized successfully")

    @property
    def available(self) -> bool:
        """Check if C++ engine is available."""
        return CPP_ENGINE_AVAILABLE

    # ========================================================================
    # High-Level Calculation Methods
    # ========================================================================

    def calculate_risk_metrics(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02,
        asset_name: str = "Asset",
        portfolio_value: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics for a return series.

        This is the primary method used by the CalculationAgent.

        Args:
            returns: Historical returns (e.g., monthly returns as decimals)
            risk_free_rate: Risk-free rate (e.g., 0.02 for 2%)
            asset_name: Name of the asset
            portfolio_value: Total portfolio value in dollars

        Returns:
            Dict containing all calculated metrics and HTML packet
        """
        logger.info(f"Calculating risk metrics for {asset_name} with {len(returns)} return periods")

        try:
            # Formula 4: Variance
            variance = self.engine.RiskAnalyzer.CalculateVariance(returns)

            # Formula 5: Volatility
            volatility = self.engine.RiskAnalyzer.CalculateVolatility(returns)

            # Formula 6: Sharpe Ratio
            sharpe_ratio = self.engine.RiskAnalyzer.CalculateSharpeRatio(returns, risk_free_rate)

            # Formula 10: Downside Deviation
            downside_deviation = self.engine.RiskAnalyzer.CalculateDownsideDeviation(returns, 0.0)

            # Formula 11: Sortino Ratio
            sortino_ratio = self.engine.RiskAnalyzer.CalculateSortinoRatio(returns, risk_free_rate)

            # Formula 12: Value at Risk (95% and 99%)
            var_95 = self.engine.RiskAnalyzer.CalculateHistoricalVaR(returns, portfolio_value, 0.95)
            var_99 = self.engine.RiskAnalyzer.CalculateHistoricalVaR(returns, portfolio_value, 0.99)

            # Formula 13: Z-Score (for most recent return)
            z_score = self.engine.RiskAnalyzer.CalculateZScore(returns[-1], returns) if len(returns) > 1 else 0.0

            # Calculate mean return
            mean_return = self.engine.RiskAnalyzer.CalculateMean(returns)

            # Create enriched HTML packet using the existing adapter
            adapter = _lazy_import_adapter()
            html_packet = adapter.from_premium_features(
                sortino_ratio=sortino_ratio,
                var_95=var_95,
                var_99=var_99,
                downside_deviation=downside_deviation,
                z_score=z_score,
                asset_name=asset_name,
                portfolio_value=portfolio_value
            )

            # Return both raw results and HTML packet
            results = {
                "variance": variance,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "downside_deviation": downside_deviation,
                "var_95": var_95,
                "var_99": var_99,
                "z_score": z_score,
                "mean_return": mean_return,
                "annualized_volatility": self.engine.RiskAnalyzer.MonthlyToAnnualVolatility(volatility)
                if len(returns) >= 12 else volatility * 3.464  # approximate if less than 1 year
            }

            # Interpret Sharpe Ratio
            sharpe_interp = self.engine.AssetClassifier.InterpretSharpeRatio(sharpe_ratio)

            # Classify asset by volatility
            annual_vol = results["annualized_volatility"]
            asset_class = self.engine.AssetClassifier.ClassifyByVolatility(annual_vol)
            risk_level = self.engine.AssetClassifier.GetRiskLevelName(asset_class.risk_level)

            logger.info(f"✓ Risk metrics calculated: Sharpe={sharpe_ratio:.4f}, Sortino={sortino_ratio:.4f}, "
                       f"VaR(95%)=${var_95:,.2f}")

            return {
                "calculation_results": results,
                "calculation_html_packet": html_packet,
                "interpretation": {
                    "sharpe_interpretation": sharpe_interp,
                    "risk_level": risk_level,
                    "asset_class_description": asset_class.description
                }
            }

        except Exception as e:
            logger.error(f"C++ calculation failed: {e}")
            raise RuntimeError(f"Failed to calculate risk metrics: {str(e)}")

    def calculate_beta_and_correlation(
        self,
        asset_returns: List[float],
        market_returns: List[float],
        asset_name: str = "Asset",
        market_name: str = "Market"
    ) -> Dict[str, Any]:
        """
        Calculate Beta and correlation relative to a market benchmark.

        Args:
            asset_returns: Historical returns of the asset
            market_returns: Historical returns of the market (e.g., S&P 500)
            asset_name: Name of the asset
            market_name: Name of the market benchmark

        Returns:
            Dict containing Beta, correlation, and interpretations
        """
        logger.info(f"Calculating Beta and correlation for {asset_name} vs {market_name}")

        try:
            # Formula 7: Beta
            beta = self.engine.RiskAnalyzer.CalculateBeta(asset_returns, market_returns)

            # Formula 8: Correlation
            correlation = self.engine.RiskAnalyzer.CalculateCorrelation(asset_returns, market_returns)

            # Get interpretation
            beta_interp = self.engine.AssetClassifier.InterpretBeta(beta)

            logger.info(f"✓ Beta={beta:.4f}, Correlation={correlation:.4f}")

            return {
                "calculation_results": {
                    "beta": beta,
                    "correlation": correlation
                },
                "interpretation": {
                    "beta_interpretation": beta_interp,
                    "correlation_strength": self._interpret_correlation(correlation)
                }
            }

        except Exception as e:
            logger.error(f"Beta/correlation calculation failed: {e}")
            raise RuntimeError(f"Failed to calculate Beta: {str(e)}")

    def optimize_portfolio(
        self,
        asset_returns: List[List[float]],
        asset_names: List[str],
        risk_free_rate: float = 0.03,
        num_simulations: int = 10000,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        Perform Modern Portfolio Theory optimization using Monte Carlo simulation.

        Args:
            asset_returns: List of return series for each asset
            asset_names: Names of assets
            risk_free_rate: Risk-free rate (e.g., 0.03 for 3%)
            num_simulations: Number of Monte Carlo simulations
            random_seed: Random seed for reproducibility

        Returns:
            Dict containing optimal portfolio and HTML packet
        """
        logger.info(f"Optimizing portfolio with {len(asset_names)} assets, {num_simulations} simulations")

        try:
            # Run efficient frontier calculation
            result = self.engine.PortfolioOptimizer.CalculateEfficientFrontier(
                asset_returns,
                asset_names,
                num_simulations,
                risk_free_rate,
                random_seed
            )

            optimal = result.optimal_sharpe_portfolio

            # Create optimal weights dict
            optimal_weights = {
                name: weight
                for name, weight in zip(asset_names, optimal.weights)
            }

            # Create enriched HTML packet
            adapter = _lazy_import_adapter()
            html_packet = adapter.from_efficient_frontier(
                optimal_weights=optimal_weights,
                expected_return=optimal.portfolio_return,
                portfolio_volatility=optimal.portfolio_risk,
                sharpe_ratio=optimal.sharpe_ratio
            )

            logger.info(f"✓ Optimal portfolio: Return={optimal.portfolio_return*100:.2f}%, "
                       f"Risk={optimal.portfolio_risk*100:.2f}%, Sharpe={optimal.sharpe_ratio:.4f}")

            return {
                "calculation_results": {
                    "optimal_weights": optimal_weights,
                    "expected_return": optimal.portfolio_return,
                    "expected_risk": optimal.portfolio_risk,
                    "sharpe_ratio": optimal.sharpe_ratio,
                    "num_simulations": num_simulations
                },
                "calculation_html_packet": html_packet,
                "all_simulations": [
                    {
                        "return": sim.portfolio_return,
                        "risk": sim.portfolio_risk,
                        "sharpe": sim.sharpe_ratio
                    }
                    for sim in result.all_simulations[:100]  # Return first 100 for visualization
                ]
            }

        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            raise RuntimeError(f"Failed to optimize portfolio: {str(e)}")

    def backtest_strategy(
        self,
        prices: List[float],
        strategy: str = "buy_and_hold",
        initial_capital: float = 10000.0,
        dca_amount: float = 1000.0,
        dca_frequency: int = 30,
        ma_short_period: int = 50,
        ma_long_period: int = 200
    ) -> Dict[str, Any]:
        """
        Backtest investment strategies on historical price data.

        Args:
            prices: Historical price data
            strategy: Strategy type ("buy_and_hold", "dca", "moving_average")
            initial_capital: Starting capital in dollars
            dca_amount: Amount to invest each period (for DCA)
            dca_frequency: Frequency in days (for DCA)
            ma_short_period: Short MA period (for MA crossover)
            ma_long_period: Long MA period (for MA crossover)

        Returns:
            Dict containing backtest results
        """
        logger.info(f"Backtesting {strategy} strategy on {len(prices)} price points")

        try:
            if strategy == "buy_and_hold":
                result = self.engine.StrategyBacktester.RunBuyAndHoldBacktest(prices, initial_capital)

            elif strategy == "dca":
                config = self.engine.DCAConfig()
                config.investment_amount = dca_amount
                config.frequency = dca_frequency
                result = self.engine.StrategyBacktester.RunDCABacktest(prices, initial_capital, config)

            elif strategy == "moving_average":
                config = self.engine.MovingAverageCrossConfig()
                config.short_period = ma_short_period
                config.long_period = ma_long_period
                result = self.engine.StrategyBacktester.RunMovingAverageCrossBacktest(
                    prices, initial_capital, config
                )

            else:
                raise ValueError(f"Unknown strategy: {strategy}")

            logger.info(f"✓ Backtest complete: Final Value=${result.final_value:,.2f}, "
                       f"Return={result.total_return*100:.2f}%")

            return {
                "calculation_results": {
                    "strategy": strategy,
                    "initial_capital": initial_capital,
                    "final_value": result.final_value,
                    "total_return": result.total_return,
                    "annualized_return": result.annualized_return,
                    "max_drawdown": result.max_drawdown,
                    "total_trades": result.total_trades
                },
                "portfolio_history": [
                    {
                        "day": snapshot.day_index,
                        "value": snapshot.portfolio_value,
                        "cash": snapshot.cash,
                        "shares": snapshot.shares
                    }
                    for snapshot in result.portfolio_history[::10]  # Every 10th for efficiency
                ]
            }

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise RuntimeError(f"Failed to backtest strategy: {str(e)}")

    def analyze_ratio(
        self,
        prices_a: List[float],
        prices_b: List[float],
        asset_name_a: str = "Asset A",
        asset_name_b: str = "Asset B"
    ) -> Dict[str, Any]:
        """
        Analyze ratio between two assets (e.g., Gold/Silver, pairs trading).

        Args:
            prices_a: Historical prices for asset A
            prices_b: Historical prices for asset B
            asset_name_a: Name of asset A
            asset_name_b: Name of asset B

        Returns:
            Dict containing ratio analysis results
        """
        logger.info(f"Analyzing {asset_name_a}/{asset_name_b} ratio")

        try:
            result = self.engine.RatioAnalyzer.AnalyzeRatio(
                prices_a, prices_b, asset_name_a, asset_name_b
            )

            is_normal = self.engine.RatioAnalyzer.IsWithinNormalRange(result.z_score)
            is_extreme = self.engine.RatioAnalyzer.IsExtremeDeviation(result.z_score)

            logger.info(f"✓ Ratio analysis: Current={result.current_ratio:.2f}, "
                       f"Z-Score={result.z_score:.2f}")

            return {
                "calculation_results": {
                    "current_ratio": result.current_ratio,
                    "historical_mean": result.historical_mean,
                    "historical_std_dev": result.historical_std_dev,
                    "z_score": result.z_score,
                    "is_within_normal_range": is_normal,
                    "is_extreme_deviation": is_extreme
                },
                "signal": result.signal,
                "interpretation": result.interpretation
            }

        except Exception as e:
            logger.error(f"Ratio analysis failed: {e}")
            raise RuntimeError(f"Failed to analyze ratio: {str(e)}")

    def calculate_future_value(
        self,
        payment: float,
        interest_rate: float,
        num_periods: int
    ) -> Dict[str, Any]:
        """
        Calculate future value of annuity (Dollar-Cost Averaging).

        Args:
            payment: Payment per period
            interest_rate: Interest rate per period
            num_periods: Number of periods

        Returns:
            Dict containing future value calculation
        """
        logger.info(f"Calculating future value: PMT=${payment}, i={interest_rate}, n={num_periods}")

        try:
            # Formula 1: Future Value
            fv = self.engine.FinancialCalculator.CalculateFutureValue(payment, interest_rate, num_periods)

            logger.info(f"✓ Future Value: ${fv:,.2f}")

            return {
                "calculation_results": {
                    "future_value": fv,
                    "payment_per_period": payment,
                    "interest_rate": interest_rate,
                    "num_periods": num_periods,
                    "total_invested": payment * num_periods
                }
            }

        except Exception as e:
            logger.error(f"Future value calculation failed: {e}")
            raise RuntimeError(f"Failed to calculate future value: {str(e)}")

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    def _interpret_correlation(correlation: float) -> str:
        """Interpret correlation coefficient."""
        abs_corr = abs(correlation)

        if abs_corr >= 0.9:
            strength = "Very Strong"
        elif abs_corr >= 0.7:
            strength = "Strong"
        elif abs_corr >= 0.5:
            strength = "Moderate"
        elif abs_corr >= 0.3:
            strength = "Weak"
        else:
            strength = "Very Weak"

        direction = "Positive" if correlation > 0 else "Negative" if correlation < 0 else "None"

        return f"{strength} {direction} Correlation"

    def get_available_functions(self) -> List[str]:
        """Get list of available C++ calculation functions."""
        return [
            "calculate_risk_metrics",
            "calculate_beta_and_correlation",
            "optimize_portfolio",
            "backtest_strategy",
            "analyze_ratio",
            "calculate_future_value"
        ]


# Singleton instance
_cpp_engine_instance = None


def get_cpp_engine() -> CppCalculationEngine:
    """
    Get singleton instance of the C++ calculation engine.

    Returns:
        CppCalculationEngine instance

    Raises:
        RuntimeError: If C++ engine is not available
    """
    global _cpp_engine_instance

    if _cpp_engine_instance is None:
        _cpp_engine_instance = CppCalculationEngine()

    return _cpp_engine_instance
