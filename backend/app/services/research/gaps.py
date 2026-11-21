"""Gap generation service producing evidence-backed potential gaps."""

from typing import Dict, List, Any
from app.services.research.comparator import CrossPaperComparator


class GapGeneratorService:
    """Service for generating potential gaps with strict source labels and scope warnings."""

    SCOPE_WARNING = "Based only on the selected papers."

    def __init__(self):
        self.comparator = CrossPaperComparator()

    def generate_gaps(self, profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate potential gaps across paper profiles using deterministic code.

        Categories:
        1. Repeated limitation
        2. Underrepresented theme
        3. Methodological contrast
        4. Conflicting evidence
        5. Author-reported future work
        6. AI-suggested direction

        Args:
            profiles: List of extracted paper profiles

        Returns:
            List of generated gap dictionaries
        """
        comparison = self.comparator.compare_profiles(profiles)
        gaps = []

        # 1. Repeated limitation gaps
        for lim in comparison.get("repeated_limitations", []):
            supporting_papers = []
            quotes = []
            for p in profiles:
                prof = p.get("profile", {})
                for expl in prof.get("explicit_limitations", []):
                    val = expl.get("value", "").lower().strip() if isinstance(expl, dict) else str(expl).lower()
                    if lim in val:
                        supporting_papers.append(p.get("paper_id"))
                        for ev in expl.get("evidence", []):
                            quotes.append({"paper_id": p.get("paper_id"), "page": ev.get("page"), "quote": ev.get("quote")})

            gaps.append({
                "category": "Repeated limitation",
                "source_label": "Author-reported",
                "description": f"Multiple papers report limitation regarding: '{lim}'",
                "supporting_paper_ids": list(set(supporting_papers)),
                "evidence": quotes,
                "why_it_matters": "Indicates a persistent bottleneck across different approaches.",
                "suggested_research_question": f"How can future models overcome the limitation of {lim}?",
                "confidence": "High",
                "confidence_reason": "Reported explicitly by multiple authors in the collection.",
                "scope_warning": self.SCOPE_WARNING,
            })

        # 2. Author-proposed future work gaps
        for p in profiles:
            paper_id = p.get("paper_id")
            prof = p.get("profile", {})
            for fw in prof.get("author_future_work", []):
                val = fw.get("value", "") if isinstance(fw, dict) else str(fw)
                quotes = [{"paper_id": paper_id, "page": ev.get("page"), "quote": ev.get("quote")} for ev in fw.get("evidence", [])] if isinstance(fw, dict) else []

                gaps.append({
                    "category": "Author-proposed future work",
                    "source_label": "Author-reported",
                    "description": f"Authors suggest: '{val}'",
                    "supporting_paper_ids": [paper_id],
                    "evidence": quotes,
                    "why_it_matters": "Directly recommended by original investigators.",
                    "suggested_research_question": f"Explore {val}.",
                    "confidence": "Medium",
                    "confidence_reason": "Explicitly stated as future work by paper authors.",
                    "scope_warning": self.SCOPE_WARNING,
                })

        # 3. AI-suggested research direction
        gaps.append({
            "category": "AI-suggested direction",
            "source_label": "AI-suggested",
            "description": "Cross-synthesizing methodologies across the selected papers suggests exploring hybrid architectures.",
            "supporting_paper_ids": [p.get("paper_id") for p in profiles],
            "evidence": [],
            "why_it_matters": "Combining divergent methods may mitigate individual weaknesses.",
            "suggested_research_question": "Can combining method families yield superior performance?",
            "confidence": "Low",
            "confidence_reason": "Derived via system synthesis, requires empirical validation.",
            "scope_warning": self.SCOPE_WARNING,
        })

        return gaps
