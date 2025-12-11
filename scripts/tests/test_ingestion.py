import pytest
from starlette.testclient import TestClient
from fastapi import status
from io import BytesIO

def test_upload_structured_csv_success(client: TestClient, mock_csv_file):
    """Integration test for successful CSV upload."""
    filename, file_io, mime_type = mock_csv_file
    
    response = client.post(
        "/upload", 
        files={"file": (filename, file_io, mime_type)}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "dataset_id" in response.json()
    assert "log processed" in response.json()["status"]

def test_upload_structured_csv_invalid_data(client: TestClient, mock_invalid_csv_file):
    """Integration test for CSV upload with invalid/missing columns."""
    filename, file_io, mime_type = mock_invalid_csv_file
    
    response = client.post(
        "/upload", 
        files={"file": (filename, file_io, mime_type)}
    )
    
    # Expect 422 Unprocessable Entity due to validation failure
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Data validation failed" in response.json()["detail"]


def test_upload_unstructured_txt_success(client: TestClient, mock_txt_file):
    """Integration test for successful TXT upload."""
    filename, file_io, mime_type = mock_txt_file
    
    response = client.post(
        "/upload", 
        files={"file": (filename, file_io, mime_type)}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "dataset_id" in response.json()
    assert "chunks, and indexed" in response.json()["status"]

def test_upload_unstructured_docx_success(client: TestClient, mock_docx_file):
    """Integration test for successful DOCX upload."""
    filename, file_io, mime_type = mock_docx_file
    
    response = client.post(
        "/upload", 
        files={"file": (filename, file_io, mime_type)}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "dataset_id" in response.json()
    assert "chunks, and indexed" in response.json()["status"]

def test_upload_unsupported_file_type(client: TestClient):
    """Integration test for an unsupported file type (e.g., JPEG)."""
    # Create a dummy image file mock
    dummy_file = ("unsupported.jpg", BytesIO(b"data"), "image/jpeg")
    
    response = client.post(
        "/upload", 
        files={"file": dummy_file}
    )
    
    # Expect 400 Bad Request due to unsupported extension
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file type" in response.json()["detail"]

# Note: To test XLSX, you would need to create a mock openpyxl file stream, 
# which is complex but follows the same pattern as mock_docx_file.