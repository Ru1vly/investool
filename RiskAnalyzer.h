#ifndef RISK_ANALYZER_H
#define RISK_ANALYZER_H

#include <vector>
#include <cmath>
#include <stdexcept>
#include <numeric>

/**
 * RiskAnalyzer - Implements risk measurement and risk-adjusted performance metrics
 *
 * These formulas measure HISTORICAL behavior. They do NOT predict the future.
 * Past performance is not a guarantee of future results.
 *
 * Based on Modern Portfolio Theory (MPT) - Widely documented by Investopedia,
 * Corporate Finance Institute (CFI), and academic finance literature.
 */
class RiskAnalyzer {
public:
    /**
     * Calculate the mean (average) of returns
     * @param returns Vector of historical returns
     * @return Average return
     */
    static double CalculateMean(const std::vector<double>& returns);

    /**
     * Formula 4: Calculate Variance (σ²)
     *
     * σ² = Σ(R_j - R̄)² / (N - 1)
     *
     * Measures the average degree to which returns differ from the mean.
     *
     * @param returns Vector of historical returns (e.g., monthly returns)
     * @return Variance - average squared deviation from mean
     */
    static double CalculateVariance(const std::vector<double>& returns);

    /**
     * Formula 5: Calculate Standard Deviation / Volatility (σ)
     *
     * σ = √(Variance)
     *
     * This is the STANDARD measure of risk.
     *
     * Interpretation:
     * - Low σ (e.g., 2%): Stable asset, low risk
     * - High σ (e.g., 40%): Volatile asset, high risk
     *
     * @param returns Vector of historical returns
     * @return Standard Deviation (Volatility) - risk measure
     */
    static double CalculateVolatility(const std::vector<double>& returns);

    /**
     * Formula 6: Calculate Sharpe Ratio
     *
     * Sharpe = (R_p - R_f) / σ_p
     *
     * Measures return per unit of risk. Higher is better.
     *
     * Interpretation:
     * - < 1.0: Poor - risk not worth it
     * - 1.0 - 1.99: Good - adequately compensated for risk
     * - ≥ 2.0: Excellent - well compensated for risk
     *
     * @param portfolioReturn Average return of the portfolio/asset
     * @param riskFreeRate Risk-free rate (e.g., government bond yield)
     * @param portfolioVolatility Volatility (σ) of the portfolio/asset
     * @return Sharpe Ratio - risk-adjusted return metric
     *
     * Source: Developed by William F. Sharpe, Nobel Prize winner
     */
    static double CalculateSharpeRatio(double portfolioReturn,
                                       double riskFreeRate,
                                       double portfolioVolatility);

    /**
     * Calculate Sharpe Ratio from return series
     * @param returns Vector of returns
     * @param riskFreeRate Risk-free rate
     * @return Sharpe Ratio
     */
    static double CalculateSharpeRatio(const std::vector<double>& returns,
                                       double riskFreeRate);

    /**
     * Calculate Covariance between two return series
     *
     * Cov(X,Y) = Σ[(X_i - X̄)(Y_i - Ȳ)] / (N - 1)
     *
     * Measures how two assets move together.
     *
     * @param returns1 First return series
     * @param returns2 Second return series
     * @return Covariance
     */
    static double CalculateCovariance(const std::vector<double>& returns1,
                                      const std::vector<double>& returns2);

    /**
     * Formula 7: Calculate Beta (β)
     *
     * β = Cov(Asset, Market) / Var(Market)
     *
     * Measures an asset's volatility relative to the market.
     *
     * Interpretation:
     * - β = 1: Moves with the market
     * - β > 1 (Aggressive): More volatile than market
     * - β < 1 (Defensive): Less volatile than market
     * - β = 0: No correlation with market
     * - β < 0: Moves opposite to market (rare)
     *
     * @param assetReturns Historical returns of the asset
     * @param marketReturns Historical returns of the market (e.g., S&P 500, BIST 100)
     * @return Beta - systematic risk measure
     *
     * Source: Part of Capital Asset Pricing Model (CAPM)
     */
    static double CalculateBeta(const std::vector<double>& assetReturns,
                                const std::vector<double>& marketReturns);

    /**
     * Convert daily volatility to annual volatility
     * Annual = Daily * √252 (252 trading days per year)
     */
    static double DailyToAnnualVolatility(double dailyVolatility);

    /**
     * Convert monthly volatility to annual volatility
     * Annual = Monthly * √12
     */
    static double MonthlyToAnnualVolatility(double monthlyVolatility);
};

#endif // RISK_ANALYZER_H
