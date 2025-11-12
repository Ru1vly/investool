# InvestTool

**Financial Goal Setting and Risk Analysis Framework**

A C++ terminal application that implements standard financial equations for analyzing investment scenarios, quantifying risk, and evaluating investment efficiency.

⚠️ **WARNING:** This tool performs mathematically accurate calculations but does NOT predict the future. Past performance is not a guarantee of future results. Use for risk analysis and planning purposes only.

## Features

### Core Features

#### 1. Future Value Calculations (Dollar-Cost Averaging)
- **Formula 1:** Calculate Future Value given regular payments
- **Formula 2:** Calculate required payment to reach a financial goal
- **Formula 3:** Calculate time needed to reach a goal
- Annual/Monthly interest rate conversions

#### 2. Risk Measurement
- **Formula 4:** Variance (σ²) - Measure of return dispersion
- **Formula 5:** Volatility/Standard Deviation (σ) - Standard risk measure
- **Formula 8:** Correlation Coefficient (ρ) - Asset correlation analysis
- **Formula 9:** Portfolio Volatility - Two-asset portfolio risk calculation
- Daily/Monthly to Annual volatility conversions

#### 3. Risk-Adjusted Performance
- **Formula 6:** Sharpe Ratio - Return per unit of risk
- **Formula 7:** Beta (β) - Correlation with market volatility
- **Formula 10-11:** Sortino Ratio - Downside risk-adjusted return
- **Formula 12:** Value at Risk (VaR) - Maximum expected loss quantification
- Covariance calculations for portfolio analysis

#### 4. Asset Classification
- Classify assets by volatility into 5 risk levels:
  - Very Low Risk (0-2% annual volatility)
  - Low Risk (2-8%)
  - Medium Risk (8-20%)
  - High Risk (20-40%)
  - Very High Risk/Speculation (40%+)
- Detailed risk interpretations and asset examples

### Premium Features

#### 5. Portfolio Optimization (Efficient Frontier)
- **Monte Carlo Simulation:** Test 10,000+ random portfolio allocations
- **Modern Portfolio Theory (MPT):** Find optimal asset mix for maximum Sharpe Ratio
- **Diversification Analysis:** Account for asset correlations and covariance
- **Risk-Return Tradeoff:** Identify efficient portfolios on the frontier

**Example Use:**
```cpp
EfficientFrontierResult result = PortfolioOptimizer::CalculateEfficientFrontier(
    {goldReturns, sp500Returns, btcReturns},
    {"Gold", "S&P 500", "Bitcoin"},
    10000,  // Number of simulations
    0.02    // Risk-free rate
);
// Returns optimal weights, expected return, risk, and Sharpe Ratio
```

#### 6. Advanced Risk Metrics (Sortino Ratio & VaR)
- **Sortino Ratio:** Better than Sharpe - only penalizes downside volatility
- **Downside Deviation:** Measures only negative return volatility
- **Value at Risk (VaR):** Parametric and Historical methods
- **Confidence Levels:** 90%, 95%, and 99% VaR calculations

**Example Use:**
```cpp
// Sortino Ratio (ignores upside volatility)
double sortino = RiskAnalyzer::CalculateSortinoRatio(returns, 0.02);

// Value at Risk
double var95 = RiskAnalyzer::CalculateHistoricalVaR(returns, 200000.0, 0.95);
// "95% confident won't lose more than $X"
```

#### 7. Strategy Backtesting
- **Dollar-Cost Averaging (DCA):** Test fixed-amount periodic investments
- **Buy and Hold:** Simple buy-and-hold strategy
- **Moving Average Crossover:** Golden Cross / Death Cross signals
- **Performance Metrics:** Total return, annualized return, maximum drawdown

**Example Use:**
```cpp
// Test DCA strategy
DCAConfig config = {500.0, 30};  // $500 every 30 days
BacktestResult result = StrategyBacktester::RunDCABacktest(
    historicalPrices, 10000.0, config
);
// Compare multiple strategies side-by-side
```

#### 8. Ratio Analysis (Z-Score for Mean Reversion)
- **Z-Score Calculation:** Identify statistical anomalies
- **Mean Reversion Signals:** Detect when ratios are extreme
- **Relative Value Analysis:** Compare two assets (Gold/Silver, etc.)
- **Statistical Thresholds:** |Z| > 2 indicates extreme deviation

**Example Use:**
```cpp
RatioAnalysisResult result = RatioAnalyzer::AnalyzeRatio(
    goldPrices, silverPrices, "Gold", "Silver"
);
// Get Z-score, signal, and interpretation
// Z > 2: Gold extremely expensive relative to silver
// Z < -2: Gold extremely cheap relative to silver
```

### Educational Framework
- Comprehensive documentation of limitations
- Black Swan event awareness (Nassim Taleb)
- Source citations for all formulas
- Clear warnings about predictive validity
- Implementation pseudocode and mathematical foundations

## Building the Project

This is a C++ terminal application. To build and run:

