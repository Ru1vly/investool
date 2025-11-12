# InvestTool

**Financial Goal Setting and Risk Analysis Framework**

A C++ terminal application that implements standard financial equations for analyzing investment scenarios, quantifying risk, and evaluating investment efficiency.

⚠️ **WARNING:** This tool performs mathematically accurate calculations but does NOT predict the future. Past performance is not a guarantee of future results. Use for risk analysis and planning purposes only.

## Features

### 1. Future Value Calculations (Dollar-Cost Averaging)
- **Formula 1:** Calculate Future Value given regular payments
- **Formula 2:** Calculate required payment to reach a financial goal
- **Formula 3:** Calculate time needed to reach a goal
- Annual/Monthly interest rate conversions

### 2. Risk Measurement
- **Formula 4:** Variance (σ²) - Measure of return dispersion
- **Formula 5:** Volatility/Standard Deviation (σ) - Standard risk measure
- Daily/Monthly to Annual volatility conversions

### 3. Risk-Adjusted Performance
- **Formula 6:** Sharpe Ratio - Return per unit of risk
- **Formula 7:** Beta (β) - Correlation with market volatility
- Covariance calculations for portfolio analysis

### 4. Asset Classification
- Classify assets by volatility into 5 risk levels:
  - Very Low Risk (0-2% annual volatility)
  - Low Risk (2-8%)
  - Medium Risk (8-20%)
  - High Risk (20-40%)
  - Very High Risk/Speculation (40%+)
- Detailed risk interpretations and asset examples

### 5. Educational Framework
- Comprehensive documentation of limitations
- Black Swan event awareness (Nassim Taleb)
- Source citations for all formulas
- Clear warnings about predictive validity

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
- `RiskAnalyzer.h/cpp` - Risk measurement and risk-adjusted performance metrics (Formulas 4-7)
- `AssetClassifier.h/cpp` - Asset classification by volatility and risk interpretation
- `main.cpp` - Demonstration application with practical examples
- `CMakeLists.txt` - CMake build configuration

**Documentation:**
- `DOCUMENTATION.md` - Complete API reference and usage guide
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

| Formula | Purpose | Implementation |
|---------|---------|----------------|
| **Formula 1** | Future Value (FV) | `CalculateFutureValue(pmt, i, n)` |
| **Formula 2** | Required Payment (PMT) | `CalculateRequiredPayment(fv, i, n)` |
| **Formula 3** | Required Periods (n) | `CalculateRequiredPeriods(fv, pmt, i)` |
| **Formula 4** | Variance (σ²) | `CalculateVariance(returns)` |
| **Formula 5** | Volatility (σ) | `CalculateVolatility(returns)` |
| **Formula 6** | Sharpe Ratio | `CalculateSharpeRatio(returns, rf)` |
| **Formula 7** | Beta (β) | `CalculateBeta(assetReturns, marketReturns)` |

## Sources

- **Future Value Formulas:** Corporate Finance Institute (CFI), standard finance literature
- **Risk Metrics:** Modern Portfolio Theory (MPT), documented by Investopedia
- **Sharpe Ratio:** William F. Sharpe (Nobel Prize winner, 1990)
- **Black Swan Theory:** Nassim Nicholas Taleb
  - "The Black Swan: The Impact of the Highly Improbable" (2007)
  - "Antifragile: Things That Gain from Disorder" (2012)

## License

This is an educational tool implementing standard financial formulas from public domain finance literature.
