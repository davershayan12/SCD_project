# Open Source Licenses

All dependencies and models used in ResearchRadar must have permissive licenses. This document tracks their licenses and verification status.

**License Policy:**
- ✅ Allowed: MIT, Apache-2.0, BSD, ISC, PSF, CC-BY, CC0
- ❌ Not Allowed: AGPL, GPL, proprietary, research-only

---

## Backend Dependencies

| Package | Version | License | Verified Date | Notes |
|---------|---------|---------|---------------|-------|
| fastapi | 0.165.0 | MIT | 2026-11-21 | ✓ |
| uvicorn | 0.54.0 | BSD-3-Clause | 2026-11-21 | ✓ |
| pydantic | 2.14.4 | MIT | 2026-11-21 | ✓ |
| pydantic-settings | 2.16.3 | MIT | 2026-11-21 | ✓ |
| python-multipart | 0.0.34 | Apache-2.0 | 2026-11-21 | ✓ |
| sqlalchemy | 2.1.9 | MIT | 2026-11-21 | ✓ |
| alembic | 1.20.1 | MIT | 2026-11-21 | ✓ |
| pypdf | 7.1.1 | BSD-3-Clause | 2026-11-21 | ✓ NOT PyMuPDF (AGPL) |
| rapidfuzz | 3.14.6 | MIT | 2026-11-21 | ✓ |
| scikit-learn | 1.9.1 | BSD-3-Clause | 2026-11-21 | ✓ |
| pytest | 9.2.0 | MIT | 2026-11-21 | ✓ |
| pytest-asyncio | 1.5.0 | Apache-2.0 | 2026-11-21 | ✓ |
| httpx | 0.28.1 | BSD-3-Clause | 2026-11-21 | ✓ |
| python-dotenv | 1.2.4 | BSD-3-Clause | 2026-11-21 | ✓ |

---

## Frontend Dependencies

| Package | Version | License | Verified Date | Notes |
|---------|---------|---------|---------------|-------|
| TBD | TBD | TBD | TBD | To be added when frontend is created |

**Key dependencies to verify:**
- React → MIT
- Tailwind CSS → MIT

---

## Models

| Model | Version | License | Link | Verified Date | Notes |
|-------|---------|---------|------|---------------|-------|
| Qwen2.5 7B Instruct | Q4 | Apache-2.0 | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct | TBD | Default LLM, verify on workstation |
| all-MiniLM-L6-v2 | latest | Apache-2.0 | https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 | TBD | Default embedding model |

---

## Runtime

| Tool | Version | License | Verified Date | Notes |
|------|---------|---------|---------------|-------|
| Ollama | TBD | MIT | TBD | To be verified on workstation |
| Python | 3.14.2 | PSF | 2026-11-21 | ✓ |

---

## Notes

- **PyMuPDF is AGPL and must not be used**. Use pypdf, pdfminer.six, or pypdfium2 instead.
- **Qwen2.5 3B is NOT Apache-2.0** — do not use as default
- All licenses must be verified against official model cards and repositories before adoption
- CI checks will fail on disallowed licenses
