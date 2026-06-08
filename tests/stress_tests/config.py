"""
Configuration and utilities for stress tests
"""
import os
import time
import random
import string
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics


@dataclass
class StressTestConfig:
    """Configuration for stress tests"""
    base_url: str = "http://localhost:8000"
    num_users: int = 100
    num_requests_per_user: int = 10
    ramp_up_time: int = 10  # seconds
    test_duration: int = 60  # seconds
    max_workers: int = 50
    timeout: int = 30
    
    # Database settings
    test_db_url: Optional[str] = None
    
    # Test data generation
    generate_test_data: bool = True
    test_data_size: int = 1000


@dataclass
class TestMetrics:
    """Metrics collected during stress tests"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[Dict] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def add_response(self, response_time: float, success: bool, error: Optional[str] = None):
        """Add a response to metrics"""
        self.total_requests += 1
        self.response_times.append(response_time)
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error:
                self.errors.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': error
                })
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.response_times:
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'error_rate': 0.0,
                'avg_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0,
                'median_response_time': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0,
                'requests_per_second': 0.0,
                'duration': 0.0
            }
        
        duration = (self.end_time or time.time()) - (self.start_time or time.time())
        sorted_times = sorted(self.response_times)
        
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'error_rate': (self.failed_requests / self.total_requests * 100) if self.total_requests > 0 else 0.0,
            'avg_response_time': statistics.mean(self.response_times),
            'min_response_time': min(self.response_times),
            'max_response_time': max(self.response_times),
            'median_response_time': statistics.median(self.response_times),
            'p95_response_time': sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0.0,
            'p99_response_time': sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0.0,
            'requests_per_second': self.total_requests / duration if duration > 0 else 0.0,
            'duration': duration,
            'error_samples': self.errors[:10]  # First 10 errors
        }


class TestDataGenerator:
    """Generate test data for stress tests"""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate random string"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email() -> str:
        """Generate random email"""
        return f"test_{TestDataGenerator.random_string(8)}@example.com"
    
    @staticmethod
    def random_phone() -> str:
        """Generate random phone number"""
        return f"+1{random.randint(2000000000, 9999999999)}"
    
    @staticmethod
    def random_name() -> str:
        """Generate random name"""
        first_names = ["John", "Jane", "Bob", "Alice", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    @staticmethod
    def random_company() -> str:
        """Generate random company name"""
        prefixes = ["Tech", "Global", "Digital", "Smart", "Innovative", "Advanced", "Premier", "Elite"]
        suffixes = ["Solutions", "Systems", "Corp", "Inc", "Group", "Enterprises", "Industries", "Technologies"]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"
    
    @staticmethod
    def random_lead_status() -> str:
        """Generate random lead status"""
        return random.choice(["HOT", "WARM", "COLD"])
    
    @staticmethod
    def random_pipeline_status() -> str:
        """Generate random pipeline status"""
        return random.choice(["NEW", "IN_PROGRESS", "CLOSED", "WON", "LOST", "ACTIVE", "INACTIVE"])
    
    @staticmethod
    def generate_user_data() -> Dict:
        """Generate user registration data"""
        return {
            "email": TestDataGenerator.random_email(),
            "password": "TestPassword123!",
            "first_name": TestDataGenerator.random_string(6),
            "last_name": TestDataGenerator.random_string(8)
        }
    
    @staticmethod
    def generate_lead_data() -> Dict:
        """Generate lead data"""
        return {
            "name": TestDataGenerator.random_name(),
            "company": TestDataGenerator.random_company(),
            "email": TestDataGenerator.random_email(),
            "phone_number": TestDataGenerator.random_phone(),
            "lead_status": TestDataGenerator.random_lead_status(),
            "pipeline_status": TestDataGenerator.random_pipeline_status()
        }
    
    @staticmethod
    def generate_note_data() -> Dict:
        """Generate note data"""
        return {
            "content": f"Test note content: {TestDataGenerator.random_string(50)}",
            "tags": random.sample(["FOLLOW_UP", "MEETING", "CALL", "EMAIL"], k=random.randint(1, 3))
        }
    
    @staticmethod
    def generate_csv_data(num_rows: int = 100) -> str:
        """Generate CSV data for bulk upload"""
        csv_lines = ["name,company,phone_number,email,lead_status,pipeline_status"]
        
        for _ in range(num_rows):
            lead = TestDataGenerator.generate_lead_data()
            csv_lines.append(
                f"{lead['name']},{lead['company']},{lead['phone_number']},"
                f"{lead['email']},{lead['lead_status']},{lead['pipeline_status']}"
            )
        
        return "\n".join(csv_lines)


class StressTestRunner:
    """Base class for running stress tests"""
    
    def __init__(self, config: StressTestConfig):
        self.config = config
        self.metrics = TestMetrics()
    
    def run_concurrent_requests(
        self,
        request_func: Callable,
        num_requests: int,
        max_workers: Optional[int] = None
    ) -> TestMetrics:
        """Run concurrent requests and collect metrics"""
        max_workers = max_workers or self.config.max_workers
        self.metrics = TestMetrics()
        self.metrics.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._timed_request, request_func) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.metrics.add_response(0.0, False, str(e))
        
        self.metrics.end_time = time.time()
        return self.metrics
    
    def _timed_request(self, request_func: Callable):
        """Execute a request and time it"""
        start_time = time.time()
        try:
            request_func()
            response_time = time.time() - start_time
            self.metrics.add_response(response_time, True)
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.add_response(response_time, False, str(e))
            raise
    
    def ramp_up_users(
        self,
        request_func: Callable,
        num_users: int,
        ramp_up_time: int
    ) -> TestMetrics:
        """Gradually ramp up users over time"""
        self.metrics = TestMetrics()
        self.metrics.start_time = time.time()
        
        delay_between_users = ramp_up_time / num_users if num_users > 0 else 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            
            for i in range(num_users):
                futures.append(executor.submit(self._timed_request, request_func))
                if i < num_users - 1:  # Don't sleep after last user
                    time.sleep(delay_between_users)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass  # Already recorded in _timed_request
        
        self.metrics.end_time = time.time()
        return self.metrics
    
    def sustained_load_test(
        self,
        request_func: Callable,
        duration: int,
        requests_per_second: int
    ) -> TestMetrics:
        """Run sustained load for a duration"""
        self.metrics = TestMetrics()
        self.metrics.start_time = time.time()
        end_time = time.time() + duration
        
        delay_between_requests = 1.0 / requests_per_second if requests_per_second > 0 else 0
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            
            while time.time() < end_time:
                futures.append(executor.submit(self._timed_request, request_func))
                time.sleep(delay_between_requests)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        
        self.metrics.end_time = time.time()
        return self.metrics
    
    def print_metrics(self, test_name: str):
        """Print test metrics"""
        summary = self.metrics.get_summary()
        
        print(f"\n{'='*60}")
        print(f"Stress Test Results: {test_name}")
        print(f"{'='*60}")
        print(f"Total Requests:        {summary['total_requests']}")
        print(f"Successful:            {summary['successful_requests']}")
        print(f"Failed:                {summary['failed_requests']}")
        print(f"Error Rate:            {summary['error_rate']:.2f}%")
        print(f"Duration:              {summary['duration']:.2f}s")
        print(f"Requests/Second:       {summary['requests_per_second']:.2f}")
        print(f"\nResponse Times (seconds):")
        print(f"  Average:             {summary['avg_response_time']:.4f}")
        print(f"  Minimum:             {summary['min_response_time']:.4f}")
        print(f"  Maximum:             {summary['max_response_time']:.4f}")
        print(f"  Median:              {summary['median_response_time']:.4f}")
        print(f"  95th Percentile:     {summary['p95_response_time']:.4f}")
        print(f"  99th Percentile:     {summary['p99_response_time']:.4f}")
        
        if summary['error_samples']:
            print(f"\nError Samples (first 10):")
            for i, error in enumerate(summary['error_samples'], 1):
                print(f"  {i}. [{error['timestamp']}] {error['error']}")
        
        print(f"{'='*60}\n")

# Made with Bob
