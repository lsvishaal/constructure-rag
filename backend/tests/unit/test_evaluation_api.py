"""
Evaluation API Tests.

Tests the evaluation endpoints for running RAG evaluation.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import pytest
from src.core.config import PROJECT_CONTEXT_ID


class TestEvaluationAPI:
    """Test evaluation API endpoints."""
    
    def test_list_queries_requires_auth(self, client):
        """Listing queries should require authentication."""
        response = client.get("/api/v1/evaluation/queries")
        assert response.status_code == 401
    
    def test_list_queries_returns_test_queries(self, client, auth_headers):
        """Authenticated user can list test queries."""
        response = client.get(
            "/api/v1/evaluation/queries",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_queries" in data
        assert data["total_queries"] >= 5  # Minimum per requirements
        assert "queries" in data
        assert len(data["queries"]) == data["total_queries"]
        
        # Each query should have required fields
        for query in data["queries"]:
            assert "id" in query
            assert "question" in query
            assert "expected_keywords" in query or "expected_answer" in query
    
    def test_run_evaluation_requires_auth(self, client):
        """Running evaluation should require authentication."""
        response = client.post("/api/v1/evaluation/run")
        assert response.status_code == 401
    
    def test_evaluation_response_has_watermark(self, client, auth_headers):
        """Evaluation responses should include watermark headers."""
        response = client.get(
            "/api/v1/evaluation/queries",
            headers=auth_headers
        )
        
        assert response.headers.get("X-Project-Id") == PROJECT_CONTEXT_ID
        assert "X-Build-Watermark" in response.headers
