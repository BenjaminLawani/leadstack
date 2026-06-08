#!/usr/bin/env python3
"""
Main Test Runner for Leadstack Stress Tests

Run all stress tests or specific test suites.
"""
import sys
import argparse
import time
from datetime import datetime
import json

from .test_auth_stress import run_auth_stress_tests
from .test_leads_stress import run_leads_stress_tests
from .test_ai_stress import run_ai_stress_tests
from .test_notes_stress import run_notes_stress_tests
from .test_concurrent_users import run_concurrent_user_tests


def print_banner():
    """Print test banner"""
    print("\n" + "="*70)
    print(" " * 15 + "LEADSTACK STRESS TEST SUITE")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


def print_summary(results: dict, total_time: float):
    """Print test summary"""
    print("\n" + "="*70)
    print(" " * 20 + "TEST SUMMARY")
    print("="*70)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for suite_name, suite_results in results.items():
        if isinstance(suite_results, dict):
            suite_total = len(suite_results)
            suite_passed = sum(1 for r in suite_results.values() if r is not None)
            suite_failed = suite_total - suite_passed
            
            total_tests += suite_total
            passed_tests += suite_passed
            failed_tests += suite_failed
            
            status = "✓ PASSED" if suite_failed == 0 else f"⚠ {suite_failed} FAILED"
            print(f"\n{suite_name.upper()}:")
            print(f"  Tests Run: {suite_total} | Passed: {suite_passed} | Failed: {suite_failed} | {status}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL TESTS:     {total_tests}")
    print(f"PASSED:          {passed_tests} ({passed_tests/total_tests*100:.1f}%)" if total_tests > 0 else "PASSED: 0")
    print(f"FAILED:          {failed_tests} ({failed_tests/total_tests*100:.1f}%)" if total_tests > 0 else "FAILED: 0")
    print(f"TOTAL TIME:      {total_time:.2f}s")
    print(f"{'='*70}\n")


def save_results(results: dict, output_file: str):
    """Save test results to JSON file"""
    try:
        # Convert results to JSON-serializable format
        json_results = {}
        for suite_name, suite_results in results.items():
            if isinstance(suite_results, dict):
                json_results[suite_name] = {}
                for test_name, test_result in suite_results.items():
                    if test_result is not None and hasattr(test_result, 'get_summary'):
                        json_results[suite_name][test_name] = test_result.get_summary()
                    else:
                        json_results[suite_name][test_name] = str(test_result)
        
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': json_results
            }, f, indent=2)
        
        print(f"✓ Results saved to {output_file}")
    except Exception as e:
        print(f"⚠ Failed to save results: {e}")


def run_all_tests(base_url: str, output_file: str = None):
    """Run all stress test suites"""
    print_banner()
    
    start_time = time.time()
    results = {}
    
    # Run each test suite
    test_suites = [
        ("Authentication", run_auth_stress_tests),
        ("Leads", run_leads_stress_tests),
        ("AI Agent", run_ai_stress_tests),
        ("Notes", run_notes_stress_tests),
        ("Concurrent Users", run_concurrent_user_tests),
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n{'='*70}")
        print(f"Running {suite_name} Tests...")
        print(f"{'='*70}")
        
        try:
            suite_results = test_func(base_url)
            results[suite_name.lower().replace(' ', '_')] = suite_results
            print(f"✓ {suite_name} tests completed")
        except Exception as e:
            print(f"❌ {suite_name} tests failed: {e}")
            results[suite_name.lower().replace(' ', '_')] = None
        
        # Small delay between test suites
        time.sleep(2)
    
    total_time = time.time() - start_time
    
    # Print summary
    print_summary(results, total_time)
    
    # Save results if output file specified
    if output_file:
        save_results(results, output_file)
    
    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run Leadstack stress tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python -m tests.stress_tests.run_all_tests
  
  # Run specific test suite
  python -m tests.stress_tests.run_all_tests --suite auth
  
  # Run against custom URL
  python -m tests.stress_tests.run_all_tests --url http://staging.example.com
  
  # Save results to file
  python -m tests.stress_tests.run_all_tests --output results.json
        """
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the application (default: http://localhost:8000)'
    )
    
    parser.add_argument(
        '--suite',
        choices=['auth', 'leads', 'ai', 'notes', 'users', 'all'],
        default='all',
        help='Test suite to run (default: all)'
    )
    
    parser.add_argument(
        '--output',
        help='Output file for test results (JSON format)'
    )
    
    args = parser.parse_args()
    
    # Run tests based on suite selection
    if args.suite == 'all':
        run_all_tests(args.url, args.output)
    elif args.suite == 'auth':
        print_banner()
        run_auth_stress_tests(args.url)
    elif args.suite == 'leads':
        print_banner()
        run_leads_stress_tests(args.url)
    elif args.suite == 'ai':
        print_banner()
        run_ai_stress_tests(args.url)
    elif args.suite == 'notes':
        print_banner()
        run_notes_stress_tests(args.url)
    elif args.suite == 'users':
        print_banner()
        run_concurrent_user_tests(args.url)


if __name__ == "__main__":
    main()

# Made with Bob
