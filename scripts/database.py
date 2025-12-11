import os
import psycopg2
from psycopg2 import sql

# --- Database Configuration ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "process_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

def get_db_connection():
    """Establishes and returns a PostgreSQL connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def setup_db(conn):
    """
    Creates necessary extensions (PGVector) and tables in the database.
    This runs once at application startup.
    """
    with conn.cursor() as cur:
        # 1. Enable the vector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # 2. Create tables for structured data (Event Logs)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS event_logs (
                id SERIAL PRIMARY KEY,
                case_id VARCHAR(255) NOT NULL,
                activity VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                resource VARCHAR(255),
                event_type VARCHAR(50),
                log_file VARCHAR(255)
            );
        """)
        
        # 3. Create table for unstructured RAG data (Vectors)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS document_vectors (
                id SERIAL PRIMARY KEY,
                doc_name VARCHAR(255) NOT NULL,
                text_chunk TEXT NOT NULL,
                -- The vector type is enabled by the 'vector' extension
                embedding vector(384) 
            );
        """)
        
        conn.commit()
        print("INFO: Database structure (PGVector, tables) confirmed.")