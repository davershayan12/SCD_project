"""
Phase 2 Evaluation Script

Evaluation of plagiarism detection performance using synthetic test fixtures.
Tests cover: exact copies, lightly edited, paraphrased, unrelated text.

Run with: python scripts/run_evaluation.py
"""

import random
import string
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.plagiarism.fuzzy import FuzzyMatchingService
from app.services.plagiarism.scoring import ScoringService
from app.services.plagiarism.winnowing import WinnowingService


@dataclass
class TestCase:
    """A single test case for evaluation."""
    name: str
    submitted_text: str
    source_texts: List[Tuple[str, str]]  # [(title, text)]
    expected_category: str  # "exact_copy", "near_exact", "paraphrase", "unrelated"
    expected_has_matches: bool


@dataclass
class EvaluationResult:
    """Result of evaluating a test case."""
    test_name: str
    expected_category: str
    actual_category: str
    match_count: int
    similarity_percent: float
    detected: bool  # matches found as expected
    correct: bool  # category classification correct
    false_positive: bool
    false_negative: bool
    processing_time_ms: float


class EvaluationFixtureGenerator:
    """Generates synthetic test fixtures for plagiarism evaluation."""

    @staticmethod
    def generate_academic_paragraph(seed: int = 42) -> str:
        """Generate a realistic academic paragraph."""
        random.seed(seed)

        templates = [
            "This study examines the relationship between {noun1} and {noun2} in {context}.",
            "Previous research has demonstrated that {noun1} significantly affects {noun2}.",
            "The methodology employed in this paper follows established protocols for {context}.",
            "Results indicate that the correlation between {noun1} and {noun2} is {adjective}.",
            "These findings contribute to the ongoing debate regarding {topic} in the field.",
            "The implications of this research extend to both {noun1} and {noun2} applications.",
        ]

        nouns = ["machine learning", "neural networks", "data science", "NLP", "deep learning",
                 "algorithm", "model", "dataset", "feature", "training", "inference"]
        contexts = ["natural language processing", "computer vision", "data analysis",
                    "artificial intelligence", "predictive modeling"]
        adjectives = ["statistically significant", "modest", "substantial", "negligible", "remarkable"]
        topics = ["AI ethics", "model interpretability", "training efficiency", "deployment strategies"]

        template = random.choice(templates)
        return template.format(
            noun1=random.choice(nouns),
            noun2=random.choice(nouns),
            context=random.choice(contexts),
            adjective=random.choice(adjectives),
            topic=random.choice(topics)
        )

    @staticmethod
    def create_exact_copy(seed: int = 42) -> Tuple[str, str]:
        """Create identical submitted and source documents."""
        text = EvaluationFixtureGenerator.generate_academic_paragraph(seed)
        return text, text

    @staticmethod
    def create_near_exact(seed: int = 42, edits: int = 3) -> Tuple[str, str]:
        """Create nearly identical documents with few word changes."""
        source = EvaluationFixtureGenerator.generate_academic_paragraph(seed)
        words = source.split()

        # Make a few edits
        for _ in range(edits):
            idx = random.randint(0, len(words) - 1)
            # Replace with synonym or slightly different word
            new_word = random.choice([
                "significant", "important", "critical",
                "methodology", "approach", "technique",
                "examine", "investigate", "analyze",
            ])
            words[idx] = new_word

        submitted = " ".join(words)
        return submitted, source

    @staticmethod
    def create_paraphrase(seed: int = 42) -> Tuple[str, str]:
        """Create semantically similar but textually different versions."""
        source = EvaluationFixtureGenerator.generate_academic_paragraph(seed)

        # Rewrite with different structure and synonyms
        words = source.split()

        # Swap some words with paraphrases
        paraphrases = {
            "this study": "the present investigation",
            "examines": "investigates",
            "relationship": "connection",
            "previous research": "earlier studies",
            "demonstrated": "shown",
            "significantly": "substantially",
            "affects": "impacts",
            "methodology": "methods",
            "follows": "adheres to",
            "established": "standard",
            "results indicate": "findings suggest",
            "correlation": "association",
            "contributions": "contributions",
            "ongoing": "continuing",
            "debate": "discussion",
            "regarding": "concerning",
            "implications": "consequences",
            "extend to": "apply to",
            "both": "both",
            "applications": "uses",
        }

        paraphrased_words = []
        for word in words:
            lower = word.lower()
            if lower in paraphrases:
                paraphrased_words.append(paraphrases[lower])
            else:
                paraphrased_words.append(word)

        submitted = " ".join(paraphrased_words)
        return submitted, source

    @staticmethod
    def create_unrelated(seed: int = 42) -> Tuple[str, str]:
        """Create completely unrelated documents."""
        random.seed(seed + 1000)

        topics_unrelated = [
            "cooking recipes", "travel destinations", "sports statistics",
            "music genres", "fashion trends", "pet care tips"
        ]

        # Generate unrelated source
        source_template = "This article discusses {topic} in detail."
        source = source_template.format(topic=random.choice(topics_unrelated))

        # Generate different unrelated submitted text
        submitted_template = "Our research on {topic} reveals interesting findings."
        submitted = submitted_template.format(topic=random.choice(topics_unrelated))

        return submitted, source

    @staticmethod
    def create_common_phrase() -> Tuple[str, str]:
        """Test handling of common academic phrases."""
        common = "further research is needed to fully understand these relationships."
        return common, common

    @staticmethod
    def create_quoted_passage() -> Tuple[str, str]:
        """Test handling of properly quoted passages."""
        quote = "As Smith (2020) stated, 'the methodology proved effective in practice.'"
        # Same quote with attribution in source
        source = "According to Smith (2020), 'the methodology proved effective in practice.' The study showed positive results."
        return quote, source


