# Project Status

**Project:** ResearchRadar  
**Current Phase:** Phase 0 — Setup and Inspection  
**Last Updated:** 2026-11-21

---

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Setup and Inspection | ✅ Complete | Approved |
| Phase 1: Ingestion | ✅ Complete | 31/31 unit tests passing |
| Phase 2: Plagiarism MVP | ✅ Complete | 54/54 unit tests passing, evaluation run (100% exact recall, 0% FP), React UI created |
| Phase 3: Semantic and Open Access | ⚪ Not Started | |
| Phase 4: Gap Extraction | ⚪ Not Started | |
| Phase 5: Gap Comparison and UI | ⚪ Not Started | |
| Phase 6: Integration and Release | ⚪ Not Started | |

---

## Completed

### Phase 0 ✅
- ✅ Open-source foundations (LICENSE, CODE_OF_CONDUCT, SECURITY, CONTRIBUTING)
- ✅ Directory structure created
- ✅ Environment version check
- ✅ Documentation skeleton complete
- ✅ CI skeleton with license checks
- ✅ Architecture design documented
- ✅ Inspection report with Phase 1 plan
- ✅ README created

### Phase 1 ✅
- ✅ Backend structure with FastAPI
- ✅ File upload with comprehensive validation
- ✅ PDF/TXT extraction (pypdf, page-aware)
- ✅ Text normalization (ligatures, hyphenation, whitespace)
- ✅ Chunking service (sentence-aware, configurable)
- ✅ Database models (Document, DocumentPage, DocumentChunk)
- ✅ RESTful API endpoints (upload, list, get, delete)
- ✅ 31 unit tests PASSING

### Phase 2 ✅
- ✅ Winnowing fingerprinting service (k-grams, mathematical detection guarantee)
- ✅ Fuzzy matching service with RapidFuzz (region extension, exact and near-exact classification)
- ✅ Overlap merging (guarantees zero double-counting across overlapping spans)
- ✅ Transparent scoring service with per-source contributions
- ✅ Report generation service with persistent disclaimers and corpus scope
- ✅ Plagiarism detection orchestration service
- ✅ Database models (PlagiarismReport, PlagiarismMatch)
- ✅ REST API endpoints (POST /check, GET /reports/{id}, GET /reports, DELETE /reports/{id})
- ✅ 23 new unit tests (54/54 total unit tests passing)
- ✅ Evaluation benchmark script with 45 test fixtures (100% exact copy recall, 0% false positive rate)
- ✅ Evaluation documentation (docs/TESTING_AND_EVALUATION.md)
- ✅ Minimal React UI component (frontend/src/features/plagiarism/PlagiarismChecker.tsx)
- ✅ Dedicated feature branch: `feature/phase-2-plagiarism-mvp` pushed to remote

---

## In Progress

None - Phase 2 complete, awaiting approval for Phase 3

---

## Not Started

- Phase 3: Semantic Embeddings and Open-Access Connectors
- Phase 4: Research Gap Extraction (Ollama LLM)
- Phase 5: Gap Comparison and UI
- Phase 6: Integration and Release

---

## Next Immediate Tasks

**Phase 2 Stop Gate:** Awaiting user approval to proceed to Phase 3 (or tag v0.1.0)

**When approved, Phase 3 tasks:**
1. Integrate Sentence Transformers with `all-MiniLM-L6-v2` (or `bge-small-en-v1.5`)
2. Vector store integration (ChromaDB or SQLite-vec)
3. Open-access full text connectors (arXiv / PubMed Central APIs)
4. Add "possible paraphrase" semantic matching layer
5. Evaluate semantic similarity improvements on paraphrase fixtures
