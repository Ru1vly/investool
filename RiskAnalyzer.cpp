#include "RiskAnalyzer.h"

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
