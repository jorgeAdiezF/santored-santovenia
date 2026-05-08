"""
Tests for the Review Service HTTP endpoints.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from shared.models import Invoice, InvoiceLine, Provider


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
    invoice_number: str = "INV-001",
) -> Invoice:
    invoice = Invoice(
        provider_id=provider.id if provider else None,
        invoice_number=invoice_number,
        invoice_date=date(2025, 1, 15),
        total="1500.00",
        currency="EUR",
        status=status,
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def _create_line(
    db: AsyncSession,
    invoice: Invoice,
    status: str = "homologated",
    line_number: int = 1,
) -> InvoiceLine:
    line = InvoiceLine(
        invoice_id=invoice.id,
        line_number=line_number,
        original_description="Acero S275",
        quantity="10.00",
        unit="kg",
        unit_price="1.50",
        subtotal="15.00",
        status=status,
        extraction_confidence=0.95,
    )
    db.add(line)
    await db.flush()
    return line


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_get_pending_invoices(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(db_session)
    await _create_invoice(db_session, provider, status="pending_review", invoice_number="INV-P1")

    response = await client.get("/reviews/invoices/pending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(inv["status"] == "pending_review" for inv in data)


async def test_get_pending_invoices_empty(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/reviews/invoices/pending")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_invoice(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(db_session, provider, invoice_number="INV-DETAIL")
    await _create_line(db_session, invoice)

    response = await client.get(f"/reviews/invoices/{invoice.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == invoice.id
    assert data["invoice_number"] == "INV-DETAIL"
    assert "lines" in data
    assert isinstance(data["lines"], list)


async def test_invoice_not_found(client: AsyncClient, db_session: AsyncSession):
    response = await client.get("/reviews/invoices/999")
    assert response.status_code == 404


async def test_update_invoice_header(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(
        db_session, provider, invoice_number="INV-UPDATE"
    )

    payload = {"invoice_number": "INV-UPDATED", "currency": "USD"}
    response = await client.put(f"/reviews/invoices/{invoice.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["invoice_number"] == "INV-UPDATED"
    assert data["currency"] == "USD"


async def test_finalize_invoice(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(
        db_session, provider, status="pending_review", invoice_number="INV-FINAL"
    )
    # All lines must be in a non-pending status to allow finalization
    await _create_line(db_session, invoice, status="homologated")

    response = await client.post(f"/reviews/invoices/{invoice.id}/finalize")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validated"


async def test_finalize_invoice_with_pending_lines(
    client: AsyncClient, db_session: AsyncSession
):
    """Finalization should be blocked when lines are still pending homologation."""
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(
        db_session, provider, status="pending_review", invoice_number="INV-BLOCK"
    )
    await _create_line(db_session, invoice, status="pending_homologation")

    response = await client.post(f"/reviews/invoices/{invoice.id}/finalize")
    assert response.status_code == 400


async def test_reject_invoice(client: AsyncClient, db_session: AsyncSession):
    provider = await _create_provider(db_session)
    invoice = await _create_invoice(
        db_session, provider, status="pending_review", invoice_number="INV-REJ"
    )

    response = await client.post(f"/reviews/invoices/{invoice.id}/reject")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


async def test_reject_invoice_not_found(client: AsyncClient, db_session: AsyncSession):
    response = await client.post("/reviews/invoices/99999/reject")
    assert response.status_code == 404
