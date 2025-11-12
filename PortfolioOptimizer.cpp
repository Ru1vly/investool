#include "PortfolioOptimizer.h"
#include "RiskAnalyzer.h"

EfficientFrontierResult PortfolioOptimizer::CalculateEfficientFrontier(
    const std::vector<std::vector<double>>& assetReturns,
    const std::vector<std::string>& assetNames,
    int numPortfolios,
    double riskFreeRate,
    unsigned int randomSeed) {

    // Validate inputs
    ValidateAssetReturns(assetReturns);

    if (assetReturns.size() != assetNames.size()) {
        throw std::invalid_argument("Number of asset names must match number of return series");
    }
    if (numPortfolios <= 0) {
        throw std::invalid_argument("Number of portfolios must be positive");
    }

    size_t numAssets = assetReturns.size();

    // Step 1: Calculate mean returns for each asset
    std::vector<double> meanReturns;
    for (const auto& returns : assetReturns) {
        double mean = RiskAnalyzer::CalculateMean(returns);
        meanReturns.push_back(mean);
    }

    // Step 2: Calculate covariance matrix
    std::vector<std::vector<double>> covMatrix = CalculateCovarianceMatrix(assetReturns);

    // Step 3: Initialize random number generator
    std::mt19937 rng;
    if (randomSeed == 0) {
        std::random_device rd;
        rng.seed(rd());
    } else {
        rng.seed(randomSeed);
    }

    // Step 4: Monte Carlo simulation
    std::vector<PortfolioResult> allSimulations;
    PortfolioResult optimalPortfolio;
    double maxSharpe = -999999.0;

    for (int i = 0; i < numPortfolios; ++i) {
        // A. Generate random weights
        std::vector<double> weights = GenerateRandomWeights(numAssets, rng);

        // B. Calculate portfolio return
        double portReturn = CalculatePortfolioReturn(weights, meanReturns);

        // C. Calculate portfolio risk
        double portRisk = CalculatePortfolioRisk(weights, covMatrix);

        // D. Calculate Sharpe Ratio
        double sharpe = (portRisk > 0) ? (portReturn - riskFreeRate) / portRisk : -999999.0;

        // E. Store result
        PortfolioResult result;
        result.portfolioReturn = portReturn;
        result.portfolioRisk = portRisk;
        result.sharpeRatio = sharpe;
        result.weights = weights;

        allSimulations.push_back(result);

        // F. Track optimal portfolio
        if (sharpe > maxSharpe) {
            maxSharpe = sharpe;
            optimalPortfolio = result;
        }
    }

    // Step 5: Return results
    EfficientFrontierResult frontierResult;
    frontierResult.optimalSharpePortfolio = optimalPortfolio;
    frontierResult.allSimulations = allSimulations;
    frontierResult.assetNames = assetNames;

    return frontierResult;
}

double PortfolioOptimizer::CalculatePortfolioReturn(
    const std::vector<double>& weights,
    const std::vector<double>& meanReturns) {

    if (weights.size() != meanReturns.size()) {
        throw std::invalid_argument("Weights and returns must have same size");
    }

    // Portfolio Return = Σ(weight_i × mean_return_i)
    double portfolioReturn = 0.0;
    for (size_t i = 0; i < weights.size(); ++i) {
        portfolioReturn += weights[i] * meanReturns[i];
    }

    return portfolioReturn;
}

double PortfolioOptimizer::CalculatePortfolioRisk(
    const std::vector<double>& weights,
    const std::vector<std::vector<double>>& covMatrix) {

    size_t n = weights.size();

    if (covMatrix.size() != n || covMatrix[0].size() != n) {
        throw std::invalid_argument("Covariance matrix dimensions must match weights size");
    }

    // Calculate portfolio variance: w^T × Σ × w
    // This is equivalent to: Σ_i Σ_j (w_i × w_j × Σ_ij)
    double variance = 0.0;

    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) {
            variance += weights[i] * weights[j] * covMatrix[i][j];
        }
    }

    // Portfolio risk = √variance
    return std::sqrt(variance);
}

std::vector<std::vector<double>> PortfolioOptimizer::CalculateCovarianceMatrix(
    const std::vector<std::vector<double>>& assetReturns) {

    ValidateAssetReturns(assetReturns);

    size_t numAssets = assetReturns.size();

    // Initialize covariance matrix (n × n)
    std::vector<std::vector<double>> covMatrix(numAssets, std::vector<double>(numAssets, 0.0));

    // Calculate covariance for each pair of assets
    for (size_t i = 0; i < numAssets; ++i) {
        for (size_t j = 0; j < numAssets; ++j) {
            if (i == j) {
                // Diagonal: variance of asset i
                covMatrix[i][j] = RiskAnalyzer::CalculateVariance(assetReturns[i]);
            } else {
                // Off-diagonal: covariance between assets i and j
                covMatrix[i][j] = RiskAnalyzer::CalculateCovariance(assetReturns[i], assetReturns[j]);
            }
        }
    }

    return covMatrix;
}

std::vector<double> PortfolioOptimizer::GenerateRandomWeights(
    size_t numAssets,
    std::mt19937& rng) {

    if (numAssets == 0) {
        throw std::invalid_argument("Number of assets must be positive");
    }

    // Generate random numbers from uniform distribution
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    std::vector<double> randomNumbers;
    double sum = 0.0;

    for (size_t i = 0; i < numAssets; ++i) {
        double r = dist(rng);
        randomNumbers.push_back(r);
        sum += r;
    }

    // Normalize so weights sum to 1.0
    std::vector<double> weights;
    for (double r : randomNumbers) {
        weights.push_back(r / sum);
    }

    return weights;
}

void PortfolioOptimizer::ValidateAssetReturns(
    const std::vector<std::vector<double>>& assetReturns) {

    if (assetReturns.empty()) {
        throw std::invalid_argument("Asset returns cannot be empty");
    }

    if (assetReturns.size() < 2) {
        throw std::invalid_argument("Need at least 2 assets for portfolio optimization");
    }

    size_t expectedLength = assetReturns[0].size();

    if (expectedLength < 2) {
        throw std::invalid_argument("Need at least 2 data points for each asset");
    }

    // Verify all return series have the same length
    for (size_t i = 1; i < assetReturns.size(); ++i) {
        if (assetReturns[i].size() != expectedLength) {
            throw std::invalid_argument("All asset return series must have the same length");
        }
    }
}
