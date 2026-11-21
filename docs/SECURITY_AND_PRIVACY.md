# Security and Privacy Policy

**Project:** ResearchRadar  
**Last Updated:** 2026-11-22  

---

## 1. Privacy by Default (Local Processing)

ResearchRadar is designed with a strict **local-first, privacy-first** architecture:
- **No Third-Party Uploads:** All document ingestion, text extraction, normalization, chunking, embedding generation, and LLM extraction run entirely locally on your machine.
- **Zero Telemetry:** ResearchRadar collects no analytics, usage tracking, or diagnostics.
- **No Cloud Dependencies:** Operates completely offline once models and dependencies are installed.

---

## 2. Data Storage & Management

All data is stored locally in SQLite and ChromaDB under the `./storage/` directory (excluded from git):
- **Document Files:** Stored in `./storage/uploads/` with randomly generated cryptographic names to prevent path traversal attacks.
- **Metadata & Reports:** Stored locally in `./storage/researchradar.db` (SQLite).
- **Embeddings & Vectors:** Stored locally in `./storage/chroma_data/` (ChromaDB).

---

## 3. Deletion & Privacy Controls

When a user deletes a document via `DELETE /api/v1/documents/{id}`, the deletion cascades across **all derived artifacts**:
1. The uploaded file on disk (`./storage/uploads/{filename}`)
2. Database records (`documents`, `document_pages`, `document_chunks`)
3. Vector embeddings in ChromaDB (`document_chunks` collection)
4. Associated plagiarism reports and matches (`plagiarism_reports`, `plagiarism_matches`)

---

## 4. Security Measures

- **File Validation:** Strict extension checking (`.pdf`, `.txt`), MIME type verification, size limits (50MB default), page count limits (500 pages), and encrypted/corrupt/scanned PDF rejection.
- **Path Traversal Protection:** Original filenames are replaced with cryptographic random tokens (`secrets.token_hex(16)`).
- **Authorization:** Document ownership isolation (`owner_id`) on all API lookups.
- **Log Sanitation:** Document full text and LLM prompts are strictly excluded from logging.
- **Dependency License Auditing:** Automated CI checks enforce permissive licenses (MIT, Apache-2.0, BSD) and block AGPL/GPL dependencies.
