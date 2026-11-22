# ResearchRadar — Internet Plagiarism Search + AI-Text Detection (v2, Lenovo V15 G4 edition)

This is a **class-demo version**: fast to build, easy to show a teacher. Paste everything below the line into your coding agent with the ResearchRadar repo open. If you saved earlier files (`00_COMMON_RULES.md`, phase files, other prompts) in `docs/`, the agent may read them, but **this prompt overrides them where they conflict** (it is demo-first and lighter).

---

You are a senior Python engineer and React developer. In my existing **ResearchRadar** project (FastAPI + React + Tailwind), build a **demo-ready "Document Check" feature** with two parts:

1. **Web plagiarism search**: take a document, search the internet for passages that appear elsewhere, and show which text matches which web page.
2. **AI-text detection**: estimate which parts of the document look AI-generated.

This is for a university project demo, not production. Prioritize: **works reliably on the demo, looks clear, easy to explain.** Build a real working implementation, not a mockup.

## My environment (design for this machine)
- **Laptop:** Lenovo V15 G4, Windows, **no dedicated GPU, CPU-only**. RAM is **[8 GB or 16 GB; I will fill this in `.env`/docs]**. Everything must run acceptably on this laptop.
- **Local LLM (Ollama)** is used **only** to generate the AI sample texts for the demo/evaluation. Plagiarism search and the AI-likelihood detector do **not** need an LLM.
  - Default: `qwen3:4b` on 16 GB RAM, `qwen3:1.7b` on 8 GB RAM (verify the model-card license; expected Apache-2.0). Make the model name configurable.
  - **Turn thinking off** (`think: false` or `/no_think`), set `num_ctx` around 4096, one request at a time.
  - Because CPU generation is slow, **generate the AI demo samples once and save them in `tests/fixtures/`**; the demo must never wait on a live LLM. A "Generate new AI sample" button is optional and must show progress.
- **Disk layout:** C: is limited. Models live on **D:**
  - Ollama models: environment variable `OLLAMA_MODELS=D:\ollama\models`.
  - Hugging Face / sentence-transformers / transformers caches: `HF_HOME=D:\hf_cache` (document this in `.env.example` and the guide).
  - Uploads, reports, and temp files go in a configurable data folder (default inside the project; allow a D: path).
- **CPU performance rules:**
  - The AI detector uses a small causal LM (`distilgpt2`/`gpt2`, about 80-125M parameters). Score in windows of at most 512 tokens, batch small, truncate very long documents with a clear notice, and **cache scores by text hash**.
  - Web fetching: modest concurrency (e.g. 4 workers), per-provider rate limits, timeouts.
  - Target: a 5-page document finishes the full check in **about 2 minutes or less** on this laptop; show live progress per stage so a wait never looks like a freeze. Report real measured timings in `docs/TESTING_AND_EVALUATION.md`.
  - If the machine runs low on RAM, fail with a clear message instead of freezing.

## Ground rules (kept short)
- Inspect my repo first, reuse what exists, do not break existing features or add a second backend/frontend.
- Free and open source only. Permissive licenses (MIT/Apache/BSD); no AGPL/GPL; no PyMuPDF (use `pypdf`). Verify every new dependency and model license and list them in `docs/OPEN_SOURCE_LICENSES.md`.
- Secrets (API keys) only in `.env`; provide `.env.example`; never commit them.
- Be honest in the UI and report: results are **indicators, not proof**. Never print "plagiarized" or "AI-written" as a verdict. Use "Match found", "Needs review", "AI-likelihood".
- Never claim a test passed unless you ran it. Do not invent accuracy numbers.

## Part 1: Web plagiarism search

