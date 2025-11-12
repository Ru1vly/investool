#include "StrategyBacktester.h"
#include <limits>
#include <algorithm>

BacktestResult StrategyBacktester::RunBacktest(
    const std::vector<double>& prices,
    StrategyType strategy,
    double initialCapital,
    const DCAConfig* dcaConfig,
    const MovingAverageCrossConfig* maConfig) {

    ValidatePrices(prices);

    if (initialCapital <= 0) {
        throw std::invalid_argument("Initial capital must be positive");
    }

    switch (strategy) {
        case StrategyType::DCA:
            if (dcaConfig == nullptr) {
                throw std::invalid_argument("DCA configuration required for DCA strategy");
            }
            return RunDCABacktest(prices, initialCapital, *dcaConfig);

        case StrategyType::MOVING_AVG_CROSS:
            if (maConfig == nullptr) {
                throw std::invalid_argument("MA configuration required for MA crossover strategy");
            }
            return RunMovingAverageCrossBacktest(prices, initialCapital, *maConfig);

        case StrategyType::BUY_AND_HOLD:
            return RunBuyAndHoldBacktest(prices, initialCapital);

        default:
            throw std::invalid_argument("Unknown strategy type");
    }
}

BacktestResult StrategyBacktester::RunDCABacktest(
    const std::vector<double>& prices,
    double initialCapital,
    const DCAConfig& config) {

    ValidatePrices(prices);

    if (config.investmentAmount <= 0) {
        throw std::invalid_argument("Investment amount must be positive");
    }
    if (config.frequency <= 0) {
        throw std::invalid_argument("Frequency must be positive");
    }

    // Initialize state
    double cash = initialCapital;
    double shares = 0.0;
    int totalTrades = 0;
    std::vector<PortfolioSnapshot> portfolioHistory;

    // Simulate each day
    for (size_t day = 0; day < prices.size(); ++day) {
        double currentPrice = prices[day];

        // Buy signal: invest on schedule
        if (day % config.frequency == 0 && cash >= config.investmentAmount) {
            double sharesBought = config.investmentAmount / currentPrice;
            shares += sharesBought;
            cash -= config.investmentAmount;
            totalTrades++;
        }

        // Record portfolio state
        double portfolioValue = cash + (shares * currentPrice);
        PortfolioSnapshot snapshot;
        snapshot.dayIndex = day;
        snapshot.portfolioValue = portfolioValue;
        snapshot.cash = cash;
        snapshot.shares = shares;
        snapshot.price = currentPrice;

        portfolioHistory.push_back(snapshot);
    }

    // Calculate metrics
    BacktestResult result;
    result.portfolioHistory = portfolioHistory;
    result.finalValue = portfolioHistory.back().portfolioValue;
    result.totalReturn = (result.finalValue - initialCapital) / initialCapital;
    result.annualizedReturn = CalculateAnnualizedReturn(result.totalReturn, prices.size());
    result.maxDrawdown = CalculateMaxDrawdown(portfolioHistory);
    result.totalTrades = totalTrades;

    return result;
}

BacktestResult StrategyBacktester::RunMovingAverageCrossBacktest(
    const std::vector<double>& prices,
    double initialCapital,
    const MovingAverageCrossConfig& config) {

    ValidatePrices(prices);

    if (config.shortPeriod <= 0 || config.longPeriod <= 0) {
        throw std::invalid_argument("MA periods must be positive");
    }
    if (config.shortPeriod >= config.longPeriod) {
        throw std::invalid_argument("Short period must be less than long period");
    }

    // Calculate moving averages
    std::vector<double> shortMA = CalculateMovingAverage(prices, config.shortPeriod);
    std::vector<double> longMA = CalculateMovingAverage(prices, config.longPeriod);

    // Initialize state
    double cash = initialCapital;
    double shares = 0.0;
    bool isInvested = false;
    int totalTrades = 0;
    std::vector<PortfolioSnapshot> portfolioHistory;

    // Simulate each day
    for (size_t day = 0; day < prices.size(); ++day) {
        double currentPrice = prices[day];
        bool buySignal = false;
        bool sellSignal = false;

        // Only check signals after both MAs are valid
        if (day >= static_cast<size_t>(config.longPeriod - 1)) {
            double currentShortMA = shortMA[day];
            double currentLongMA = longMA[day];

            // Check for crossover
            if (day > static_cast<size_t>(config.longPeriod - 1)) {
                double prevShortMA = shortMA[day - 1];
                double prevLongMA = longMA[day - 1];

                // Golden Cross: Short MA crosses above Long MA
                if (prevShortMA <= prevLongMA && currentShortMA > currentLongMA && !isInvested) {
                    buySignal = true;
                }
                // Death Cross: Short MA crosses below Long MA
                else if (prevShortMA >= prevLongMA && currentShortMA < currentLongMA && isInvested) {
                    sellSignal = true;
                }
            }
        }

        // Execute trades
        if (buySignal && cash > 0) {
            shares = cash / currentPrice;  // Go all-in
            cash = 0;
            isInvested = true;
            totalTrades++;
        } else if (sellSignal && shares > 0) {
            cash = shares * currentPrice;  // Sell all
            shares = 0;
            isInvested = false;
            totalTrades++;
        }

        // Record portfolio state
        double portfolioValue = cash + (shares * currentPrice);
        PortfolioSnapshot snapshot;
        snapshot.dayIndex = day;
        snapshot.portfolioValue = portfolioValue;
        snapshot.cash = cash;
        snapshot.shares = shares;
        snapshot.price = currentPrice;

        portfolioHistory.push_back(snapshot);
    }

    // Calculate metrics
    BacktestResult result;
    result.portfolioHistory = portfolioHistory;
    result.finalValue = portfolioHistory.back().portfolioValue;
    result.totalReturn = (result.finalValue - initialCapital) / initialCapital;
    result.annualizedReturn = CalculateAnnualizedReturn(result.totalReturn, prices.size());
    result.maxDrawdown = CalculateMaxDrawdown(portfolioHistory);
    result.totalTrades = totalTrades;

    return result;
}

