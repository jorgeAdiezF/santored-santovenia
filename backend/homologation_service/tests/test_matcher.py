"""
Unit tests for the matcher service (no HTTP, pure function-level tests).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from services.matcher import (
    fuzzy_similarity,
    extract_dimensions,
    rank_candidates,
    should_auto_assign,
    normalize_text,
    dimension_similarity,
)


# ---------------------------------------------------------------------------
# normalize_text
# ---------------------------------------------------------------------------

async def test_normalize_text_lowercases():
    assert normalize_text("ACERO S275") == "acero s275"


async def test_normalize_text_strips_whitespace():
    assert normalize_text("  acero  ") == "acero"


# ---------------------------------------------------------------------------
# fuzzy_similarity
# ---------------------------------------------------------------------------

async def test_exact_match():
    score = fuzzy_similarity("tubo acero 40x20x2", "tubo acero 40x20x2")
    assert score == pytest.approx(1.0, abs=0.01)


async def test_fuzzy_match_high_confidence():
    score = fuzzy_similarity("tubo acero 40x20x2", "Tubo Acero 40x20x2mm")
    assert score >= 0.7, f"Expected >= 0.7, got {score}"


async def test_no_match():
    score = fuzzy_similarity("tubo acero cuadrado", "chapa aluminio pulido")
    assert score < 0.5, f"Expected < 0.5, got {score}"


async def test_empty_strings_return_zero():
    assert fuzzy_similarity("", "acero") == 0.0
    assert fuzzy_similarity("acero", "") == 0.0


# ---------------------------------------------------------------------------
# extract_dimensions
# ---------------------------------------------------------------------------

async def test_dimension_extraction_profile():
    dims = extract_dimensions("HEA 200")
    # Should capture "200" from the HEA pattern
    assert any("200" in d for d in dims), f"Dims returned: {dims}"


async def test_dimension_extraction_tube():
    dims = extract_dimensions("tubo 40x20x2")
    # The cross-section pattern should match and produce "40x20x2"
    assert any("40" in d for d in dims), f"Dims returned: {dims}"
    joined = "".join(dims)
    assert "20" in joined and "2" in joined


async def test_dimension_extraction_no_dims():
    dims = extract_dimensions("acero inoxidable")
    assert dims == []


async def test_dimension_extraction_mm():
    dims = extract_dimensions("chapa 3mm grosor")
    assert len(dims) >= 1


# ---------------------------------------------------------------------------
# dimension_similarity
# ---------------------------------------------------------------------------

async def test_dimension_similarity_same_profile():
    score = dimension_similarity("HEA 200", "perfil HEA 200")
    assert score > 0.0


async def test_dimension_similarity_no_dims_both():
    # Both texts lack dimension tokens → returns 0.5 (neutral)
    score = dimension_similarity("acero inoxidable", "acero negro")
    assert score == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------------------
# rank_candidates
# ---------------------------------------------------------------------------

async def test_suggest_candidates_sorted_by_confidence():
    materials = [
        {
            "id": 1,
            "master_code": "A",
            "normalized_description": "tubo acero 40x20x2",
            "family": "Tubos",
            "dimensions": "40x20x2",
            "aliases": [],
        },
        {
            "id": 2,
            "master_code": "B",
            "normalized_description": "chapa aluminio 1mm",
            "family": "Chapas",
            "dimensions": "1mm",
            "aliases": [],
        },
        {
            "id": 3,
            "master_code": "C",
            "normalized_description": "tubo acero cuadrado 40x40",
            "family": "Tubos",
            "dimensions": "40x40",
            "aliases": [],
        },
    ]
    candidates = rank_candidates(
        description="tubo acero 40x20x2",
        supplier_code=None,
        materials=materials,
        top_k=3,
    )
    assert len(candidates) <= 3
    # Must be sorted descending by confidence
    confidences = [c["confidence"] for c in candidates]
    assert confidences == sorted(confidences, reverse=True)
    # The closest match should be at the top
    assert candidates[0]["master_code"] == "A"


async def test_suggest_candidates_empty_materials():
    result = rank_candidates("tubo acero", None, [], top_k=5)
    assert result == []


async def test_suggest_candidates_respects_top_k():
    materials = [
        {
            "id": i,
            "master_code": f"M{i}",
            "normalized_description": f"material numero {i}",
            "family": "Test",
            "dimensions": None,
            "aliases": [],
        }
        for i in range(10)
    ]
    result = rank_candidates("material", None, materials, top_k=3)
    assert len(result) <= 3


# ---------------------------------------------------------------------------
# should_auto_assign
# ---------------------------------------------------------------------------

async def test_should_auto_assign_above_threshold():
    assert should_auto_assign(0.9) is True


async def test_should_auto_assign_below_threshold():
    assert should_auto_assign(0.7) is False


async def test_should_auto_assign_at_threshold():
    # 0.85 is the AUTO_ASSIGN_THRESHOLD — should return True (>=)
    assert should_auto_assign(0.85) is True
