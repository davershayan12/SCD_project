# Phase 5 — Gap Analyzer: Cross-Paper Comparison, Gap Generation, UI

**Read first:** `00_COMMON_RULES.md`
**Prerequisite:** Phase 4 approved
**Goal:** Compare 2-5 verified paper profiles and produce cautious, evidence-backed "potential gaps in the analyzed collection," with report and UI.

## 1. Comparison (`comparator.py`)
- Compare problems, method families, datasets, metrics, limitations, future work, findings across selected papers (2-5, configurable up to 10; default max 5).
- Cluster similar limitations/themes with embeddings. **Counts and frequencies come from Python.**
- The LLM only explains and names clusters that code already formed. It never counts and never invents evidence.

## 2. Gap categories (`gaps.py`)
1. **Repeated limitation** (similar limitation in >= 2 papers)
2. **Underrepresented theme** (method/population/dataset/setting appears rarely in this collection)
3. **Methodological contrast**
4. **Conflicting evidence**
5. **Author-proposed future work** (author-reported)
6. **AI-suggested research direction** (AI-suggested)

Each item includes: description, category, **source label** (author-reported / system-observed / AI-suggested), supporting paper IDs, quotes with pages, why it may matter, suggested research question, confidence (low/medium/high) **with a plain-language reason** (not a calibrated probability), and the scope warning **"Based only on the selected papers."**

Wording: **"potential gaps in the analyzed collection,"** never "research gaps in the field."

## 3. Evidence for cross-paper claims
Reuse Phase 4 verification. Every cross-paper claim must show verified evidence from each supporting paper. Unverified items are flagged or dropped per config. If evidence is thin, output "Insufficient evidence."

## 4. API
- `POST /api/v1/research-analysis/jobs` (2-N document IDs)
- `GET /api/v1/research-analysis/jobs/{id}`
- `GET /api/v1/research-analysis/reports/{id}` and `/download`
- Entity `research_reports`. A report is never "completed" if a stage failed; partial results are labelled as partial.

## 5. UI (`frontend/src/features/research-analysis/`)
Paper selector; selected-paper metadata; analyze button; job progress and failure handling; paper profile cards; method/dataset comparison table; explicit limitations; recurring themes; potential gaps with evidence and page links; suggested research questions; export. Visually distinguish author-reported, system-observed, and AI-suggested items. Reuse the existing design system; loading/empty/success/error states; accessible.

## 6. Evaluation
On the Phase 4 annotated set, have a human rate usefulness and check every gap for support.

Targets:
- Unsupported-claim rate in the final report <= 5%
- Every item carries its source label and scope warning
- Verified-quote rate stays >= 95%

## Tests
Counting/clustering unit tests (deterministic), category assignment, label/warning presence, evidence required for each item, partial-failure handling, API permissions, mocked LLM.

## Do not
- Let the LLM decide frequencies or "prove" a gap
- Present AI-suggested directions as author claims
- Drop the scope warning

## Acceptance checklist
- [ ] All six categories implemented with labels
- [ ] Counts from code, not the LLM
- [ ] Each item has verified evidence or is flagged
- [ ] UI distinguishes the three source labels
- [ ] Evaluation recorded honestly
- [ ] Tests actually run

## Stop gate
Summarize, update docs, **wait for approval before Phase 6.**
