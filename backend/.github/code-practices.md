# Code Practices & Principles Guide

**For Automated GitHub PR Review Agent — Lyzr Backend Intern Challenge**

---

## Core Principles (In Order of Priority)

### 1. YAGNI (You Aren't Gonna Need It)

**Rule**: Don't build features, abstractions, or tooling unless they're needed to pass the current requirements.

- ❌ Don't pre-build a full agent framework with plugins, adapters, and config layers if you only need 4 agents.
- ✅ Build a simple agent orchestrator first. If you have time and it fits naturally, add the pluggable pattern.
- ❌ Don't set up a full-featured database, migrations, or ORMs for temporary state.
- ✅ Use in-memory storage, env vars, or minimal JSON files.

**For this project**:
- Skip fancy caching layers unless PR review latency becomes a blocker.
- Don't add authentication/authorization unless explicitly in requirements.
- Avoid "future-proof" config structures; use what you need now.

---

### 2. SoC (Separation of Concerns)

**Rule**: Each module/class should have one clear responsibility. If a function/class does multiple things, split it.

**Layers**:
- **GitHub layer** (`src/app/github/`): Fetch PRs, diffs, handle tokens. Only GitHub logic here.
- **Parsing layer** (`src/app/diff/`): Convert raw diff into structured `FileDiff` objects. No LLM calls, no GitHub here.
- **Agent layer** (`src/app/agents/`): Core reasoning. Agents receive structured data, return structured `ReviewComment` objects.
- **API layer** (`src/app/api/`): HTTP endpoints, Pydantic validation, error handling. No business logic.
- **Logging & config** (`src/app/core/`): Settings, logging setup, observability hooks.

**Example of bad SoC**:
```python
def review_pr(pr_id, github_token, model_key):
    # Fetch from GitHub
    pr = github_api_call(...)
    diff = extract_diff(...)
    # Parse
    files = parse_diff(diff)
    # Run agents
    comments = run_agents(files, model_key)
    # Format and return
    return format_comments(comments)
```

**Example of good SoC**:
```python
# GitHub handler
pr = github_client.get_pr(pr_id)
diff = github_client.get_diff(pr_id)

# Diff parser (isolated)
file_diffs = diff_parser.parse(diff)

# Agent orchestrator (isolated)
review_comments = agent_manager.review(file_diffs)

# API response formatting
return ReviewResponse(comments=review_comments)
```

---

### 3. KISS (Keep It Simple, Stupid)

**Rule**: Solve the problem with the simplest approach that works. Avoid over-engineering.

- ❌ Don't use complex state machines or event buses for a linear workflow (fetch → parse → review → return).
- ✅ Use simple async functions with clear input/output.
- ❌ Don't design agents with inter-agent communication patterns.
- ✅ Use a manager agent that calls specialist agents sequentially.
- ❌ Don't build a distributed tracing system from scratch.
- ✅ Use request IDs in logs and link them in Prometheus metrics.

**For this project**:
- Agents are simple functions/classes: `async def logic_agent(chunk: CodeChunk) -> ReviewComment`.
- Agent manager is a simple orchestrator: loop through agents, collect results, deduplicate.
- No complex queues, caching, or retry logic (unless absolutely needed).

---

### 4. DRY (Don't Repeat Yourself)

**Rule**: Single source of truth for logic, config, and data models. Avoid copy-paste.

- ❌ Define PR metadata in multiple places (API request model, internal model, agent input model).
- ✅ Define once in a central Pydantic model; reuse everywhere.
- ❌ Repeat logging patterns across functions.
- ✅ Create a logger module with structured logging helpers; import and use consistently.
- ❌ Hardcode model names, tokens, or API endpoints in functions.
- ✅ Load from `Settings` and pass as dependencies.

**Example of bad DRY**:
```python
@app.post("/review/pr")
def review_pr(pr_id: int, repo: str):
    # ... fetch and review ...
    logger.info(f"Reviewed PR {pr_id}")
    return {"status": "done"}

@app.get("/pr/{pr_id}")
def get_pr(pr_id: int):
    # ... fetch PR ...
    logger.info(f"Fetched PR {pr_id}")
    return pr_data
```

**Example of good DRY**:
```python
def log_pr_event(pr_id: int, event: str, **extra):
    logger.info("PR event", extra={**extra, "pr_id": pr_id, "event": event})

@app.post("/review/pr")
def review_pr(pr_id: int, repo: str):
    log_pr_event(pr_id, "review_started")
    return {"status": "done"}

@app.get("/pr/{pr_id}")
def get_pr(pr_id: int):
    log_pr_event(pr_id, "fetch")
    return pr_data
```

---

### 5. Self-Documenting Code

**Rule**: Code should be clear and intention-evident without heavy comments. Names, types, and structure should explain intent.

#### Naming

- ✅ `fetch_pr_diff()` is clear; ❌ `get_data()` is not.
- ✅ `agent_review_comments` is clear; ❌ `result` is not.
- ✅ `FileDiff`, `ReviewComment`, `CodeChunk` — domain names are good.
- ✅ `LOGIC_ANALYSIS_THRESHOLD` for a constant; ❌ `THRESHOLD` is vague.

#### Type Hints

- ✅ Use full Pydantic models: `def parse_diff(raw_diff: str) -> list[FileDiff]`.
- ✅ Use enums for options: `class ReviewLevel(str, Enum): CRITICAL = "critical"`.
- ❌ Don't use `Any` unless truly necessary.
- ❌ Don't return bare dicts; use Pydantic models.

#### Structure & Readability

- ✅ One clear responsibility per function (SoC helps here).
- ✅ Keep functions short (<30 lines ideally).
- ✅ Use early returns to reduce nesting:
  ```python
  if not file_has_changed:
      return []
  
  # Main logic here...
  ```
