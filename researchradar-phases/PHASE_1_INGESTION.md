# Phase 1 — Safe Upload and Page-Aware Ingestion

**Read first:** `00_COMMON_RULES.md`
**Prerequisite:** Phase 0 approved
**Goal:** A shared, tested pipeline that safely accepts PDF/TXT files, extracts text page by page, normalizes it, and chunks it. Used by both modules later.

## Tasks
1. **Upload validation.** Accept PDF and TXT. Validate extension, MIME type, size limit, page-count limit, and that the PDF actually opens. Reject corrupt, empty, encrypted, or scanned-with-no-text files with clear messages (no OCR).
2. **Safe storage.** Random server-side filenames; never use the uploaded filename as a path; store outside any web root; compute SHA-256 and **dedupe by hash**.
3. **Extraction (`services/extraction.py`).** Page-by-page text using `pypdf` (default). Keep page numbers and character offsets. Abstract it so `pdfminer.six` / `pypdfium2` / GROBID can be swapped in later.
4. **Normalization (`services/normalization.py`).** Unicode NFKC, de-hyphenate line-break splits, fix ligatures, collapse whitespace, keep meaningful punctuation. Keep a mapping from normalized text back to original page/offset so highlights are accurate later.
5. **Optional exclusions.** Detect references section, headers/footers, boilerplate. Heuristics only for now; **state low confidence when unsure.** Expose as options, never silent.
6. **Chunking (`services/chunking.py`).** Sentence/paragraph chunks with page references. Chunk size is configurable. **For MiniLM-class embedding models, stay within about 256 tokens** because longer text is silently truncated.
7. **Storage and models.** Tables/entities (adapt to the existing schema, don't duplicate): `documents`, `document_pages`, `document_chunks`. Every lookup checks owner/workspace. Store chunks as text only; **no embeddings yet.**
8. **API**
   - `POST /api/v1/documents`
   - `GET /api/v1/documents/{id}`
   - `DELETE /api/v1/documents/{id}` removes pages, chunks, vectors (none yet), and the stored file.
9. **Config.** Max file size, max pages, chunk size, storage path, all settable via environment.

## Tests (write and actually run)
- Valid PDF, valid TXT
- Corrupt, empty, encrypted, scanned/no-text PDF -> correct error messages
- Wrong extension / wrong MIME / oversize
- Duplicate upload deduped by hash
- Page numbers preserved; offset mapping correct after normalization
- Hyphenation and ligature fixes
- Another user cannot read or delete my document
- Delete removes file and rows
- Fixtures only from open-licensed papers, logged in `tests/fixtures/DATA_LICENSES.md`

## Do not
- Implement matching, scoring, embeddings, or LLM calls
- Log full document text
- Return stack traces or filesystem paths in responses

## Deliverables
Upload/extraction/normalization/chunking services, models and migrations, document API, tests, updated docs (`API_REFERENCE.md`, `ARCHITECTURE.md`, `SECURITY_AND_PRIVACY.md`, log, status).

## Acceptance checklist
- [ ] PDF/TXT ingestion preserves pages and offsets
- [ ] All rejection cases give clear messages
- [ ] Authorization and deletion tested
- [ ] No new dependency without a recorded license
- [ ] Tests actually run, results recorded

## Stop gate
Summarize, update docs, **wait for approval before Phase 2.**
