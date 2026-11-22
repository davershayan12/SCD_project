re# Web Plagiarism & Scholarly API Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate a secure web fetcher, scholarly API connectors (OpenAlex, arXiv, Semantic Scholar), user-supplied URL fetching, and distinctive query selection into ResearchRadar's plagiarism detection engine, with privacy opt-in controls and UI updates.

**Architecture:** A robust safe fetcher prevents SSRF and enforces size caps and `robots.txt` compliance. Scholarly connectors and URL lists fetch candidate text passages. Distinctive query extraction selects 8-12 word phrases across the submitted document. Retrieved web/scholarly pages are fed into our existing winnowing + RapidFuzz engine, keeping matches transparent, non-double-counted, and clearly attributed with provenance.

**Tech Stack:** FastAPI, Pydantic, RapidFuzz, pypdf, httpx, React, Tailwind CSS.

**Spec:** `ResearchRadar_Web_Analyzer_Integration_Prompt.md` & `00_COMMON_RULES.md`

## Global Constraints

- **No AGPL/GPL dependencies:** Use permissive licenses (MIT, Apache-2.0, BSD). Do not use PyMuPDF.
- **Privacy by default:** Online checking is off by default and requires explicit user opt-in. Only short query snippets are transmitted, never full confidential documents.
- **SSRF Protection:** Safe fetcher must block private, loopback, link-local, and metadata IP ranges (before and after redirects).
- **No LLM as Matcher:** Matching uses winnowing + RapidFuzz; LLM is never used for plagiarism matching.
- **Corpus Scope Visibility:** Every report explicitly states which sources were checked (Local corpus vs. Scholarly APIs vs. URL list).

## Review Focus

1. **SSRF attacks via crafted URLs/redirects:** Malicious URLs pointing to internal metadata services (e.g., `169.254.169.254`) must be blocked.
2. **Robots.txt compliance & rate limiting:** Fetcher must respect `robots.txt` and apply backoff.
3. **Privacy enforcement:** Online mode must not transmit documents unless explicitly opted in.
4. **Non-double-counting scoring:** Web/scholarly matches must merge overlapping spans correctly.
5. **Clear failure status:** If external APIs or URLs fail to fetch, report status accurately without failing the whole local check.

---

## Task 1: Safe Fetcher with SSRF Protection & Robots.txt Compliance

**Files:**
- Create: `backend/app/services/fetcher/__init__.py`
- Create: `backend/app/services/fetcher/safe_fetcher.py`
- Test: `tests/unit/fetcher/test_safe_fetcher.py`

**Interfaces:**
- Produces: `SafeFetcher.fetch_url(url: str) -> FetchResult`

- [ ] **Step 1: Write the failing test for IP blocking and safe fetching**

```python
import pytest
from app.services.fetcher.safe_fetcher import SafeFetcher, FetchError

def test_block_private_ips():
    fetcher = SafeFetcher()
    with pytest.raises(FetchError, match="Blocked private or internal IP"):
        fetcher._validate_url("http://127.0.0.1/admin")
    with pytest.raises(FetchError, match="Blocked private or internal IP"):
        fetcher._validate_url("http://169.254.169.254/latest/meta-data")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/unit/fetcher/test_safe_fetcher.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `SafeFetcher` in `backend/app/services/fetcher/safe_fetcher.py`**

Implement URL validation, IP blocking against private/loopback/link-local ranges, `robots.txt` checking, and streamed size capping.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/unit/fetcher/test_safe_fetcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/fetcher/safe_fetcher.py backend/tests/unit/fetcher/test_safe_fetcher.py
git commit -m "feat: implement SSRF-protected safe fetcher"
```

---

## Task 2: Open-Access Scholarly Connectors & URL List Handler

**Files:**
- Create: `backend/app/services/connectors/scholarly.py`
- Test: `tests/unit/connectors/test_scholarly.py`

**Interfaces:**
- Consumes: `SafeFetcher`
- Produces: `ScholarlySearchService.search_all(query: str) -> List[ExternalSourceDocument]`

- [ ] **Step 1: Write the failing test for scholarly API connectors**

```python
def test_scholarly_connector_mock(monkeypatch):
    # Test connector parsing with mock HTTP response
    pass
```

- [ ] **Step 2: Implement Scholarly connectors (OpenAlex, arXiv, Semantic Scholar) in `backend/app/services/connectors/scholarly.py`**
- [ ] **Step 3: Run tests and commit**

```bash
git add backend/app/services/connectors/scholarly.py
git commit -m "feat: add open-access scholarly API connectors"
```

---

## Task 3: Distinctive Passage Query Selection

**Files:**
- Create: `backend/app/services/plagiarism/query_selector.py`
- Test: `tests/unit/plagiarism/test_query_selector.py`

**Interfaces:**
- Produces: `QuerySelector.select_queries(text: str, max_queries: int = 15) -> List[str]`

- [ ] **Step 1: Write test and implement query selector for distinctive 8-12 word phrases across document sections.**
- [ ] **Step 2: Run tests and commit.**

---

## Task 4: Plagiarism Engine Integration & API Extension

**Files:**
- Modify: `backend/app/services/plagiarism/detection.py`
- Modify: `backend/app/schemas/plagiarism.py`
- Modify: `backend/app/api/v1/plagiarism.py`
- Test: `backend/tests/integration/test_plagiarism_online.py`

**Interfaces:**
- Consumes: `SafeFetcher`, `ScholarlySearchService`, `QuerySelector`
- Produces: Extended plagiarism check request supporting online mode and URL lists.

- [ ] **Step 1: Extend backend plagiarism check service to accept `online_mode: bool` and `custom_urls: List[str]`.**
- [ ] **Step 2: Run tests and commit.**

---

## Task 5: Frontend UI Updates for Online & URL Checking

**Files:**
- Modify: `frontend/src/features/plagiarism/PlagiarismChecker.tsx`

- [ ] **Step 1: Add online mode toggle with privacy warning, custom URL input list, and source provenance display in the UI.**
- [ ] **Step 2: Build and verify frontend with Vite.**

---

## Task 6: Final Documentation & Review

**Files:**
- Create: `docs/REFERENCE_REPO_AUDIT.md`
- Create: `docs/THIRD_PARTY_NOTICES.md`
- Create: `docs/USER_GUIDE.md`
- Create: `docs/WHAT_YOU_MUST_DO.md`

- [ ] **Step 1: Write reference audit and documentation files.**
- [ ] **Step 2: Run full unit test suite (all tests passing).**
- [ ] **Step 3: Commit all changes.**
