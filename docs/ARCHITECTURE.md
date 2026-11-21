# ResearchRadar Architecture

**Last Updated:** 2026-11-21  
**Status:** Phase 0 — Planning

---

## Overview

ResearchRadar consists of two main modules:
1. **Plagiarism/Similarity Checker** — lexical and semantic text comparison
2. **Research Gap Analyzer** — structured extraction and cross-paper analysis

Both modules share common infrastructure for document ingestion, processing, and storage.

---

## High-Level Architecture

```text
┌─────────────────────────────────────────┐
│         React + Tailwind UI             │
│  (plagiarism checker + gap analyzer)    │
└─────────────────┬───────────────────────┘
                  │ HTTP
┌─────────────────▼───────────────────────┐
│            FastAPI Backend              │
│         (thin routes, schemas)          │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
┌───────────────┐    ┌──────────────────┐
│  Plagiarism   │    │ Research Analysis│
│   Services    │    │    Services      │
└───────┬───────┘    └────────┬─────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
    ┌──────────────────────────────┐
    │   Shared Services Layer      │
    │ - Document extraction        │
    │ - Text normalization         │
    │ - Chunking                   │
    │ - Embedding generation       │
    │ - Vector store access        │
    │ - Ollama LLM integration     │
    └──────────────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌────────────────┐
│   PostgreSQL  │    │  Vector Store  │
│   or SQLite   │    │   (ChromaDB)   │
│  (metadata,   │    │   (embeddings, │
│   jobs, refs) │    │     chunks)    │
└───────────────┘    └────────────────┘
```

---

## Proposed Directory Structure

```text
SCD_project/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI application entry
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py            # Settings (pydantic-settings)
│   │   │   ├── errors.py            # Custom exceptions
│   │   │   └── security.py          # File validation, auth helpers
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Database setup
│   │   │   ├── session.py           # Session management
│   │   │   └── repositories/        # Data access layer
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py          # Document ORM models
│   │   │   ├── job.py               # Job tracking
│   │   │   └── report.py            # Reports
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── document.py          # Pydantic schemas
│   │   │   ├── plagiarism.py
│   │   │   └── research.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── documents.py     # Upload, list, delete
│   │   │       ├── plagiarism.py    # Plagiarism check endpoints
│   │   │       ├── research.py      # Gap analysis endpoints
│   │   │       └── reports.py       # Report retrieval
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── extraction.py        # PDF → text (pypdf)
│   │   │   ├── normalization.py     # Text cleaning
│   │   │   ├── chunking.py          # Text → chunks
│   │   │   ├── embeddings.py        # Sentence Transformers
│   │   │   ├── vector_store.py      # ChromaDB abstraction
│   │   │   ├── ollama.py            # Ollama client
│   │   │   ├── plagiarism/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── winnowing.py     # Winnowing fingerprints
│   │   │   │   ├── fuzzy.py         # RapidFuzz matching
│   │   │   │   ├── semantic.py      # Embedding-based (Phase 3)
│   │   │   │   ├── scoring.py       # Match scoring
│   │   │   │   └── report.py        # Report generation
│   │   │   └── research/
│   │   │       ├── __init__.py
│   │   │       ├── sections.py      # Section extraction
│   │   │       ├── profile.py       # Per-paper profile extraction
│   │   │       ├── comparator.py    # Cross-paper comparison
│   │   │       ├── gaps.py          # Gap identification
│   │   │       ├── evidence.py      # Evidence verification
│   │   │       └── report.py        # Gap report generation
│   │   └── prompts/
│   │       ├── profile_extraction.txt    # Versioned prompts
│   │       ├── gap_analysis.txt
│   │       └── evidence_check.txt
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── unit/                    # Unit tests
│   │   ├── integration/             # Integration tests
│   │   └── fixtures/                # Test data
│   ├── requirements.txt             # Production dependencies
│   ├── requirements-dev.txt         # Dev dependencies
│   └── pyproject.toml               # Project config (optional)
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── plagiarism/
│   │   │   │   ├── PlagiarismChecker.tsx
│   │   │   │   ├── MatchViewer.tsx
│   │   │   │   └── PlagiarismReport.tsx
│   │   │   └── research-analysis/
│   │   │       ├── PaperSelector.tsx
│   │   │       ├── GapAnalysis.tsx
│   │   │       └── GapReport.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   ├── ARCHITECTURE.md              # This file
│   ├── IMPLEMENTATION_LOG.md        # Development log
│   ├── PROJECT_STATUS.md            # Current status
│   ├── OPEN_SOURCE_LICENSES.md      # License tracking
│   ├── API_REFERENCE.md             # API documentation (Phase 2+)
│   ├── TESTING_AND_EVALUATION.md    # Test strategy (Phase 2+)
│   └── SECURITY_AND_PRIVACY.md      # Security details (Phase 1+)
├── tests/
│   └── fixtures/
│       └── DATA_LICENSES.md         # Test data licenses
├── .gitignore
├── LICENSE
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── README.md                        # To be created
├── 00_COMMON_RULES.md              # Phase guidelines
├── PHASE_0_SETUP_AND_INSPECTION.md
├── PHASE_1_INGESTION.md
├── PHASE_2_PLAGIARISM_MVP.md
├── PHASE_3_SEMANTIC_AND_OPEN_ACCESS.md
├── PHASE_4_GAP_EXTRACTION.md
├── PHASE_5_GAP_COMPARISON_AND_UI.md
└── PHASE_6_INTEGRATION_AND_RELEASE.md
```

