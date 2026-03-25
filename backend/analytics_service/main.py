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
    Invoice, InvoiceLine, MaterialMaster, Provider, PriceHistory, User
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
    allow_origins=["*"],
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
            "family": row[2],
            "normalized_description": row[3],
            "purchase_count": row[4] or 0,
            "total_quantity": str(row[5]) if row[5] else "0",
            "avg_unit_price": str(row[6]) if row[6] else None,
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

    return {
        "material_id": material_id,
        "material_description": material.normalized_description,
        "providers": [
            {
                "provider_id": row[0],
                "provider_name": row[1],
                "avg_price": str(row[2]) if row[2] else None,
                "min_price": str(row[3]) if row[3] else None,
                "max_price": str(row[4]) if row[4] else None,
                "purchase_count": row[5],
                "last_purchase": str(row[6]) if row[6] else None,
            }
            for row in rows
        ],
    }


@app.get("/analytics/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_invoices_result = await db.execute(select(func.count(Invoice.id)))
    total_invoices = total_invoices_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.status == "pending_review")
    )
    pending_review = pending_result.scalar() or 0

    from datetime import date
    current_month_start = date.today().replace(day=1)
    validated_month_result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.status == "validated",
            Invoice.validated_at >= current_month_start,
        )
    )
    validated_this_month = validated_month_result.scalar() or 0

    spend_result = await db.execute(
        select(func.sum(Invoice.total)).where(
            Invoice.status == "validated",
            Invoice.invoice_date >= current_month_start,
        )
    )
    total_spend = spend_result.scalar()

    pending_lines_result = await db.execute(
        select(func.count(InvoiceLine.id)).where(
            InvoiceLine.status == "pending_homologation"
        )
    )
    pending_homologation_lines = pending_lines_result.scalar() or 0

    return DashboardResponse(
        total_invoices=total_invoices,
        pending_review=pending_review,
        validated_this_month=validated_this_month,
        total_spend_this_month=total_spend,
        pending_homologation_lines=pending_homologation_lines,
    )


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
        .where(Invoice.status == "validated")
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
        .where(Invoice.status == "validated")
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

    return [
        SpendingByFamilyResponse(
            family=row[0] or "Unknown",
            total_spend=row[1] or Decimal("0"),
            line_count=row[2],
        )
        for row in rows
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
