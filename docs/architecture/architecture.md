## AI-Powered Conversational Process Intelligence Platform: Complete System Architecture Documentation

-----

## 1\. System Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              React/Vue.js Web Application                    │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │   │
│  │  │  Process Map   │  │  Variant       │  │  Chat Interface│  │   │
│  │  │  Viewer        │  │  Explorer      │  │  (AI QandA)    │  │   │
│  │  │  (bpmn-js)     │  │                │  │                │  │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ HTTPS/REST API
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                         API GATEWAY LAYER                           │
│                         (FastAPI Backend)                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  API Routes                                                   │  │
│  │  • /upload - Data ingestion                                   │  │
│  │  • /discover - Process discovery                              │  │
│  │  • /variants - Variant analysis                               │  │
│  │  • /query - RAG-powered QandA                                 │  │
│  │  • /export - BPMN export                                      │  │
│  └───────────────────────────────────────────────────────────────┘  │
└───────────┬─────────────────┬─────────────────┬─────────────────────┘
            │                 │                 │
            │                 │                 │
    ┌───────▼──────┐  ┌───────▼─────┐  ┌────────▼────────┐
    │  Process     │  │  RAG and AI │  │  Data           │
    │  Mining      │  │  Pipeline   │  │  Management     │
    │  Engine      │  │             │  │                 │
    └───────┬──────┘  └───────┬─────┘  └────────┬────────┘
            │                 │                 │
┌───────────▼─────────────────▼─────────────────▼─────────────────────┐
│                      DATA PERSISTENCE LAYER                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │   PostgreSQL     │  │    PGVector      │  │   File Storage   │   │
│  │   (Metadata)     │  │   (Embeddings)   │  │   (Raw Data)     │   │
│  │                  │  │                  │  │                  │   │
│  │ • User data      │  │ • Event vectors  │  │ • CSV/XES files  │   │
│  │ • Project info   │  │ • Doc vectors    │  │ • PDF/TXT docs   │   │
│  │ • Event logs     │  │ • Semantic index │  │ • BPMN exports   │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
            │                 │                 
    ┌───────▼──────┐  ┌───────▼─────────────────┐
    │   pm4py      │  │   LangChain Framework   │
    │   Library    │  │   ┌──────────────────┐  │
    │              │  │   │ SentenceTransf.  │  │
    │ • Discovery  │  │   │ (Embeddings)     │  │
    │ • Conformance│  │   └──────────────────┘  │
    │ • Variants   │  │   ┌──────────────────┐  │
    │ • Statistics │  │   │ LLM API          │  │
    │              │  │   │ (Gemini/OpenAI)  │  │
    └──────────────┘  │   └──────────────────┘  │
                      └─────────────────────────┘
