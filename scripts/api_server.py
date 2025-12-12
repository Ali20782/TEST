import os
import time
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import psycopg2

from scripts import database, data_processing_service, embedding_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- App Initialization ---
app = FastAPI(
    title="Process Mining Platform API",
    description="Backend API for Process Mining with structured and unstructured data ingestion",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Ensure database connection and setup on startup"""
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database connection (attempt {attempt+1}/{max_retries})")
            conn = database.get_db_connection()
            database.setup_db(conn)
            conn.close()
            logger.info("✅ Database setup successful")
            return
        except psycopg2.OperationalError as e:
            logger.warning(f"Database connection failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ Could not connect to database after all retries")
                raise HTTPException(
                    status_code=500, 
                    detail="Database connection failed"
                )
        except Exception as e:
            logger.error(f"Unexpected error during startup: {e}")
            raise

# ----------------------------------------------------
# Health Check Endpoint
# ----------------------------------------------------

@app.get("/health", status_code=status.HTTP_200_OK, summary="API Health Check")
async def health_check():
    """Check the operational status of the API and database"""
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = "error"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "api_version": "1.0.0"
    }

# ----------------------------------------------------
# Root Endpoint
# ----------------------------------------------------

@app.get("/", summary="API Root")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Process Mining Platform API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "ingest_structured": "/ingest/structured",
            "ingest_unstructured": "/ingest/unstructured"
        }
    }

# ----------------------------------------------------
# Ingestion Endpoints
# ----------------------------------------------------

@app.post("/ingest/structured", summary="Ingest Structured Data (CSV/XLSX)")
async def ingest_structured_data(file: UploadFile = File(...)):
    """
    Ingest structured event log files (CSV or XLSX)
    
    Required columns: case_id, activity, timestamp
    Optional columns: resource, cost, location, product_type
    """
    try:
        logger.info(f"Receiving file: {file.filename}")
        
        # Read file
        file_bytes = await file.read()
        
        # Process structured data
        df, metrics = data_processing_service.process_structured_data(
            file_bytes, 
            file.filename
        )
        
        # Store in database
        conn = database.get_db_connection()
        try:
            embedding_service.store_structured_log(conn, df, file.filename)
            conn.close()
        except Exception as e:
            conn.close()
            raise
        
        logger.info(f"✅ Successfully processed {file.filename}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "filename": file.filename,
                "status": "Structured data successfully ingested and stored.",
                "metrics": metrics
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/ingest/unstructured", summary="Ingest Unstructured Data (TXT/DOCX)")
async def ingest_unstructured_data(file: UploadFile = File(...)):
    """
    Ingest unstructured documentation files (TXT or DOCX)
    
    Files are chunked and embeddings are generated for RAG pipeline
    """
    try:
        logger.info(f"Receiving file: {file.filename}")
        
        # Read file
        file_bytes = await file.read()
        
        # Extract text
        content = data_processing_service.extract_text_from_unstructured(
            file_bytes, 
            file.filename
        )
        
        # Chunk document
        chunks = data_processing_service.chunk_document(content)
        
        # Generate embeddings (placeholder for now)
        embeddings = embedding_service.generate_embeddings(chunks)
        
        # Store in database
        conn = database.get_db_connection()
        try:
            embedding_service.store_embeddings_in_pgvector(
                conn, 
                file.filename, 
                chunks, 
                embeddings
            )
            conn.close()
        except Exception as e:
            conn.close()
            raise
        
        logger.info(f"✅ Successfully processed {file.filename}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "filename": file.filename,
                "status": "Unstructured data successfully chunked and vectorised.",
                "metrics": {
                    "character_count": len(content),
                    "total_chunks": len(chunks),
                    "embeddings_generated": len(embeddings)
                }
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )