# Advanced Financial Analysis Formulas

## Overview

This document provides the mathematical formulas and theoretical foundations for four advanced concepts used in financial analysis and risk management:

1. **Modern Portfolio Theory (MPT) Optimization**
2. **Sortino Ratio (Downside Risk Analysis)**
3. **Value at Risk (VaR)**
4. **Z-Score (Ratio Analysis)**

These equations extend beyond the basic calculations (covered in [DOCUMENTATION.md](DOCUMENTATION.md)) into portfolio optimization, advanced risk assessment, and statistical timing analysis.

**⚠️ CRITICAL WARNING:** These tools analyze PAST data and perform mathematical calculations. They do NOT predict the future. Past performance is not a guarantee of future results.

---

## 1. Modern Portfolio Theory (MPT)

Modern Portfolio Theory, developed by Harry Markowitz (Nobel Prize winner, 1990), aims to find the "Efficient Frontier" - the set of portfolios that offer the highest expected return for a defined level of risk.

### Background

The key insight of MPT is that portfolio risk is not simply the weighted average of individual asset risks. Instead, the **correlation** between assets plays a crucial role. Diversification works because different assets don't always move together.

### Formula 8: Correlation Coefficient (ρ)

**Purpose:** Measures the degree to which two assets move in relation to each other.

**Formula:**
```
ρ_AB = Cov(R_A, R_B) / (σ_A × σ_B)
```

**Parameters:**
- `ρ_AB`: The correlation coefficient between assets A and B
- `Cov(R_A, R_B)`: The covariance of returns for assets A and B
- `σ_A`: The standard deviation (volatility) of asset A's returns
- `σ_B`: The standard deviation (volatility) of asset B's returns

**Range:** -1 to +1

**Interpretation:**
- `ρ = +1`: Perfect positive correlation (assets move together)
- `ρ = 0`: No correlation (assets move independently)
- `ρ = -1`: Perfect negative correlation (assets move in opposite directions)
- `ρ = 0.7 to 1.0`: Strong positive correlation
- `ρ = -0.7 to -1.0`: Strong negative correlation
- `ρ = -0.3 to 0.3`: Weak or no correlation

**Why It Matters:**
- Assets with low or negative correlation provide better diversification
- Combining assets with ρ < 1 reduces portfolio risk
- Gold and stocks often have low correlation (good diversification)
- Tech stocks often have high correlation with each other (poor diversification)

**Example:**
```cpp
// Historical returns
std::vector<double> goldReturns = {0.02, -0.01, 0.03, -0.02};
std::vector<double> stockReturns = {0.05, 0.03, -0.02, 0.04};

// Calculate covariance and volatilities
double cov = RiskAnalyzer::CalculateCovariance(goldReturns, stockReturns);
double sigmaGold = RiskAnalyzer::CalculateVolatility(goldReturns);
double sigmaStock = RiskAnalyzer::CalculateVolatility(stockReturns);

// Correlation coefficient
double rho = cov / (sigmaGold * sigmaStock);

// If rho ≈ 0.2: Low correlation → Good diversification benefit
```

---

### Formula 9: Two-Asset Portfolio Volatility (σ_p)

**Purpose:** Calculates the total risk (standard deviation) of a two-asset portfolio, accounting for diversification effects.

**Formula:**
```
σ_p = √[w_A² × σ_A² + w_B² × σ_B² + 2 × w_A × w_B × ρ_AB × σ_A × σ_B]
```

**Parameters:**
- `σ_p`: The standard deviation (volatility) of the portfolio
- `w_A`, `w_B`: The weight (percentage) of asset A and asset B in the portfolio
  - Note: `w_A + w_B = 1.0` (100%)
- `σ_A²`, `σ_B²`: The variance of asset A and asset B (volatility squared)
- `ρ_AB`: The correlation coefficient from Formula 8
- `σ_A`, `σ_B`: The standard deviation of asset A and asset B

