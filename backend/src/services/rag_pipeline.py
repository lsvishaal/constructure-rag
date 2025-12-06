"""
RAG Pipeline Service - Phase 4 (Async Optimized)

Complete RAG (Retrieval-Augmented Generation) pipeline.
Combines retrieval with LLM generation for Q&A with citations.

Optimizations applied:
- Temperature 0 for factual responses
- Structure-aware prompting for tables
- Markdown output enforcement
- Relevance threshold filtering
- Fully async with concurrent operations
- httpx async client for LLM calls

Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
"""
from dataclasses import dataclass, field
from typing import Any
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging
import re

import httpx

from src.core.config import PROJECT_CONTEXT_ID, settings
from src.services.retrieval import RetrievalService, RetrievalResult
from src.services.cache import CacheService, get_cache

logger = logging.getLogger(__name__)

# Async HTTP client for LLM calls (reuse connection)
_http_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    """Get or create async HTTP client for LLM calls."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Citation:
    """
    Source citation for RAG response.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    text: str
    source_file: str | None
    page: int | None
    chunk_index: int | None = None
    score: float = 0.0
    watermark: str = PROJECT_CONTEXT_ID


@dataclass
class RAGResponse:
    """
    Complete RAG response with answer and citations.
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    answer: str
    citations: list[Citation] = field(default_factory=list)
    query: str = ""
    error: bool = False
    error_message: str | None = None
    watermark: str = PROJECT_CONTEXT_ID


# =============================================================================
# RAG Pipeline Service (Async Optimized)
# =============================================================================

class RAGPipeline:
    """
    Complete RAG pipeline for construction document Q&A.
    
    Pipeline flow:
    1. Retrieve relevant chunks from vector store (async)
    2. Filter by relevance threshold
    3. Build structured prompt with context
    4. Generate answer with LLM (async, temperature=0)
    5. Extract and format citations
    
    Async features:
    - Concurrent retrieval operations
    - Non-blocking LLM generation
    - Connection pooling for HTTP requests
    
    Watermark: CONSTRUCTURE_RAG_VISHAAL_LS_2025
    """
    
    # ==========================================================================
    # SYSTEM PROMPT - Optimized for Qwen2.5-7B RAG
    # ==========================================================================
    SYSTEM_PROMPT = """You are a Construction Document Assistant that provides precise, factual answers from source documents.

CRITICAL RULES:
1. Answer ONLY using information explicitly stated in the provided CONTEXT
2. If the answer is not in the context, respond: "This information is not found in the provided documents."
3. Be concise - 1-3 sentences for simple facts, tables for wage/rate data
4. Always cite the page number: [Page X]
5. For wage rates, use this format: "Classification: $XX.XX/hour, Fringes: $XX.XX [Page X]"

FORBIDDEN:
- Making up information not in the context
- Using external knowledge or statistics
- Speculation or interpretation
- Verbose explanations when a direct answer suffices"""

    CONTEXT_TEMPLATE = """CONTEXT FROM CONSTRUCTION DOCUMENTS:
{context}

---
QUESTION: {question}

