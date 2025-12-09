"""
API Testing Suite
Tests all endpoints for Milestone 2
"""

import requests
import json
from pathlib import Path
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DATA_DIR = Path("data/clean")

class APITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.project_id = None
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*70)
        print("🧪 API TESTING SUITE - MILESTONE 2")
        print("="*70)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Create Project", self.test_create_project),
            ("List Projects", self.test_list_projects),
            ("Upload Structured Data", self.test_upload_structured),
            ("Get Project Events", self.test_get_events),
            ("Get Project Statistics", self.test_get_statistics),
            ("Upload Unstructured Data", self.test_upload_unstructured),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n{'─'*70}")
            print(f"🔬 Running: {test_name}")
            print('─'*70)
            
            try:
                test_func()
                print(f"✅ PASSED: {test_name}")
                passed += 1
            except Exception as e:
                print(f"❌ FAILED: {test_name}")
                print(f"   Error: {str(e)}")
                failed += 1
            
            time.sleep(0.5)
        
        print("\n" + "="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        print(f"   ✅ Passed: {passed}/{len(tests)}")
        print(f"   ❌ Failed: {failed}/{len(tests)}")
        print(f"   Success Rate: {(passed/len(tests)*100):.1f}%")
        print("="*70 + "\n")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        
        data = response.json()
        assert data['status'] == 'healthy', "Service not healthy"
        assert data['database'] == 'connected', "Database not connected"
        
        print(f"   Status: {data['status']}")
        print(f"   Database: {data['database']}")
        print(f"   Services: {data['services']}")
    
    def test_create_project(self):
        """Test project creation"""
        payload = {
            'name': 'Test Project - API Testing',
            'description': 'Automated test project',
            'dataset_type': 'structured'
        }
        
        response = self.session.post(
            f"{self.base_url}/projects",
            data=payload
        )
        response.raise_for_status()
        
        data = response.json()
        self.project_id = data['id']
        
        assert 'id' in data, "No project ID returned"
        assert data['name'] == payload['name'], "Name mismatch"
        assert data['status'] == 'pending', "Status should be pending"
        
        print(f"   Created Project ID: {self.project_id}")
        print(f"   Name: {data['name']}")
        print(f"   Status: {data['status']}")
    
    def test_list_projects(self):
        """Test listing projects"""
        response = self.session.get(f"{self.base_url}/projects")
        response.raise_for_status()
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one project"
        
        print(f"   Total Projects: {len(data)}")
        print(f"   Latest Project: {data[0]['name']}")
    
    def test_upload_structured(self):
        """Test structured file upload"""
        if not self.project_id:
            raise Exception("No project ID available")
        
        # Use existing test file
        test_file = TEST_DATA_DIR / "BPI_2012_clean.csv"
        
        if not test_file.exists():
            print(f"   ⚠️  Test file not found: {test_file}")
            print(f"   Creating sample CSV...")
            self._create_sample_csv(test_file)
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_data.csv', f, 'text/csv')}
            data = {'project_id': self.project_id}
            
            response = self.session.post(
                f"{self.base_url}/upload/structured",
                files=files,
                data=data
            )
            response.raise_for_status()
        
        result = response.json()
        assert result['status'] == 'completed', "Upload should complete"
        assert result['records_processed'] > 0, "Should process records"
        
        print(f"   Records Processed: {result['records_processed']}")
        print(f"   File Size: {result['file_size']} bytes")
        print(f"   Status: {result['status']}")
    
    def test_get_events(self):
        """Test retrieving project events"""
        if not self.project_id:
            raise Exception("No project ID available")
        
        response = self.session.get(
            f"{self.base_url}/projects/{self.project_id}/events",
            params={'limit': 10}
        )
        response.raise_for_status()
        
        data = response.json()
        assert 'events' in data, "No events in response"
        
        print(f"   Events Retrieved: {data['count']}")
        if data['count'] > 0:
            print(f"   Sample Event: {data['events'][0]['activity']}")
    
    def test_get_statistics(self):
        """Test project statistics"""
        if not self.project_id:
            raise Exception("No project ID available")
        
        response = self.session.get(
            f"{self.base_url}/projects/{self.project_id}/statistics"
        )
        response.raise_for_status()
        
        data = response.json()
        stats = data['statistics']
        
        print(f"   Total Events: {stats.get('total_events', 0)}")
        print(f"   Total Cases: {stats.get('total_cases', 0)}")
        print(f"   Unique Activities: {stats.get('total_activities', 0)}")
    
    def test_upload_unstructured(self):
        """Test unstructured file upload"""
        if not self.project_id:
            raise Exception("No project ID available")
        
        # Create sample text file
        sample_text = """
        Process Mining Documentation
        
        This document describes the invoice approval process.
        
        Step 1: Create Invoice
        The invoice is created by the clerk with all necessary details.
        
        Step 2: Validation
        The system validates the invoice data for completeness.
        
        Step 3: Approval
        The supervisor approves or rejects the invoice.
        """
        
        test_file = Path("uploads/test_document.txt")
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text(sample_text)
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_doc.txt', f, 'text/plain')}
            data = {'project_id': self.project_id}
            
            response = self.session.post(
                f"{self.base_url}/upload/unstructured",
                files=files,
                data=data
            )
            response.raise_for_status()
        
        result = response.json()
        assert result['status'] == 'completed', "Upload should complete"
        assert result.get('chunks_created', 0) > 0, "Should create chunks"
        
        print(f"   Chunks Created: {result.get('chunks_created')}")
        print(f"   File Size: {result['file_size']} bytes")
        print(f"   Status: {result['status']}")
    
    def _create_sample_csv(self, filepath):
        """Create a sample CSV for testing"""
        import pandas as pd
        from datetime import datetime, timedelta
        
        data = []
        start_time = datetime.now()
        
        for i in range(100):
            case_id = f"CASE_{i:03d}"
            for activity in ['Start', 'Process', 'Review', 'Complete']:
                data.append({
                    'case_id': case_id,
                    'activity': activity,
                    'timestamp': (start_time + timedelta(hours=i, minutes=data.__len__())).isoformat(),
                    'resource': f'User_{i % 5}',
                    'cost': 10.0,
                    'location': 'Test'
                })
        
        df = pd.DataFrame(data)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False)
        print(f"   Created sample CSV: {filepath}")

def main():
    """Run API tests"""
    print("\n🚀 Starting API Test Suite...")
    print(f"   Target: {BASE_URL}")
    print(f"   Checking if server is running...")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        response.raise_for_status()
        print("   ✅ Server is running\n")
    except Exception as e:
        print(f"   ❌ Server not accessible: {str(e)}")
        print("\n💡 Make sure the server is running:")
        print("   docker-compose up -d")
        print("   OR")
        print("   python -m scripts.api_server\n")
        return
    
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()