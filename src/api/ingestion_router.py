from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from typing import Dict, Any
from io import BytesIO

# Assuming these are defined elsewhere
# from dependencies import get_db_connection, get_project_id
from src.services.data_processing_service import DataProcessingService 

router = APIRouter(tags=["Ingestion"])

# Mock dependencies for demonstration
def get_db_connection():
    # Placeholder for database connection object
    return None 

def get_project_id():
    # Placeholder for authenticated user's project ID
    return "MOCK_PROJECT_ID"


@router.post(
    "/upload", 
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Structured (CSV/XLSX) or Unstructured (TXT/DOCX) Data",
    description="Accepts event logs for process mining or documents for RAG. Uses file extension to determine processing logic."
)
async def upload_file_for_processing(
    file: UploadFile = File(...), 
    db_conn: Any = Depends(get_db_connection), # Assuming DB connection is passed
    project_id: str = Depends(get_project_id) # Assuming security validates and returns project_id
):
    """
    Handles file upload and passes content to the DataProcessingService.
    """
    
    # Check file size (e.g., 50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the 50MB limit."
        )

    service = DataProcessingService(db_conn)
    
    # Read file content into memory buffer
    file_bytes = await file.read()
    file_io = BytesIO(file_bytes)
    
    # Determine file type based on extension
    filename = file.filename
    ext = filename.split('.')[-1].lower()

    try:
        if ext in ['csv', 'xlsx', 'xls']:
            result = service.process_structured_log(file_io, filename, project_id)
        elif ext in ['txt', 'docx']:
            result = service.process_unstructured_doc(file_io, filename, project_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: .{ext}. Only CSV, XLSX, TXT, and DOCX are allowed."
            )
        
        return result
        
    except ValueError as e:
        # Catch validation errors from the service
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data validation failed: {str(e)}"
        )
    except Exception as e:
        # Catch general processing errors (e.g., corrupted file)
        print(f"Processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during file processing."
        )