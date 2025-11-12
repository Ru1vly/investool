# InvestTool - Financial Equations and Risk Framework Documentation

## Overview

This C++ application implements a comprehensive framework for financial goal setting and risk analysis. It provides mathematically accurate calculations for investment planning, risk measurement, and asset classification.

**⚠️ CRITICAL WARNING:** These tools analyze PAST data and perform mathematical calculations. They do NOT predict the future. Past performance is not a guarantee of future results.

## Architecture

The framework consists of three main components:

### 1. FinancialCalculator
Handles Future Value of Annuity calculations for Dollar-Cost Averaging (DCA) strategies.

### 2. RiskAnalyzer
Implements risk measurement and risk-adjusted performance metrics based on Modern Portfolio Theory.

### 3. AssetClassifier
Classifies assets based on volatility and provides interpretations for risk metrics.

---

## API Reference

## FinancialCalculator Class

### Core Formulas

#### `CalculateFutureValue(pmt, i, n)`
**Formula 1: Future Value (FV)**

```cpp
double fv = FinancialCalculator::CalculateFutureValue(20000.0, 0.01, 7);
```

**Formula:**
```
FV = PMT * [(1 + i)^n - 1] / i
```

**Parameters:**
- `pmt` (double): Payment per period (e.g., 20,000 TL monthly)
- `i` (double): Interest rate per period (e.g., 0.01 for 1% monthly)
- `n` (int): Number of periods (e.g., 7 months)

**Returns:** Future Value - total amount at end of period

**Example:**
```cpp
// Calculate how much you'll have after 7 months
// investing 20,000 TL/month at 1% monthly return
double fv = FinancialCalculator::CalculateFutureValue(20000.0, 0.01, 7);
// Result: ~144,270.70 TL
```

---

#### `CalculateRequiredPayment(fv, i, n)`
**Formula 2: Required Payment (PMT)**

```cpp
double pmt = FinancialCalculator::CalculateRequiredPayment(200000.0, 0.01, 7);
```

**Formula:**
```
PMT = FV * i / [(1 + i)^n - 1]
```

**Parameters:**
- `fv` (double): Target Future Value (e.g., 200,000 TL)
- `i` (double): Interest rate per period
- `n` (int): Number of periods

**Returns:** Required payment per period to reach goal

**Example:**
```cpp
// Calculate how much to invest monthly to reach 200,000 TL
// in 7 months at 1% monthly return
double pmt = FinancialCalculator::CalculateRequiredPayment(200000.0, 0.01, 7);
// Result: ~27,725.66 TL/month
```

---

#### `CalculateRequiredPeriods(fv, pmt, i)`
**Formula 3: Required Number of Periods (n)**

```cpp
double n = FinancialCalculator::CalculateRequiredPeriods(200000.0, 20000.0, 0.01);
```

**Formula:**
```
n = ln(1 + (FV * i / PMT)) / ln(1 + i)
```

**Parameters:**
- `fv` (double): Target Future Value
- `pmt` (double): Payment per period
- `i` (double): Interest rate per period

**Returns:** Number of periods needed to reach goal

**Example:**
```cpp
// Calculate how many months to reach 200,000 TL
// investing 20,000 TL/month at 1% monthly return
double n = FinancialCalculator::CalculateRequiredPeriods(200000.0, 20000.0, 0.01);
// Result: ~9.58 months
```

---

### Utility Functions

#### `AnnualToMonthlyRate(annualRate)`
Convert annual interest rate to monthly rate (simple approximation).

```cpp
double monthlyRate = FinancialCalculator::AnnualToMonthlyRate(0.12); // 0.01
```

#### `MonthlyToAnnualRate(monthlyRate)`
Convert monthly interest rate to annual rate (simple approximation).

```cpp
double annualRate = FinancialCalculator::MonthlyToAnnualRate(0.01); // 0.12
```

---

## RiskAnalyzer Class

### Statistical Measures

