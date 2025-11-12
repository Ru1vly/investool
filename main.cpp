#include <iostream>
#include <iomanip>
#include <vector>
#include <cmath>
#include "FinancialCalculator.h"
#include "RiskAnalyzer.h"
#include "AssetClassifier.h"
#include "PortfolioOptimizer.h"
#include "StrategyBacktester.h"
#include "RatioAnalyzer.h"

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

void demonstrateAdvancedRiskMetrics() {
    printSectionHeader("PREMIUM FEATURE 2: ADVANCED RISK METRICS (Sortino & VaR)");

    std::cout << "\nThis demonstration shows advanced risk measurement beyond standard volatility.\n";
    std::cout << "Sortino Ratio: Only penalizes downside risk (better than Sharpe for asymmetric returns)\n";
    std::cout << "Value at Risk: Quantifies maximum expected loss at a confidence level\n";

    // Hypothetical portfolio returns (monthly)
    std::vector<double> portfolioReturns = {
        0.08, -0.15, 0.12, 0.05, -0.08, 0.15, 0.02, -0.20, 0.18, 0.10, -0.05, 0.07
    };

    std::cout << "\nHypothetical Portfolio Returns (12 months):\n  [";
    for (size_t i = 0; i < portfolioReturns.size(); ++i) {
        std::cout << std::fixed << std::setprecision(1) << (portfolioReturns[i] * 100) << "%";
        if (i < portfolioReturns.size() - 1) std::cout << ", ";
    }
    std::cout << "]\n";

    std::cout << std::fixed << std::setprecision(4);

    // Calculate traditional metrics for comparison
    double avgReturn = RiskAnalyzer::CalculateMean(portfolioReturns);
    double volatility = RiskAnalyzer::CalculateVolatility(portfolioReturns);
    double riskFreeRate = 0.02;  // 2% per period

    try {
        // Sharpe Ratio (traditional)
        double sharpe = RiskAnalyzer::CalculateSharpeRatio(portfolioReturns, riskFreeRate);

        // Sortino Ratio (advanced)
        double sortino = RiskAnalyzer::CalculateSortinoRatio(portfolioReturns, riskFreeRate);

        // Downside Deviation
        double downsideDev = RiskAnalyzer::CalculateDownsideDeviation(portfolioReturns, 0.0);

        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ FORMULA 10-11: SORTINO RATIO (Downside Risk Only)                                   │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
        std::cout << "  Average Return:        " << std::setprecision(2) << (avgReturn * 100) << "%\n";
        std::cout << "  Risk-Free Rate:        " << (riskFreeRate * 100) << "%\n";
        std::cout << "  \n";
        std::cout << "  Total Volatility (σ):  " << std::setprecision(2) << (volatility * 100) << "%\n";
        std::cout << "  Downside Deviation:    " << (downsideDev * 100) << "% (only negative returns)\n";
        std::cout << "  \n";
        std::cout << "  Sharpe Ratio:          " << std::setprecision(3) << sharpe << "\n";
        std::cout << "  Sortino Ratio:         " << sortino << " (" << std::setprecision(1)
                  << ((sortino / sharpe - 1.0) * 100) << "% better)\n";
        std::cout << "  \n";
        std::cout << "  Interpretation: " << AssetClassifier::InterpretSharpeRatio(sortino) << "\n";
        std::cout << "  \n";
        std::cout << "  Why Sortino > Sharpe? It ignores 'good' upside volatility!\n";

    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }

    // Value at Risk calculation
    double portfolioValue = 200000.0;  // $200,000 portfolio

    try {
        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ FORMULA 12: VALUE AT RISK (VaR) - Historical Method                                 │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
        std::cout << "  Portfolio Value: $" << std::setprecision(0) << portfolioValue << "\n";
        std::cout << "  \n";

        double var95 = RiskAnalyzer::CalculateHistoricalVaR(portfolioReturns, portfolioValue, 0.95);
        double var99 = RiskAnalyzer::CalculateHistoricalVaR(portfolioReturns, portfolioValue, 0.99);

        std::cout << "  95% Confidence VaR: $" << var95 << "\n";
        std::cout << "    → \"I am 95% confident I won't lose more than $" << var95 << " next period\"\n";
        std::cout << "    → " << std::setprecision(1) << (var95 / portfolioValue * 100) << "% of portfolio\n";
        std::cout << "  \n";
        std::cout << "  99% Confidence VaR: $" << std::setprecision(0) << var99 << "\n";
        std::cout << "    → \"I am 99% confident I won't lose more than $" << var99 << " next period\"\n";
        std::cout << "    → " << std::setprecision(1) << (var99 / portfolioValue * 100) << "% of portfolio\n";
        std::cout << "  \n";
        std::cout << "  ⚠ LIMITATION: VaR can be exceeded! Not a guarantee, just a statistical estimate.\n";

    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }
}

