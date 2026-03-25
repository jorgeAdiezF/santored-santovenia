import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from shared.database import get_db
from shared.models import DetectedDoc, Invoice, InvoiceLine, User
from shared.auth import get_current_user
from shared.schemas import JobResponse, InvoiceResponse, MessageResponse
from shared.exceptions import NotFoundError
from shared.config import get_settings

settings = get_settings()

app = FastAPI(title="OCR Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_celery_app():
    from celery import Celery
    return Celery(
        "ocr",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ocr_service"}


@app.post("/ocr/{segment_id}", response_model=JobResponse)
async def trigger_ocr(
    segment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DetectedDoc).where(DetectedDoc.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise NotFoundError("Segment", segment_id)

    celery_app = get_celery_app()
    task = celery_app.send_task(
        "ocr_worker.process_segment",
        args=[segment.document_id, segment_id],
    )

    return JobResponse(
        job_id=task.id,
        status="queued",
        message=f"OCR job queued for segment {segment_id}",
    )


@app.get("/ocr/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    celery_app = get_celery_app()
    task = celery_app.AsyncResult(job_id)

    return JobResponse(
        job_id=job_id,
        status=task.status.lower(),
        message=str(task.result) if task.ready() else None,
    )


@app.get("/ocr/{segment_id}/result")
async def get_ocr_result(
    segment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DetectedDoc).where(DetectedDoc.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise NotFoundError("Segment", segment_id)

    result = await db.execute(
        select(Invoice).where(Invoice.detected_doc_id == segment_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        return {
            "segment_id": segment_id,
            "status": segment.status,
            "invoice": None,
            "lines": [],
        }

    result = await db.execute(
        select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)
    )
    lines = result.scalars().all()

    return {
        "segment_id": segment_id,
        "status": segment.status,
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": str(invoice.invoice_date) if invoice.invoice_date else None,
            "tax_id": invoice.tax_id,
            "provider_id": invoice.provider_id,
            "subtotal": str(invoice.subtotal) if invoice.subtotal else None,
            "vat": str(invoice.vat) if invoice.vat else None,
            "total": str(invoice.total) if invoice.total else None,
            "currency": invoice.currency,
            "status": invoice.status,
        },
        "lines": [
            {
                "id": line.id,
                "line_number": line.line_number,
                "supplier_code": line.supplier_code,
                "original_description": line.original_description,
                "quantity": str(line.quantity) if line.quantity else None,
                "unit": line.unit,
                "unit_price": str(line.unit_price) if line.unit_price else None,
                "subtotal": str(line.subtotal) if line.subtotal else None,
                "status": line.status,
                "extraction_confidence": line.extraction_confidence,
            }
            for line in lines
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
