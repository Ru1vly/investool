#include "RiskAnalyzer.h"
#include <algorithm>

double RiskAnalyzer::CalculateMean(const std::vector<double>& returns) {
    if (returns.empty()) {
        throw std::invalid_argument("Returns vector cannot be empty");
    }

    double sum = std::accumulate(returns.begin(), returns.end(), 0.0);
    return sum / returns.size();
}

double RiskAnalyzer::CalculateVariance(const std::vector<double>& returns) {
    if (returns.size() < 2) {
        throw std::invalid_argument("Need at least 2 data points for variance");
    }

    // Calculate mean
    double mean = CalculateMean(returns);

    // Calculate sum of squared deviations
    double sumSquaredDev = 0.0;
    for (double r : returns) {
        double deviation = r - mean;
        sumSquaredDev += deviation * deviation;
    }

    // Divide by (N - 1) for sample variance (Bessel's correction)
    return sumSquaredDev / (returns.size() - 1);
}

double RiskAnalyzer::CalculateVolatility(const std::vector<double>& returns) {
    // Volatility = √Variance
    return std::sqrt(CalculateVariance(returns));
}

double RiskAnalyzer::CalculateSharpeRatio(double portfolioReturn,
                                          double riskFreeRate,
                                          double portfolioVolatility) {
    if (portfolioVolatility <= 0) {
        throw std::invalid_argument("Volatility must be positive");
    }

    // Sharpe = (R_p - R_f) / σ_p
    return (portfolioReturn - riskFreeRate) / portfolioVolatility;
}

double RiskAnalyzer::CalculateSharpeRatio(const std::vector<double>& returns,
                                          double riskFreeRate) {
    if (returns.empty()) {
        throw std::invalid_argument("Returns vector cannot be empty");
    }

    double avgReturn = CalculateMean(returns);
    double volatility = CalculateVolatility(returns);

    return CalculateSharpeRatio(avgReturn, riskFreeRate, volatility);
}

double RiskAnalyzer::CalculateCovariance(const std::vector<double>& returns1,
                                         const std::vector<double>& returns2) {
    if (returns1.size() != returns2.size()) {
        throw std::invalid_argument("Return series must have same length");
    }
    if (returns1.size() < 2) {
        throw std::invalid_argument("Need at least 2 data points for covariance");
    }

    double mean1 = CalculateMean(returns1);
    double mean2 = CalculateMean(returns2);

    double sumProduct = 0.0;
    for (size_t i = 0; i < returns1.size(); ++i) {
        sumProduct += (returns1[i] - mean1) * (returns2[i] - mean2);
    }

    // Divide by (N - 1) for sample covariance
    return sumProduct / (returns1.size() - 1);
}

double RiskAnalyzer::CalculateBeta(const std::vector<double>& assetReturns,
                                   const std::vector<double>& marketReturns) {
    if (assetReturns.size() != marketReturns.size()) {
        throw std::invalid_argument("Asset and market returns must have same length");
    }

    // β = Cov(Asset, Market) / Var(Market)
    double covariance = CalculateCovariance(assetReturns, marketReturns);
    double marketVariance = CalculateVariance(marketReturns);

    if (marketVariance == 0) {
        throw std::invalid_argument("Market variance cannot be zero");
    }

    return covariance / marketVariance;
}

double RiskAnalyzer::DailyToAnnualVolatility(double dailyVolatility) {
    // 252 trading days per year (approximate)
    return dailyVolatility * std::sqrt(252.0);
}

double RiskAnalyzer::MonthlyToAnnualVolatility(double monthlyVolatility) {
    // 12 months per year
    return monthlyVolatility * std::sqrt(12.0);
}

double RiskAnalyzer::CalculateCorrelation(const std::vector<double>& returns1,
                                          const std::vector<double>& returns2) {
    if (returns1.size() != returns2.size()) {
        throw std::invalid_argument("Return series must have same length");
    }
    if (returns1.size() < 2) {
        throw std::invalid_argument("Need at least 2 data points for correlation");
    }

    // ρ = Cov(A, B) / (σ_A × σ_B)
    double covariance = CalculateCovariance(returns1, returns2);
    double sigma1 = CalculateVolatility(returns1);
    double sigma2 = CalculateVolatility(returns2);

    if (sigma1 == 0 || sigma2 == 0) {
        throw std::invalid_argument("Standard deviation cannot be zero");
    }

    return covariance / (sigma1 * sigma2);
}

