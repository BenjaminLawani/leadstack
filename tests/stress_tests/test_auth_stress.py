"""
Authentication Stress Tests

Tests authentication endpoints under high load:
- User registration
- Login
- Token validation
- Concurrent authentication
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


class AuthStressTest(StressTestRunner):
    """Stress tests for authentication endpoints"""
    
    def __init__(self, config: StressTestConfig):
        super().__init__(config)
        self.created_users: List[Dict] = []
        self.tokens: List[str] = []
    
    def test_concurrent_registrations(self, num_users: int = 100):
        """Test concurrent user registrations"""
        print(f"\n🔐 Testing {num_users} concurrent user registrations...")
        
        def register_user():
            user_data = TestDataGenerator.generate_user_data()
            response = requests.post(
                f"{self.config.base_url}/auth/get-started",
                json=user_data,
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                self.created_users.append({
                    'email': user_data['email'],
                    'password': user_data['password']
                })
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(register_user, num_users)
        self.print_metrics("Concurrent User Registrations")
        return metrics
    
    def test_concurrent_logins(self, num_logins: int = 100):
        """Test concurrent user logins"""
        print(f"\n🔐 Testing {num_logins} concurrent logins...")
        
        # Ensure we have users to login with
        if not self.created_users:
            print("Creating test users first...")
            self.test_concurrent_registrations(min(50, num_logins))
        
        def login_user():
            if not self.created_users:
                raise Exception("No users available for login")
            
            user = self.created_users[len(self.tokens) % len(self.created_users)]
            response = requests.post(
                f"{self.config.base_url}/auth/login",
                data={
                    'username': user['email'],
                    'password': user['password']
                },
                timeout=self.config.timeout
            )
            if response.status_code == 200:
                token = response.json().get('access_token')
                if token:
                    self.tokens.append(token)
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(login_user, num_logins)
        self.print_metrics("Concurrent User Logins")
        return metrics
    
    def test_token_validation(self, num_requests: int = 200):
        """Test concurrent token validation via /auth/me endpoint"""
        print(f"\n🔐 Testing {num_requests} concurrent token validations...")
        
        # Ensure we have tokens
        if not self.tokens:
            print("Creating tokens first...")
            self.test_concurrent_logins(50)
        
        def validate_token():
            if not self.tokens:
                raise Exception("No tokens available")
            
            token = self.tokens[len(self.metrics.response_times) % len(self.tokens)]
            response = requests.get(
                f"{self.config.base_url}/auth/me",
                headers={'Authorization': f'Bearer {token}'},
                timeout=self.config.timeout
            )
            response.raise_for_status()
        
        metrics = self.run_concurrent_requests(validate_token, num_requests)
        self.print_metrics("Concurrent Token Validations")
        return metrics
    
    def test_registration_with_duplicates(self, num_attempts: int = 50):
        """Test handling of duplicate email registrations"""
        print(f"\n🔐 Testing {num_attempts} duplicate registration attempts...")
        
        # Create one user first
        user_data = TestDataGenerator.generate_user_data()
        requests.post(
            f"{self.config.base_url}/auth/get-started",
            json=user_data,
            timeout=self.config.timeout
        )
        
        def register_duplicate():
            response = requests.post(
                f"{self.config.base_url}/auth/get-started",
                json=user_data,
                timeout=self.config.timeout
            )
            # We expect 409 Conflict for duplicates
            if response.status_code != 409:
                raise Exception(f"Expected 409, got {response.status_code}")
        
        metrics = self.run_concurrent_requests(register_duplicate, num_attempts)
        self.print_metrics("Duplicate Registration Handling")
        return metrics
    
    def test_invalid_login_attempts(self, num_attempts: int = 100):
        """Test handling of invalid login attempts"""
        print(f"\n🔐 Testing {num_attempts} invalid login attempts...")
        
        def invalid_login():
            response = requests.post(
                f"{self.config.base_url}/auth/login",
                data={
                    'username': TestDataGenerator.random_email(),
                    'password': 'WrongPassword123!'
                },
                timeout=self.config.timeout
            )
            # We expect 401 Unauthorized
            if response.status_code != 401:
                raise Exception(f"Expected 401, got {response.status_code}")
        
        metrics = self.run_concurrent_requests(invalid_login, num_attempts)
        self.print_metrics("Invalid Login Attempts")
        return metrics
    
    def test_ramp_up_authentication(self, num_users: int = 100, ramp_up_time: int = 10):
        """Test gradual ramp-up of authentication requests"""
        print(f"\n🔐 Testing ramp-up of {num_users} users over {ramp_up_time}s...")
        
        def auth_flow():
            # Register
            user_data = TestDataGenerator.generate_user_data()
            reg_response = requests.post(
                f"{self.config.base_url}/auth/get-started",
                json=user_data,
                timeout=self.config.timeout
            )
            reg_response.raise_for_status()
            
            # Login
            login_response = requests.post(
                f"{self.config.base_url}/auth/login",
                data={
                    'username': user_data['email'],
                    'password': user_data['password']
                },
                timeout=self.config.timeout
            )
            login_response.raise_for_status()
        
        metrics = self.ramp_up_users(auth_flow, num_users, ramp_up_time)
        self.print_metrics("Ramp-up Authentication Flow")
        return metrics
    
    def test_sustained_auth_load(self, duration: int = 30, requests_per_second: int = 10):
        """Test sustained authentication load"""
        print(f"\n🔐 Testing sustained auth load: {requests_per_second} req/s for {duration}s...")
        
        # Pre-create some users for login tests
        print("Pre-creating test users...")
        for _ in range(20):
            user_data = TestDataGenerator.generate_user_data()
            try:
                response = requests.post(
                    f"{self.config.base_url}/auth/get-started",
                    json=user_data,
                    timeout=self.config.timeout
                )
                if response.status_code == 200:
                    self.created_users.append({
                        'email': user_data['email'],
                        'password': user_data['password']
                    })
            except Exception:
                pass
        
        def mixed_auth_requests():
            # Randomly choose between login and token validation
            import random
            if random.random() < 0.5 and self.created_users:
                # Login
                user = random.choice(self.created_users)
                response = requests.post(
                    f"{self.config.base_url}/auth/login",
                    data={
                        'username': user['email'],
                        'password': user['password']
                    },
                    timeout=self.config.timeout
                )
                response.raise_for_status()
            else:
                # Register new user
                user_data = TestDataGenerator.generate_user_data()
                response = requests.post(
                    f"{self.config.base_url}/auth/get-started",
                    json=user_data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
        
        metrics = self.sustained_load_test(mixed_auth_requests, duration, requests_per_second)
        self.print_metrics("Sustained Authentication Load")
        return metrics
    
    def run_all_tests(self):
        """Run all authentication stress tests"""
        print("\n" + "="*60)
        print("AUTHENTICATION STRESS TESTS")
        print("="*60)
        
        results = {}
        
        try:
            results['concurrent_registrations'] = self.test_concurrent_registrations(100)
        except Exception as e:
            print(f"❌ Concurrent registrations test failed: {e}")
        
        try:
            results['concurrent_logins'] = self.test_concurrent_logins(100)
        except Exception as e:
            print(f"❌ Concurrent logins test failed: {e}")
        
        try:
            results['token_validation'] = self.test_token_validation(200)
        except Exception as e:
            print(f"❌ Token validation test failed: {e}")
        
        try:
            results['duplicate_registrations'] = self.test_registration_with_duplicates(50)
        except Exception as e:
            print(f"❌ Duplicate registration test failed: {e}")
        
        try:
            results['invalid_logins'] = self.test_invalid_login_attempts(100)
        except Exception as e:
            print(f"❌ Invalid login test failed: {e}")
        
        try:
            results['ramp_up'] = self.test_ramp_up_authentication(100, 10)
        except Exception as e:
            print(f"❌ Ramp-up test failed: {e}")
        
        try:
            results['sustained_load'] = self.test_sustained_auth_load(30, 10)
        except Exception as e:
            print(f"❌ Sustained load test failed: {e}")
        
        return results


def run_auth_stress_tests(base_url: str = "http://localhost:8000"):
    """Run authentication stress tests"""
    config = StressTestConfig(base_url=base_url)
    test_suite = AuthStressTest(config)
    return test_suite.run_all_tests()


if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    run_auth_stress_tests(base_url)

# Made with Bob
