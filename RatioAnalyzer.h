#ifndef RATIO_ANALYZER_H
#define RATIO_ANALYZER_H

#include <vector>
#include <string>
#include <stdexcept>

/**
 * Structure representing ratio analysis results
 */
struct RatioAnalysisResult {
    double currentRatio;          // Current observed ratio
    double historicalMean;        // Historical average of the ratio
    double historicalStdDev;      // Historical standard deviation
    double zScore;                // Z-Score of current ratio
    std::string signal;           // Interpretation/signal
    std::string interpretation;   // Detailed interpretation
};

/**
 * RatioAnalyzer - Analyzes ratios between two assets using Z-Score
 *
 * Identifies when one asset is historically cheap or expensive relative
 * to another, which can signal mean reversion opportunities.
 *
 * Common uses:
 * - Gold/Silver Ratio
 * - Stock pairs trading
 * - P/E Ratios vs historical average
 * - Currency pairs
 * - Commodity spreads
 *
 * WARNING: Mean reversion is NOT guaranteed. Historical relationships can
 * break down due to:
 * - Structural changes in markets
 * - New technologies or regulations
 * - Changes in supply/demand fundamentals
 * - "This time is different" can sometimes be true
 *
 * Use for relative value analysis, not absolute predictions.
 */
class RatioAnalyzer {
public:
    /**
     * Analyze ratio between two assets using Z-Score
     *
     * Calculates the historical ratio between two assets, determines
     * the Z-Score of the current ratio, and provides trading signals
     * based on mean reversion principles.
     *
     * Algorithm:
     * 1. Calculate historical ratio: price_A[i] / price_B[i] for each period
     * 2. Calculate mean and standard deviation of historical ratios
     * 3. Calculate Z-Score: (current_ratio - mean) / std_dev
     * 4. Generate signal based on Z-Score thresholds
     *
     * @param pricesA Historical prices for asset A (numerator)
     * @param pricesB Historical prices for asset B (denominator)
     * @param assetNameA Name of asset A (e.g., "Gold")
     * @param assetNameB Name of asset B (e.g., "Silver")
     * @return RatioAnalysisResult with statistics and signals
     */
    static RatioAnalysisResult AnalyzeRatio(
        const std::vector<double>& pricesA,
        const std::vector<double>& pricesB,
        const std::string& assetNameA,
        const std::string& assetNameB
    );

    /**
     * Calculate historical ratio series
     *
     * @param pricesA Prices for asset A
     * @param pricesB Prices for asset B
     * @return Vector of ratios (A/B) for each time period
     */
    static std::vector<double> CalculateRatioSeries(
        const std::vector<double>& pricesA,
        const std::vector<double>& pricesB
    );

    /**
     * Generate trading signal from Z-Score
     *
     * Thresholds:
     * - Z > 2.0: Asset A extremely expensive relative to B (SELL A, BUY B)
     * - Z > 1.0: Asset A expensive relative to B
     * - -1.0 < Z < 1.0: Normal range (HOLD)
     * - Z < -1.0: Asset A cheap relative to B
     * - Z < -2.0: Asset A extremely cheap relative to B (BUY A, SELL B)
     *
     * @param zScore Z-Score value
     * @param assetNameA Name of asset A
     * @param assetNameB Name of asset B
     * @return Trading signal string
     */
    static std::string GenerateSignal(
        double zScore,
        const std::string& assetNameA,
        const std::string& assetNameB
    );

    /**
     * Generate detailed interpretation of Z-Score
     *
     * @param zScore Z-Score value
     * @return Interpretation string
     */
    static std::string InterpretZScore(double zScore);

    /**
     * Check if ratio is within normal range
     *
     * @param zScore Z-Score value
     * @return True if |Z| < 1.0 (within normal range)
     */
    static bool IsWithinNormalRange(double zScore);

    /**
     * Check if ratio shows extreme deviation
     *
     * @param zScore Z-Score value
     * @return True if |Z| >= 2.0 (extreme deviation)
     */
    static bool IsExtremeDeviation(double zScore);

private:
    /**
     * Validate that price vectors are valid and aligned
     */
    static void ValidatePrices(
        const std::vector<double>& pricesA,
        const std::vector<double>& pricesB
    );
};

#endif // RATIO_ANALYZER_H
