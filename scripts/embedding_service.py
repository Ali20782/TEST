"""
Embedding Service Module
Handles text embedding using SentenceTransformers
"""

from sentence_transformers import SentenceTransformer
import logging
import os
from typing import List
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.model = None
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2
    
    def load_model(self):
        """Load the embedding model"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"✅ Embedding model loaded successfully")
                
                # Verify embedding dimension
                test_embedding = self.model.encode("test")
                self.embedding_dim = len(test_embedding)
                logger.info(f"Embedding dimension: {self.embedding_dim}")
                
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
                raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text string
        
        Returns:
            List of floats representing the embedding vector
        """
        if self.model is None:
            self.load_model()
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list for database storage
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for processing
        
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            self.load_model()
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 100
            )
            
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score (0-1)
        """
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)