#### `CalculateMean(returns)`
Calculate average return from a series of returns.

```cpp
std::vector<double> returns = {0.15, -0.20, 0.30, -0.10};
double mean = RiskAnalyzer::CalculateMean(returns);
```

---

#### `CalculateVariance(returns)`
**Formula 4: Variance (σ²)**

```cpp
double variance = RiskAnalyzer::CalculateVariance(returns);
```

**Formula:**
```
σ² = Σ(R_j - R̄)² / (N - 1)
```

Measures the average degree to which returns differ from the mean.

**Parameters:**
- `returns` (vector<double>): Historical returns (e.g., monthly returns)

**Returns:** Variance - average squared deviation from mean

---

#### `CalculateVolatility(returns)`
**Formula 5: Standard Deviation / Volatility (σ)**

```cpp
double volatility = RiskAnalyzer::CalculateVolatility(returns);
```

**Formula:**
```
σ = √(Variance)
```

This is the **STANDARD measure of risk**.

**Interpretation:**
- Low σ (e.g., 2%): Stable asset, low risk
- High σ (e.g., 40%): Volatile asset, high risk

**Example:**
```cpp
std::vector<double> cryptoReturns = {0.15, -0.20, 0.30, -0.10, 0.25};
double monthlyVol = RiskAnalyzer::CalculateVolatility(cryptoReturns);
double annualVol = RiskAnalyzer::MonthlyToAnnualVolatility(monthlyVol);
```

---

### Risk-Adjusted Performance Metrics

#### `CalculateSharpeRatio(portfolioReturn, riskFreeRate, portfolioVolatility)`
**Formula 6: Sharpe Ratio**

```cpp
double sharpe = RiskAnalyzer::CalculateSharpeRatio(0.05, 0.005, 0.20);
```

**Formula:**
```
Sharpe = (R_p - R_f) / σ_p
```

Measures return per unit of risk. **Higher is better.**

**Parameters:**
- `portfolioReturn` (double): Average return of the portfolio/asset
- `riskFreeRate` (double): Risk-free rate (e.g., government bond yield)
- `portfolioVolatility` (double): Volatility (σ) of the portfolio/asset

**Returns:** Sharpe Ratio - risk-adjusted return metric

**Interpretation:**
- < 1.0: **Poor** - risk not worth it
- 1.0 - 1.99: **Good** - adequately compensated for risk
- ≥ 2.0: **Excellent** - well compensated for risk

**Alternative Signature:**
```cpp
// Calculate Sharpe Ratio directly from returns
double sharpe = RiskAnalyzer::CalculateSharpeRatio(returns, 0.005);
```

**Source:** Developed by William F. Sharpe (Nobel Prize winner)

---

#### `CalculateBeta(assetReturns, marketReturns)`
**Formula 7: Beta (β)**

```cpp
double beta = RiskAnalyzer::CalculateBeta(assetReturns, marketReturns);
```

**Formula:**
```
β = Cov(Asset, Market) / Var(Market)
```

Measures an asset's volatility **relative to the market**.

**Parameters:**
- `assetReturns` (vector<double>): Historical returns of the asset
- `marketReturns` (vector<double>): Historical returns of the market (e.g., S&P 500, BIST 100)

**Returns:** Beta - systematic risk measure

**Interpretation:**
- β = 1: Moves with the market
- β > 1 (Aggressive): More volatile than market
- β < 1 (Defensive): Less volatile than market
- β = 0: No correlation with market
- β < 0: Moves opposite to market (rare)

**Example:**
```cpp
std::vector<double> cryptoReturns = {0.15, -0.20, 0.30};
std::vector<double> sp500Returns = {0.02, -0.01, 0.03};
double beta = RiskAnalyzer::CalculateBeta(cryptoReturns, sp500Returns);
// High beta indicates the asset is much more volatile than the market
```

**Source:** Part of Capital Asset Pricing Model (CAPM)

---

