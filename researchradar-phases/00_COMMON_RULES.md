# ResearchRadar — Common Rules (read before EVERY phase)

**Project:** ResearchRadar
**Modules:** (1) Plagiarism / text-similarity checker, (2) Research gap and limitation analyzer
**Goal:** Build both as maintainable, explainable, locally runnable features using **only open-source software, open-weight models, and openly licensed data**, integrated into the existing ResearchRadar app. Do not break existing functionality.

## How to use these files
1. Give your coding agent this file **plus the one phase file** you are working on (`PHASE_0` ... `PHASE_6`).
2. Do phases **in order**. Each phase ends with a stop gate: the agent summarizes, updates the docs, and waits for your approval.
3. Ship Phase 2 (plagiarism MVP) as a usable release before starting Phase 4.

| File | Deliverable |
|---|---|
| PHASE_0_SETUP_AND_INSPECTION.md | Inspect repo, plan, LICENSE, CI skeleton |
| PHASE_1_INGESTION.md | Safe upload, page-aware extraction, normalization, chunking |
| PHASE_2_PLAGIARISM_MVP.md | Winnowing + fuzzy, scoring, report, API, minimal UI, evaluation |
| PHASE_3_SEMANTIC_AND_OPEN_ACCESS.md | Embeddings, vector store, open-access connectors |
| PHASE_4_GAP_EXTRACTION.md | Sections, Ollama structured extraction, profiles, evidence verification |
| PHASE_5_GAP_COMPARISON_AND_UI.md | Cross-paper comparison, gap generation, report, UI |
| PHASE_6_INTEGRATION_AND_RELEASE.md | Integration, export, deletion, docs, demo, final evaluation |

## 1. Product summary

### A. Plagiarism and Similarity Checker
A user uploads a PDF/TXT (or pastes text). The system extracts and normalizes the text, compares it against documents the user is authorized to search, and produces a report with: lexical similarity percentage (labelled as an indicator, not a verdict), matching passages with page numbers, matching source documents, match type (**exact**, **near-exact**, later **possible paraphrase**), highlighted/side-by-side view, optional exclusion of references and quotes, and a downloadable report stating the corpus searched and formula used.

**Scope limitation (must appear in UI and report):** an open-source checker has no access to the whole internet, paywalled journals, or Turnitin's private corpus. It compares against (1) documents the current user uploaded and (2) later, open-access full text fetched through permitted APIs. Never claim to check "the internet" or "all publications." A match is not proof of plagiarism.

### B. Research Gap and Limitation Analyzer
A user selects 2-5 papers (configurable up to 10). The system extracts per paper: problem, objectives, methodology, algorithms, datasets, metrics, findings, **explicit limitations**, **author-stated future work**, then compares papers. Outputs are **"potential gaps in the analyzed collection,"** never proven gaps in all literature. Each item is labelled **Author-reported**, **System-observed pattern**, or **AI-suggested direction**. The model must not invent citations, quotes, page numbers, datasets, or claims. Missing evidence -> "Not mentioned" / "Insufficient evidence."

## 2. Non-goals (do not build)
- A Turnitin clone or claim of exhaustive plagiarism detection
- Crawling the open web or scraping paywalled / ToS-restricted sites
- Automatic accusations or "plagiarism confirmed" labels
- OCR in the MVP (scanned PDFs get a clear "not supported yet" message)
- Multi-user team corpora, DOCX, multilingual support in the MVP
- Cloud / paid APIs (everything local by default)
- Proving a global research gap

