# Phase 0 — Setup and Inspection

**Read first:** `00_COMMON_RULES.md`
**Prerequisite:** none
**Goal:** Understand the existing ResearchRadar repo, record a plan, and put the open-source foundations in place. **No feature code in this phase.**

## Tasks
1. **Inspect the repo.** Read the README, dependency files, backend, frontend, DB models, auth, existing upload/RAG code, config, and tests.
2. **Report back** (before changing anything):
   - Existing project structure
   - Reusable components
   - Missing components
   - Files you propose to create or modify
   - Risks and assumptions (include any license concerns)
   - Phase 1 plan
3. **Open-source foundations**
   - Add `LICENSE` (MIT or Apache-2.0, as I choose).
   - Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
   - Update `.gitignore`: `.env`, uploads, reports, databases, vector-store files, model caches.
4. **CI skeleton** (GitHub Actions): run backend tests, frontend tests/lint, `pip-licenses` and `license-checker`, failing on AGPL/GPL and unknown licenses. Placeholders are fine if tests don't exist yet, but say so.
5. **Docs skeleton:** create `docs/IMPLEMENTATION_LOG.md`, `docs/PROJECT_STATUS.md`, `docs/OPEN_SOURCE_LICENSES.md` (table: name, version, license, link, verified date), `tests/fixtures/DATA_LICENSES.md`.
6. **Environment check** (document results, do not assume): Python version, CUDA build of PyTorch, Ollama installed, `ollama pull qwen2.5:7b` works, VRAM use on the RTX 3080, GPU vs CPU speed.
7. **Risk spikes** (tiny throwaway scripts, not product code):
   - Extract text from 2-3 sample PDFs with `pypdf`; note hyphenation, column, and ligature problems.
   - Ask Ollama for JSON output on one paper excerpt using the schema `format` field; note reliability.

## Do not
- Add features, endpoints, or UI.
- Add dependencies without checking their license.
- Replace frameworks or delete working code.

## Deliverables
- Written inspection report and plan
- `LICENSE`, community files, `.gitignore` updates, CI skeleton, docs skeleton
- Environment and spike findings recorded in `IMPLEMENTATION_LOG.md`

## Acceptance checklist
- [ ] Repo inspected; existing features untouched
- [ ] License and community files added
- [ ] CI runs (even if with placeholder tests) and license check is wired in
- [ ] Docs skeleton exists
- [ ] Environment and spike results recorded honestly

## Stop gate
Update the log and status files, summarize, and **wait for my approval before Phase 1.**
