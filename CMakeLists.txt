cmake_minimum_required(VERSION 3.10)

project(investool VERSION 1.0.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add pybind11 subdirectory
add_subdirectory(external/pybind11)

# Define the core library sources (shared by both Python module and standalone executable)
set(INVESTOOL_CORE_SOURCES
    FinancialCalculator.cpp
    RiskAnalyzer.cpp
    AssetClassifier.cpp
    PortfolioOptimizer.cpp
    StrategyBacktester.cpp
    RatioAnalyzer.cpp
)

# ============================================================================
# Build Python Module (Primary Target)
# ============================================================================
# This builds the shared library that Python can import
pybind11_add_module(investool_engine bindings.cpp ${INVESTOOL_CORE_SOURCES})

# Set module properties
set_target_properties(investool_engine PROPERTIES
    OUTPUT_NAME "investool_engine"
    PREFIX "${PYTHON_MODULE_PREFIX}"
    SUFFIX "${PYTHON_MODULE_EXTENSION}"
)

# ============================================================================
# Build Standalone Executable (Optional, for testing)
# ============================================================================
# Uncomment the following lines if you want to build the standalone C++ executable
# add_executable(investool
#     main.cpp
#     ${INVESTOOL_CORE_SOURCES}
# )
