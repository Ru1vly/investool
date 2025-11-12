#ifndef ASSET_CLASSIFIER_H
#define ASSET_CLASSIFIER_H

#include <string>
#include <vector>

/**
 * Risk levels for asset classification
 */
enum class RiskLevel {
    VERY_LOW,      // 0% - 2% annual volatility
    LOW,           // 2% - 8% annual volatility
    MEDIUM,        // 8% - 20% annual volatility
    HIGH,          // 20% - 40% annual volatility
    VERY_HIGH      // 40%+ annual volatility (Speculation)
};

/**
 * Asset classification information
 */
struct AssetClass {
    RiskLevel riskLevel;
    double minVolatility;         // Minimum annual volatility (%)
    double maxVolatility;         // Maximum annual volatility (%)
    std::string description;      // Risk level description
    std::string typicalAssets;    // Examples of typical assets
    std::string returnExpectation; // Expected return level
    std::string riskOfLoss;       // Risk of principal loss
};

/**
 * AssetClassifier - Classifies assets based on volatility (risk)
 *
 * Based on general financial industry standards for asset classification.
 * These are approximations and can vary by market conditions and region.
 */
class AssetClassifier {
public:
    /**
     * Get all asset classifications
     * @return Vector of all asset class definitions
     */
    static std::vector<AssetClass> GetAllAssetClasses();

    /**
     * Classify an asset based on its annual volatility
     *
     * @param annualVolatility Annual volatility in decimal form (e.g., 0.15 for 15%)
     * @return AssetClass containing classification information
     */
    static AssetClass ClassifyByVolatility(double annualVolatility);

    /**
     * Get risk level name as string
     * @param level Risk level enum
     * @return String representation of risk level
     */
    static std::string GetRiskLevelName(RiskLevel level);

    /**
     * Get interpretation for a Sharpe Ratio value
     *
     * @param sharpeRatio The calculated Sharpe Ratio
     * @return Interpretation string
     */
    static std::string InterpretSharpeRatio(double sharpeRatio);

    /**
     * Get interpretation for a Beta value
     *
     * @param beta The calculated Beta
     * @return Interpretation string
     */
    static std::string InterpretBeta(double beta);

    /**
     * Print a formatted asset classification table
     */
    static void PrintAssetClassificationTable();
};

#endif // ASSET_CLASSIFIER_H