### Supporting Functions

#### `CalculateCovariance(returns1, returns2)`
Measures how two assets move together.

```cpp
double cov = RiskAnalyzer::CalculateCovariance(assetReturns, marketReturns);
```

#### `DailyToAnnualVolatility(dailyVolatility)`
Convert daily volatility to annual: `Annual = Daily * √252`

#### `MonthlyToAnnualVolatility(monthlyVolatility)`
Convert monthly volatility to annual: `Annual = Monthly * √12`

---

## AssetClassifier Class

### Classification System

#### `ClassifyByVolatility(annualVolatility)`
Classify an asset based on its annual volatility.

```cpp
AssetClass classification = AssetClassifier::ClassifyByVolatility(0.70);
std::cout << classification.description << std::endl;
// Output: "Very High Risk (Speculation)"
```

**Parameters:**
- `annualVolatility` (double): Annual volatility in decimal form (e.g., 0.15 for 15%)

**Returns:** `AssetClass` struct containing:
- `riskLevel`: Enum value (VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH)
- `minVolatility`: Minimum volatility for this class (%)
- `maxVolatility`: Maximum volatility for this class (%)
- `description`: Human-readable risk level
- `typicalAssets`: Examples of assets in this class
- `returnExpectation`: Expected return characteristics
- `riskOfLoss`: Risk of principal loss

### Risk Level Classification Table

| Risk Level | Annual Volatility | Typical Assets | Return Expectation | Risk of Loss |
|------------|-------------------|----------------|-------------------|--------------|
| **Very Low** | 0% - 2% | Savings Accounts, Government Bonds | Low (Predictable) | Almost None |
| **Low** | 2% - 8% | Corporate Bonds, Gold | Low-Medium | Low |
| **Medium** | 8% - 20% | Index Funds, Blue-Chip Stocks | Medium | Medium |
| **High** | 20% - 40% | Growth Stocks, Emerging Markets | High | High |
| **Very High** | 40%+ | Crypto, Leverage, Options | Very High/Unlimited | Very High/Total Loss |

---

### Interpretation Functions

#### `InterpretSharpeRatio(sharpeRatio)`
Get human-readable interpretation of a Sharpe Ratio.

```cpp
std::string interpretation = AssetClassifier::InterpretSharpeRatio(0.5);
// Returns: "Poor - Risk is not worth it"
```

#### `InterpretBeta(beta)`
Get human-readable interpretation of a Beta value.

```cpp
std::string interpretation = AssetClassifier::InterpretBeta(1.5);
// Returns: "Aggressive - More volatile than market"
```

#### `GetRiskLevelName(level)`
Convert risk level enum to string.

#### `PrintAssetClassificationTable()`
Print formatted table of all asset classifications.

---

## Usage Examples

### Example 1: Investment Goal Analysis

```cpp
#include "FinancialCalculator.h"

// Scenario: Want to reach 200,000 TL in 7 months
double targetFV = 200000.0;
double monthlyPayment = 20000.0;
double annualRate = 0.12;  // 12% annual
double monthlyRate = FinancialCalculator::AnnualToMonthlyRate(annualRate);
int periods = 7;

// Calculate what you'd actually achieve
double actualFV = FinancialCalculator::CalculateFutureValue(
    monthlyPayment, monthlyRate, periods
);
std::cout << "You would reach: " << actualFV << " TL" << std::endl;

// Calculate what you'd need to invest
double requiredPMT = FinancialCalculator::CalculateRequiredPayment(
    targetFV, monthlyRate, periods
);
std::cout << "Required investment: " << requiredPMT << " TL/month" << std::endl;
```

### Example 2: Risk Analysis of an Asset

