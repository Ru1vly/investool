#ifndef PORTFOLIO_OPTIMIZER_H
#define PORTFOLIO_OPTIMIZER_H

#include <vector>
#include <string>
#include <cmath>
#include <random>
#include <algorithm>
#include <stdexcept>

/**
 * Structure representing a single simulated portfolio
 */
struct PortfolioResult {
    double portfolioReturn;       // Annualized expected return
    double portfolioRisk;         // Annualized volatility (standard deviation)
    double sharpeRatio;           // Risk-adjusted return metric
    std::vector<double> weights;  // Asset allocation weights (sum to 1.0)
};

/**
 * Structure representing the efficient frontier analysis results
 */
struct EfficientFrontierResult {
    PortfolioResult optimalSharpePortfolio;        // Portfolio with highest Sharpe Ratio
    std::vector<PortfolioResult> allSimulations;   // All simulated portfolios
    std::vector<std::string> assetNames;           // Names of assets in portfolio
};

/**
 * PortfolioOptimizer - Implements Modern Portfolio Theory optimization
 *
 * Uses Monte Carlo simulation to find the optimal asset allocation that
 * maximizes risk-adjusted returns (Sharpe Ratio).
 *
 * WARNING: This uses HISTORICAL data. Past performance does NOT guarantee
 * future results. Optimal allocations change as market conditions change.
 *
 * Based on Modern Portfolio Theory by Harry Markowitz (Nobel Prize, 1990)
 */
class PortfolioOptimizer {
public:
    /**
     * Calculate the efficient frontier using Monte Carlo simulation
     *
     * This function simulates thousands of random portfolio allocations,
     * calculates their expected return and risk, and finds the optimal
     * portfolio with the highest Sharpe Ratio.
     *
     * Algorithm:
     * 1. Generate random weights for each asset (sum to 1.0)
     * 2. Calculate portfolio return: weighted average of asset returns
     * 3. Calculate portfolio risk: √(w^T × Σ × w) where Σ is covariance matrix
     * 4. Calculate Sharpe Ratio: (return - risk_free) / risk
     * 5. Repeat for numPortfolios iterations
     * 6. Find portfolio with maximum Sharpe Ratio
     *
     * @param assetReturns Vector of return series for each asset
     *                     Example: {goldReturns, sp500Returns, btcReturns}
     * @param assetNames Names of assets for labeling
     * @param numPortfolios Number of random portfolios to simulate (e.g., 10,000)
     * @param riskFreeRate Annual risk-free rate (e.g., 0.03 for 3%)
     * @param randomSeed Random seed for reproducibility (0 = random)
     * @return EfficientFrontierResult containing optimal portfolio and all simulations
     */
    static EfficientFrontierResult CalculateEfficientFrontier(
        const std::vector<std::vector<double>>& assetReturns,
        const std::vector<std::string>& assetNames,
        int numPortfolios,
        double riskFreeRate,
        unsigned int randomSeed = 0
    );

    /**
     * Calculate portfolio expected return
     *
     * Portfolio Return = Σ(weight_i × mean_return_i)
     *
     * @param weights Asset allocation weights
     * @param meanReturns Mean return for each asset
     * @return Expected portfolio return
     */
    static double CalculatePortfolioReturn(
        const std::vector<double>& weights,
        const std::vector<double>& meanReturns
    );

    /**
     * Calculate portfolio volatility (risk)
     *
     * Portfolio Risk = √(w^T × Σ × w)
     * where w is weights vector and Σ is covariance matrix
     *
     * This accounts for diversification effects based on asset correlations.
     *
     * @param weights Asset allocation weights
     * @param covMatrix Covariance matrix of asset returns
     * @return Portfolio volatility (standard deviation)
     */
    static double CalculatePortfolioRisk(
        const std::vector<double>& weights,
        const std::vector<std::vector<double>>& covMatrix
    );

    /**
     * Calculate covariance matrix for multiple assets
     *
     * The covariance matrix Σ has:
     * - Variances on the diagonal (σ_i²)
     * - Covariances on off-diagonal (σ_i × σ_j × ρ_ij)
     *
     * @param assetReturns Vector of return series for each asset
     * @return Covariance matrix (n×n where n = number of assets)
     */
    static std::vector<std::vector<double>> CalculateCovarianceMatrix(
        const std::vector<std::vector<double>>& assetReturns
    );

    /**
     * Generate random portfolio weights that sum to 1.0
     *
     * Uses Dirichlet distribution for uniform sampling of simplex.
     *
     * @param numAssets Number of assets
     * @param rng Random number generator
     * @return Vector of weights summing to 1.0
     */
    static std::vector<double> GenerateRandomWeights(
        size_t numAssets,
        std::mt19937& rng
    );

private:
    /**
     * Validate that all asset return series have the same length
     */
    static void ValidateAssetReturns(
        const std::vector<std::vector<double>>& assetReturns
    );
};

#endif // PORTFOLIO_OPTIMIZER_H
