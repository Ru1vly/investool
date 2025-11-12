#include <iostream>
#include <iomanip>
#include <vector>
#include "FinancialCalculator.h"
#include "RiskAnalyzer.h"
#include "AssetClassifier.h"

void printSectionHeader(const std::string& title) {
    std::cout << "\n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "  " << title << "\n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
}

void demonstrateFutureValueCalculations() {
    printSectionHeader("FUTURE VALUE OF ANNUITY - Dollar Cost Averaging (DCA) Analysis");

    std::cout << "\nScenario: You want to reach 200,000 TL in 7 months\n";
    std::cout << "You are considering a high-risk investment with 12% monthly return\n";

    double targetFV = 200000.0;
    double monthlyPayment = 20000.0;
    double annualRate = 0.12;  // 12% annual
    double monthlyRate = FinancialCalculator::AnnualToMonthlyRate(annualRate);
    int periods = 7;

    std::cout << std::fixed << std::setprecision(2);

    // Formula 1: Calculate FV given PMT
    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ FORMULA 1: Future Value Calculation                                                  │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  Given:   PMT = " << monthlyPayment << " TL/month\n";
    std::cout << "           Interest Rate = " << (annualRate * 100) << "% annual (" << (monthlyRate * 100) << "% monthly)\n";
    std::cout << "           Periods = " << periods << " months\n";

    try {
        double fv = FinancialCalculator::CalculateFutureValue(monthlyPayment, monthlyRate, periods);
        std::cout << "  Result:  FV = " << fv << " TL\n";
        std::cout << "  ⚠ WARNING: You would only reach " << fv << " TL, falling short by " << (targetFV - fv) << " TL\n";
    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }

    // Formula 2: Calculate required PMT
    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ FORMULA 2: Required Payment Calculation                                              │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  Given:   FV = " << targetFV << " TL (target)\n";
    std::cout << "           Interest Rate = " << (annualRate * 100) << "% annual\n";
    std::cout << "           Periods = " << periods << " months\n";

    try {
        double requiredPMT = FinancialCalculator::CalculateRequiredPayment(targetFV, monthlyRate, periods);
        std::cout << "  Result:  Required PMT = " << requiredPMT << " TL/month\n";
        std::cout << "  Analysis: You would need to invest " << requiredPMT << " TL per month\n";
        std::cout << "            (vs your current " << monthlyPayment << " TL/month)\n";
    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }

    // Formula 3: Calculate required periods
    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ FORMULA 3: Required Time Period Calculation                                          │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  Given:   FV = " << targetFV << " TL (target)\n";
    std::cout << "           PMT = " << monthlyPayment << " TL/month\n";
    std::cout << "           Interest Rate = " << (annualRate * 100) << "% annual\n";

    try {
        double requiredPeriods = FinancialCalculator::CalculateRequiredPeriods(targetFV, monthlyPayment, monthlyRate);
        std::cout << "  Result:  Required Periods = " << requiredPeriods << " months\n";
        std::cout << "  Analysis: You would need " << requiredPeriods << " months to reach your goal\n";
        std::cout << "            (vs your target of " << periods << " months)\n";
    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }

    std::cout << "\n⚠ CRITICAL WARNING:\n";
    std::cout << "  These calculations assume a CONSTANT " << (monthlyRate * 100) << "% monthly return.\n";
    std::cout << "  This is EXTREMELY unrealistic in real markets!\n";
    std::cout << "  Use for planning purposes ONLY, not as predictions.\n";
}

