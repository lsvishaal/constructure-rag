"""
Evaluation Harness Service - Part 4

Runs test queries through RAG pipeline and scores results.
Implements lightweight evaluation for quality assessment.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass, field
from typing import Any
import logging
import time
import json
from pathlib import Path

from src.core.config import PROJECT_CONTEXT_ID

logger = logging.getLogger(__name__)


# =============================================================================
# Test Queries - Based on provided construction documents
# =============================================================================

TEST_QUERIES = [
    # ==========================================================================
    # Safe Davis-Bacon Wage Determination Queries (GA20250305)
    # Based on actual document content - no external knowledge needed
    # ==========================================================================
    
    # General Decision Info
    {
        "id": "db_1",
        "question": "What is the General Decision Number for this wage determination?",
        "expected_keywords": ["GA20250305"],
        "expected_answer": "GA20250305",
        "category": "wage_determination",
    },
    {
        "id": "db_2",
        "question": "What state and county does this wage determination cover?",
        "expected_keywords": ["georgia", "dekalb"],
        "expected_answer": "Dekalb County in Georgia",
        "category": "wage_determination",
    },
    {
        "id": "db_3",
        "question": "What type of construction does this wage determination apply to?",
        "expected_keywords": ["building"],
        "expected_answer": "Building construction projects",
        "category": "wage_determination",
    },
    
    # Executive Order Minimums
    {
        "id": "db_4",
        "question": "What is the Executive Order 14026 minimum wage rate for 2025?",
        "expected_keywords": ["17.75", "14026"],
        "expected_answer": "$17.75 per hour under Executive Order 14026",
        "category": "wage_determination",
    },
    {
        "id": "db_5",
        "question": "What is the Executive Order 13658 minimum wage rate?",
        "expected_keywords": ["13.30", "13658"],
        "expected_answer": "$13.30 per hour under Executive Order 13658",
        "category": "wage_determination",
    },
    
    # Specific Trade Rates from Document
    {
        "id": "db_6",
        "question": "What is the wage rate for an Electrician?",
        "expected_keywords": ["34.50", "electrician"],
        "expected_answer": "Electrician rate is $34.50",
        "category": "wage_determination",
    },
    {
        "id": "db_7",
        "question": "What is the rate for Sheet Metal Workers doing HVAC Duct Installation?",
        "expected_keywords": ["35.21", "sheet metal"],
        "expected_answer": "Sheet Metal Worker (HVAC Duct) rate is $35.21",
        "category": "wage_determination",
    },
    {
        "id": "db_8",
        "question": "What are the wages for Ironworkers?",
        "expected_keywords": ["30.24", "ironworker"],
        "expected_answer": "Ironworker rate is $30.24",
        "category": "wage_determination",
    },
    {
        "id": "db_9",
        "question": "What is the wage rate for a Millwright?",
        "expected_keywords": ["31.58", "millwright"],
        "expected_answer": "Millwright rate is $31.58",
        "category": "wage_determination",
    },
    {
        "id": "db_10",
        "question": "What is the rate for Power Equipment Operators running a Crane?",
        "expected_keywords": ["34.66", "crane"],
        "expected_answer": "Crane Operator rate is $34.66",
        "category": "wage_determination",
    },
    
    # Edge case - should NOT find answer
    {
        "id": "edge_1",
        "question": "What is the weather forecast for construction?",
        "expected_keywords": [],
        "expected_answer": "Information not found in documents",
        "category": "edge_case",
        "expect_no_answer": True,
    },
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class QueryResult:
    """
    Result of a single evaluation query.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    query_id: str
    question: str
    expected_keywords: list[str]
    actual_answer: str
    sources_used: list[dict]
    score: str  # "correct", "partially_correct", "wrong"
    response_time_ms: float
    keywords_found: list[str] = field(default_factory=list)
    keywords_missing: list[str] = field(default_factory=list)
    error: str | None = None
    watermark: str = PROJECT_CONTEXT_ID


