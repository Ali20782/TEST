"""
Enhanced Data Processing Service
Comprehensive file processing with validation, transformation, and error handling
"""

import pandas as pd
import io
from docx import Document
from typing import Tuple, Dict, Any, List
import chardet
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Required columns for event logs
REQUIRED_COLUMNS = ['case_id', 'activity', 'timestamp']

# Optional columns with defaults
OPTIONAL_COLUMNS = {
    'resource': 'Unknown',
    'cost': 0.0,
    'location': '',
    'product_type': ''
}


def detect_encoding(file_bytes: bytes) -> str:
    """
    Detect file encoding using chardet.
    
    Args:
        file_bytes: Raw file bytes
        
    Returns:
        Detected encoding string
    """
    result = chardet.detect(file_bytes)
    return result['encoding'] or 'utf-8'


def validate_event_log_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that dataframe has required event log columns.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, missing_columns)
    """
    # Normalize column names for comparison
    df_columns = [col.lower().replace(' ', '_') for col in df.columns]
    required_lower = [col.lower() for col in REQUIRED_COLUMNS]
    
    missing = [col for col in REQUIRED_COLUMNS if col not in df_columns]
    
    return len(missing) == 0, missing


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and sanitize dataframe.
    
    Args:
        df: Input dataframe
        
    Returns:
        Sanitized dataframe
    """
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Fill null values in critical columns
    if 'activity' in df.columns:
        df['activity'] = df['activity'].fillna('Unknown Activity')
    
    if 'case_id' in df.columns:
        df['case_id'] = df['case_id'].fillna('Unknown Case')
    
    # Convert case_id to string
    if 'case_id' in df.columns:
        df['case_id'] = df['case_id'].astype(str)
    
    # Trim whitespace from string columns
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].dtype == 'object':
            try:
                df[col] = df[col].str.strip()
            except:
                pass
    
    return df


def transform_to_canonical_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform dataframe to canonical event log format.
    
    Args:
        df: Input dataframe
        
    Returns:
        Transformed dataframe with canonical schema
    """
    # Normalize column names
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Parse timestamps with multiple format support
    if 'timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        except Exception as e:
            logger.warning(f"Timestamp parsing error: {e}")
            # Try common formats
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S']:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], format=fmt)
                    break
                except:
                    continue
    
    # Add optional columns if missing
    for col, default_value in OPTIONAL_COLUMNS.items():
        if col not in df.columns:
            df[col] = default_value
    
    # Convert cost to float
    if 'cost' in df.columns:
        df['cost'] = pd.to_numeric(df['cost'], errors='coerce').fillna(0.0)
    
    return df


def process_structured_data(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Process structured file (CSV/XLSX) with comprehensive validation and transformation.
    
    Args:
        file_bytes: Raw file bytes
        filename: Name of the file
        
    Returns:
        Tuple of (dataframe, metrics)
        
    Raises:
        ValueError: If file format is unsupported or required columns are missing
    """
    try:
        # Determine file type
        if filename.lower().endswith(('.csv', '.CSV')):
            # Detect encoding
            encoding = detect_encoding(file_bytes)
            
            # Read CSV with detected encoding
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
            except UnicodeDecodeError:
                # Fallback to utf-8
                df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8', encoding_errors='ignore')
                
        elif filename.lower().endswith(('.xlsx', '.XLSX', '.xls', '.XLS')):
            # Read Excel file (uses first sheet by default)
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported structured file type. Use CSV or XLSX.")
        
        # Validate schema
        is_valid, missing_cols = validate_event_log_schema(df)
        if not is_valid:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Sanitize data
        df = sanitize_dataframe(df)
        
        # Transform to canonical format
        df = transform_to_canonical_format(df)
        
        # Calculate metrics
        metrics = {
            "total_events": len(df),
            "unique_cases": df['case_id'].nunique(),
            "unique_activities": df['activity'].nunique(),
            "date_range": (
                df['timestamp'].min().isoformat() if 'timestamp' in df.columns and len(df) > 0 else None,
                df['timestamp'].max().isoformat() if 'timestamp' in df.columns and len(df) > 0 else None
            ) if 'timestamp' in df.columns else (None, None)
        }
        
        # Add optional metrics
        if 'resource' in df.columns:
            metrics['unique_resources'] = df['resource'].nunique()
        
        if 'cost' in df.columns:
            metrics['total_cost'] = float(df['cost'].sum())
            metrics['average_cost'] = float(df['cost'].mean())
        
        logger.info(f"Successfully processed {filename}: {metrics['total_events']} events, {metrics['unique_cases']} cases")
        
        return df, metrics
        
    except pd.errors.EmptyDataError:
        raise ValueError("File is empty or contains no data")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing file: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing structured data: {str(e)}")
        raise


