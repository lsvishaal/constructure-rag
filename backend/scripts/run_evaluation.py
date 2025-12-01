#!/usr/bin/env python3
"""
Evaluation Script - Run RAG evaluation against indexed documents.

Usage:
    uv run python scripts/run_evaluation.py [--output report.json]

This script:
1. Connects to the existing Qdrant vector store
2. Runs predefined test queries through the RAG pipeline
3. Scores answers based on expected keywords
4. Outputs a detailed report

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings, PROJECT_CONTEXT_ID
from src.services.embeddings import EmbeddingService
from src.services.vector_store import VectorStoreService
from src.services.retrieval import RetrievalService
from src.services.rag_pipeline import RAGPipeline
from src.services.evaluation import EvaluationRunner, TEST_QUERIES


def main():
    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/evaluation_report.json",
        help="Output path for evaluation report (default: data/evaluation_report.json)"
    )
    parser.add_argument(
        "--llm",
        type=str,
        default=settings.llm_provider,
        choices=["mock", "ollama", "openai"],
        help="LLM provider to use (default: from settings)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only output the summary, no details"
    )
    args = parser.parse_args()
    
    print(f"\n🔍 Constructure RAG Evaluation")
    print(f"   Watermark: {PROJECT_CONTEXT_ID}")
    print("=" * 60)
    
    # Initialize services
    print("\n📦 Initializing services...")
    
    try:
        embedding_service = EmbeddingService()
        print(f"   ✅ Embeddings: {embedding_service.model_name}")
    except Exception as e:
        print(f"   ❌ Embeddings failed: {e}")
        sys.exit(1)
    
    try:
        vector_store = VectorStoreService(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
            use_memory=False
        )
        doc_count = vector_store.count()
        print(f"   ✅ Vector Store: {doc_count} chunks indexed")
        
        if doc_count == 0:
            print("\n⚠️  No documents indexed! Please ingest documents first:")
            print("   uv run python -c \"from src.services.fast_parser import FastPDFParser; ...\"")
            print("   Or use the Streamlit UI: uv run streamlit run streamlit_app.py")
            sys.exit(1)
            
    except Exception as e:
        print(f"   ❌ Vector Store failed: {e}")
        print("   Make sure Qdrant is running: docker-compose up -d qdrant")
        sys.exit(1)
    
    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store
    )
    print("   ✅ Retrieval service initialized")
    
    rag_pipeline = RAGPipeline(
        retrieval_service=retrieval_service,
        llm_provider=args.llm,
        ollama_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model
    )
    print(f"   ✅ RAG Pipeline: {args.llm}")
    
    # Run evaluation
    print(f"\n🧪 Running {len(TEST_QUERIES)} evaluation queries...")
    print("-" * 60)
    
    runner = EvaluationRunner(rag_pipeline=rag_pipeline)
    report = runner.run()
    
    # Print summary
    if not args.quiet:
        runner.print_summary(report)
    else:
        print(f"\n✅ Accuracy: {report['accuracy_score']:.1%}")
        print(f"   Correct: {report['correct']}/{report['total_queries']}")
        print(f"   Avg Time: {report['avg_response_time_ms']:.0f}ms")
    
    # Save report
    output_path = Path(args.output)
    runner.save_report(report, output_path)
    print(f"\n📄 Report saved to: {output_path}")
    
    # Exit code based on accuracy
    if report['accuracy_score'] >= 0.7:
        print("\n✅ Evaluation PASSED (accuracy >= 70%)")
        sys.exit(0)
    else:
        print("\n❌ Evaluation FAILED (accuracy < 70%)")
        sys.exit(1)


if __name__ == "__main__":
    main()