void demonstratePortfolioOptimization() {
    printSectionHeader("PREMIUM FEATURE 1: PORTFOLIO OPTIMIZATION (Efficient Frontier)");

    std::cout << "\nModern Portfolio Theory: Finding the optimal mix of assets\n";
    std::cout << "Goal: Maximize risk-adjusted return (Sharpe Ratio) through diversification\n";

    // Simulated historical monthly returns for 3 assets
    std::vector<double> goldReturns = {0.02, -0.01, 0.03, -0.02, 0.04, 0.01, 0.02, -0.01, 0.03, 0.00, 0.02, 0.01};
    std::vector<double> sp500Returns = {0.05, 0.03, -0.02, 0.04, 0.06, -0.03, 0.07, 0.02, -0.04, 0.05, 0.03, 0.04};
    std::vector<double> btcReturns = {0.15, -0.20, 0.30, -0.10, 0.25, -0.15, 0.20, -0.05, 0.10, 0.08, -0.12, 0.18};

    std::vector<std::vector<double>> assetReturns = {goldReturns, sp500Returns, btcReturns};
    std::vector<std::string> assetNames = {"Gold", "S&P 500", "Bitcoin"};

    std::cout << "\nAssets in Portfolio:\n";
    for (size_t i = 0; i < assetNames.size(); ++i) {
        double avgReturn = RiskAnalyzer::CalculateMean(assetReturns[i]);
        double volatility = RiskAnalyzer::CalculateVolatility(assetReturns[i]);
        double annualReturn = avgReturn * 12;
        double annualVol = RiskAnalyzer::MonthlyToAnnualVolatility(volatility);

        std::cout << "  " << i + 1 << ". " << assetNames[i] << ":\n";
        std::cout << "     Annual Return: " << std::setprecision(1) << std::fixed
                  << (annualReturn * 100) << "%\n";
        std::cout << "     Annual Volatility: " << (annualVol * 100) << "%\n";
    }

    try {
        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ FORMULA 8-9: MODERN PORTFOLIO THEORY (MPT) OPTIMIZATION                             │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
        std::cout << "  Running Monte Carlo simulation (10,000 random portfolios)...\n";

        EfficientFrontierResult result = PortfolioOptimizer::CalculateEfficientFrontier(
            assetReturns,
            assetNames,
            10000,      // Number of simulations
            0.02 / 12   // Monthly risk-free rate (2% annual)
        );

        PortfolioResult optimal = result.optimalSharpePortfolio;

        std::cout << "\n  OPTIMAL PORTFOLIO (Maximum Sharpe Ratio):\n";
        std::cout << "  ─────────────────────────────────────\n";
        std::cout << "  Asset Allocation:\n";
        for (size_t i = 0; i < optimal.weights.size(); ++i) {
            std::cout << "    " << assetNames[i] << ": " << std::setprecision(1)
                      << (optimal.weights[i] * 100) << "%\n";
        }

        double annualReturn = optimal.portfolioReturn * 12;
        double annualRisk = RiskAnalyzer::MonthlyToAnnualVolatility(optimal.portfolioRisk);

        std::cout << "  \n";
        std::cout << "  Expected Annual Return: " << std::setprecision(2) << (annualReturn * 100) << "%\n";
        std::cout << "  Annual Volatility (Risk): " << (annualRisk * 100) << "%\n";
        std::cout << "  Sharpe Ratio: " << std::setprecision(3) << optimal.sharpeRatio << "\n";
        std::cout << "  \n";
        std::cout << "  Interpretation: " << AssetClassifier::InterpretSharpeRatio(optimal.sharpeRatio) << "\n";
        std::cout << "  \n";
        std::cout << "  🎯 This allocation provides the best risk-adjusted return based on HISTORICAL data.\n";
        std::cout << "  ⚠  Future correlations and returns WILL differ from historical values!\n";

    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }
}

