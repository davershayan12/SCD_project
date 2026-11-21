# Phase 2 — Plagiarism MVP (ship this before the gap analyzer)

**Read first:** `00_COMMON_RULES.md`
**Prerequisite:** Phase 1 approved
**Goal:** A working lexical plagiarism/similarity checker against the user's own uploaded documents, with a transparent score, report, API, minimal UI, and a recorded evaluation.

## 1. Lexical engine: winnowing + fuzzy verification
Hashing whole sentences breaks when one word changes, so use fingerprinting (`services/plagiarism/winnowing.py`, `fuzzy.py`):
1. Tokenize to normalized word tokens.
2. Build **word k-gram shingles** (configurable `k`, start near 5).
3. Hash each shingle; select fingerprints with **winnowing** (window `w`; any match of length >= `w+k-1` is guaranteed to be found).
4. Index source fingerprints (inverted index; MinHash/LSH later if the corpus grows).
5. For candidate source/submitted pairs, extend matching regions and **verify with RapidFuzz** to classify:
   - **exact**: normalized text identical
   - **near-exact**: high fuzzy ratio over a minimum length
6. Ignore very short or very common phrases (min token length, stop-phrase list; both configurable).
7. Return source document, pages, offsets, and matching text on both sides.

**The LLM is not used anywhere in this phase.**

## 2. Corpus scope
Compare the submitted document only against **other documents the current user uploaded**. Show the corpus scope in every report. Never imply a wider search.

## 3. Scoring (`scoring.py`, transparent)
- Eligible tokens = tokens of the submitted document after exclusions (references/quotes optional, with caveats shown).
- Mark token spans covered by exact/near-exact matches; **merge overlapping spans so nothing is double-counted**, even across several sources.
- `lexical_similarity_percent = covered_eligible_tokens / eligible_tokens x 100`.
- Also report the largest single-source contribution.
- Show formula, parameters (`k`, `w`, thresholds), exclusions, and corpus searched in every report.
- Never average pairwise similarity scores into a "plagiarism percentage."

## 4. Report contract (adapt field names to the repo)
```json
{
  "report_id": "uuid",
  "document_id": "uuid",
  "status": "completed",
  "corpus_scope": "user documents (12 docs)",
  "parameters": {"k": 5, "w": 4, "min_tokens": 8, "excluded": ["references"]},
  "eligible_word_count": 4200,
  "matched_word_count": 630,
  "lexical_similarity_percent": 15.0,
  "largest_single_source_percent": 9.2,
  "matches": [{
    "match_type": "exact",
    "submitted_page": 2, "submitted_span": [1034, 1210],
    "source_document_id": "uuid", "source_title": "Example", "source_page": 4,
    "similarity": 1.0,
    "submitted_text": "...", "source_text": "..."
  }],
  "disclaimer": "Similarity is not a determination of plagiarism."
}
```

## 5. API and jobs
- `POST /api/v1/plagiarism/check` (document ID or pasted text)
- `GET /api/v1/plagiarism/reports/{id}`
- `GET /api/v1/reports/{id}/download`
- Simple job table (`analysis_jobs`) with polling; use the existing job system if there is one. Entities: `plagiarism_reports`, `plagiarism_matches`.
- A report is never "completed" if any stage failed.

## 6. Minimal UI (`frontend/src/features/plagiarism/`)
Title and short explanation; PDF/TXT dropzone; optional pasted text; **corpus scope display**; reference/quote exclusion options with caveats; run button; progress and errors; summary metrics with formula; match list; side-by-side view with highlights; page links; report download; **persistent disclaimer**. Neutral labels only (see Common Rules section 8). Loading/empty/success/error states.

## 7. Evaluation (record real numbers)
Build a labelled fixture set (open-licensed only): originals, exact copies, lightly edited, paraphrased, unrelated, common academic phrases, properly quoted/referenced passages. Optionally use PAN data (check its license first).

Measure precision, recall, F1, false-positive rate, processing time. **Inspect false positives manually.**

Targets for the MVP (adjust after a first run and record reasons):
- Exact-copy recall >= 95% on controlled fixtures
- Near-exact (light edits) recall >= 85%
- False-positive rate on unrelated text <= 2%
- Overlapping matches never double-counted (unit-tested)
- Report always shows corpus scope, formula, and parameters

## Tests
Unit tests for winnowing guarantees, shingling, span merging, scoring math, exclusions; integration tests for the API; permission tests; evaluation script committed with fixtures.

## Do not
- Use embeddings, vector stores, or LLMs here
- Claim internet-wide checking
- Use accusatory wording ("plagiarized", "confirmed")

## Acceptance checklist
- [ ] Winnowing + fuzzy matching works end to end
- [ ] Overlaps not double-counted (tested)
- [ ] Corpus scope, formula, parameters visible in report and UI
- [ ] Disclaimer persistent
- [ ] Evaluation run and results recorded in `docs/TESTING_AND_EVALUATION.md`, including misses
- [ ] Tests actually run

## Stop gate
This is a releasable MVP. Summarize, update docs, **wait for approval before Phase 3.** (Consider tagging `v0.1.0` here.)
