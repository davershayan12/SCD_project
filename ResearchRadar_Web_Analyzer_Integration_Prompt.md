# ResearchRadar — Prompt: Adapt "web-plagiarism-analyzer" into ResearchRadar

Paste everything below the line into your coding agent with the ResearchRadar repo open. If you already saved the earlier files (`00_COMMON_RULES.md`, the phase files, `ResearchRadar_Online_Plagiarism_Prompt.md`) into `docs/`, tell the agent to read them too; this prompt is written to work with them.

---

You are a senior Python engineer and React developer. In my existing **ResearchRadar** project (FastAPI + React + Tailwind, local-first, open source), add a **web plagiarism-check capability** by studying and adapting ideas from this reference project, **not by copying it wholesale**:

**Reference repo (read-only):** https://github.com/jiya-19/web-plagiarism-analyzer (MIT license, Flask prototype)

Clone it to a temporary folder **outside** the ResearchRadar repo, or read it online. Never vendor the whole repo into mine.

## 1. What the reference project does
Flask app. Accepts PDF/DOCX/TXT, extracts text, splits into sentences, takes the first 12 sentences, builds a keyword query for each, searches the web, downloads the result pages, splits each page into sentences, scores each student sentence against each page sentence with TF-IDF cosine (70%) plus word overlap (30%), keeps the best match per sentence, averages those scores into an "overall" percentage, and shows Low/Medium/High risk in a dashboard with flagged sentences, closest source sentence, ranked sources, and a status message explaining what happened.

## 2. Known problems to confirm yourself (I only read `README.md` and `checker.py`)
Read **all** files, including `app.py`, `templates/`, and `static/`, and verify or correct each point. Record the result in `docs/REFERENCE_REPO_AUDIT.md`.
1. **Scrapes search-engine HTML** (the code requests `bing.com/search` and parses result markup, while the README says Google). This is fragile and likely against the engine's terms. It also sends a spoofed browser User-Agent. **Do not reproduce this.**
2. **Weak queries:** the query is the first 16 non-stopword keywords wrapped in quotes. A quoted bag of keywords rarely appears verbatim on any page, so exact-phrase search will mostly return nothing.
3. **Only the first 12 sentences** of the document are ever checked, so most of a paper is never examined.
4. **Overall score is wrong for our purpose:** it averages the best pairwise score of matched sentences only. It is not "share of the document that matches," ignores unmatched text, and can't merge overlaps. Our spec forbids averaging pairwise scores into a plagiarism percentage.
5. **TF-IDF is fitted on just two texts** (one student sentence, one candidate sentence) and re-fitted for every candidate sentence. IDF is meaningless with two documents, and it is very slow on long pages.
6. **Word overlap uses sets of 3+ letter words**, so common words inflate scores.
7. **Fetching is unsafe:** arbitrary URLs from search results are fetched with no private-IP/SSRF protection, no response-size cap (the page is fully downloaded before being truncated), no `robots.txt` check, no HTTP status check.
8. **One result per domain** is kept, which can drop the actual source.
9. Sentence splitter is a regex and breaks on "et al.", "e.g.", decimals.
10. `PyPDF2` is the old package name; use `pypdf`.
11. Thresholds (20% flag, 35/65% risk bands) are arbitrary prototype values.
12. No page numbers, no character offsets, no highlighting, no tests, no authorization, uploaded files stored in `uploads/`.

## 3. What to reuse (as ideas) and what to replace

| Reference idea | Decision |
|---|---|
| Supported file types (TXT, PDF, DOCX) | Keep TXT/PDF as in my spec. Add DOCX as an **optional** extra using `python-docx` (MIT); warn that DOCX has no real page numbers |
| Sentence-level flagged list with the closest source sentence and link | **Keep** as UX, but compute it from winnowing + fuzzy matches with page/offset |
| Ranked source list with number of matches | **Keep** (group by source, show provenance) |
| Diagnostic status messages (no sentences / no results / pages not retrievable / N pages analyzed) | **Keep and expand**: per-stage counts and per-source status (ok / blocked by robots / timeout / not HTML / too large / rate-limited) |
| Demo guidance (short doc with copied sentences) | Reuse for `docs/USER_GUIDE.md` and a demo fixture made from **open-licensed** text |
| Bing/Google HTML scraping | **Replace** with the connector design in section 4 |
| TF-IDF + overlap combined score | **Replace** with winnowing + RapidFuzz for lexical matches; TF-IDF/embeddings only for a separate "possible paraphrase" list, fitted on the whole candidate corpus, never in the lexical percentage |
| Mean of best scores | **Replace** with merged-span coverage: `covered_eligible_tokens / eligible_tokens x 100` |
| Low/Medium/High | Optional "review priority" label from the coverage percent with **configurable, visible thresholds**, labelled as a heuristic, never as a verdict |
| Flask, Jinja templates, plain CSS | **Drop.** Implement as FastAPI routes + React components in my existing design system |
| Per-sentence keyword query | **Replace** with distinctive-passage selection (section 4.2) |

## 4. Required design in ResearchRadar

### 4.1 Source connectors (one interface, each switchable in config)
1. **Local documents** (my own uploads): always available, works offline.
2. **Open-access scholarly APIs** (default online mode): OpenAlex, arXiv, CORE, Semantic Scholar, Crossref, Unpaywall. **Verify each API's current capabilities, auth requirements, rate limits, and terms yourself** and document them. Some are metadata-only or DOI-based.
3. **User-supplied URL list**: I paste URLs and the tool compares my document against those pages only. This is the deterministic, legitimate way to check specific web pages.
4. **Optional general web search provider**, **off by default**, only through an **official search API with a key I supply** in `.env`. Research which general search APIs currently exist and permit this use, and propose options in your plan. **No scraping of search-result HTML, no spoofed User-Agent, no CAPTCHA or paywall bypass.** If no suitable provider exists, leave the interface and say so.

