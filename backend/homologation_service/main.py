import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date

from shared.database import get_db
from shared.models import InvoiceLine, MaterialMaster, MaterialAlias, PriceHistory, Invoice, User
from shared.auth import get_current_user
from shared.schemas import (
    HomologationSuggestion, HomologationAssign, InvoiceLineResponse,
    MessageResponse, JobResponse,
)
from shared.exceptions import NotFoundError, BadRequestError
from shared.config import get_settings

from services.matcher import rank_candidates, should_auto_assign

settings = get_settings()

app = FastAPI(title="Homologation Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_celery_app():
    from celery import Celery
    return Celery(
        "homologation",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "homologation_service"}


@app.post("/homologation/{line_id}", response_model=MessageResponse)
async def manually_link_line(
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
    return MessageResponse(message=f"Line {line_id} linked to material {assign_data.material_id}")


@app.get("/homologation/pending", response_model=List[InvoiceLineResponse])
async def list_pending_homologation(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InvoiceLine)
        .options(selectinload(InvoiceLine.destinations))
        .where(InvoiceLine.status.in_(["pending_homologation", "no_match"]))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@app.get("/homologation/suggestions/{line_id}", response_model=List[HomologationSuggestion])
async def get_suggestions(
    line_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(InvoiceLine).where(InvoiceLine.id == line_id))
    line = result.scalar_one_or_none()
    if not line:
        raise NotFoundError("InvoiceLine", line_id)

    if not line.original_description:
        return []

    result = await db.execute(
        select(MaterialMaster).where(MaterialMaster.active == True)
    )
    all_materials = result.scalars().all()

    result_aliases = await db.execute(select(MaterialAlias))
    aliases = result_aliases.scalars().all()

    alias_map = {}
    for alias in aliases:
        if alias.material_id not in alias_map:
            alias_map[alias.material_id] = []
        alias_map[alias.material_id].append({
            "supplier_code": alias.supplier_code,
            "supplier_description": alias.supplier_description,
        })

    materials_data = [
        {
            "id": m.id,
            "master_code": m.master_code,
            "normalized_description": m.normalized_description,
            "family": m.family,
            "dimensions": m.dimensions,
            "aliases": alias_map.get(m.id, []),
        }
        for m in all_materials
    ]

    candidates = rank_candidates(
        description=line.original_description,
        supplier_code=line.supplier_code,
        materials=materials_data,
        top_k=5,
    )

    return [HomologationSuggestion(**c) for c in candidates]


@app.post("/homologation/auto", response_model=JobResponse)
async def trigger_auto_homologation(
    current_user: User = Depends(get_current_user),
):
    celery_app = get_celery_app()
    task = celery_app.send_task("homologation_worker.auto_homologate_all")

    return JobResponse(
        job_id=task.id,
        status="queued",
        message="Auto-homologation job dispatched for all pending lines",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
