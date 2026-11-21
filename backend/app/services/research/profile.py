"""Per-paper profile extraction service with Pydantic validation and evidence verification."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.ollama import OllamaService
from app.services.research.evidence import EvidenceVerificationService
from app.services.research.sections import SectionDetectionService


class EvidenceSchema(BaseModel):
    page: int
    quote: str


class FieldWithEvidence(BaseModel):
    value: str
    evidence: List[EvidenceSchema] = Field(default_factory=list)


class PaperProfileSchema(BaseModel):
    title: str = "Unknown"
    year: int = 2024
    research_problem: FieldWithEvidence
    objectives: List[FieldWithEvidence] = Field(default_factory=list)
    methodology: List[FieldWithEvidence] = Field(default_factory=list)
    algorithms: List[FieldWithEvidence] = Field(default_factory=list)
    datasets: List[FieldWithEvidence] = Field(default_factory=list)
    evaluation_metrics: List[FieldWithEvidence] = Field(default_factory=list)
    findings: List[FieldWithEvidence] = Field(default_factory=list)
    explicit_limitations: List[FieldWithEvidence] = Field(default_factory=list)
    author_future_work: List[FieldWithEvidence] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)


class ProfileExtractionService:
    """Service for extracting structured paper profiles via Ollama."""

    PROMPT_VERSION = "v1.0"

    def __init__(self, ollama_service: Optional[OllamaService] = None):
        self.ollama = ollama_service or OllamaService()
        self.evidence_verifier = EvidenceVerificationService()
        self.section_detector = SectionDetectionService()

        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "profile_extraction.txt"
        if prompt_path.exists():
            self.system_prompt = prompt_path.read_text(encoding="utf-8")
        else:
            self.system_prompt = "Extract academic paper profile in JSON format."

    def extract_profile(
        self,
        document_id: str,
        pages: List[tuple[str, int]],
        title_hint: str = "",
    ) -> Dict[str, Any]:
        """Extract structured profile for a paper with evidence verification.

        Args:
            document_id: Document ID
            pages: List of (page_text, page_number) tuples
            title_hint: Optional title hint

        Returns:
            Dictionary containing extracted profile and verification status
        """
        # Compile relevant excerpts (abstract, intro, methods, results, limitations, conclusion)
        sections = self.section_detector.detect_sections(pages)

        excerpts_text = []
        for sec in sections:
            excerpts_text.append(f"[Page {sec.page_number}] {sec.title.upper()}\n{sec.text[:2000]}")

        combined_excerpts = "\n\n".join(excerpts_text)
        if len(combined_excerpts) > 12000:
            combined_excerpts = combined_excerpts[:12000]  # Fit within context

        user_prompt = f"Analyze the following paper excerpts and extract the profile.\nTitle Hint: {title_hint}\n\nExcerpts:\n{combined_excerpts}"

        # Get JSON schema from Pydantic model
        json_schema = PaperProfileSchema.model_json_schema()

        # Generate structured output from Ollama (with 1 repair attempt)
        raw_data = None
        for attempt in range(2):
            try:
                raw_data = self.ollama.generate_json(
                    prompt=user_prompt,
                    json_schema=json_schema,
                    system_prompt=self.system_prompt,
                )
                # Validate with Pydantic
                profile = PaperProfileSchema(**raw_data)
                raw_data = profile.model_dump()
                break
            except Exception as e:
                if attempt == 1:
                    raise RuntimeError(f"Profile extraction failed validation after repair attempt: {str(e)}")

        if not raw_data:
            raise RuntimeError("Profile extraction failed to produce valid output")

        # Verify all evidence quotes
        verification_results = []
        all_fields = [
            raw_data.get("research_problem"),
            *raw_data.get("objectives", []),
            *raw_data.get("methodology", []),
            *raw_data.get("algorithms", []),
            *raw_data.get("datasets", []),
            *raw_data.get("evaluation_metrics", []),
            *raw_data.get("findings", []),
            *raw_data.get("explicit_limitations", []),
            *raw_data.get("author_future_work", []),
        ]

        verified_count = 0
        total_evidence_count = 0

        for field_item in all_fields:
            if not field_item or not isinstance(field_item, dict):
                continue
            for ev in field_item.get("evidence", []):
                total_evidence_count += 1
                ver = self.evidence_verifier.verify_quote(
                    quote=ev.get("quote", ""),
                    claimed_page=ev.get("page", 1),
                    document_pages=pages,
                )
                if ver.is_verified:
                    verified_count += 1
                verification_results.append({
                    "quote": ev.get("quote"),
                    "claimed_page": ev.get("page"),
                    "is_verified": ver.is_verified,
                    "matched_page": ver.matched_page,
                    "error": ver.error_message,
                })

        verification_rate = (verified_count / total_evidence_count) if total_evidence_count > 0 else 1.0

        return {
            "paper_id": document_id,
            "profile": raw_data,
            "model_name": self.ollama.model_name,
            "prompt_version": self.PROMPT_VERSION,
            "status": "completed" if verification_rate >= 0.8 else "flagged_unverified",
            "verification_rate": verification_rate,
            "verification_details": verification_results,
        }