### Pipeline
1. **Input:** upload PDF/TXT (DOCX optional via `python-docx`) or paste text. Extract text page by page with `pypdf`, normalize (NFKC, de-hyphenate, whitespace), keep page numbers and character offsets.
2. **Pick queries from the whole document** (not just the first sentences): choose a configurable number (default about 15-20) of distinctive passages, ranked by rare words and length, skipping references, quotes, and very common phrases, and spread across the document. Search with **contiguous phrases of about 8-12 words from the real text**, in quotes, with an unquoted fallback.
3. **Search providers** (pluggable interface, switchable in `.env`):
   - **A. Official search API with my key.** Research which general web-search APIs currently have a free tier and are practical for a demo (the agent must check current availability and terms itself, and propose options in its plan). Preferred for reliability.
   - **B. Demo fallback:** a lightweight library-based web search (e.g. the MIT-licensed `ddgs` package) if verified permissive. Label it "demo only, may be rate-limited or blocked" in the docs. If it fails mid-run, show a clear message and continue with other providers.
   - **C. Free scholarly APIs:** arXiv, OpenAlex, CORE (verify what each can actually do; some are metadata-only).
   - **D. URL list:** I paste specific URLs and the tool compares my document against those pages only (best for a guaranteed demo).
   Do not solve CAPTCHAs or bypass logins/paywalls.
4. **Fetch result pages** with timeouts (about 10 s), a response-size cap (stream, e.g. 2 MB), status and content-type checks (HTML/plain text/PDF), an honest User-Agent, `robots.txt` respected where practical, and block private/loopback IP addresses. Extract main text (strip nav/footer/scripts). Run fetches concurrently but politely.
5. **Match** my text against each page with **word k-gram shingles + winnowing**, then verify with **RapidFuzz**; classify **Exact** or **Near-exact**. Keep page/offset for my text. Ignore very short or common phrases (configurable).
6. **Score:** `similarity % = covered_words / eligible_words x 100`, with overlapping matches merged so nothing is double-counted. Also show the largest single-source share. **Do not average pairwise scores.** Show the formula in the report.
7. **Optional "possible paraphrase":** TF-IDF or embeddings, shown separately, never in the percentage.

### Output
Highlighted document view (matched text colored by source); list of matched passages with the web page title/URL and the matching text side by side; ranked source list; a **status panel** that says plainly what happened (queries run, results found, pages fetched, pages blocked/failed and why). The report must say it covers **only the sources it actually searched**; "no match found" never means "original."

## Part 2: AI-text detection

Be honest here: **AI detectors are unreliable.** They produce false positives (especially for non-native English writers and formal academic writing) and miss paraphrased or newer-model text. Build it as an **"AI-likelihood indicator"** with clear caveats, and measure it on my own data.

### Method
1. **Default detector (no heavy download):** per-paragraph (and per-sentence for highlighting) **perplexity and burstiness** using a small open causal LM through `transformers` (e.g. `distilgpt2` or `gpt2`, MIT; verify license). Lower perplexity and low variance across sentences suggest more machine-like text. Normalize and combine into a 0-100 AI-likelihood score per paragraph with a documented formula.
2. **Optional second detector:** a pretrained open AI-text classifier from Hugging Face (for example `roberta-base-openai-detector`, but **verify its license and note it targets older GPT-2 text**, or another open model you find). Combine it with method 1 only if evaluation shows it helps. Record the license.
3. **Do not ask an LLM "is this AI-written?"**; that is unreliable and not evidence.
4. **Guards:** require a minimum length (e.g. 150+ words per scored block) or show "too short to assess"; show a confidence band (Low / Medium / High **AI-likelihood**) with visible, configurable thresholds; always display the caveat text: *"AI-likelihood is a statistical indicator, not proof of authorship. It can be wrong, especially for non-native English writing and formal academic text."*
5. Show the **overall AI-likelihood** (mean over eligible paragraphs) and a **per-paragraph heat highlight** with scores.

### Keep the two checks independent
Copied web text can be human-written, and AI text usually has **no web match**. The UI should present them as two separate panels and say that plainly.

