#ifndef STRATEGY_BACKTESTER_H
#define STRATEGY_BACKTESTER_H

#include <vector>
#include <string>
#include <stdexcept>
#include <cmath>

/**
 * Enumeration of available backtesting strategies
 */
enum class StrategyType {
    DCA,                    // Dollar-Cost Averaging (fixed amount each period)
    MOVING_AVG_CROSS,       // Moving Average Crossover (Golden/Death Cross)
    BUY_AND_HOLD            // Simple buy and hold strategy
};

/**
 * Structure representing a single day's price data
 */
struct PricePoint {
    int dayIndex;           // Day number (0, 1, 2, ...)
    double price;           // Asset price
    double shortMA;         // Short-term moving average (if applicable)
    double longMA;          // Long-term moving average (if applicable)
};

/**
 * Structure representing portfolio state at a point in time
 */
struct PortfolioSnapshot {
    int dayIndex;           // Day number
    double portfolioValue;  // Total portfolio value (cash + holdings)
    double cash;            // Cash on hand
    double shares;          // Number of shares held
    double price;           // Current asset price
};

/**
 * Configuration for Dollar-Cost Averaging strategy
 */
struct DCAConfig {
    double investmentAmount;    // Amount to invest each period (e.g., $1000)
    int frequency;              // Frequency in days (e.g., 30 for monthly)
};

/**
 * Configuration for Moving Average Crossover strategy
 */
struct MovingAverageCrossConfig {
    int shortPeriod;        // Short MA period (e.g., 50 days)
    int longPeriod;         // Long MA period (e.g., 200 days)
};

/**
 * Results from a backtest simulation
 */
struct BacktestResult {
    std::vector<PortfolioSnapshot> portfolioHistory;  // Daily portfolio values
    double finalValue;                                 // Final portfolio value
    double totalReturn;                                // Total return (%)
    double annualizedReturn;                           // Annualized return (%)
    double maxDrawdown;                                // Maximum drawdown (%)
    int totalTrades;                                   // Number of trades executed
};

/**
 * StrategyBacktester - Simulate investment strategies on historical data
 *
 * Tests how different strategies would have performed using historical prices.
 *
 * WARNING: Past performance does NOT guarantee future results.
 * Historical backtests are subject to:
 * - Survivorship bias (only testing assets that survived)
 * - Look-ahead bias (if not careful with data)
 * - Overfitting (strategies that worked in past may not work in future)
 *
 * Use for educational purposes and strategy comparison only.
 */
class StrategyBacktester {
public:
    /**
     * Run a backtest simulation
     *
     * @param prices Historical price data
     * @param strategy Strategy type to test
     * @param initialCapital Starting cash amount
     * @param dcaConfig DCA configuration (if using DCA strategy)
     * @param maConfig MA configuration (if using MA crossover strategy)
     * @return BacktestResult containing performance metrics
     */
    static BacktestResult RunBacktest(
        const std::vector<double>& prices,
        StrategyType strategy,
        double initialCapital,
        const DCAConfig* dcaConfig = nullptr,
        const MovingAverageCrossConfig* maConfig = nullptr
    );

    /**
     * Run Dollar-Cost Averaging backtest
     *
     * Invests a fixed amount at regular intervals regardless of price.
     *
     * @param prices Historical price data
     * @param initialCapital Starting cash
     * @param config DCA configuration
     * @return BacktestResult
     */
    static BacktestResult RunDCABacktest(
        const std::vector<double>& prices,
        double initialCapital,
        const DCAConfig& config
    );

    /**
     * Run Moving Average Crossover backtest
     *
     * Buy signal: Short MA crosses above Long MA (Golden Cross)
     * Sell signal: Short MA crosses below Long MA (Death Cross)
     *
     * @param prices Historical price data
     * @param initialCapital Starting cash
     * @param config MA configuration
     * @return BacktestResult
     */
    static BacktestResult RunMovingAverageCrossBacktest(
        const std::vector<double>& prices,
        double initialCapital,
        const MovingAverageCrossConfig& config
    );

    /**
     * Run Buy and Hold backtest
     *
     * Simply buy at the first price and hold until the end.
     *
     * @param prices Historical price data
     * @param initialCapital Starting cash
     * @return BacktestResult
     */
    static BacktestResult RunBuyAndHoldBacktest(
        const std::vector<double>& prices,
        double initialCapital
    );

    /**
     * Calculate Simple Moving Average (SMA)
     *
     * @param prices Price data
     * @param period Number of periods for MA
     * @return Vector of moving averages (same length as prices, with NaN for early periods)
     */
    static std::vector<double> CalculateMovingAverage(
        const std::vector<double>& prices,
        int period
    );

    /**
     * Calculate maximum drawdown from portfolio history
     *
     * Maximum Drawdown = Maximum loss from a peak to a trough
     *
     * @param portfolioHistory Portfolio values over time
     * @return Maximum drawdown as a percentage (negative value)
     */
    static double CalculateMaxDrawdown(
        const std::vector<PortfolioSnapshot>& portfolioHistory
    );

    /**
     * Calculate annualized return
     *
     * @param totalReturn Total return (e.g., 0.50 for 50%)
     * @param numDays Number of days in the period
     * @return Annualized return
     */
    static double CalculateAnnualizedReturn(
        double totalReturn,
        int numDays
    );

private:
    /**
     * Validate price data
     */
    static void ValidatePrices(const std::vector<double>& prices);
};

#endif // STRATEGY_BACKTESTER_H
