"""
Unit Tests for Database Module
Tests all database operations and PGVector functionality
"""

import pytest
import os
from datetime import datetime
from scripts.database import Database


# --- Database Configuration ---
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "process_db")
DB_USER = os.getenv("DB_USER", "pm_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "pm_admin_786")
# Using environment variable for setup
DB_URL_FOR_SETUP = os.getenv('DATABASE_URL', f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

@pytest.fixture
def db():
    """Database fixture"""
    database = Database()
    yield database
    database.close()

@pytest.fixture
def test_project(db):
    """Create test project"""
    project_id = db.create_project(
        name="Test Project",
        description="Unit test project",
        dataset_type="structured"
    )
    yield project_id
    # Cleanup
    db.execute("DELETE FROM process_mining.projects WHERE id = %s", (project_id,))

class TestDatabaseConnection:
    """Test database connection and basic operations"""
    
    def test_connection(self, db):
        """Test database connection"""
        assert db.test_connection() == True
    
    def test_get_connection(self, db):
        """Test getting connection object"""
        conn = db.get_connection()
        assert conn is not None
        assert not conn.closed
    
    def test_execute_query(self, db):
        """Test executing simple query"""
        result = db.execute("SELECT 1 as test", fetch=True)
        assert result is not None
        assert len(result) == 1
        assert result[0]['test'] == 1

class TestProjectOperations:
    """Test project CRUD operations"""
    
    def test_create_project(self, db):
        """Test creating a new project"""
        project_id = db.create_project(
            name="Test Create Project",
            description="Testing project creation",
            dataset_type="structured"
        )
        assert isinstance(project_id, int)
        assert project_id > 0
        
        # Cleanup
        db.execute("DELETE FROM process_mining.projects WHERE id = %s", (project_id,))
    
    def test_get_project(self, db, test_project):
        """Test retrieving a project"""
        project = db.get_project(test_project)
        assert project is not None
        assert project['id'] == test_project
        assert project['name'] == "Test Project"
        assert project['dataset_type'] == "structured"
        assert project['status'] == "pending"
    
    def test_get_nonexistent_project(self, db):
        """Test getting project that doesn't exist"""
        project = db.get_project(999999)
        assert project is None
    
    def test_list_projects(self, db, test_project):
        """Test listing all projects"""
        projects = db.list_projects()
        assert isinstance(projects, list)
        assert len(projects) > 0
        assert any(p['id'] == test_project for p in projects)
    
    def test_update_project_status(self, db, test_project):
        """Test updating project status"""
        db.update_project_status(test_project, "processing")
        project = db.get_project(test_project)
        assert project['status'] == "processing"
        
        db.update_project_status(test_project, "completed")
        project = db.get_project(test_project)
        assert project['status'] == "completed"

class TestEventLogOperations:
    """Test event log operations"""
    
    def test_insert_single_event(self, db, test_project):
        """Test inserting a single event"""
        events = [{
            'case_id': 'TEST_001',
            'activity': 'Start',
            'timestamp': datetime.now(),
            'resource': 'TestUser',
            'cost': 10.0,
            'location': 'TestLocation',
            'product_type': 'TestProduct'
        }]
        
        db.insert_events(test_project, events)
        
        # Verify insertion
        result = db.execute("""
            SELECT * FROM process_mining.event_logs 
            WHERE project_id = %s AND case_id = 'TEST_001'
        """, (test_project,), fetch=True)
        
        assert len(result) == 1
        assert result[0]['activity'] == 'Start'
        assert result[0]['resource'] == 'TestUser'
    
    def test_insert_multiple_events(self, db, test_project):
        """Test bulk inserting events"""
        events = [
            {
                'case_id': f'CASE_{i}',
                'activity': 'Activity',
                'timestamp': datetime.now(),
                'resource': 'User',
                'cost': 5.0,
                'location': 'Location',
                'product_type': 'Product'
            }
            for i in range(100)
        ]
        
        db.insert_events(test_project, events)
        
        # Verify count
        result = db.execute("""
            SELECT COUNT(*) as count FROM process_mining.event_logs 
            WHERE project_id = %s
        """, (test_project,), fetch=True)
        
        assert result[0]['count'] >= 100

class TestEmbeddingOperations:
    """Test embedding storage and retrieval"""
    
    def test_insert_event_embedding(self, db, test_project):
        """Test inserting event embedding"""
        # First create an event
        events = [{
            'case_id': 'EMB_001',
            'activity': 'Test Activity',
            'timestamp': datetime.now(),
            'resource': 'User',
            'cost': 0,
            'location': None,
            'product_type': None
        }]
        db.insert_events(test_project, events)
        
        # Get event ID
        event = db.execute("""
            SELECT id FROM process_mining.event_logs 
            WHERE project_id = %s AND case_id = 'EMB_001'
        """, (test_project,), fetch=True)[0]
        
        # Insert embedding
        embedding = [0.1] * 384  # 384-dimensional vector
        db.insert_event_embedding(
            project_id=test_project,
            event_id=event['id'],
            event_text="Test event text",
            embedding=embedding
        )
        
        # Verify
        result = db.execute("""
            SELECT * FROM process_mining.event_embeddings 
            WHERE event_id = %s
        """, (event['id'],), fetch=True)
        
        assert len(result) == 1
        assert result[0]['event_text'] == "Test event text"
    
    def test_insert_document_chunk(self, db, test_project):
        """Test inserting document chunk with embedding"""
        # First create a document
        doc_id = db.insert_document(
            project_id=test_project,
            filename="test.txt",
            file_type="txt",
            file_path="/test/test.txt",
            file_size=1000,
            content_text="Test content"
        )
        
        # Insert chunk
        embedding = [0.2] * 384
        db.insert_document_chunk(
            document_id=doc_id,
            project_id=test_project,
            chunk_index=0,
            chunk_text="This is a test chunk",
            embedding=embedding,
            metadata={'page': 1}
        )
        
        # Verify
        result = db.execute("""
            SELECT * FROM process_mining.document_chunks 
            WHERE document_id = %s
        """, (doc_id,), fetch=True)
        
        assert len(result) == 1
        assert result[0]['chunk_text'] == "This is a test chunk"
        assert result[0]['chunk_index'] == 0

class TestDocumentOperations:
    """Test document operations"""
    
    def test_insert_document(self, db, test_project):
        """Test inserting document metadata"""
        doc_id = db.insert_document(
            project_id=test_project,
            filename="test_doc.pdf",
            file_type="pdf",
            file_path="/path/to/test_doc.pdf",
            file_size=50000,
            content_text="Document content"
        )
        
        assert isinstance(doc_id, int)
        assert doc_id > 0
        
        # Verify
        result = db.execute("""
            SELECT * FROM process_mining.documents WHERE id = %s
        """, (doc_id,), fetch=True)
        
        assert len(result) == 1
        assert result[0]['filename'] == "test_doc.pdf"
        assert result[0]['file_type'] == "pdf"
    
    def test_update_document_chunk_count(self, db, test_project):
        """Test updating document chunk count"""
        doc_id = db.insert_document(
            project_id=test_project,
            filename="test.txt",
            file_type="txt",
            file_path="/test.txt",
            file_size=1000
        )
        
        db.update_document_chunk_count(doc_id, 5)
        
        result = db.execute("""
            SELECT chunk_count FROM process_mining.documents WHERE id = %s
        """, (doc_id,), fetch=True)
        
        assert result[0]['chunk_count'] == 5

class TestVectorSearch:
    """Test vector similarity search operations"""
    
    def test_search_similar_events(self, db, test_project):
        """Test searching for similar events"""
        # Create test events with embeddings
        events = [{
            'case_id': 'SEARCH_001',
            'activity': 'Search Test',
            'timestamp': datetime.now(),
            'resource': 'User',
            'cost': 0,
            'location': None,
            'product_type': None
        }]
        db.insert_events(test_project, events)
        
        event = db.execute("""
            SELECT id FROM process_mining.event_logs 
            WHERE case_id = 'SEARCH_001'
        """, fetch=True)[0]
        
        # Insert embedding
        test_embedding = [0.1] * 384
        db.insert_event_embedding(
            project_id=test_project,
            event_id=event['id'],
            event_text="Search test event",
            embedding=test_embedding
        )
        
        # Search
        query_embedding = [0.15] * 384  # Similar vector
        results = db.search_similar_events(query_embedding, test_project, limit=5)
        
        assert isinstance(results, list)
        # Should find at least our test event
        assert len(results) > 0
    
    def test_search_similar_documents(self, db, test_project):
        """Test searching for similar document chunks"""
        # Create document with chunk
        doc_id = db.insert_document(
            project_id=test_project,
            filename="search_test.txt",
            file_type="txt",
            file_path="/test.txt",
            file_size=100
        )
        
        embedding = [0.3] * 384
        db.insert_document_chunk(
            document_id=doc_id,
            project_id=test_project,
            chunk_index=0,
            chunk_text="Searchable chunk text",
            embedding=embedding
        )
        
        # Search
        query_embedding = [0.35] * 384
        results = db.search_similar_documents(query_embedding, test_project, limit=5)
        
        assert isinstance(results, list)
        assert len(results) > 0

class TestTransactions:
    """Test transaction handling"""
    
    def test_rollback_on_error(self, db):
        """Test that transactions rollback on error"""
        initial_count = db.execute(
            "SELECT COUNT(*) as count FROM process_mining.projects",
            fetch=True
        )[0]['count']
        
        # Try to create project with invalid dataset_type
        try:
            db.execute("""
                INSERT INTO process_mining.projects (name, dataset_type)
                VALUES (%s, %s)
            """, ("Invalid Project", "invalid_type"))
        except:
            pass  # Expected to fail
        
        # Verify count unchanged
        final_count = db.execute(
            "SELECT COUNT(*) as count FROM process_mining.projects",
            fetch=True
        )[0]['count']
        
        assert initial_count == final_count

class TestPerformance:
    """Test database performance"""
    
    def test_bulk_insert_performance(self, db, test_project):
        """Test bulk insert performance"""
        import time
        
        events = [
            {
                'case_id': f'PERF_{i}',
                'activity': 'Performance Test',
                'timestamp': datetime.now(),
                'resource': 'User',
                'cost': 1.0,
                'location': 'Location',
                'product_type': 'Product'
            }
            for i in range(1000)
        ]
        
        start_time = time.time()
        db.insert_events(test_project, events)
        elapsed = time.time() - start_time
        
        # Should insert 1000 events in reasonable time
        assert elapsed < 10.0  # Less than 10 seconds
        print(f"\n  ⏱️  Inserted 1000 events in {elapsed:.2f} seconds")
    
    def test_vector_search_performance(self, db, test_project):
        """Test vector search performance"""
        import time
        
        # Create some events with embeddings
        for i in range(10):
            events = [{
                'case_id': f'SEARCH_PERF_{i}',
                'activity': 'Search Performance',
                'timestamp': datetime.now(),
                'resource': 'User',
                'cost': 0,
                'location': None,
                'product_type': None
            }]
            db.insert_events(test_project, events)
            
            event = db.execute("""
                SELECT id FROM process_mining.event_logs 
                WHERE case_id = %s
            """, (f'SEARCH_PERF_{i}',), fetch=True)[0]
            
            embedding = [0.1 * i] * 384
            db.insert_event_embedding(
                project_id=test_project,
                event_id=event['id'],
                event_text=f"Search test {i}",
                embedding=embedding
            )
        
        # Test search speed
        query_embedding = [0.5] * 384
        start_time = time.time()
        results = db.search_similar_events(query_embedding, test_project, limit=10)
        elapsed = time.time() - start_time
        
        # Search should be fast (< 100ms)
        assert elapsed < 0.1
        print(f"\n  ⏱️  Vector search completed in {elapsed*1000:.2f}ms")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])