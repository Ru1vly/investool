"""
Phase 3: Specialized Agents

All 5 agents that power the multi-agent workflow:
1. Data Agent - RAG retrieval
2. Context Agent - Memory retrieval
3. Calculation Agent - Secure code execution
4. Narrative Agent - Multimodal report generation
5. Quality Agent - Validation and fact-checking
"""

from typing import Dict, Any, Optional
import re
import json
import logging
from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import guarded_iter_unpack_sequence
import google.generativeai as genai

from finrisk_ai.core.state import AgentState
from finrisk_ai.rag.hybrid_search import VectorDatabase, Document
from finrisk_ai.rag.graph_rag import GraphRAG
from finrisk_ai.memory.mem0_system import Mem0System

logger = logging.getLogger(__name__)


class DataAgent:
    """
    Phase 3.1: Data Agent - RAG Retrieval Node

    Responsible for fetching all necessary factual context using:
    - Advanced RAG pipeline (hybrid search + reranking)
    - GraphRAG for structural context
    """

    def __init__(
        self,
        vector_db: VectorDatabase,
        graph_rag: GraphRAG
    ):
        """
        Initialize Data Agent.

        Args:
            vector_db: Vector database for RAG
            graph_rag: Graph RAG system
        """
        self.vector_db = vector_db
        self.graph_rag = graph_rag
        logger.info("DataAgent initialized")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute Data Agent - fetch RAG and GraphRAG context.

        Args:
            state: Current agent state

        Returns:
            Dict with rag_context and graph_rag_context
        """
        logger.info(f"DataAgent executing for query: '{state.user_query}'")

        # 1. Run Advanced RAG pipeline
        rag_docs = self.vector_db.hybrid_search(
            query=state.user_query,
            top_k=5
        )

        # 2. Run GraphRAG pipeline
        graph_context = self.graph_rag.query(
            query=state.user_query,
            max_nodes=10
        )

        logger.info(f"Retrieved {len(rag_docs)} RAG documents and {len(graph_context.nodes)} graph nodes")

        return {
            "rag_context": rag_docs,
            "graph_rag_context": graph_context.nodes
        }


class ContextAgent:
    """
    Phase 3.2: Context Agent - Memory Retrieval Node

    Responsible for fetching all personalization context from Mem0 system.
    """

    def __init__(self, mem0_system: Mem0System):
        """
        Initialize Context Agent.

        Args:
            mem0_system: Mem0 memory system
        """
        self.mem0 = mem0_system
        logger.info("ContextAgent initialized")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute Context Agent - fetch user context from memory.

        Args:
            state: Current agent state

        Returns:
            Dict with user_preferences, user_history, and temporal_insights
        """
        logger.info(f"ContextAgent executing for user: {state.user_id}")

        # Fetch complete user context
        user_context = self.mem0.get_user_context(
            user_id=state.user_id,
            session_id=state.session_id
        )

        # Add current query to session memory
        self.mem0.add_message(
            user_id=state.user_id,
            session_id=state.session_id,
            role="user",
            content=state.user_query
        )

        logger.info(f"Retrieved context: {user_context.preferences.reporting_style} style, "
                   f"{len(user_context.history)} recent activities")

        return {
            "user_preferences": user_context.preferences,
            "user_history": [
                {
                    "type": act.activity_type,
                    "timestamp": act.timestamp.isoformat(),
                    "content": act.content
                }
                for act in user_context.history
            ],
            "temporal_insights": user_context.temporal_insights
        }


