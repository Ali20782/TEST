import pandas as pd
import io
from docx import Document
from typing import Tuple, Dict, Any, Union

# --- Structured Data Processing ---

def process_structured_data(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Reads structured file (CSV/XLSX) and performs initial validation."""
    if filename.endswith(('.csv', '.CSV')):
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif filename.endswith(('.xlsx', '.XLSX')):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported structured file type. Use CSV or XLSX.")

    required_cols = ['case_id', 'activity', 'timestamp']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    # Basic data standardisation (more complex PM4PY logic would go here)
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    metrics = {
        "total_events": len(df),
        "unique_cases": df['case_id'].nunique()
    }

    return df, metrics

# --- Unstructured Data Processing ---

def extract_text_from_unstructured(file_bytes: bytes, filename: str) -> str:
    """Extracts raw text content from unstructured files (TXT/DOCX)."""
    if filename.endswith(('.txt', '.TXT')):
        content = file_bytes.decode('utf-8')
    elif filename.endswith(('.docx', '.DOCX')):
        doc = Document(io.BytesIO(file_bytes))
        content = '\n'.join([p.text for p in doc.paragraphs])
    else:
        raise ValueError("Unsupported unstructured file type. Use TXT or DOCX.")
    
    return content