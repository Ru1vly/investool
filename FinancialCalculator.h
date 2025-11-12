#ifndef FINANCIAL_CALCULATOR_H
#define FINANCIAL_CALCULATOR_H

#include <cmath>
#include <stdexcept>

/**
 * FinancialCalculator - Implements Future Value of Annuity calculations
 *
 * These formulas calculate outcomes for Dollar-Cost Averaging (DCA) strategies
 * where a fixed amount is invested at regular intervals.
 *
 * WARNING: These calculations assume constant returns, which is NOT realistic
 * in actual markets. Use for planning purposes only, not prediction.
 */
class FinancialCalculator {
public:
    /**
     * Formula 1: Calculate Future Value (FV)
     *
     * FV = PMT * [(1 + i)^n - 1] / i
     *
     * @param pmt Payment per period (e.g., 20,000 TL monthly)
     * @param i Interest rate per period (e.g., 0.01 for 1% monthly)
     * @param n Number of periods (e.g., 7 months)
     * @return Future Value - total amount at end of period
     *
     * Example: CalculateFutureValue(20000, 0.01, 7) = ~145,000 TL
     */
    static double CalculateFutureValue(double pmt, double i, int n);

    /**
     * Formula 2: Calculate Required Payment (PMT)
     *
     * PMT = FV * i / [(1 + i)^n - 1]
     *
     * @param fv Target Future Value (e.g., 200,000 TL)
     * @param i Interest rate per period
     * @param n Number of periods
     * @return Required payment per period to reach goal
     *
     * Example: CalculateRequiredPayment(200000, 0.01, 7) = ~27,500 TL/month
     */
    static double CalculateRequiredPayment(double fv, double i, int n);

    /**
     * Formula 3: Calculate Required Number of Periods (n)
     *
     * n = ln(1 + (FV * i / PMT)) / ln(1 + i)
     *
     * @param fv Target Future Value
     * @param pmt Payment per period
     * @param i Interest rate per period
     * @return Number of periods needed to reach goal
     *
     * Example: CalculateRequiredPeriods(200000, 20000, 0.01) = ~8.7 months
     */
    static double CalculateRequiredPeriods(double fv, double pmt, double i);

    /**
     * Convert annual rate to monthly rate
     * @param annualRate Annual interest rate (e.g., 0.12 for 12%)
     * @return Monthly interest rate
     */
    static double AnnualToMonthlyRate(double annualRate);

    /**
     * Convert monthly rate to annual rate
     * @param monthlyRate Monthly interest rate
     * @return Annual interest rate
     */
    static double MonthlyToAnnualRate(double monthlyRate);
};

#endif // FINANCIAL_CALCULATOR_H