class CalculationAgent:
    """
    Phase 3.3: Calculation Agent - Code Execution Node

    Performs all mathematics accurately using code delegation, not LLM reasoning.
    Uses Gemini Pro for code generation and secure sandbox for execution.
    """

    def __init__(self, gemini_api_key: str, model: str = "gemini-1.5-pro-latest"):
        """
        Initialize Calculation Agent.

        Args:
            gemini_api_key: Google Gemini API key
            model: Gemini model to use
        """
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(model)
        logger.info(f"CalculationAgent initialized with {model}")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute Calculation Agent - generate and execute Python code for calculations.

        Args:
            state: Current agent state

        Returns:
            Dict with calculation_code and calculation_results
        """
        logger.info("CalculationAgent executing...")

        # 1. Create prompt for code generation
        rag_data_summary = "\n".join([
            f"- {doc.content[:200]}..." for doc in state.rag_context[:3]
        ])

        prompt = f"""
Based on the user query: '{state.user_query}'

And the available data:
{rag_data_summary}

Generate a Python script to calculate all necessary financial metrics.
Use these formulas from InvestTool if applicable:
- Variance (Formula 4): σ² = Σ(R_j - R̄)² / (N - 1)
- Volatility (Formula 5): σ = √(Variance)
- Sharpe Ratio (Formula 6): (R_p - R_f) / σ_p
- Sortino Ratio (Formula 11): (R_p - R_f) / σ_d
- Value at Risk (Formula 12): |μ - Z × σ|
- Z-Score (Formula 13): (x - μ) / σ

Requirements:
1. Define a function called `calculate()` that returns a dictionary
2. Only output raw Python code, no markdown, no explanations
3. Print the results as JSON: print(json.dumps(results))
4. Handle errors gracefully

Example output format:
```python
import json
import math

def calculate():
    # Your calculations here
    results = {{
        "volatility": 0.15,
        "sharpe_ratio": 1.2,
        "var_95": 5000
    }}
    return results

if __name__ == "__main__":
    result = calculate()
    print(json.dumps(result))
```

