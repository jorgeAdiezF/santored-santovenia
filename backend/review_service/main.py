import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone

from shared.database import get_db
from shared.models import Invoice, InvoiceLine, MaterialMaster, MaterialAlias, PriceHistory, User
from shared.auth import get_current_user
from shared.schemas import (
    InvoiceResponse, InvoiceUpdate, InvoiceLineResponse, InvoiceLineUpdate,
    HomologationAssign, MessageResponse,
)
from shared.exceptions import NotFoundError, BadRequestError
from shared.config import get_settings
from shared.audit import record_audit

settings = get_settings()

app = FastAPI(title="Review Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "review_service"}


@app.get("/reviews/invoices/pending", response_model=List[InvoiceResponse])
async def list_pending_invoices(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.provider),
            selectinload(Invoice.lines),
        )
        .where(Invoice.status.in_(["pending_review", "under_review", "rejected"]))
        .order_by(Invoice.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@app.get("/reviews/invoices/{invoice_id}")
async def get_invoice_detail(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Invoice", invoice_id)

    return {
        "id": invoice.id,
        "detected_doc_id": invoice.detected_doc_id,
        "provider_id": invoice.provider_id,
        "tax_id": invoice.tax_id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": str(invoice.invoice_date) if invoice.invoice_date else None,
        "subtotal": str(invoice.subtotal) if invoice.subtotal else None,
        "vat": str(invoice.vat) if invoice.vat else None,
        "total": str(invoice.total) if invoice.total else None,
        "currency": invoice.currency,
        "status": invoice.status,
        "validated_at": invoice.validated_at.isoformat() if invoice.validated_at else None,
        "validated_by": invoice.validated_by,
        "lines": [
            {
                "id": line.id,
                "line_number": line.line_number,
                "supplier_code": line.supplier_code,
                "original_description": line.original_description,
                "quantity": str(line.quantity) if line.quantity else None,
                "unit": line.unit,
                "unit_price": str(line.unit_price) if line.unit_price else None,
                "discount": str(line.discount) if line.discount else None,
                "subtotal": str(line.subtotal) if line.subtotal else None,
                "tax_rate": str(line.tax_rate) if line.tax_rate else None,
                "status": line.status,
                "extraction_confidence": line.extraction_confidence,
            }
            for line in invoice.lines
        ],
    }


@app.put("/reviews/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Invoice", invoice_id)

    update_fields = invoice_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(invoice, field, value)

    await db.flush()
    await record_audit(db, "update", "invoice", invoice.id, current_user.id,
                       new_value=update_fields)
    return invoice


@app.put("/reviews/invoices/{invoice_id}/lines/{line_id}", response_model=InvoiceLineResponse)
async def update_invoice_line(
    invoice_id: int,
    line_id: int,
    line_data: InvoiceLineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InvoiceLine).where(
            InvoiceLine.id == line_id,
            InvoiceLine.invoice_id == invoice_id,
        )
    )
    line = result.scalar_one_or_none()
    if not line:
        raise NotFoundError("InvoiceLine", line_id)

    line_update_fields = line_data.model_dump(exclude_unset=True)
    for field, value in line_update_fields.items():
        setattr(line, field, value)

    await db.flush()
    await record_audit(db, "update", "invoice_line", line.id, current_user.id,
                       new_value=line_update_fields)
    return line


@app.post("/reviews/invoices/{invoice_id}/finalize", response_model=InvoiceResponse)
async def finalize_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice).options(selectinload(Invoice.lines)).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Invoice", invoice_id)

    if invoice.status not in ("pending_review", "rejected"):
        raise BadRequestError(f"Invoice cannot be finalized from status '{invoice.status}'")

    if not invoice.provider_id:
        raise BadRequestError("Invoice must have a provider assigned before finalizing")

    if not invoice.invoice_number:
        raise BadRequestError("Invoice must have a valid invoice number before finalizing")

    pending_lines = [l for l in invoice.lines if l.status == "pending_homologation"]
    if pending_lines:
        raise BadRequestError(
            f"Invoice has {len(pending_lines)} line(s) still pending homologation"
        )

    # Arithmetic check: subtotal + vat should be within 1% of total
    if invoice.subtotal is not None and invoice.vat is not None and invoice.total is not None:
        from decimal import Decimal
        computed = invoice.subtotal + invoice.vat
        diff = abs(computed - invoice.total)
        tolerance = invoice.total * Decimal("0.01") if invoice.total else Decimal("0.01")
        if diff > tolerance:
            raise BadRequestError(
                f"Invoice arithmetic mismatch: subtotal ({invoice.subtotal}) + vat ({invoice.vat}) "
                f"= {computed}, but total is {invoice.total}"
            )

    invoice.status = "validated"
    invoice.validated_at = datetime.now(timezone.utc)
    invoice.validated_by = current_user.id

    await db.flush()
    await record_audit(db, "validate", "invoice", invoice.id, current_user.id,
                       new_value={"status": "validated"})
    return invoice


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@app.post("/reviews/invoices/{invoice_id}/reject", response_model=InvoiceResponse)
async def reject_invoice(
    invoice_id: int,
    body: Optional[RejectRequest] = None,
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise NotFoundError("Invoice", invoice_id)

    effective_reason = reason or (body.reason if body else None)
    invoice.status = "rejected"
    await db.flush()
    await record_audit(db, "reject", "invoice", invoice.id, current_user.id,
                       new_value={"status": "rejected"}, notes=effective_reason)
    return invoice


@app.get("/reviews/homologation/pending", response_model=List[InvoiceLineResponse])
async def list_pending_homologation_review(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InvoiceLine)
        .where(InvoiceLine.status.in_(["pending_homologation", "pending_review", "no_match"]))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@app.put("/reviews/lines/{line_id}/homologate", response_model=InvoiceLineResponse)
async def assign_material_to_line(
    line_id: int,
    assign_data: HomologationAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InvoiceLine).where(InvoiceLine.id == line_id))
    line = result.scalar_one_or_none()
    if not line:
        raise NotFoundError("InvoiceLine", line_id)

    result = await db.execute(
        select(MaterialMaster).where(MaterialMaster.id == assign_data.material_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise NotFoundError("Material", assign_data.material_id)

    line.status = "homologated"

    result = await db.execute(select(Invoice).where(Invoice.id == line.invoice_id))
    invoice = result.scalar_one_or_none()

    if invoice and invoice.invoice_date and line.unit_price is not None:
        price_entry = PriceHistory(
            material_id=assign_data.material_id,
            provider_id=invoice.provider_id or 1,
            invoice_line_id=line.id,
            unit_price_original=line.unit_price,
            unit=line.unit,
            unit_price_standard=line.unit_price,
            standard_unit=line.unit,
            quantity=line.quantity,
            purchase_date=invoice.invoice_date,
        )
        db.add(price_entry)

    if line.supplier_code or line.original_description:
        alias = MaterialAlias(
            material_id=assign_data.material_id,
            provider_id=invoice.provider_id if invoice else None,
            supplier_code=line.supplier_code,
            supplier_description=line.original_description,
            confidence=assign_data.confidence or 1.0,
        )
        db.add(alias)

    await db.flush()
    await record_audit(db, "homologate", "invoice_line", line.id, current_user.id,
                       new_value={"material_id": assign_data.material_id, "status": "homologated"})
    return line


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
