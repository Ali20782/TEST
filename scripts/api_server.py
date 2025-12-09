"""
FastAPI Backend Server for Process Mining Platform
Milestone 2: Data Ingestion APIs with PostgreSQL/PGVector
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import pandas as pd
import os
from datetime import datetime
import logging
from pathlib import Path

# Import custom modules
from scripts.database import Database, get_db
from scripts.file_processors import (
    process_structured_file,
    process_unstructured_file,
    validate_file_type
)
from scripts.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Process Mining Intelligence Platform API",
    description="Backend API for AI-powered conversational process intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
embedding_service = EmbeddingService()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    services: dict

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    dataset_type: str
    status: str
    created_at: str
    file_size: Optional[int]

class UploadResponse(BaseModel):
    project_id: int
    message: str
    filename: str
    file_type: str
    file_size: int
    records_processed: Optional[int] = None
    chunks_created: Optional[int] = None
    status: str

# ============================================================================
# STARTUP / SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Process Mining API Server...")
    
    # Create upload directories
    os.makedirs("uploads/structured", exist_ok=True)
    os.makedirs("uploads/unstructured", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Test database connection
    try:
        db = Database()
        db.test_connection()
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        raise
    
    # Load embedding model
    try:
        embedding_service.load_model()
        logger.info("✅ Embedding model loaded")
    except Exception as e:
        logger.error(f"❌ Embedding model failed to load: {str(e)}")
        raise
    
    logger.info("✅ API Server ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down API Server...")

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/", tags=["Status"])
async def root():
    """Root endpoint"""
    return {
        "message": "Process Mining Intelligence Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check(db: Database = Depends(get_db)):
    """
    Comprehensive health check endpoint
    Returns status of all critical services
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "unknown",
        "services": {}
    }
    
    # Check database connection
    try:
        db_healthy = db.test_connection()
        health_status["database"] = "connected" if db_healthy else "disconnected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check embedding service
    try:
        model_loaded = embedding_service.model is not None
        health_status["services"]["embedding_model"] = "loaded" if model_loaded else "not_loaded"
    except Exception as e:
        health_status["services"]["embedding_model"] = f"error: {str(e)}"
    
    # Check file system
    try:
        upload_dir = Path("uploads")
        health_status["services"]["file_system"] = "writable" if upload_dir.exists() else "not_accessible"
    except Exception as e:
        health_status["services"]["file_system"] = f"error: {str(e)}"
    
    return health_status