**Key Insight:**
This formula shows that portfolio risk is **NOT** simply:
```
σ_p ≠ w_A × σ_A + w_B × σ_B  (INCORRECT - ignores correlation)
```

The correlation term (`2 × w_A × w_B × ρ_AB × σ_A × σ_B`) reduces portfolio risk when ρ < 1.

**Example:**
```cpp
// Portfolio: 60% stocks, 40% bonds
double w_stocks = 0.60;
double w_bonds = 0.40;

// Asset volatilities (annual)
double sigma_stocks = 0.20;  // 20% annual volatility
double sigma_bonds = 0.05;   // 5% annual volatility

// Correlation
double rho = 0.10;  // Low correlation between stocks and bonds

// Calculate portfolio volatility
double variance_portfolio =
    pow(w_stocks, 2) * pow(sigma_stocks, 2) +
    pow(w_bonds, 2) * pow(sigma_bonds, 2) +
    2 * w_stocks * w_bonds * rho * sigma_stocks * sigma_bonds;

double sigma_portfolio = sqrt(variance_portfolio);
// Result: ~12.3% annual volatility

// Compare to naive calculation (ignoring correlation):
double naive = w_stocks * sigma_stocks + w_bonds * sigma_bonds;
// Result: 14% (overestimates risk)

// Diversification benefit: 14% - 12.3% = 1.7% risk reduction
```

**Interpretation:**
- Lower correlation → Greater diversification benefit
- If ρ = 1: No diversification benefit (portfolio σ = weighted average)
- If ρ < 1: Portfolio σ < weighted average (diversification works!)
- If ρ = -1: Maximum diversification benefit (can eliminate risk entirely)

**Use Cases:**
- Optimal portfolio construction
- Understanding diversification benefits
- Risk-parity portfolio strategies
- Multi-asset allocation decisions

**Source:** Harry Markowitz, "Portfolio Selection" (1952), Journal of Finance

---

## 2. Sortino Ratio (Downside Risk Analysis)

### Background

The Sharpe Ratio (Formula 6) treats all volatility as "bad" - both upside and downside. But investors don't complain about upside volatility! The Sortino Ratio addresses this by only penalizing downside volatility.

**Developed by:** Frank A. Sortino

### Formula 10: Downside Deviation (σ_d)

**Purpose:** Measures the volatility of only the negative or below-target returns.

**Formula:**
```
σ_d = √[Σ min(0, R_i - MARR)² / n]
```

**Parameters:**
- `σ_d`: The downside deviation
- `n`: The total number of periods
- `R_i`: The return for the i-th period
- `MARR`: The Minimum Acceptable Rate of Return (e.g., 0% or risk-free rate)
- `min(0, ...)`: This function ensures that any period where `R_i > MARR` is counted as zero

**How It Works:**
1. For each period, calculate: `R_i - MARR`
2. If positive (good return), set to 0
3. If negative (bad return), square the difference
4. Average the squared differences and take the square root

**Example:**
```cpp
std::vector<double> returns = {0.15, -0.20, 0.30, -0.10, 0.25, -0.05};
double MARR = 0.00;  // 0% minimum acceptable return

std::vector<double> downsideSquared;
for (double r : returns) {
    double diff = r - MARR;
    if (diff < 0) {
        downsideSquared.push_back(diff * diff);
    } else {
        downsideSquared.push_back(0);  // Ignore positive returns
    }
}

// downsideSquared = [0, 0.04, 0, 0.01, 0, 0.0025]
double sumSquares = 0.0525;
double sigma_d = sqrt(sumSquares / returns.size());
// Result: ~0.0935 or 9.35% downside deviation
```

**Comparison with Standard Deviation:**
```cpp
// Standard deviation includes ALL volatility
double sigma = RiskAnalyzer::CalculateVolatility(returns);
// Result: ~0.185 or 18.5%

// Downside deviation only includes BAD volatility
// sigma_d = ~0.0935 or 9.35% (about half)

// This makes sense: only 3 out of 6 periods had negative returns
```

