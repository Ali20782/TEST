import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import psycopg2
from scripts import database, data_processing_service, embedding_service

# Load environment variables (for local testing outside Docker)
load_dotenv()

# --- App Initialisation ---
app = FastAPI(
    title="Conversational Process Intelligence API",
    description="Backend API for Process Mining and RAG-powered query handling.",
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    """Ensure database connection and enable PGVector extension on startup."""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            conn = database.get_db_connection()
            database.setup_db(conn) # Runs PGVector setup and table creation
            conn.close()
            print("INFO: Startup successful.")
            return
        except psycopg2.OperationalError as e:
            print(f"WARNING: DB connection failed (attempt {attempt+1}/{max_retries}). Retrying in 5s... Error: {e}")
            time.sleep(5)
    
    # If all retries fail, raise an error
    raise HTTPException(status_code=500, detail="Could not connect to the database after multiple retries.")

# ----------------------------------------------------
# Health Check Endpoint
# ----------------------------------------------------

@app.get("/health", status_code=status.HTTP_200_OK, summary="API Health Check")
async def health_check():
    """Checks the operational status of the API and its database connection."""
    try:
        conn = database.get_db_connection()
        conn.close()
        db_status = "ok"
    except Exception:
        db_status = "error"
    
    return {
        "api_status": "ok",
        "database_status": db_status
    }

# ----------------------------------------------------
# Ingestion Endpoints
# ----------------------------------------------------

@app.post("/ingest/structured", summary="Ingest Structured Data (CSV/XLSX)")
async def ingest_structured_data(file: UploadFile = File(...)):
    """Handles ingestion and processing of structured event logs."""
    try:
        file_bytes = await file.read()
        df, metrics = data_processing_service.process_structured_data(file_bytes, file.filename)
        
        # --- Database Insertion (Placeholder) ---
        conn = database.get_db_connection()
        embedding_service.store_structured_log(conn, df, file.filename)
        conn.close()
        # ----------------------------------------
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "filename": file.filename,
                "status": "Structured data successfully ingested and stored.",
                "metrics": metrics
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during structured ingestion: {e}")


@app.post("/ingest/unstructured", summary="Ingest Unstructured Data (TXT/DOCX)")
async def ingest_unstructured_data(file: UploadFile = File(...)):
    """Handles ingestion and vectorisation of unstructured documentation."""
    try:
        file_bytes = await file.read()
        content = data_processing_service.extract_text_from_unstructured(file_bytes, file.filename)
        
        # --- RAG Pipeline Steps (Placeholder) ---
        chunks = embedding_service.chunk_document(content)
        embeddings = embedding_service.generate_embeddings(chunks)
        
        conn = database.get_db_connection()
        embedding_service.store_embeddings_in_pgvector(conn, file.filename, chunks, embeddings)
        conn.close()
        # ----------------------------------------
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "filename": file.filename,
                "status": "Unstructured data successfully chunked and vectorised.",
                "metrics": {
                    "character_count": len(content),
                    "total_chunks": len(chunks)
                }
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during unstructured ingestion: {e}")