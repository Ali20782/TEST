import pytest
import pandas as pd
from src.services.data_processing_service import DataProcessingService

# Initialize the service with a mock connection (None)
@pytest.fixture
def data_service():
    return DataProcessingService(db_conn=None)

def test_process_structured_log_success(data_service, mock_csv_file, project_id):
    """Test successful processing of a valid event log."""
    filename, file_io, _ = mock_csv_file
    result = data_service.process_structured_log(file_io, filename, project_id)
    
    assert "dataset_id" in result
    assert result["dataset_id"].startswith("LOG-")
    assert "processed and indexed" in result["status"]
    
def test_process_structured_log_invalid(data_service, mock_invalid_csv_file, project_id):
    """Test failure when event log is missing required columns."""
    filename, file_io, _ = mock_invalid_csv_file
    
    with pytest.raises(ValueError) as excinfo:
        data_service.process_structured_log(file_io, filename, project_id)
        
    assert "missing required columns" in str(excinfo.value)
    
def test_process_unstructured_doc_txt_success(data_service, mock_txt_file, project_id):
    """Test successful processing of a TXT document."""
    filename, file_io, _ = mock_txt_file
    result = data_service.process_unstructured_doc(file_io, filename, project_id)
    
    assert "dataset_id" in result
    assert result["dataset_id"].startswith("DOC-")
    assert "chunks, and indexed" in result["status"]

def test_process_unstructured_doc_docx_success(data_service, mock_docx_file, project_id):
    """Test successful processing of a DOCX document."""
    filename, file_io, _ = mock_docx_file
    result = data_service.process_unstructured_doc(file_io, filename, project_id)
    
    assert "dataset_id" in result
    assert result["dataset_id"].startswith("DOC-")
    assert "chunks, and indexed" in result["status"]
    
def test_unsupported_file_type(data_service, project_id):
    """Test failure when an unsupported file type is passed."""
    mock_file = ("image.jpg", BytesIO(b"data"), "image/jpeg")
    filename, file_io, _ = mock_file
    
    # Check for general exception handling for unknown type in both structured and unstructured paths
    with pytest.raises(ValueError):
        data_service._load_structured_file(file_io, filename)
    
    with pytest.raises(ValueError):
        data_service._read_unstructured_file(file_io, filename)