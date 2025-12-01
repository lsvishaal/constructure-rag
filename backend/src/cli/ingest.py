"""
Ingestion CLI - Offline document ingestion

Usage:
    python -m src.cli.ingest --project-id=508-22-105
    python -m src.cli.ingest --pdf=Assets/myfile.pdf
    python -m src.cli.ingest --assets-dir=./Assets

Separates parsing from indexing for debuggability.

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
import argparse
import json
import logging
import time
from pathlib import Path
from dataclasses import dataclass, asdict

from src.core.config import PROJECT_CONTEXT_ID, settings
from src.services.smart_parser import SmartPDFParser, ParsedDocument
from src.services.smart_chunker import SmartChunker, SmartChunk
from src.services.embeddings import EmbeddingService, EmbeddedChunk
from src.services.vector_store import VectorStoreService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f"[{PROJECT_CONTEXT_ID}] %(asctime)s - %(levelname)s - %(message)s"
)
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


@dataclass
class IngestionReport:
    """Report of ingestion results."""
    project_id: str
    files_processed: int
    total_pages: int
    text_pages: int
    image_only_pages: int
    parse_errors: int
    total_chunks: int
    chunks_indexed: int
    total_time_seconds: float
    files: list
    watermark: str = PROJECT_CONTEXT_ID
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def summary(self) -> str:
        return (
            f"\n{'='*60}\n"
            f"INGESTION REPORT - {self.project_id}\n"
            f"{'='*60}\n"
            f"Files processed:    {self.files_processed}\n"
            f"Total pages:        {self.total_pages}\n"
            f"  - With text:      {self.text_pages}\n"
            f"  - Image-only:     {self.image_only_pages}\n"
            f"  - Parse errors:   {self.parse_errors}\n"
            f"Total chunks:       {self.total_chunks}\n"
            f"Chunks indexed:     {self.chunks_indexed}\n"
            f"Time:               {self.total_time_seconds:.2f}s\n"
            f"{'='*60}\n"
        )


class IngestionPipeline:
    """
    Complete ingestion pipeline: Parse → Chunk → Embed → Index
    
    Designed for offline batch processing, not real-time requests.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    def __init__(
        self,
        project_id: str,
        qdrant_url: str = None,
        collection_name: str = None,
        chunk_size: int = 400,
        save_parsed: bool = True,
        parsed_output_dir: str = "./data/parsed"
    ):
        self.project_id = project_id
        self.chunk_size = chunk_size
        self.save_parsed = save_parsed
        self.parsed_output_dir = Path(parsed_output_dir)
        
        # Initialize services
        self.parser = SmartPDFParser()
        self.chunker = SmartChunker(chunk_size=chunk_size)
        self.embedding_service = None  # Lazy load
        self.vector_store = None  # Lazy load
        
        self._qdrant_url = qdrant_url or settings.qdrant_url
        self._collection_name = collection_name or settings.qdrant_collection
    
    def _get_embedding_service(self) -> EmbeddingService:
        """Lazy load embedding service."""
        if self.embedding_service is None:
            logger.info(f"[{PROJECT_CONTEXT_ID}] Loading embedding model...")
            self.embedding_service = EmbeddingService()
        return self.embedding_service
    
    def _get_vector_store(self) -> VectorStoreService:
        """Lazy load vector store."""
        if self.vector_store is None:
            logger.info(f"[{PROJECT_CONTEXT_ID}] Connecting to Qdrant at {self._qdrant_url}...")
            self.vector_store = VectorStoreService(
                url=self._qdrant_url,
                collection_name=self._collection_name,
                use_memory=False
            )
        return self.vector_store
    
    def ingest_directory(self, assets_dir: str) -> IngestionReport:
        """Ingest all PDFs in a directory."""
        assets_path = Path(assets_dir)
        if not assets_path.exists():
            raise FileNotFoundError(f"Assets directory not found: {assets_dir}")
        
        pdf_files = list(assets_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {assets_dir}")
            return IngestionReport(
                project_id=self.project_id,
                files_processed=0,
                total_pages=0,
                text_pages=0,
                image_only_pages=0,
                parse_errors=0,
                total_chunks=0,
                chunks_indexed=0,
                total_time_seconds=0,
                files=[]
            )
        
        logger.info(f"[{PROJECT_CONTEXT_ID}] Found {len(pdf_files)} PDF files to ingest")
        
        start_time = time.time()
        all_results = []
        total_pages = 0
        total_text_pages = 0
        total_image_only = 0
        total_errors = 0
        total_chunks = 0
        total_indexed = 0
        
        for pdf_path in pdf_files:
            result = self.ingest_file(str(pdf_path))
            all_results.append(result)
            total_pages += result.get("total_pages", 0)
            total_text_pages += result.get("text_pages", 0)
            total_image_only += result.get("image_only_pages", 0)
            total_errors += result.get("parse_errors", 0)
            total_chunks += result.get("chunks_created", 0)
            total_indexed += result.get("chunks_indexed", 0)
        
        total_time = time.time() - start_time
        
        report = IngestionReport(
            project_id=self.project_id,
            files_processed=len(pdf_files),
            total_pages=total_pages,
            text_pages=total_text_pages,
            image_only_pages=total_image_only,
            parse_errors=total_errors,
            total_chunks=total_chunks,
            chunks_indexed=total_indexed,
            total_time_seconds=round(total_time, 2),
            files=all_results
        )
        
        logger.info(report.summary())
        return report
    
    def ingest_file(self, pdf_path: str) -> dict:
        """Ingest a single PDF file."""
        pdf_path = Path(pdf_path)
        logger.info(f"[{PROJECT_CONTEXT_ID}] Ingesting {pdf_path.name}...")
        
        file_start = time.time()
        result = {
            "file_name": pdf_path.name,
            "status": "success"
        }
        
        try:
            # Step 1: Parse
            logger.info(f"[{PROJECT_CONTEXT_ID}] Step 1: Parsing...")
            document = self.parser.parse(str(pdf_path), project_id=self.project_id)
            
            result.update({
                "total_pages": document.total_pages,
                "text_pages": document.text_pages,
                "image_only_pages": document.image_only_pages,
                "parse_errors": document.parse_errors,
                "document_type": document.document_type
            })
            
            # Save parsed data for debugging/re-chunking
            if self.save_parsed:
                self.parsed_output_dir.mkdir(parents=True, exist_ok=True)
                parsed_path = self.parsed_output_dir / f"{pdf_path.stem}.jsonl"
                self.parser.save_to_jsonl(document, str(parsed_path))
                result["parsed_file"] = str(parsed_path)
            
            # Step 2: Chunk
            logger.info(f"[{PROJECT_CONTEXT_ID}] Step 2: Chunking...")
            chunks = self.chunker.chunk_document(document)
            result["chunks_created"] = len(chunks)
            
            # Step 3: Embed and Index
            logger.info(f"[{PROJECT_CONTEXT_ID}] Step 3: Embedding and indexing {len(chunks)} chunks...")
            indexed = self._index_chunks(chunks)
            result["chunks_indexed"] = indexed
            
            file_time = time.time() - file_start
            result["time_seconds"] = round(file_time, 2)
            
            logger.info(
                f"[{PROJECT_CONTEXT_ID}] Completed {pdf_path.name}: "
                f"{document.total_pages} pages, {len(chunks)} chunks, {file_time:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"[{PROJECT_CONTEXT_ID}] Error ingesting {pdf_path.name}: {e}", exc_info=True)
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def _index_chunks(self, chunks: list[SmartChunk]) -> int:
        """Embed and store chunks in vector DB."""
        embedding_service = self._get_embedding_service()
        vector_store = self._get_vector_store()
        
        indexed = 0
        batch_size = 10
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            for chunk in batch:
                try:
                    # Embed
                    vector = embedding_service.embed(chunk.text)
                    
                    # Create embedded chunk
                    embedded = EmbeddedChunk(
                        text=chunk.text,
                        vector=vector,
                        metadata=chunk.to_metadata_dict(),
                        watermark=PROJECT_CONTEXT_ID
                    )
                    
                    # Store
                    vector_store.store(embedded)
                    indexed += 1
                    
                except Exception as e:
                    logger.warning(f"[{PROJECT_CONTEXT_ID}] Failed to index chunk {chunk.chunk_index}: {e}")
            
            # Log progress
            if (i + batch_size) % 50 == 0 or i + batch_size >= len(chunks):
                logger.info(f"[{PROJECT_CONTEXT_ID}] Indexed {min(i+batch_size, len(chunks))}/{len(chunks)} chunks")
        
        return indexed


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest construction documents into RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Ingest all PDFs in Assets directory
    python -m src.cli.ingest --assets-dir=./Assets --project-id=508-22-105
    
    # Ingest a single PDF
    python -m src.cli.ingest --pdf=./Assets/myfile.pdf --project-id=test
    
    # Use custom Qdrant settings
    python -m src.cli.ingest --assets-dir=./Assets --qdrant-url=http://localhost:6333
        """
    )
    
    parser.add_argument(
        "--project-id", 
        default="default",
        help="Project identifier for this document set"
    )
    parser.add_argument(
        "--assets-dir",
        help="Directory containing PDF files to ingest"
    )
    parser.add_argument(
        "--pdf",
        help="Path to single PDF file to ingest"
    )
    parser.add_argument(
        "--qdrant-url",
        default=settings.qdrant_url,
        help=f"Qdrant server URL (default: {settings.qdrant_url})"
    )
    parser.add_argument(
        "--collection",
        default=settings.qdrant_collection,
        help=f"Qdrant collection name (default: {settings.qdrant_collection})"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=400,
        help="Target chunk size in tokens (default: 400)"
    )
    parser.add_argument(
        "--output-dir",
        default="./data/parsed",
        help="Directory to save parsed JSON files"
    )
    parser.add_argument(
        "--no-save-parsed",
        action="store_true",
        help="Don't save intermediate parsed files"
    )
    
    args = parser.parse_args()
    
    if not args.assets_dir and not args.pdf:
        parser.error("Must specify either --assets-dir or --pdf")
    
    # Create pipeline
    pipeline = IngestionPipeline(
        project_id=args.project_id,
        qdrant_url=args.qdrant_url,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        save_parsed=not args.no_save_parsed,
        parsed_output_dir=args.output_dir
    )
    
    # Run ingestion
    if args.pdf:
        result = pipeline.ingest_file(args.pdf)
        print(json.dumps(result, indent=2))
    else:
        report = pipeline.ingest_directory(args.assets_dir)
        
        # Save report
        report_path = Path(args.output_dir) / "ingestion_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
