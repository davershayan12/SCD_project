"""Cross-paper comparison service using deterministic counting and clustering."""

from collections import Counter
from typing import Dict, List, Any


class CrossPaperComparator:
    """Service for comparing paper profiles and computing frequencies."""

    def compare_profiles(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple paper profiles.

        Args:
            profiles: List of extracted paper profile dictionaries

        Returns:
            Comparison summary with computed frequencies and overlaps
        """
        if not profiles:
            return {"papers_count": 0, "shared_datasets": [], "common_limitations": []}

        # Collect all datasets
        all_datasets = []
        all_methods = []
        all_limitations = []

        for p in profiles:
            prof = p.get("profile", {})
            for ds in prof.get("datasets", []):
                if isinstance(ds, dict):
                    all_datasets.append(ds.get("value", "").lower().strip())
                elif isinstance(ds, str):
                    all_datasets.append(ds.lower().strip())

            for m in prof.get("methodology", []):
                if isinstance(m, dict):
                    all_methods.append(m.get("value", "").lower().strip())
                elif isinstance(m, str):
                    all_methods.append(m.lower().strip())

            for lim in prof.get("explicit_limitations", []):
                if isinstance(lim, dict):
                    all_limitations.append(lim.get("value", "").lower().strip())
                elif isinstance(lim, str):
                    all_limitations.append(lim.lower().strip())

        # Compute frequencies in Python (never by LLM)
        dataset_counts = Counter(all_datasets)
        method_counts = Counter(all_methods)
        limitation_counts = Counter(all_limitations)

        # Find shared datasets (appear in >= 2 papers)
        shared_datasets = [ds for ds, count in dataset_counts.items() if count >= 2 and ds]

        # Find repeated limitations (appear in >= 2 papers)
        repeated_limitations = [lim for lim, count in limitation_counts.items() if count >= 2 and lim]

        return {
            "papers_count": len(profiles),
            "dataset_frequencies": dict(dataset_counts),
            "method_frequencies": dict(method_counts),
            "shared_datasets": shared_datasets,
            "repeated_limitations": repeated_limitations,
        }