void demonstrateStrategyBacktesting() {
    printSectionHeader("PREMIUM FEATURE 3: STRATEGY BACKTESTING");

    std::cout << "\nTest how different investment strategies would have performed historically.\n";
    std::cout << "Compare: Dollar-Cost Averaging (DCA) vs Buy-and-Hold vs Moving Average Crossover\n";

    // Simulated price data (e.g., 500 days of prices)
    std::vector<double> prices;
    double basePrice = 100.0;
    for (int i = 0; i < 500; ++i) {
        // Simulate price with trend and volatility
        double trend = 0.001 * i;  // Slight upward trend
        double noise = (std::sin(i * 0.1) * 10.0) + (std::sin(i * 0.05) * 20.0);
        prices.push_back(basePrice + trend + noise);
    }

    double initialCapital = 10000.0;

    std::cout << "\nSimulated Asset Price Data:\n";
    std::cout << "  Starting Price: $" << std::setprecision(2) << std::fixed << prices[0] << "\n";
    std::cout << "  Ending Price: $" << prices.back() << "\n";
    std::cout << "  Total Days: " << prices.size() << "\n";
    std::cout << "  Initial Capital: $" << std::setprecision(0) << initialCapital << "\n";

    try {
        // Strategy 1: Buy and Hold
        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ STRATEGY 1: BUY AND HOLD                                                             │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";

        BacktestResult bhResult = StrategyBacktester::RunBuyAndHoldBacktest(prices, initialCapital);

        std::cout << "  Final Value: $" << std::setprecision(2) << bhResult.finalValue << "\n";
        std::cout << "  Total Return: " << std::setprecision(1) << (bhResult.totalReturn * 100) << "%\n";
        std::cout << "  Annualized Return: " << (bhResult.annualizedReturn * 100) << "%\n";
        std::cout << "  Maximum Drawdown: " << (bhResult.maxDrawdown * 100) << "%\n";
        std::cout << "  Trades: " << bhResult.totalTrades << "\n";

        // Strategy 2: Dollar-Cost Averaging
        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ STRATEGY 2: DOLLAR-COST AVERAGING (DCA)                                             │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";

        DCAConfig dcaConfig;
        dcaConfig.investmentAmount = 500.0;  // Invest $500 every period
        dcaConfig.frequency = 30;             // Every 30 days

        std::cout << "  Investment: $" << dcaConfig.investmentAmount << " every "
                  << dcaConfig.frequency << " days\n";

        BacktestResult dcaResult = StrategyBacktester::RunDCABacktest(prices, initialCapital, dcaConfig);

        std::cout << "  Final Value: $" << std::setprecision(2) << dcaResult.finalValue << "\n";
        std::cout << "  Total Return: " << std::setprecision(1) << (dcaResult.totalReturn * 100) << "%\n";
        std::cout << "  Annualized Return: " << (dcaResult.annualizedReturn * 100) << "%\n";
        std::cout << "  Maximum Drawdown: " << (dcaResult.maxDrawdown * 100) << "%\n";
        std::cout << "  Trades: " << dcaResult.totalTrades << "\n";

        // Strategy 3: Moving Average Crossover
        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ STRATEGY 3: MOVING AVERAGE CROSSOVER (Golden/Death Cross)                           │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";

        MovingAverageCrossConfig maConfig;
        maConfig.shortPeriod = 50;   // 50-day MA
        maConfig.longPeriod = 200;   // 200-day MA

        std::cout << "  Buy Signal: " << maConfig.shortPeriod << "-day MA crosses above "
                  << maConfig.longPeriod << "-day MA (Golden Cross)\n";
        std::cout << "  Sell Signal: " << maConfig.shortPeriod << "-day MA crosses below "
                  << maConfig.longPeriod << "-day MA (Death Cross)\n";

        BacktestResult maResult = StrategyBacktester::RunMovingAverageCrossBacktest(
            prices, initialCapital, maConfig);

        std::cout << "  Final Value: $" << std::setprecision(2) << maResult.finalValue << "\n";
        std::cout << "  Total Return: " << std::setprecision(1) << (maResult.totalReturn * 100) << "%\n";
        std::cout << "  Annualized Return: " << (maResult.annualizedReturn * 100) << "%\n";
        std::cout << "  Maximum Drawdown: " << (maResult.maxDrawdown * 100) << "%\n";
        std::cout << "  Trades: " << maResult.totalTrades << "\n";

        // Comparison
        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ STRATEGY COMPARISON                                                                  │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";
        std::cout << "  Strategy              Final Value    Total Return    Max Drawdown    Trades\n";
        std::cout << "  ─────────────────────────────────────────────────────────────────────────────\n";
        std::cout << "  Buy & Hold            $" << std::setw(10) << std::setprecision(2) << bhResult.finalValue
                  << "    " << std::setw(7) << std::setprecision(1) << (bhResult.totalReturn * 100) << "%"
                  << "        " << std::setw(7) << (bhResult.maxDrawdown * 100) << "%"
                  << "        " << bhResult.totalTrades << "\n";
        std::cout << "  DCA                   $" << std::setw(10) << dcaResult.finalValue
                  << "    " << std::setw(7) << (dcaResult.totalReturn * 100) << "%"
                  << "        " << std::setw(7) << (dcaResult.maxDrawdown * 100) << "%"
                  << "        " << dcaResult.totalTrades << "\n";
        std::cout << "  MA Crossover          $" << std::setw(10) << maResult.finalValue
                  << "    " << std::setw(7) << (maResult.totalReturn * 100) << "%"
                  << "        " << std::setw(7) << (maResult.maxDrawdown * 100) << "%"
                  << "        " << maResult.totalTrades << "\n";

        std::cout << "\n  ⚠ WARNING: Past performance does NOT guarantee future results!\n";
        std::cout << "             Strategies that worked historically may fail in the future.\n";

    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }
}