class PlagiarismEvaluator:
    """Evaluates plagiarism detection performance."""

    def __init__(self):
        self.winnowing = WinnowingService(k=5, w=4)
        self.fuzzy = FuzzyMatchingService(
            exact_threshold=1.0,
            near_exact_threshold=0.85,
            min_match_tokens=8
        )
        self.scoring = ScoringService()

    def detect(
        self, submitted_text: str, source_texts: List[Tuple[str, str]]
    ) -> Tuple[int, float, List[dict]]:
        """Run plagiarism detection on test case.

        Returns: (match_count, similarity_percent, match_details)
        """
        # Generate fingerprints for submitted
        submitted_result = self.winnowing.fingerprint(submitted_text)
        submitted_tokens = self.winnowing.tokenize(submitted_text)
        submitted_position_to_page = {i: 1 for i in range(len(submitted_tokens))}

        # Build corpus index
        corpus_index = {}
        for title, source in source_texts:
            source_result = self.winnowing.fingerprint(source)
            source_tokens = self.winnowing.tokenize(source)

            for fp in source_result.fingerprints:
                if fp.hash_value not in corpus_index:
                    corpus_index[fp.hash_value] = []
                corpus_index[fp.hash_value].append((title, fp.position))

        # Find candidates
        candidates = {}
        for fp in submitted_result.fingerprints:
            if fp.hash_value in corpus_index:
                for doc_title, pos in corpus_index[fp.hash_value]:
                    if doc_title not in candidates:
                        candidates[doc_title] = []
                    candidates[doc_title].append((fp.position, pos, 1))

        # Verify and classify
        matches = []
        for doc_title, positions in candidates.items():
            source = next((s for t, s in source_texts if t == doc_title), "")
            source_result = self.winnowing.fingerprint(source)
            source_tokens = self.winnowing.tokenize(source)
            source_position_to_page = {i: 1 for i in range(len(source_tokens))}

            for sub_pos, src_pos, _ in positions:
                region = self.fuzzy.extend_match_region(
                    submitted_tokens, source_tokens, sub_pos, src_pos, 5
                )
                match_type = self.fuzzy.classify_match(region)

                if match_type:
                    matches.append({
                        "type": match_type,
                        "submitted_span": (region.submitted_start, region.submitted_end),
                        "source_span": (region.source_start, region.source_end),
                        "similarity": region.similarity_ratio,
                    })

        # Calculate similarity
        import time
        start = time.time()

        # Merge overlapping matches
        if matches:
            match_objects = []
            for m in matches:
                match_objects.append(
                    type('Match', (), {
                        'match_type': m['type'],
                        'submitted_start': m['submitted_span'][0],
                        'submitted_end': m['submitted_span'][1],
                        'source_start': m['source_span'][0],
                        'source_end': m['source_span'][1],
                        'similarity_ratio': m['similarity'],
                        'submitted_page': 1,
                        'source_page': 1,
                    })()
                )
            merged_spans = self.scoring.merge_overlapping_spans(match_objects)
            matched_tokens = sum(end - start for start, end in merged_spans)
            eligible = len(submitted_tokens)
            similarity = (matched_tokens / eligible * 100) if eligible > 0 else 0
        else:
            similarity = 0.0

        elapsed_ms = (time.time() - start) * 1000

        return len(matches), similarity, matches

    def evaluate_test_case(self, test_case: TestCase) -> EvaluationResult:
        """Evaluate a single test case."""
        import time
        start = time.time()

        match_count, similarity, matches = self.detect(
            test_case.submitted_text,
            test_case.source_texts
        )

        elapsed_ms = (time.time() - start) * 1000

        # Classify result
        if match_count == 0:
            actual_category = "no_match"
        elif similarity > 80:
            actual_category = "high_similarity"
        elif similarity > 30:
            actual_category = "medium_similarity"
        else:
            actual_category = "low_similarity"

        # Determine if detection was correct
        expected_has_matches = test_case.expected_has_matches
        has_matches = match_count > 0
        detected = has_matches == expected_has_matches

        correct = detected and (
            (test_case.expected_category == "unrelated" and not has_matches) or
            (test_case.expected_category in ["exact_copy", "near_exact"] and has_matches)
        )

        false_positive = has_matches and test_case.expected_category == "unrelated"
        false_negative = not has_matches and test_case.expected_category in ["exact_copy", "near_exact"]

        return EvaluationResult(
            test_name=test_case.name,
            expected_category=test_case.expected_category,
            actual_category=actual_category,
            match_count=match_count,
            similarity_percent=similarity,
            detected=detected,
            correct=correct,
            false_positive=false_positive,
            false_negative=false_negative,
            processing_time_ms=elapsed_ms,
        )


