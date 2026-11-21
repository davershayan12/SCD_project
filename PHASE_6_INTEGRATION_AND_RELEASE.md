# Phase 6 — Integration, Export, Deletion Controls, Docs, Release

**Read first:** `00_COMMON_RULES.md`
**Prerequisite:** Phase 5 approved
**Goal:** Make both modules a coherent part of ResearchRadar, close security and documentation gaps, run the final evaluation, and prepare an open-source release.

## 1. Integration
- Navigation and UX consistent with the rest of ResearchRadar.
- Shared document library works for both modules.
- Consistent error handling, loading states, and wording across modules.

## 2. Export
Downloadable plagiarism and gap reports (formats the app already supports, e.g. PDF/Markdown/JSON). Every export states corpus scope, formula/parameters, model and prompt versions, and the disclaimers.

## 3. Deletion and privacy controls
- User can delete a document and **everything derived from it**: file, pages, chunks, vectors, reports, matches, profiles.
- No full document text or prompts in logs.
- `docs/SECURITY_AND_PRIVACY.md` finalized (local-only processing, no telemetry, what is stored where).

## 4. Security review (do it, don't just claim it)
Upload validation, path traversal, authorization on every document/report/job route, rate limits where auth exists, error responses with no stack traces or paths, `.gitignore` covers `.env`, uploads, reports, databases, vector files. Scan git history for secrets and copyrighted PDFs.

## 5. Open-source release readiness
- `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` present.
- `docs/OPEN_SOURCE_LICENSES.md` complete and verified (name, version, license, link, verified date); CI license check passing with no AGPL/GPL.
- `tests/fixtures/DATA_LICENSES.md` complete.
- `docker-compose.yml` plus a no-Docker README path; CUDA/PyTorch note for Windows.
- **Clean-clone test:** follow only the README in a fresh folder; fix gaps.

## 6. Final evaluation
Re-run both evaluations on final code. Record real numbers against the targets in `docs/TESTING_AND_EVALUATION.md`, including failures and known limitations.

## 7. Documentation
Complete and current: `README.md` (what it does, what it doesn't, limitations, setup), `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`, `docs/OPEN_SOURCE_LICENSES.md`, `docs/TESTING_AND_EVALUATION.md`, `docs/SECURITY_AND_PRIVACY.md`, `docs/IMPLEMENTATION_LOG.md`, `docs/PROJECT_STATUS.md`.

## 8. Demo and release
Short demo script/recording instructions for the README; draft release notes for the first tag stating what works and what doesn't (scope, no OCR, corpus limits).

## Final checklist
- [ ] Repo inspected earlier; existing features preserved
- [ ] No AGPL/GPL dependency; all model and data licenses recorded and verified
- [ ] CI runs tests and license checks and passes
- [ ] PDF/TXT ingestion preserves pages
- [ ] Winnowing + fuzzy works; overlaps not double-counted
- [ ] Semantic candidates kept separate from lexical percentage
- [ ] Corpus scope, formula, parameters visible in reports
- [ ] Per-paper extraction schema-validated with verified quotes
- [ ] Author-reported / system-observed / AI-suggested clearly separated
- [ ] Gaps worded as "potential gaps in the analyzed collection"
- [ ] Authorization, upload validation, deletion implemented and tested
- [ ] Tests added and actually run; evaluation recorded honestly
- [ ] Docs, log, status, and README current; clean-clone test passed

## Stop gate
Summarize final state honestly (what works, what doesn't, known limits). **Wait for my approval before tagging a release.**