---

### Formula 11: Sortino Ratio

**Purpose:** Calculates risk-adjusted return using only downside deviation as the measure of risk.

**Formula:**
```
Sortino Ratio = (R_p - R_f) / σ_d
```

**Parameters:**
- `R_p`: The average return of the portfolio
- `R_f`: The risk-free rate (often used interchangeably with MARR)
- `σ_d`: The downside deviation from Formula 10

**Interpretation:**
- **Higher is better** (same as Sharpe Ratio)
- Sortino Ratio > Sharpe Ratio when returns are asymmetric (common in practice)
- Better measure for strategies with positive skew (more upside than downside)

**Thresholds (similar to Sharpe Ratio):**
- `< 1.0`: Poor - downside risk not worth it
- `1.0 - 1.99`: Good - adequately compensated for downside risk
- `≥ 2.0`: Excellent - well compensated for downside risk

**Example:**
```cpp
std::vector<double> returns = {0.15, -0.20, 0.30, -0.10, 0.25, -0.05};
double riskFreeRate = 0.02;  // 2% per period

// Calculate mean return
double avgReturn = RiskAnalyzer::CalculateMean(returns);  // 0.0583 or 5.83%

// Calculate Sharpe Ratio (Formula 6)
double sigma = RiskAnalyzer::CalculateVolatility(returns);  // 0.185
double sharpe = (avgReturn - riskFreeRate) / sigma;
// Sharpe = (0.0583 - 0.02) / 0.185 = 0.207 (Poor)

// Calculate Sortino Ratio (Formula 11)
double sigma_d = CalculateDownsideDeviation(returns, 0.02);  // 0.123
double sortino = (avgReturn - riskFreeRate) / sigma_d;
// Sortino = (0.0583 - 0.02) / 0.123 = 0.311 (Still poor, but better)

// Sortino > Sharpe because we ignore upside volatility
```

**When to Use:**
- Strategies with asymmetric returns (more upside potential)
- Options strategies (limited downside, unlimited upside)
- Hedge fund analysis
- When investors care more about downside protection than total volatility

**Source:** Frank A. Sortino and Robert van der Meer, "Downside Risk" (1991)

---

## 3. Value at Risk (VaR) - Parametric Method

### Background

Value at Risk (VaR) answers the question: "What is the maximum loss I can expect with X% confidence over the next N days?"

**Example:** "I am 95% confident I won't lose more than $10,000 next month."

### Formula 12: Value at Risk (Parametric Method)

**Purpose:** Quantifies the potential financial loss of a portfolio over a specific time frame, given a certain confidence level.

**Formula:**
```
VaR = |μ - Z × σ|
```

**Parameters:**
- `μ`: The average expected return for the period (often assumed to be 0 for short time frames)
- `σ`: The standard deviation (volatility) of the portfolio for the period
- `Z`: The Z-Score corresponding to the desired confidence level
- `|...|`: Absolute value, ensuring VaR is expressed as a positive loss amount

**Common Z-Scores:**
| Confidence Level | Z-Score | Interpretation |
|------------------|---------|----------------|
| 90% | 1.282 | 10% chance of exceeding this loss |
| 95% | 1.645 | 5% chance of exceeding this loss |
| 99% | 2.326 | 1% chance of exceeding this loss |

**Assumptions:**
1. Returns are normally distributed (Gaussian)
   - **Limitation:** Real markets have "fat tails" (extreme events more common than normal distribution predicts)
2. Historical volatility predicts future volatility
   - **Limitation:** Volatility changes over time
3. Portfolio composition remains constant
   - **Limitation:** Positions change, correlations change

