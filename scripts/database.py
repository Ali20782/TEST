"""
Database Module - PostgreSQL with PGVector Integration
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection_string = os.getenv(
            'DATABASE_URL',
            'postgresql://process_admin:ProcessMining2024!@localhost:5432/process_mining'
        )
        self._connection = None
    
    def get_connection(self):
        """Get database connection"""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
        return self._connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def execute(
        self,
        query: str,
        params: tuple = None,
        fetch: bool = False
    ) -> Optional[List[Dict]]:
        """Execute SQL query"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    def create_project(
        self,
        name: str,
        description: str = None,
        dataset_type: str = 'structured'
    ) -> int:
        """Create new project"""
        query = """
            INSERT INTO process_mining.projects (name, description, dataset_type)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        result = self.execute(query, (name, description, dataset_type), fetch=True)
        return result[0]['id']
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Get project by ID"""
        query = """
            SELECT * FROM process_mining.projects WHERE id = %s
        """
        result = self.execute(query, (project_id,), fetch=True)
        return result[0] if result else None
    
    def list_projects(self) -> List[Dict]:
        """List all projects"""
        query = """
            SELECT * FROM process_mining.projects 
            ORDER BY created_at DESC
        """
        return self.execute(query, fetch=True)
    
    def update_project_status(self, project_id: int, status: str):
        """Update project status"""
        query = """
            UPDATE process_mining.projects 
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        self.execute(query, (status, project_id))
    
    def insert_events(self, project_id: int, events: List[Dict]):
        """Bulk insert event logs"""
        query = """
            INSERT INTO process_mining.event_logs 
            (project_id, case_id, activity, timestamp, resource, cost, location, product_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        with self.get_cursor() as cursor:
            for event in events:
                cursor.execute(query, (
                    project_id,
                    event.get('case_id'),
                    event.get('activity'),
                    event.get('timestamp'),
                    event.get('resource'),
                    event.get('cost', 0.0),
                    event.get('location'),
                    event.get('product_type')
                ))
    
    def insert_event_embedding(
        self,
        project_id: int,
        event_id: int,
        event_text: str,
        embedding: List[float]
    ):
        """Insert event embedding"""
        query = """
            INSERT INTO process_mining.event_embeddings 
            (project_id, event_id, event_text, embedding)
            VALUES (%s, %s, %s, %s)
        """
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        self.execute(query, (project_id, event_id, event_text, embedding_str))
    
    def insert_document_chunk(
        self,
        document_id: int,
        project_id: int,
        chunk_index: int,
        chunk_text: str,
        embedding: List[float],
        metadata: Dict = None
    ):
        """Insert document chunk with embedding"""
        query = """
            INSERT INTO process_mining.document_chunks 
            (document_id, project_id, chunk_index, chunk_text, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        import json
        metadata_json = json.dumps(metadata) if metadata else None
        self.execute(query, (
            document_id,
            project_id,
            chunk_index,
            chunk_text,
            embedding_str,
            metadata_json
        ))
    
    def insert_document(
        self,
        project_id: int,
        filename: str,
        file_type: str,
        file_path: str,
        file_size: int,
        content_text: str = None
    ) -> int:
        """Insert document metadata"""
        query = """
            INSERT INTO process_mining.documents 
            (project_id, filename, file_type, file_path, file_size, content_text)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute(query, (
            project_id,
            filename,
            file_type,
            file_path,
            file_size,
            content_text
        ), fetch=True)
        return result[0]['id']
    
    def update_document_chunk_count(self, document_id: int, chunk_count: int):
        """Update document chunk count"""
        query = """
            UPDATE process_mining.documents 
            SET chunk_count = %s 
            WHERE id = %s
        """
        self.execute(query, (chunk_count, document_id))
    
    def search_similar_events(
        self,
        query_embedding: List[float],
        project_id: int = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search for similar events using vector similarity"""
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        if project_id:
            query = """
                SELECT 
                    ee.event_text,
                    el.case_id,
                    el.activity,
                    el.timestamp,
                    1 - (ee.embedding <=> %s::vector) as similarity
                FROM process_mining.event_embeddings ee
                JOIN process_mining.event_logs el ON ee.event_id = el.id
                WHERE ee.project_id = %s
                ORDER BY ee.embedding <=> %s::vector
                LIMIT %s
            """
            return self.execute(query, (embedding_str, project_id, embedding_str, limit), fetch=True)
        else:
            query = """
                SELECT 
                    ee.event_text,
                    el.case_id,
                    el.activity,
                    el.timestamp,
                    1 - (ee.embedding <=> %s::vector) as similarity
                FROM process_mining.event_embeddings ee
                JOIN process_mining.event_logs el ON ee.event_id = el.id
                ORDER BY ee.embedding <=> %s::vector
                LIMIT %s
            """
            return self.execute(query, (embedding_str, embedding_str, limit), fetch=True)
    
    def search_similar_documents(
        self,
        query_embedding: List[float],
        project_id: int = None,
        limit: int = 10
    ) -> List[Dict]:
        """Search for similar document chunks"""
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        if project_id:
            query = """
                SELECT 
                    dc.chunk_text,
                    d.filename,
                    dc.chunk_index,
                    1 - (dc.embedding <=> %s::vector) as similarity
                FROM process_mining.document_chunks dc
                JOIN process_mining.documents d ON dc.document_id = d.id
                WHERE dc.project_id = %s
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s
            """
            return self.execute(query, (embedding_str, project_id, embedding_str, limit), fetch=True)
        else:
            query = """
                SELECT 
                    dc.chunk_text,
                    d.filename,
                    dc.chunk_index,
                    1 - (dc.embedding <=> %s::vector) as similarity
                FROM process_mining.document_chunks dc
                JOIN process_mining.documents d ON dc.document_id = d.id
                ORDER BY dc.embedding <=> %s::vector
                LIMIT %s
            """
            return self.execute(query, (embedding_str, embedding_str, limit), fetch=True)
    
    def close(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

def get_db():
    """FastAPI dependency for database"""
    db = Database()
    try:
        yield db
    finally:
        pass