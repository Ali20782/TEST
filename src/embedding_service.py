import os
import logging
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from psycopg2.extras import execute_values


logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
# Global variable to persist the model in memory
_MODEL_INSTANCE = None
# Simple in-memory cache for embeddings
_EMBEDDING_CACHE = {}

def get_model():
    """
        Handle GPU/CPU fallback and model loading
    """
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading SentenceTransformer on {device}...")
        _MODEL_INSTANCE = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    return _MODEL_INSTANCE

def generate_embeddings(texts):
    model = get_model()
    
    # Check cache first
    needed_indices = [i for i, t in enumerate(texts) if t not in _EMBEDDING_CACHE]
    results = [None] * len(texts)

    # Fill from cache
    for i, text in enumerate(texts):
        if text in _EMBEDDING_CACHE:
            results[i] = _EMBEDDING_CACHE[text]

    if needed_indices:
        texts_to_encode = [texts[i] for i in needed_indices]
        
        # Process in chunks to avoid memory issues
        chunk_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
        all_embeddings = []
        
        logger.info(f"Generating embeddings for {len(texts_to_encode)} texts...")
        
        for i in range(0, len(texts_to_encode), chunk_size):
            chunk = texts_to_encode[i:i + chunk_size]
            chunk_embeddings = model.encode(
                chunk,
                show_progress_bar=False,  # Disable individual progress bars
                batch_size=128,
                convert_to_numpy=True
            )
            all_embeddings.extend(chunk_embeddings)
            
            # Log progress
            if (i + chunk_size) % 1000 == 0:
                logger.info(f"  Processed {i + chunk_size}/{len(texts_to_encode)} embeddings...")
        
        # Cache and store results
        for idx, embedding in zip(needed_indices, all_embeddings):
            emb_list = embedding.tolist()
            _EMBEDDING_CACHE[texts[idx]] = emb_list
            results[idx] = emb_list
        
        logger.info(f"✅ Completed embedding generation")

    return results


def store_embeddings_in_pgvector(conn, filename, chunks, embeddings):
    """
    Optimized storage using batch inserts and psycopg2 extras.
    """
    try:
        with conn.cursor() as cur:
            # Insert parent document and get ID
            cur.execute("""
                INSERT INTO documents (filename, file_type, content_text)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (filename, filename.split('.')[-1], '\n\n'.join(chunks)))
            
            doc_id = cur.fetchone()[0]
            
            # Prepare data for batch insertion
            # Format the embedding as a list/string that PGVector understands
            data_to_insert = [
                (doc_id, idx, chunk, embedding)
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]
            
            # High-performance batch insertion using execute_values
            # The %s for embedding will automatically handle list-to-array conversion if using pgvector-python, or we can cast it explicitly.
            insert_query = """
                INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding)
                VALUES %s
            """
            
            execute_values(cur, insert_query, data_to_insert)
        
        conn.commit()
        logger.info(f"Successfully batch-stored {len(chunks)} chunks for {filename}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error during batch storage: {e}")
        raise
    
def store_structured_log(conn, df, filename):
    """Store structured event log"""
    from src import database
    database.store_structured_log(conn, df, filename)