## 3. Open-source policy (applies to every phase)
1. **Repository license:** one permissive license (MIT or Apache-2.0) in `LICENSE`. Also `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
2. **No copyleft surprises:** no AGPL/GPL dependencies. **Do not use PyMuPDF** (AGPL). Use `pypdf`, `pdfminer.six`, or `pypdfium2`.
3. **Models must be open-weight with a permissive license** (Apache-2.0, MIT). Custom or research-only licenses (some Qwen sizes, Llama, Gemma) are not the default. Read the official model card; record in `docs/OPEN_SOURCE_LICENSES.md`.
4. **Data must be openly licensed.** No copyrighted PDFs in the repo. Test papers come from arXiv, PubMed Central open-access subset, or other CC-BY/CC0 sources. Record each file's source and license in `tests/fixtures/DATA_LICENSES.md`.
5. **CI license check:** GitHub Actions run tests plus `pip-licenses` (backend) and `license-checker` (frontend), failing on disallowed licenses.
6. **Reproducible setup:** `docker-compose.yml` plus a no-Docker path in the README.
7. **Privacy by default:** all processing local; no third-party uploads; no telemetry.

## 4. Recommended stack
Licenses are expected values. **Verify each against the official repo/model card when adopting** and record versions.

| Layer | Choice | Expected license |
|---|---|---|
| Language / API | Python 3.11+, FastAPI, Pydantic, pydantic-settings | MIT |
| PDF text | `pypdf` (default); `pdfminer.six` or `pypdfium2` alternatives | BSD / MIT / Apache-BSD |
| Scientific PDF parsing (optional) | GROBID (separate service) | Apache-2.0 |
| Lexical matching | RapidFuzz, scikit-learn, own winnowing implementation | MIT / BSD |
| Embeddings | Sentence Transformers + `all-MiniLM-L6-v2`, or `bge-small-en-v1.5` | Apache-2.0 / MIT |
| Vector store | ChromaDB (or `sqlite-vec` / pgvector) | Apache-2.0 / MIT |
| LLM runtime | Ollama | MIT |
| LLM (default) | **Qwen2.5 7B Instruct, Q4** (~5 GB). Alternatives: Qwen3 4B/8B, Mistral 7B, Phi-4-mini | Apache-2.0 / MIT (verify) |
| Database | Existing DB; otherwise SQLite for MVP | public domain |
| Frontend | Existing React + Tailwind | MIT |
| Testing | pytest, httpx, existing frontend tooling | MIT |

Qwen2.5 **3B** is, to the best of my knowledge, not Apache-2.0. Do not use it as the default.

## 5. Hardware-aware requirements
Target: Windows PC, RTX 3080 10 GB VRAM, 16 GB RAM.
- One LLM request at a time; sequential or small-batch PDF processing.
- Quantized model, moderate context. **Set Ollama `num_ctx` explicitly** (e.g. 8192); the default is small and silently truncates.
- Do not load multiple embedding/LLM models at once. CPU fallback if CUDA is unavailable.
- Configurable: model name, Ollama URL, `num_ctx`, chunk size, batch size, file-size and page-count limits.
- README notes installing the CUDA build of PyTorch on Windows.

## 6. Architecture principles
```text
React + Tailwind
      |
FastAPI (thin routes, Pydantic schemas)
      |
  +---+--------------------------+
  |                              |
Plagiarism services        Research-analysis services
  |                              |
  +--- shared: extraction, normalization, chunking, storage ---+
                                 |
        Relational DB (metadata, jobs, reports) + vector store (chunks)
```
- Routes are thin; logic lives in services. Vector-store access sits behind one abstraction.
- Keep page number and character offsets through the whole pipeline.
- **Never use an LLM as the plagiarism matcher. Never use an LLM guess as evidence of a gap.** The LLM extracts and explains; deterministic code counts, matches, and verifies.
- Counts and frequencies are computed in Python, not by the LLM.

### Repository layout
First inspect the existing repo and follow its conventions. Do not create a second backend/frontend. Minimal layout if starting fresh; **create files only when they have a real purpose**:
```text
backend/app/
  core/            config, errors, security (file validation)
  api/v1/          documents, plagiarism, research_analysis, reports
  schemas/         Pydantic contracts
  models/ + db/    ORM models, session, repositories
  services/
    extraction.py, normalization.py, chunking.py, embeddings.py, vector_store.py, ollama.py
    plagiarism/    winnowing.py, fuzzy.py, semantic.py, scoring.py, report.py
    research/      sections.py, profile.py, comparator.py, gaps.py, evidence.py, report.py
  prompts/         versioned prompt text files
backend/tests/     unit/, integration/, fixtures/ (open-licensed only)
frontend/src/features/plagiarism/ and research-analysis/
docs/
```

## 7. Security and reliability (every phase must respect)
- Validate extension, MIME, size, and real content; random storage names; no path traversal; never execute uploads.
- Authorization on every document/report lookup (owner/workspace); rate limits if auth exists.
- No full document text or prompts in logs; no stack traces or filesystem paths in API responses.
- Keep `.env`, uploads, reports, databases, and vector files out of Git.
- Clear messages for scanned/empty/corrupt/encrypted PDFs, Ollama down or model missing, embedding download failure, vector-store errors.
- Jobs are safely retryable. Dedupe by file hash. **Never show a report as complete if a stage failed.**
- Respect API terms, rate limits, and licenses.

## 8. UI rules
Reuse the existing design system. Loading/empty/success/error states. Accessible labels and keyboard navigation. Neutral labels only: "Exact text match," "Near-exact match," "Possible paraphrase," "Needs review." **No red "plagiarism confirmed" wording.** Visually distinguish author-reported, system-observed, and AI-suggested items.

## 9. Honesty and documentation rules
- Never mark a feature complete if it is only scaffolded. Never claim a test passed unless you ran it. Do not fabricate metrics. If a command can't be run, say why.
- At the end of **every** phase update:
  - `docs/IMPLEMENTATION_LOG.md`: date, phase, files created/modified, what was done, commands actually run, test results actually observed, issues, next steps.
  - `docs/PROJECT_STATUS.md`: completed, in progress, not started, blockers, latest test status, exact next task, setup notes.
  - Other docs touched by the phase (`README.md`, `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, `docs/OPEN_SOURCE_LICENSES.md`, `docs/TESTING_AND_EVALUATION.md`, `docs/SECURITY_AND_PRIVACY.md`).
- Work only on the current phase. At the end: summarize, then **stop and wait for approval**.
