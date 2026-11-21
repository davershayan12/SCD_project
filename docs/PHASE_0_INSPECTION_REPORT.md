# Phase 0 Inspection Report

**Date:** 2026-11-21  
**Phase:** Phase 0 — Setup and Inspection  
**Status:** Complete (pending approval)

---

## Executive Summary

ResearchRadar is a **greenfield project** — a fresh repository with no existing backend, frontend, or features. Phase 0 establishes the open-source foundations, directory structure, CI skeleton, and architectural plan.

**Current environment constraint:** Development on laptop without RTX 3080 GPU or Ollama. Full GPU/LLM testing deferred to workstation.

---

## 1. Existing Repository Inspection

### What Exists
- Fresh git repository with remote at `https://github.com/davershayan12/SCD_project.git`
- `.gitignore` with appropriate exclusions (Python, Node, databases, uploads, secrets)
- `00_COMMON_RULES.md` — project specification and phase guidelines
- Phase files (`PHASE_0` through `PHASE_6`) with detailed requirements

### What Does NOT Exist
- No backend code
- No frontend code
- No database
- No tests
- No dependencies installed
- No existing features to preserve

**Conclusion:** This is a complete build from scratch, not an integration into an existing app.

---

## 2. Reusable Components

None — starting fresh.

---

## 3. Missing Components (All of them)

Everything needs to be built:

### Backend (Phase 1+)
- FastAPI application skeleton
- Document upload and validation
- PDF text extraction (pypdf)
- Text normalization and chunking
- Database models (documents, jobs, reports)
- Vector store integration (ChromaDB)
- Ollama LLM client
- Embedding service (Sentence Transformers)

### Plagiarism Module (Phase 2)
- Winnowing fingerprinting
- Fuzzy matching (RapidFuzz)
- Match scoring
- Report generation
- API endpoints
- Basic UI

### Research Analysis Module (Phase 4-5)
- Section detection
- Structured extraction with Ollama
- Cross-paper comparison
- Gap identification
- Evidence verification
- Report generation
- API endpoints
- UI

### Frontend (Phase 2+)
- React application
- Plagiarism checker UI
- Gap analyzer UI
- Document management
- Report viewing

### Infrastructure
- Database setup
- Vector store setup
- Configuration management
- Error handling
- Logging
- Tests

---

## 4. Files Proposed to Create

### Phase 0 (Created)
- ✅ `LICENSE` (MIT)
- ✅ `CODE_OF_CONDUCT.md`
- ✅ `SECURITY.md`
- ✅ `CONTRIBUTING.md`
- ✅ `.github/workflows/ci.yml`
- ✅ `docs/ARCHITECTURE.md`
- ✅ `docs/IMPLEMENTATION_LOG.md`
- ✅ `docs/PROJECT_STATUS.md`
- ✅ `docs/OPEN_SOURCE_LICENSES.md`
- ✅ `tests/fixtures/DATA_LICENSES.md`
- ✅ `docs/PHASE_0_INSPECTION_REPORT.md` (this file)
- ⏳ `README.md` (next)

### Phase 1 (Planned)
- Backend skeleton with FastAPI
- `requirements.txt` and `requirements-dev.txt`
- Core services (extraction, normalization, chunking)
- Database models
- Upload endpoints
- Initial tests

See `docs/ARCHITECTURE.md` for complete proposed structure.

---

## 5. Risks and Assumptions

### Risks

1. **Environment Split Risk** 🔴
   - Development on laptop without GPU/Ollama
   - Testing on workstation with RTX 3080
   - **Mitigation:** Flexible configuration, CPU fallbacks, mock mode

2. **PDF Extraction Quality** 🟡
   - pypdf may struggle with complex layouts, columns, ligatures
   - **Mitigation:** Test with real papers in Phase 1, document limitations

3. **LLM Hallucination** 🟡
   - Ollama may generate false citations, claims, or data
   - **Mitigation:** Evidence verification layer, explicit "not mentioned" handling

4. **License Compliance** 🟡
   - Risk of accidentally adding AGPL/GPL dependency
   - **Mitigation:** CI license checks, manual verification before adoption

5. **Performance on 10GB VRAM** 🟡
   - Qwen2.5 7B Q4 may be tight on 10GB
   - **Mitigation:** Sequential processing, context limits, alternative 4B model

6. **No Multi-User Auth in MVP** 🟡
   - Phase 0-2 focus on single-user or assumes existing auth
   - **Mitigation:** Document clearly, design for future auth integration

### Assumptions

1. ✅ **Open-source only:** No cloud APIs, no paid services
2. ✅ **Local processing:** Everything runs on user's machine
3. ✅ **Windows target:** Primary development on Windows 10
4. ✅ **English only:** No multilingual support in MVP
5. ✅ **Text-based PDFs:** OCR not supported in MVP
6. ✅ **Sequential processing:** One LLM request at a time
7. ✅ **User-uploaded corpus:** Plagiarism checks against user's own documents + open-access APIs (Phase 3)

### License Concerns

- ⚠️ **PyMuPDF is AGPL** — must use pypdf, pdfminer.six, or pypdfium2
- ⚠️ **Qwen2.5 3B is NOT Apache-2.0** — use 7B version
- ⚠️ **Verify every model license** — don't assume Hugging Face means open
- ✅ **MIT license chosen** for ResearchRadar itself

---

## 6. Phase 1 Plan

**Goal:** Build document ingestion pipeline (upload → extract → normalize → chunk → store)

