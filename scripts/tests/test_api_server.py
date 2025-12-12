"""
Comprehensive API Server Tests
Tests all FastAPI endpoints and middleware
"""

import pytest
from fastapi.testclient import TestClient
from scripts.api_server import app
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_csv():
    """Create a sample CSV file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("case_id,activity,timestamp,resource,cost,location\n")
        for i in range(10):
            f.write(f"CASE_{i:03d},Start,2024-01-{(i%28)+1:02d}T10:00:00,User1,10.0,Texas\n")
            f.write(f"CASE_{i:03d},Complete,2024-01-{(i%28)+1:02d}T11:00:00,User1,5.0,Texas\n")
        temp_path = f.name
    
    yield temp_path
    Path(temp_path).unlink()


@pytest.fixture
def sample_txt():
    """Create a sample text file for testing"""
    content = """
    Process Mining Documentation
    
    This document describes the invoice approval process in detail.
    The process starts with invoice creation and ends with payment.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    Path(temp_path).unlink()


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test health check returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "api_status" in data
        assert data["api_status"] == "ok"
    
    def test_health_check_structure(self, client):
        """Test health check response structure"""
        response = client.get("/health")
        data = response.json()
        
        assert isinstance(data, dict)
        assert "api_status" in data
        assert "database_status" in data


class TestStructuredIngestion:
    """Test structured data ingestion endpoints"""
    
    def test_ingest_csv_success(self, client, sample_csv):
        """Test successful CSV ingestion"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/ingest/structured",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "filename" in data
        assert "status" in data
        assert "metrics" in data
        assert data["status"] == "Structured data successfully ingested and stored."
    
    def test_ingest_csv_metrics(self, client, sample_csv):
        """Test CSV ingestion returns correct metrics"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/ingest/structured",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        data = response.json()
        metrics = data["metrics"]
        
        assert "total_events" in metrics
        assert "unique_cases" in metrics
        assert metrics["total_events"] == 20  # 10 cases * 2 activities
        assert metrics["unique_cases"] == 10
    
    def test_ingest_invalid_format(self, client):
        """Test ingestion with invalid file format"""
        content = b"Invalid content"
        
        response = client.post(
            "/ingest/structured",
            files={"file": ("test.exe", content, "application/octet-stream")}
        )
        
        assert response.status_code == 400
    
    def test_ingest_missing_columns(self, client):
        """Test ingestion with missing required columns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("wrong,columns\n")
            f.write("value1,value2\n")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/ingest/structured",
                    files={"file": ("invalid.csv", f, "text/csv")}
                )
            
            assert response.status_code == 400
            assert "Missing required columns" in response.json()["detail"]
        finally:
            Path(temp_path).unlink()
    
    def test_ingest_empty_file(self, client):
        """Test ingestion with empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("case_id,activity,timestamp\n")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/ingest/structured",
                    files={"file": ("empty.csv", f, "text/csv")}
                )
            
            # Should succeed but with 0 events
            assert response.status_code == 200
        finally:
            Path(temp_path).unlink()


class TestUnstructuredIngestion:
    """Test unstructured data ingestion endpoints"""
    
    def test_ingest_txt_success(self, client, sample_txt):
        """Test successful text file ingestion"""
        with open(sample_txt, 'rb') as f:
            response = client.post(
                "/ingest/unstructured",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "filename" in data
        assert "status" in data
        assert "metrics" in data
        assert data["status"] == "Unstructured data successfully chunked and vectorised."
    
    def test_ingest_txt_metrics(self, client, sample_txt):
        """Test text ingestion returns correct metrics"""
        with open(sample_txt, 'rb') as f:
            response = client.post(
                "/ingest/unstructured",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        data = response.json()
        metrics = data["metrics"]
        
        assert "character_count" in metrics
        assert "total_chunks" in metrics
        assert metrics["character_count"] > 0
        assert metrics["total_chunks"] > 0
    
    def test_ingest_invalid_unstructured_format(self, client):
        """Test ingestion with invalid unstructured format"""
        content = b"Invalid content"
        
        response = client.post(
            "/ingest/unstructured",
            files={"file": ("test.exe", content, "application/octet-stream")}
        )
        
        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_invalid_endpoint(self, client):
        """Test accessing non-existent endpoint"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method"""
        response = client.get("/ingest/structured")
        assert response.status_code == 405
    
    def test_missing_file(self, client):
        """Test ingestion without file"""
        response = client.post("/ingest/structured")
        assert response.status_code == 422  # Unprocessable Entity


class TestConcurrency:
    """Test concurrent request handling"""
    
    def test_multiple_health_checks(self, client):
        """Test handling multiple simultaneous health checks"""
        responses = [client.get("/health") for _ in range(10)]
        
        assert all(r.status_code == 200 for r in responses)
        assert all("api_status" in r.json() for r in responses)


class TestResponseFormat:
    """Test response format consistency"""
    
    def test_health_json_format(self, client):
        """Test health endpoint returns valid JSON"""
        response = client.get("/health")
        
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)
    
    def test_structured_ingestion_json_format(self, client, sample_csv):
        """Test structured ingestion returns valid JSON"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/ingest/structured",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)


class TestFileValidation:
    """Test file validation logic"""
    
    def test_csv_with_special_characters(self, client):
        """Test CSV with special characters in data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write("case_id,activity,timestamp,resource\n")
            f.write("CASE_001,Start™,2024-01-01T10:00:00,Üser\n")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/ingest/structured",
                    files={"file": ("special.csv", f, "text/csv")}
                )
            
            assert response.status_code == 200
        finally:
            Path(temp_path).unlink()
    
    def test_large_file_handling(self, client):
        """Test handling of larger files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("case_id,activity,timestamp,resource\n")
            for i in range(1000):
                f.write(f"CASE_{i},Activity,2024-01-01T10:00:00,User\n")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as f:
                response = client.post(
                    "/ingest/structured",
                    files={"file": ("large.csv", f, "text/csv")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["metrics"]["total_events"] == 1000
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
