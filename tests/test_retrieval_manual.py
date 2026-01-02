from src.database import get_db_connection
from src.embedding_service import get_model
from src.retrieval_service import search_event_logs

conn = get_db_connection()
model = get_model()

# Test query
query = "Which cases involved Manager Approval?"
query_embedding = model.encode([query])[0].tolist()

# Search
cur = conn.cursor()
results = search_event_logs(cur, query_embedding, top_k=5)

print(f"Query: {query}")
print(f"\nTop 5 results:")
for i, res in enumerate(results, 1):
    print(f"{i}. Case {res['case_id']}: {res['activity']} (score: {res['score']:.3f})")

conn.close()