BacktestResult StrategyBacktester::RunBuyAndHoldBacktest(
    const std::vector<double>& prices,
    double initialCapital) {

    ValidatePrices(prices);

    if (initialCapital <= 0) {
        throw std::invalid_argument("Initial capital must be positive");
    }

    // Buy all shares on day 0
    double firstPrice = prices[0];
    double shares = initialCapital / firstPrice;
    double cash = 0.0;

    std::vector<PortfolioSnapshot> portfolioHistory;

    // Simulate each day
    for (size_t day = 0; day < prices.size(); ++day) {
        double currentPrice = prices[day];
        double portfolioValue = cash + (shares * currentPrice);

        PortfolioSnapshot snapshot;
        snapshot.dayIndex = day;
        snapshot.portfolioValue = portfolioValue;
        snapshot.cash = cash;
        snapshot.shares = shares;
        snapshot.price = currentPrice;

        portfolioHistory.push_back(snapshot);
    }

    // Calculate metrics
    BacktestResult result;
    result.portfolioHistory = portfolioHistory;
    result.finalValue = portfolioHistory.back().portfolioValue;
    result.totalReturn = (result.finalValue - initialCapital) / initialCapital;
    result.annualizedReturn = CalculateAnnualizedReturn(result.totalReturn, prices.size());
    result.maxDrawdown = CalculateMaxDrawdown(portfolioHistory);
    result.totalTrades = 1;  // One initial buy

    return result;
}

std::vector<double> StrategyBacktester::CalculateMovingAverage(
    const std::vector<double>& prices,
    int period) {

    if (prices.empty()) {
        throw std::invalid_argument("Prices cannot be empty");
    }
    if (period <= 0) {
        throw std::invalid_argument("Period must be positive");
    }
    if (static_cast<size_t>(period) > prices.size()) {
        throw std::invalid_argument("Period cannot be larger than price data");
    }

    std::vector<double> ma(prices.size(), 0.0);

    // Calculate MA for each position
    for (size_t i = 0; i < prices.size(); ++i) {
        if (i < static_cast<size_t>(period - 1)) {
            // Not enough data yet, set to 0 (or could use NaN)
            ma[i] = 0.0;
        } else {
            // Calculate average of last 'period' prices
            double sum = 0.0;
            for (int j = 0; j < period; ++j) {
                sum += prices[i - j];
            }
            ma[i] = sum / period;
        }
    }

    return ma;
}

double StrategyBacktester::CalculateMaxDrawdown(
    const std::vector<PortfolioSnapshot>& portfolioHistory) {

    if (portfolioHistory.empty()) {
        return 0.0;
    }

    double maxValue = portfolioHistory[0].portfolioValue;
    double maxDrawdown = 0.0;

    for (const auto& snapshot : portfolioHistory) {
        double currentValue = snapshot.portfolioValue;

        // Update peak
        if (currentValue > maxValue) {
            maxValue = currentValue;
        }

        // Calculate drawdown from peak
        double drawdown = (currentValue - maxValue) / maxValue;

        // Update max drawdown (most negative)
        if (drawdown < maxDrawdown) {
            maxDrawdown = drawdown;
        }
    }

    return maxDrawdown;
}

double StrategyBacktester::CalculateAnnualizedReturn(
    double totalReturn,
    int numDays) {

    if (numDays <= 0) {
        throw std::invalid_argument("Number of days must be positive");
    }

    // Annualized Return = (1 + Total Return)^(365/numDays) - 1
    double years = numDays / 365.0;
    return std::pow(1.0 + totalReturn, 1.0 / years) - 1.0;
}

void StrategyBacktester::ValidatePrices(const std::vector<double>& prices) {
    if (prices.empty()) {
        throw std::invalid_argument("Prices cannot be empty");
    }

    for (double price : prices) {
        if (price <= 0) {
            throw std::invalid_argument("All prices must be positive");
        }
    }
}
