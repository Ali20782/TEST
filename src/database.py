import os
import psycopg2
from psycopg2 import sql, extras
from dotenv import load_dotenv
import pandas as pd
import logging
from typing import Dict

from .embedding_service import generate_embeddings
from .data_processing_service import format_event_for_embedding

load_dotenv()
logger = logging.getLogger(__name__)

def get_db_connection():
    host = os.getenv("DB_HOST", "db") 
    try:
        conn = psycopg2.connect(
            host=host,
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "process_db"),
            user=os.getenv("DB_USER", "pm_admin"),
            password=os.getenv("DB_PASSWORD", "pm_admin_786"),
            connect_timeout=5
        )
        return conn
    except psycopg2.OperationalError:
        # Fallback for local development outside Docker
        return psycopg2.connect(
            host="localhost",
            port="5432",
            database="process_db",
            user="pm_admin",
            password="pm_admin_786"
        )

def get_table_schema(conn, table_name: str = "event_logs") -> Dict[str, str]:
    """Dynamically fetches column names and data types to handle any business dataset."""
    schema = {}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
            """, (table_name,))
            for row in cur.fetchall():
                schema[row[0]] = row[1]
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
    return schema

def setup_db(conn):
    """Creates necessary extensions and tables"""
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
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
                    embedding vector(384),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    content_text TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
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
            logger.info("Database setup completed")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed setup: {e}")
        raise

def store_structured_log(conn, df: pd.DataFrame, filename: str):
    try:
        # Pre-processing: Clean Case IDs to prevent string mismatch
        df['case_id'] = df['case_id'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        texts_to_embed = [format_event_for_embedding(row) for _, row in df.iterrows()]
        embeddings = generate_embeddings(texts_to_embed)

        with conn.cursor() as cur:
            data_to_insert = []
            for (_, row), emb in zip(df.iterrows(), embeddings):
                data_to_insert.append((
                    row['case_id'],
                    str(row.get('activity', 'Unknown')),
                    row.get('timestamp'),
                    str(row.get('resource', 'Unknown')).replace('.0', ''),
                    float(row.get('cost', 0.0)),
                    str(row.get('location', '')),
                    str(row.get('product_type', '')),
                    filename,
                    emb
                ))

            insert_query = """
                INSERT INTO event_logs 
                (case_id, activity, timestamp, resource, cost, location, product_type, log_file, embedding)
                VALUES %s
            """
            extras.execute_values(cur, insert_query, data_to_insert)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Storage error: {e}")