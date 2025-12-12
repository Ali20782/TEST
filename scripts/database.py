# scripts/database.py

import os
from typing import List, Optional, Tuple, Any, Dict
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
DB_USER = os.getenv("DB_USER", "pm_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pm_admin_786")
# Using environment variable for test setup
DB_URL_FOR_SETUP = os.getenv('DATABASE_URL', f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

@contextmanager
def get_db_connection():
    """Context manager for PostgreSQL connection."""
    conn = None
    try:
        conn = psycopg2.connect(DB_URL_FOR_SETUP)
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def setup_db():
    """Creates necessary extensions and tables (Run once)."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Assuming the database name is process_db and the user process_admin exists
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # 1. Projects Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        status VARCHAR(50) DEFAULT 'created',
                        description TEXT,
                        log_file_name VARCHAR(255),
                        dataset_type VARCHAR(50)
                    );
                """)
                
                # 2. Event Logs Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS event_logs (
                        id SERIAL PRIMARY KEY,
                        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                        case_id VARCHAR(255) NOT NULL,
                        activity VARCHAR(255) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                        resource VARCHAR(255),
                        event_type VARCHAR(50),
                        log_file VARCHAR(255),
                        event_embedding vector(384)
                    );
                """)

                # 3. Documents Table (Metadata for RAG)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                        doc_name VARCHAR(255) NOT NULL,
                        doc_type VARCHAR(50) NOT NULL,
                        chunk_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)

                # 4. Document Vectors Table (Unstructured RAG data)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS document_vectors (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                        project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                        text_chunk TEXT NOT NULL,
                        chunk_index INTEGER,
                        embedding vector(384)
                    );
                """)
                
                conn.commit()
                # print("INFO: Database structure (PGVector, tables) confirmed.") # Removed print for clean test output
    except Exception as e:
        logger.error(f"Failed to setup database tables: {e}")
        # Re-raise for test environment visibility
        # raise

class Database:
    """Provides a functional interface for database operations."""
    
    def __init__(self):
        # Ensure setup is run once when the class is instantiated
        # Note: In a production environment, this should be run outside of the app startup
        setup_db()

    def get_connection(self):
        """Returns a raw connection object (used primarily for test_connection)."""
        return psycopg2.connect(DB_URL_FOR_SETUP)

    def close(self):
        """Placeholder for closing resources (required by test_database.py fixture)."""
        pass

    def test_connection(self):
        """Checks if a connection can be established."""
        try:
            with get_db_connection():
                return True
        except Exception:
            return False

    def execute(self, query: str, params: Optional[Tuple] = None, fetch: bool = False) -> Optional[List[Dict[str, Any]]]:
        """
        Executes a query and optionally fetches results, returning a list of dictionaries.
        Required for test_database.py assertions.
        """
        result = None
        with get_db_connection() as conn:
            try:
                # Use RealDictCursor to return results as dictionaries
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur: 
                    cur.execute(query, params)
                    if fetch:
                        result = cur.fetchall()
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                raise e

    # --- Project Operations ---

    def create_project(self, name: str, description: Optional[str] = None, log_file_name: Optional[str] = None, dataset_type: Optional[str] = 'event_log') -> int:
        """Creates a new project and returns its ID."""
        query = """
            INSERT INTO projects (name, description, log_file_name, dataset_type) 
            VALUES (%s, %s, %s, %s) 
            RETURNING id;
        """
        params = (name, description, log_file_name, dataset_type)
        result = self.execute(query, params, fetch=True)
        return result[0]['id'] if result else None
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a project by ID."""
        # Note: The 'status' key is expected by one of your integration tests.
        query = "SELECT id, name, status, description, log_file_name, dataset_type FROM projects WHERE id = %s;"
        result = self.execute(query, (project_id,), fetch=True)
        
        return result[0] if result else None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """Lists all projects."""
        query = "SELECT id, name, status, dataset_type FROM projects ORDER BY id DESC;"
        results = self.execute(query, fetch=True)
        return results if results is not None else []

    def update_project_status(self, project_id: int, status: str):
        """Updates the status of a project."""
        query = "UPDATE projects SET status = %s WHERE id = %s;"
        self.execute(query, (status, project_id))

    # --- Event Log Operations ---
    
    def insert_multiple_events(self, df: pd.DataFrame, project_id: int, log_file: str) -> int:
        """Bulk inserts canonical event log data using psycopg2.extras.execute_values."""
        with get_db_connection() as conn:
            try:
                df['project_id'] = project_id
                df['log_file'] = log_file
                
                columns = ['project_id', 'case_id', 'activity', 'timestamp', 'resource', 'event_type', 'log_file']
                
                # Convert DataFrame to a list of tuples, handling NaT/None
                records = [
                    tuple(row[col] if pd.notna(row[col]) else None for col in columns)
                    for index, row in df.iterrows()
                ]

                query = sql.SQL(
                    "INSERT INTO event_logs ({}) VALUES %s"
                ).format(sql.SQL(', ').join(map(sql.Identifier, columns)))
                
                with conn.cursor() as cur:
                    extras.execute_values(cur, query, records, page_size=1000)

                conn.commit()
                return len(records)
            except Exception as e:
                conn.rollback()
                raise e

    def retrieve_events(self, project_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves events for a project."""
        query = "SELECT case_id, activity, timestamp, resource FROM event_logs WHERE project_id = %s LIMIT %s;"
        results = self.execute(query, (project_id, limit), fetch=True)
        return results if results is not None else []
        
    def get_event_statistics(self, project_id: int) -> Dict[str, Any]:
        """Calculates basic event log statistics."""
        # Simple count query
        total_events = self.execute("SELECT COUNT(*) AS count FROM event_logs WHERE project_id = %s;", (project_id,), fetch=True)[0]['count']
        total_cases = self.execute("SELECT COUNT(DISTINCT case_id) AS count FROM event_logs WHERE project_id = %s;", (project_id,), fetch=True)[0]['count']
        total_activities = self.execute("SELECT COUNT(DISTINCT activity) AS count FROM event_logs WHERE project_id = %s;", (project_id,), fetch=True)[0]['count']
        
        return {
            "total_events": total_events,
            "total_cases": total_cases,
            "total_activities": total_activities
        }

    # --- Document/Embedding Operations ---

    def insert_document(self, project_id: int, doc_name: str, doc_type: str = 'text') -> int:
        """Inserts document metadata and returns the ID."""
        query = "INSERT INTO documents (project_id, doc_name, doc_type) VALUES (%s, %s, %s) RETURNING id;"
        result = self.execute(query, (project_id, doc_name, doc_type), fetch=True)
        return result[0]['id'] if result else None

    def update_document_chunk_count(self, doc_id: int, chunk_count: int):
        """Updates the number of chunks for a document."""
        query = "UPDATE documents SET chunk_count = %s WHERE id = %s;"
        self.execute(query, (chunk_count, doc_id))

    def insert_document_chunk(self, document_id: int, project_id: int, text_chunk: str, embedding: List[float], chunk_index: int):
        """Inserts a single document chunk with its vector."""
        query = """
            INSERT INTO document_vectors (document_id, project_id, text_chunk, embedding, chunk_index) 
            VALUES (%s, %s, %s, %s, %s);
        """
        # Convert embedding list to string representation for PGVector
        vector_str = "[" + ",".join(map(str, embedding)) + "]"
        self.execute(query, (document_id, project_id, text_chunk, vector_str, chunk_index))