/**
 * Python Bindings for InvestTool C++ Financial Engine
 *
 * This file creates Python-callable wrappers for all InvestTool C++ classes
 * using pybind11. This enables the finrisk_ai Python AI system to call
 * the C++ calculation engine directly with 100% accuracy.
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>      // Automatic conversion for std::vector, std::string
#include <pybind11/functional.h> // For std::function if needed

#include "FinancialCalculator.h"
#include "RiskAnalyzer.h"
#include "PortfolioOptimizer.h"
#include "StrategyBacktester.h"
#include "RatioAnalyzer.h"
#include "AssetClassifier.h"

namespace py = pybind11;

PYBIND11_MODULE(investool_engine, m) {
    m.doc() = R"pbdoc(
        InvestTool C++ Financial Engine - Python Bindings

        A production-grade financial calculation engine implementing 13+ advanced
        formulas for risk analysis, portfolio optimization, and backtesting.

        This module provides deterministic, high-performance calculations that
        bridge the InvestTool C++ library with the finrisk_ai Python AI system.
    )pbdoc";

    // ========================================================================
    // FinancialCalculator - Future Value of Annuity Calculations (Formulas 1-3)
    // ========================================================================

    py::class_<FinancialCalculator>(m, "FinancialCalculator", R"pbdoc(
        Future Value of Annuity Calculator

        Implements formulas for Dollar-Cost Averaging (DCA) strategies where
        a fixed amount is invested at regular intervals.
    )pbdoc")
        .def_static("CalculateFutureValue", &FinancialCalculator::CalculateFutureValue,
            py::arg("pmt"), py::arg("i"), py::arg("n"),
            R"pbdoc(
                Formula 1: Calculate Future Value (FV)

                FV = PMT * [(1 + i)^n - 1] / i

                Args:
                    pmt (float): Payment per period (e.g., 20,000 TL monthly)
                    i (float): Interest rate per period (e.g., 0.01 for 1% monthly)
                    n (int): Number of periods (e.g., 7 months)

                Returns:
                    float: Future Value - total amount at end of period

                Example:
                    >>> FinancialCalculator.CalculateFutureValue(20000, 0.01, 7)
                    145069.82
            )pbdoc")

        .def_static("CalculateRequiredPayment", &FinancialCalculator::CalculateRequiredPayment,
            py::arg("fv"), py::arg("i"), py::arg("n"),
            R"pbdoc(
                Formula 2: Calculate Required Payment (PMT)

                PMT = FV * i / [(1 + i)^n - 1]

                Args:
                    fv (float): Target Future Value
                    i (float): Interest rate per period
                    n (int): Number of periods

                Returns:
                    float: Required payment per period to reach goal
            )pbdoc")

        .def_static("CalculateRequiredPeriods", &FinancialCalculator::CalculateRequiredPeriods,
            py::arg("fv"), py::arg("pmt"), py::arg("i"),
            R"pbdoc(
                Formula 3: Calculate Required Number of Periods (n)

                n = ln(1 + (FV * i / PMT)) / ln(1 + i)

                Args:
                    fv (float): Target Future Value
                    pmt (float): Payment per period
                    i (float): Interest rate per period

                Returns:
                    float: Number of periods needed to reach goal
            )pbdoc")

        .def_static("AnnualToMonthlyRate", &FinancialCalculator::AnnualToMonthlyRate,
            py::arg("annual_rate"),
            "Convert annual interest rate to monthly rate")

        .def_static("MonthlyToAnnualRate", &FinancialCalculator::MonthlyToAnnualRate,
            py::arg("monthly_rate"),
            "Convert monthly interest rate to annual rate");

    // ========================================================================
    // RiskAnalyzer - Risk Measurement and Risk-Adjusted Performance (Formulas 4-13)
    // ========================================================================

    py::class_<RiskAnalyzer>(m, "RiskAnalyzer", R"pbdoc(
        Risk Analysis and Risk-Adjusted Performance Metrics

        Implements Modern Portfolio Theory (MPT) formulas for measuring
        historical risk and risk-adjusted returns. Based on Investopedia,
        Corporate Finance Institute (CFI), and academic finance literature.

        WARNING: These formulas measure HISTORICAL behavior. They do NOT
        predict the future. Past performance is not a guarantee of future results.
    )pbdoc")
        .def_static("CalculateMean", &RiskAnalyzer::CalculateMean,
            py::arg("returns"),
            "Calculate the mean (average) of returns")

        .def_static("CalculateVariance", &RiskAnalyzer::CalculateVariance,
            py::arg("returns"),
            R"pbdoc(
                Formula 4: Calculate Variance (σ²)

                σ² = Σ(R_j - R̄)² / (N - 1)

                Args:
                    returns (List[float]): Vector of historical returns

                Returns:
                    float: Variance - average squared deviation from mean
            )pbdoc")

        .def_static("CalculateVolatility", &RiskAnalyzer::CalculateVolatility,
            py::arg("returns"),
            R"pbdoc(
                Formula 5: Calculate Standard Deviation / Volatility (σ)

                σ = √(Variance)

                This is the STANDARD measure of risk.

                Interpretation:
                - Low σ (e.g., 2%): Stable asset, low risk
                - High σ (e.g., 40%): Volatile asset, high risk

                Args:
                    returns (List[float]): Vector of historical returns

                Returns:
                    float: Standard Deviation (Volatility) - risk measure
            )pbdoc")

        .def_static("CalculateSharpeRatio",
            py::overload_cast<double, double, double>(&RiskAnalyzer::CalculateSharpeRatio),
            py::arg("portfolio_return"), py::arg("risk_free_rate"), py::arg("portfolio_volatility"),
            R"pbdoc(
                Formula 6: Calculate Sharpe Ratio

                Sharpe = (R_p - R_f) / σ_p

                Measures return per unit of risk. Higher is better.

                Interpretation:
                - < 1.0: Poor - risk not worth it
                - 1.0 - 1.99: Good - adequately compensated for risk
                - ≥ 2.0: Excellent - well compensated for risk

                Args:
                    portfolio_return (float): Average return of the portfolio/asset
                    risk_free_rate (float): Risk-free rate (e.g., government bond yield)
                    portfolio_volatility (float): Volatility (σ) of the portfolio/asset

                Returns:
                    float: Sharpe Ratio - risk-adjusted return metric

                Source: Developed by William F. Sharpe, Nobel Prize winner
            )pbdoc")

        .def_static("CalculateSharpeRatio",
            py::overload_cast<const std::vector<double>&, double>(&RiskAnalyzer::CalculateSharpeRatio),
            py::arg("returns"), py::arg("risk_free_rate"),
            "Calculate Sharpe Ratio from return series")

        .def_static("CalculateCovariance", &RiskAnalyzer::CalculateCovariance,
            py::arg("returns1"), py::arg("returns2"),
            R"pbdoc(
                Calculate Covariance between two return series

                Cov(X,Y) = Σ[(X_i - X̄)(Y_i - Ȳ)] / (N - 1)

                Measures how two assets move together.
            )pbdoc")

        .def_static("CalculateBeta", &RiskAnalyzer::CalculateBeta,
            py::arg("asset_returns"), py::arg("market_returns"),
            R"pbdoc(
                Formula 7: Calculate Beta (β)

                β = Cov(Asset, Market) / Var(Market)

                Measures an asset's volatility relative to the market.

                Interpretation:
                - β = 1: Moves with the market
                - β > 1 (Aggressive): More volatile than market
                - β < 1 (Defensive): Less volatile than market
                - β = 0: No correlation with market
                - β < 0: Moves opposite to market (rare)

                Args:
                    asset_returns (List[float]): Historical returns of the asset
                    market_returns (List[float]): Historical returns of the market

                Returns:
                    float: Beta - systematic risk measure

                Source: Part of Capital Asset Pricing Model (CAPM)
            )pbdoc")

        .def_static("DailyToAnnualVolatility", &RiskAnalyzer::DailyToAnnualVolatility,
            py::arg("daily_volatility"),
            "Convert daily volatility to annual volatility (Annual = Daily * √252)")

        .def_static("MonthlyToAnnualVolatility", &RiskAnalyzer::MonthlyToAnnualVolatility,
            py::arg("monthly_volatility"),
            "Convert monthly volatility to annual volatility (Annual = Monthly * √12)")

        .def_static("CalculateCorrelation", &RiskAnalyzer::CalculateCorrelation,
            py::arg("returns1"), py::arg("returns2"),
            R"pbdoc(
                Formula 8: Calculate Correlation Coefficient (ρ)

                ρ = Cov(A, B) / (σ_A × σ_B)

                Measures the degree to which two assets move in relation to each other.
                Range: -1 (perfect inverse) to +1 (perfect positive correlation)
            )pbdoc")

        .def_static("CalculatePortfolioVolatility", &RiskAnalyzer::CalculatePortfolioVolatility,
            py::arg("weight1"), py::arg("sigma1"), py::arg("weight2"), py::arg("sigma2"), py::arg("correlation"),
            R"pbdoc(
                Formula 9: Calculate Two-Asset Portfolio Volatility

                σ_p = √[w_A² × σ_A² + w_B² × σ_B² + 2 × w_A × w_B × ρ_AB × σ_A × σ_B]

                Calculates portfolio risk accounting for diversification effects.
            )pbdoc")

        .def_static("CalculateDownsideDeviation", &RiskAnalyzer::CalculateDownsideDeviation,
            py::arg("returns"), py::arg("MARR") = 0.0,
            R"pbdoc(
                Formula 10: Calculate Downside Deviation (σ_d)

                σ_d = √[Σ min(0, R_i - MARR)² / n]

                Measures only negative volatility (downside risk).

                Args:
                    returns (List[float]): Vector of returns
                    MARR (float): Minimum Acceptable Rate of Return (default: 0.0)
            )pbdoc")

        .def_static("CalculateSortinoRatio", &RiskAnalyzer::CalculateSortinoRatio,
            py::arg("returns"), py::arg("risk_free_rate"), py::arg("MARR") = -999.0,
            R"pbdoc(
                Formula 11: Calculate Sortino Ratio

                Sortino = (R_p - R_f) / σ_d

                Risk-adjusted return using only downside deviation.
                Better measure than Sharpe for asymmetric returns.

                Interpretation (similar to Sharpe):
                - < 1.0: Poor - downside risk not worth it
                - 1.0 - 1.99: Good - adequately compensated
                - ≥ 2.0: Excellent - well compensated

                Source: Frank A. Sortino and Robert van der Meer (1991)
            )pbdoc")

        .def_static("CalculateVaR", &RiskAnalyzer::CalculateVaR,
            py::arg("portfolio_value"), py::arg("volatility"), py::arg("confidence_level"), py::arg("expected_return") = 0.0,
            R"pbdoc(
                Formula 12: Calculate Value at Risk (VaR) - Parametric Method

                VaR = |μ - Z × σ|

                Quantifies potential loss at a given confidence level.

                Source: J.P. Morgan RiskMetrics (1996)
            )pbdoc")

        .def_static("CalculateHistoricalVaR", &RiskAnalyzer::CalculateHistoricalVaR,
            py::arg("returns"), py::arg("portfolio_value"), py::arg("confidence_level"),
            R"pbdoc(
                Calculate Historical Value at Risk

                More robust than parametric VaR as it doesn't assume normal distribution.
                Uses actual historical returns to find loss at confidence level.
            )pbdoc")

        .def_static("CalculateZScore", &RiskAnalyzer::CalculateZScore,
            py::arg("current_value"), py::arg("historical_data"),
            R"pbdoc(
                Formula 13: Calculate Z-Score

                Z = (x - μ) / σ

                Measures how many standard deviations an observation is from the mean.

                Interpretation:
                - |Z| < 1: Within normal range
                - |Z| < 2: Moderate deviation
                - |Z| < 3: Significant deviation
                - |Z| ≥ 3: Extreme deviation (very rare)
            )pbdoc");

    // ========================================================================
    // PortfolioOptimizer - Modern Portfolio Theory
    // ========================================================================

    // Bind PortfolioResult struct
    py::class_<PortfolioResult>(m, "PortfolioResult", "Results from a single portfolio simulation")
        .def_readonly("portfolio_return", &PortfolioResult::portfolioReturn, "Annualized expected return")
        .def_readonly("portfolio_risk", &PortfolioResult::portfolioRisk, "Annualized volatility (standard deviation)")
        .def_readonly("sharpe_ratio", &PortfolioResult::sharpeRatio, "Risk-adjusted return metric")
        .def_readonly("weights", &PortfolioResult::weights, "Asset allocation weights (sum to 1.0)")
        .def("__repr__", [](const PortfolioResult& r) {
            return "<PortfolioResult: return=" + std::to_string(r.portfolioReturn) +
                   ", risk=" + std::to_string(r.portfolioRisk) +
                   ", sharpe=" + std::to_string(r.sharpeRatio) + ">";
        });

    // Bind EfficientFrontierResult struct
    py::class_<EfficientFrontierResult>(m, "EfficientFrontierResult", "Results from efficient frontier analysis")
        .def_readonly("optimal_sharpe_portfolio", &EfficientFrontierResult::optimalSharpePortfolio,
            "Portfolio with highest Sharpe Ratio")
        .def_readonly("all_simulations", &EfficientFrontierResult::allSimulations,
            "All simulated portfolios")
        .def_readonly("asset_names", &EfficientFrontierResult::assetNames,
            "Names of assets in portfolio");

    // Bind PortfolioOptimizer class
    py::class_<PortfolioOptimizer>(m, "PortfolioOptimizer", R"pbdoc(
        Modern Portfolio Theory Optimization

        Uses Monte Carlo simulation to find the optimal asset allocation that
        maximizes risk-adjusted returns (Sharpe Ratio).

        Based on Modern Portfolio Theory by Harry Markowitz (Nobel Prize, 1990)

        WARNING: This uses HISTORICAL data. Past performance does NOT guarantee
        future results. Optimal allocations change as market conditions change.
    )pbdoc")
        .def_static("CalculateEfficientFrontier", &PortfolioOptimizer::CalculateEfficientFrontier,
            py::arg("asset_returns"), py::arg("asset_names"), py::arg("num_portfolios"),
            py::arg("risk_free_rate"), py::arg("random_seed") = 0,
            R"pbdoc(
                Calculate the efficient frontier using Monte Carlo simulation

                This function simulates thousands of random portfolio allocations,
                calculates their expected return and risk, and finds the optimal
                portfolio with the highest Sharpe Ratio.

                Args:
                    asset_returns (List[List[float]]): Vector of return series for each asset
                    asset_names (List[str]): Names of assets for labeling
                    num_portfolios (int): Number of random portfolios to simulate
                    risk_free_rate (float): Annual risk-free rate
                    random_seed (int): Random seed for reproducibility (0 = random)

                Returns:
                    EfficientFrontierResult: Optimal portfolio and all simulations
            )pbdoc")

        .def_static("CalculatePortfolioReturn", &PortfolioOptimizer::CalculatePortfolioReturn,
            py::arg("weights"), py::arg("mean_returns"),
            "Calculate portfolio expected return: Σ(weight_i × mean_return_i)")

        .def_static("CalculatePortfolioRisk", &PortfolioOptimizer::CalculatePortfolioRisk,
            py::arg("weights"), py::arg("cov_matrix"),
            "Calculate portfolio volatility: √(w^T × Σ × w)")

        .def_static("CalculateCovarianceMatrix", &PortfolioOptimizer::CalculateCovarianceMatrix,
            py::arg("asset_returns"),
            "Calculate covariance matrix for multiple assets");

    // ========================================================================
    // StrategyBacktester - Backtest Investment Strategies
    // ========================================================================

    // Bind enums
    py::enum_<StrategyType>(m, "StrategyType", "Available backtesting strategies")
        .value("DCA", StrategyType::DCA, "Dollar-Cost Averaging")
        .value("MOVING_AVG_CROSS", StrategyType::MOVING_AVG_CROSS, "Moving Average Crossover")
        .value("BUY_AND_HOLD", StrategyType::BUY_AND_HOLD, "Buy and Hold")
        .export_values();

    // Bind structs
    py::class_<PricePoint>(m, "PricePoint", "Single day's price data")
        .def_readonly("day_index", &PricePoint::dayIndex)
        .def_readonly("price", &PricePoint::price)
        .def_readonly("short_ma", &PricePoint::shortMA)
        .def_readonly("long_ma", &PricePoint::longMA);

    py::class_<PortfolioSnapshot>(m, "PortfolioSnapshot", "Portfolio state at a point in time")
        .def_readonly("day_index", &PortfolioSnapshot::dayIndex)
        .def_readonly("portfolio_value", &PortfolioSnapshot::portfolioValue)
        .def_readonly("cash", &PortfolioSnapshot::cash)
        .def_readonly("shares", &PortfolioSnapshot::shares)
        .def_readonly("price", &PortfolioSnapshot::price);

    py::class_<DCAConfig>(m, "DCAConfig", "Configuration for Dollar-Cost Averaging strategy")
        .def(py::init<>())
        .def_readwrite("investment_amount", &DCAConfig::investmentAmount)
        .def_readwrite("frequency", &DCAConfig::frequency);

    py::class_<MovingAverageCrossConfig>(m, "MovingAverageCrossConfig", "Configuration for Moving Average Crossover")
        .def(py::init<>())
        .def_readwrite("short_period", &MovingAverageCrossConfig::shortPeriod)
        .def_readwrite("long_period", &MovingAverageCrossConfig::longPeriod);

    py::class_<BacktestResult>(m, "BacktestResult", "Results from a backtest simulation")
        .def_readonly("portfolio_history", &BacktestResult::portfolioHistory)
        .def_readonly("final_value", &BacktestResult::finalValue)
        .def_readonly("total_return", &BacktestResult::totalReturn)
        .def_readonly("annualized_return", &BacktestResult::annualizedReturn)
        .def_readonly("max_drawdown", &BacktestResult::maxDrawdown)
        .def_readonly("total_trades", &BacktestResult::totalTrades)
        .def("__repr__", [](const BacktestResult& r) {
            return "<BacktestResult: final_value=$" + std::to_string(r.finalValue) +
                   ", total_return=" + std::to_string(r.totalReturn * 100) + "%>";
        });

    // Bind StrategyBacktester class
    py::class_<StrategyBacktester>(m, "StrategyBacktester", R"pbdoc(
        Backtest Investment Strategies on Historical Data

        Tests how different strategies would have performed using historical prices.

        WARNING: Past performance does NOT guarantee future results.
        Historical backtests are subject to:
        - Survivorship bias (only testing assets that survived)
        - Look-ahead bias (if not careful with data)
        - Overfitting (strategies that worked in past may not work in future)
    )pbdoc")
        .def_static("RunBacktest", &StrategyBacktester::RunBacktest,
            py::arg("prices"), py::arg("strategy"), py::arg("initial_capital"),
            py::arg("dca_config") = nullptr, py::arg("ma_config") = nullptr,
            "Run a backtest simulation")

        .def_static("RunDCABacktest", &StrategyBacktester::RunDCABacktest,
            py::arg("prices"), py::arg("initial_capital"), py::arg("config"),
            "Run Dollar-Cost Averaging backtest")

        .def_static("RunMovingAverageCrossBacktest", &StrategyBacktester::RunMovingAverageCrossBacktest,
            py::arg("prices"), py::arg("initial_capital"), py::arg("config"),
            "Run Moving Average Crossover backtest")

        .def_static("RunBuyAndHoldBacktest", &StrategyBacktester::RunBuyAndHoldBacktest,
            py::arg("prices"), py::arg("initial_capital"),
            "Run Buy and Hold backtest")

        .def_static("CalculateMovingAverage", &StrategyBacktester::CalculateMovingAverage,
            py::arg("prices"), py::arg("period"),
            "Calculate Simple Moving Average (SMA)")

        .def_static("CalculateMaxDrawdown", &StrategyBacktester::CalculateMaxDrawdown,
            py::arg("portfolio_history"),
            "Calculate maximum drawdown from portfolio history")

        .def_static("CalculateAnnualizedReturn", &StrategyBacktester::CalculateAnnualizedReturn,
            py::arg("total_return"), py::arg("num_days"),
            "Calculate annualized return");

    // ========================================================================
    // RatioAnalyzer - Asset Ratio Analysis
    // ========================================================================

    py::class_<RatioAnalysisResult>(m, "RatioAnalysisResult", "Results from ratio analysis")
        .def_readonly("current_ratio", &RatioAnalysisResult::currentRatio)
        .def_readonly("historical_mean", &RatioAnalysisResult::historicalMean)
        .def_readonly("historical_std_dev", &RatioAnalysisResult::historicalStdDev)
        .def_readonly("z_score", &RatioAnalysisResult::zScore)
        .def_readonly("signal", &RatioAnalysisResult::signal)
        .def_readonly("interpretation", &RatioAnalysisResult::interpretation)
        .def("__repr__", [](const RatioAnalysisResult& r) {
            return "<RatioAnalysisResult: ratio=" + std::to_string(r.currentRatio) +
                   ", z_score=" + std::to_string(r.zScore) +
                   ", signal='" + r.signal + "'>";
        });

    py::class_<RatioAnalyzer>(m, "RatioAnalyzer", R"pbdoc(
        Asset Ratio Analysis using Z-Score

        Identifies when one asset is historically cheap or expensive relative
        to another, which can signal mean reversion opportunities.

        Common uses:
        - Gold/Silver Ratio
        - Stock pairs trading
        - P/E Ratios vs historical average

        WARNING: Mean reversion is NOT guaranteed. Historical relationships
        can break down due to structural changes in markets.
    )pbdoc")
        .def_static("AnalyzeRatio", &RatioAnalyzer::AnalyzeRatio,
            py::arg("prices_a"), py::arg("prices_b"), py::arg("asset_name_a"), py::arg("asset_name_b"),
            "Analyze ratio between two assets using Z-Score")

        .def_static("CalculateRatioSeries", &RatioAnalyzer::CalculateRatioSeries,
            py::arg("prices_a"), py::arg("prices_b"),
            "Calculate historical ratio series")

        .def_static("GenerateSignal", &RatioAnalyzer::GenerateSignal,
            py::arg("z_score"), py::arg("asset_name_a"), py::arg("asset_name_b"),
            "Generate trading signal from Z-Score")

        .def_static("InterpretZScore", &RatioAnalyzer::InterpretZScore,
            py::arg("z_score"),
            "Generate detailed interpretation of Z-Score")

        .def_static("IsWithinNormalRange", &RatioAnalyzer::IsWithinNormalRange,
            py::arg("z_score"),
            "Check if ratio is within normal range (|Z| < 1.0)")

        .def_static("IsExtremeDeviation", &RatioAnalyzer::IsExtremeDeviation,
            py::arg("z_score"),
            "Check if ratio shows extreme deviation (|Z| >= 2.0)");

    // ========================================================================
    // AssetClassifier - Risk Classification
    // ========================================================================

    py::enum_<RiskLevel>(m, "RiskLevel", "Risk levels for asset classification")
        .value("VERY_LOW", RiskLevel::VERY_LOW, "0% - 2% annual volatility")
        .value("LOW", RiskLevel::LOW, "2% - 8% annual volatility")
        .value("MEDIUM", RiskLevel::MEDIUM, "8% - 20% annual volatility")
        .value("HIGH", RiskLevel::HIGH, "20% - 40% annual volatility")
        .value("VERY_HIGH", RiskLevel::VERY_HIGH, "40%+ annual volatility")
        .export_values();

    py::class_<AssetClass>(m, "AssetClass", "Asset classification information")
        .def_readonly("risk_level", &AssetClass::riskLevel)
        .def_readonly("min_volatility", &AssetClass::minVolatility)
        .def_readonly("max_volatility", &AssetClass::maxVolatility)
        .def_readonly("description", &AssetClass::description)
        .def_readonly("typical_assets", &AssetClass::typicalAssets)
        .def_readonly("return_expectation", &AssetClass::returnExpectation)
        .def_readonly("risk_of_loss", &AssetClass::riskOfLoss)
        .def("__repr__", [](const AssetClass& a) {
            return "<AssetClass: " + a.description + " (" +
                   std::to_string(a.minVolatility) + "% - " +
                   std::to_string(a.maxVolatility) + "%)>";
        });

    py::class_<AssetClassifier>(m, "AssetClassifier", R"pbdoc(
        Asset Classification based on Volatility (Risk)

        Based on general financial industry standards for asset classification.
    )pbdoc")
        .def_static("GetAllAssetClasses", &AssetClassifier::GetAllAssetClasses,
            "Get all asset classifications")

        .def_static("ClassifyByVolatility", &AssetClassifier::ClassifyByVolatility,
            py::arg("annual_volatility"),
            "Classify an asset based on its annual volatility")

        .def_static("GetRiskLevelName", &AssetClassifier::GetRiskLevelName,
            py::arg("level"),
            "Get risk level name as string")

        .def_static("InterpretSharpeRatio", &AssetClassifier::InterpretSharpeRatio,
            py::arg("sharpe_ratio"),
            "Get interpretation for a Sharpe Ratio value")

        .def_static("InterpretBeta", &AssetClassifier::InterpretBeta,
            py::arg("beta"),
            "Get interpretation for a Beta value")

        .def_static("PrintAssetClassificationTable", &AssetClassifier::PrintAssetClassificationTable,
            "Print a formatted asset classification table");

    // Version info
    m.attr("__version__") = "1.0.0";
}
