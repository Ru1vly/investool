"""
Phase 1.1: Data Ingestion & HTML Serialization

Converts all numerical and textual data into AI-optimal HTML format
with comprehensive metadata enrichment for Gemini interpretation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime


@dataclass
class DataStatistics:
    """Statistical metadata for financial data"""
    mean: float
    median: float
    std: float
    min_val: float
    max_val: float
    count: int


@dataclass
class EnrichedDataPacket:
    """Enriched data packet with metadata and HTML representation"""
    html_content: str
    metadata: Dict[str, Any]
    source: str
    calculation_method: str
    timestamp: datetime
    statistics: DataStatistics


class DataIngestionEngine:
    """
    Handles conversion of raw financial data into AI-optimal format.

    Key Features:
    1. HTML Serialization - preserves structural context
    2. Metadata Enrichment - adds descriptive statistics
    3. Source Tracking - maintains data provenance
    """

    @staticmethod
    def calculate_statistics(data: List[float]) -> DataStatistics:
        """
        Calculate descriptive statistics for numerical data.

        Args:
            data: List of numerical values

        Returns:
            DataStatistics object with comprehensive stats
        """
        arr = np.array(data)
        return DataStatistics(
            mean=float(np.mean(arr)),
            median=float(np.median(arr)),
            std=float(np.std(arr)),
            min_val=float(np.min(arr)),
            max_val=float(np.max(arr)),
            count=len(arr)
        )

    @staticmethod
    def convert_dict_to_html(data: Dict[str, Any], title: str = "Data") -> str:
        """
        Convert dictionary data to HTML table format.

        Args:
            data: Dictionary of key-value pairs
            title: Table title

        Returns:
            HTML string representation
        """
        html = f'<table class="data-table">\n'
        html += f'  <caption>{title}</caption>\n'
        html += '  <thead>\n    <tr><th>Metric</th><th>Value</th></tr>\n  </thead>\n'
        html += '  <tbody>\n'

        for key, value in data.items():
            formatted_value = f"{value:.4f}" if isinstance(value, (float, np.floating)) else str(value)
            html += f'    <tr><td>{key}</td><td>{formatted_value}</td></tr>\n'

        html += '  </tbody>\n</table>'
        return html

    @staticmethod
    def convert_dataframe_to_html(df: pd.DataFrame, title: str = "Financial Data") -> str:
        """
        Convert pandas DataFrame to HTML table with proper formatting.

        Args:
            df: pandas DataFrame
            title: Table title

        Returns:
            HTML string representation
        """
        html = f'<div class="dataframe-container">\n'
        html += f'  <h3>{title}</h3>\n'

        # Use pandas built-in HTML conversion with custom styling
        html += df.to_html(
            classes='financial-table',
            float_format=lambda x: f'{x:.4f}',
            index=True,
            border=1
        )

        html += '</div>'
        return html

    @classmethod
    def enrich_data(
        cls,
        raw_data: Any,
        source_doc: str,
        calc_method: str,
        data_type: str = "dict",
        title: Optional[str] = None
    ) -> EnrichedDataPacket:
        """
        Main enrichment function - converts raw data to enriched packet.

        Args:
            raw_data: Raw financial data (dict, DataFrame, or list)
            source_doc: Source document/module name
            calc_method: Calculation method used
            data_type: Type of data ("dict", "dataframe", "timeseries")
            title: Optional title for the data

        Returns:
            EnrichedDataPacket with HTML and metadata
        """
        # Calculate statistics based on data type
        if data_type == "dict" and isinstance(raw_data, dict):
            numerical_values = [v for v in raw_data.values() if isinstance(v, (int, float))]
            stats = cls.calculate_statistics(numerical_values) if numerical_values else None
            html_table = cls.convert_dict_to_html(raw_data, title or "Metrics")

        elif data_type == "dataframe" and isinstance(raw_data, pd.DataFrame):
            numerical_cols = raw_data.select_dtypes(include=[np.number]).values.flatten()
            stats = cls.calculate_statistics(numerical_cols.tolist()) if len(numerical_cols) > 0 else None
            html_table = cls.convert_dataframe_to_html(raw_data, title or "Financial Data")

        elif data_type == "timeseries" and isinstance(raw_data, list):
            stats = cls.calculate_statistics(raw_data)
            df = pd.DataFrame({'Value': raw_data}, index=range(len(raw_data)))
            html_table = cls.convert_dataframe_to_html(df, title or "Time Series")

        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        # Create metadata packet
        metadata = {
            "data_type": data_type,
            "timestamp": datetime.now().isoformat(),
            "source": source_doc,
            "calculation": calc_method,
        }

        if stats:
            metadata["statistics"] = {
                "mean": stats.mean,
                "median": stats.median,
                "std": stats.std,
                "range": [stats.min_val, stats.max_val],
                "count": stats.count
            }

        # Create final enriched HTML
        enriched_html = f"""
<div class="enriched-data-packet">
  <metadata>
    <source>{source_doc}</source>
    <calculation>{calc_method}</calculation>
    <timestamp>{datetime.now().isoformat()}</timestamp>
    {f'<stats mean="{stats.mean:.4f}" median="{stats.median:.4f}" std="{stats.std:.4f}" />' if stats else ''}
  </metadata>
  <data>
    {html_table}
  </data>
</div>
"""

        return EnrichedDataPacket(
            html_content=enriched_html,
            metadata=metadata,
            source=source_doc,
            calculation_method=calc_method,
            timestamp=datetime.now(),
            statistics=stats
        )


# Example usage for C++ integration
class CppFinancialDataAdapter:
    """
    Adapter to convert C++ InvestTool calculations to enriched format.
    This bridges the existing C++ calculations with the AI system.
    """

    @staticmethod
    def from_risk_metrics(
        variance: float,
        volatility: float,
        sharpe_ratio: float,
        beta: float,
        asset_name: str
    ) -> EnrichedDataPacket:
        """Convert C++ RiskAnalyzer results to enriched format"""

        metrics = {
            "Asset": asset_name,
            "Variance (σ²)": variance,
            "Volatility (σ)": volatility,
            "Sharpe Ratio": sharpe_ratio,
            "Beta (β)": beta
        }

        return DataIngestionEngine.enrich_data(
            raw_data=metrics,
            source_doc="RiskAnalyzer.cpp",
            calc_method="Modern Portfolio Theory (Formulas 4-7)",
            data_type="dict",
            title=f"Risk Metrics: {asset_name}"
        )

    @staticmethod
    def from_premium_features(
        sortino_ratio: float,
        var_95: float,
        var_99: float,
        downside_deviation: float,
        z_score: float,
        asset_name: str,
        portfolio_value: float
    ) -> EnrichedDataPacket:
        """Convert C++ premium calculation results to enriched format"""

        metrics = {
            "Asset": asset_name,
            "Portfolio Value": portfolio_value,
            "Sortino Ratio": sortino_ratio,
            "Downside Deviation (σ_d)": downside_deviation,
            "VaR (95%)": var_95,
            "VaR (99%)": var_99,
            "Z-Score": z_score
        }

        return DataIngestionEngine.enrich_data(
            raw_data=metrics,
            source_doc="RiskAnalyzer.cpp / PortfolioOptimizer.cpp",
            calc_method="Advanced Risk Metrics (Formulas 10-13)",
            data_type="dict",
            title=f"Premium Risk Analysis: {asset_name}"
        )

    @staticmethod
    def from_efficient_frontier(
        optimal_weights: Dict[str, float],
        expected_return: float,
        portfolio_volatility: float,
        sharpe_ratio: float
    ) -> EnrichedDataPacket:
        """Convert C++ Efficient Frontier results to enriched format"""

        df = pd.DataFrame([
            {"Metric": "Expected Return", "Value": expected_return},
            {"Metric": "Portfolio Volatility", "Value": portfolio_volatility},
            {"Metric": "Sharpe Ratio", "Value": sharpe_ratio}
        ])

        # Add weights
        for asset, weight in optimal_weights.items():
            df = pd.concat([df, pd.DataFrame([{"Metric": f"Weight: {asset}", "Value": weight}])], ignore_index=True)

        return DataIngestionEngine.enrich_data(
            raw_data=df,
            source_doc="PortfolioOptimizer.cpp",
            calc_method="Monte Carlo Simulation - Efficient Frontier (MPT)",
            data_type="dataframe",
            title="Optimal Portfolio Allocation"
        )
