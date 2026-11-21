# ResearchRadar

**Open-source plagiarism checker and research gap analyzer**

ResearchRadar helps researchers check text similarity and identify potential research gaps across academic papers — all running locally with open-source tools and open-weight models.

## Features

### 🔍 Plagiarism & Similarity Checker
- Compare documents against your uploaded corpus
- Lexical matching (winnowing, fuzzy matching)
- Semantic similarity (coming in Phase 3)
- Page-level match tracking
- Clear, honest reporting (similarity percentage, not accusations)
- Export detailed reports

### 🔬 Research Gap Analyzer
- Analyze 2-10 papers simultaneously
- Extract methodology, datasets, findings, and limitations
- Cross-paper comparison
- Identify patterns and potential research directions
- Evidence-based reporting with source citations

## Project Status

**Current Phase:** Phase 0 — Setup and Inspection ✅

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for detailed status.

| Phase | Status |
|-------|--------|
| Phase 0: Setup | 🟡 In Progress |
| Phase 1: Ingestion | ⚪ Not Started |
| Phase 2: Plagiarism MVP | ⚪ Not Started |
| Phase 3: Semantic & Open Access | ⚪ Not Started |
| Phase 4: Gap Extraction | ⚪ Not Started |
| Phase 5: Gap Comparison & UI | ⚪ Not Started |
| Phase 6: Integration & Release | ⚪ Not Started |

## Important Limitations

- **Not a Turnitin replacement:** No access to paywalled journals or private corpora
- **Local processing only:** Compares against documents you upload
- **No "plagiarism proof":** Matches can be quotes, references, or common phrases
- **English text PDFs only:** No OCR support in MVP
- **Single user:** No multi-user authentication in MVP

## Technology Stack

### Open Source, Local First
- **Backend:** Python 3.11+, FastAPI, pypdf (NOT PyMuPDF)
- **LLM:** Ollama + Qwen2.5 7B Instruct (Apache-2.0 license)
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Store:** ChromaDB
- **Frontend:** React + Vite + Tailwind CSS
- **Database:** SQLite (MVP) or PostgreSQL

All components are MIT/Apache-2.0/BSD licensed. See [`docs/OPEN_SOURCE_LICENSES.md`](docs/OPEN_SOURCE_LICENSES.md).

## Requirements

### Minimum (Development)
- Python 3.11+
- Node.js 18+
- 8GB RAM
- CPU-only mode supported

### Recommended (Full Features)
- NVIDIA GPU with 10GB+ VRAM (RTX 3080 or better)
- 16GB RAM
- CUDA-enabled PyTorch
- 20GB free disk space (for models)

## Installation

*Installation instructions will be added in Phase 1*

```bash
# Clone repository
git clone https://github.com/davershayan12/SCD_project.git
cd SCD_project

# Backend setup (Phase 1)
# cd backend
# python -m venv venv
# source venv/bin/activate  # or venv\Scripts\activate on Windows
# pip install -r requirements.txt

# Frontend setup (Phase 2)
# cd frontend
# npm install

# Install Ollama and pull model (workstation only)
# ollama pull qwen2.5:7b
```

## Configuration

Create `.env` file in backend directory:

```bash
# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_NUM_CTX=8192

# Hardware
USE_GPU=true
EMBEDDING_DEVICE=cuda  # or cpu

# Limits
MAX_FILE_SIZE_MB=50
MAX_PAGE_COUNT=500
```

## Usage

*Usage instructions will be added in Phase 2*

## Development

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution guidelines.

### Project Structure

```text
SCD_project/
├── backend/         # FastAPI backend (Phase 1+)
├── frontend/        # React frontend (Phase 2+)
├── docs/            # Documentation
├── tests/           # Test fixtures
└── .github/         # CI/CD workflows
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design and structure
- [Project Status](docs/PROJECT_STATUS.md) — Current phase and blockers
- [Implementation Log](docs/IMPLEMENTATION_LOG.md) — Development history
- [Open Source Licenses](docs/OPEN_SOURCE_LICENSES.md) — Dependency licenses
- [Security Policy](SECURITY.md) — Security considerations
- [Phase Guidelines](00_COMMON_RULES.md) — Development phases

## Security & Privacy

- **Local processing:** No data sent to third parties
- **File validation:** Extension, MIME, size, content checks
- **No code execution:** Uploaded files never executed
- **No telemetry:** Zero tracking or analytics

See [`SECURITY.md`](SECURITY.md) for details.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.

## Acknowledgments

Built with:
- [Ollama](https://ollama.ai/) — Local LLM runtime
- [Qwen2.5](https://huggingface.co/Qwen) — Open-weight language model
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [React](https://react.dev/) — UI library
- [ChromaDB](https://www.trychroma.com/) — Vector database

## Roadmap

- [x] Phase 0: Project setup and architecture
- [ ] Phase 1: Document ingestion pipeline
- [ ] Phase 2: Plagiarism MVP with lexical matching
- [ ] Phase 3: Semantic matching and open-access integration
- [ ] Phase 4: Research gap extraction
- [ ] Phase 5: Gap comparison and UI
- [ ] Phase 6: Integration and release

## Contact

For questions or issues, please open a GitHub issue.

---

**Note:** This project is under active development. Phase 0 (foundations) is complete. Phase 1 (document ingestion) is next.