ANSWER:"""

    # Relevance threshold - chunks below this score are filtered out
    MIN_RELEVANCE_SCORE = 0.01  # Very low since RRF scores are rank-based (~0.03)

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_provider: str = "mock",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "llama3.2:1b",
        watermark: str = PROJECT_CONTEXT_ID,
        cache: CacheService | None = None,
        enable_cache: bool = True,
        min_relevance_score: float = 0.01
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            retrieval_service: Service for document retrieval
            llm_provider: LLM provider ('mock', 'ollama', 'openai')
            ollama_url: Ollama server URL
            ollama_model: Ollama model name
            watermark: Project watermark identifier
            cache: Optional cache service instance
            enable_cache: Whether to use caching (default True)
            min_relevance_score: Minimum score to include a chunk (default 0.3)
        """
        self.retrieval_service = retrieval_service
        self.llm_provider = llm_provider
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.watermark = watermark
        self.enable_cache = enable_cache
        self.cache = cache if cache else (get_cache() if enable_cache else None)
        self.min_relevance_score = min_relevance_score
        
        logger.info(f"[{self.watermark}] RAGPipeline initialized with {llm_provider} (cache={'enabled' if enable_cache else 'disabled'})")
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        use_keyword_search: bool = True,
        bypass_cache: bool = False
    ) -> RAGResponse:
        """
        Answer a question using RAG (sync wrapper).
        
        For async code, use query_async() instead.
        
        Args:
            question: User's question
            top_k: Number of context chunks to retrieve
            use_keyword_search: Enable hybrid keyword search
            bypass_cache: Force fresh query, ignoring cache
            
        Returns:
            RAGResponse with answer and citations
        """
        # Run async query in event loop - handle various event loop states
        try:
            # Try to get existing loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context - need to run in thread with new loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self._query_fresh_loop(question, top_k, use_keyword_search, bypass_cache)
                    )
                    return future.result(timeout=120)
            except RuntimeError:
                # No running loop - we can create one
                return asyncio.run(
                    self.query_async(question, top_k, use_keyword_search, bypass_cache)
                )
        except Exception as e:
            logger.error(f"[{self.watermark}] Query error: {e}")
            return RAGResponse(
                answer="An error occurred while processing your question.",
                citations=[],
                query=question,
                error=True,
                error_message=str(e),
                watermark=self.watermark
            )
    
    async def _query_fresh_loop(
        self,
        question: str,
        top_k: int = 5,
        use_keyword_search: bool = True,
        bypass_cache: bool = False
    ) -> RAGResponse:
        """Run query with fresh HTTP client (for thread pool execution)."""
        # Create a fresh client for this thread
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Temporarily store the global client and replace
            global _http_client
            old_client = _http_client
            _http_client = client
            try:
                return await self.query_async(question, top_k, use_keyword_search, bypass_cache)
            finally:
                _http_client = old_client
    
    async def query_async(
        self,
        question: str,
        top_k: int = 5,
        use_keyword_search: bool = True,
        bypass_cache: bool = False
    ) -> RAGResponse:
        """
        Answer a question using RAG (async).
        
        Args:
            question: User's question
            top_k: Number of context chunks to retrieve
            use_keyword_search: Enable hybrid keyword search
            bypass_cache: Force fresh query, ignoring cache
            
        Returns:
            RAGResponse with answer and citations
        """
        # Handle empty question
        if not question or not question.strip():
            return RAGResponse(
                answer="Please provide a question.",
                citations=[],
                query=question,
                error=True,
                error_message="Empty question",
                watermark=self.watermark
            )
        
        # Check cache first
        cache_key = None
        if self.cache and self.enable_cache and not bypass_cache:
            cache_key = self.cache.generate_key(
                question,
                top_k=top_k,
                llm=self.llm_provider,
                model=self.ollama_model
            )
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"[{self.watermark}] Cache hit for query: {question[:50]}...")
                return cached
        
        try:
            # Retrieve relevant documents with hybrid search (async)
            results = await self.retrieval_service.retrieve_async(
                question,
                top_k=top_k,
                use_keyword_search=use_keyword_search
            )
            
            # Filter by relevance score - don't include garbage
            filtered_results = [
                r for r in results 
                if r.score >= self.min_relevance_score
            ]
            
            logger.debug(f"[{self.watermark}] Retrieved {len(results)} chunks, {len(filtered_results)} above threshold")
            
            # Handle no results
            if not filtered_results:
                return RAGResponse(
                    answer="I couldn't find relevant information in the documents to answer your question. Please try rephrasing or ask about a different topic.",
                    citations=[],
                    query=question,
                    error=False,
                    watermark=self.watermark
                )
            
            # Build prompt with context
            prompt = self.build_prompt(question, top_k, filtered_results)
            
            # Generate answer (async)
            answer = await self._generate_answer_async(prompt)
            
            # Build citations from filtered results
            citations = self._build_citations(filtered_results)
            
            response = RAGResponse(
                answer=answer,
                citations=citations,
                query=question,
                error=False,
                watermark=self.watermark
            )
            
            # Store in cache
            if cache_key and self.cache:
                self.cache.set(cache_key, response)
                logger.debug(f"[{self.watermark}] Cached response for: {question[:50]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"[{self.watermark}] RAG pipeline error: {e}")
            return RAGResponse(
                answer="An error occurred while processing your question.",
                citations=[],
                query=question,
                error=True,
                error_message=str(e),
                watermark=self.watermark
            )
    
    def build_prompt(
        self,
        question: str,
        top_k: int = 5,
        results: list[RetrievalResult] | None = None
    ) -> str:
        """
        Build the prompt with retrieved context.
        
        Formats context with clear source attribution and structure detection.
        
        Args:
            question: User's question
            top_k: Number of chunks to include
            results: Pre-retrieved results (optional)
            
        Returns:
            Formatted prompt string
        """
        # Retrieve if not provided (sync for backward compat)
        if results is None:
            results = self.retrieval_service.retrieve(question, top_k=top_k)
        
        # Format context with improved structure
        context_parts = []
        for i, result in enumerate(results[:top_k], 1):
            source = result.metadata.get("source_file", "unknown")
            page = result.metadata.get("page", "?")
            section = result.metadata.get("section", "")
            
            # Clean and normalize the text
            text = self._clean_text(result.text)
            
            # Detect if this looks like tabular data
            is_tabular = self._detect_tabular_data(text)
            
            # Format the source block
            header = f"[SOURCE {i}: {source}, Page {page}]"
            if section:
                header += f" Section: {section}"
            if is_tabular:
                header += " [TABULAR DATA]"
            
            context_parts.append(f"{header}\n{text}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Build full prompt
        prompt = self.CONTEXT_TEMPLATE.format(
            context=context,
            question=question
        )
        
        return prompt
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for better LLM comprehension.
        
        - Normalizes excessive whitespace
        - Preserves table-like structures
        - Removes garbage characters
        """
        if not text:
            return ""
        
        # Replace multiple spaces with single space (but preserve newlines for tables)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Replace more than 2 consecutive newlines with 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up lines that are just dots or dashes (table alignment chars)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that are ONLY dots/dashes (PDF table formatting artifacts)
            if line and not re.match(r'^[\.\-_\s]+$', line):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _detect_tabular_data(self, text: str) -> bool:
        """
        Detect if text contains tabular data (rates, schedules, etc).
        
        Returns True if text looks like it contains structured data.
        """
        # Check for dollar signs with numbers (wage data)
        if re.search(r'\$\s*\d+\.\d{2}', text):
            return True
        
        # Check for multiple aligned numbers
        if re.search(r'\d+\.\d+\s+\d+\.\d+', text):
            return True
        
        # Check for common table headers
        table_keywords = ['rate', 'fringes', 'classification', 'schedule', 'width', 'height', 'mark']
        text_lower = text.lower()
        if sum(1 for kw in table_keywords if kw in text_lower) >= 2:
            return True
        
        return False
    
    def _generate_answer(self, prompt: str) -> str:
        """
        Generate answer using configured LLM (sync wrapper).
        
        Args:
            prompt: Formatted prompt with context
            
        Returns:
            Generated answer text
        """
        try:
            return asyncio.run(self._generate_answer_async(prompt))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._generate_answer_async(prompt))
    
    async def _generate_answer_async(self, prompt: str) -> str:
        """
        Generate answer using configured LLM (async).
        
        Args:
            prompt: Formatted prompt with context
            
        Returns:
            Generated answer text
        """
        if self.llm_provider == "mock":
            return self._mock_generate(prompt)
        elif self.llm_provider == "ollama":
            return await self._ollama_generate_async(prompt)
        elif self.llm_provider == "openai":
            return await self._openai_generate_async(prompt)
        else:
            return self._mock_generate(prompt)
    
    def _mock_generate(self, prompt: str) -> str:
        """Mock LLM for testing - returns context-based response."""
        # Extract the first piece of context as the answer
        if "Context from construction documents:" in prompt:
            # Find the context section
            context_start = prompt.find("Context from construction documents:") + len("Context from construction documents:")
            context_end = prompt.find("---", context_start)
            if context_end > context_start:
                context = prompt[context_start:context_end].strip()
                # Return first sentence of context as mock answer
                first_source = context.split("\n\n")[0] if "\n\n" in context else context
                if "]" in first_source:
                    answer = first_source.split("]", 1)[1].strip()
                else:
                    answer = first_source
                return f"Based on the construction documents: {answer}"
        
        return "Based on the available documents, I can provide information on construction specifications."
    
    async def _ollama_generate_async(self, prompt: str) -> str:
        """Generate using Ollama (Qwen2.5-7B) - optimized for RAG accuracy."""
        try:
            client = get_http_client()
            
            # Build the full prompt with system instructions
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"
            
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "keep_alive": "10m",   # Keep model loaded for 10 min
                    "options": {
                        "temperature": 0,      # Deterministic for factual RAG
                        "num_predict": 300,    # Allow longer responses for tables
                        "num_ctx": 8192,       # Qwen2.5 supports 128K, use 8K for speed
                        "top_p": 1.0,
                        "top_k": 1,            # Most likely token only
                        "repeat_penalty": 1.1, # Light penalty (Qwen is less repetitive)
                        "stop": ["CONTEXT:", "QUESTION:", "---"],
                    }
                },
                timeout=120.0  # 2 min timeout for larger model
            )
            response.raise_for_status()
            answer = response.json().get("response", "")
            
            # Post-process: clean up any artifacts
            answer = self._post_process_answer(answer)
            
            return answer
        except httpx.TimeoutException as e:
            logger.error(f"[{self.watermark}] Ollama timeout: {e}")
            raise Exception("LLM request timed out. The model may be loading - please try again.")
        except httpx.ConnectError as e:
            logger.error(f"[{self.watermark}] Ollama connection error: {e}")
            raise Exception("Cannot connect to LLM service. Please ensure Ollama is running.")
        except Exception as e:
            logger.error(f"[{self.watermark}] Ollama error: {e}")
            raise Exception(f"LLM generation failed: {str(e)}")
    
    async def _openai_generate_async(self, prompt: str) -> str:
        """Generate using OpenAI API - optimized async for RAG accuracy."""
        try:
            import openai
            client = openai.AsyncOpenAI()
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,  # CRITICAL: 0 for factual RAG responses
                max_tokens=500,
            )
            answer = response.choices[0].message.content
            return self._post_process_answer(answer)
        except Exception as e:
            logger.error(f"[{self.watermark}] OpenAI error: {e}")
            return self._mock_generate(prompt)
    
    def _post_process_answer(self, answer: str) -> str:
        """
        Post-process LLM answer to clean up common issues.
        """
        if not answer:
            return answer
        
        # Remove common LLM preambles
        preambles = [
            "Based on the provided context,",
            "Based on the documents,",
            "Based on the construction documents,",
            "According to the documents,",
            "According to the context,",
            "Here is the information:",
            "Here's what I found:",
        ]
        
        for preamble in preambles:
            if answer.lower().startswith(preamble.lower()):
                answer = answer[len(preamble):].strip()
                break
        
        return answer.strip()
    
    def _build_citations(self, results: list[RetrievalResult]) -> list[Citation]:
        """Build citations from retrieval results."""
        citations = []
        for result in results:
            citations.append(Citation(
                text=result.text[:200] + "..." if len(result.text) > 200 else result.text,
                source_file=result.metadata.get("source_file"),
                page=result.metadata.get("page"),
                chunk_index=result.metadata.get("chunk_index"),
                score=result.score,
                watermark=self.watermark
            ))
        return citations