void demonstrateRatioAnalysis() {
    printSectionHeader("PREMIUM FEATURE 4: RATIO ANALYSIS (Z-Score)");

    std::cout << "\nAnalyze the ratio between two assets to identify mean reversion opportunities.\n";
    std::cout << "Example: Gold/Silver Ratio - Is gold expensive or cheap relative to silver?\n";

    // Simulated historical prices
    std::vector<double> goldPrices;
    std::vector<double> silverPrices;

    // Generate ~100 data points with Gold/Silver ratio fluctuating around 65
    for (int i = 0; i < 100; ++i) {
        double baseRatio = 65.0 + std::sin(i * 0.1) * 10.0 + std::sin(i * 0.05) * 5.0;
        silverPrices.push_back(25.0 + std::sin(i * 0.15) * 2.0);
        goldPrices.push_back(silverPrices.back() * baseRatio);
    }

    // Make current ratio elevated (expensive gold)
    goldPrices.back() = silverPrices.back() * 80.0;

    std::cout << "\nHistorical Price Data:\n";
    std::cout << "  Data Points: " << goldPrices.size() << "\n";
    std::cout << "  Current Gold Price: $" << std::setprecision(2) << std::fixed << goldPrices.back() << "\n";
    std::cout << "  Current Silver Price: $" << silverPrices.back() << "\n";
    std::cout << "  Current Ratio: " << (goldPrices.back() / silverPrices.back()) << "\n";

    try {
        std::cout << "\n┌─────────────────────────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ FORMULA 13: Z-SCORE RATIO ANALYSIS                                                  │\n";
        std::cout << "└─────────────────────────────────────────────────────────────────────────────────────┘\n";

        RatioAnalysisResult result = RatioAnalyzer::AnalyzeRatio(
            goldPrices,
            silverPrices,
            "Gold",
            "Silver"
        );

        std::cout << "  Historical Statistics:\n";
        std::cout << "    Historical Mean Ratio: " << std::setprecision(2) << result.historicalMean << "\n";
        std::cout << "    Standard Deviation: " << result.historicalStdDev << "\n";
        std::cout << "  \n";
        std::cout << "  Current Analysis:\n";
        std::cout << "    Current Ratio: " << result.currentRatio << "\n";
        std::cout << "    Z-Score: " << std::setprecision(3) << result.zScore << "\n";
        std::cout << "  \n";
        std::cout << "  " << result.signal << "\n";
        std::cout << "  \n";
        std::cout << "  Detailed Interpretation:\n";
        std::cout << "  " << result.interpretation << "\n";
        std::cout << "  \n";

        if (RatioAnalyzer::IsExtremeDeviation(result.zScore)) {
            std::cout << "  🎯 ACTIONABLE SIGNAL: Extreme deviation detected!\n";
        } else if (RatioAnalyzer::IsWithinNormalRange(result.zScore)) {
            std::cout << "  ✓ Normal range - No compelling mean reversion opportunity.\n";
        } else {
            std::cout << "  ⚠ Moderate deviation - Watch for mean reversion.\n";
        }

        std::cout << "  \n";
        std::cout << "  ⚠ CRITICAL: Mean reversion is NOT guaranteed!\n";
        std::cout << "             Historical relationships can break down permanently.\n";

    } catch (const std::exception& e) {
        std::cout << "  Error: " << e.what() << "\n";
    }
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
    std::cout << "PREMIUM FEATURES:\n";
    std::cout << "  • Portfolio Optimization (Efficient Frontier via Monte Carlo)\n";
    std::cout << "  • Advanced Risk Metrics (Sortino Ratio, Value at Risk)\n";
    std::cout << "  • Strategy Backtesting (DCA, Buy-and-Hold, MA Crossover)\n";
    std::cout << "  • Ratio Analysis (Z-Score for mean reversion)\n";
    std::cout << "\n";
    std::cout << "⚠ WARNING: These tools analyze PAST data. They do NOT predict the future!\n";
    std::cout << "           Past performance is not a guarantee of future results.\n";
    std::cout << "\n";

    // Run basic demonstrations
    demonstrateFutureValueCalculations();
    demonstrateRiskAnalysis();
    demonstrateAssetClassification();

    // Run premium feature demonstrations
    demonstratePortfolioOptimization();
    demonstrateAdvancedRiskMetrics();
    demonstrateStrategyBacktesting();
    demonstrateRatioAnalysis();

    // Final warning
    demonstrateBlackSwanWarning();

    std::cout << "\n═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "                              END OF ANALYSIS                                          \n";
    std::cout << "═══════════════════════════════════════════════════════════════════════════════════════\n";
    std::cout << "\n";

    return 0;
}