**Example 1: Daily VaR**
```cpp
// Portfolio: $100,000
// Daily volatility: 2% (σ = 0.02)
// Confidence level: 95% (Z = 1.645)
// Assume μ = 0 for short-term

double portfolioValue = 100000.0;
double dailySigma = 0.02;
double Z_95 = 1.645;

double VaR_percentage = Z_95 * dailySigma;
// VaR = 1.645 × 0.02 = 0.0329 or 3.29%

double VaR_dollars = portfolioValue * VaR_percentage;
// VaR = $100,000 × 0.0329 = $3,290

// Interpretation: "I am 95% confident I won't lose more than $3,290 tomorrow"
```

**Example 2: Monthly VaR**
```cpp
// Same portfolio, but 1-month horizon
// Annual volatility: 20% (σ_annual = 0.20)
// Convert to monthly: σ_monthly = 0.20 / √12 = 0.0577

double monthlyVol = 0.20 / sqrt(12);  // 0.0577
double Z_99 = 2.326;  // 99% confidence

double VaR_percentage = Z_99 * monthlyVol;
// VaR = 2.326 × 0.0577 = 0.1342 or 13.42%

double VaR_dollars = 100000.0 * VaR_percentage;
// VaR = $100,000 × 0.1342 = $13,420

// Interpretation: "I am 99% confident I won't lose more than $13,420 next month"
```

**Time Scaling (Square Root of Time Rule):**
```
σ_t = σ_daily × √t

Examples:
- σ_weekly = σ_daily × √5
- σ_monthly = σ_daily × √21
- σ_annual = σ_daily × √252
```

**Example 3: Implementation**
```cpp
double CalculateVaR(double portfolioValue, double volatility,
                    double confidenceLevel, double expectedReturn = 0.0) {
    // Map confidence level to Z-score
    double Z;
    if (confidenceLevel == 0.90) Z = 1.282;
    else if (confidenceLevel == 0.95) Z = 1.645;
    else if (confidenceLevel == 0.99) Z = 2.326;
    else throw std::invalid_argument("Unsupported confidence level");

    // Calculate VaR percentage
    double VaR_pct = abs(expectedReturn - Z * volatility);

    // Convert to dollar amount
    return portfolioValue * VaR_pct;
}

// Usage
double var95 = CalculateVaR(100000.0, 0.02, 0.95);
std::cout << "95% 1-day VaR: $" << var95 << std::endl;
// Output: "95% 1-day VaR: $3290"
```

**Limitations:**
1. **Assumes Normal Distribution**
   - Real markets have "fat tails" (2008 crisis was a "25-sigma event" - should be impossible)
   - Black Monday (1987): -22% in one day (should occur once every 10^50 years)

2. **Doesn't Capture Tail Risk**
   - VaR tells you the threshold, not how bad it can get beyond that
   - Use Conditional VaR (CVaR) or Expected Shortfall for tail risk

3. **Historical Data Dependence**
   - Based on historical volatility
   - Doesn't predict Black Swan events

**Alternative VaR Methods:**
- **Historical VaR:** Uses actual historical returns (no distribution assumption)
- **Monte Carlo VaR:** Simulates thousands of scenarios (more flexible)

**Use Cases:**
- Risk management and position sizing
- Regulatory capital requirements (banks must hold capital based on VaR)
- Portfolio stress testing
- Risk budgeting and limits

**Source:** J.P. Morgan, "RiskMetrics" (1994); Philippe Jorion, "Value at Risk" (2006)

---

## 4. Z-Score (Ratio Analysis)

### Background

The Z-Score is a fundamental statistical measure used in finance for:
- Identifying mean reversion opportunities
- Detecting anomalies in financial ratios
- Statistical arbitrage strategies
- Quantifying "how extreme" a current observation is

### Formula 13: Z-Score

**Purpose:** Quantifies how many standard deviations an observation is away from the mean of a data set.

**Formula:**
```
Z = (x - μ) / σ
```

