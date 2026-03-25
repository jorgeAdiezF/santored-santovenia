import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional

from shared.database import get_db
from shared.models import Document, DetectedDoc, User
from shared.auth import get_current_user
from shared.schemas import DetectedDocResponse, DetectedDocUpdate, SegmentMergeRequest, SegmentSplitRequest, JobResponse, MessageResponse
from shared.exceptions import NotFoundError, BadRequestError
from shared.config import get_settings

settings = get_settings()

app = FastAPI(title="Segmentation Service", version="1.0.0")

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
        "segmentation",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "segmentation_service"}


@app.post("/segmentation/{document_id}", response_model=JobResponse)
async def trigger_segmentation(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document", document_id)

    celery_app = get_celery_app()
    task = celery_app.send_task(
        "segmentation_worker.segment_document",
        args=[document_id],
    )

    return JobResponse(
        job_id=task.id,
        status="queued",
        message=f"Segmentation job queued for document {document_id}",
    )


@app.get("/segmentation/jobs/{job_id}", response_model=JobResponse)
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


@app.get("/documents/{document_id}/segments", response_model=List[DetectedDocResponse])
async def list_segments(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("Document", document_id)

    result = await db.execute(
        select(DetectedDoc)
        .where(DetectedDoc.document_id == document_id)
        .order_by(DetectedDoc.start_page)
    )
    return result.scalars().all()


@app.put("/segments/{segment_id}", response_model=DetectedDocResponse)
async def update_segment(
    segment_id: int,
    segment_data: DetectedDocUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DetectedDoc).where(DetectedDoc.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise NotFoundError("Segment", segment_id)

    if segment_data.start_page is not None:
        segment.start_page = segment_data.start_page
    if segment_data.end_page is not None:
        segment.end_page = segment_data.end_page
    if segment_data.status is not None:
        segment.status = segment_data.status

    if segment.start_page > segment.end_page:
        raise BadRequestError("start_page cannot be greater than end_page")

    await db.flush()
    return segment


@app.post("/segments/{segment_id}/confirm", response_model=DetectedDocResponse)
async def confirm_segment(
    segment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DetectedDoc).where(DetectedDoc.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise NotFoundError("Segment", segment_id)

    segment.status = "confirmed"
    segment.confidence = 1.0
    await db.flush()
    return segment


@app.post("/segments/merge", response_model=DetectedDocResponse)
async def merge_segments(
    merge_request: SegmentMergeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result1 = await db.execute(
        select(DetectedDoc).where(DetectedDoc.id == merge_request.segment_id_1)
    )
    segment1 = result1.scalar_one_or_none()
    if not segment1:
        raise NotFoundError("Segment", merge_request.segment_id_1)

    result2 = await db.execute(
        select(DetectedDoc).where(DetectedDoc.id == merge_request.segment_id_2)
    )
    segment2 = result2.scalar_one_or_none()
    if not segment2:
        raise NotFoundError("Segment", merge_request.segment_id_2)

    if segment1.document_id != segment2.document_id:
        raise BadRequestError("Cannot merge segments from different documents")

    merged_start = min(segment1.start_page, segment2.start_page)
    merged_end = max(segment1.end_page, segment2.end_page)

    segment1.start_page = merged_start
    segment1.end_page = merged_end
    segment1.status = "merged"
    segment1.confidence = min(segment1.confidence, segment2.confidence)

    await db.delete(segment2)
    await db.flush()
    return segment1


@app.post("/segments/{segment_id}/split", response_model=List[DetectedDocResponse])
async def split_segment(
    segment_id: int,
    split_request: SegmentSplitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DetectedDoc).where(DetectedDoc.id == segment_id))
    segment = result.scalar_one_or_none()
    if not segment:
        raise NotFoundError("Segment", segment_id)

    split_page = split_request.split_at_page
    if split_page <= segment.start_page or split_page > segment.end_page:
        raise BadRequestError(
            f"split_at_page {split_page} must be between {segment.start_page + 1} and {segment.end_page}"
        )

    original_end = segment.end_page
    segment.end_page = split_page - 1
    segment.status = "split"

    new_segment = DetectedDoc(
        document_id=segment.document_id,
        start_page=split_page,
        end_page=original_end,
        status="detected",
        confidence=segment.confidence,
    )
    db.add(new_segment)
    await db.flush()

    return [segment, new_segment]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
