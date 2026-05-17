import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from shared.database import get_db
from shared.models import (
    Invoice, InvoiceLine, MaterialMaster, Provider, PriceHistory, User, Document
)
from shared.auth import get_current_user
from shared.schemas import (
    LastPriceResponse, DashboardResponse, SpendingByProviderResponse,
    SpendingByFamilyResponse, PriceHistoryResponse,
)
from shared.exceptions import NotFoundError
from shared.config import get_settings

settings = get_settings()

app = FastAPI(title="Analytics Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "analytics_service"}


@app.get("/analytics/last-price/{material_id}", response_model=List[LastPriceResponse])
async def get_last_price(
    material_id: int,
    provider_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MaterialMaster).where(MaterialMaster.id == material_id)
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("Material", material_id)

    try:
        query_str = """
            SELECT
                material_id,
                provider_id,
                provider_name,
                material_description,
                unit_price_standard,
                standard_unit,
                purchase_date
            FROM last_price_per_material
            WHERE material_id = :material_id
        """
        params = {"material_id": material_id}
        if provider_id:
            query_str += " AND provider_id = :provider_id"
            params["provider_id"] = provider_id
        query_str += " ORDER BY purchase_date DESC"

        result = await db.execute(text(query_str), params)
        rows = result.fetchall()

        return [
            LastPriceResponse(
                material_id=row[0],
                provider_id=row[1],
                provider_name=row[2],
                material_description=row[3],
                unit_price_standard=row[4],
                standard_unit=row[5],
                purchase_date=row[6],
            )
            for row in rows
        ]
    except Exception:
        query = (
            select(
                PriceHistory.material_id,
                PriceHistory.provider_id,
                Provider.fiscal_name.label("provider_name"),
                MaterialMaster.normalized_description.label("material_description"),
                PriceHistory.unit_price_standard,
                PriceHistory.standard_unit,
                PriceHistory.purchase_date,
            )
            .join(Provider, Provider.id == PriceHistory.provider_id)
            .join(MaterialMaster, MaterialMaster.id == PriceHistory.material_id)
            .where(PriceHistory.material_id == material_id)
        )
        if provider_id:
            query = query.where(PriceHistory.provider_id == provider_id)
        query = query.order_by(PriceHistory.purchase_date.desc()).limit(10)

        result = await db.execute(query)
        rows = result.fetchall()

        return [
            LastPriceResponse(
                material_id=row[0],
                provider_id=row[1],
                provider_name=row[2],
                material_description=row[3],
                unit_price_standard=row[4],
                standard_unit=row[5],
                purchase_date=row[6],
            )
            for row in rows
        ]


@app.get("/analytics/price-history/{material_id}", response_model=List[PriceHistoryResponse])
async def get_price_history(
    material_id: int,
    provider_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MaterialMaster).where(MaterialMaster.id == material_id)
    )
    if not result.scalar_one_or_none():
        raise NotFoundError("Material", material_id)

    query = select(PriceHistory).where(PriceHistory.material_id == material_id)

    if provider_id:
        query = query.where(PriceHistory.provider_id == provider_id)
    if date_from:
        query = query.where(PriceHistory.purchase_date >= date_from)
    if date_to:
        query = query.where(PriceHistory.purchase_date <= date_to)

    query = query.order_by(PriceHistory.purchase_date.desc())
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/analytics/materials-stats")
async def get_materials_stats(
    family: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(
            MaterialMaster.id,
            MaterialMaster.master_code,
            MaterialMaster.family,
            MaterialMaster.normalized_description,
            func.count(PriceHistory.id).label("purchase_count"),
            func.sum(PriceHistory.quantity).label("total_quantity"),
            func.avg(PriceHistory.unit_price_standard).label("avg_unit_price"),
        )
        .outerjoin(PriceHistory, PriceHistory.material_id == MaterialMaster.id)
        .where(MaterialMaster.active == True)
        .group_by(
            MaterialMaster.id,
            MaterialMaster.master_code,
            MaterialMaster.family,
            MaterialMaster.normalized_description,
        )
    )

    if family:
        query = query.where(MaterialMaster.family.ilike(f"%{family}%"))
    if date_from:
        query = query.where(PriceHistory.purchase_date >= date_from)
    if date_to:
        query = query.where(PriceHistory.purchase_date <= date_to)

    query = query.order_by(func.count(PriceHistory.id).desc()).limit(limit)
    result = await db.execute(query)
    rows = result.fetchall()

    return [
        {
            "material_id": row[0],
            "master_code": row[1],
            "normalized_description": row[3],
            "invoice_count": row[4] or 0,
            "total_quantity": float(row[5]) if row[5] else 0.0,
            "avg_price": float(row[6]) if row[6] else 0.0,
            "total_spend": float((row[5] or 0) * (row[6] or 0)),
            "currency": "EUR",
        }
        for row in rows
    ]


