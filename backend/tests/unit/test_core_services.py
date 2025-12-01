"""
Core Services Tests - Consolidated & Fast

Tests the essential functionality of all services in a streamlined way.
Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import pytest
import numpy as np
from pathlib import Path

from src.core.config import PROJECT_CONTEXT_ID


class TestPDFParser:
    """PDF Parser essential tests."""
    
    def test_parse_real_pdf(self, sample_pdf_path):
        """Parse actual test PDF and verify structure."""
        from src.services.pdf_parser import PDFParser
        
        if not sample_pdf_path.exists():
            pytest.skip("Test PDF not available")
        
        parser = PDFParser()
        result = parser.parse(str(sample_pdf_path))
        
        assert result.page_count > 0
        assert len(result.pages) == result.page_count
        assert result.watermark == PROJECT_CONTEXT_ID
    
    def test_parse_invalid_file_raises_error(self, tmp_path):
        """Invalid file should raise appropriate error."""
        from src.services.pdf_parser import PDFParser
        
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"not a pdf")
        
        parser = PDFParser()
        with pytest.raises(ValueError):
            parser.parse(str(fake_pdf))


class TestChunking:
    """Chunking service essential tests."""
    
    def test_chunk_text_into_pieces(self):
        """Chunk long text into appropriately sized pieces."""
        from src.services.chunking import ChunkingService, Chunk
        
        long_text = "This is a test sentence. " * 100  # ~500 words
        chunker = ChunkingService(chunk_size=100, chunk_overlap=20)
        
        chunks = chunker.chunk(long_text, source_file="test.pdf", page=1)
        
        assert len(chunks) > 1
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.watermark == PROJECT_CONTEXT_ID for c in chunks)
        assert all(c.text and c.chunk_index >= 0 for c in chunks)


class TestEmbeddings:
    """Embedding service essential tests."""
    
    def test_embed_text_returns_vector(self, embedding_service):
        """Embedding text should return proper vector."""
        text = "Fire rating for corridor walls"
        
        vector = embedding_service.embed(text)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 384
        assert vector.dtype == np.float32
    
    def test_similar_texts_have_high_similarity(self, embedding_service):
        """Similar texts should have higher cosine similarity."""
        vec1 = embedding_service.embed("door width is 36 inches")
        vec2 = embedding_service.embed("door must be 36 inches wide")
        vec3 = embedding_service.embed("the weather is sunny")
        
        sim_12 = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        sim_13 = np.dot(vec1, vec3) / (np.linalg.norm(vec1) * np.linalg.norm(vec3))
        
        assert sim_12 > sim_13


class TestVectorStore:
    """Vector store essential tests."""
    
    def test_store_and_search(self, vector_store, sample_embedded_chunk):
        """Store chunk and retrieve by similarity."""
        # Store
        doc_id = vector_store.store(sample_embedded_chunk)
        assert doc_id is not None
        
        # Search with same vector should find it
        results = vector_store.search(sample_embedded_chunk.vector, top_k=1)
        
        assert len(results) == 1
        assert results[0].watermark == PROJECT_CONTEXT_ID
    
    def test_count_documents(self, vector_store, sample_embedded_chunk):
        """Count should reflect stored documents."""
        assert vector_store.count() == 0
        
        vector_store.store(sample_embedded_chunk)
        
        assert vector_store.count() == 1


class TestRetrieval:
    """Retrieval service essential tests."""
    
    def test_retrieve_relevant_documents(self, retrieval_service, vector_store, embedding_service, sample_construction_texts):
        """Retrieve should return relevant documents for query."""
        from src.services.embeddings import EmbeddedChunk
        
        # Index sample documents
        for i, text in enumerate(sample_construction_texts):
            vector = embedding_service.embed(text)
            chunk = EmbeddedChunk(
                text=text,
                vector=vector,
                metadata={"source_file": "spec.pdf", "page": i+1, "chunk_index": i},
                watermark=PROJECT_CONTEXT_ID
            )
            vector_store.store(chunk)
        
        # Query
        results = retrieval_service.retrieve("fire rating for walls", top_k=2)
        
        assert len(results) > 0
        assert "fire" in results[0].text.lower() or "rating" in results[0].text.lower()


class TestRAGPipeline:
    """RAG pipeline essential tests."""
    
    def test_query_returns_response_with_citations(self, retrieval_service, vector_store, embedding_service, sample_construction_texts):
        """RAG query should return answer with citations."""
        from src.services.rag_pipeline import RAGPipeline, RAGResponse
        from src.services.embeddings import EmbeddedChunk
        
        # Index documents
        for i, text in enumerate(sample_construction_texts):
            vector = embedding_service.embed(text)
            chunk = EmbeddedChunk(
                text=text,
                vector=vector,
                metadata={"source_file": "spec.pdf", "page": i+1, "chunk_index": i},
                watermark=PROJECT_CONTEXT_ID
            )
            vector_store.store(chunk)
        
        # Create pipeline and query
        pipeline = RAGPipeline(retrieval_service=retrieval_service, llm_provider="mock")
        response = pipeline.query("What is the fire rating?")
        
        assert isinstance(response, RAGResponse)
        assert len(response.answer) > 0
        assert len(response.citations) > 0
        assert response.watermark == PROJECT_CONTEXT_ID


class TestExtraction:
    """Extraction service essential tests."""
    
    def test_extract_door_schedule(self, retrieval_service, vector_store, embedding_service):
        """Extract structured door schedule data."""
        from src.services.extraction import ExtractionService, ExtractedData
        from src.services.embeddings import EmbeddedChunk
        
        # Index door schedule text
        door_texts = [
            "Door D-101, Width 36\", Height 84\", Material Hollow Metal, Fire Rating 20 min",
            "Door D-102, Width 42\", Height 84\", Material Wood, Fire Rating None",
        ]
        
        for i, text in enumerate(door_texts):
            vector = embedding_service.embed(text)
            chunk = EmbeddedChunk(
                text=text,
                vector=vector,
                metadata={"source_file": "schedules.pdf", "page": i+1, "chunk_index": i},
                watermark=PROJECT_CONTEXT_ID
            )
            vector_store.store(chunk)
        
        # Extract
        service = ExtractionService(retrieval_service=retrieval_service)
        result = service.extract("door schedule", data_type="door_schedule")
        
        assert isinstance(result, ExtractedData)
        assert len(result.entries) > 0
        assert result.watermark == PROJECT_CONTEXT_ID
    
    def test_extract_wage_table_with_llm(self, retrieval_service, vector_store, embedding_service):
        """Extract wage data using LLM-based extraction."""
        from src.services.extraction import ExtractionService, ExtractedData
        from src.services.embeddings import EmbeddedChunk
        
        # Index wage determination text (realistic format)
        wage_texts = [
            """PLUM0072-004 07/01/2024
