"""
===============================================================================
FILE 4: test_setup.py  
===============================================================================
"""

# test_setup.py
import sys
import os
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
import json
import time

class SetupTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.kafka_server = 'localhost:9092'
        
    def print_test(self, test_name):
        print(f"\n[TEST] {test_name}...", end=' ')
    
    def print_pass(self, message=""):
        print(f"✓ PASS" + (f" - {message}" if message else ""))
        self.tests_passed += 1
    
    def print_fail(self, message=""):
        print(f"✗ FAIL" + (f" - {message}" if message else ""))
        self.tests_failed += 1
    
    def test_python_version(self):
        self.print_test("Python version >= 3.8")
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.print_pass(f"Python {version.major}.{version.minor}")
        else:
            self.print_fail(f"Python {version.major}.{version.minor} found, need 3.8+")
    
    def test_imports(self):
        self.print_test("Required Python packages")
        required = ['kafka', 'matplotlib', 'numpy']
        missing = []
        for package in required:
            try:
                __import__(package)
            except ImportError:
                missing.append(package)
        if not missing:
            self.print_pass("All packages installed")
        else:
            self.print_fail(f"Missing: {', '.join(missing)}")
    
    def test_dataset(self):
        self.print_test("Dataset file (wiki-Vote.txt)")
        if os.path.exists('wiki-Vote.txt'):
            with open('wiki-Vote.txt', 'r') as f:
                lines = sum(1 for line in f if line.strip() and not line.startswith('#'))
            self.print_pass(f"{lines:,} edges found")
        else:
            self.print_fail("wiki-Vote.txt not found")
    
    def test_kafka_connection(self):
        self.print_test(f"Kafka connection ({self.kafka_server})")
        try:
            admin = KafkaAdminClient(bootstrap_servers=self.kafka_server, request_timeout_ms=5000)
            admin.close()
            self.print_pass("Connection successful")
        except Exception as e:
            self.print_fail(f"Cannot connect: {str(e)[:50]}")
    
    def run_all_tests(self):
        print("\n" + "="*70)
        print("  KAFKA STREAMING SETUP VERIFICATION")
        print("="*70)
        
        self.test_python_version()
        self.test_imports()
        self.test_dataset()
        self.test_kafka_connection()
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        total = self.tests_passed + self.tests_failed
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {self.tests_passed} ✓")
        print(f"Failed: {self.tests_failed} ✗")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! Ready to run the streaming pipeline.")
        else:
            print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\n" + "="*70 + "\n")
        return self.tests_failed == 0

def main():
    tester = SetupTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()