```cpp
#include "RiskAnalyzer.h"
#include "AssetClassifier.h"

// Historical monthly returns (hypothetical crypto asset)
std::vector<double> returns = {
    0.15, -0.20, 0.30, -0.10, 0.25, -0.15, 0.20, -0.05
};

// Calculate risk metrics
double avgReturn = RiskAnalyzer::CalculateMean(returns);
double monthlyVol = RiskAnalyzer::CalculateVolatility(returns);
double annualVol = RiskAnalyzer::MonthlyToAnnualVolatility(monthlyVol);

// Classify the asset
AssetClass classification = AssetClassifier::ClassifyByVolatility(annualVol);
std::cout << "Risk Level: " << classification.description << std::endl;
std::cout << "Risk of Loss: " << classification.riskOfLoss << std::endl;
```

### Example 3: Risk-Adjusted Performance

```cpp
// Calculate Sharpe Ratio
double riskFreeRate = 0.005;  // 0.5% monthly (6% annual)
double sharpeRatio = RiskAnalyzer::CalculateSharpeRatio(returns, riskFreeRate);

std::cout << "Sharpe Ratio: " << sharpeRatio << std::endl;
std::cout << AssetClassifier::InterpretSharpeRatio(sharpeRatio) << std::endl;

// Calculate Beta vs market
std::vector<double> marketReturns = {
    0.02, -0.01, 0.03, -0.02, 0.04, 0.01, 0.02, -0.01
};

double beta = RiskAnalyzer::CalculateBeta(returns, marketReturns);
std::cout << "Beta: " << beta << std::endl;
std::cout << AssetClassifier::InterpretBeta(beta) << std::endl;
```

---

## Critical Limitations

### Mathematical Accuracy: 100%
All formulas are mathematically correct. If you provide inputs, calculations will be accurate.

### Predictive Power: EXTREMELY LOW
These models **CANNOT** predict the future because:

1. **Past Performance ≠ Future Results**
   - All inputs are based on historical data
   - Markets change continuously

2. **Black Swan Events** (Nassim Nicholas Taleb)
   - Unpredictable, high-impact events:
     - COVID-19 pandemic (2020)
     - Global financial crisis (2008)
     - Wars, political upheavals
   - These events make historical data irrelevant

3. **Changing Inputs**
   - Volatility (σ) is NOT fixed
   - Returns (i) are NOT constant
   - They change based on:
     - New information
     - Economic policy
     - Market psychology
     - Regulatory changes

### Correct Use of This Tool

✅ **DO USE FOR:**
- Risk Analysis: "What risk level does this asset fall into?"
- Reality Check: "Is a 12% monthly return realistic?"
- Requirement Analysis: "What would I need to reach my goal?"

❌ **DO NOT USE FOR:**
- Prediction: "I will definitely reach 200,000 TL in 7 months"
- Guarantee: "This asset will return 15% next month"
- Future Planning: "Volatility will stay at 20% forever"

---

## Sources and References

### Future Value Formulas
- Corporate Finance Institute (CFI)
- Standard finance textbooks and literature

### Risk Metrics (Standard Deviation, Beta, Sharpe Ratio)
- Modern Portfolio Theory (MPT)
- Investopedia documentation
- Sharpe Ratio: William F. Sharpe (Nobel Prize winner in Economics, 1990)

### Black Swan Theory
- Nassim Nicholas Taleb
  - "The Black Swan: The Impact of the Highly Improbable" (2007)
  - "Antifragile: Things That Gain from Disorder" (2012)

---

## Error Handling

All functions throw `std::invalid_argument` exceptions for invalid inputs:
- Negative or zero values where positive values are required
- Empty return vectors
- Mismatched vector lengths
- Division by zero scenarios

**Example:**
```cpp
try {
    double fv = FinancialCalculator::CalculateFutureValue(-1000, 0.01, 7);
} catch (const std::invalid_argument& e) {
    std::cerr << "Error: " << e.what() << std::endl;
    // Output: "Error: Payment must be positive"
}
```

---

## Building the Project

See [README.md](README.md) for build instructions.

---

## License

This is an educational tool implementing standard financial formulas from public domain finance literature.