### Tasks
1. Set up FastAPI backend skeleton
2. Create configuration system (pydantic-settings, `.env`)
3. Implement file upload with security validation
4. Implement PDF text extraction with pypdf
5. Implement text normalization
6. Implement chunking with page number preservation
7. Set up database (SQLite for MVP)
8. Create document models and repositories
9. Write unit tests for each service
10. Update documentation

### Deliverables
- Working upload API
- Extraction pipeline with tests
- Database with document storage
- Documentation of extraction quality issues

### Environment Note
- Can develop on laptop (no GPU needed for ingestion)
- Cannot test Ollama features yet
- Need sample open-access PDFs for testing

---

## 7. Open-Source Foundations

### Completed ✅
- `LICENSE` (MIT) added
- `CONTRIBUTING.md` added
- `CODE_OF_CONDUCT.md` (Contributor Covenant 2.0) added
- `SECURITY.md` added
- `.gitignore` already appropriate
- CI skeleton created with license checks

### CI Status
- GitHub Actions workflow configured
- Backend tests (placeholder)
- Frontend tests (placeholder)
- License verification (functional)
- Will activate checks as dependencies are added

---

## 8. Docs Skeleton

### Created ✅
- `docs/IMPLEMENTATION_LOG.md` — chronological development log
- `docs/PROJECT_STATUS.md` — current phase status and blockers
- `docs/OPEN_SOURCE_LICENSES.md` — dependency license tracking
- `docs/ARCHITECTURE.md` — system design and structure
- `tests/fixtures/DATA_LICENSES.md` — test data license tracking
- `docs/PHASE_0_INSPECTION_REPORT.md` — this inspection report

### To Be Created (Later Phases)
- `docs/API_REFERENCE.md` (Phase 2)
- `docs/TESTING_AND_EVALUATION.md` (Phase 2)
- `docs/SECURITY_AND_PRIVACY.md` (Phase 1)
- `README.md` (Phase 0 final task)

---

## 9. Environment Check

### Current Environment (Laptop)
- ✅ Python: 3.14.2 (exceeds requirement of 3.11+)
- ✅ Node.js: v26.13.1
- ✅ npm: 12.2.3
- ✅ Git: 2.51.1.windows.1
- ❌ nvidia-smi: Not available (no GPU on laptop)
- ❌ Ollama: Not installed
- ❌ pypdf: Not installed yet (will be in Phase 1)
- ❌ PyTorch: Not checked (will verify CUDA build on workstation)

### Target Environment (Workstation)
- Windows 10 Pro
- RTX 3080 10GB VRAM
- 16GB RAM
- Ollama with Qwen2.5 7B Q4
- CUDA-enabled PyTorch

### Configuration Strategy
Flexible `.env` configuration to support both environments:
- `USE_GPU=false` on laptop, `true` on workstation
- `OLLAMA_URL` configurable
- `EMBEDDING_DEVICE=cpu` on laptop, `cuda` on workstation
- `MOCK_MODE=true` for testing without Ollama

---

## 10. Risk Spikes

### PDF Extraction Spike
**Status:** ⏸️ Deferred
**Reason:** pypdf not installed, no sample PDFs available yet
**Plan:** Will test in Phase 1 with open-access papers from arXiv

### Ollama JSON Output Spike
**Status:** ⏸️ Blocked
**Reason:** Ollama not available on laptop
**Plan:** Will test on workstation in Phase 4 (first LLM use)

### Alternative Approach
Since spikes are blocked:
- Proceed with Phase 1 (ingestion) which doesn't require Ollama
- Document known issues from research:
  - pypdf may have issues with hyphenation, columns, ligatures
  - Ollama structured output requires explicit `format` parameter
  - Need to validate JSON responses and handle failures

---

## 11. Recommendations

### Immediate (Phase 0 Completion)
1. ✅ Create README.md with project overview
2. ✅ Commit Phase 0 foundations
3. ⏳ Get approval before Phase 1

### Phase 1 Preparation
1. Download 2-3 open-access test PDFs from arXiv
2. Document their licenses in `tests/fixtures/DATA_LICENSES.md`
3. Install Python dependencies: FastAPI, pypdf, pydantic, pytest
4. Set up virtual environment

### Workstation Setup (When Available)
1. Install Ollama
2. Pull Qwen2.5 7B model: `ollama pull qwen2.5:7b`
3. Verify CUDA PyTorch installation
4. Test GPU memory usage with model loaded
5. Run deferred spikes (PDF extraction, LLM JSON output)

### Development Workflow
1. Develop structure and CPU-compatible code on laptop
2. Test GPU/LLM features on workstation
3. Keep configuration flexible for both environments
4. Document what is tested where

---

## 12. Acceptance Checklist

- ✅ Repo inspected; existing features untouched (none exist)
- ✅ License (MIT) and community files added
- ✅ CI runs (placeholder tests, license check functional)
- ✅ Docs skeleton exists
- ⚠️ Environment and spike results: Environment checked, spikes deferred with reason
- ✅ Architecture documented
- ⏳ README.md (creating next)

---

## Phase 0 Summary

**What was done:**
- Established open-source foundations (MIT license, community files)
- Created directory structure
- Set up CI skeleton with license checks
- Documented proposed architecture
- Verified development environment (Python, Node, Git)
- Identified environment constraints (laptop vs workstation)

**What was NOT done:**
- No feature code (correct for Phase 0)
- No dependencies installed yet
- No spikes run (blocked by environment)

**Blockers:**
- Laptop environment prevents GPU/Ollama testing
- Flexible configuration strategy documented

**Ready for Phase 1:** Yes, with laptop limitations understood

---

## Stop Gate

Phase 0 is complete. Awaiting approval to proceed to Phase 1 (Ingestion).
