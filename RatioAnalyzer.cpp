#include "RatioAnalyzer.h"
#include "RiskAnalyzer.h"
#include <cmath>
#include <sstream>
#include <iomanip>

RatioAnalysisResult RatioAnalyzer::AnalyzeRatio(
    const std::vector<double>& pricesA,
    const std::vector<double>& pricesB,
    const std::string& assetNameA,
    const std::string& assetNameB) {

    // Validate inputs
    ValidatePrices(pricesA, pricesB);

    // Step 1: Calculate historical ratio series
    std::vector<double> ratioHistory = CalculateRatioSeries(pricesA, pricesB);

    // Step 2: Get current ratio (most recent)
    double currentRatio = ratioHistory.back();

    // Step 3: Calculate historical statistics
    double historicalMean = RiskAnalyzer::CalculateMean(ratioHistory);
    double historicalStdDev = RiskAnalyzer::CalculateVolatility(ratioHistory);

    // Step 4: Calculate Z-Score
    double zScore = RiskAnalyzer::CalculateZScore(currentRatio, ratioHistory);

    // Step 5: Generate signals
    std::string signal = GenerateSignal(zScore, assetNameA, assetNameB);
    std::string interpretation = InterpretZScore(zScore);

    // Step 6: Package results
    RatioAnalysisResult result;
    result.currentRatio = currentRatio;
    result.historicalMean = historicalMean;
    result.historicalStdDev = historicalStdDev;
    result.zScore = zScore;
    result.signal = signal;
    result.interpretation = interpretation;

    return result;
}

std::vector<double> RatioAnalyzer::CalculateRatioSeries(
    const std::vector<double>& pricesA,
    const std::vector<double>& pricesB) {

    ValidatePrices(pricesA, pricesB);

    std::vector<double> ratios;

    for (size_t i = 0; i < pricesA.size(); ++i) {
        if (pricesB[i] == 0) {
            throw std::invalid_argument("Asset B price cannot be zero (division by zero)");
        }
        double ratio = pricesA[i] / pricesB[i];
        ratios.push_back(ratio);
    }

    return ratios;
}

std::string RatioAnalyzer::GenerateSignal(
    double zScore,
    const std::string& assetNameA,
    const std::string& assetNameB) {

    std::ostringstream signal;

    if (zScore > 2.0) {
        // Asset A is EXTREMELY expensive relative to B
        signal << "STRONG SIGNAL: " << assetNameA << " is extremely expensive relative to "
               << assetNameB << std::fixed << std::setprecision(2)
               << " (Z=" << zScore << ", >2σ above mean)";
        signal << "\nConsider: SELL " << assetNameA << " or BUY " << assetNameB;

    } else if (zScore > 1.0) {
        // Asset A is expensive relative to B
        signal << "SIGNAL: " << assetNameA << " is expensive relative to "
               << assetNameB << std::fixed << std::setprecision(2)
               << " (Z=" << zScore << ", >1σ above mean)";
        signal << "\nModerate opportunity for mean reversion";

    } else if (zScore < -2.0) {
        // Asset A is EXTREMELY cheap relative to B
        signal << "STRONG SIGNAL: " << assetNameA << " is extremely cheap relative to "
               << assetNameB << std::fixed << std::setprecision(2)
               << " (Z=" << zScore << ", >2σ below mean)";
        signal << "\nConsider: BUY " << assetNameA << " or SELL " << assetNameB;

    } else if (zScore < -1.0) {
        // Asset A is cheap relative to B
        signal << "SIGNAL: " << assetNameA << " is cheap relative to "
               << assetNameB << std::fixed << std::setprecision(2)
               << " (Z=" << zScore << ", >1σ below mean)";
        signal << "\nModerate opportunity for mean reversion";

    } else {
        // Within normal range
        signal << "NO SIGNAL: Ratio is within normal historical range"
               << std::fixed << std::setprecision(2)
               << " (Z=" << zScore << ")";
        signal << "\nNo actionable mean reversion opportunity";
    }

    return signal.str();
}

std::string RatioAnalyzer::InterpretZScore(double zScore) {
    double absZ = std::abs(zScore);

    std::ostringstream interpretation;
    interpretation << std::fixed << std::setprecision(2);

    if (absZ < 1.0) {
        interpretation << "Within normal range (|Z| < 1.0)";
        interpretation << "\nThe ratio is within 1 standard deviation of its historical mean.";
        interpretation << "\nThis is expected normal variation (~68% of the time).";

    } else if (absZ < 2.0) {
        interpretation << "Moderate deviation (1.0 ≤ |Z| < 2.0)";
        interpretation << "\nThe ratio is between 1-2 standard deviations from the mean.";
        interpretation << "\nThis is somewhat unusual (~27% of the time).";
        interpretation << "\nModerate mean reversion opportunity.";

    } else if (absZ < 3.0) {
        interpretation << "Significant deviation (2.0 ≤ |Z| < 3.0)";
        interpretation << "\nThe ratio is between 2-3 standard deviations from the mean.";
        interpretation << "\nThis is rare (~4.3% of the time).";
        interpretation << "\nStrong mean reversion opportunity, if historical relationship holds.";

    } else {
        interpretation << "EXTREME deviation (|Z| ≥ 3.0)";
        interpretation << "\nThe ratio is more than 3 standard deviations from the mean.";
        interpretation << "\nThis is VERY rare (~0.3% of the time).";
        interpretation << "\nEither: (1) Exceptional mean reversion opportunity, or";
        interpretation << "\n        (2) Fundamental relationship has changed permanently.";
        interpretation << "\nCaution: 'This time is different' can sometimes be true.";
    }

    if (zScore > 0) {
        interpretation << "\n\nDirection: Ratio is ABOVE historical average";
    } else {
        interpretation << "\n\nDirection: Ratio is BELOW historical average";
    }

    return interpretation.str();
}

bool RatioAnalyzer::IsWithinNormalRange(double zScore) {
    return std::abs(zScore) < 1.0;
}

bool RatioAnalyzer::IsExtremeDeviation(double zScore) {
    return std::abs(zScore) >= 2.0;
}

void RatioAnalyzer::ValidatePrices(
    const std::vector<double>& pricesA,
    const std::vector<double>& pricesB) {

    if (pricesA.empty() || pricesB.empty()) {
        throw std::invalid_argument("Price vectors cannot be empty");
    }

    if (pricesA.size() != pricesB.size()) {
        throw std::invalid_argument("Price vectors must have the same length");
    }

    if (pricesA.size() < 2) {
        throw std::invalid_argument("Need at least 2 data points for ratio analysis");
    }

    // Check for non-positive prices
    for (double price : pricesA) {
        if (price <= 0) {
            throw std::invalid_argument("All prices for asset A must be positive");
        }
    }

    for (double price : pricesB) {
        if (price <= 0) {
            throw std::invalid_argument("All prices for asset B must be positive");
        }
    }
}