@app.get("/analytics/provider-comparison/{material_id}")
async def get_provider_comparison(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MaterialMaster).where(MaterialMaster.id == material_id)
    )
    material = result.scalar_one_or_none()
    if not material:
        raise NotFoundError("Material", material_id)

    query = (
        select(
            Provider.id.label("provider_id"),
            Provider.fiscal_name.label("provider_name"),
            func.avg(PriceHistory.unit_price_standard).label("avg_price"),
            func.min(PriceHistory.unit_price_standard).label("min_price"),
            func.max(PriceHistory.unit_price_standard).label("max_price"),
            func.count(PriceHistory.id).label("purchase_count"),
            func.max(PriceHistory.purchase_date).label("last_purchase"),
        )
        .join(PriceHistory, PriceHistory.provider_id == Provider.id)
        .where(PriceHistory.material_id == material_id)
        .group_by(Provider.id, Provider.fiscal_name)
        .order_by(func.avg(PriceHistory.unit_price_standard))
    )

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        {
            "provider_id": row[0],
            "provider_name": row[1],
            "avg_price": float(row[2]) if row[2] else 0.0,
            "min_price": float(row[3]) if row[3] else 0.0,
            "max_price": float(row[4]) if row[4] else 0.0,
            "purchase_count": row[5],
            "last_price": float(row[2]) if row[2] else 0.0,
            "last_date": str(row[6]) if row[6] else None,
        }
        for row in rows
    ]


