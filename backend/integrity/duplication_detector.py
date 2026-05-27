"""
YieldLens Duplication Detector Module
Implements advanced SequenceMatcher and n-gram text comparison algorithms
to prevent template duplication, copied credit memos, and generic statements.
"""

import difflib
import logging

from database.cache import cache

logger = logging.getLogger("YieldLens.Integrity.Duplication")


class DuplicationDetector:
    """Detects repeated content, metrics, recommendations, and template plagiarism."""

    @classmethod
    def get_shingle_set(cls, text: str, n: int = 3) -> set:
        """Helper to tokenize text and extract character n-gram shingles for robust similarity."""
        clean_text = "".join(c.lower() for c in text if c.isalnum() or c.isspace())
        words = clean_text.split()
        if len(words) < n:
            return set(words)
        return set(" ".join(words[i : i + n]) for i in range(len(words) - n + 1))

    @classmethod
    def calculate_similarity(cls, text_a: str, text_b: str) -> float:
        """
        Calculates exact text similarity using a combination of SequenceMatcher ratio
        and Jaccard similarity on word 3-shingles to detect structural duplication.
        """
        if not text_a or not text_b:
            return 0.0

        # 1. Standard SequenceMatcher ratio
        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        ratio = matcher.ratio()

        # 2. Shingle Jaccard overlap
        set_a = cls.get_shingle_set(text_a)
        set_b = cls.get_shingle_set(text_b)

        if not set_a or not set_b:
            return ratio

        union = set_a.union(set_b)
        intersection = set_a.intersection(set_b)
        jaccard = len(intersection) / len(union)

        # Return the maximum score of the two to be conservative
        return max(ratio, jaccard)

    @classmethod
    def check_uniqueness(cls, text: str, category: str, ticker: str) -> dict:
        """
        Compares new text against previously stored historical and session results for the category.
        If similarity exceeds 30%, returns success=False to trigger regeneration.
        """
        if not text or len(text.strip()) < 50:
            return {
                "success": True,
                "similarity": 0.0,
                "reason": "Text too short for comparison",
            }

        cache_key = f"integrity_history_{category}"
        history = cache.get(cache_key) or {}

        max_similarity = 0.0
        offending_ticker = None
        matched_phrase = ""

        # Compare against all other companies in history
        for other_ticker, old_text in history.items():
            if other_ticker == ticker:
                continue

            sim = cls.calculate_similarity(text, old_text)
            if sim > max_similarity:
                max_similarity = sim
                offending_ticker = other_ticker

                # Extract a sample of matching phrases
                matcher = difflib.SequenceMatcher(None, text[:300], old_text[:300])
                match = matcher.find_longest_match(
                    0, min(300, len(text)), 0, min(300, len(old_text))
                )
                if match.size > 10:
                    matched_phrase = text[match.a : match.a + match.size].strip()

        # Register this new output into history
        history[ticker] = text
        cache.set(cache_key, history, ttl=86400)  # Persist rolling history for 24h

        threshold = 0.30  # 30% similarity limit
        is_unique = max_similarity <= threshold

        if not is_unique:
            logger.warning(
                f"[Integrity Alert] Plagiarism/Template repetition detected for {ticker} in category '{category}'! "
                f"Similarity with {offending_ticker} is {max_similarity * 100:.1f}% (exceeds {threshold * 100:.0f}% limit)."
            )

        return {
            "success": is_unique,
            "similarity_score": round(max_similarity, 4),
            "threshold": threshold,
            "compared_against": offending_ticker,
            "offending_phrase": matched_phrase,
            "message": (
                "Unique content verified"
                if is_unique
                else f"Content too similar to {offending_ticker} ({max_similarity*100:.1f}%)"
            ),
        }