### 4.2 Query selection (replaces first-12-sentences)
- Consider the **whole** document after exclusions (references, quoted text, headers/footers, boilerplate).
- Rank passages deterministically: rarity of terms, length, not a definition/common phrase, spread across the document so coverage isn't only the introduction.
- Query with **contiguous phrases from the real text (about 8-12 words)**, not stopword-stripped keyword bags; use a keyword fallback for APIs that need it.
- Number of queries is configurable (e.g. 15-30) with per-API rate limits.

### 4.3 Safe fetcher (for URL list and any fetched page)
- Only `http`/`https`; resolve DNS and **block private, loopback, link-local, and metadata IP ranges** (also after redirects); limited redirects.
- Honest User-Agent that names the project and contact email; **respect `robots.txt`**.
- Timeouts, retry with backoff, **streamed download with a hard size cap**, status code checks, content-type allowlist (HTML, plain text, PDF), no JavaScript execution.
- Extract main text (strip nav/footer/scripts) and keep it **transient**: do not persist full text of third-party pages unless the license clearly allows it. Persist only fingerprints, the source URL/title/license/fetch date, and short matched excerpts needed for the report.

### 4.4 Matching and scoring
Use the engine from my spec: word k-gram shingles, winnowing, RapidFuzz verification, span merging so nothing is double-counted across sources, page numbers and offsets on my side, minimum token length and stop-phrase list. Report the formula, parameters, exclusions, corpus scope, and largest single-source share. Keep semantic "possible paraphrase" candidates separate.

### 4.5 Privacy
Online mode is **off by default** and needs an explicit per-check opt-in. Send only the short selected passages, never the whole document, and show me exactly what was sent and to which service. Provide full offline mode. Never log full document text. Warn clearly that confidential documents should not be checked online.

### 4.6 Report and UI
Summary with the formula; match list with highlights and side-by-side view; **sources searched** with status; **sources not checked** with the reason; provenance for every source; persistent disclaimer: *"Similarity is not a determination of plagiarism. This report covers only the listed sources."* Neutral labels only. Reuse the reference UX ideas: flagged-sentence view, closest source text, ranked sources, plain-language status explaining why nothing was found.

## 5. Licensing and credit
- The reference repo is MIT. If you copy or closely adapt any code, keep its copyright notice and add `THIRD_PARTY_NOTICES.md` crediting **jiya-19/web-plagiarism-analyzer** with the license text. Prefer re-implementing the ideas.
- Only permissive dependencies (no AGPL/GPL, no PyMuPDF). Record every new dependency and its license in `docs/OPEN_SOURCE_LICENSES.md`.
- No copyrighted pages or PDFs in the repo; fixtures must be open-licensed and logged in `tests/fixtures/DATA_LICENSES.md`.

## 6. Rules that always apply
Inspect my repo first and reuse what exists; don't replace frameworks or break features; the LLM is never the matcher; never claim to search "the internet" or declare "no plagiarism"; a report is never "completed" if a stage failed; thin routes, Pydantic schemas, type hints, configurable limits, authorization on every lookup, no stack traces or file paths in responses, secrets only in `.env` (provide `.env.example`); never claim a test passed unless you ran it.

## 7. Tests (write and run)
Winnowing, span merging, scoring; exact / light-edit / paraphrase / unrelated fixtures; **connector tests with mocked or recorded responses only (no live calls in CI)**; SSRF tests (private IPs, redirects to private IPs, DNS tricks); size-cap, content-type, timeout, and robots tests; privacy opt-in enforced (nothing leaves the machine without it); permission tests; one regression test showing the reference project's averaging bug is not present. Record real evaluation numbers (targets: exact-copy recall >= 95%, light-edit recall >= 85%, false positives on unrelated text <= 2%).

## 8. Documentation to write
- `docs/REFERENCE_REPO_AUDIT.md`: your verified findings and the reuse/replace decisions.
- `docs/USER_GUIDE.md`: step-by-step for a student (install on Windows, `.env` variables, start backend/frontend, local check, online check with the privacy warning, URL-list check, reading the report, false positives, export/delete, troubleshooting).
- `docs/WHAT_YOU_MUST_DO.md`: manual steps only I can do (API keys, contact email, search-provider key if I choose one, review terms, add test papers, decide whether to enable online mode), marked required/optional with links and exact variable names.
- Update `README.md`, `ARCHITECTURE.md`, `API_REFERENCE.md`, `SECURITY_AND_PRIVACY.md`, `TESTING_AND_EVALUATION.md`, `IMPLEMENTATION_LOG.md`, `PROJECT_STATUS.md`.

## 9. Working method
1. **First response, before changing code:** report your audit of the reference repo (all files), my repo's structure and reusable parts, the connector options you propose and what each can actually do, risks (terms, privacy, SSRF), files you'll create/modify, and a step-by-step plan. **Wait for my approval.**
2. Then implement in order, updating the log after each step: (a) safe fetcher, (b) connectors, (c) query selection, (d) matching + scoring + report, (e) UI, (f) tests and evaluation, (g) docs.
3. At the end tell me what works, what doesn't, known limits, exact run commands, and my manual steps.

Build a real, testable implementation, not a mockup.
