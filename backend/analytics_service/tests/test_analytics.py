"""
Tests for the Analytics Service HTTP endpoints.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import date

from shared.models import (
    Invoice, InvoiceLine, MaterialMaster, Provider, PriceHistory
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_provider(
    db: AsyncSession,
    fiscal_name: str = "Proveedor SA",
    tax_id: str | None = None,
) -> Provider:
    provider = Provider(
        fiscal_name=fiscal_name,
        tax_id=tax_id,
        active=True,
    )
    db.add(provider)
    await db.flush()
    return provider


async def _create_material(
    db: AsyncSession,
    master_code: str = "MAT-001",
    description: str = "Acero S275",
    family: str = "Aceros",
) -> MaterialMaster:
    material = MaterialMaster(
        master_code=master_code,
        normalized_description=description,
        family=family,
        active=True,
    )
    db.add(material)
    await db.flush()
    return material


async def _create_invoice(
    db: AsyncSession,
    provider: Provider,
    status: str = "validated",
    total: str = "1000.00",
    invoice_date: date = date(2025, 1, 10),
    invoice_number: str = "INV-001",
) -> Invoice:
    invoice = Invoice(
        provider_id=provider.id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        total=Decimal(total),
        currency="EUR",
        status=status,
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def _create_line(
    db: AsyncSession,
    invoice: Invoice,
    subtotal: str = "100.00",
    status: str = "homologated",
    line_number: int = 1,
) -> InvoiceLine:
    line = InvoiceLine(
        invoice_id=invoice.id,
        line_number=line_number,
        original_description="Acero",
        quantity="1.00",
        unit="kg",
        unit_price=Decimal(subtotal),
        subtotal=Decimal(subtotal),
        status=status,
        extraction_confidence=0.9,
    )
    db.add(line)
    await db.flush()
    return line


async def _create_price_history(
    db: AsyncSession,
    material: MaterialMaster,
    provider: Provider,
    invoice_line: InvoiceLine | None = None,
    unit_price: str = "2.50",
    purchase_date: date = date(2025, 1, 10),
) -> PriceHistory:
    ph = PriceHistory(
        material_id=material.id,
        provider_id=provider.id,
        invoice_line_id=invoice_line.id if invoice_line else None,
        unit_price_original=Decimal(unit_price),
        unit="kg",
        unit_price_standard=Decimal(unit_price),
        standard_unit="kg",
        quantity=Decimal("10.00"),
        purchase_date=purchase_date,
    )
    db.add(ph)
    await db.flush()
    return ph


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_dashboard_empty(client: AsyncClient, db_session: AsyncSession):
    """Dashboard with no data should return zeros."""
    response = await client.get("/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_invoices" in data
    assert "pending_review" in data
    assert "validated_this_month" in data
    assert "pending_homologation_lines" in data
    assert data["total_invoices"] == 0
    assert data["pending_review"] == 0


async def test_dashboard(client: AsyncClient, db_session: AsyncSession):
    """Dashboard stats reflect actual DB content."""
    provider = await _create_provider(db_session)
    await _create_invoice(
        db_session, provider, status="pending_review", invoice_number="INV-D1"
    )
    await _create_invoice(
        db_session, provider, status="validated", invoice_number="INV-D2"
    )

    response = await client.get("/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_invoices"] >= 2
    assert data["pending_review"] >= 1


async def test_last_price_not_found(client: AsyncClient, db_session: AsyncSession):
    """Requesting last price for a non-existent material returns 404."""
    response = await client.get("/analytics/last-price/999")
    assert response.status_code == 404


async def test_last_price_empty(client: AsyncClient, db_session: AsyncSession):
    """Existing material with no price history returns an empty list."""
    material = await _create_material(db_session, master_code="MAT-NOPRICE")

    response = await client.get(f"/analytics/last-price/{material.id}")
    assert response.status_code == 200
    assert response.json() == []


async def test_last_price_with_data(client: AsyncClient, db_session: AsyncSession):
    """Existing material with price history returns entries."""
    provider = await _create_provider(db_session, tax_id="T001")
    material = await _create_material(db_session, master_code="MAT-PRICE")
    invoice = await _create_invoice(
        db_session, provider, status="validated", invoice_number="INV-LP"
    )
    line = await _create_line(db_session, invoice)
    await _create_price_history(db_session, material, provider, line)

    response = await client.get(f"/analytics/last-price/{material.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["material_id"] == material.id


async def test_price_history_empty(client: AsyncClient, db_session: AsyncSession):
    """Price history for a material with no records returns empty list."""
    material = await _create_material(db_session, master_code="MAT-HIST")

    response = await client.get(f"/analytics/price-history/{material.id}")
    assert response.status_code == 200
    assert response.json() == []


async def test_price_history_not_found(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/analytics/price-history/99999")
    assert response.status_code == 404


async def test_spending_by_provider(client: AsyncClient, db_session: AsyncSession):
    """Spending by provider returns a list (may be empty when no validated invoices)."""
    response = await client.get("/analytics/spending-by-provider")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_spending_by_provider_with_data(
    client: AsyncClient, db_session: AsyncSession
):
    provider = await _create_provider(db_session, fiscal_name="Aceros Finos SA", tax_id="B11111111")
    await _create_invoice(
        db_session,
        provider,
        status="validated",
        total="5000.00",
        invoice_number="INV-SP",
    )

    response = await client.get("/analytics/spending-by-provider")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    provider_ids = [item["provider_id"] for item in data]
    assert provider.id in provider_ids


async def test_spending_by_family(client: AsyncClient, db_session: AsyncSession):
    """Spending by family returns a list (may be empty)."""
    response = await client.get("/analytics/spending-by-family")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