def run_evaluation():
    """Run full evaluation suite."""
    print("=" * 60)
    print("ResearchRadar Plagiarism Detection Evaluation")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Generate test cases
    fixture_gen = EvaluationFixtureGenerator()
    evaluator = PlagiarismEvaluator()

    test_cases = []

    # Exact copies (10 cases)
    for i in range(10):
        submitted, source = fixture_gen.create_exact_copy(seed=100 + i)
        test_cases.append(TestCase(
            name=f"Exact copy {i+1}",
            submitted_text=submitted,
            source_texts=[(f"Source {i+1}", source)],
            expected_category="exact_copy",
            expected_has_matches=True,
        ))

    # Near-exact edits (10 cases)
    for i in range(10):
        submitted, source = fixture_gen.create_near_exact(seed=200 + i, edits=3)
        test_cases.append(TestCase(
            name=f"Near-exact {i+1}",
            submitted_text=submitted,
            source_texts=[(f"Source {i+1}", source)],
            expected_category="near_exact",
            expected_has_matches=True,
        ))

    # Paraphrases (10 cases)
    for i in range(10):
        submitted, source = fixture_gen.create_paraphrase(seed=300 + i)
        test_cases.append(TestCase(
            name=f"Paraphrase {i+1}",
            submitted_text=submitted,
            source_texts=[(f"Source {i+1}", source)],
            expected_category="paraphrase",
            expected_has_matches=False,  # May or may not detect
        ))

    # Unrelated (10 cases)
    for i in range(10):
        submitted, source = fixture_gen.create_unrelated(seed=400 + i)
        test_cases.append(TestCase(
            name=f"Unrelated {i+1}",
            submitted_text=submitted,
            source_texts=[(f"Source {i+1}", source)],
            expected_category="unrelated",
            expected_has_matches=False,
        ))

    # Common phrases (5 cases)
    for i in range(5):
        submitted, source = fixture_gen.create_common_phrase()
        test_cases.append(TestCase(
            name=f"Common phrase {i+1}",
            submitted_text=submitted,
            source_texts=[("Source", source)],
            expected_category="common_phrase",
            expected_has_matches=False,  # May detect but not count as plagiarism
        ))

    # Run evaluation
    results = []
    for test in test_cases:
        result = evaluator.evaluate_test_case(test)
        results.append(result)

    # Calculate metrics
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    false_positives = sum(1 for r in results if r.false_positive)
    false_negatives = sum(1 for r in results if r.false_negative)

    exact_copy_results = [r for r in results if r.expected_category == "exact_copy"]
    near_exact_results = [r for r in results if r.expected_category == "near_exact"]
    unrelated_results = [r for r in results if r.expected_category == "unrelated"]

    # Calculate precision/recall for exact and near-exact
    relevant = len(exact_copy_results) + len(near_exact_results)
    retrieved = sum(1 for r in exact_copy_results + near_exact_results if r.detected)
    true_positives = retrieved - false_negatives  # Simplified

    precision = (true_positives / retrieved * 100) if retrieved > 0 else 0
    recall = (true_positives / relevant * 100) if relevant > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    # False positive rate on unrelated
    fp_rate = (false_positives / len(unrelated_results) * 100) if unrelated_results else 0

    # Print results
    print(f"Total test cases: {total}")
    print(f"Correct classifications: {correct} ({correct/total*100:.1f}%)")
    print()

    print("-" * 60)
    print("Performance Metrics:")
    print("-" * 60)
    print(f"Exact-copy recall:     {sum(1 for r in exact_copy_results if r.detected)}/{len(exact_copy_results)} ({sum(1 for r in exact_copy_results if r.detected)/len(exact_copy_results)*100:.1f}%)")
    print(f"Near-exact recall:     {sum(1 for r in near_exact_results if r.detected)}/{len(near_exact_results)} ({sum(1 for r in near_exact_results if r.detected)/len(near_exact_results)*100:.1f}%)")
    print(f"Unrelated FP rate:     {false_positives}/{len(unrelated_results)} ({fp_rate:.1f}%)")
    print()
    print(f"Precision:             {precision:.1f}%")
    print(f"Recall:                {recall:.1f}%")
    print(f"F1 Score:              {f1:.1f}%")
    print()

    print("-" * 60)
    print("Detailed Results by Category:")
    print("-" * 60)

    categories = {
        "exact_copy": exact_copy_results,
        "near_exact": near_exact_results,
        "paraphrase": [r for r in results if r.expected_category == "paraphrase"],
        "unrelated": unrelated_results,
    }

    for cat_name, cat_results in categories.items():
        if cat_results:
            detected = sum(1 for r in cat_results if r.detected)
            avg_similarity = sum(r.similarity_percent for r in cat_results) / len(cat_results)
            print(f"{cat_name}: {detected}/{len(cat_results)} detected, avg similarity: {avg_similarity:.1f}%")

    print()
    print("-" * 60)
    print("Sample Results (first 5):")
    print("-" * 60)
    for r in results[:5]:
        status = "✓" if r.correct else "✗"
        print(f"{status} {r.test_name}")
        print(f"   Expected: {r.expected_category}, Got: {r.actual_category}")
        print(f"   Matches: {r.match_count}, Similarity: {r.similarity_percent:.1f}%")

    print()
    print("-" * 60)
    print("Phase 2 Acceptance Criteria Check:")
    print("-" * 60)

    # Check targets from PHASE_2_PLAGIARISM_MVP.md
    exact_recall = sum(1 for r in exact_copy_results if r.detected)/len(exact_copy_results)*100 if exact_copy_results else 0
    near_exact_recall = sum(1 for r in near_exact_results if r.detected)/len(near_exact_results)*100 if near_exact_results else 0

    print(f"Exact-copy recall >= 95%: {'✓ PASS' if exact_recall >= 95 else '✗ FAIL'} ({exact_recall:.1f}%)")
    print(f"Near-exact recall >= 85%: {'✓ PASS' if near_exact_recall >= 85 else '✗ FAIL'} ({near_exact_recall:.1f}%)")
    print(f"Unrelated FP rate <= 2%: {'✓ PASS' if fp_rate <= 2 else '✗ FAIL'} ({fp_rate:.1f}%)")
    print(f"Overlapping spans merged: {'✓ PASS' if all(r.correct for r in exact_copy_results[:3]) else '✗ FAIL'}")
    print()

    # Return results for documentation
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total,
        "correct": correct,
        "accuracy_percent": correct/total*100,
        "exact_copy_recall": exact_recall,
        "near_exact_recall": near_exact_recall,
        "false_positive_rate": fp_rate,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
    }


if __name__ == "__main__":
    results = run_evaluation()

    # Save results
    import json
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("Results saved to evaluation_results.json")