void demonstrateRiskAnalysis() {
    printSectionHeader("RISK ANALYSIS - Volatility and Risk Metrics");

    // Example: Historical monthly returns for a volatile asset (e.g., cryptocurrency)
    std::cout << "\nExample Asset: Cryptocurrency (e.g., Bitcoin)\n";
    std::cout << "Historical Monthly Returns (hypothetical):\n";

    std::vector<double> cryptoReturns = {0.15, -0.20, 0.30, -0.10, 0.25, -0.15, 0.20, -0.05, 0.10, 0.05, -0.25, 0.35};

    std::cout << "  [";
    for (size_t i = 0; i < cryptoReturns.size(); ++i) {
        std::cout << std::fixed << std::setprecision(1) << (cryptoReturns[i] * 100) << "%";
        if (i < cryptoReturns.size() - 1) std::cout << ", ";
    }
    std::cout << "]\n";

    // Calculate statistics
    double mean = RiskAnalyzer::CalculateMean(cryptoReturns);
    double variance = RiskAnalyzer::CalculateVariance(cryptoReturns);
    double monthlyVol = RiskAnalyzer::CalculateVolatility(cryptoReturns);
    double annualVol = RiskAnalyzer::MonthlyToAnnualVolatility(monthlyVol);

    std::cout << std::fixed << std::setprecision(4);

    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ FORMULA 4 & 5: Variance and Volatility (Standard Deviation)                         │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  Average Return:      " << (mean * 100) << "%/month\n";
    std::cout << "  Variance (σ²):       " << variance << "\n";
    std::cout << "  Monthly Volatility:  " << (monthlyVol * 100) << "%\n";
    std::cout << "  Annual Volatility:   " << (annualVol * 100) << "%\n";

    // Classify the asset
    AssetClass classification = AssetClassifier::ClassifyByVolatility(annualVol);
    std::cout << "\n  Asset Classification: " << classification.description << "\n";
    std::cout << "  Risk Assessment:      " << classification.riskOfLoss << "\n";

    // Sharpe Ratio
    double riskFreeRate = 0.005;  // 0.5% monthly (6% annual)
    double sharpeRatio = RiskAnalyzer::CalculateSharpeRatio(cryptoReturns, riskFreeRate);

    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ FORMULA 6: Sharpe Ratio - Risk-Adjusted Return                                      │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  Portfolio Return:    " << (mean * 100) << "%/month\n";
    std::cout << "  Risk-Free Rate:      " << (riskFreeRate * 100) << "%/month\n";
    std::cout << "  Volatility:          " << (monthlyVol * 100) << "%\n";
    std::cout << "  Sharpe Ratio:        " << sharpeRatio << "\n";
    std::cout << "  Interpretation:      " << AssetClassifier::InterpretSharpeRatio(sharpeRatio) << "\n";

    // Beta calculation
    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ FORMULA 7: Beta - Market Correlation                                                │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";

    // Market returns (e.g., S&P 500)
    std::vector<double> marketReturns = {0.02, -0.01, 0.03, -0.02, 0.04, 0.01, 0.02, -0.01, 0.03, 0.02, -0.03, 0.04};

    std::cout << "  Market Returns (S&P 500): [";
    for (size_t i = 0; i < marketReturns.size(); ++i) {
        std::cout << std::fixed << std::setprecision(1) << (marketReturns[i] * 100) << "%";
        if (i < marketReturns.size() - 1) std::cout << ", ";
    }
    std::cout << "]\n";

    double beta = RiskAnalyzer::CalculateBeta(cryptoReturns, marketReturns);
    std::cout << std::fixed << std::setprecision(4);
    std::cout << "  Beta (β):            " << beta << "\n";
    std::cout << "  Interpretation:      " << AssetClassifier::InterpretBeta(beta) << "\n";

    std::cout << "\n⚠ CRITICAL LIMITATION:\n";
    std::cout << "  These metrics measure PAST behavior, NOT future performance.\n";
    std::cout << "  'Black Swan' events can make all historical data irrelevant.\n";
    std::cout << "  Volatility and Beta are NOT constant - they change over time.\n";
}

void demonstrateAssetClassification() {
    printSectionHeader("ASSET CLASSIFICATION BY RISK LEVEL");
    AssetClassifier::PrintAssetClassificationTable();
}

