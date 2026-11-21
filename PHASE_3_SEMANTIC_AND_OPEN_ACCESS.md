# Phase 3 — Semantic Candidates and Open-Access Corpus

**Read first:** `00_COMMON_RULES.md`
**Prerequisite:** Phase 2 approved
**Goal:** Add embedding-based "possible paraphrase" candidates and a permitted open-access source corpus, without changing the lexical score.

## 1. Embeddings and vector store
- `services/embeddings.py`: Sentence Transformers with `all-MiniLM-L6-v2` (or `bge-small-en-v1.5`). Model name configurable; GPU if available, CPU fallback; load one model at a time.
- `services/vector_store.py`: ChromaDB (or `sqlite-vec` / pgvector if it reduces infrastructure). **All access sits behind one abstraction.**
- Chunks must fit the model's max sequence length (about 256 tokens for MiniLM); re-chunk if needed.
- Embed chunks on upload (or on demand) in small batches, within the VRAM/RAM limits in Common Rules section 5.
- Handle embedding model download failure and vector-store errors with clear messages.
- Deleting a document must remove its vectors (extend the Phase 1 delete flow and test it).

## 2. Semantic candidates (`services/plagiarism/semantic.py`)
- Retrieve nearest neighbours from the vector store; re-rank by cosine similarity and optional lexical overlap.
- Report as **"Possible paraphrase"** candidates, shown **separately**. They **never enter the lexical percentage.**
- Thresholds are tuned on a labelled validation set; **do not invent a universal threshold.** Record the chosen values and why.
- Report adds `semantic_candidates_count` and a candidates list with the same side-by-side structure.
- UI: separate section, clearly labelled "Needs review."

## 3. Open-access source corpus
Use documented, rate-limited APIs and respect each license/ToS: **OpenAlex** (metadata, CC0), **arXiv** (metadata/API; each paper has its own license), **CORE**, **Unpaywall**, **Semantic Scholar API**.
- Build connectors behind a common interface; each is optional and configurable.
- Cache only what the license allows. **Record provenance per source document:** URL, license, fetch date. Show it in the report.
- If full text isn't available or licensed, compare **metadata only** and say so.
- Respect rate limits; back off on errors; never scrape sites that forbid it.
- Update `corpus_scope` wording in reports and UI to list exactly which sources were searched.

## 4. Evaluation
Extend the Phase 2 fixtures with paraphrased and cross-source cases. Record precision/recall for semantic candidates separately from lexical results. Inspect false positives manually.

## Tests
Embedding/vector abstraction tests (with a fake store), threshold behaviour, connector tests using recorded/mocked responses (no live calls in CI), provenance recorded, deletion removes vectors, semantic results never change the lexical percentage.

## Do not
- Mix semantic scores into the lexical percentage
- Fetch or store full text without a license that allows it
- Claim exhaustive coverage of any source

## Acceptance checklist
- [ ] Semantic candidates separate from lexical score
- [ ] Thresholds tuned on validation data and documented
- [ ] Each connector records provenance and obeys rate limits/ToS
- [ ] Report lists exactly which corpora were searched
- [ ] New dependencies and models recorded in `OPEN_SOURCE_LICENSES.md`
- [ ] Tests actually run; evaluation recorded

## Stop gate
Summarize, update docs, **wait for approval before Phase 4.**