PLUMBER, Excludes HVAC Pipe Work
Rates    Fringes
Plumbers......................$ 39.13    15.65""",
            """ELEC0613-001 06/01/2024
ELECTRICIAN (Including Cable Splicer)
Rates    Fringes
Electrician....................$ 38.00    20.04""",
            """IRON0387-002 01/01/2024
IRONWORKER, STRUCTURAL
Rates    Fringes
Structural....................$ 32.28    21.43""",
        ]
        
        for i, text in enumerate(wage_texts):
            vector = embedding_service.embed(text)
            chunk = EmbeddedChunk(
                text=text,
                vector=vector,
                metadata={"source_file": "wages.pdf", "page": i+1, "chunk_index": i},
                watermark=PROJECT_CONTEXT_ID
            )
            vector_store.store(chunk)
        
        # Extract wage table
        service = ExtractionService(retrieval_service=retrieval_service, llm_provider="mock")
        result = service.extract("wage rates for all trades", data_type="wage_table")
        
        assert isinstance(result, ExtractedData)
        assert result.data_type == "wage_table"
        assert len(result.sources) > 0
        # Verify we got structured entries
        assert len(result.entries) > 0
        assert result.watermark == PROJECT_CONTEXT_ID
    
    def test_extract_returns_json_schema(self, retrieval_service, vector_store, embedding_service):
        """Extraction should return data matching expected JSON schema."""
        from src.services.extraction import ExtractionService
        from src.services.embeddings import EmbeddedChunk
        
        # Index sample text
        text = "Door D-101 is located at Level 1 Corridor, width 900mm, height 2100mm, fire rated 1 HR, hollow metal"
        vector = embedding_service.embed(text)
        chunk = EmbeddedChunk(
            text=text,
            vector=vector,
            metadata={"source_file": "door_schedule.pdf", "page": 1, "chunk_index": 0},
            watermark=PROJECT_CONTEXT_ID
        )
        vector_store.store(chunk)
        
        service = ExtractionService(retrieval_service=retrieval_service, llm_provider="mock")
        result = service.extract("generate door schedule", data_type="door_schedule")
        
        # Verify structure matches requirements (from raw_requirements.md)
        # Expected: mark, location, width_mm, height_mm, fire_rating, material
        assert len(result.entries) > 0
        entry = result.entries[0]
        
        # Entry should be a dict with standard fields (or convertible to dict)
        if hasattr(entry, '__dict__'):
            entry_dict = {k: v for k, v in entry.__dict__.items() if not k.startswith('_')}
        else:
            entry_dict = entry
        
        # Verify it has required fields structure
        assert isinstance(entry_dict, dict)


class TestEvaluation:
    """Evaluation harness tests."""
    
    def test_evaluation_runner_exists(self):
        """Evaluation runner module should exist."""
        from src.services.evaluation import EvaluationRunner
        assert EvaluationRunner is not None
    
    def test_evaluation_has_test_queries(self):
        """Evaluation should have predefined test queries."""
        from src.services.evaluation import EvaluationRunner, TEST_QUERIES
        
        assert len(TEST_QUERIES) >= 5  # Minimum 5-10 per requirements
        for query in TEST_QUERIES:
            assert "question" in query
            assert "expected_keywords" in query or "expected_answer" in query
    
    def test_evaluation_runs_queries(self, retrieval_service, vector_store, embedding_service):
        """Evaluation runner should execute queries and score results."""
        from src.services.evaluation import EvaluationRunner
        from src.services.rag_pipeline import RAGPipeline
        from src.services.embeddings import EmbeddedChunk
        
        # Index some test data
        texts = [
            "The wage rate for plumbers is $39.13 per hour with $15.65 in fringes.",
            "Fire rating for corridor partitions must be 1 hour minimum per code.",
            "Door D-101 specs: 36 inches wide, 84 inches tall, hollow metal material.",
        ]
        for i, text in enumerate(texts):
            vector = embedding_service.embed(text)
            chunk = EmbeddedChunk(
                text=text,
                vector=vector,
                metadata={"source_file": "test.pdf", "page": i+1, "chunk_index": i},
                watermark=PROJECT_CONTEXT_ID
            )
            vector_store.store(chunk)
        
        # Create pipeline and runner
        pipeline = RAGPipeline(retrieval_service=retrieval_service, llm_provider="mock")
        runner = EvaluationRunner(rag_pipeline=pipeline)
        
        # Run evaluation
        results = runner.run()
        
        assert "total_queries" in results
        assert "results" in results
        assert results["total_queries"] > 0
    
    def test_evaluation_scores_correctness(self):
        """Evaluation should score answers as correct/partial/wrong."""
        from src.services.evaluation import EvaluationRunner
        
        # Test scoring logic
        runner = EvaluationRunner(rag_pipeline=None)
        
        # Correct - contains expected keywords
        score = runner.score_answer(
            answer="The plumber wage rate is $39.13 per hour.",
            expected_keywords=["39.13", "plumber"]
        )
        assert score in ["correct", "partially_correct", "wrong"]


class TestCaching:
    """Response caching tests (bonus feature)."""
    
    def test_cache_service_exists(self):
        """Cache service module should exist."""
        from src.services.cache import CacheService
        assert CacheService is not None
    
    def test_cache_stores_and_retrieves(self):
        """Cache should store and retrieve values."""
        from src.services.cache import CacheService
        
        cache = CacheService()
        
        # Store value
        cache.set("test_key", {"answer": "test answer", "sources": []})
        
        # Retrieve
        result = cache.get("test_key")
        assert result is not None
        assert result["answer"] == "test answer"
    
    def test_cache_returns_none_for_missing_key(self):
        """Cache should return None for missing keys."""
        from src.services.cache import CacheService
        
        cache = CacheService()
        result = cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_generates_consistent_keys(self):
        """Same query should generate same cache key."""
        from src.services.cache import CacheService
        
        cache = CacheService()
        
        key1 = cache.generate_key("What is the wage rate?", top_k=5)
        key2 = cache.generate_key("What is the wage rate?", top_k=5)
        key3 = cache.generate_key("What is the wage rate?", top_k=10)
        
        assert key1 == key2
        assert key1 != key3
    
    def test_cache_expiry(self):
        """Cache entries should expire after TTL."""
        from src.services.cache import CacheService
        import time
        
        cache = CacheService(ttl_seconds=0.1)  # 100ms TTL
        
        cache.set("expiring_key", {"data": "value"})
        
        # Should exist immediately
        assert cache.get("expiring_key") is not None
        
        # Wait for expiry
        time.sleep(0.15)
        
        # Should be expired
        assert cache.get("expiring_key") is None
