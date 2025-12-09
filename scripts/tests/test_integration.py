"""
Integration Tests
Tests complete workflows end-to-end
"""

import pytest
import requests
import tempfile
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"

@pytest.fixture(scope="module")
def api_url():
    """Base API URL fixture"""
    return BASE_URL

@pytest.fixture(scope="module")
def test_project(api_url):
    """Create a test project for integration tests"""
    response = requests.post(
        f"{api_url}/projects",
        data={
            "name": "Integration Test Project",
            "description": "Project for integration testing",
            "dataset_type": "hybrid"
        }
    )
    response.raise_for_status()
    project_id = response.json()['id']
    
    yield project_id
    
    # Cleanup (optional - depends if you want to keep test data)

@pytest.fixture
def sample_csv():
    """Create sample CSV file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("case_id,activity,timestamp,resource,cost,location\n")
        for i in range(50):
            f.write(f"CASE_{i:03d},Start,2024-01-{(i%28)+1:02d}T10:00:00,User{i%3},10.5,Texas\n")
            f.write(f"CASE_{i:03d},Process,2024-01-{(i%28)+1:02d}T11:00:00,User{i%3},15.0,Texas\n")
            f.write(f"CASE_{i:03d},Complete,2024-01-{(i%28)+1:02d}T12:00:00,User{i%3},5.0,Texas\n")
        temp_path = f.name
    
    yield temp_path
    
    Path(temp_path).unlink()

@pytest.fixture
def sample_document():
    """Create sample document"""
    content = """
    Invoice Approval Process Documentation
    
    Overview:
    This document describes the invoice approval workflow used in our organization.
    
    Step 1: Invoice Creation
    The process begins when an invoice is created in the system by the accounts payable clerk.
    
    Step 2: Data Validation
    The system automatically validates the invoice data for completeness and accuracy.
    
    Step 3: Manager Review
    If the invoice amount exceeds $1000, it requires manager approval.
    
    Step 4: Payment Processing
    Once approved, the invoice is sent to the payment processing system.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    Path(temp_path).unlink()