@app.get("/analytics/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import date, timedelta

    today = date.today()
    current_month_start = today.replace(day=1)

    total_invoices_result = await db.execute(select(func.count(Invoice.id)))
    total_invoices = total_invoices_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.status.in_(["pending_review", "under_review", "rejected"])
        )
    )
    pending_review = pending_result.scalar() or 0

    spend_result = await db.execute(
        select(func.sum(Invoice.total)).where(
            Invoice.status.in_(["approved", "validated"]),
            Invoice.invoice_date >= current_month_start,
        )
    )
    total_spend = float(spend_result.scalar() or 0)

    pending_lines_result = await db.execute(
        select(func.count(InvoiceLine.id)).where(
            InvoiceLine.status.in_(["pending_homologation", "no_match"])
        )
    )
    pending_homologation = pending_lines_result.scalar() or 0

    # Monthly spend for last 6 months
    invoices_by_month = []
    for i in range(5, -1, -1):
        if today.month - i <= 0:
            month_num = today.month - i + 12
            year = today.year - 1
        else:
            month_num = today.month - i
            year = today.year
        month_start = date(year, month_num, 1)
        if month_num == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month_num + 1, 1)

        month_result = await db.execute(
            select(func.sum(Invoice.total), func.count(Invoice.id)).where(
                Invoice.status.in_(["approved", "validated"]),
                Invoice.invoice_date >= month_start,
                Invoice.invoice_date < month_end,
            )
        )
        row = month_result.one()
        invoices_by_month.append({
            "month": month_start.strftime("%Y-%m"),
            "total": float(row[0] or 0),
            "count": row[1] or 0,
        })

    # Spending by provider
    provider_query = (
        select(
            Provider.id,
            Provider.fiscal_name,
            func.sum(Invoice.total).label("total"),
        )
        .join(Invoice, Invoice.provider_id == Provider.id)
        .where(Invoice.status.in_(["approved", "validated"]))
        .group_by(Provider.id, Provider.fiscal_name)
        .order_by(func.sum(Invoice.total).desc())
        .limit(10)
    )
    provider_result = await db.execute(provider_query)
    spending_by_provider = [
        {"provider_id": row[0], "provider_name": row[1], "total": float(row[2] or 0), "percentage": 0.0}
        for row in provider_result.fetchall()
    ]
    # Compute percentages
    all_provider_total = sum(p["total"] for p in spending_by_provider)
    if all_provider_total > 0:
        for p in spending_by_provider:
            p["percentage"] = round(p["total"] / all_provider_total * 100, 1)

    # Recent documents
    recent_docs_result = await db.execute(
        select(Document)
        .where(Document.status != "deleted")
        .order_by(Document.upload_date.desc())
        .limit(5)
    )
    recent_docs = []
    for doc in recent_docs_result.scalars().all():
        s = doc.status
        if s == "pages_extracted":
            s = "processing"
        recent_docs.append({
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.filename,
            "file_size": doc.file_size,
            "page_count": doc.page_count,
            "status": s,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "uploaded_by": doc.upload_user_id,
            "detected_count": 0,
        })

    return {
        "total_invoices": total_invoices,
        "pending_review": pending_review,
        "total_spent_this_month": total_spend,
        "pending_homologation": pending_homologation,
        "invoices_by_month": invoices_by_month,
        "spending_by_provider": spending_by_provider,
        "recent_documents": recent_docs,
    }


@app.get("/analytics/spending-by-provider", response_model=List[SpendingByProviderResponse])
async def get_spending_by_provider(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(
            Provider.id,
            Provider.fiscal_name,
            func.sum(Invoice.total).label("total_spend"),
            func.count(Invoice.id).label("invoice_count"),
        )
        .join(Invoice, Invoice.provider_id == Provider.id)
        .where(Invoice.status.in_(["approved", "validated"]))
        .group_by(Provider.id, Provider.fiscal_name)
        .order_by(func.sum(Invoice.total).desc())
    )

    if date_from:
        query = query.where(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.where(Invoice.invoice_date <= date_to)

    result = await db.execute(query)
    rows = result.fetchall()

    return [
        SpendingByProviderResponse(
            provider_id=row[0],
            provider_name=row[1],
            total_spend=row[2] or Decimal("0"),
            invoice_count=row[3],
        )
        for row in rows
    ]


@app.get("/analytics/spending-by-family", response_model=List[SpendingByFamilyResponse])
async def get_spending_by_family(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(
            MaterialMaster.family,
            func.sum(InvoiceLine.subtotal).label("total_spend"),
            func.count(InvoiceLine.id).label("line_count"),
        )
        .join(PriceHistory, PriceHistory.invoice_line_id == InvoiceLine.id)
        .join(MaterialMaster, MaterialMaster.id == PriceHistory.material_id)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .where(Invoice.status.in_(["approved", "validated"]))
        .where(MaterialMaster.family.isnot(None))
        .group_by(MaterialMaster.family)
        .order_by(func.sum(InvoiceLine.subtotal).desc())
    )

    if date_from:
        query = query.where(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.where(Invoice.invoice_date <= date_to)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        {
            "family_id": i + 1,
            "family_name": row[0] or "Desconocida",
            "total": float(row[1] or 0),
            "percentage": 0.0,
        }
        for i, row in enumerate(rows)
    ]
    grand_total = sum(p["total"] for p in items)
    if grand_total > 0:
        for p in items:
            p["percentage"] = round(p["total"] / grand_total * 100, 1)
    return items


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
