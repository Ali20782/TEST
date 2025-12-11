import os
import pandas as pd
from typing import IO, List, Dict, Any
import psycopg2.errors
from langchain_text_splitters import RecursiveCharacterTextSplitter
from docx import Document
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.log.obj import EventLog
# from sentence_transformers import SentenceTransformer # Install if running locally/not mocked

# --- Constants based on Architecture ---
REQUIRED_EVENT_COLUMNS = ['case_id', 'activity', 'timestamp'] 
VECTOR_DIMENSION = 384 # Based on SentenceTransformers all-MiniLM-L6-v2

class DataProcessingService:
    """Handles parsing, validation, and storage for structured and unstructured data."""

    def __init__(self, db_conn):
        # self.db_conn = db_conn
        # self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2') # Uncomment for real deployment
        pass 

    # --- Structured Data Processing (CSV/XLSX) ---

    def _load_structured_file(self, file_io: IO, filename: str) -> pd.DataFrame:
        """Loads CSV or XLSX into a pandas DataFrame."""
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension == '.csv':
            df = pd.read_csv(file_io)
        elif file_extension in ('.xlsx', '.xls'):
            df = pd.read_excel(file_io, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported structured file type: {file_extension}")
        
        return df

    def process_structured_log(self, file_io: IO, filename: str, project_id: str) -> Dict[str, Any]:
        """Loads and processes event logs for process mining."""
        df = self._load_structured_file(file_io, filename)

        # 1. Validate Schema
        # pm4py utility to standardize column names (e.g., from 'CaseID' to 'case_id')
        df = dataframe_utils.rename_columns_event_log(df) 
        
        # Ensure required columns are present after standardization
        missing_cols = [col for col in REQUIRED_EVENT_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Event log is missing required columns: {', '.join(missing_cols)}")
        
        # 2. Conversion and Validation (pm4py)
        event_log = EventLog(df.to_dict('records')) 

        # 3. Store Raw Data and Metadata (PostgreSQL)
        dataset_id = self._store_raw_log_to_db(df, filename, project_id)
        
        # 4. Generate Embeddings for RAG (Event Summaries)
        event_summaries = self._generate_event_summaries(df)
        self._store_embeddings(dataset_id, event_summaries)
        
        return {"dataset_id": dataset_id, "status": "Event log processed and indexed."}

    # --- Unstructured Data Processing (TXT/DOCX) ---

    def _read_unstructured_file(self, file_io: IO, filename: str) -> str:
        """Reads content from TXT or DOCX files."""
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension == '.txt':
            # Decode file content from bytes
            return file_io.read().decode('utf-8') 
        elif file_extension == '.docx':
            # docx library handles file stream directly
            document = Document(file_io)
            return '\n'.join([p.text for p in document.paragraphs])
        else:
            raise ValueError(f"Unsupported unstructured file type: {file_extension}")

    def process_unstructured_doc(self, file_io: IO, filename: str, project_id: str) -> Dict[str, Any]:
        """Loads, chunks, and embeds unstructured documents for RAG."""
        text_content = self._read_unstructured_file(file_io, filename)

        # 1. Chunking Strategy (LangChain integration)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, 
            chunk_overlap=100
        )
        chunks = text_splitter.split_text(text_content)

        # 2. Store Metadata (PostgreSQL)
        dataset_id = self._store_document_metadata_to_db(filename, project_id)

        # 3. Generate and Store Embeddings (PGVector)
        self._store_embeddings(dataset_id, chunks)

        return {"dataset_id": dataset_id, "status": f"Document processed, split into {len(chunks)} chunks, and indexed."}

    # --- Internal Storage/Embedding Helpers (MOCKED) ---

    def _store_raw_log_to_db(self, df: pd.DataFrame, filename: str, project_id: str) -> str:
        """MOCK: Simulates storing event log data and metadata in PostgreSQL."""
        # In a real implementation, this would use SQL to save data and return a unique ID.
        return f"LOG-{project_id}-{hash(filename)}"

    def _store_document_metadata_to_db(self, filename: str, project_id: str) -> str:
        """MOCK: Simulates storing document metadata in PostgreSQL."""
        return f"DOC-{project_id}-{hash(filename)}"

    def _generate_event_summaries(self, df: pd.DataFrame) -> List[str]:
        """Generates summary text per event for embedding."""
        # Example summary text generation:
        summaries = [
            f"Case {row['case_id']}: Activity '{row['activity']}' by {row.get('resource', 'Unknown')} at {row['timestamp']}"
            for index, row in df.head(100).iterrows()
        ]
        return summaries

    def _store_embeddings(self, dataset_id: str, texts: List[str]):
        """MOCK: Simulates generating and storing vectors in PGVector."""
        # In real code, use self.embedding_model.encode(texts) and insert into PGVector.
        pass