### Prerequisites
- CMake 3.10 or higher
- C++ compiler with C++17 support (GCC, Clang, or MSVC)

### Build Instructions

```bash
# Create build directory
mkdir build
cd build

# Configure with CMake
cmake ..

# Build the project
make

# Run the application
./investool
```

### Project Structure

**Core Components:**
- `FinancialCalculator.h/cpp` - Future Value of Annuity calculations (Formulas 1-3)
- `RiskAnalyzer.h/cpp` - Risk measurement and risk-adjusted performance metrics (Formulas 4-13)
- `AssetClassifier.h/cpp` - Asset classification by volatility and risk interpretation
- `main.cpp` - Demonstration application with practical examples

**Premium Features:**
- `PortfolioOptimizer.h/cpp` - Efficient Frontier via Monte Carlo simulation (Formulas 8-9)
- `StrategyBacktester.h/cpp` - Investment strategy backtesting engine
- `RatioAnalyzer.h/cpp` - Z-Score ratio analysis for mean reversion (Formula 13)

**Build Configuration:**
- `CMakeLists.txt` - CMake build configuration

**Documentation:**
- `DOCUMENTATION.md` - Complete API reference for core features (Formulas 1-7)
- `ADVANCED_FORMULAS.md` - Detailed mathematical documentation for premium features (Formulas 8-13)
- `README.md` - This file

**Build Artifacts:**
- `build/` - CMake build directory (generated, gitignored)

## Quick Start Example

```cpp
#include "FinancialCalculator.h"
#include "RiskAnalyzer.h"
#include "AssetClassifier.h"

// Calculate investment goal
double fv = FinancialCalculator::CalculateFutureValue(20000, 0.01, 7);

// Analyze risk
std::vector<double> returns = {0.15, -0.20, 0.30, -0.10, 0.25};
double volatility = RiskAnalyzer::CalculateVolatility(returns);
double annualVol = RiskAnalyzer::MonthlyToAnnualVolatility(volatility);

// Classify asset
AssetClass classification = AssetClassifier::ClassifyByVolatility(annualVol);
std::cout << classification.description << std::endl;
```

For complete API reference and detailed examples, see [DOCUMENTATION.md](DOCUMENTATION.md).

## Key Formulas

### Core Formulas (Formulas 1-7)

| Formula | Purpose | Implementation |
|---------|---------|----------------|
| **Formula 1** | Future Value (FV) | `CalculateFutureValue(pmt, i, n)` |
| **Formula 2** | Required Payment (PMT) | `CalculateRequiredPayment(fv, i, n)` |
| **Formula 3** | Required Periods (n) | `CalculateRequiredPeriods(fv, pmt, i)` |
| **Formula 4** | Variance (σ²) | `CalculateVariance(returns)` |
| **Formula 5** | Volatility (σ) | `CalculateVolatility(returns)` |
| **Formula 6** | Sharpe Ratio | `CalculateSharpeRatio(returns, rf)` |
| **Formula 7** | Beta (β) | `CalculateBeta(assetReturns, marketReturns)` |

### Premium Formulas (Formulas 8-13)

| Formula | Purpose | Implementation |
|---------|---------|----------------|
| **Formula 8** | Correlation Coefficient (ρ) | `CalculateCorrelation(returns1, returns2)` |
| **Formula 9** | Portfolio Volatility (σ_p) | `CalculatePortfolioVolatility(w1, σ1, w2, σ2, ρ)` |
| **Formula 10** | Downside Deviation (σ_d) | `CalculateDownsideDeviation(returns, MARR)` |
| **Formula 11** | Sortino Ratio | `CalculateSortinoRatio(returns, rf)` |
| **Formula 12** | Value at Risk (VaR) | `CalculateHistoricalVaR(returns, value, conf)` |
| **Formula 13** | Z-Score | `CalculateZScore(value, historicalData)` |

## Sources

### Core Features
- **Future Value Formulas:** Corporate Finance Institute (CFI), standard finance literature
- **Risk Metrics:** Modern Portfolio Theory (MPT), documented by Investopedia
- **Sharpe Ratio:** William F. Sharpe (Nobel Prize winner, 1990)
- **Beta & CAPM:** Capital Asset Pricing Model, standard finance theory

### Premium Features
- **Modern Portfolio Theory:** Harry Markowitz, "Portfolio Selection" (1952), Nobel Prize winner (1990)
- **Sortino Ratio:** Frank A. Sortino and Robert van der Meer, "Downside Risk" (1991)
- **Value at Risk:** J.P. Morgan RiskMetrics (1996); Philippe Jorion, "Value at Risk" (2006)
- **Z-Score & Statistical Methods:** Standard statistical theory, quantitative finance literature

### Risk Awareness
- **Black Swan Theory:** Nassim Nicholas Taleb
  - "The Black Swan: The Impact of the Highly Improbable" (2007)
  - "Antifragile: Things That Gain from Disorder" (2012)
  - "Fooled by Randomness" (2001)

## License

This is an educational tool implementing standard financial formulas from public domain finance literature.
