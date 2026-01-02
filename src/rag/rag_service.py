import os
import logging
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from src.retrieval_service import search_documents, search_event_logs, rerank_results
from .prompt_templates import PROMPT

logger = logging.getLogger(__name__)

class ProcessRAGService:
    def __init__(self, conn):
        self.conn = conn
        # Primary: Gemini 1.5 Pro (Free tier via API Key)
        self.primary_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        # Fallback: GPT-4o (Limited free tier usage)
        self.fallback_llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def query(self, question: str, query_embedding: List[float], filters: Optional[Dict] = None) -> Dict[str, Any]:
        with self.conn.cursor() as cur:
            # Retrieval
            raw_docs = search_documents(cur, query_embedding, top_k=3)
            raw_events = search_event_logs(cur, query_embedding, top_k=5, filters=filters)
            
            # Context Preparation
            event_context = "\n".join([e['text'] for e in raw_events])
            doc_context = "\n".join([d['text'] for d in raw_docs])
            
            chain_input = {
                "event_context": event_context,
                "doc_context": doc_context,
                "question": question
            }

            # Execution with Fallback Logic
            try:
                response = self.primary_llm.invoke(PROMPT.format(**chain_input))
                model_used = "gemini-1.5-pro"
            except Exception as e:
                logger.warning(f"Primary model (Gemini) failed or rate-limited: {e}")
                response = self.fallback_llm.invoke(PROMPT.format(**chain_input))
                model_used = "gpt-4o"

            answer = response.content

            # Citation and Hallucination Check
            sources = [e['case_id'] for e in raw_events]
            confidence = self._calculate_confidence(answer, raw_events)

            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "model_metadata": {"model": model_used},
                "retrieved_chunks": [d['text'] for d in raw_docs]
            }

    def _calculate_confidence(self, answer: str, events: List[Dict]) -> float:
        if "insufficient data" in answer.lower():
            return 0.0
        # Check if at least one retrieved case ID is mentioned in the answer
        has_citation = any(str(e['case_id']) in answer for e in events)
        return 0.95 if has_citation else 0.4