- ✅ Use docstrings for **why**, not **what** (types already show what).
  ```python
  async def logic_agent(chunk: CodeChunk) -> ReviewComment:
      """Analyze code for logical flaws.
      
      Uses multi-step reasoning to catch subtle bugs in control flow.
      """
  ```

#### Constants & Config

- ✅ Extract magic numbers:
  ```python
  MAX_CHUNK_SIZE = 1000
  REASONING_DEPTH = 3
  
  def process_chunk(chunk):
      if len(chunk) > MAX_CHUNK_SIZE:
          split_chunk(chunk)
  ```
- ✅ Use enums for state/levels:
  ```python
  class Severity(str, Enum):
      CRITICAL = "critical"
      WARNING = "warning"
      INFO = "info"
  ```

---

## Patterns & Practices for This Project

### Pydantic Models (Core Data)

```python
# models.py - Single source of truth

from pydantic import BaseModel, Field
from typing import Optional

class CodeChunk(BaseModel):
    """A section of code that changed."""
    file_path: str
    language: Optional[str] = None
    original_lines: list[str]
    new_lines: list[str]
    start_line: int

class ReviewComment(BaseModel):
    """A single code review comment."""
    file_path: str
    line_number: int
    severity: Severity = Severity.WARNING
    category: str  # "logic", "readability", "performance", "security"
    message: str
    suggestion: Optional[str] = None

class ReviewRequest(BaseModel):
    """API request for PR review."""
    pr_id: Optional[int] = None
    repo: Optional[str] = None
    diff: Optional[str] = None  # Manual diff input

class ReviewResponse(BaseModel):
    """API response with review."""
    pr_id: Optional[int] = None
    comments: list[ReviewComment]
    total_issues: int = Field(default_factory=lambda: len(comments))
```

### Agents (Clean & Simple)

```python
# agents/base.py
from abc import ABC, abstractmethod

class ReviewAgent(ABC):
    """Base class for specialized review agents."""
    
    @abstractmethod
    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Return review comments for a code chunk."""
        pass

# agents/logic.py
class LogicAgent(ReviewAgent):
    """Detects logical flaws in code."""
    
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def analyze(self, chunk: CodeChunk) -> list[ReviewComment]:
        """Analyze for control flow, edge case, and logic issues."""
        prompt = self._build_prompt(chunk)
        response = await self.llm.reason(prompt)
        return self._parse_response(response)
    
    def _build_prompt(self, chunk: CodeChunk) -> str:
        """Build prompt for LLM."""
        return f"""Analyze this code for logical errors:
{chunk.new_code}"""
    
    def _parse_response(self, response: str) -> list[ReviewComment]:
        """Parse LLM response into structured comments."""
        # Parse and return
        pass

# agents/manager.py
class AgentManager:
    """Orchestrates multiple agents."""
    
    def __init__(self, agents: dict[str, ReviewAgent]):
        self.agents = agents
    
    async def review(self, chunks: list[CodeChunk]) -> list[ReviewComment]:
        """Run all agents and consolidate results."""
        all_comments = []
        for chunk in chunks:
            for agent_name, agent in self.agents.items():
                comments = await agent.analyze(chunk)
                all_comments.extend(comments)
        
        return self._deduplicate_and_rank(all_comments)
    
    def _deduplicate_and_rank(self, comments: list[ReviewComment]) -> list[ReviewComment]:
        """Remove duplicates, rank by severity."""
        # Dedupe logic
        pass
```

### API Layer (Thin & Clean)

```python
# api/review.py
from fastapi import APIRouter, Depends
from src.app.models import ReviewRequest, ReviewResponse
from src.app.agents.manager import AgentManager

router = APIRouter(prefix="/review", tags=["review"])

@router.post("/pr")
async def review_pr(
    request: ReviewRequest,
    agent_manager: AgentManager = Depends(get_agent_manager)
) -> ReviewResponse:
    """Review a PR via GitHub API or manual diff."""
    
    # Validate request
    if not request.pr_id and not request.diff:
        raise ValueError("Provide either pr_id or diff")
    
    # Fetch and parse
    if request.pr_id:
        diff = await github_client.get_diff(request.pr_id, request.repo)
    else:
        diff = request.diff
    
    chunks = diff_parser.parse(diff)
    comments = await agent_manager.review(chunks)
    
    return ReviewResponse(pr_id=request.pr_id, comments=comments)
```

### Logging (Structured & Reusable)

```python
# core/logging_config.py
import json
from logging import LogRecord

class StructuredFormatter(logging.Formatter):
    """Outputs JSON logs with context."""
    
    def format(self, record: LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "pr_id": getattr(record, "pr_id", None),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def get_logger(name: str):
    """Get a logger with structured output."""
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger

# Usage anywhere
logger = get_logger(__name__)
logger.info("Review started", extra={"pr_id": 123})
```

---

## Checklist Before Committing

- [ ] Each function has one clear purpose.
- [ ] No magic numbers; use named constants.
- [ ] Type hints on all functions and class methods.
- [ ] Pydantic models for all structured data (no bare dicts).
- [ ] Logging is structured (JSON with consistent fields).
- [ ] No hardcoded secrets, tokens, or endpoints.
- [ ] Logs and config come from environment variables via `Settings`.
- [ ] Function names are clear and verb-based (`fetch_pr`, `parse_diff`, `analyze_chunk`).
- [ ] Dead code and unused imports are removed (DRY).
- [ ] No copy-paste logic; extracted to utilities or base classes.
- [ ] Docstrings explain **why**, not **what** (types show what).