void demonstrateBlackSwanWarning() {
    printSectionHeader("CRITICAL LIMITATION: MATHEMATICAL ACCURACY vs PREDICTIVE POWER");

    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ Mathematical Accuracy: 100%                                                          │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  All formulas in this tool are mathematically correct.\n";
    std::cout << "  If you provide inputs, the calculations will be accurate.\n";
    std::cout << "  2 + 2 will always equal 4.\n";

    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ Predictive Power (Validity): EXTREMELY LOW                                           │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  These models CANNOT predict the future for the following reasons:\n";
    std::cout << "\n";
    std::cout << "  1. PAST PERFORMANCE ≠ FUTURE RESULTS\n";
    std::cout << "     - All inputs (returns, volatility, beta) are based on historical data\n";
    std::cout << "     - Markets change; what happened before won't necessarily repeat\n";
    std::cout << "\n";
    std::cout << "  2. BLACK SWAN EVENTS (Nassim Nicholas Taleb)\n";
    std::cout << "     - Unpredictable, high-impact events:\n";
    std::cout << "       * COVID-19 pandemic (2020)\n";
    std::cout << "       * Global financial crisis (2008)\n";
    std::cout << "       * Wars, political upheavals, technological disruptions\n";
    std::cout << "     - These events make historical data irrelevant\n";
    std::cout << "\n";
    std::cout << "  3. CHANGING INPUTS\n";
    std::cout << "     - Volatility (σ) is NOT fixed\n";
    std::cout << "     - Returns (i) are NOT constant\n";
    std::cout << "     - They change based on:\n";
    std::cout << "       * New information\n";
    std::cout << "       * Economic policy changes\n";
    std::cout << "       * Market psychology\n";
    std::cout << "       * Regulatory changes\n";

    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ CORRECT USE OF THIS TOOL                                                             │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  ✓ Risk Analysis:      \"What risk level does this asset fall into?\"\n";
    std::cout << "  ✓ Reality Check:      \"Is a 12% monthly return realistic?\"\n";
    std::cout << "  ✓ Requirement Analysis: \"What would I need to reach my goal?\"\n";
    std::cout << "\n";
    std::cout << "  ✗ Prediction:         \"I will definitely reach 200,000 TL in 7 months\"\n";
    std::cout << "  ✗ Guarantee:          \"This asset will return 15% next month\"\n";
    std::cout << "  ✗ Future Planning:    \"Volatility will stay at 20% forever\"\n";

    std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
    std::cout << "│ SOURCES                                                                              │\n";
    std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
    std::cout << "  • Future Value Formulas: Corporate Finance Institute (CFI), Finance textbooks\n";
    std::cout << "  • Standard Deviation, Beta, Sharpe Ratio: Modern Portfolio Theory (MPT)\n";
    std::cout << "    - Widely documented by Investopedia\n";
    std::cout << "    - Sharpe Ratio: William F. Sharpe (Nobel Prize winner)\n";
    std::cout << "  • Black Swan Theory: Nassim Nicholas Taleb\n";
    std::cout << "    - \"The Black Swan: The Impact of the Highly Improbable\" (2007)\n";
    std::cout << "    - \"Antifragile: Things That Gain from Disorder\" (2012)\n";

    std::cout << "\n";
}

int main(int argc, char* argv[]) {
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "                                    INVESTOOL                                          \n";
    std::cout << "                 Financial Goal Setting and Risk Analysis Framework                    \n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "\n";
    std::cout << "This tool implements standard financial equations for:\n";
    std::cout << "  • Future Value calculations (DCA strategy analysis)\n";
    std::cout << "  • Risk measurement (Volatility, Variance)\n";
    std::cout << "  • Risk-adjusted performance (Sharpe Ratio, Beta)\n";
    std::cout << "  • Asset classification by risk level\n";
    std::cout << "\n";
    std::cout << "⚠ WARNING: These tools analyze PAST data. They do NOT predict the future!\n";
    std::cout << "           Past performance is not a guarantee of future results.\n";
    std::cout << "\n";

    // Run demonstrations
    demonstrateFutureValueCalculations();
    demonstrateRiskAnalysis();
    demonstrateAssetClassification();
    demonstrateBlackSwanWarning();

    std::cout << "\n═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "                              END OF ANALYSIS                                          \n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "\n";

    return 0;
}
