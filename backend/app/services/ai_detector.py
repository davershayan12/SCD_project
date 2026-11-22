"""AI-text likelihood detector using perplexity and burstiness (distilgpt2).

Principles:
- Uses a small causal LM (distilgpt2, MIT/Apache) to compute token perplexity.
- Lower perplexity and low variance (burstiness) indicate machine-generated text.
- Caches scores by text hash to avoid re-scoring.
- Never gives a definitive verdict ("AI-written"), but an "AI-likelihood indicator" with caveats.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from typing import Any, Dict, List, Optional
import torch

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIDetectorService:
    """Service for computing per-paragraph AI likelihood scores."""

    DISCLAIMER = (
        "AI-likelihood is a statistical indicator, not proof of authorship. "
        "It can be wrong, especially for non-native English writing and formal academic text."
    )

    def __init__(
        self,
        model_name: Optional[str] = None,
        min_words: Optional[int] = None,
        max_tokens: Optional[int] = None,
    ):
        self.model_name = model_name or settings.ai_detector_model
        self.min_words = min_words or settings.ai_detector_min_words
        self.max_tokens = max_tokens or settings.ai_detector_max_tokens
        self._tokenizer = None
        self._model = None
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _load_model(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        try:
            import os
            # Ensure Hugging Face cache is directed to D:\hf_cache if configured
            if "HF_HOME" not in os.environ:
                os.environ["HF_HOME"] = "D:\\hf_cache"

            from transformers import AutoTokenizer, AutoModelForCausalLM

            logger.info("Loading AI detector model '%s'...", self.model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self._model.eval()
        except Exception as e:
            logger.error("Failed to load AI detector model: %s", e)
            raise RuntimeError(f"Failed to load AI detector model '{self.model_name}': {str(e)}")

    def _compute_block_score(self, text: str) -> Dict[str, float]:
        self._load_model()
        assert self._tokenizer is not None
        assert self._model is not None

        # Tokenize text
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_tokens,
        )
        input_ids = inputs["input_ids"]
        if input_ids.shape[1] < 5:
            return {"perplexity": 0.0, "burstiness": 0.0, "score": 0.0}

        with torch.no_grad():
            outputs = self._model(**inputs, labels=input_ids)
            loss = outputs.loss
            perplexity = math.exp(min(float(loss), 20.0))

        # Compute simple sentence burstiness (variance of sentence lengths / perplexities)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        if len(sentences) > 1:
            sent_lens = [len(s.split()) for s in sentences]
            mean_len = sum(sent_lens) / len(sent_lens)
            variance = sum((l - mean_len) ** 2 for l in sent_lens) / len(sent_lens)
            burstiness = math.sqrt(variance) / (mean_len + 1e-5)
        else:
            burstiness = 0.5

        # Heuristic mapping: lower perplexity (< 15) and lower burstiness suggest AI text (0-100 score)
        # Human text typically has higher perplexity (> 25) and higher burstiness.
        p_score = max(0.0, min(100.0, (50.0 - perplexity) * 2.0))
        b_score = max(0.0, min(100.0, (0.5 - burstiness) * 100.0))
        combined = (p_score * 0.7) + (b_score * 0.3)
        score = max(0.0, min(100.0, combined))

        return {
            "perplexity": round(perplexity, 2),
            "burstiness": round(burstiness, 2),
            "score": round(score, 1),
        }

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze document text paragraph by paragraph for AI likelihood."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        analyzed_paragraphs = []
        total_score = 0.0
        scored_count = 0

        for idx, para in enumerate(paragraphs):
            words = para.split()
            word_count = len(words)

            if word_count < self.min_words:
                analyzed_paragraphs.append({
                    "index": idx,
                    "text": para,
                    "word_count": word_count,
                    "status": "Too short to assess",
                    "score": 0.0,
                })
                continue

            # Check cache by text hash
            h = hashlib.sha256(para.encode("utf-8")).hexdigest()
            if h in self._cache:
                metrics = self._cache[h]
            else:
                try:
                    metrics = self._compute_block_score(para)
                    self._cache[h] = metrics
                except Exception as e:
                    logger.warning("AI scoring failed for paragraph: %s", e)
                    metrics = {"perplexity": 0.0, "burstiness": 0.0, "score": 0.0}

            score = metrics["score"]
            total_score += score
            scored_count += 1

            # Categorize likelihood band
            if score >= 70:
                band = "High"
            elif score >= 40:
                band = "Medium"
            else:
                band = "Low"

            analyzed_paragraphs.append({
                "index": idx,
                "text": para,
                "word_count": word_count,
                "status": "Assessed",
                "score": score,
                "likelihood_band": band,
                "metrics": metrics,
            })

        overall_score = (total_score / scored_count) if scored_count > 0 else 0.0

        if overall_score >= 70:
            overall_band = "High"
        elif overall_score >= 40:
            overall_band = "Medium"
        else:
            overall_band = "Low"

        return {
            "overall_score": round(overall_score, 1),
            "overall_likelihood_band": overall_band,
            "status": "completed" if scored_count > 0 else "insufficient_text",
            "paragraphs": analyzed_paragraphs,
            "disclaimer": self.DISCLAIMER,
        }
