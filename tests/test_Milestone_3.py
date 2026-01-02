import json
import os
from datetime import datetime
import logging

from src.rag.rag_evaluator import RAGEvaluator
from src.database import get_db_connection

import pytest

@pytest.fixture
def evaluator():
    conn = get_db_connection()
    yield RAGEvaluator(conn)
    conn.close()

def test_retrieval_accuracy_threshold(evaluator):
    """
        Verify that the RAG system hits the >= 80% accuracy target.
    """
    dataset_path = "src/rag/test_queries.json"
    results = evaluator.run_suite(dataset_path)
    
    # Core requirement: Achieve >= 80% retrieval accuracy
    assert results['Accuracy'] >= 0.80, f"Accuracy was {results['Accuracy']:.2%}, expected >= 80%"

# Initialise logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_baseline_report():
    conn = get_db_connection()
    evaluator = RAGEvaluator(conn)
    
    dataset_path = "src/rag/test_queries.json"
    logger.info(f"Starting baseline evaluation using {dataset_path}...")
    
    # Run evaluation
    results = evaluator.run_suite(dataset_path)
    
    # Format the Markdown Report
    report = f"""# Milestone 3: RAG Baseline Evaluation Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. Executive Summary
| Metric | Value | Target | Status |
| :--- | :--- | :--- | :--- |
| **Retrieval Accuracy** | {results['Accuracy']:.2%} | 80% | {'✅ PASS' if results['Accuracy'] >= 0.8 else '❌ FAIL'} |
| **Mean Precision** | {results['Mean Precision']:.3f} | - | - |
| **Mean Recall** | {results['Mean Recall']:.3f} | - | - |
| **MRR** | {results['MRR']:.3f} | - | - |

## 2. Methodology
- **Model:** Gemini 1.5 Pro (Primary) / GPT-4o (Fallback)
- **Vector DB:** PostgreSQL + PGVector (HNSW Index enabled)
- **Top-K:** 5
- **Dataset:** BPI Challenge 2012/2017

## 3. Failure Mode Analysis
### Known Struggles
- **Numerical Reasoning:** Queries involving "greater than" on loan amounts sometimes fail if the vector doesn't explicitly contain the number as text.
- **Temporal Logic:** Retrieval of specific months works well, but calculating "duration between" events relies heavily on LLM reasoning over retrieved timestamps.

### Recommended Fixes
- Implement a **SQL Agent** for aggregation queries (Sum/Avg).
- Expand `format_event_for_embedding` to include more verbose attribute labels.
"""

    with open("baseline_report.md", "w") as f:
        f.write(report)
    
    print("✅ Baseline report generated: baseline_report.md")
    conn.close()

if __name__ == "__main__":
    generate_baseline_report()