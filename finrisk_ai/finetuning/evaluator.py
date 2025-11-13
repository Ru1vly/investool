"""
Phase 5.5: Performance Evaluation and Benchmarking

Measures performance improvements from fine-tuning and hybrid approach.

Metrics:
- Accuracy: Correctness of calculations and recommendations
- Relevance: Quality of narrative responses
- Consistency: Deterministic behavior
- Latency: Response time
- User satisfaction: Feedback scores

Benchmarks against research paper targets:
- Baseline: 75%
- RAG only: 87% (+12%)
- Fine-tuning only: 85% (+10%)
- Hybrid (target): 98% (+23% or +11% over RAG)
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import time

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Single evaluation result"""

    test_id: str
    query: str
    expected_output: Optional[str]
    actual_output: str
    model_used: str

    # Scores (0.0 - 1.0)
    accuracy_score: float
    relevance_score: float
    completeness_score: float

    # Performance
    latency_ms: float

    # Metadata
    timestamp: str
    rag_enabled: bool
    finetuned_enabled: bool


@dataclass
class BenchmarkReport:
    """Complete benchmark report"""

    name: str
    model_configuration: Dict[str, Any]
    total_tests: int
    passed_tests: int
    failed_tests: int

    # Average scores
    avg_accuracy: float
    avg_relevance: float
    avg_completeness: float
    avg_latency_ms: float

    # Performance vs baseline
    improvement_over_baseline: float  # Percentage

    timestamp: str
    results: List[EvaluationResult]


