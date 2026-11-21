# Phase 4 — Gap Analyzer: Extraction, Profiles, Evidence Verification

**Read first:** `00_COMMON_RULES.md`
**Prerequisite:** Phase 3 approved (Phase 2 releasable)
**Goal:** Reliably extract a structured, **evidence-verified** profile for each individual paper. No cross-paper comparison yet.

## 1. Section detection (`services/research/sections.py`)
Headings and heuristics first; GROBID (optional separate service) if available; LLM classification only for uncertain sections. Preserve page references.

## 2. Ollama client (`services/ollama.py`)
- Model configurable (default Qwen2.5 7B Instruct Q4); Ollama URL configurable.
- **Set `num_ctx` explicitly** (e.g. 8192).
- Use **structured output**: pass a JSON schema in the `format` field.
- Handle Ollama down, model missing, timeouts, and out-of-memory with clear errors.
- One LLM request at a time.

## 3. Per-paper extraction (`profile.py`)
1. Page-level extraction (shared service).
2. Chunk by section with page references.
3. Send **only relevant sections** to the LLM: abstract, end of intro, method, results, limitations/discussion, conclusion/future work.
4. Validate output with Pydantic. **One controlled repair attempt**, otherwise mark the profile as failed. Never silently accept malformed output.
5. Verify evidence (section 4) before saving.

Profile shape:
```json
{
  "paper_id": "uuid", "title": "...", "year": 2024,
  "research_problem": {"value": "...", "evidence": [{"page": 1, "quote": "..."}]},
  "objectives": [], "methodology": [], "algorithms": [], "datasets": [],
  "evaluation_metrics": [], "findings": [],
  "explicit_limitations": [], "author_future_work": [],
  "missing_information": []
}
```
Every list item has `value` plus `evidence`. Absent fields are empty arrays or "Not mentioned."

## 4. Evidence verification (`evidence.py`, deterministic code)
- Normalize both the quote and the page text (hyphenation, ligatures, whitespace), then confirm the quote exists via exact or **high-threshold fuzzy** matching (RapidFuzz).
- Confirm the page belongs to that document.
- Reject or flag unsupported claims; flagged items are shown as "unverified" or dropped, per config.

## 5. Prompts (`backend/app/prompts/`, versioned)
Rules to embed: extract only from the supplied excerpts; quote briefly and give pages; do not infer a limitation from silence; do not invent datasets, results, citations, quotes, or pages; separate author-stated limitations from your own observations; return JSON only. Store `model_name` and `prompt_version` with every profile.

## 6. Storage
Entity `research_paper_profiles` (with `model_name`, `prompt_version`, status, verification results). Jobs table reused from Phase 2. Every lookup checks owner/workspace.

## 7. Evaluation
Hand-annotate **5-10 open-access papers on one narrow topic**: limitations, future work, methods, datasets, with pages. Measure extraction correctness, quote correctness, page correctness, unsupported-claim rate. Record misses honestly.

Targets:
- Verified-quote rate >= 95% (anything unverified is flagged or removed)
- 100% of outputs pass schema validation or are marked failed

## Tests
Section detection on fixtures; schema validation and repair path; evidence verification (exact, fuzzy, hyphenated, wrong page, fabricated quote); Ollama-down/model-missing handling with a mocked client; no live LLM required in CI.

## Do not
- Compare papers or generate gaps yet
- Let the LLM compute counts or decide what is "verified"
- Save a profile that failed validation as if it succeeded

## Acceptance checklist
- [ ] Structured output validated; failures marked, not hidden
- [ ] Fabricated quotes are caught by tests
- [ ] `num_ctx` set and documented
- [ ] Evaluation recorded with real numbers
- [ ] Model license verified and logged
- [ ] Tests actually run

## Stop gate
Summarize, update docs, **wait for approval before Phase 5.**
