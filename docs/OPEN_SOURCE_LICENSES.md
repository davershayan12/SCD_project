# Open Source Licenses

All dependencies and models used in ResearchRadar must have permissive licenses. This document tracks their licenses and verification status.

**License Policy:**
- ✅ Allowed: MIT, Apache-2.0, BSD, ISC, PSF, CC-BY, CC0
- ❌ Not Allowed: AGPL, GPL, proprietary, research-only

---

## Backend Dependencies

| Package | Version | License | Verified Date | Notes |
|---------|---------|---------|---------------|-------|
| TBD | TBD | TBD | TBD | To be added in Phase 1 |

**Key dependencies to verify:**
- FastAPI → MIT
- Pydantic → MIT
- pypdf (NOT PyMuPDF) → BSD
- RapidFuzz → MIT
- scikit-learn → BSD
- Sentence Transformers → Apache-2.0
- ChromaDB → Apache-2.0
- pytest → MIT

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