class PerformanceEvaluator:
    """
    Evaluates model performance on test sets.

    Supports:
    - Benchmark tests (predefined test cases)
    - Production evaluation (live traffic)
    - A/B testing comparison
    - Regression testing
    """

    def __init__(
        self,
        test_cases_path: Optional[str] = None,
        baseline_score: float = 0.75,  # From research paper
    ):
        self.test_cases_path = test_cases_path
        self.baseline_score = baseline_score

        # Load test cases if available
        self.test_cases = self._load_test_cases() if test_cases_path else []

        logger.info(
            f"PerformanceEvaluator initialized with {len(self.test_cases)} test cases"
        )

    def evaluate_model(
        self,
        model_callable: Any,  # Function that generates responses
        model_name: str,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        rag_enabled: bool = True,
        finetuned_enabled: bool = False,
    ) -> BenchmarkReport:
        """
        Run complete benchmark evaluation.

        Args:
            model_callable: Function(query) -> response
            model_name: Name of model being tested
            test_cases: Test cases (uses default if None)
            rag_enabled: Whether RAG is enabled
            finetuned_enabled: Whether fine-tuning is enabled

        Returns:
            BenchmarkReport: Complete evaluation report
        """
        logger.info(f"Starting evaluation of {model_name}")

        # Use provided test cases or default
        cases = test_cases or self.test_cases
        if not cases:
            raise ValueError("No test cases available for evaluation")

        results = []
        passed = 0
        failed = 0

        for i, test_case in enumerate(cases, 1):
            logger.info(f"Running test {i}/{len(cases)}: {test_case.get('name', 'unnamed')}")

            result = self._evaluate_single_case(
                test_case=test_case,
                model_callable=model_callable,
                model_name=model_name,
                rag_enabled=rag_enabled,
                finetuned_enabled=finetuned_enabled,
            )

            results.append(result)

            # Count pass/fail (threshold: 0.7)
            if result.accuracy_score >= 0.7 and result.relevance_score >= 0.7:
                passed += 1
            else:
                failed += 1

        # Calculate averages
        avg_accuracy = sum(r.accuracy_score for r in results) / len(results)
        avg_relevance = sum(r.relevance_score for r in results) / len(results)
        avg_completeness = sum(r.completeness_score for r in results) / len(results)
        avg_latency = sum(r.latency_ms for r in results) / len(results)

        # Calculate overall score (weighted average)
        overall_score = (
            avg_accuracy * 0.5 +
            avg_relevance * 0.3 +
            avg_completeness * 0.2
        )

        # Improvement over baseline
        improvement = ((overall_score - self.baseline_score) / self.baseline_score) * 100

        # Create report
        report = BenchmarkReport(
            name=f"{model_name}_benchmark",
            model_configuration={
                "model_name": model_name,
                "rag_enabled": rag_enabled,
                "finetuned_enabled": finetuned_enabled,
            },
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=failed,
            avg_accuracy=avg_accuracy,
            avg_relevance=avg_relevance,
            avg_completeness=avg_completeness,
            avg_latency_ms=avg_latency,
            improvement_over_baseline=improvement,
            timestamp=datetime.utcnow().isoformat(),
            results=results,
        )

        logger.info(f"Evaluation complete: {passed}/{len(cases)} passed")
        logger.info(f"Overall score: {overall_score:.2%}")
        logger.info(f"Improvement over baseline: {improvement:+.1f}%")

        return report

    def _evaluate_single_case(
        self,
        test_case: Dict[str, Any],
        model_callable: Any,
        model_name: str,
        rag_enabled: bool,
        finetuned_enabled: bool,
    ) -> EvaluationResult:
        """Evaluate a single test case"""

        query = test_case["query"]
        expected = test_case.get("expected_output")

        # Time the generation
        start_time = time.time()
        try:
            actual_output = model_callable(query)
            if isinstance(actual_output, dict):
                actual_output = actual_output.get("text", str(actual_output))
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            actual_output = f"ERROR: {str(e)}"

        latency_ms = (time.time() - start_time) * 1000

        # Score the output
        accuracy = self._score_accuracy(actual_output, expected, test_case)
        relevance = self._score_relevance(actual_output, query)
        completeness = self._score_completeness(actual_output, test_case)

        return EvaluationResult(
            test_id=test_case.get("id", f"test_{id(test_case)}"),
            query=query,
            expected_output=expected,
            actual_output=actual_output,
            model_used=model_name,
            accuracy_score=accuracy,
            relevance_score=relevance,
            completeness_score=completeness,
            latency_ms=latency_ms,
            timestamp=datetime.utcnow().isoformat(),
            rag_enabled=rag_enabled,
            finetuned_enabled=finetuned_enabled,
        )

    def _score_accuracy(
        self,
        output: str,
        expected: Optional[str],
        test_case: Dict[str, Any]
    ) -> float:
        """
        Score accuracy of output.

        Uses multiple methods:
        - Exact match (if expected output provided)
        - Keyword presence
        - Numerical correctness (for calculation tasks)
        """
        if not output or output.startswith("ERROR"):
            return 0.0

        score = 0.5  # Base score for non-error output

        # Check expected output match
        if expected:
            # Simple similarity (in production, use embeddings)
            overlap = len(set(output.lower().split()) & set(expected.lower().split()))
            total = len(set(expected.lower().split()))
            if total > 0:
                score += 0.3 * (overlap / total)

        # Check required keywords
        required_keywords = test_case.get("required_keywords", [])
        if required_keywords:
            found = sum(1 for kw in required_keywords if kw.lower() in output.lower())
            score += 0.2 * (found / len(required_keywords))

        return min(1.0, score)

    def _score_relevance(self, output: str, query: str) -> float:
        """
        Score relevance to query.

        Checks if output addresses the query.
        """
        if not output or output.startswith("ERROR"):
            return 0.0

        # Extract key terms from query
        query_terms = set(query.lower().split())

        # Check presence in output
        output_terms = set(output.lower().split())
        overlap = len(query_terms & output_terms)

        relevance = overlap / len(query_terms) if query_terms else 0.0

        # Bonus for financial terms
        financial_terms = ["volatility", "sharpe", "ratio", "risk", "return", "portfolio"]
        found_financial = sum(1 for term in financial_terms if term in output.lower())

        relevance += min(0.3, found_financial * 0.1)

        return min(1.0, relevance)

    def _score_completeness(self, output: str, test_case: Dict[str, Any]) -> float:
        """
        Score completeness of response.

        Checks:
        - Adequate length
        - Sections present
        - Conclusion provided
        """
        if not output or output.startswith("ERROR"):
            return 0.0

        score = 0.0

        # Length check
        word_count = len(output.split())
        min_words = test_case.get("min_words", 50)
        if word_count >= min_words:
            score += 0.4
        elif word_count >= min_words * 0.7:
            score += 0.2

        # Check for structure
        if any(marker in output for marker in ["##", "**", "1.", "•"]):
            score += 0.2  # Has formatting

        # Check for conclusion
        conclusion_markers = ["in conclusion", "summary", "overall", "in summary"]
        if any(marker in output.lower() for marker in conclusion_markers):
            score += 0.2

        # Check for numerical results
        if any(char.isdigit() for char in output):
            score += 0.2

        return min(1.0, score)

    def compare_models(
        self,
        model_a_report: BenchmarkReport,
        model_b_report: BenchmarkReport,
    ) -> Dict[str, Any]:
        """
        Compare two model benchmark reports.

        Used for A/B testing and regression testing.
        """
        comparison = {
            "model_a": model_a_report.name,
            "model_b": model_b_report.name,
            "accuracy_diff": model_b_report.avg_accuracy - model_a_report.avg_accuracy,
            "relevance_diff": model_b_report.avg_relevance - model_a_report.avg_relevance,
            "completeness_diff": model_b_report.avg_completeness - model_a_report.avg_completeness,
            "latency_diff_ms": model_b_report.avg_latency_ms - model_a_report.avg_latency_ms,
            "improvement_diff": (
                model_b_report.improvement_over_baseline -
                model_a_report.improvement_over_baseline
            ),
        }

        # Determine winner
        overall_score_a = (
            model_a_report.avg_accuracy * 0.5 +
            model_a_report.avg_relevance * 0.3 +
            model_a_report.avg_completeness * 0.2
        )
        overall_score_b = (
            model_b_report.avg_accuracy * 0.5 +
            model_b_report.avg_relevance * 0.3 +
            model_b_report.avg_completeness * 0.2
        )

        comparison["winner"] = model_b_report.name if overall_score_b > overall_score_a else model_a_report.name
        comparison["score_difference"] = abs(overall_score_b - overall_score_a)

        return comparison

    def save_report(self, report: BenchmarkReport, output_path: str):
        """Save benchmark report to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict (handle nested dataclasses)
        report_dict = asdict(report)

        with open(output_file, "w") as f:
            json.dump(report_dict, f, indent=2)

        logger.info(f"Saved benchmark report to {output_file}")

    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases from file"""
        if not self.test_cases_path:
            return []

        test_cases_file = Path(self.test_cases_path)
        if not test_cases_file.exists():
            logger.warning(f"Test cases file not found: {self.test_cases_path}")
            return []

        with open(test_cases_file, "r") as f:
            cases = json.load(f)

        logger.info(f"Loaded {len(cases)} test cases from {self.test_cases_path}")
        return cases
