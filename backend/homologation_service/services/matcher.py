import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz, process as fuzz_process

AUTO_ASSIGN_THRESHOLD = 0.85
MANUAL_REVIEW_THRESHOLD = 0.5

DIMENSION_PATTERNS = [
    re.compile(r"\b(\d+)\s*[xX×]\s*(\d+)\s*(?:[xX×]\s*(\d+))?\b"),
    re.compile(r"\b(?:HEA|HEB|HEM|IPE|UPN|INP|IPN|L)\s*(\d+)\b", re.IGNORECASE),
    re.compile(r"\b(\d+(?:[.,]\d+)?)\s*[mM][mM]\b"),
    re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:mm|cm|m)\b", re.IGNORECASE),
]

UNIT_NORMALIZERS = {
    "kg": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
    "t": "t", "tn": "t", "ton": "t", "tonelada": "t",
    "m": "m", "ml": "m", "metro": "m", "metros": "m",
    "m2": "m2", "m²": "m2",
    "m3": "m3", "m³": "m3",
    "ud": "ud", "uds": "ud", "unidad": "ud", "unidades": "ud", "pcs": "ud",
    "l": "l", "lt": "l", "litro": "l", "litros": "l",
}


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\d\-\./×xX]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_dimensions(text: str) -> List[str]:
    """Extract dimension strings from text."""
    dims = []
    for pattern in DIMENSION_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            if isinstance(match, tuple):
                dim = "x".join(str(m) for m in match if m)
            else:
                dim = str(match)
            dims.append(dim.lower())
    return dims


def dimension_similarity(text1: str, text2: str) -> float:
    """Calculate similarity based on dimensions."""
    dims1 = set(extract_dimensions(text1))
    dims2 = set(extract_dimensions(text2))

    if not dims1 and not dims2:
        return 0.5
    if not dims1 or not dims2:
        return 0.0

    intersection = dims1.intersection(dims2)
    union = dims1.union(dims2)

    return len(intersection) / len(union) if union else 0.0


def fuzzy_similarity(text1: str, text2: str) -> float:
    """Calculate fuzzy string similarity."""
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    if not norm1 or not norm2:
        return 0.0

    ratio = fuzz.token_set_ratio(norm1, norm2) / 100.0
    partial = fuzz.partial_ratio(norm1, norm2) / 100.0

    return 0.7 * ratio + 0.3 * partial


def tfidf_similarity(query: str, candidates: List[str]) -> List[float]:
    """Calculate TF-IDF cosine similarity between query and candidates."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        texts = [normalize_text(query)] + [normalize_text(c) for c in candidates]
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=1,
        )
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            query_vec = tfidf_matrix[0:1]
            candidate_vecs = tfidf_matrix[1:]
            similarities = cosine_similarity(query_vec, candidate_vecs)[0]
            return similarities.tolist()
        except ValueError:
            return [0.0] * len(candidates)
    except ImportError:
        return [fuzzy_similarity(query, c) for c in candidates]


def combined_score(
    description: str,
    candidate_description: str,
    candidate_dimensions: str = None,
    supplier_code: str = None,
    candidate_supplier_code: str = None,
) -> float:
    """Calculate combined matching score."""
    fuzzy_score = fuzzy_similarity(description, candidate_description)

    dim_score = 0.0
    if candidate_dimensions:
        dim_score = dimension_similarity(description, candidate_dimensions)
    else:
        dim_score = dimension_similarity(description, candidate_description)

    code_score = 0.0
    if supplier_code and candidate_supplier_code:
        code_score = fuzzy_similarity(supplier_code, candidate_supplier_code)

    if supplier_code and candidate_supplier_code:
        score = 0.5 * fuzzy_score + 0.2 * dim_score + 0.3 * code_score
    else:
        score = 0.7 * fuzzy_score + 0.3 * dim_score

    return min(score, 1.0)


def rank_candidates(
    description: str,
    supplier_code: Optional[str],
    materials: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Rank material candidates by similarity to invoice line description.
    Returns top_k candidates with confidence scores.
    """
    if not materials:
        return []

    candidate_descriptions = [m["normalized_description"] for m in materials]

    tfidf_scores = tfidf_similarity(description, candidate_descriptions)

    scored = []
    for i, material in enumerate(materials):
        fuzzy_score = fuzzy_similarity(description, material["normalized_description"])
        dim_score = dimension_similarity(description, material.get("dimensions", "") or "")

        code_score = 0.0
        if supplier_code:
            for alias in material.get("aliases", []):
                alias_code = alias.get("supplier_code", "")
                if alias_code:
                    alias_score = fuzzy_similarity(supplier_code, alias_code)
                    code_score = max(code_score, alias_score)

                alias_desc = alias.get("supplier_description", "")
                if alias_desc:
                    alias_desc_score = fuzzy_similarity(description, alias_desc)
                    fuzzy_score = max(fuzzy_score, alias_desc_score * 0.9)

        tfidf_score = tfidf_scores[i] if i < len(tfidf_scores) else 0.0

        if supplier_code and code_score > 0:
            final_score = 0.35 * fuzzy_score + 0.25 * dim_score + 0.25 * code_score + 0.15 * tfidf_score
        else:
            final_score = 0.45 * fuzzy_score + 0.3 * dim_score + 0.25 * tfidf_score

        scored.append({
            "material_id": material["id"],
            "master_code": material["master_code"],
            "normalized_description": material["normalized_description"],
            "family": material.get("family"),
            "confidence": round(min(final_score, 1.0), 4),
        })

    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return scored[:top_k]


def should_auto_assign(confidence: float) -> bool:
    """Determine if a match should be auto-assigned."""
    return confidence >= AUTO_ASSIGN_THRESHOLD


def needs_manual_review(confidence: float) -> bool:
    """Determine if a match needs manual review."""
    return MANUAL_REVIEW_THRESHOLD <= confidence < AUTO_ASSIGN_THRESHOLD
