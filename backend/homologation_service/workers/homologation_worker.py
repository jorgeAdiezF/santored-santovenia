import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from celery import Celery
from shared.config import get_settings

settings = get_settings()

celery_app = Celery(
    "homologation_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="homologation_worker.homologate_lines", bind=True, max_retries=3)
def homologate_lines(self, invoice_id: int, line_ids: list):
    """Batch homologation of invoice lines."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from shared.models import InvoiceLine, MaterialMaster, MaterialAlias, PriceHistory, Invoice
    from services.matcher import rank_candidates, should_auto_assign

    async def _run():
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            result = await session.execute(
                select(MaterialMaster).where(MaterialMaster.active == True)
            )
            all_materials = result.scalars().all()

            result_aliases = await session.execute(select(MaterialAlias))
            aliases = result_aliases.scalars().all()

            alias_map = {}
            for alias in aliases:
                if alias.material_id not in alias_map:
                    alias_map[alias.material_id] = []
                alias_map[alias.material_id].append({
                    "supplier_code": alias.supplier_code,
                    "supplier_description": alias.supplier_description,
                    "provider_id": alias.provider_id,
                })

            materials_data = []
            for m in all_materials:
                materials_data.append({
                    "id": m.id,
                    "master_code": m.master_code,
                    "normalized_description": m.normalized_description,
                    "family": m.family,
                    "dimensions": m.dimensions,
                    "aliases": alias_map.get(m.id, []),
                })

            auto_assigned = 0
            needs_review = 0
            no_match = 0

            for line_id in line_ids:
                result = await session.execute(
                    select(InvoiceLine).where(InvoiceLine.id == line_id)
                )
                line = result.scalar_one_or_none()
                if not line or not line.original_description:
                    no_match += 1
                    continue

                candidates = rank_candidates(
                    description=line.original_description,
                    supplier_code=line.supplier_code,
                    materials=materials_data,
                    top_k=5,
                )

                if candidates and should_auto_assign(candidates[0]["confidence"]):
                    best = candidates[0]
                    line.status = "homologated"

                    invoice_result = await session.execute(
                        select(Invoice).where(Invoice.id == line.invoice_id)
                    )
                    invoice = invoice_result.scalar_one_or_none()

                    if invoice and invoice.invoice_date:
                        price_entry = PriceHistory(
                            material_id=best["material_id"],
                            provider_id=invoice.provider_id or 1,
                            invoice_line_id=line.id,
                            unit_price_original=line.unit_price or 0,
                            unit=line.unit,
                            unit_price_standard=line.unit_price,
                            standard_unit=line.unit,
                            quantity=line.quantity,
                            purchase_date=invoice.invoice_date,
                        )
                        session.add(price_entry)

                    existing_alias = False
                    for alias in alias_map.get(best["material_id"], []):
                        if alias.get("supplier_code") == line.supplier_code:
                            existing_alias = True
                            break

                    if not existing_alias and (line.supplier_code or line.original_description):
                        new_alias = MaterialAlias(
                            material_id=best["material_id"],
                            provider_id=invoice.provider_id if invoice else None,
                            supplier_code=line.supplier_code,
                            supplier_description=line.original_description,
                            confidence=best["confidence"],
                        )
                        session.add(new_alias)

                    auto_assigned += 1
                elif candidates and candidates[0]["confidence"] >= 0.5:
                    line.status = "pending_review"
                    needs_review += 1
                else:
                    line.status = "no_match"
                    no_match += 1

            await session.commit()

            return {
                "invoice_id": invoice_id,
                "total_lines": len(line_ids),
                "auto_assigned": auto_assigned,
                "needs_review": needs_review,
                "no_match": no_match,
            }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="homologation_worker.auto_homologate_all", bind=True)
def auto_homologate_all(self):
    """Auto-homologate all pending lines."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select
    from shared.models import InvoiceLine

    async def _get_pending():
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            result = await session.execute(
                select(InvoiceLine).where(InvoiceLine.status == "pending_homologation")
            )
            lines = result.scalars().all()
            invoice_lines_map = {}
            for line in lines:
                if line.invoice_id not in invoice_lines_map:
                    invoice_lines_map[line.invoice_id] = []
                invoice_lines_map[line.invoice_id].append(line.id)
            return invoice_lines_map

    invoice_lines_map = asyncio.run(_get_pending())

    results = []
    for invoice_id, line_ids in invoice_lines_map.items():
        result = homologate_lines.delay(invoice_id, line_ids)
        results.append(result.id)

    return {"dispatched_jobs": len(results), "job_ids": results}