double RiskAnalyzer::CalculatePortfolioVolatility(double weight1, double sigma1,
                                                  double weight2, double sigma2,
                                                  double correlation) {
    if (weight1 < 0 || weight2 < 0 || sigma1 < 0 || sigma2 < 0) {
        throw std::invalid_argument("Weights and volatilities must be non-negative");
    }
    if (std::abs((weight1 + weight2) - 1.0) > 0.001) {
        throw std::invalid_argument("Weights must sum to 1.0");
    }
    if (correlation < -1.0 || correlation > 1.0) {
        throw std::invalid_argument("Correlation must be between -1 and 1");
    }

    // σ_p = √[w_A² × σ_A² + w_B² × σ_B² + 2 × w_A × w_B × ρ_AB × σ_A × σ_B]
    double variance = std::pow(weight1, 2) * std::pow(sigma1, 2) +
                      std::pow(weight2, 2) * std::pow(sigma2, 2) +
                      2 * weight1 * weight2 * correlation * sigma1 * sigma2;

    return std::sqrt(variance);
}

double RiskAnalyzer::CalculateDownsideDeviation(const std::vector<double>& returns,
                                                double MARR) {
    if (returns.empty()) {
        throw std::invalid_argument("Returns vector cannot be empty");
    }

    // Calculate sum of squared downside deviations
    double sumSquared = 0.0;
    for (double r : returns) {
        double diff = r - MARR;
        if (diff < 0) {
            // Only count returns below MARR
            sumSquared += diff * diff;
        }
        // Otherwise, count as 0 (ignore upside volatility)
    }

    // Downside deviation = √(average of squared downside deviations)
    double meanSquared = sumSquared / returns.size();
    return std::sqrt(meanSquared);
}

double RiskAnalyzer::CalculateSortinoRatio(const std::vector<double>& returns,
                                           double riskFreeRate,
                                           double MARR) {
    if (returns.empty()) {
        throw std::invalid_argument("Returns vector cannot be empty");
    }

    // If MARR not specified, use risk-free rate
    if (MARR == -999.0) {
        MARR = riskFreeRate;
    }

    double avgReturn = CalculateMean(returns);
    double downsideDeviation = CalculateDownsideDeviation(returns, MARR);

    if (downsideDeviation == 0) {
        throw std::invalid_argument("Downside deviation cannot be zero");
    }

    // Sortino = (R_p - R_f) / σ_d
    return (avgReturn - riskFreeRate) / downsideDeviation;
}

double RiskAnalyzer::CalculateVaR(double portfolioValue,
                                  double volatility,
                                  double confidenceLevel,
                                  double expectedReturn) {
    if (portfolioValue <= 0) {
        throw std::invalid_argument("Portfolio value must be positive");
    }
    if (volatility < 0) {
        throw std::invalid_argument("Volatility must be non-negative");
    }

    // Map confidence level to Z-score
    double Z;
    if (std::abs(confidenceLevel - 0.90) < 0.001) {
        Z = 1.282;
    } else if (std::abs(confidenceLevel - 0.95) < 0.001) {
        Z = 1.645;
    } else if (std::abs(confidenceLevel - 0.99) < 0.001) {
        Z = 2.326;
    } else {
        throw std::invalid_argument("Confidence level must be 0.90, 0.95, or 0.99");
    }

    // VaR = |μ - Z × σ|
    double varPercentage = std::abs(expectedReturn - Z * volatility);
    return portfolioValue * varPercentage;
}

double RiskAnalyzer::CalculateHistoricalVaR(const std::vector<double>& returns,
                                            double portfolioValue,
                                            double confidenceLevel) {
    if (returns.empty()) {
        throw std::invalid_argument("Returns vector cannot be empty");
    }
    if (portfolioValue <= 0) {
        throw std::invalid_argument("Portfolio value must be positive");
    }
    if (confidenceLevel <= 0 || confidenceLevel >= 1.0) {
        throw std::invalid_argument("Confidence level must be between 0 and 1");
    }

    // Sort returns from worst to best
    std::vector<double> sortedReturns = returns;
    std::sort(sortedReturns.begin(), sortedReturns.end());

    // Find the return at the (1 - confidence_level) percentile
    double lossPercentile = 1.0 - confidenceLevel;
    size_t cutoffIndex = static_cast<size_t>(std::ceil(sortedReturns.size() * lossPercentile));

    // Ensure index is within bounds
    if (cutoffIndex >= sortedReturns.size()) {
        cutoffIndex = sortedReturns.size() - 1;
    }

    // Get the return at this percentile (this will be negative for losses)
    double varPercent = sortedReturns[cutoffIndex];

    // Convert to dollar amount (absolute value)
    return std::abs(varPercent) * portfolioValue;
}

double RiskAnalyzer::CalculateZScore(double currentValue,
                                     const std::vector<double>& historicalData) {
    if (historicalData.empty()) {
        throw std::invalid_argument("Historical data cannot be empty");
    }

    double mean = CalculateMean(historicalData);
    double sigma = CalculateVolatility(historicalData);

    if (sigma == 0) {
        throw std::invalid_argument("Standard deviation cannot be zero");
    }

    // Z = (x - μ) / σ
    return (currentValue - mean) / sigma;
}