def chunk_document(content: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Split text into chunks with overlap for better context preservation.
    
    Args:
        content: Text content to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(content) <= chunk_size:
        return [content]
    
    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(content):
            # Look for sentence endings
            for sep in ['. ', '.\n', '! ', '?\n']:
                last_sep = content[start:end].rfind(sep)
                if last_sep > chunk_size * 0.7:  # Only if we find separator in last 30%
                    end = start + last_sep + len(sep)
                    break
        
        chunks.append(content[start:end].strip())
        start = end - overlap if end < len(content) else end
    
    return chunks


def extract_text_from_unstructured(file_bytes: bytes, filename: str) -> str:
    """
    Extract text content from unstructured files (TXT/DOCX/PDF).
    
    Args:
        file_bytes: Raw file bytes
        filename: Name of the file
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If file format is unsupported
    """
    try:
        if filename.lower().endswith(('.txt', '.TXT')):
            # Detect encoding
            encoding = detect_encoding(file_bytes)
            
            # Decode with detected encoding
            try:
                content = file_bytes.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to utf-8 with error handling
                content = file_bytes.decode('utf-8', errors='ignore')
                
        elif filename.lower().endswith(('.docx', '.DOCX')):
            # Extract text from DOCX
            doc = Document(io.BytesIO(file_bytes))
            paragraphs = [paragraph.text for paragraph in doc.paragraphs]
            content = '\n'.join(paragraphs)
            
        elif filename.lower().endswith(('.pdf', '.PDF')):
            # PDF extraction (requires PyPDF2 or pdfplumber)
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                content = ''
                for page in pdf_reader.pages:
                    content += page.extract_text() + '\n'
            except ImportError:
                raise ValueError("PDF support requires PyPDF2. Install with: pip install PyPDF2")
                
        else:
            raise ValueError("Unsupported unstructured file type. Use TXT, DOCX, or PDF.")
        
        # Clean up content
        content = content.strip()
        
        logger.info(f"Successfully extracted {len(content)} characters from {filename}")
        
        return content
        
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}")
        raise


def process_unstructured_data(file_bytes: bytes, filename: str) -> Tuple[str, List[str], Dict[str, Any]]:
    """
    Process unstructured file with text extraction and chunking.
    
    Args:
        file_bytes: Raw file bytes
        filename: Name of the file
        
    Returns:
        Tuple of (full_text, chunks, metrics)
    """
    # Extract text
    content = extract_text_from_unstructured(file_bytes, filename)
    
    # Create chunks
    chunks = chunk_document(content, chunk_size=500, overlap=100)
    
    # Calculate metrics
    metrics = {
        "character_count": len(content),
        "word_count": len(content.split()),
        "total_chunks": len(chunks),
        "average_chunk_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0
    }
    
    return content, chunks, metrics


def validate_file_size(file_bytes: bytes, max_size_mb: int = 100) -> bool:
    """
    Validate file size is within limits.
    
    Args:
        file_bytes: Raw file bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        True if valid, False otherwise
    """
    size_mb = len(file_bytes) / (1024 * 1024)
    return size_mb <= max_size_mb


def get_file_info(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Get comprehensive file information.
    
    Args:
        file_bytes: Raw file bytes
        filename: Name of the file
        
    Returns:
        Dictionary with file information
    """
    return {
        "filename": filename,
        "size_bytes": len(file_bytes),
        "size_mb": round(len(file_bytes) / (1024 * 1024), 2),
        "extension": filename.split('.')[-1].lower() if '.' in filename else None,
        "encoding": detect_encoding(file_bytes) if filename.endswith(('.txt', '.csv')) else None,
        "processed_at": datetime.utcnow().isoformat()
    }