"""
Concurrent User Simulation Tests

Simulates realistic user behavior with multiple concurrent users:
- User registration and login
- Creating and managing leads
- Adding notes
- Using AI features
- Mixed realistic workflows
"""
import requests
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from .config import (
    StressTestConfig,
    TestDataGenerator,
    StressTestRunner,
    TestMetrics
)


@dataclass
class SimulatedUser:
    """Represents a simulated user"""
    email: str
    password: str
    token: Optional[str] = None
    lead_ids: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.lead_ids is None:
            self.lead_ids = []


class ConcurrentUserSimulation(StressTestRunner):
    """Simulate realistic concurrent user behavior"""
    
    def __init__(self, config: StressTestConfig):
        super().__init__(config)
        self.users: List[SimulatedUser] = []
    
    def _register_and_login_user(self) -> SimulatedUser:
        """Register and login a new user"""
        user_data = TestDataGenerator.generate_user_data()
        user = SimulatedUser(
            email=user_data['email'],
            password=user_data['password']
        )
        
        # Register
        try:
            requests.post(
                f"{self.config.base_url}/auth/get-started",
                json=user_data,
                timeout=self.config.timeout
            )
        except Exception:
            pass  # User might already exist
        
        # Login
        login_response = requests.post(
            f"{self.config.base_url}/auth/login",
            data={
                'username': user.email,
                'password': user.password
            },
            timeout=self.config.timeout
        )
        
        if login_response.status_code == 200:
            user.token = login_response.json()['access_token']
        
        return user
    
    def _user_workflow(self, user: SimulatedUser, actions: int = 10):
        """Simulate a realistic user workflow"""
        headers = {'Authorization': f'Bearer {user.token}'}
        
        for _ in range(actions):
            # Randomly choose an action
            action = random.choice([
                'create_lead',
                'view_leads',
                'update_lead',
                'add_note',
                'view_notes',
                'ai_query',
                'check_profile'
            ])
            
            try:
                if action == 'create_lead':
                    lead_data = TestDataGenerator.generate_lead_data()
                    response = requests.post(
                        f"{self.config.base_url}/leads/",
                        json=lead_data,
                        headers=headers,
                        timeout=self.config.timeout
                    )
                    if response.status_code == 200:
                        lead_id = response.json().get('id')
                        if lead_id:
                            user.lead_ids.append(lead_id)
                
                elif action == 'view_leads':
                    requests.get(
                        f"{self.config.base_url}/leads/",
                        headers=headers,
                        timeout=self.config.timeout
                    )
                
                elif action == 'update_lead' and user.lead_ids:
                    lead_id = random.choice(user.lead_ids)
                    update_data = {
                        "pipeline_status": TestDataGenerator.random_pipeline_status()
                    }
                    requests.put(
                        f"{self.config.base_url}/leads/{lead_id}",
                        json=update_data,
                        headers=headers,
                        timeout=self.config.timeout
                    )
                
                elif action == 'add_note' and user.lead_ids:
                    lead_id = random.choice(user.lead_ids)
                    note_data = TestDataGenerator.generate_note_data()
                    requests.post(
                        f"{self.config.base_url}/notes/{lead_id}/",
                        json=note_data,
                        headers=headers,
                        timeout=self.config.timeout
                    )
                
                elif action == 'view_notes' and user.lead_ids:
                    lead_id = random.choice(user.lead_ids)
                    requests.get(
                        f"{self.config.base_url}/notes/{lead_id}/",
                        headers=headers,
                        timeout=self.config.timeout
                    )
                
                elif action == 'ai_query':
                    queries = [
                        "How many leads do I have?",
                        "Show me my hot leads",
                        "What's my pipeline status?",
                        "Give me lead generation tips"
                    ]
                    requests.post(
                        f"{self.config.base_url}/ai/query",
                        json={"query": random.choice(queries)},
                        headers=headers,
                        timeout=self.config.timeout * 2
                    )
                
                elif action == 'check_profile':
                    requests.get(
                        f"{self.config.base_url}/auth/me",
                        headers=headers,
                        timeout=self.config.timeout
                    )
                
                # Random delay between actions (0.5-2 seconds)
                time.sleep(random.uniform(0.5, 2.0))
                
            except Exception:
                pass  # Continue with next action
    
    def test_concurrent_user_sessions(self, num_users: int = 50, actions_per_user: int = 10):
        """Test multiple concurrent user sessions"""
        print(f"\n👥 Testing {num_users} concurrent users ({actions_per_user} actions each)...")
        
        def user_session():
            user = self._register_and_login_user()
            if user.token:
                self.users.append(user)
                self._user_workflow(user, actions_per_user)
        
        metrics = self.run_concurrent_requests(user_session, num_users, max_workers=20)
        self.print_metrics(f"Concurrent User Sessions ({num_users} users)")
        return metrics
    
    def test_gradual_user_ramp_up(self, num_users: int = 100, ramp_up_time: int = 30):
        """Test gradual user ramp-up"""
        print(f"\n👥 Testing gradual ramp-up: {num_users} users over {ramp_up_time}s...")
        
        def user_session():
            user = self._register_and_login_user()
            if user.token:
                self.users.append(user)
                self._user_workflow(user, actions=5)
        
        metrics = self.ramp_up_users(user_session, num_users, ramp_up_time)
        self.print_metrics(f"Gradual User Ramp-up ({num_users} users)")
        return metrics
    
    def test_peak_load_simulation(self, duration: int = 60, users_per_second: int = 5):
        """Simulate peak load with continuous user activity"""
        print(f"\n👥 Testing peak load: {users_per_second} new users/s for {duration}s...")
        
        def user_session():
            user = self._register_and_login_user()
            if user.token:
                self.users.append(user)
                self._user_workflow(user, actions=3)
        
        metrics = self.sustained_load_test(user_session, duration, users_per_second)
        self.print_metrics(f"Peak Load Simulation ({users_per_second} users/s)")
        return metrics
    
    def test_realistic_daily_usage(self, num_users: int = 30):
        """Simulate realistic daily usage patterns"""
        print(f"\n👥 Testing realistic daily usage with {num_users} users...")
        
        # Create users first
        print("Creating user accounts...")
        for _ in range(num_users):
            try:
                user = self._register_and_login_user()
                if user.token:
                    self.users.append(user)
            except Exception:
                pass
        
        print(f"Created {len(self.users)} users")
        
        # Simulate different usage patterns
        def morning_routine():
            """Morning: Check leads, add notes"""
            user = random.choice(self.users)
            headers = {'Authorization': f'Bearer {user.token}'}
            
            # Check leads
            requests.get(
                f"{self.config.base_url}/leads/",
                headers=headers,
                timeout=self.config.timeout
            )
            
            # Add a note if we have leads
            if user.lead_ids:
                lead_id = random.choice(user.lead_ids)
                note_data = TestDataGenerator.generate_note_data()
                requests.post(
                    f"{self.config.base_url}/notes/{lead_id}/",
                    json=note_data,
                    headers=headers,
                    timeout=self.config.timeout
                )
        
        def midday_routine():
            """Midday: Create leads, update pipeline"""
            user = random.choice(self.users)
            headers = {'Authorization': f'Bearer {user.token}'}
            
            # Create a lead
            lead_data = TestDataGenerator.generate_lead_data()
            response = requests.post(
                f"{self.config.base_url}/leads/",
                json=lead_data,
                headers=headers,
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                lead_id = response.json().get('id')
                if lead_id:
                    user.lead_ids.append(lead_id)
            
            # Update existing lead
            if user.lead_ids:
                lead_id = random.choice(user.lead_ids)
                update_data = {
                    "pipeline_status": TestDataGenerator.random_pipeline_status()
                }
                requests.put(
                    f"{self.config.base_url}/leads/{lead_id}",
                    json=update_data,
                    headers=headers,
                    timeout=self.config.timeout
                )
        
        def afternoon_routine():
            """Afternoon: AI queries, analysis"""
            user = random.choice(self.users)
            headers = {'Authorization': f'Bearer {user.token}'}
            
            queries = [
                "Analyze my pipeline",
                "Show me leads that need follow-up",
                "What's my conversion rate?",
                "Give me insights on my hot leads"
            ]
            
            requests.post(
                f"{self.config.base_url}/ai/query",
                json={"query": random.choice(queries)},
                headers=headers,
                timeout=self.config.timeout * 2
            )
        
        # Run different routines
        print("\nSimulating morning activity...")
        morning_metrics = self.run_concurrent_requests(morning_routine, num_users * 2)
        
        print("\nSimulating midday activity...")
        midday_metrics = self.run_concurrent_requests(midday_routine, num_users * 3)
        
        print("\nSimulating afternoon activity...")
        afternoon_metrics = self.run_concurrent_requests(afternoon_routine, num_users)
        
        # Print combined results
        print(f"\n{'='*60}")
        print(f"Realistic Daily Usage Summary")
        print(f"{'='*60}")
        print(f"Total Users:           {len(self.users)}")
        print(f"Morning Requests:      {morning_metrics.total_requests}")
        print(f"Midday Requests:       {midday_metrics.total_requests}")
        print(f"Afternoon Requests:    {afternoon_metrics.total_requests}")
        print(f"Total Requests:        {morning_metrics.total_requests + midday_metrics.total_requests + afternoon_metrics.total_requests}")
        print(f"{'='*60}\n")
        
        return {
            'morning': morning_metrics,
            'midday': midday_metrics,
            'afternoon': afternoon_metrics
        }
    
    def test_heavy_user_vs_light_user(self, heavy_users: int = 10, light_users: int = 40):
        """Test mix of heavy and light users"""
        print(f"\n👥 Testing {heavy_users} heavy users + {light_users} light users...")
        
        def heavy_user_session():
            """Heavy user: lots of activity"""
            user = self._register_and_login_user()
            if user.token:
                self.users.append(user)
                self._user_workflow(user, actions=20)
        
        def light_user_session():
            """Light user: minimal activity"""
            user = self._register_and_login_user()
            if user.token:
                self.users.append(user)
                self._user_workflow(user, actions=3)
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        self.metrics = TestMetrics()
        self.metrics.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            
            # Submit heavy users
            for _ in range(heavy_users):
                futures.append(executor.submit(self._timed_request, heavy_user_session))
            
            # Submit light users
            for _ in range(light_users):
                futures.append(executor.submit(self._timed_request, light_user_session))
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        
        self.metrics.end_time = time.time()
        self.print_metrics(f"Mixed User Load ({heavy_users} heavy + {light_users} light)")
        return self.metrics
    
    def run_all_tests(self):
        """Run all concurrent user simulation tests"""
        print("\n" + "="*60)
        print("CONCURRENT USER SIMULATION TESTS")
        print("="*60)
        
        results = {}
        
        try:
            results['concurrent_sessions'] = self.test_concurrent_user_sessions(50, 10)
        except Exception as e:
            print(f"❌ Concurrent sessions test failed: {e}")
        
        try:
            results['gradual_ramp_up'] = self.test_gradual_user_ramp_up(100, 30)
        except Exception as e:
            print(f"❌ Gradual ramp-up test failed: {e}")
        
        try:
            results['peak_load'] = self.test_peak_load_simulation(60, 5)
        except Exception as e:
            print(f"❌ Peak load test failed: {e}")
        
        try:
            results['realistic_usage'] = self.test_realistic_daily_usage(30)
        except Exception as e:
            print(f"❌ Realistic usage test failed: {e}")
        
        try:
            results['mixed_users'] = self.test_heavy_user_vs_light_user(10, 40)
        except Exception as e:
            print(f"❌ Mixed users test failed: {e}")
        
        return results


def run_concurrent_user_tests(base_url: str = "http://localhost:8000"):
    """Run concurrent user simulation tests"""
    config = StressTestConfig(base_url=base_url)
    test_suite = ConcurrentUserSimulation(config)
    return test_suite.run_all_tests()


if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    run_concurrent_user_tests(base_url)

# Made with Bob
