"""
Notes Endpoint Stress Tests

Tests notes management endpoints under high load:
- Note creation
- Note retrieval
- Note updates
- Concurrent operations
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


class NotesStressTest(StressTestRunner):
    """Stress tests for notes endpoints"""
    
    def __init__(self, config: StressTestConfig):
        super().__init__(config)
        self.auth_token: str = ""
        self.lead_ids: List[str] = []
        self.note_ids: Dict[str, List[str]] = {}  # lead_id -> [note_ids]
        self._setup_auth_and_leads()
    
    def _setup_auth_and_leads(self):
        """Setup authentication and create test leads"""
        print("Setting up authentication and test leads...")
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
        
        # Create test leads
        print("Creating test leads...")
        for _ in range(10):
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
                        self.lead_ids.append(lead_id)
                        self.note_ids[lead_id] = []
            except Exception:
                pass
        
        print(f"✓ Setup complete with {len(self.lead_ids)} test leads")
    
    def _get_headers(self) -> Dict:
        """Get authorization headers"""
        return {'Authorization': f'Bearer {self.auth_token}'}
    
    def test_concurrent_note_creation(self, num_notes: int = 200):
        """Test concurrent note creation"""
        print(f"\n📝 Testing {num_notes} concurrent note creations...")
        
        if not self.lead_ids:
            raise Exception("No leads available for note creation")
        
        def create_note():
            import random
            lead_id = random.choice(self.lead_ids)
            note_data = TestDataGenerator.generate_note_data()
            
            response = requests.post(
                f"{self.config.base_url}/notes/{lead_id}/",
                json=note_data,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                note_id = response.json().get('id')
                if note_id:
                    self.note_ids[lead_id].append(note_id)
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(create_note, num_notes)
        self.print_metrics("Concurrent Note Creation")
        return metrics
    
    def test_concurrent_note_retrieval(self, num_requests: int = 150):
        """Test concurrent note retrieval"""
        print(f"\n📝 Testing {num_requests} concurrent note retrievals...")
        
        # Ensure we have notes
        if not any(self.note_ids.values()):
            print("Creating test notes first...")
            self.test_concurrent_note_creation(50)
        
        def get_notes():
            import random
            # Get notes for a random lead
            lead_id = random.choice(self.lead_ids)
            response = requests.get(
                f"{self.config.base_url}/notes/{lead_id}/",
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(get_notes, num_requests)
        self.print_metrics("Concurrent Note Retrieval (List)")
        return metrics
    
    def test_concurrent_single_note_retrieval(self, num_requests: int = 150):
        """Test concurrent single note retrieval"""
        print(f"\n📝 Testing {num_requests} concurrent single note retrievals...")
        
        # Ensure we have notes
        if not any(self.note_ids.values()):
            print("Creating test notes first...")
            self.test_concurrent_note_creation(50)
        
        def get_single_note():
            import random
            # Find a lead with notes
            leads_with_notes = [lid for lid, nids in self.note_ids.items() if nids]
            if not leads_with_notes:
                raise Exception("No notes available")
            
            lead_id = random.choice(leads_with_notes)
            note_id = random.choice(self.note_ids[lead_id])
            
            response = requests.get(
                f"{self.config.base_url}/notes/{lead_id}/{note_id}",
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(get_single_note, num_requests)
        self.print_metrics("Concurrent Single Note Retrieval")
        return metrics
    
    def test_concurrent_note_updates(self, num_updates: int = 100):
        """Test concurrent note updates"""
        print(f"\n📝 Testing {num_updates} concurrent note updates...")
        
        # Ensure we have notes
        if not any(self.note_ids.values()):
            print("Creating test notes first...")
            self.test_concurrent_note_creation(50)
        
        def update_note():
            import random
            # Find a lead with notes
            leads_with_notes = [lid for lid, nids in self.note_ids.items() if nids]
            if not leads_with_notes:
                raise Exception("No notes available")
            
            lead_id = random.choice(leads_with_notes)
            note_id = random.choice(self.note_ids[lead_id])
            
            update_data = {
                "content": f"Updated note content: {TestDataGenerator.random_string(50)}",
                "tags": random.sample(["FOLLOW_UP", "MEETING", "CALL", "EMAIL"], k=random.randint(1, 3))
            }
            
            response = requests.put(
                f"{self.config.base_url}/notes/{lead_id}/{note_id}",
                json=update_data,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(update_note, num_updates)
        self.print_metrics("Concurrent Note Updates")
        return metrics
    
    def test_notes_per_lead_stress(self, notes_per_lead: int = 50):
        """Test creating many notes for a single lead"""
        print(f"\n📝 Testing {notes_per_lead} notes for a single lead...")
        
        if not self.lead_ids:
            raise Exception("No leads available")
        
        lead_id = self.lead_ids[0]
        
        def create_note_for_lead():
            note_data = TestDataGenerator.generate_note_data()
            response = requests.post(
                f"{self.config.base_url}/notes/{lead_id}/",
                json=note_data,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(create_note_for_lead, notes_per_lead)
        self.print_metrics(f"Notes per Lead Stress ({notes_per_lead} notes)")
        return metrics
    
    def test_mixed_note_operations(self, duration: int = 30, requests_per_second: int = 15):
        """Test mixed note operations under sustained load"""
        print(f"\n📝 Testing mixed operations: {requests_per_second} req/s for {duration}s...")
        
        # Ensure we have notes
        if not any(self.note_ids.values()):
            print("Creating test notes first...")
            self.test_concurrent_note_creation(30)
        
        def mixed_operations():
            import random
            operation = random.choice(['create', 'read', 'update', 'list'])
            
            lead_id = random.choice(self.lead_ids)
            
            if operation == 'create':
                note_data = TestDataGenerator.generate_note_data()
                response = requests.post(
                    f"{self.config.base_url}/notes/{lead_id}/",
                    json=note_data,
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            elif operation == 'read' and self.note_ids.get(lead_id):
                note_id = random.choice(self.note_ids[lead_id])
                response = requests.get(
                    f"{self.config.base_url}/notes/{lead_id}/{note_id}",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            elif operation == 'update' and self.note_ids.get(lead_id):
                note_id = random.choice(self.note_ids[lead_id])
                update_data = {
                    "content": f"Updated: {TestDataGenerator.random_string(30)}"
                }
                response = requests.put(
                    f"{self.config.base_url}/notes/{lead_id}/{note_id}",
                    json=update_data,
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            else:  # list
                response = requests.get(
                    f"{self.config.base_url}/notes/{lead_id}/",
                    headers=self._get_headers(),
                    timeout=self.config.timeout
                )
            
            response.raise_for_status()
        
        metrics = self.sustained_load_test(mixed_operations, duration, requests_per_second)
        self.print_metrics("Mixed Note Operations")
        return metrics
    
    def test_note_retrieval_for_nonexistent_lead(self, num_attempts: int = 50):
        """Test handling of note operations on non-existent leads"""
        print(f"\n📝 Testing {num_attempts} operations on non-existent leads...")
        
        def invalid_operation():
            import uuid
            fake_lead_id = str(uuid.uuid4())
            response = requests.get(
                f"{self.config.base_url}/notes/{fake_lead_id}/",
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            # We expect 404 Not Found
            if response.status_code != 404:
                raise Exception(f"Expected 404, got {response.status_code}")
        
        metrics = self.run_concurrent_requests(invalid_operation, num_attempts)
        self.print_metrics("Non-existent Lead Handling")
        return metrics
    
    def test_bulk_note_creation_per_lead(self):
        """Test creating bulk notes for multiple leads"""
        print(f"\n📝 Testing bulk note creation across all leads...")
        
        if not self.lead_ids:
            raise Exception("No leads available")
        
        notes_per_lead = 20
        total_notes = len(self.lead_ids) * notes_per_lead
        
        print(f"Creating {notes_per_lead} notes for each of {len(self.lead_ids)} leads ({total_notes} total)...")
        
        def create_notes_for_all_leads():
            for lead_id in self.lead_ids:
                for _ in range(notes_per_lead):
                    note_data = TestDataGenerator.generate_note_data()
                    response = requests.post(
                        f"{self.config.base_url}/notes/{lead_id}/",
                        json=note_data,
                        headers=self._get_headers(),
                        timeout=self.config.timeout
                    )
                    response.raise_for_status()
        
        start_time = time.time()
        try:
            create_notes_for_all_leads()
            elapsed = time.time() - start_time
            
            print(f"\n{'='*60}")
            print(f"Bulk Note Creation Results")
            print(f"{'='*60}")
            print(f"Total notes created:   {total_notes}")
            print(f"Leads:                 {len(self.lead_ids)}")
            print(f"Notes per lead:        {notes_per_lead}")
            print(f"Total time:            {elapsed:.2f}s")
            print(f"Notes per second:      {total_notes/elapsed:.2f}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ Bulk creation failed: {e}")
            raise
    
    def run_all_tests(self):
        """Run all notes stress tests"""
        print("\n" + "="*60)
        print("NOTES ENDPOINT STRESS TESTS")
        print("="*60)
        
        results = {}
        
        try:
            results['concurrent_creation'] = self.test_concurrent_note_creation(200)
        except Exception as e:
            print(f"❌ Concurrent creation test failed: {e}")
        
        try:
            results['concurrent_retrieval'] = self.test_concurrent_note_retrieval(150)
        except Exception as e:
            print(f"❌ Concurrent retrieval test failed: {e}")
        
        try:
            results['single_note_retrieval'] = self.test_concurrent_single_note_retrieval(150)
        except Exception as e:
            print(f"❌ Single note retrieval test failed: {e}")
        
        try:
            results['concurrent_updates'] = self.test_concurrent_note_updates(100)
        except Exception as e:
            print(f"❌ Concurrent updates test failed: {e}")
        
        try:
            results['notes_per_lead'] = self.test_notes_per_lead_stress(50)
        except Exception as e:
            print(f"❌ Notes per lead test failed: {e}")
        
        try:
            results['mixed_operations'] = self.test_mixed_note_operations(30, 15)
        except Exception as e:
            print(f"❌ Mixed operations test failed: {e}")
        
        try:
            results['nonexistent_lead'] = self.test_note_retrieval_for_nonexistent_lead(50)
        except Exception as e:
            print(f"❌ Non-existent lead test failed: {e}")
        
        try:
            self.test_bulk_note_creation_per_lead()
        except Exception as e:
            print(f"❌ Bulk creation test failed: {e}")
        
        return results


def run_notes_stress_tests(base_url: str = "http://localhost:8000"):
    """Run notes stress tests"""
    config = StressTestConfig(base_url=base_url)
    test_suite = NotesStressTest(config)
    return test_suite.run_all_tests()


if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    run_notes_stress_tests(base_url)

# Made with Bob
