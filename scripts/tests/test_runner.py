#!/usr/bin/env python3
"""
Master Test Runner
Runs all test suites with comprehensive reporting
"""

import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime
import json


class TestRunner:
    def __init__(self):
        self.results = {
            'start_time': datetime.now().isoformat(),
            'test_suites': {},
            'summary': {}
        }
        self.colors = {
            'GREEN': '\033[0;32m',
            'BLUE': '\033[0;34m',
            'YELLOW': '\033[1;33m',
            'RED': '\033[0;31m',
            'NC': '\033[0m'  # No Color
        }
    
    def print_colored(self, text, color='NC'):
        """Print colored text"""
        if sys.stdout.isatty():
            print(f"{self.colors[color]}{text}{self.colors['NC']}")
        else:
            print(text)
    
    def print_header(self, text):
        """Print section header"""
        self.print_colored("\n" + "="*70, 'BLUE')
        self.print_colored(f"  {text}", 'BLUE')
        self.print_colored("="*70, 'BLUE')
    
    def run_test_suite(self, name, test_file, markers=None):
        """
        Run a single test suite
        
        Args:
            name: Name of the test suite
            test_file: Path to test file
            markers: Optional pytest markers to filter tests
        """
        self.print_colored(f"\n📋 Running: {name}", 'YELLOW')
        self.print_colored("─"*70, 'YELLOW')
        
        # Build pytest command
        cmd = [
            'pytest',
            test_file,
            '-v',
            '--tb=short',
            '--color=yes',
            '-ra'
        ]
        
        if markers:
            cmd.extend(['-m', markers])
        
        # Run tests
        start = datetime.now()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        end = datetime.now()
        duration = (end - start).total_seconds()
        
        # Parse results
        passed = failed = 0
        for line in result.stdout.split('\n'):
            if 'passed' in line.lower():
                # Extract numbers from pytest output
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'passed' in part.lower() and i > 0:
                        try:
                            passed = int(parts[i-1])
                        except:
                            pass
            if 'failed' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if 'failed' in part.lower() and i > 0:
                        try:
                            failed = int(parts[i-1])
                        except:
                            pass
        
        # Store results
        self.results['test_suites'][name] = {
            'passed': passed,
            'failed': failed,
            'duration': duration,
            'exit_code': result.returncode
        }
        
        # Print output
        print(result.stdout)
        
        # Print summary for this suite
        if result.returncode == 0:
            self.print_colored(f"✅ {name}: PASSED ({duration:.2f}s)", 'GREEN')
        else:
            self.print_colored(f"❌ {name}: FAILED ({duration:.2f}s)", 'RED')
            if result.stderr:
                self.print_colored("Errors:", 'RED')
                print(result.stderr)
        
        return result.returncode == 0
    
    def check_server_running(self):
        """Check if API server is running"""
        try:
            import requests
            response = requests.get('http://localhost:8000/health', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run_all_tests(self, test_type='all'):
        """
        Run all test suites
        
        Args:
            test_type: Type of tests to run (all, unit, integration, quick)
        """
        self.print_header("Process Mining Platform - Test Suite")
        
        # Check if server is needed
        if test_type in ['all', 'integration', 'api']:
            self.print_colored("\n🔍 Checking API server...", 'BLUE')
            if not self.check_server_running():
                self.print_colored("⚠️  Warning: API server not running!", 'YELLOW')
                self.print_colored("   Some tests may fail. Start server with:", 'YELLOW')
                self.print_colored("   docker-compose up -d", 'YELLOW')
                
                response = input("\n   Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
            else:
                self.print_colored("✅ API server is running", 'GREEN')
        
        # Define test suites
        test_suites = {
            'unit': [
                ('Database Tests', 'scripts/tests/test_database.py'),
                ('Data Processing Tests', 'scripts/tests/test_data_processing.py'),
                ('Embedding Service Tests', 'scripts/tests/test_embedding_service.py'),
            ],
            'integration': [
                ('API Server Tests', 'scripts/tests/test_api_server.py'),
                ('Integration Tests', 'scripts/tests/test_integration.py'),
            ]
        }
        
        # Determine which suites to run
        if test_type == 'all':
            suites_to_run = test_suites['unit'] + test_suites['integration']
        elif test_type == 'unit':
            suites_to_run = test_suites['unit']
        elif test_type == 'integration':
            suites_to_run = test_suites['integration']
        elif test_type == 'quick':
            # Run with fail-fast
            suites_to_run = test_suites['unit'][:2]  # First two unit tests only
        else:
            self.print_colored(f"Unknown test type: {test_type}", 'RED')
            return False
        
        # Run test suites
        all_passed = True
        for name, test_file in suites_to_run:
            # Check if test file exists
            if not Path(test_file).exists():
                self.print_colored(f"⚠️  Test file not found: {test_file}", 'YELLOW')
                continue
            
            passed = self.run_test_suite(name, test_file)
            if not passed:
                all_passed = False
                if test_type == 'quick':
                    self.print_colored("\n⚠️  Stopping due to failure (quick mode)", 'YELLOW')
                    break
        
        # Calculate summary
        total_passed = sum(s['passed'] for s in self.results['test_suites'].values())
        total_failed = sum(s['failed'] for s in self.results['test_suites'].values())
        total_duration = sum(s['duration'] for s in self.results['test_suites'].values())
        
        self.results['summary'] = {
            'total_suites': len(self.results['test_suites']),
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_duration': total_duration,
            'all_passed': all_passed
        }
        
        # Print final summary
        self.print_header("Test Results Summary")
        self.print_colored(f"\n📊 Test Suites Run: {self.results['summary']['total_suites']}", 'BLUE')
        self.print_colored(f"✅ Total Tests Passed: {total_passed}", 'GREEN')
        if total_failed > 0:
            self.print_colored(f"❌ Total Tests Failed: {total_failed}", 'RED')
        self.print_colored(f"⏱️  Total Duration: {total_duration:.2f}s", 'BLUE')
        
        # Individual suite results
        self.print_colored("\n📋 Suite Breakdown:", 'BLUE')
        for suite_name, results in self.results['test_suites'].items():
            status = "✅ PASS" if results['exit_code'] == 0 else "❌ FAIL"
            self.print_colored(
                f"   {status} | {suite_name}: {results['passed']} passed, "
                f"{results['failed']} failed ({results['duration']:.2f}s)",
                'GREEN' if results['exit_code'] == 0 else 'RED'
            )
        
        # Final verdict
        self.print_colored("\n" + "="*70, 'BLUE')
        if all_passed:
            self.print_colored("🎉 ALL TESTS PASSED!", 'GREEN')
        else:
            self.print_colored("❌ SOME TESTS FAILED", 'RED')
        self.print_colored("="*70, 'BLUE')
        
        # Save results to file
        self.save_results()
        
        return all_passed
    
    def save_results(self):
        """Save test results to JSON file"""
        output_file = Path('test_results.json')
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.print_colored(f"\n💾 Results saved to: {output_file}", 'BLUE')


def main():
    """Main entry point"""
    # Parse command line arguments
    test_type = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    valid_types = ['all', 'unit', 'integration', 'quick']
    if test_type not in valid_types:
        print(f"Usage: python run_tests.py [{' | '.join(valid_types)}]")
        print(f"\nTest Types:")
        print(f"  all         - Run all tests (default)")
        print(f"  unit        - Run unit tests only")
        print(f"  integration - Run integration tests only")
        print(f"  quick       - Run quick tests (fail fast)")
        sys.exit(1)
    
    # Create and run test runner
    runner = TestRunner()
    success = runner.run_all_tests(test_type)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
