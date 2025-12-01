"""
Shared Test Fixtures - Optimized for Speed

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import pytest
import numpy as np
from pathlib import Path

from src.core.config import PROJECT_CONTEXT_ID, settings


# =============================================================================
# Module-scoped fixtures (loaded once per test module)
# =============================================================================

@pytest.fixture(scope="module")
def embedding_service():
    """
    Module-scoped embedding service - loads model ONCE per test file.
    This dramatically speeds up tests that use embeddings.
    """
    from src.services.embeddings import EmbeddingService
    return EmbeddingService()


@pytest.fixture(scope="function")
def auth_service():
    """
    Function-scoped auth service - fresh for each test.
    """
    from src.services.auth import AuthService
    return AuthService()


@pytest.fixture(scope="function")
def vector_store():
    """
    Function-scoped vector store - fresh for each test.
    Uses in-memory mode for speed.
    """
    from src.services.vector_store import VectorStoreService
    store = VectorStoreService(use_memory=True)
    yield store
    store.delete_collection()


@pytest.fixture(scope="function")
def retrieval_service(embedding_service, vector_store):
    """Retrieval service with shared embedding service."""
    from src.services.retrieval import RetrievalService
    return RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store
    )


# =============================================================================
# API Client Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.main import app
    return TestClient(app)


@pytest.fixture
def test_user_credentials():
    """Test user credentials from settings."""
    return {
        "email": settings.test_user_email,
        "password": settings.test_user_password
    }


@pytest.fixture
def auth_headers(client, test_user_credentials):
    """Auth headers with valid token for test user."""
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": test_user_credentials["email"],
            "password": test_user_credentials["password"],
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_construction_texts():
    """Sample construction document texts for testing."""
    return [
        "The fire rating for corridor walls must be a minimum of 1 hour per building code.",
        "Door D-101: Width 36\", Height 84\", Material Hollow Metal, Fire Rating 20 min.",
        "All structural steel members shall conform to ASTM A992 grade specifications.",
        "Window W-101: Size 48\"x60\", Type Fixed, Glass Tempered.",
        "The HVAC system shall provide 15 CFM of outside air per occupant minimum.",
    ]


@pytest.fixture
def sample_pdf_path():
    """Path to small test PDF (wages PDF - 6 pages)."""
    return Path(__file__).parent.parent / "Assets" / "Attachment+5+-+DBA+Wages+GA20250305+01-03-2025 (2).pdf"


@pytest.fixture
def sample_chunk():
    """Sample chunk dict for testing."""
    return {
        "text": "Fire rating for corridor walls is 1 hour minimum.",
        "chunk_index": 0,
        "source_file": "spec.pdf",
        "page": 5,
        "watermark": PROJECT_CONTEXT_ID
    }


@pytest.fixture
def sample_embedded_chunk(embedding_service, sample_chunk):
    """Sample embedded chunk for testing."""
    from src.services.embeddings import EmbeddedChunk
    vector = embedding_service.embed(sample_chunk["text"])
    return EmbeddedChunk(
        text=sample_chunk["text"],
        vector=vector,
        metadata={k: v for k, v in sample_chunk.items() if k != "text"},
        watermark=PROJECT_CONTEXT_ID
    )