@dataclass
class EvaluationReport:
    """
    Complete evaluation report.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    total_queries: int
    correct: int
    partially_correct: int
    wrong: int
    errors: int
    accuracy_score: float  # 0.0 to 1.0
    avg_response_time_ms: float
    results: list[QueryResult] = field(default_factory=list)
    timestamp: str = ""
    watermark: str = PROJECT_CONTEXT_ID


# =============================================================================
# Evaluation Runner
# =============================================================================

class EvaluationRunner:
    """
    Runs evaluation queries through RAG pipeline and scores results.
    
    Scoring logic:
    - correct: All expected keywords found in answer
    - partially_correct: Some expected keywords found
    - wrong: No expected keywords found (or incorrect info)
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    def __init__(
        self,
        rag_pipeline: Any | None = None,
        queries: list[dict] | None = None,
        watermark: str = PROJECT_CONTEXT_ID
    ):
        """
        Initialize evaluation runner.
        
        Args:
            rag_pipeline: RAG pipeline instance (optional for scoring tests)
            queries: Custom test queries (defaults to TEST_QUERIES)
            watermark: Project watermark identifier
        """
        self.rag_pipeline = rag_pipeline
        self.queries = queries or TEST_QUERIES
        self.watermark = watermark
        
        logger.info(f"[{self.watermark}] EvaluationRunner initialized with {len(self.queries)} queries")
    
    def run(self, queries: list[dict] | None = None) -> dict:
        """
        Run all evaluation queries and generate report.
        
        Args:
            queries: Optional subset of queries to run
            
        Returns:
            Dictionary with evaluation results
        """
        queries_to_run = queries or self.queries
        results = []
        
        for query in queries_to_run:
            result = self._run_single_query(query)
            results.append(result)
        
        # Calculate summary statistics
        correct = sum(1 for r in results if r.score == "correct")
        partial = sum(1 for r in results if r.score == "partially_correct")
        wrong = sum(1 for r in results if r.score == "wrong")
        errors = sum(1 for r in results if r.error)
        
        total = len(results)
        # Weighted score: correct=1, partial=0.5, wrong=0
        accuracy = (correct + partial * 0.5) / total if total > 0 else 0.0
        
        avg_time = sum(r.response_time_ms for r in results) / total if total > 0 else 0.0
        
        report = EvaluationReport(
            total_queries=total,
            correct=correct,
            partially_correct=partial,
            wrong=wrong,
            errors=errors,
            accuracy_score=accuracy,
            avg_response_time_ms=avg_time,
            results=results,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            watermark=self.watermark
        )
        
        return self._report_to_dict(report)
    
    def _run_single_query(self, query: dict) -> QueryResult:
        """Run a single evaluation query."""
        query_id = query.get("id", "unknown")
        question = query["question"]
        expected = query.get("expected_keywords", [])
        expect_no_answer = query.get("expect_no_answer", False)
        
        start_time = time.time()
        
        try:
            if self.rag_pipeline is None:
                # Mock response for testing without pipeline
                actual_answer = "Mock answer for testing"
                sources = []
            else:
                response = self.rag_pipeline.query(question, top_k=5)
                actual_answer = response.answer
                sources = [
                    {
                        "file": c.source_file,
                        "page": c.page,
                        "score": c.score
                    }
                    for c in response.citations
                ]
            
            response_time = (time.time() - start_time) * 1000
            
            # Score the answer
            score = self.score_answer(actual_answer, expected, expect_no_answer)
            
            # Track which keywords were found/missing
            answer_lower = actual_answer.lower()
            found = [kw for kw in expected if kw.lower() in answer_lower]
            missing = [kw for kw in expected if kw.lower() not in answer_lower]
            
            return QueryResult(
                query_id=query_id,
                question=question,
                expected_keywords=expected,
                actual_answer=actual_answer,
                sources_used=sources,
                score=score,
                response_time_ms=response_time,
                keywords_found=found,
                keywords_missing=missing,
                watermark=self.watermark
            )
            
        except Exception as e:
            logger.error(f"[{self.watermark}] Query error for {query_id}: {e}")
            return QueryResult(
                query_id=query_id,
                question=question,
                expected_keywords=expected,
                actual_answer="",
                sources_used=[],
                score="wrong",
                response_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
                watermark=self.watermark
            )
    
    def score_answer(
        self,
        answer: str,
        expected_keywords: list[str],
        expect_no_answer: bool = False
    ) -> str:
        """
        Score an answer based on expected keywords.
        
        Args:
            answer: The actual answer from RAG
            expected_keywords: Keywords that should appear
            expect_no_answer: Whether we expect no answer (edge case)
            
        Returns:
            "correct", "partially_correct", or "wrong"
        """
        if not answer:
            return "wrong"
        
        answer_lower = answer.lower()
        
        # Handle edge case where we expect no answer
        if expect_no_answer:
            no_answer_phrases = [
                "couldn't find",
                "not found",
                "no information",
                "unable to find",
                "don't have information",
                "cannot answer"
            ]
            if any(phrase in answer_lower for phrase in no_answer_phrases):
                return "correct"
            return "wrong"
        
        # Normal scoring based on keywords
        if not expected_keywords:
            # No keywords to check, consider it correct if we got any answer
            return "correct" if len(answer) > 10 else "wrong"
        
        found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
        total = len(expected_keywords)
        
        if found == total:
            return "correct"
        elif found > 0:
            return "partially_correct"
        else:
            return "wrong"
    
    def _report_to_dict(self, report: EvaluationReport) -> dict:
        """Convert report to dictionary for JSON serialization."""
        return {
            "total_queries": report.total_queries,
            "correct": report.correct,
            "partially_correct": report.partially_correct,
            "wrong": report.wrong,
            "errors": report.errors,
            "accuracy_score": report.accuracy_score,
            "avg_response_time_ms": report.avg_response_time_ms,
            "timestamp": report.timestamp,
            "watermark": report.watermark,
            "results": [
                {
                    "query_id": r.query_id,
                    "question": r.question,
                    "expected_keywords": r.expected_keywords,
                    "actual_answer": r.actual_answer[:200] + "..." if len(r.actual_answer) > 200 else r.actual_answer,
                    "sources_used": r.sources_used,
                    "score": r.score,
                    "response_time_ms": r.response_time_ms,
                    "keywords_found": r.keywords_found,
                    "keywords_missing": r.keywords_missing,
                    "error": r.error,
                }
                for r in report.results
            ]
        }
    
    def save_report(self, report: dict, path: str | Path) -> None:
        """Save evaluation report to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"[{self.watermark}] Evaluation report saved to {path}")
    
    def print_summary(self, report: dict) -> None:
        """Print human-readable summary of evaluation."""
        print("\n" + "=" * 60)
        print(f"EVALUATION REPORT - {report['timestamp']}")
        print("=" * 60)
        print(f"Total Queries:     {report['total_queries']}")
        print(f"Correct:           {report['correct']} ✅")
        print(f"Partially Correct: {report['partially_correct']} ⚠️")
        print(f"Wrong:             {report['wrong']} ❌")
        print(f"Errors:            {report['errors']} ��")
        print(f"Accuracy Score:    {report['accuracy_score']:.1%}")
        print(f"Avg Response Time: {report['avg_response_time_ms']:.0f}ms")
        print("-" * 60)
        
        for result in report['results']:
            status = "✅" if result['score'] == "correct" else ("⚠️" if result['score'] == "partially_correct" else "❌")
            print(f"{status} [{result['query_id']}] {result['question'][:50]}...")
            if result['error']:
                print(f"   ERROR: {result['error']}")
            elif result['keywords_missing']:
                print(f"   Missing: {', '.join(result['keywords_missing'])}")
        
        print("=" * 60 + "\n")
