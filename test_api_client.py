#!/usr/bin/env python3
"""
Phase 3 API Test Client

Comprehensive test client for the FinRisk AI API.

Tests all endpoints:
- Health check
- User creation
- Report generation
- Knowledge indexing
- User context retrieval
"""

import requests
import json
import time
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_123"
TEST_SESSION_ID = "test_session_abc"


class FinRiskAPIClient:
    """Client for interacting with FinRisk AI API"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def create_user(
        self,
        user_id: str,
        risk_tolerance: str = "moderate",
        reporting_style: str = "detailed"
    ) -> Dict[str, Any]:
        """Create or update user preferences"""
        payload = {
            "user_id": user_id,
            "risk_tolerance": risk_tolerance,
            "reporting_style": reporting_style
        }
        response = self.session.post(f"{self.base_url}/v1/user", json=payload)
        response.raise_for_status()
        return response.json()

    def generate_report(
        self,
        user_query: str,
        user_id: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Generate financial analysis report"""
        payload = {
            "user_query": user_query,
            "user_id": user_id,
            "session_id": session_id
        }
        response = self.session.post(f"{self.base_url}/v1/report", json=payload)
        response.raise_for_status()
        return response.json()

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context from memory"""
        response = self.session.get(f"{self.base_url}/v1/user/{user_id}/context")
        response.raise_for_status()
        return response.json()

    def index_knowledge(self, documents: list) -> Dict[str, Any]:
        """Index documents into RAG system"""
        payload = {"documents": documents}
        response = self.session.post(f"{self.base_url}/v1/knowledge/index", json=payload)
        response.raise_for_status()
        return response.json()


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"  └─ {details}")


def test_health_check(client: FinRiskAPIClient) -> bool:
    """Test health check endpoint"""
    print_section("TEST 1: Health Check")

    try:
        result = client.health_check()

        print(f"Status: {result['status']}")
        print(f"Version: {result['version']}")
        print(f"C++ Engine: {'✓ Available' if result['cpp_engine_available'] else '✗ Not Available'}")
        print(f"\nComponents:")
        for component, status in result['components'].items():
            print(f"  - {component}: {status}")

        passed = result['status'] in ['healthy', 'degraded']
        print_result("Health Check", passed)
        return passed

    except Exception as e:
        print_result("Health Check", False, f"Error: {e}")
        return False


def test_user_creation(client: FinRiskAPIClient) -> bool:
    """Test user creation endpoint"""
    print_section("TEST 2: User Creation")

    try:
        result = client.create_user(
            user_id=TEST_USER_ID,
            risk_tolerance="moderate",
            reporting_style="detailed"
        )

        print(f"Response: {result['message']}")

        passed = result.get('success', False)
        print_result("User Creation", passed)
        return passed

    except Exception as e:
        print_result("User Creation", False, f"Error: {e}")
        return False


def test_knowledge_indexing(client: FinRiskAPIClient) -> bool:
    """Test knowledge indexing endpoint"""
    print_section("TEST 3: Knowledge Indexing")

    try:
        documents = [
            {
                "content": "The Sharpe Ratio measures risk-adjusted returns. Values above 1.0 indicate good performance.",
                "metadata": {"source": "test", "category": "risk_metrics"}
            },
            {
                "content": "Portfolio diversification reduces risk by spreading investments across different assets.",
                "metadata": {"source": "test", "category": "diversification"}
            }
        ]

        result = client.index_knowledge(documents)

        print(f"Response: {result['message']}")

        passed = result.get('success', False)
        print_result("Knowledge Indexing", passed)
        return passed

    except Exception as e:
        print_result("Knowledge Indexing", False, f"Error: {e}")
        return False


def test_report_generation(client: FinRiskAPIClient) -> bool:
    """Test report generation endpoint (requires GEMINI_API_KEY)"""
    print_section("TEST 4: Report Generation")

    try:
        print("Generating report (this may take 10-30 seconds)...")
        start_time = time.time()

        result = client.generate_report(
            user_query="Calculate the Sharpe ratio for a portfolio with monthly returns of 5%, -2%, 3%, 8%, -1%, 4%, 2%, 6%, -3%, 5% and explain what it means.",
            user_id=TEST_USER_ID,
            session_id=TEST_SESSION_ID
        )

        elapsed = time.time() - start_time

        print(f"\n✓ Report generated in {elapsed:.1f} seconds")
        print(f"\nCalculation Results:")
        for metric, value in result['calculation_results'].items():
            if isinstance(value, float):
                print(f"  - {metric}: {value:.4f}")
            else:
                print(f"  - {metric}: {value}")

        print(f"\nMetadata:")
        print(f"  - Validation Passed: {result['metadata']['validation_passed']}")
        print(f"  - Retry Count: {result['metadata']['retry_count']}")
        print(f"  - RAG Documents: {result['metadata']['rag_documents_retrieved']}")

        print(f"\nReport Preview (first 300 chars):")
        print(f"  {result['final_report_text'][:300]}...")

        passed = len(result['final_report_text']) > 100
        print_result("Report Generation", passed)
        return passed

    except Exception as e:
        print_result("Report Generation", False, f"Error: {e}")
        print("\nNote: Report generation requires GEMINI_API_KEY environment variable")
        return False


def test_user_context_retrieval(client: FinRiskAPIClient) -> bool:
    """Test user context retrieval endpoint"""
    print_section("TEST 5: User Context Retrieval")

    try:
        result = client.get_user_context(TEST_USER_ID)

        print(f"User ID: {result['user_id']}")
        print(f"Risk Tolerance: {result['risk_tolerance']}")
        print(f"Reporting Style: {result['reporting_style']}")
        print(f"Recent Activities: {len(result['recent_activities'])}")
        print(f"Temporal Insights: {len(result['temporal_insights'])}")

        if result['recent_activities']:
            print(f"\nLatest Activity:")
            latest = result['recent_activities'][0]
            print(f"  - Type: {latest['type']}")
            print(f"  - Timestamp: {latest['timestamp']}")

        passed = result['user_id'] == TEST_USER_ID
        print_result("User Context Retrieval", passed)
        return passed

    except Exception as e:
        print_result("User Context Retrieval", False, f"Error: {e}")
        return False


def main():
    """Run all API tests"""
    print("\n" + "="*80)
    print("  🚀 FinRisk AI API - Comprehensive Test Suite")
    print("="*80)
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print("\nIMPORTANT: Make sure the API server is running:")
    print("  python3 -m finrisk_ai.api.main")
    print("\nOr with uvicorn:")
    print("  uvicorn finrisk_ai.api.main:app --reload")

    # Wait for user confirmation
    input("\nPress Enter to start tests (or Ctrl+C to cancel)...")

    # Create client
    client = FinRiskAPIClient(API_BASE_URL)

    # Run tests
    results = []

    results.append(("Health Check", test_health_check(client)))
    results.append(("User Creation", test_user_creation(client)))
    results.append(("Knowledge Indexing", test_knowledge_indexing(client)))

    # Only run report generation if previous tests passed
    if all(r[1] for r in results):
        results.append(("Report Generation", test_report_generation(client)))
        results.append(("User Context Retrieval", test_user_context_retrieval(client)))
    else:
        print("\n⚠️  Skipping Report Generation (prerequisite tests failed)")

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        print_result(test_name, result)

    print("\n" + "="*80)
    if passed == total:
        print(f"  🎉 ALL TESTS PASSED ({passed}/{total})")
        print("="*80)
        print("\n✅ API is fully functional!")
        print("✅ All endpoints responding correctly!")
        print("\n📚 API Documentation: http://localhost:8000/docs")
        return 0
    else:
        print(f"  ⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        print("="*80)
        return 1


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("\n\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running:")
        print("  python3 -m finrisk_ai.api.main")
        sys.exit(1)
