"""
Leads Endpoint Stress Tests

Tests lead management endpoints under high load:
- Lead creation
- Lead retrieval
- Lead updates
- Bulk operations
- CSV uploads
"""
import requests
import time
import io
from typing import List, Dict
from .config import (
    StressTestConfig,
    TestDataGenerator,
    StressTestRunner,
    TestMetrics
)


class LeadsStressTest(StressTestRunner):
    """Stress tests for leads endpoints"""
    
    def __init__(self, config: StressTestConfig):
        super().__init__(config)
        self.auth_token: str = ""
        self.created_leads: List[str] = []
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
    
    def test_concurrent_lead_creation(self, num_leads: int = 200):
        """Test concurrent lead creation"""
        print(f"\n📊 Testing {num_leads} concurrent lead creations...")
        
        def create_lead():
            lead_data = TestDataGenerator.generate_lead_data()
            response = requests.post(
                f"{self.config.base_url}/leads/",
                json=lead_data,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                lead_id = response.json().get('id')
                if lead_id:
                    self.created_leads.append(lead_id)
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(create_lead, num_leads)
        self.print_metrics("Concurrent Lead Creation")
        return metrics
    
    def test_concurrent_lead_retrieval(self, num_requests: int = 300):
        """Test concurrent lead retrieval"""
        print(f"\n📊 Testing {num_requests} concurrent lead retrievals...")
        
        # Ensure we have leads to retrieve
        if not self.created_leads:
            print("Creating test leads first...")
            self.test_concurrent_lead_creation(50)
        
        def get_leads():
            response = requests.get(
                f"{self.config.base_url}/leads/",
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(get_leads, num_requests)
        self.print_metrics("Concurrent Lead Retrieval (List All)")
        return metrics
    
    def test_concurrent_single_lead_retrieval(self, num_requests: int = 200):
        """Test concurrent single lead retrieval"""
        print(f"\n📊 Testing {num_requests} concurrent single lead retrievals...")
        
        # Ensure we have leads
        if not self.created_leads:
            print("Creating test leads first...")
            self.test_concurrent_lead_creation(50)
        
        def get_single_lead():
            if not self.created_leads:
                raise Exception("No leads available")
            
            lead_id = self.created_leads[len(self.metrics.response_times) % len(self.created_leads)]
            response = requests.get(
                f"{self.config.base_url}/leads/{lead_id}",
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(get_single_lead, num_requests)
        self.print_metrics("Concurrent Single Lead Retrieval")
        return metrics
    
    def test_concurrent_lead_updates(self, num_updates: int = 150):
        """Test concurrent lead updates"""
        print(f"\n📊 Testing {num_updates} concurrent lead updates...")
        
        # Ensure we have leads
        if not self.created_leads:
            print("Creating test leads first...")
            self.test_concurrent_lead_creation(50)
        
        def update_lead():
            if not self.created_leads:
                raise Exception("No leads available")
            
            lead_id = self.created_leads[len(self.metrics.response_times) % len(self.created_leads)]
            update_data = {
                "pipeline_status": TestDataGenerator.random_pipeline_status(),
                "lead_status": TestDataGenerator.random_lead_status()
            }
            response = requests.put(
                f"{self.config.base_url}/leads/{lead_id}",
                json=update_data,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(update_lead, num_updates)
        self.print_metrics("Concurrent Lead Updates")
        return metrics
    
    def test_csv_upload_stress(self, num_uploads: int = 20, rows_per_csv: int = 100):
        """Test concurrent CSV uploads"""
        print(f"\n📊 Testing {num_uploads} concurrent CSV uploads ({rows_per_csv} rows each)...")
        
        def upload_csv():
            csv_content = TestDataGenerator.generate_csv_data(rows_per_csv)
            files = {
                'file': ('test_leads.csv', io.StringIO(csv_content), 'text/csv')
            }
            response = requests.post(
                f"{self.config.base_url}/leads/upload-csv",
                files=files,
                headers=self._get_headers(),
                timeout=self.config.timeout * 2  # CSV uploads take longer
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(upload_csv, num_uploads)
        self.print_metrics(f"CSV Upload Stress ({rows_per_csv} rows)")
        return metrics
    
    def test_large_csv_upload(self, num_rows: int = 1000):
        """Test single large CSV upload"""
        print(f"\n📊 Testing large CSV upload ({num_rows} rows)...")
        
        start_time = time.time()
        csv_content = TestDataGenerator.generate_csv_data(num_rows)
        files = {
            'file': ('large_test_leads.csv', io.StringIO(csv_content), 'text/csv')
        }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/leads/upload-csv",
                files=files,
                headers=self._get_headers(),
                timeout=self.config.timeout * 3
            )
            response.raise_for_status()
            
            elapsed = time.time() - start_time
            result = response.json()
            
            print(f"\n{'='*60}")
            print(f"Large CSV Upload Results")
            print(f"{'='*60}")
            print(f"Rows in CSV:           {num_rows}")
            print(f"Successfully imported: {result.get('successful', 0)}")
            print(f"Failed:                {result.get('failed', 0)}")
            print(f"Upload time:           {elapsed:.2f}s")
            print(f"Rows per second:       {num_rows/elapsed:.2f}")
            print(f"{'='*60}\n")
            
            return result
        except Exception as e:
            print(f"❌ Large CSV upload failed: {e}")
            raise
    
    def test_mixed_lead_operations(self, duration: int = 30, requests_per_second: int = 20):
        """Test mixed lead operations under sustained load"""
        print(f"\n📊 Testing mixed operations: {requests_per_second} req/s for {duration}s...")
        
        # Pre-create some leads
        print("Pre-creating test leads...")
        for _ in range(20):
            try:
                lead_data = TestDataGenerator.generate_lead_data()
                response = requests.post(
                    f"{self.config.base_url}/leads/",
                    json=lead_data,
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
                if response.status_code == 200:
                    lead_id = response.json().get('id')
                    if lead_id:
                        self.created_leads.append(lead_id)
            except Exception:
                pass
        
        def mixed_operations():
            import random
            operation = random.choice(['create', 'read', 'update', 'list'])
            
            if operation == 'create':
                lead_data = TestDataGenerator.generate_lead_data()
                response = requests.post(
                    f"{self.config.base_url}/leads/",
                    json=lead_data,
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            elif operation == 'read' and self.created_leads:
                lead_id = random.choice(self.created_leads)
                response = requests.get(
                    f"{self.config.base_url}/leads/{lead_id}",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            elif operation == 'update' and self.created_leads:
                lead_id = random.choice(self.created_leads)
                update_data = {
                    "pipeline_status": TestDataGenerator.random_pipeline_status()
                }
                response = requests.put(
                    f"{self.config.base_url}/leads/{lead_id}",
                    json=update_data,
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            else:  # list
                response = requests.get(
                    f"{self.config.base_url}/leads/",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            
            response.raise_for_status()
        
        metrics = self.sustained_load_test(mixed_operations, duration, requests_per_second)
        self.print_metrics("Mixed Lead Operations")
        return metrics
    
    def test_duplicate_lead_handling(self, num_attempts: int = 50):
        """Test handling of duplicate lead creation"""
        print(f"\n📊 Testing {num_attempts} duplicate lead creation attempts...")
        
        # Create one lead first
        lead_data = TestDataGenerator.generate_lead_data()
        requests.post(
            f"{self.config.base_url}/leads/",
            json=lead_data,
            headers=self._get_headers(),
            timeout=self.config.timeout
        )
        
        def create_duplicate():
            response = requests.post(
                f"{self.config.base_url}/leads/",
                json=lead_data,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            # We expect 400 Bad Request for duplicates
            if response.status_code != 400:
                raise Exception(f"Expected 400, got {response.status_code}")
        
        metrics = self.run_concurrent_requests(create_duplicate, num_attempts)
        self.print_metrics("Duplicate Lead Handling")
        return metrics
    
    def run_all_tests(self):
        """Run all leads stress tests"""
        print("\n" + "="*60)
        print("LEADS ENDPOINT STRESS TESTS")
        print("="*60)
        
        results = {}
        
        try:
            results['concurrent_creation'] = self.test_concurrent_lead_creation(200)
        except Exception as e:
            print(f"❌ Concurrent creation test failed: {e}")
        
        try:
            results['concurrent_retrieval'] = self.test_concurrent_lead_retrieval(300)
        except Exception as e:
            print(f"❌ Concurrent retrieval test failed: {e}")
        
        try:
            results['single_lead_retrieval'] = self.test_concurrent_single_lead_retrieval(200)
        except Exception as e:
            print(f"❌ Single lead retrieval test failed: {e}")
        
        try:
            results['concurrent_updates'] = self.test_concurrent_lead_updates(150)
        except Exception as e:
            print(f"❌ Concurrent updates test failed: {e}")
        
        try:
            results['csv_upload'] = self.test_csv_upload_stress(20, 100)
        except Exception as e:
            print(f"❌ CSV upload test failed: {e}")
        
        try:
            results['large_csv'] = self.test_large_csv_upload(1000)
        except Exception as e:
            print(f"❌ Large CSV test failed: {e}")
        
        try:
            results['mixed_operations'] = self.test_mixed_lead_operations(30, 20)
        except Exception as e:
            print(f"❌ Mixed operations test failed: {e}")
        
        try:
            results['duplicate_handling'] = self.test_duplicate_lead_handling(50)
        except Exception as e:
            print(f"❌ Duplicate handling test failed: {e}")
        
        return results


def run_leads_stress_tests(base_url: str = "http://localhost:8000"):
    """Run leads stress tests"""
    config = StressTestConfig(base_url=base_url)
    test_suite = LeadsStressTest(config)
    return test_suite.run_all_tests()


if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    run_leads_stress_tests(base_url)

# Made with Bob
