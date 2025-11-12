#include "FinancialCalculator.h"

double FinancialCalculator::CalculateFutureValue(double pmt, double i, int n) {
    if (pmt <= 0) {
        throw std::invalid_argument("Payment must be positive");
    }
    if (i <= 0) {
        throw std::invalid_argument("Interest rate must be positive");
    }
    if (n <= 0) {
        throw std::invalid_argument("Number of periods must be positive");
    }

    // FV = PMT * [(1 + i)^n - 1] / i
    double factor = std::pow(1.0 + i, n);
    return pmt * (factor - 1.0) / i;
}

double FinancialCalculator::CalculateRequiredPayment(double fv, double i, int n) {
    if (fv <= 0) {
        throw std::invalid_argument("Future value must be positive");
    }
    if (i <= 0) {
        throw std::invalid_argument("Interest rate must be positive");
    }
    if (n <= 0) {
        throw std::invalid_argument("Number of periods must be positive");
    }

    // PMT = FV * i / [(1 + i)^n - 1]
    double factor = std::pow(1.0 + i, n);
    return fv * i / (factor - 1.0);
}

double FinancialCalculator::CalculateRequiredPeriods(double fv, double pmt, double i) {
    if (fv <= 0) {
        throw std::invalid_argument("Future value must be positive");
    }
    if (pmt <= 0) {
        throw std::invalid_argument("Payment must be positive");
    }
    if (i <= 0) {
        throw std::invalid_argument("Interest rate must be positive");
    }

    // n = ln(1 + (FV * i / PMT)) / ln(1 + i)
    double numerator = std::log(1.0 + (fv * i / pmt));
    double denominator = std::log(1.0 + i);

    if (numerator <= 0) {
        throw std::invalid_argument("Goal cannot be reached with these parameters");
    }

    return numerator / denominator;
}

double FinancialCalculator::AnnualToMonthlyRate(double annualRate) {
    // Simple approximation: annual / 12
    // For exact: (1 + annual)^(1/12) - 1
    return annualRate / 12.0;
}

double FinancialCalculator::MonthlyToAnnualRate(double monthlyRate) {
    // Simple approximation: monthly * 12
    // For exact: (1 + monthly)^12 - 1
    return monthlyRate * 12.0;
}
