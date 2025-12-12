import os
import psycopg2
from psycopg2 import sql, extras
from dotenv import load_dotenv
import pandas as pd
import logging
from contextlib import contextmanager

load_dotenv()
logger = logging.getLogger(__name__)

# --- Database Configuration ---
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "process_db")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secret_password")

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def setup_db(conn):
    """Creates necessary extensions and tables"""
    try:
        with conn.cursor() as cur:
            # Enable PGVector extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # 1. Event Logs Table (simplified for Milestone 1)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS event_logs (
                    id SERIAL PRIMARY KEY,
                    case_id VARCHAR(255) NOT NULL,
                    activity VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    resource VARCHAR(255),
                    cost FLOAT DEFAULT 0.0,
                    location VARCHAR(255),
                    product_type VARCHAR(255),
                    log_file VARCHAR(255),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # 2. Documents Table (for unstructured data)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    content_text TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            # 3. Document Chunks Table (with embeddings)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER,
                    chunk_text TEXT NOT NULL,
                    embedding vector(384),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            conn.commit()
            logger.info("Database setup completed successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to setup database: {e}")
        raise

def store_structured_log(conn, df: pd.DataFrame, filename: str):
    """Store structured event log in database"""
    try:
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                cur.execute("""
                    INSERT INTO event_logs 
                    (case_id, activity, timestamp, resource, cost, location, product_type, log_file)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(row.get('case_id', '')),
                    str(row.get('activity', '')),
                    row.get('timestamp'),
                    str(row.get('resource', '')),
                    float(row.get('cost', 0.0)),
                    str(row.get('location', '')),
                    str(row.get('product_type', '')),
                    filename
                ))
        conn.commit()
        logger.info(f"Stored {len(df)} events from {filename}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error storing structured data: {e}")
        raise