```

-----

## 2\. Component Selection Reason

### 2.1 Frontend Layer: React.js

**Selected Technology:** React.js with TypeScript

**Reason:**

  - **Component Reusability:** Modular **architecture** perfect for **building** complex **dashboards** with **process maps**, **variant explorers**, and **chat interfaces**.
  - **Rich Ecosystem:** **Direct integration** with **bpmn-js** for **BPMN visualisation**.
  - **State Management:** **Redux Toolkit** for **managing** complex **application state** (**selected variants**, **chat history**, **loaded datasets**).
  - **Real-time Updates:** **React hooks** enable **smooth real-time updates** when **RAG queries** return **results**.
  - **TypeScript:** **Type safety** crucial for **handling** complex **process mining data structures**.

**Alternative Considered:** Vue.js (simpler learning curve but smaller ecosystem for specialised **libraries**).

-----

### 2.2 BPMN Visualisation: bpmn-js

**Selected Technology:** bpmn-js by Camunda

**Reason:**

  - **Industry Standard:** Most widely **used** **BPMN** 2.0 **rendering library**.
  - **Interactive:** **Built-in pan**, **zoom**, and **element selection capabilities**.
  - **Extensible:** **Custom overlays** for **performance metrics** (**bottleneck highlighting**, **frequency annotations**).
  - **Export Ready:** **Native support** for **BPMN** 2.0 **XML import**/export.
  - **Active Maintenance:** **Regular updates** and **strong community support**.

**Key Features Used:**

  - **Process map rendering** from **BPMN XML**.
  - **Custom overlays** for **performance data visualisation**.
  - **Variant filtering** (highlight **selected paths**, **grey out others**).
  - **Click-to-drill-down** on **activities**.

-----

### 2.3 Backend Framework: FastAPI

**Selected Technology:** FastAPI (Python)

**Reason:**

  - **Performance:** **ASGI-based**, **async support** for **handling concurrent RAG queries** and **process discovery operations**.
  - **Native Python:** **Seamless integration** with **pm4py**, **LangChain**, and **ML libraries**.
  - **Auto-Documentation:** **Built-in OpenAPI** (**Swagger**) **documentation** for **API endpoints**.
  - **Type Validation:** **Pydantic models** ensure **data integrity** at **API boundaries**.
  - **WebSocket Support:** **Real-time streaming** for **long-running process discovery tasks** and **RAG responses**.

**Why Not Flask/Django:**

  - **Flask:** **Synchronous**, slower for **AI workloads**.
  - **Django:** **Too heavyweight**, unnecessary **ORM complexity** for **our use case**.

-----

### 2.4 Process Mining Engine: pm4py

**Selected Technology:** pm4py

**Reason:**

  - **Comprehensive:** **All-in-one library** for **discovery**, **conformance**, **variants**, and **performance analysis**.
  - **Algorithm Variety:** - **Inductive Miner** (**guarantees sound process models**).
      - **Heuristics Miner** (**handles noise well**).
      - **Alpha Miner** (**simple**, **fast** for **clean logs**).
  - **Standards Compliant:** **Native XES** and **BPMN** 2.0 **support**.
  - **Active Development:** **IEEE Task Force backing** ensures **long-term viability**.
  - **Python Native:** **No external dependencies** or **JVM required**.

**Core Algorithms Selected:**

  - **Process Discovery:** **Inductive Miner** (**guarantees fitness**).
  - **Conformance Checking:** **Token-based replay** and **alignments**.
  - **Variant Analysis:** **Built-in variant extraction** with **frequency**/**performance metrics**.

-----

### 2.5 Vector Database: PGVector

**Selected Technology:** **PGVector** (**PostgreSQL extension**)

**Reason:**

  - **Unified Database:** **Single database** for **both structured** (**event logs**) and **vector data** (**embeddings**).
  - **Production-Ready:** **Built** on **PostgreSQL's reliability** and **ACID guarantees**.
  - **Performance:** **Native indexing** (**HNSW**, **IVFFlat**) for **fast similarity search**.
  - **Cost-Effective:** **No separate vector DB service needed** (**vs Pinecone**, **Weaviate**).
  - **SQL Joins:** **Can directly join vector similarity results** with **structured event log data**.

**Why Not ChromaDB/Pinecone:**

  - **ChromaDB:** **Great** for **prototypes** but **lacks enterprise features** (**multi-tenancy**, **access control**).
  - **Pinecone:** **Expensive** for **large deployments**, **vendor lock-in**.

-----

### 2.6 RAG Orchestration: LangChain

**Selected Technology:** **LangChain**

**Reason:**

  - **RAG Abstraction:** **High-level abstractions** for **Retrieval-Augmented Generation**.
  - **Multi-Source:** **Unified interface** for **vectorised event logs** + **document embeddings**.
  - **Prompt Templates:** **Structured prompts** to **prevent hallucination** in **root cause analysis**.
  - **Chain Composition:** **Sequential chains** for: **query** → **retrieve** → **re-rank** → **generate**.
  - **LLM Agnostic:** **Easy switch** between **OpenAI**, **Gemini**, or **local models**.

**RAG Pipeline Architecture:**

```
User Query → Embed Query → Semantic Search (PGVector) → Retrieve Top-K Context → Re-rank →
Build Prompt → LLM Generation → Cite Sources → Return Answer
```

-----

### 2.7 Embedding Model: SentenceTransformers

**Selected Technology:** **all-MiniLM-L6-v2** (**default**), **all-mpnet-base-v2** (**high-quality**)

**Reason:**

  - **Lightweight:** **22M parameters**, **runs** on **CPU**, **fast inference**.
  - **Multilingual:** **Supports process data** in **multiple languages**.
  - **Semantic Quality:** **Fine-tuned** for **sentence similarity** (**critical** for **RAG**).
  - **Self-Hosted:** **No API costs**, **no data privacy concerns**.
  - **Proven:** **Industry standard** for **RAG applications**.

**Embedding Strategy:**

  - **Event Logs:** **Generate summary text** per **event**: "**Case INV\_001**: **Activity** '**Approve**' **by John** at **2024-01-15** (**duration**: **2.3 hours**)"
  - **Documents:** **Chunk documents** into **500-token segments** with **100-token overlap**.
  - **Storage:** **Store embeddings** as **384-dimensional vectors** in **PGVector**.

-----

### 2.8 LLM Provider: Google Gemini / OpenAI

**Selected Technology:** **Google Gemini** 1.5 Pro (**primary**), **OpenAI GPT-4o** (**fallback**)

**Reason:**

**Gemini 1.5 Pro:**

  - **Long Context:** **1M token context window** (**can ingest entire process logs** if **needed**).
  - **Multimodal:** **Future capability** to **analyse process diagrams**/**screenshots**.
  - **Cost:** **More economical** than **GPT-4** for **high-volume queries**.
  - **Speed:** **Faster response times** for **conversational UI**.

**GPT-4o (Fallback):**

  - **Reliability:** **Proven track record** for **structured reasoning**.
  - **JSON Mode:** **Native JSON output** for **structured responses**.

**Prompt Strategy:**

```
System: You are a process mining expert analysing event logs.
Context: {retrieved_events_and_documents}
Question: {user_question}
Instructions: 
- Provide root cause analysis based ONLY on the context
- Cite specific case IDs and document sources
- If insufficient data, state clearly
```

-----

### 2.9 Data Storage: PostgreSQL

**Selected Technology:** **PostgreSQL** with **PGVector extension**

**Reason:**

  - **Relational + Vector:** **Hybrid storage** in **single database**.
  - **JSONB Support:** **Store complex process attributes** as **flexible JSON**.
  - **Indexing:** **B-tree** for **event logs**, **HNSW** for **vector similarity**.
  - **Transactions:** **ACID guarantees** for **data integrity**.
  - **Scalability:** **Proven** at **enterprise scale** (**handles billions of rows**).

-----

## 3\. Data Flow Architecture

### 3.1 Data Ingestion Flow

```
User Uploads CSV/XES
       ↓
