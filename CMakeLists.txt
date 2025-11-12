cmake_minimum_required(VERSION 3.10)

project(investool VERSION 1.0.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add executable
add_executable(investool
    main.cpp
    FinancialCalculator.cpp
    RiskAnalyzer.cpp
    AssetClassifier.cpp
    PortfolioOptimizer.cpp
    StrategyBacktester.cpp
    RatioAnalyzer.cpp
)
