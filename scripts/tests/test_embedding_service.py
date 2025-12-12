"""
Unit Tests for Embedding Service
Tests SentenceTransformers integration
"""

import pytest
import numpy as np
from scripts.embedding_service import EmbeddingService

@pytest.fixture
def embedding_service():
    """Embedding service fixture"""
    service = EmbeddingService()
    service.load_model()
    return service

class TestEmbeddingService:
    """Test embedding service functionality"""
    
    def test_load_model(self):
        """Test loading embedding model"""
        service = EmbeddingService()
        service.load_model()
        
        assert service.model is not None
        assert service.embedding_dim == 384
    
    def test_embed_single_text(self, embedding_service):
        """Test embedding single text"""
        text = "This is a test sentence for embedding."
        embedding = embedding_service.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_empty_text(self, embedding_service):
        """Test embedding empty text"""
        embedding = embedding_service.embed_text("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
    
    def test_embed_long_text(self, embedding_service):
        """Test embedding long text"""
        text = " ".join(["word"] * 1000)
        embedding = embedding_service.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
    
    def test_embed_special_characters(self, embedding_service):
        """Test embedding text with special characters"""
        text = "Test with émojis 🎉 and spëcial çharacters!"
        embedding = embedding_service.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384

class TestBatchEmbedding:
    """Test batch embedding functionality"""
    
    def test_embed_batch(self, embedding_service):
        """Test batch embedding"""
        texts = [
            "First test sentence",
            "Second test sentence",
            "Third test sentence"
        ]
        
        embeddings = embedding_service.embed_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
    
    def test_embed_large_batch(self, embedding_service):
        """Test embedding large batch"""
        texts = [f"Test sentence number {i}" for i in range(100)]
        embeddings = embedding_service.embed_batch(texts, batch_size=32)
        
        assert len(embeddings) == 100
        assert all(len(emb) == 384 for emb in embeddings)
    
    def test_embed_batch_consistency(self, embedding_service):
        """Test that batch embedding is consistent"""
        text = "Consistency test"
        
        # Single embedding
        single_emb = embedding_service.embed_text(text)
        
        # Batch embedding
        batch_emb = embedding_service.embed_batch([text])[0]
        
        # Should be identical or very close
        diff = np.abs(np.array(single_emb) - np.array(batch_emb))
        assert np.max(diff) < 1e-5

class TestSimilarity:
    """Test similarity computation"""
    
    def test_compute_similarity_identical(self, embedding_service):
        """Test similarity of identical embeddings"""
        text = "Test sentence"
        emb = embedding_service.embed_text(text)
        
        similarity = embedding_service.compute_similarity(emb, emb)
        
        # Should be 1.0 for identical vectors
        assert abs(similarity - 1.0) < 1e-5
    
    def test_compute_similarity_similar_texts(self, embedding_service):
        """Test similarity of similar texts"""
        text1 = "The invoice was approved by the manager"
        text2 = "Manager approved the invoice"
        
        emb1 = embedding_service.embed_text(text1)
        emb2 = embedding_service.embed_text(text2)
        
        similarity = embedding_service.compute_similarity(emb1, emb2)
        
        # Should be high similarity
        assert similarity > 0.5
    
    def test_compute_similarity_different_texts(self, embedding_service):
        """Test similarity of different texts"""
        text1 = "The weather is sunny today"
        text2 = "Database connection failed"
        
        emb1 = embedding_service.embed_text(text1)
        emb2 = embedding_service.embed_text(text2)
        
        similarity = embedding_service.compute_similarity(emb1, emb2)
        
        # Should be low similarity
        assert similarity < 0.5

class TestEmbeddingProperties:
    """Test mathematical properties of embeddings"""
    
    def test_embedding_normalization(self, embedding_service):
        """Test that embeddings are normalized"""
        text = "Test normalization"
        embedding = np.array(embedding_service.embed_text(text))
        
        # Check if normalized (L2 norm ≈ 1)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.1  # Allow some tolerance
    
    def test_embedding_consistency(self, embedding_service):
        """Test that same text produces same embedding"""
        text = "Consistency test"
        
        emb1 = embedding_service.embed_text(text)
        emb2 = embedding_service.embed_text(text)
        
        # Should be identical
        diff = np.abs(np.array(emb1) - np.array(emb2))
        assert np.max(diff) < 1e-6
    
    def test_embedding_semantic_similarity(self, embedding_service):
        """Test semantic similarity preservation"""
        # Similar meanings
        texts = [
            "invoice approval",
            "approve invoice",
            "invoice was approved"
        ]
        
        embeddings = [embedding_service.embed_text(t) for t in texts]
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                sim = embedding_service.compute_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        # All should be reasonably similar
        assert all(s > 0.4 for s in similarities)

class TestPerformance:
    """Test embedding performance"""
    
    def test_single_embedding_speed(self, embedding_service):
        """Test speed of single embedding"""
        import time
        
        text = "Test sentence for performance measurement"
        
        start = time.time()
        for _ in range(10):
            embedding_service.embed_text(text)
        elapsed = time.time() - start
        
        avg_time = elapsed / 10
        assert avg_time < 0.1  # Should be < 100ms per embedding
        print(f"\n  ⏱️  Average embedding time: {avg_time*1000:.2f}ms")
    
    def test_batch_embedding_speed(self, embedding_service):
        """Test speed of batch embedding"""
        import time
        
        texts = [f"Test sentence {i}" for i in range(100)]
        
        start = time.time()
        embeddings = embedding_service.embed_batch(texts, batch_size=32)
        elapsed = time.time() - start
        
        assert len(embeddings) == 100
        assert elapsed < 5.0  # Should process 100 in < 5 seconds
        print(f"\n  ⏱️  Batch embedded 100 texts in {elapsed:.2f}s ({elapsed*10:.2f}ms each)")
    
    def test_similarity_computation_speed(self, embedding_service):
        """Test speed of similarity computation"""
        import time
        
        emb1 = [0.1] * 384
        emb2 = [0.2] * 384
        
        start = time.time()
        for _ in range(1000):
            embedding_service.compute_similarity(emb1, emb2)
        elapsed = time.time() - start
        
        avg_time = elapsed / 1000
        assert avg_time < 0.001  # Should be < 1ms
        print(f"\n  ⏱️  Average similarity computation: {avg_time*1000:.3f}ms")

class TestErrorHandling:
    """Test error handling"""
    
    def test_embed_none(self, embedding_service):
        """Test handling None input"""
        with pytest.raises((TypeError, AttributeError)):
            embedding_service.embed_text(None)
    
    def test_embed_invalid_type(self, embedding_service):
        """Test handling invalid type"""
        with pytest.raises((TypeError, AttributeError)):
            embedding_service.embed_text(12345)
    
    def test_similarity_different_dimensions(self, embedding_service):
        """Test similarity with different dimensions"""
        emb1 = [0.1] * 384
        emb2 = [0.2] * 256  # Wrong dimension
        
        with pytest.raises((ValueError, IndexError)):
            embedding_service.compute_similarity(emb1, emb2)

class TestModelConfiguration:
    """Test model configuration"""
    
    def test_default_model(self):
        """Test default model configuration"""
        service = EmbeddingService()
        assert service.model_name == 'all-MiniLM-L6-v2'
    
    def test_model_dimension(self, embedding_service):
        """Test model embedding dimension"""
        assert embedding_service.embedding_dim == 384

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])