---

## Key Design Principles

### 1. Separation of Concerns
- **Routes**: Thin, validation only
- **Services**: Business logic
- **Models**: Data structure
- **Repositories**: Data access

### 2. No LLM as Matcher
- Plagiarism matching uses deterministic algorithms (winnowing, fuzzy matching)
- LLMs used only for extraction and explanation in gap analysis
- Counts and frequencies computed in Python, never by LLM

### 3. Page Number Preservation
- Extract page numbers during PDF parsing
- Maintain page+character offsets through entire pipeline
- Every match and extracted claim must be traceable to source page

### 4. Hardware Awareness
- Single LLM request at a time
- Sequential or small-batch processing
- CPU fallback when CUDA unavailable
- Configurable limits (file size, page count, batch size)

### 5. Security by Default
- File validation (extension, MIME, size, content)
- Random storage names (no path traversal)
- Never execute uploaded files
- Authorization on all document/report access
- No document text or prompts in logs

---

## Data Flow

### Plagiarism Check Flow

```text
1. User uploads PDF/TXT
2. Extraction Service → text + page numbers
3. Normalization Service → cleaned text
4. Chunking Service → chunks with offsets
5. Winnowing + Fuzzy Matcher → exact/near-exact matches
6. (Phase 3) Embedding Service → semantic matches
7. Scoring Service → similarity percentage
8. Report Service → formatted report with matches
9. Return report to user
```

### Gap Analysis Flow

```text
1. User selects 2-5 papers
2. For each paper:
   a. Extraction → text + page numbers
   b. Section Detection → intro, methods, results, discussion, limitations
   c. Ollama LLM → structured profile (problem, methods, findings, limitations)
   d. Evidence Verification → validate extracted claims
3. Comparator → cross-paper analysis
4. Gap Generator → identify patterns and potential gaps
5. Report Generator → formatted report with evidence
6. Return report to user
```

---

## Technology Decisions

### Backend
- **FastAPI**: Modern, async, automatic OpenAPI docs
- **Pydantic**: Type-safe schemas and settings
- **pypdf**: BSD license (NOT PyMuPDF which is AGPL)
- **RapidFuzz**: Fast fuzzy string matching
- **ChromaDB**: Vector store with simple API

### LLM/Embeddings
- **Ollama**: Local LLM runtime (MIT license)
- **Qwen2.5 7B Instruct Q4**: Default LLM (Apache-2.0, ~5GB)
- **all-MiniLM-L6-v2**: Lightweight embeddings (Apache-2.0)

### Database
- **SQLite**: MVP simplicity (or PostgreSQL for production)
- **ChromaDB**: Vector storage for embeddings

### Frontend
- **React + Vite**: Modern, fast development
- **Tailwind CSS**: Utility-first styling
- **TypeScript**: Type safety

---

## Configuration Strategy

All configurable via `.env`:

```bash
# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_NUM_CTX=8192

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu  # or cuda

# Limits
MAX_FILE_SIZE_MB=50
MAX_PAGE_COUNT=500
MAX_CHUNK_SIZE=512
BATCH_SIZE=10

# Storage
UPLOAD_DIR=./storage/uploads
VECTOR_STORE_PATH=./storage/chroma_data
DATABASE_URL=sqlite:///./storage/researchradar.db

# Processing
USE_GPU=false  # Set true on workstation with RTX 3080
MOCK_MODE=false  # Set true for testing without Ollama
```

---

## Next Steps (Phase 1)

1. Create backend skeleton with FastAPI
2. Implement document upload with validation
3. Implement PDF text extraction with pypdf
4. Implement normalization and chunking
5. Add database models for documents
6. Write tests for extraction pipeline