FastAPI /upload endpoint
       ↓
Validate Schema (case_id, activity, timestamp)
       ↓
       ├→ Store raw data in PostgreSQL
       ├→ Generate event summaries
       └→ Embed with SentenceTransformers → PGVector
       ↓
Return: Upload Success + Dataset ID
```

-----

### 3.2 Process Discovery Flow

```
User Clicks "Discover Process"
       ↓
FastAPI /discover endpoint
       ↓
Fetch event log from PostgreSQL
       ↓
pm4py Inductive Miner
       ↓
Generate Process Tree → Convert to BPMN 2.0 XML
       ↓
       ├→ Store BPMN in PostgreSQL
       └→ Return BPMN XML to frontend
       ↓
bpmn-js renders interactive process map
```

-----

### 3.3 RAG Query Flow

```
User Asks: "Why are invoices stuck in Texas?"
       ↓
FastAPI /query endpoint
       ↓
Embed query with SentenceTransformers
       ↓
PGVector similarity search (top 10 results)
       ├→ Search event embeddings
       └→ Search document embeddings
       ↓
LangChain retriever merges and re-ranks results
       ↓
Build prompt with context + question
       ↓
Call Gemini API
       ↓
Parse response + extract citations
       ↓
Return structured answer with sources
       ↓
Display in chat interface with clickable case IDs
```

-----

## 4\. Scalability and Performance Design

### 4.1 Caching Strategy

  - **Redis Layer:** **Cache frequently accessed process models** and **query results**.
  - **CDN:** **Static assets** (**React bundle**, **images**) **served** via **CDN**.
  - **Database Caching:** **PostgreSQL query plan caching** for **repeated variant queries**.

### 4.2 Async Processing

  - **Celery Workers:** **Background tasks** for **large file processing** (**10M+ events**).
  - **WebSocket Updates:** **Real-time progress** for **long-running discoveries**.
  - **Queue System:** **RabbitMQ** for **task distribution**.

### 4.3 Vector Search Optimisation

  - **HNSW Index:** **Approximate nearest neighbour search** (**10x faster** than **exact**).
  - **Quantisation:** **Reduce embedding dimensions** if **needed** (**384** → **128**).
  - **Hybrid Search:** **Combine vector similarity** with **keyword filters** for **precision**.

-----

## 5\. Security Architecture

### 5.1 Authentication

  - **JWT Tokens:** **Stateless authentication** with **24-hour expiry**.
  - **OAuth 2.0:** **Support** for **SSO** (**Google**, **Microsoft**).
  - **API Keys:** For **programmatic access**.

### 5.2 Data Isolation

  - **Multi-Tenancy:** **Row-level security** in **PostgreSQL**.
  - **Project Scoping:** **All queries filtered** by **user's project\_id**.
  - **Encryption:** **At-rest** (**PostgreSQL TDE**) and **in-transit** (**TLS** 1.3).

-----

## 6\. Deployment Architecture

```
┌─────────────────────────────────────────┐
│         Load Balancer (Nginx)           │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │                           │
┌───▼─────┐              ┌──────▼──────┐
│ FastAPI │              │   FastAPI   │
│ Instance│              │   Instance  │
│    1    │              │      2      │
└────┬────┘              └──────┬──────┘
     │                          │
     └──────────┬───────────────┘
                │
    ┌───────────▼────────────┐
    │   PostgreSQL Cluster   │
    │   (Primary + Replica)  │
    └────────────────────────┘
```

-----

## 7\. Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React.js | **UI framework** |
| | TypeScript | **Type safety** |
| | bpmn-js | **BPMN visualisation** |
| | Tailwind CSS | **Styling** |
| **Backend** | FastAPI | **API server** |
| | Python | **Language** |
| | Uvicorn | **ASGI server** |
| **Process Mining** | pm4py | **Core algorithms** |
| **AI/RAG** | LangChain | **RAG orchestration** |
| | SentenceTransformers | **Embeddings** |
| | Google Gemini | **LLM** |
| **Database** | PostgreSQL | **Relational data** |
| | PGVector | **Vector storage** |
| **Deployment** | Docker | **Containerisation** |
| | Nginx | **Reverse proxy** |
| **Data Science** | pandas | **Data manipulation** |
| | scikit-learn | **Clustering** (**Phase** 4) |

-----