**Parameters:**
- `Z`: The Z-Score (standardized value)
- `x`: The current observation (e.g., today's Gold/Silver ratio)
- `μ`: The historical average (mean) of the data set
- `σ`: The historical standard deviation of the data set

**Interpretation:**
| Z-Score | Meaning | Probability (Normal Distribution) |
|---------|---------|-----------------------------------|
| 0 | At the mean | 50% |
| ±1 | 1 standard deviation from mean | 68% within ±1 |
| ±2 | 2 standard deviations from mean | 95% within ±2 |
| ±3 | 3 standard deviations from mean | 99.7% within ±3 |
| > +3 | Extremely high (rare) | < 0.15% |
| < -3 | Extremely low (rare) | < 0.15% |

**Sign Interpretation:**
- `Z > 0`: Observation is above average
- `Z < 0`: Observation is below average
- `|Z| > 2`: Statistically significant deviation (potentially actionable)
- `|Z| > 3`: Extreme deviation (very rare, high potential for mean reversion)

**Example 1: Gold/Silver Ratio Analysis**
```cpp
// Historical data (20-year lookback)
double mean_ratio = 65.0;      // Historical average ratio
double sigma_ratio = 10.0;     // Historical standard deviation
double current_ratio = 80.0;   // Today's observed ratio

// Calculate Z-Score
double Z = (current_ratio - mean_ratio) / sigma_ratio;
// Z = (80 - 65) / 10 = 1.5

// Interpretation:
// Gold is 1.5 standard deviations more expensive than historical average
// This is elevated but not extreme (Z < 2)
// Moderate mean reversion opportunity
```

**Example 2: Volatility Z-Score (VIX)**
```cpp
// VIX (S&P 500 volatility index)
double mean_VIX = 15.0;       // Historical average VIX
double sigma_VIX = 5.0;       // Historical standard deviation
double current_VIX = 35.0;    // Today's VIX (during market stress)

// Calculate Z-Score
double Z = (current_VIX - mean_VIX) / sigma_VIX;
// Z = (35 - 15) / 5 = 4.0

// Interpretation:
// VIX is 4 standard deviations above normal (EXTREME fear)
// Probability of Z > 4: ~0.003% (very rare)
// Strong mean reversion opportunity (historically, VIX reverts to ~15)
```

**Example 3: P/E Ratio Analysis**
```cpp
// S&P 500 Price-to-Earnings (P/E) ratio
std::vector<double> historical_PE = {
    16.2, 18.5, 22.1, 15.8, 20.3, 17.9, 19.2, 24.5, 14.3, 21.7
};

// Calculate mean and standard deviation
double mean_PE = CalculateMean(historical_PE);      // 19.05
double sigma_PE = CalculateVolatility(historical_PE); // 3.12

// Current P/E ratio
double current_PE = 28.0;

// Calculate Z-Score
double Z = (current_PE - mean_PE) / sigma_PE;
// Z = (28.0 - 19.05) / 3.12 = 2.87

// Interpretation:
// Market is 2.87 standard deviations above historical average
// P/E is very elevated (approaching "expensive" territory)
// Probability of Z > 2.87: ~0.2% (rare)
```

**Example 4: Implementation**
```cpp
class ZScoreAnalyzer {
public:
    static double CalculateZScore(double currentValue,
                                   const std::vector<double>& historicalData) {
        if (historicalData.empty()) {
            throw std::invalid_argument("Historical data cannot be empty");
        }

        double mean = CalculateMean(historicalData);
        double sigma = CalculateVolatility(historicalData);

        if (sigma == 0) {
            throw std::invalid_argument("Standard deviation cannot be zero");
        }

        return (currentValue - mean) / sigma;
    }

    static std::string InterpretZScore(double Z) {
        if (abs(Z) < 1.0) return "Normal range (within 1σ)";
        else if (abs(Z) < 2.0) return "Moderate deviation (within 2σ)";
        else if (abs(Z) < 3.0) return "Significant deviation (within 3σ)";
        else return "EXTREME deviation (beyond 3σ) - Very rare!";
    }
};

// Usage
std::vector<double> historicalRatio = {65, 70, 63, 68, 72, 64, 69};
double currentRatio = 85.0;
double Z = ZScoreAnalyzer::CalculateZScore(currentRatio, historicalRatio);
std::cout << "Z-Score: " << Z << std::endl;
std::cout << ZScoreAnalyzer::InterpretZScore(Z) << std::endl;
```

**Trading Application (Mean Reversion Strategy):**
```cpp
// Simple mean reversion logic
if (Z > 2.0) {
    // Asset is 2+ standard deviations above mean
    // Consider: SELL or SHORT (expect reversion downward)
    std::cout << "Signal: Overvalued - Consider selling" << std::endl;
} else if (Z < -2.0) {
    // Asset is 2+ standard deviations below mean
    // Consider: BUY or LONG (expect reversion upward)
    std::cout << "Signal: Undervalued - Consider buying" << std::endl;
} else {
    // Within normal range
    std::cout << "Signal: Hold - No extreme deviation" << std::endl;
}
```

**Limitations:**
1. **Assumes Stationarity**
   - Historical mean and σ must be stable
   - If market regime changes, historical stats become irrelevant
   - Example: Interest rates in 2020s vs 1980s

2. **Assumes Normal Distribution**
   - Real financial data often has fat tails
   - Z-scores beyond ±3 are more common than normal distribution predicts

3. **Mean Reversion Not Guaranteed**
   - "This time is different" can be true
   - Structural changes invalidate historical statistics
   - Example: Tech stock P/E ratios before 2000 bubble

4. **Lookback Period Matters**
   - Short lookback: More reactive, but noisy
   - Long lookback: Smoother, but may miss regime changes
   - Common: 20-day, 50-day, 200-day lookbacks

**Use Cases:**
- Pairs trading and statistical arbitrage
- Relative value analysis (Gold vs Silver, stocks vs bonds)
- Market timing (P/E ratios, volatility)
- Anomaly detection in financial ratios
- Risk monitoring (identifying outlier positions)

**Source:** Standard statistical measure; widely used in quantitative finance

---

## Summary Table: All Advanced Formulas

| Formula # | Name | Purpose | Key Use Case |
|-----------|------|---------|--------------|
| **8** | Correlation Coefficient (ρ) | Measure how two assets move together | Diversification analysis |
| **9** | Portfolio Volatility (σ_p) | Calculate two-asset portfolio risk | Portfolio construction |
| **10** | Downside Deviation (σ_d) | Measure only negative volatility | Risk measurement |
| **11** | Sortino Ratio | Risk-adjusted return (downside only) | Performance evaluation |
| **12** | Value at Risk (VaR) | Maximum expected loss at confidence level | Risk management |
| **13** | Z-Score | Standard deviations from mean | Mean reversion, anomaly detection |

---

## Integration with Existing Framework

These advanced formulas build upon the foundational formulas in [DOCUMENTATION.md](DOCUMENTATION.md):

**Foundation (Formulas 1-7):**
- Future Value calculations (1-3)
- Variance and Volatility (4-5)
- Sharpe Ratio and Beta (6-7)

**Advanced (Formulas 8-13):**
- Modern Portfolio Theory (8-9) - extends volatility and correlation concepts
- Sortino Ratio (10-11) - improves on Sharpe Ratio
- Value at Risk (12) - applies volatility to risk quantification
- Z-Score (13) - statistical timing and analysis

---

## Critical Limitations (Repeated for Emphasis)

### All These Models Share Common Weaknesses:

1. **Historical Data ≠ Future Reality**
   - All parameters (μ, σ, ρ) are estimated from past data
   - Past performance does not guarantee future results

2. **Normal Distribution Assumption**
   - Most models assume Gaussian returns
   - Real markets have fat tails (extreme events are more common)
   - Black Monday 1987, 2008 Crisis, COVID-19 crash - all were "impossible" under normal distribution

3. **Parameter Instability**
   - Volatility changes over time (volatility clustering)
   - Correlations change (often increase to 1.0 during crises)
   - Mean returns are NOT stable

4. **Black Swan Events** (Nassim Taleb)
   - Unpredictable, high-impact events
   - No amount of historical analysis predicts them
   - Examples: 9/11, COVID-19, financial crises

### Correct Use of These Tools

✅ **DO USE FOR:**
- Understanding portfolio diversification benefits
- Quantifying historical risk characteristics
- Comparing risk-adjusted performance
- Setting risk limits and position sizes
- Identifying statistical anomalies

❌ **DO NOT USE FOR:**
- Guaranteeing maximum loss (VaR can be exceeded)
- Predicting future returns or volatility
- Assuming mean reversion will always occur
- Ignoring fundamental changes in market structure

---

## Implementation Roadmap

These formulas are candidates for implementation in the InvestTool framework:

**Priority 1 (High Value):**
- [ ] Formula 8: Correlation Coefficient - needed for diversification analysis
- [ ] Formula 9: Two-Asset Portfolio Volatility - core MPT functionality
- [ ] Formula 12: Value at Risk - standard risk management tool

**Priority 2 (Specialized):**
- [ ] Formula 13: Z-Score - useful for ratio analysis and timing
- [ ] Formula 10-11: Sortino Ratio - better alternative to Sharpe Ratio

**Suggested Class Structure:**
```cpp
// Extend RiskAnalyzer.h
class RiskAnalyzer {
public:
    // Existing methods (Formulas 4-7)
    // ...

    // New MPT methods (Formulas 8-9)
    static double CalculateCorrelation(
        const std::vector<double>& returns1,
        const std::vector<double>& returns2
    );

    static double CalculatePortfolioVolatility(
        double weight1, double sigma1,
        double weight2, double sigma2,
        double correlation
    );

    // New downside risk methods (Formulas 10-11)
    static double CalculateDownsideDeviation(
        const std::vector<double>& returns,
        double MARR = 0.0
    );

    static double CalculateSortinoRatio(
        const std::vector<double>& returns,
        double riskFreeRate,
        double MARR = 0.0
    );

    // Value at Risk (Formula 12)
    static double CalculateVaR(
        double portfolioValue,
        double volatility,
        double confidenceLevel,
        double expectedReturn = 0.0
    );

    // Statistical analysis (Formula 13)
    static double CalculateZScore(
        double currentValue,
        const std::vector<double>& historicalData
    );
};
```

---

## Sources and References

### Modern Portfolio Theory
- Harry Markowitz, "Portfolio Selection" (1952), Journal of Finance
- Harry Markowitz, Nobel Prize in Economics (1990)
- William F. Sharpe, "Capital Asset Prices: A Theory of Market Equilibrium" (1964)

### Sortino Ratio
- Frank A. Sortino and Robert van der Meer, "Downside Risk" (1991)
- Frank A. Sortino and Lee N. Price, "Performance Measurement in a Downside Risk Framework" (1994)

### Value at Risk
- J.P. Morgan, "RiskMetrics Technical Document" (1996)
- Philippe Jorion, "Value at Risk: The New Benchmark for Managing Financial Risk" (3rd Edition, 2006)
- Basel Committee on Banking Supervision guidelines

### Z-Score and Statistical Methods
- Standard statistical theory
- John C. Hull, "Options, Futures, and Other Derivatives" (multiple editions)
- Quantitative finance literature

### Black Swan Theory and Limitations
- Nassim Nicholas Taleb, "The Black Swan: The Impact of the Highly Improbable" (2007)
- Nassim Nicholas Taleb, "Antifragile: Things That Gain from Disorder" (2012)
- Nassim Nicholas Taleb, "Fooled by Randomness" (2001)

---

## License

This is an educational document describing standard financial formulas from public domain finance and statistics literature.
