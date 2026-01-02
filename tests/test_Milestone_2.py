"""
Milestone 2 Integration Tests
Tests deployment, health checks, and basic ingestion
"""

import pytest
import requests
import tempfile
from pathlib import Path

BASE_URL = "http://localhost:8000"

@pytest.fixture
def sample_csv():
    """Create sample CSV file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("case_id,activity,timestamp,resource\n")
        f.write("CASE_001,Start,2024-01-01T10:00:00,User1\n")
        f.write("CASE_001,Complete,2024-01-01T11:00:00,User1\n")
        f.write("CASE_002,Start,2024-01-02T10:00:00,User2\n")
        f.write("CASE_002,Complete,2024-01-02T11:00:00,User2\n")
        temp_path = f.name
    
    yield temp_path
    Path(temp_path).unlink()

@pytest.fixture
def sample_txt():
    """Create sample text file"""
    content = """
    Process Mining Documentation
    
    This document describes invoice approval processes.
    It includes information about bottlenecks and variants.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    Path(temp_path).unlink()

class TestDeployment:
    """Test that the deployment is working"""
    
    def test_api_is_accessible(self):
        """Test API is running and accessible"""
        try:
            response = requests.get(BASE_URL, timeout=5)
            assert response.status_code == 200
            print("✅ API is accessible")
        except requests.exceptions.ConnectionError:
            pytest.fail("❌ API is not accessible. Ensure docker-compose is running.")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        print("✅ Health check passed")
    
    def test_swagger_docs(self):
        """Test Swagger documentation is accessible"""
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        assert response.status_code == 200
        print("✅ Swagger docs accessible")

class TestStructuredIngestion:
    """Test structured data ingestion"""
    
    def test_ingest_csv(self, sample_csv):
        """Test CSV file ingestion"""
        with open(sample_csv, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/ingest/structured",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["filename"] == "test.csv"
        assert data["status"] == "Structured data successfully ingested and stored."
        assert "metrics" in data
        assert data["metrics"]["total_events"] == 4
        assert data["metrics"]["unique_cases"] == 2
        print(f"✅ CSV ingestion successful: {data['metrics']['total_events']} events")
    
    def test_ingest_invalid_csv(self):
        """Test rejection of invalid CSV"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("wrong,columns\n")
            f.write("data1,data2\n")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = requests.post(
                    f"{BASE_URL}/ingest/structured",
                    files={"file": ("invalid.csv", f, "text/csv")}
                )
            
            assert response.status_code == 400
            assert "Missing required columns" in response.json()["detail"]
            print("✅ Invalid CSV correctly rejected")
        finally:
            Path(temp_path).unlink()

class TestUnstructuredIngestion:
    """Test unstructured data ingestion"""
    
    def test_ingest_txt(self, sample_txt):
        """Test TXT file ingestion"""
        with open(sample_txt, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/ingest/unstructured",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["status"] == "Unstructured data successfully chunked and vectorised."
        assert "metrics" in data
        assert data["metrics"]["character_count"] > 0
        assert data["metrics"]["total_chunks"] > 0
        print(f"✅ TXT ingestion successful: {data['metrics']['total_chunks']} chunks")

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_endpoint(self):
        """Test accessing non-existent endpoint"""
        response = requests.get(f"{BASE_URL}/nonexistent")
        assert response.status_code == 404
        print("✅ 404 handling works")
    
    def test_method_not_allowed(self):
        """Test using wrong HTTP method"""
        response = requests.get(f"{BASE_URL}/ingest/structured")
        assert response.status_code == 405
        print("✅ 405 handling works")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