## Evaluation (so I can show real numbers to the teacher)
Build a small labelled test set in `tests/fixtures/`:
- **Human text:** open-licensed writing that predates modern LLMs (for example arXiv abstracts/sections from before 2021, or other CC-BY text). Log sources and licenses in `tests/fixtures/DATA_LICENSES.md`.
- **AI text:** generate samples **locally** with my Ollama model on the same topics.
- **Copied text:** passages from open pages (for example Wikipedia paragraphs, CC BY-SA, with attribution) and lightly edited versions of them.
- **Original text** I write or that is clearly unrelated.

Report real recall, precision, false-positive rate for the web matcher, and accuracy / false-positive rate / a simple threshold sweep for the AI detector, in `docs/TESTING_AND_EVALUATION.md`. Include failures honestly (for example paraphrased AI text, human text flagged as AI).

## UI (React + Tailwind, existing design system)
One "Document Check" page:
- Upload/paste box, a checkbox row: **Web search**, **AI-likelihood**, provider selector, "paste URLs" box.
- A run button with live progress per stage.
- Two result panels: **Web similarity** (percentage with formula, highlighted document, matched sources) and **AI-likelihood** (overall score, per-paragraph heat highlight).
- A status/diagnostics panel, a persistent disclaimer, and **export report** (Markdown or PDF, whichever the app already supports).
- A **"Load demo samples" button** with three built-in samples: (1) text copied from an open web page, (2) locally generated AI text, (3) original human text. The demo must work in under a minute.
- Loading, empty, and error states; accessible labels.

## Backend
Thin FastAPI routes, services, Pydantic schemas, type hints. Run checks as an async job with progress polling. Configurable limits (file size, pages, number of queries, per-provider timeouts). A stage failure must show in the report (never present a partial run as complete). No full document text in logs; no stack traces in API responses. Delete uploaded files after the report is generated unless I choose to keep them.

## Tests (write and actually run)
Winnowing/merging/scoring unit tests; exact, light-edit, and unrelated fixtures; **search and fetch tests with mocked responses (no live calls in CI)**; size-cap, timeout, and private-IP tests; AI-detector tests for the "too short" guard and score normalization; one end-to-end test with demo samples using mocked search.

## Documentation to write
1. `docs/DEMO_GUIDE.md`: **step-by-step for me**: install on Windows (Python venv, dependencies, installing Ollama and moving its models to D: with `OLLAMA_MODELS`, setting `HF_HOME` on D:, pulling the model, frontend), `.env` variables explained with where to get each key, how to start everything, how to run the three demo samples, **a 5-minute demo script for the teacher** (what to click, what result to expect, what to say), and troubleshooting (search blocked, rate limits, slow model download).
2. `docs/WHAT_YOU_MUST_DO.md`: manual steps only I can do (create any API key, fill `.env`, download models, prepare test samples, rehearse the demo), marked required/optional with links and exact variable names.
3. `docs/LIMITATIONS_FOR_TEACHER.md`: a one-page honest summary of what the tool can and can't do (the two checks are indicators; AI detectors can be wrong; web coverage depends on the provider; no OCR), written so I can present it confidently.
4. Update `README.md`, `docs/OPEN_SOURCE_LICENSES.md`, `docs/IMPLEMENTATION_LOG.md`, `docs/PROJECT_STATUS.md`.

## Working method
1. **First response, before changing code:** confirm the CPU-only/D: plan above is feasible, then report my repo's structure and reusable parts, the search providers you propose (with what each can actually do and any cost/limits), the AI-detector options and their licenses, risks, files you will create/modify, and a step-by-step plan. **Wait for my approval.**
2. Build in this order, updating the log after each step: (a) text extraction + shared services, (b) web search + fetch + matching + report, (c) AI-likelihood detector, (d) UI + demo samples, (e) tests + evaluation, (f) docs.
3. At the end tell me what works, what doesn't, the exact commands to run it, my manual steps, the real evaluation numbers, and the **measured run time on this laptop**.
