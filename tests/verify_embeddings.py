from src.database import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Check event_logs table
cur.execute("SELECT COUNT(*) FROM event_logs WHERE embedding IS NOT NULL")
event_count = cur.fetchone()[0]
print(f"Events with embeddings: {event_count}")

# Check document_chunks table  
cur.execute("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
doc_count = cur.fetchone()[0]
print(f"Document chunks with embeddings: {doc_count}")

conn.close()