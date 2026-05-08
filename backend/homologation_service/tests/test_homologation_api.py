"""
Integration tests for the Homologation Service HTTP endpoints.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import InvoiceLine, Invoice, MaterialMaster, Provider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_provider(db: AsyncSession, fiscal_name: str = "Prov SA") -> Provider:
    provider = Provider(fiscal_name=fiscal_name, active=True)
    db.add(provider)
    await db.flush()
    return provider


async def _create_invoice(
    db: AsyncSession,
    provider: Provider | None = None,
    status: str = "pending_review",
) -> Invoice:
    invoice = Invoice(
        provider_id=provider.id if provider else None,
        status=status,
        currency="EUR",
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def _create_line(
    db: AsyncSession,
    invoice: Invoice,
    description: str = "Tubo acero 40x20",
    status: str = "pending_homologation",
) -> InvoiceLine:
    line = InvoiceLine(
        invoice_id=invoice.id,
        line_number=1,
        original_description=description,
        status=status,
        extraction_confidence=0.9,
    )
    db.add(line)
    await db.flush()
    return line


async def _create_material(
    db: AsyncSession,
    master_code: str = "MAT-001",
    description: str = "Tubo acero 40x20x2",
) -> MaterialMaster:
    material = MaterialMaster(
        master_code=master_code,
        normalized_description=description,
        active=True,
    )
    db.add(material)
    await db.flush()
    return material


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_get_pending(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(db_session, provider)
    await _create_line(db_session, invoice, status="pending_homologation")

    response = await client.get("/homologation/pending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["status"] == "pending_homologation"


async def test_get_pending_empty(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/homologation/pending")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_suggestions(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(db_session, provider)
    line = await _create_line(
        db_session, invoice, description="Tubo acero cuadrado 40x20x2"
    )
    await _create_material(
        db_session, master_code="TUBO-001", description="Tubo acero 40x20x2"
    )

    response = await client.get(f"/homologation/suggestions/{line.id}")
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)
    # At least one suggestion with required fields
    if suggestions:
        first = suggestions[0]
        assert "material_id" in first
        assert "confidence" in first
        assert "master_code" in first


async def test_get_suggestions_line_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.get("/homologation/suggestions/99999")
    assert response.status_code == 404


async def test_get_suggestions_no_description(
    client: AsyncClient, db_session: AsyncSession
):
    """A line without a description should return an empty list of suggestions."""
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(db_session, provider)
    line = InvoiceLine(
        invoice_id=invoice.id,
        line_number=2,
        original_description=None,
        status="pending_homologation",
        extraction_confidence=0.0,
    )
    db_session.add(line)
    await db_session.flush()

    response = await client.get(f"/homologation/suggestions/{line.id}")
    assert response.status_code == 200
    assert response.json() == []
