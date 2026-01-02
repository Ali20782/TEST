import json
import numpy as np
import logging
from typing import List, Dict
from src.embedding_service import get_model
from src.retrieval_service import search_documents, search_event_logs

logger = logging.getLogger(__name__)

class RAGEvaluator:
    def __init__(self, conn):
        self.conn = conn
        self.model = get_model()

    def evaluate_query(self, test_case: Dict) -> Dict:
        """Evaluates detailed metrics for a single test case."""
        query_text = test_case["query"]
        query_embedding = self.model.encode([query_text])[0].tolist()
        
        with self.conn.cursor() as cur:
            # Note: Added query_text here to support Hybrid Search
            results = search_event_logs(cur, query_embedding, query_text, top_k=5)
            retrieved_cases = [str(res['case_id']) for res in results]
            
            expected = set(str(c) for c in test_case.get("expected_cases", []))
            retrieved = set(retrieved_cases)
            
            true_positives = len(expected.intersection(retrieved))
            precision = true_positives / len(retrieved) if retrieved else 0
            recall = true_positives / len(expected) if expected else 0
            
            rr = 0
            for i, case_id in enumerate(retrieved_cases):
                if case_id in expected:
                    rr = 1 / (i + 1)
                    break
            
            return {"precision": precision, "recall": recall, "rr": rr}

    def run_suite(self, dataset_path):
        """Runs the bulk evaluation suite and returns overall accuracy."""
        try:
            with open(dataset_path, 'r') as f:
                queries = json.load(f)
        except FileNotFoundError:
            logger.error(f"Dataset not found at {dataset_path}")
            return {"Accuracy": 0.0, "error": "File not found"}

        correct = 0
        total = len(queries)

        # Use a single cursor for the whole suite for better performance
        with self.conn.cursor() as cur:
            for q in queries:
                query_text = q['query']
                query_vector = self.model.encode([query_text])[0].tolist()

                # FIX: Changed self.cur to cur (local cursor from context manager)
                results = search_event_logs(cur, query_vector, query_text, top_k=15)
                
                # Normalize both to strings to ensure match (e.g., '173688' == '173688')
                retrieved_cases = [str(r['case_id']) for r in results]
                expected_cases = [str(c) for c in q.get('expected_cases', [])]
                
                # Check for hit in top_k
                if any(case in retrieved_cases for case in expected_cases):
                    correct += 1
                else:
                    logger.info(f"❌ Miss: '{query_text}'")
                    logger.debug(f"Expected: {expected_cases} | Got: {retrieved_cases[:3]}")
                
                # Temporary debug print inside run_suite
                print(f"DEBUG: Retrieved: {retrieved_cases[:2]} | Expected: {expected_cases}")

        accuracy = correct / total if total > 0 else 0
        return {"Accuracy": accuracy, "total_queries": total, "correct": correct}