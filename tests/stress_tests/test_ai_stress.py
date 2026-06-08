"""
AI Agent Stress Tests

Tests AI agent endpoints under high load:
- Query processing
- Lead search
- CSV processing
- Concurrent AI requests
"""
import requests
import time
from typing import List, Dict
from .config import (
    StressTestConfig,
    TestDataGenerator,
    StressTestRunner,
    TestMetrics
)


class AIStressTest(StressTestRunner):
    """Stress tests for AI agent endpoints"""
    
    def __init__(self, config: StressTestConfig):
        super().__init__(config)
        self.auth_token: str = ""
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup authentication for tests"""
        print("Setting up authentication...")
        user_data = TestDataGenerator.generate_user_data()
        
        # Register user
        reg_response = requests.post(
            f"{self.config.base_url}/auth/get-started",
            json=user_data,
            timeout=self.config.timeout
        )
        
        if reg_response.status_code != 200:
            # Try to login if user already exists
            login_response = requests.post(
                f"{self.config.base_url}/auth/login",
                data={
                    'username': user_data['email'],
                    'password': user_data['password']
                },
                timeout=self.config.timeout
            )
            if login_response.status_code == 200:
                self.auth_token = login_response.json()['access_token']
        else:
            # Login with new user
            login_response = requests.post(
                f"{self.config.base_url}/auth/login",
                data={
                    'username': user_data['email'],
                    'password': user_data['password']
                },
                timeout=self.config.timeout
            )
            self.auth_token = login_response.json()['access_token']
        
        print(f"✓ Authentication setup complete")
    
    def _get_headers(self) -> Dict:
        """Get authorization headers"""
        return {'Authorization': f'Bearer {self.auth_token}'}
    
    def test_health_check(self, num_requests: int = 100):
        """Test AI health check endpoint"""
        print(f"\n🤖 Testing {num_requests} AI health checks...")
        
        def check_health():
            response = requests.get(
                f"{self.config.base_url}/ai/health",
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(check_health, num_requests)
        self.print_metrics("AI Health Check")
        return metrics
    
    def test_concurrent_queries(self, num_queries: int = 50):
        """Test concurrent AI queries"""
        print(f"\n🤖 Testing {num_queries} concurrent AI queries...")
        
        queries = [
            "What are the best practices for lead generation?",
            "How can I improve my conversion rate?",
            "Tell me about my pipeline status",
            "What leads should I follow up with?",
            "Give me insights on my hot leads",
            "How many leads do I have in progress?",
            "What's the best way to qualify leads?",
            "Analyze my lead distribution",
            "Show me my recent leads",
            "What are common lead generation strategies?"
        ]
        
        def query_agent():
            import random
            query = random.choice(queries)
            response = requests.post(
                f"{self.config.base_url}/ai/query",
                json={"query": query},
                headers=self._get_headers(),
                timeout=self.config.timeout * 2  # AI queries take longer
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(query_agent, num_queries)
        self.print_metrics("Concurrent AI Queries")
        return metrics
    
    def test_lead_search_stress(self, num_searches: int = 30):
        """Test concurrent lead search requests"""
        print(f"\n🤖 Testing {num_searches} concurrent lead searches...")
        
        search_params = [
            {"industry": "Technology", "location": "San Francisco"},
            {"industry": "Healthcare", "location": "New York"},
            {"industry": "Finance", "location": "London"},
            {"industry": "E-commerce", "location": "Los Angeles"},
            {"industry": "Manufacturing", "location": "Chicago"},
        ]
        
        def search_leads():
            import random
            params = random.choice(search_params)
            response = requests.post(
                f"{self.config.base_url}/ai/search-leads",
                json=params,
                headers=self._get_headers(),
                timeout=self.config.timeout * 3  # Search takes longer
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(search_leads, num_searches)
        self.print_metrics("Concurrent Lead Searches")
        return metrics
    
    def test_csv_processing_stress(self, num_requests: int = 20):
        """Test concurrent CSV processing"""
        print(f"\n🤖 Testing {num_requests} concurrent CSV processing requests...")
        
        def process_csv():
            csv_content = TestDataGenerator.generate_csv_data(50)
            response = requests.post(
                f"{self.config.base_url}/ai/process-csv",
                json={
                    "csv_content": csv_content,
                    "filters": {"lead_status": "HOT"}
                },
                headers=self._get_headers(),
                timeout=self.config.timeout * 2
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(process_csv, num_requests)
        self.print_metrics("Concurrent CSV Processing")
        return metrics
    
    def test_long_running_queries(self, num_queries: int = 10):
        """Test long-running complex queries"""
        print(f"\n🤖 Testing {num_queries} long-running queries...")
        
        complex_queries = [
            "Search for technology leads in San Francisco and export to CSV",
            "Find healthcare companies in New York with decision makers and create a spreadsheet",
            "Analyze my pipeline and give me a detailed report with recommendations",
            "Search for e-commerce leads in major US cities and filter by company size",
            "Generate a comprehensive lead list for the finance industry in Europe",
        ]
        
        def long_query():
            import random
            query = random.choice(complex_queries)
            response = requests.post(
                f"{self.config.base_url}/ai/query",
                json={"query": query},
                headers=self._get_headers(),
                timeout=self.config.timeout * 4  # Very long timeout for complex queries
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(long_query, num_queries, max_workers=5)
        self.print_metrics("Long-running Complex Queries")
        return metrics
    
    def test_mixed_ai_operations(self, duration: int = 30, requests_per_second: int = 5):
        """Test mixed AI operations under sustained load"""
        print(f"\n🤖 Testing mixed AI operations: {requests_per_second} req/s for {duration}s...")
        
        def mixed_operations():
            import random
            operation = random.choice(['query', 'health', 'search'])
            
            if operation == 'query':
                queries = [
                    "What are my hot leads?",
                    "Show me leads in progress",
                    "Give me pipeline insights",
                    "How many leads do I have?"
                ]
                response = requests.post(
                    f"{self.config.base_url}/ai/query",
                    json={"query": random.choice(queries)},
                    headers=self._get_headers(),
                    timeout=self.config.timeout * 2
                )
            elif operation == 'health':
                response = requests.get(
                    f"{self.config.base_url}/ai/health",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            else:  # search
                industries = ["Technology", "Healthcare", "Finance", "E-commerce"]
                response = requests.post(
                    f"{self.config.base_url}/ai/search-leads",
                    json={"industry": random.choice(industries)},
                    headers=self._get_headers(),
                    timeout=self.config.timeout * 3
                )
            
            response.raise_for_status()
        
        metrics = self.sustained_load_test(mixed_operations, duration, requests_per_second)
        self.print_metrics("Mixed AI Operations")
        return metrics
    
    def test_query_response_time_distribution(self, num_queries: int = 50):
        """Test and analyze query response time distribution"""
        print(f"\n🤖 Testing query response time distribution ({num_queries} queries)...")
        
        queries = [
            "Quick question: how many leads?",
            "Tell me about my pipeline",
            "What are best practices for lead generation in the tech industry?",
            "Analyze my leads and provide detailed insights with recommendations",
            "Search for leads and create a comprehensive report",
        ]
        
        query_times = {query: [] for query in queries}
        
        for query in queries:
            for _ in range(num_queries // len(queries)):
                start_time = time.time()
                try:
                    response = requests.post(
                        f"{self.config.base_url}/ai/query",
                        json={"query": query},
                        headers=self._get_headers(),
                        timeout=self.config.timeout * 3
                    )
                    response.raise_for_status()
                    elapsed = time.time() - start_time
                    query_times[query].append(elapsed)
                except Exception as e:
                    print(f"Query failed: {e}")
        
        print(f"\n{'='*60}")
        print(f"Query Response Time Analysis")
        print(f"{'='*60}")
        
        for query, times in query_times.items():
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                print(f"\nQuery: {query[:50]}...")
                print(f"  Avg: {avg_time:.2f}s | Min: {min_time:.2f}s | Max: {max_time:.2f}s")
        
        print(f"{'='*60}\n")
    
    def test_error_handling(self, num_requests: int = 30):
        """Test AI error handling with invalid requests"""
        print(f"\n🤖 Testing {num_requests} error handling scenarios...")
        
        def invalid_request():
            import random
            scenarios = [
                # Empty query
                lambda: requests.post(
                    f"{self.config.base_url}/ai/query",
                    json={"query": ""},
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                ),
                # Invalid CSV
                lambda: requests.post(
                    f"{self.config.base_url}/ai/process-csv",
                    json={"csv_content": "invalid,csv,data\n1,2"},
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                ),
                # Missing required fields
                lambda: requests.post(
                    f"{self.config.base_url}/ai/search-leads",
                    json={},
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                ),
            ]
            
            response = random.choice(scenarios)()
            # We expect these to fail gracefully (4xx or 5xx)
            if response.status_code < 400:
                raise Exception(f"Expected error status, got {response.status_code}")
        
        metrics = self.run_concurrent_requests(invalid_request, num_requests)
        self.print_metrics("AI Error Handling")
        return metrics
    
    def run_all_tests(self):
        """Run all AI stress tests"""
        print("\n" + "="*60)
        print("AI AGENT STRESS TESTS")
        print("="*60)
        
        results = {}
        
        try:
            results['health_check'] = self.test_health_check(100)
        except Exception as e:
            print(f"❌ Health check test failed: {e}")
        
        try:
            results['concurrent_queries'] = self.test_concurrent_queries(50)
        except Exception as e:
            print(f"❌ Concurrent queries test failed: {e}")
        
        try:
            results['lead_search'] = self.test_lead_search_stress(30)
        except Exception as e:
            print(f"❌ Lead search test failed: {e}")
        
        try:
            results['csv_processing'] = self.test_csv_processing_stress(20)
        except Exception as e:
            print(f"❌ CSV processing test failed: {e}")
        
        try:
            results['long_queries'] = self.test_long_running_queries(10)
        except Exception as e:
            print(f"❌ Long queries test failed: {e}")
        
        try:
            results['mixed_operations'] = self.test_mixed_ai_operations(30, 5)
        except Exception as e:
            print(f"❌ Mixed operations test failed: {e}")
        
        try:
            self.test_query_response_time_distribution(50)
        except Exception as e:
            print(f"❌ Response time analysis failed: {e}")
        
        try:
            results['error_handling'] = self.test_error_handling(30)
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
        
        return results


def run_ai_stress_tests(base_url: str = "http://localhost:8000"):
    """Run AI stress tests"""
    config = StressTestConfig(base_url=base_url)
    test_suite = AIStressTest(config)
    return test_suite.run_all_tests()


if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    run_ai_stress_tests(base_url)

# Made with Bob
