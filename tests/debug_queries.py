from src.database import get_db_connection
from src.embedding_service import get_model  
from src.retrieval_service import search_event_logs
import json

conn = get_db_connection()
model = get_model()

with open('src/rag/test_queries.json') as f:
    queries = json.load(f)

cur = conn.cursor()
for q in queries[:5]:  # Test first 5
    query_text = q['query']
    query_vector = model.encode([query_text])[0].tolist()
    results = search_event_logs(cur, query_vector, query_text, top_k=10)
    
    retrieved = [r['case_id'] for r in results]
    expected = [str(c) for c in q['expected_cases']]
    
    hit = any(c in retrieved for c in expected)
    status = "✅" if hit else "❌"
    
    print(f"{status} Query: {query_text}")
    print(f"   Expected: {expected[:3]}")
    print(f"   Got: {retrieved[:3]}")
    print()

conn.close()