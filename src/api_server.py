import os
import time
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import psycopg2
from fastapi import BackgroundTasks

from src.rag.rag_service import ProcessRAGService
from src.embedding_service import get_model
from src import database, data_processing_service, embedding_service

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
            "ingest_unstructured": "/ingest/unstructured",
            "ask_query": "/query"
        }
    }

# ----------------------------------------------------
# Ingestion Endpoints
# ----------------------------------------------------

@app.post("/ingest/structured", summary="Ingest Structured Data (CSV/XLSX)")
async def ingest_structured_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Ingest structured event log files (CSV or XLSX)
    For large files (>100K rows), processing happens in background
    """
    try:
        logger.info(f"Receiving file: {file.filename}")
        
        # Read and validate file
        file_bytes = await file.read()
        df, metrics = data_processing_service.process_structured_data(
            file_bytes, 
            file.filename
        )
        
        # Check if large file
        if len(df) > 100000:
            # Schedule background processing
            background_tasks.add_task(
                process_large_file_background,
                df, 
                file.filename
            )
            
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "filename": file.filename,
                    "status": "Processing in background (large file)",
                    "metrics": metrics,
                    "message": "Check /ingestion/status endpoint for progress"
                }
            )
        else:
            # Process immediately for small files
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

def process_large_file_background(df, filename):
    """Background task for large file processing"""
    try:
        conn = database.get_db_connection()
        embedding_service.store_structured_log(conn, df, filename)
        conn.close()
        logger.info(f"✅ Background processing complete for {filename}")
    except Exception as e:
        logger.error(f"Background processing failed: {e}")

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
    

"""
Initialise the RAG service (outside the route if needed for performance in the future)
or inside a dependency injection block.
"""
@app.post("/query", summary="Ask questions about process data")
async def query_process_data(question: str, top_k: int = 5):
    """
        RAG Endpoint: Use Gemini/GPT to answer questions based on 
        ingested logs and documents.
    """
    try:
        conn = database.get_db_connection()
        # Generate embedding for the question
        model = get_model()
        query_vector = model.encode([question])[0].tolist()
        
        # Run RAG Pipeline
        rag_service = ProcessRAGService(conn)
        result = rag_service.query(question, query_vector)
        
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))