Generate the code now:
"""

        # 2. Generate code using Gemini Pro
        try:
            response = self.model.generate_content(prompt)
            generated_code = response.text

            # Extract code from markdown if present
            code_match = re.search(r'```python\n(.*?)\n```', generated_code, re.DOTALL)
            if code_match:
                generated_code = code_match.group(1)

            logger.debug(f"Generated code:\n{generated_code}")

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {
                "calculation_code": "",
                "calculation_results": {},
                "calculation_error": f"Code generation failed: {str(e)}"
            }

        # 3. Execute code in secure sandbox
        try:
            results = self._execute_in_sandbox(generated_code)
            logger.info(f"Calculation results: {results}")

            return {
                "calculation_code": generated_code,
                "calculation_results": results,
                "calculation_error": None
            }

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return {
                "calculation_code": generated_code,
                "calculation_results": {},
                "calculation_error": f"Execution failed: {str(e)}"
            }

    def _execute_in_sandbox(self, code: str) -> Dict[str, float]:
        """
        Execute Python code in a restricted sandbox.

        This uses RestrictedPython to prevent dangerous operations.
        In production, use a more robust sandbox (Docker container, etc.)

        Args:
            code: Python code to execute

        Returns:
            Dictionary of calculation results
        """
        # Compile with RestrictedPython
        byte_code = compile_restricted(
            code,
            filename='<inline code>',
            mode='exec'
        )

        # Safe globals (only math, json allowed)
        safe_env = {
            '__builtins__': safe_globals,
            'json': json,
            'math': __import__('math'),
            '_getiter_': lambda x: iter(x),
            '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
            'printed_output': []
        }

        # Capture print output
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            # Execute the code
            exec(byte_code, safe_env)

            # Restore stdout
            sys.stdout = sys.__stdout__

            # Get output
            output = captured_output.getvalue()

            # Parse JSON result
            if output:
                # Find JSON in output
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    results = json.loads(json_match.group(0))
                    return results

            # If no JSON output, try to get from calculate() function
            if 'calculate' in safe_env:
                results = safe_env['calculate']()
                return results

            return {}

        finally:
            sys.stdout = sys.__stdout__


class NarrativeAgent:
    """
    Phase 3.4: Narrative Agent - Multimodal Report Generation Node

    Synthesizes all data into a personalized, multimodal financial analyst report.
    Uses Gemini Pro for high-level reasoning and narrative generation.
    """

    def __init__(self, gemini_api_key: str, model: str = "gemini-1.5-pro-latest"):
        """
        Initialize Narrative Agent.

        Args:
            gemini_api_key: Google Gemini API key
            model: Gemini model to use
        """
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(model)
        logger.info(f"NarrativeAgent initialized with {model}")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute Narrative Agent - generate personalized financial report.

        Steps:
        1. Macro-Planning (JSON structure)
        2. Chart Generation (Vega-Lite JSON)
        3. Multimodal Narrative Generation

        Args:
            state: Current agent state

        Returns:
            Dict with macro_plan_json, chart_json, and final_report_text
        """
        logger.info("NarrativeAgent executing...")

        # Step 1: Macro-Planning
        macro_plan = self._generate_macro_plan(state)

        # Step 2: Chart Generation
        chart_json = self._generate_chart(state)

        # Step 3: Final Narrative
        final_report = self._generate_narrative(state, macro_plan, chart_json)

        return {
            "macro_plan_json": macro_plan,
            "chart_json": chart_json,
            "final_report_text": final_report
        }

    def _generate_macro_plan(self, state: AgentState) -> Dict[str, Any]:
        """Generate macro plan for report structure"""

        prompt = f"""
You are a financial analyst. Based on:
- User query: {state.user_query}
- User preferences: {state.user_preferences.reporting_style if state.user_preferences else 'detailed'}
- Calculation results: {state.calculation_results}

Generate a JSON-only macro plan for the final report structure.

Example format:
{{
  "sections": [
    "Executive Summary",
    "Risk Analysis (VaR, Sortino)",
    "Market Context",
    "Recommendations"
  ],
  "tone": "professional",
  "length": "detailed"
}}

Output only valid JSON, no other text:
"""

        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {"sections": ["Summary", "Analysis", "Conclusion"], "tone": "professional"}

        except Exception as e:
            logger.error(f"Macro planning failed: {e}")
            return {"sections": ["Summary", "Analysis"], "tone": "professional"}

    def _generate_chart(self, state: AgentState) -> Dict[str, Any]:
        """Generate Vega-Lite chart specification"""

        if not state.calculation_results:
            return {}

        prompt = f"""
Based on these calculation results: {state.calculation_results}

Generate a Vega-Lite JSON specification for a bar chart or line chart.
Output only valid Vega-Lite JSON, no other text.

Example format:
{{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {{"values": [...]}},
  "mark": "bar",
  "encoding": {{
    "x": {{"field": "metric", "type": "nominal"}},
    "y": {{"field": "value", "type": "quantitative"}}
  }}
}}

Generate the specification now:
"""

        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {}

        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return {}

    def _generate_narrative(
        self,
        state: AgentState,
        macro_plan: Dict[str, Any],
        chart_json: Dict[str, Any]
    ) -> str:
        """Generate final narrative report"""

        # Format calculation results as HTML
        calc_results_html = "<table>\n"
        for metric, value in state.calculation_results.items():
            calc_results_html += f"  <tr><td>{metric}</td><td>{value:.4f}</td></tr>\n"
        calc_results_html += "</table>"

        # Format RAG context
        rag_context_text = "\n".join([
            f"- {doc.content[:300]}..." for doc in state.rag_context[:5]
        ])

        # Format temporal insights
        temporal_text = "\n".join([f"- {insight}" for insight in state.temporal_insights])

        prompt = f"""
You are a financial analyst writing a personalized report.

User preferences:
- Style: {state.user_preferences.reporting_style if state.user_preferences else 'detailed'}
- Risk tolerance: {state.user_preferences.risk_tolerance if state.user_preferences else 'moderate'}

User query: {state.user_query}

Follow this plan: {macro_plan.get('sections', [])}

Use these EXACT calculation results (formatted as HTML):
{calc_results_html}

Context from knowledge base:
{rag_context_text}

Temporal insights (trends over time):
{temporal_text}

{'Chart is provided: ' + str(chart_json) if chart_json else 'No chart available'}

Write a professional, comprehensive financial analyst report that:
1. Answers the user's query directly
2. Uses the exact numbers from the calculation results table
3. Provides context and interpretation
4. Includes recommendations based on risk tolerance
5. Cites specific metrics and their implications

Report:
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            return f"Error generating report: {str(e)}"


class QualityAgent:
    """
    Phase 3.5: Quality Agent - Validation and Fact-Checking Node

    Ensures the generated narrative matches calculation results and RAG context.
    Uses Gemini Flash for fast, rule-based checking.
    """

    def __init__(self, gemini_api_key: str, model: str = "gemini-1.5-flash-latest"):
        """
        Initialize Quality Agent.

        Args:
            gemini_api_key: Google Gemini API key
            model: Gemini model to use (Flash for speed)
        """
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(model)
        logger.info(f"QualityAgent initialized with {model}")

    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute Quality Agent - validate report against ground truth.

        Checks:
        1. All calculation results are mentioned correctly
        2. No hallucinated numbers
        3. Recommendations align with risk profile

        Args:
            state: Current agent state

        Returns:
            Dict with validation_passed and validation_errors
        """
        logger.info("QualityAgent executing...")

        errors = []

        # 1. Check that calculation results are present in report
        for metric, value in state.calculation_results.items():
            # Check if metric is mentioned
            if metric.lower().replace('_', ' ') not in state.final_report_text.lower():
                errors.append(f"Missing metric in report: {metric}")

            # Extract numbers from report
            numbers_in_report = re.findall(r'-?\d+\.?\d*', state.final_report_text)
            value_str = f"{value:.2f}"

            # Check if value is approximately present (allow for rounding)
            if not any(abs(float(num) - value) < 0.01 * abs(value) if value != 0 else abs(float(num)) < 0.01
                      for num in numbers_in_report if '.' in num):
                # This is a simplified check - in production, use more sophisticated matching
                logger.warning(f"Value {value} for {metric} may not be in report")

        # 2. LLM-based validation
        llm_validation_errors = self._llm_validate(state)
        errors.extend(llm_validation_errors)

        # Determine if validation passed
        validation_passed = len(errors) == 0

        if validation_passed:
            logger.info("✓ Quality validation passed")
        else:
            logger.warning(f"✗ Quality validation failed: {len(errors)} errors")

        return {
            "validation_passed": validation_passed,
            "validation_errors": errors
        }

    def _llm_validate(self, state: AgentState) -> list[str]:
        """Use LLM to validate report quality"""

        prompt = f"""
You are a quality assurance agent for financial reports.

Calculation results (ground truth):
{json.dumps(state.calculation_results, indent=2)}

Generated report:
{state.final_report_text}

Validation tasks:
1. Check if all metrics from calculation results are mentioned
2. Check if the numbers in the report match the calculation results
3. Check if there are any hallucinated numbers not in calculation results
4. Check if recommendations make sense

Output format (JSON only):
{{
  "all_metrics_present": true/false,
  "numbers_match": true/false,
  "no_hallucinations": true/false,
  "errors": ["error 1", "error 2", ...]
}}

Validation result:
"""

        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                validation_result = json.loads(json_match.group(0))
                return validation_result.get("errors", [])

        except Exception as e:
            logger.error(f"LLM validation failed: {e}")

        return []


def check_quality_gate(state: AgentState) -> str:
    """
    Conditional edge function for LangGraph.

    Determines whether to pass or retry based on validation results.

    Args:
        state: Current agent state

    Returns:
        "pass" or "fail"
    """
    if state.validation_passed:
        return "pass"
    elif state.retry_count >= 2:
        logger.warning("Max retries reached, proceeding despite validation failure")
        return "pass"  # Prevent infinite loop
    else:
        state.retry_count += 1
        return "fail"
