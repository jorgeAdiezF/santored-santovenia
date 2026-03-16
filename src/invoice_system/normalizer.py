from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class ProductNormalizer:
    def __init__(self, similarity_threshold: float = 0.85) -> None:
        self.similarity_threshold = similarity_threshold

    def pick_canonical_name(self, raw_description: str, known_canonicals: list[str]) -> str:
        candidate = normalize_text(raw_description)
        if not known_canonicals:
            return candidate

        scored = [
            (SequenceMatcher(None, candidate, known).ratio(), known)
            for known in known_canonicals
        ]
        score, best = max(scored, key=lambda item: item[0])
        if score >= self.similarity_threshold:
            return best
        return candidate