# ============================================================================
# PROJECT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/projects", response_model=ProjectResponse, tags=["Projects"])
async def create_project(
    name: str = Form(...),
    description: str = Form(None),
    dataset_type: str = Form(..., regex="^(structured|unstructured|hybrid)$"),
    db: Database = Depends(get_db)
):
    """
    Create a new project
    
    - **name**: Project name
    - **description**: Optional project description
    - **dataset_type**: Type of data (structured/unstructured/hybrid)
    """
    try:
        project_id = db.create_project(name, description, dataset_type)
        project = db.get_project(project_id)
        
        return ProjectResponse(
            id=project['id'],
            name=project['name'],
            description=project['description'],
            dataset_type=project['dataset_type'],
            status=project['status'],
            created_at=project['created_at'].isoformat(),
            file_size=project['file_size']
        )
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.get("/projects", response_model=List[ProjectResponse], tags=["Projects"])
async def list_projects(db: Database = Depends(get_db)):
    """List all projects"""
    try:
        projects = db.list_projects()
        return [
            ProjectResponse(
                id=p['id'],
                name=p['name'],
                description=p['description'],
                dataset_type=p['dataset_type'],
                status=p['status'],
                created_at=p['created_at'].isoformat(),
                file_size=p['file_size']
            ) for p in projects
        ]
    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def get_project(project_id: int, db: Database = Depends(get_db)):
    """Get project details"""
    try:
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse(
            id=project['id'],
            name=project['name'],
            description=project['description'],
            dataset_type=project['dataset_type'],
            status=project['status'],
            created_at=project['created_at'].isoformat(),
            file_size=project['file_size']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# DATA INGESTION ENDPOINTS - STRUCTURED
# ============================================================================

@app.post("/upload/structured", response_model=UploadResponse, tags=["Data Ingestion"])
async def upload_structured_data(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Database = Depends(get_db)
):
    """
    Upload structured event log data (CSV/XLSX)
    
    Expected columns: case_id, activity, timestamp, resource (optional), 
                     cost (optional), location (optional)
    """
    logger.info(f"Receiving structured file upload: {file.filename}")
    
    # Validate file type
    if not validate_file_type(file.filename, ['csv', 'xlsx', 'xls']):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: CSV, XLSX, XLS"
        )
    
    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Save file
        file_path = f"uploads/structured/{project_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = os.path.getsize(file_path)
        
        # Update project status
        db.update_project_status(project_id, "processing")
        
        # Process structured file
        result = process_structured_file(
            file_path,
            project_id,
            db,
            embedding_service
        )
        
        # Update project with file info
        db.execute("""
            UPDATE process_mining.projects 
            SET file_path = %s, file_size = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (file_path, file_size, project_id))
        
        # Update status to completed
        db.update_project_status(project_id, "completed")
        
        logger.info(f"✅ Structured file processed: {result['records_processed']} records")
        
        return UploadResponse(
            project_id=project_id,
            message="Structured data uploaded and processed successfully",
            filename=file.filename,
            file_type="structured",
            file_size=file_size,
            records_processed=result['records_processed'],
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to process structured file: {str(e)}")
        db.update_project_status(project_id, "failed")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# ============================================================================
# DATA INGESTION ENDPOINTS - UNSTRUCTURED
# ============================================================================

@app.post("/upload/unstructured", response_model=UploadResponse, tags=["Data Ingestion"])
async def upload_unstructured_data(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Database = Depends(get_db)
):
    """
    Upload unstructured documents (TXT/DOCX/PDF)
    
    Documents will be:
    - Extracted to text
    - Chunked into segments
    - Embedded with SentenceTransformers
    - Stored in PGVector for RAG
    """
    logger.info(f"Receiving unstructured file upload: {file.filename}")
    
    # Validate file type
    if not validate_file_type(file.filename, ['txt', 'docx', 'pdf']):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: TXT, DOCX, PDF"
        )
    
    # Verify project exists
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Save file
        file_path = f"uploads/unstructured/{project_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = os.path.getsize(file_path)
        
        # Update project status
        db.update_project_status(project_id, "processing")
        
        # Process unstructured file
        result = process_unstructured_file(
            file_path,
            project_id,
            db,
            embedding_service
        )
        
        # Update project status
        db.update_project_status(project_id, "completed")
        
        logger.info(f"✅ Unstructured file processed: {result['chunks_created']} chunks")
        
        return UploadResponse(
            project_id=project_id,
            message="Unstructured document uploaded and processed successfully",
            filename=file.filename,
            file_type="unstructured",
            file_size=file_size,
            chunks_created=result['chunks_created'],
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to process unstructured file: {str(e)}")
        db.update_project_status(project_id, "failed")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# ============================================================================
# DATA RETRIEVAL ENDPOINTS
# ============================================================================

@app.get("/projects/{project_id}/events", tags=["Data Retrieval"])
async def get_project_events(
    project_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Database = Depends(get_db)
):
    """Retrieve event logs for a project"""
    try:
        events = db.execute("""
            SELECT id, case_id, activity, timestamp, resource, cost, location
            FROM process_mining.event_logs
            WHERE project_id = %s
            ORDER BY timestamp
            LIMIT %s OFFSET %s
        """, (project_id, limit, offset), fetch=True)
        
        return {
            "project_id": project_id,
            "count": len(events),
            "events": events
        }
    except Exception as e:
        logger.error(f"Failed to retrieve events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}/statistics", tags=["Data Retrieval"])
async def get_project_statistics(project_id: int, db: Database = Depends(get_db)):
    """Get project statistics"""
    try:
        stats = db.execute("""
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT case_id) as total_cases,
                COUNT(DISTINCT activity) as total_activities,
                MIN(timestamp) as start_date,
                MAX(timestamp) as end_date
            FROM process_mining.event_logs
            WHERE project_id = %s
        """, (project_id,), fetch=True)
        
        return {
            "project_id": project_id,
            "statistics": stats[0] if stats else {}
        }
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================================================
# RUN SERVER (for local development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")