class TestAPIAvailability:
    """Test that API is available and healthy"""
    
    def test_api_is_running(self, api_url):
        """Test that API is accessible"""
        response = requests.get(api_url, timeout=5)
        assert response.status_code == 200
    
    def test_health_check(self, api_url):
        """Test health check endpoint"""
        response = requests.get(f"{api_url}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'
    
    def test_swagger_docs_available(self, api_url):
        """Test Swagger documentation is accessible"""
        response = requests.get(f"{api_url}/docs", timeout=5)
        assert response.status_code == 200

class TestProjectWorkflow:
    """Test complete project workflow"""
    
    def test_create_project(self, api_url):
        """Test creating a new project"""
        response = requests.post(
            f"{api_url}/projects",
            data={
                "name": "Test Project Workflow",
                "description": "Testing project creation",
                "dataset_type": "structured"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'id' in data
        assert data['name'] == "Test Project Workflow"
        assert data['status'] == 'pending'
    
    def test_list_projects(self, api_url, test_project):
        """Test listing all projects"""
        response = requests.get(f"{api_url}/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify test project is in list
        project_ids = [p['id'] for p in data]
        assert test_project in project_ids
    
    def test_get_project(self, api_url, test_project):
        """Test getting specific project"""
        response = requests.get(f"{api_url}/projects/{test_project}")
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == test_project
        assert 'name' in data
        assert 'status' in data

class TestStructuredDataWorkflow:
    """Test complete structured data workflow"""
    
    def test_upload_csv(self, api_url, test_project, sample_csv):
        """Test uploading CSV file"""
        with open(sample_csv, 'rb') as f:
            response = requests.post(
                f"{api_url}/upload/structured",
                files={'file': ('test.csv', f, 'text/csv')},
                data={'project_id': test_project}
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data['project_id'] == test_project
        assert data['status'] == 'completed'
        assert data['records_processed'] > 0
        
        print(f"\n  ✅ Processed {data['records_processed']} records")
    
    def test_retrieve_events(self, api_url, test_project):
        """Test retrieving uploaded events"""
        # Wait a bit for processing
        time.sleep(2)
        
        response = requests.get(
            f"{api_url}/projects/{test_project}/events",
            params={'limit': 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'events' in data
        assert data['count'] > 0
    
    def test_get_statistics(self, api_url, test_project):
        """Test getting project statistics"""
        response = requests.get(f"{api_url}/projects/{test_project}/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert 'statistics' in data
        stats = data['statistics']
        
        assert 'total_events' in stats
        assert 'total_cases' in stats
        assert stats['total_events'] > 0

class TestUnstructuredDataWorkflow:
    """Test complete unstructured data workflow"""
    
    def test_upload_document(self, api_url, test_project, sample_document):
        """Test uploading document"""
        with open(sample_document, 'rb') as f:
            response = requests.post(
                f"{api_url}/upload/unstructured",
                files={'file': ('document.txt', f, 'text/plain')},
                data={'project_id': test_project}
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data['project_id'] == test_project
        assert data['status'] == 'completed'
        assert data.get('chunks_created', 0) > 0
        
        print(f"\n  ✅ Created {data['chunks_created']} document chunks")

class TestEndToEndWorkflow:
    """Test complete end-to-end workflow"""
    
    def test_complete_workflow(self, api_url, sample_csv, sample_document):
        """Test complete workflow from project creation to data retrieval"""
        # Step 1: Create project
        print("\n  📝 Step 1: Creating project...")
        response = requests.post(
            f"{api_url}/projects",
            data={
                "name": "E2E Test Project",
                "description": "End-to-end test",
                "dataset_type": "hybrid"
            }
        )
        assert response.status_code == 200
        project_id = response.json()['id']
        print(f"  ✅ Project created: {project_id}")
        
        # Step 2: Upload structured data
        print("\n  📤 Step 2: Uploading CSV data...")
        with open(sample_csv, 'rb') as f:
            response = requests.post(
                f"{api_url}/upload/structured",
                files={'file': ('test.csv', f, 'text/csv')},
                data={'project_id': project_id}
            )
        assert response.status_code == 200
        records_processed = response.json()['records_processed']
        print(f"  ✅ Processed {records_processed} records")
        
        # Step 3: Upload unstructured data
        print("\n  📤 Step 3: Uploading document...")
        with open(sample_document, 'rb') as f:
            response = requests.post(
                f"{api_url}/upload/unstructured",
                files={'file': ('doc.txt', f, 'text/plain')},
                data={'project_id': project_id}
            )
        assert response.status_code == 200
        chunks_created = response.json()['chunks_created']
        print(f"  ✅ Created {chunks_created} chunks")
        
        # Step 4: Retrieve events
        print("\n  📊 Step 4: Retrieving events...")
        time.sleep(2)  # Wait for processing
        response = requests.get(
            f"{api_url}/projects/{project_id}/events",
            params={'limit': 5}
        )
        assert response.status_code == 200
        events = response.json()
        print(f"  ✅ Retrieved {events['count']} events")
        
        # Step 5: Get statistics
        print("\n  📈 Step 5: Getting statistics...")
        response = requests.get(f"{api_url}/projects/{project_id}/statistics")
        assert response.status_code == 200
        stats = response.json()['statistics']
        print(f"  ✅ Total events: {stats['total_events']}")
        print(f"  ✅ Total cases: {stats['total_cases']}")
        
        # Step 6: Verify project status
        print("\n  ✔️  Step 6: Verifying project status...")
        response = requests.get(f"{api_url}/projects/{project_id}")
        assert response.status_code == 200
        project = response.json()
        print(f"  ✅ Project status: {project['status']}")
        
        print("\n  🎉 End-to-end workflow completed successfully!")

class TestErrorHandling:
    """Test error handling in integration scenarios"""
    
    def test_upload_without_project(self, api_url, sample_csv):
        """Test uploading without valid project ID"""
        with open(sample_csv, 'rb') as f:
            response = requests.post(
                f"{api_url}/upload/structured",
                files={'file': ('test.csv', f, 'text/csv')},
                data={'project_id': 999999}
            )
        
        assert response.status_code in [404, 500]
    
    def test_upload_invalid_file_type(self, api_url, test_project):
        """Test uploading invalid file type"""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b'fake binary content')
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = requests.post(
                    f"{api_url}/upload/structured",
                    files={'file': ('malware.exe', f, 'application/octet-stream')},
                    data={'project_id': test_project}
                )
            
            assert response.status_code in [400, 422]
        finally:
            Path(temp_path).unlink()
    
    def test_get_nonexistent_project(self, api_url):
        """Test getting project that doesn't exist"""
        response = requests.get(f"{api_url}/projects/999999")
        assert response.status_code == 404

class TestPerformance:
    """Test performance under load"""
    
    def test_concurrent_health_checks(self, api_url):
        """Test handling concurrent health check requests"""
        import concurrent.futures
        
        def make_request():
            response = requests.get(f"{api_url}/health", timeout=5)
            return response.status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        assert all(status == 200 for status in results)
        print(f"\n  ✅ Handled 50 concurrent health checks successfully")
    
    def test_large_csv_upload(self, api_url, test_project):
        """Test uploading large CSV file"""
        # Create large CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("case_id,activity,timestamp,resource\n")
            for i in range(1000):
                f.write(f"CASE_{i},Activity,2024-01-15T10:00:00,User\n")
            temp_path = f.name
        
        try:
            start_time = time.time()
            
            with open(temp_path, 'rb') as f:
                response = requests.post(
                    f"{api_url}/upload/structured",
                    files={'file': ('large.csv', f, 'text/csv')},
                    data={'project_id': test_project},
                    timeout=60
                )
            
            elapsed = time.time() - start_time
            
            assert response.status_code == 200
            print(f"\n  ⏱️  Uploaded 1000 events in {elapsed:.2f}s")
        finally:
            Path(temp_path).unlink()

class TestDataIntegrity:
    """Test data integrity across operations"""
    
    def test_event_count_consistency(self, api_url, test_project, sample_csv):
        """Test that event counts are consistent"""
        # Count events in CSV
        df = pd.read_csv(sample_csv)
        expected_count = len(df)
        
        # Upload
        with open(sample_csv, 'rb') as f:
            response = requests.post(
                f"{api_url}/upload/structured",
                files={'file': ('test.csv', f, 'text/csv')},
                data={'project_id': test_project}
            )
        
        processed_count = response.json()['records_processed']
        
        # Get statistics
        time.sleep(2)
        response = requests.get(f"{api_url}/projects/{test_project}/statistics")
        stats_count = response.json()['statistics']['total_events']
        
        # All counts should match
        assert processed_count == expected_count
        # Stats might be higher due to previous tests, so just check it increased
        assert stats_count >= expected_count

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])