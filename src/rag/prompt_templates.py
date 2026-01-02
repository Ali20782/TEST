from langchain_core.prompts import PromptTemplate

PROCESS_RAG_PROMPT = """You are a Process Mining Expert. Use the provided Context to answer the User Question.

CONTEXT:
---
EVENT LOG EVIDENCE:
{event_context}

DOCUMENTATION CHUNKS:
{doc_context}
---

CONSTRAINTS:
1. ONLY use the provided context. If the answer isn't there, say "I have insufficient data to answer this."
2. CITE specific Case IDs and Filenames when making claims.
3. If describing a process flow, use "Step 1 -> Step 2" notation.
4. If you see a bottleneck (long durations), explicitly flag it.

USER QUESTION: {question}

YOUR ANALYTICAL RESPONSE:"""

PROMPT = PromptTemplate(
    template=PROCESS_RAG_PROMPT, 
    input_variables=["event_context", "doc_context", "question"]
)