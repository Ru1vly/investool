#include "AssetClassifier.h"
#include <iostream>
#include <iomanip>

std::vector<AssetClass> AssetClassifier::GetAllAssetClasses() {
    return {
        {
            RiskLevel::VERY_LOW,
            0.0,
            2.0,
            "Very Low Risk",
            "Savings Accounts, Government Bonds (DİBS)",
            "Low (Predictable)",
            "Almost None (Inflation risk exists)"
        },
        {
            RiskLevel::LOW,
            2.0,
            8.0,
            "Low Risk",
            "High-Grade Corporate Bonds, Gold (partially)",
            "Low-Medium",
            "Low"
        },
        {
            RiskLevel::MEDIUM,
            8.0,
            20.0,
            "Medium Risk",
            "Broad Market Index Funds (S&P 500, BIST 30), Blue-Chip Stocks",
            "Medium",
            "Medium (Loss is likely in short term)"
        },
        {
            RiskLevel::HIGH,
            20.0,
            40.0,
            "High Risk",
            "Growth Stocks (Tech), Silver, Emerging Market Stocks",
            "High",
            "High (Significant loss is possible)"
        },
        {
            RiskLevel::VERY_HIGH,
            40.0,
            999.0,  // No upper limit for speculation
            "Very High Risk (Speculation)",
            "Cryptocurrencies (BTC, ETH), Leveraged Instruments (Futures, Forex), Options, Altcoins",
            "Very High / Unlimited",
            "Very High / Total Loss Possible"
        }
    };
}

AssetClass AssetClassifier::ClassifyByVolatility(double annualVolatility) {
    // Convert to percentage for comparison
    double volPercent = annualVolatility * 100.0;

    auto classes = GetAllAssetClasses();

    for (const auto& assetClass : classes) {
        if (volPercent >= assetClass.minVolatility &&
            volPercent < assetClass.maxVolatility) {
            return assetClass;
        }
    }

    // If above all ranges, return VERY_HIGH
    return classes.back();
}

std::string AssetClassifier::GetRiskLevelName(RiskLevel level) {
    switch (level) {
        case RiskLevel::VERY_LOW:  return "Very Low Risk";
        case RiskLevel::LOW:       return "Low Risk";
        case RiskLevel::MEDIUM:    return "Medium Risk";
        case RiskLevel::HIGH:      return "High Risk";
        case RiskLevel::VERY_HIGH: return "Very High Risk (Speculation)";
        default:                   return "Unknown";
    }
}

std::string AssetClassifier::InterpretSharpeRatio(double sharpeRatio) {
    if (sharpeRatio < 1.0) {
        return "Poor - Risk is not worth it";
    } else if (sharpeRatio < 2.0) {
        return "Good - Adequately compensated for risk";
    } else {
        return "Excellent - Well compensated for risk";
    }
}

std::string AssetClassifier::InterpretBeta(double beta) {
    if (beta < 0) {
        return "Negative Beta - Moves opposite to market (rare, defensive)";
    } else if (beta == 0) {
        return "Zero Beta - No correlation with market";
    } else if (beta < 0.5) {
        return "Very Defensive - Much less volatile than market";
    } else if (beta < 1.0) {
        return "Defensive - Less volatile than market";
    } else if (beta == 1.0) {
        return "Neutral - Moves in line with market";
    } else if (beta < 1.5) {
        return "Aggressive - More volatile than market";
    } else {
        return "Very Aggressive - Much more volatile than market";
    }
}

void AssetClassifier::PrintAssetClassificationTable() {
    auto classes = GetAllAssetClasses();

    std::cout << "\n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "                        ASSET CLASSIFICATION BY VOLATILITY                              \n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << std::left;

    for (const auto& ac : classes) {
        std::cout << "\n";
        std::cout << "┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ " << std::setw(84) << ac.description << "│\n";
        std::cout << "├─────────────────────────────────────────────────────────────────────────────────────┤\n";

        std::string volRange = std::to_string(static_cast<int>(ac.minVolatility)) + "% - " +
                               (ac.maxVolatility >= 999.0 ? "∞" : std::to_string(static_cast<int>(ac.maxVolatility)) + "%");
        std::cout << "│ Annual Volatility (σ): " << std::setw(61) << volRange << "│\n";
        std::cout << "│ Typical Assets:        " << std::setw(61) << ac.typicalAssets << "│\n";
        std::cout << "│ Return Expectation:    " << std::setw(61) << ac.returnExpectation << "│\n";
        std::cout << "│ Risk of Loss:          " << std::setw(61) << ac.riskOfLoss << "│\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    }

    std::cout << "\n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "NOTE: Past volatility does NOT predict future volatility.\n";
    std::cout << "      These classifications are approximations based on historical patterns.\n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "\n";
}
