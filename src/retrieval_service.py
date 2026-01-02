import logging
from typing import List, Dict, Any, Optional
import re
from src.database import get_table_schema

logger = logging.getLogger(__name__)

def search_documents(cur, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
    """Semantic search over unstructured documentation"""
    query = """
        SELECT chunk_text, document_id, 1 - (embedding <=> %s) AS similarity
        FROM document_chunks ORDER BY similarity DESC LIMIT %s;
    """
    cur.execute(query, (query_embedding, top_k))
    return [{"text": r[0], "doc_id": r[1], "score": r[2]} for r in cur.fetchall()]

def search_event_logs(cur, query_embedding: List[float], query_text: str, top_k: int = 15) -> List[Dict]:
    """
    Optimized Hybrid Search:
    - Extracts Case IDs and Resources via Regex
    - Uses Vector Similarity for semantic relevance
    - Deduplicates results in Python to maintain ranking integrity
    """
    query_lower = query_text.lower()
    
    # 1. Improved ID Extraction
    # Matches 6-digit IDs or IDs mentioned after "case" or "application"
    case_ids = re.findall(r'\b(?:case|app|id)?[\s_-]*(\d{4,7})\b', query_lower)
    
    # 2. Base SQL Query 
    # Removed DISTINCT ON to fix the sorting/accuracy issue
    sql_query = """
        SELECT 
            case_id, 
            activity, 
            timestamp, 
            resource,
            cost,
            location,
            1 - (embedding <=> %s::vector) AS similarity
        FROM event_logs
        WHERE embedding IS NOT NULL
    """
    params = [query_embedding]
    filters = []

    # 3. Apply Filters (Hard filters only if IDs are explicitly mentioned)
    if case_ids:
        filters.append(f"case_id IN ({','.join(['%s'] * len(case_ids))})")
        params.extend(case_ids)

    # Resource filter (More lenient matching)
    resource_match = re.search(r'(?:resource|user|by)\s+(\d+)', query_lower)
    if resource_match:
        res_id = resource_match.group(1)
        # Match both '112' and '112.0' formats common in BPI datasets
        filters.append("(resource = %s OR resource = %s)")
        params.extend([res_id, f"{res_id}.0"])

    if filters:
        sql_query += " AND " + " AND ".join(filters)

    # 4. Sort by Similarity and fetch extra rows for deduplication
    sql_query += " ORDER BY similarity DESC LIMIT %s"
    params.append(top_k * 5) 

    try:
        cur.execute(sql_query, tuple(params))
        rows = cur.fetchall()
        
        # 5. Python Deduplication: Keep only the highest similarity event per Case ID
        seen_cases = {}
        for r in rows:
            cid = str(r[0])
            sim_score = float(r[6])
            
            if cid not in seen_cases or sim_score > seen_cases[cid]['score']:
                seen_cases[cid] = {
                    "case_id": cid,
                    "activity": str(r[1]),
                    "timestamp": str(r[2]),
                    "resource": str(r[3]),
                    "cost": float(r[4]) if r[4] else 0.0,
                    "location": str(r[5]) if r[5] else "",
                    "score": sim_score,
                    "text": f"Case {cid}: Activity '{r[1]}' performed by {r[3]}"
                }

        # Sort final dictionary by score and return top_k
        results = sorted(seen_cases.values(), key=lambda x: x['score'], reverse=True)[:top_k]
        
        if results:
            logger.info(f"Search Success: Found {len(results)} cases for query: '{query_text[:50]}...'")
        return results

    except Exception as e:
        logger.error(f"Search Error: {e}")
        return []


def rerank_results(results: List[Dict], query_keywords: List[str]) -> List[Dict]:
    """Apply business logic re-ranking"""
    for res in results:
        keyword_score = sum(2.0 for kw in query_keywords if kw.lower() in res.get('text', '').lower())
        res['final_score'] = res.get('similarity', res.get('score', 0)) + (keyword_score * 0.05)
        
    return sorted(results, key=lambda x: x['final_score'], reverse=True)