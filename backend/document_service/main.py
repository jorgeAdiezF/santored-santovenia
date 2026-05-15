import sys
import os
import hashlib
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date

from celery import Celery

from shared.database import get_db
from shared.models import Document, Page, DetectedDoc, User
from shared.auth import get_current_user
from shared.schemas import DocumentResponse, PageResponse, DetectedDocResponse, MessageResponse
from shared.exceptions import NotFoundError, ConflictError, StorageError
from shared.config import get_settings

from services.storage import upload_bytes, get_presigned_url
from services.pdf_processor import process_document_pages, get_page_count_from_pdf

settings = get_settings()

app = FastAPI(title="Document Service", version="1.0.0")

celery_app = Celery(broker=settings.celery_broker_url, backend=settings.celery_result_backend)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "document_service"}


def trigger_segmentation(document_id: int) -> None:
    try:
        celery_app.send_task(
            "segmentation_worker.segment_document",
            args=[document_id],
            queue="segmentation",
        )
    except Exception as e:
        print(f"Warning: Failed to trigger segmentation for document {document_id}: {e}")


@app.post("/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = []
    for file in files:
        content = await file.read()

        file_hash = hashlib.sha256(content).hexdigest()

        existing = await db.execute(select(Document).where(Document.file_hash == file_hash))
        if existing.scalar_one_or_none():
            continue

        file_type = file.content_type or "application/octet-stream"
        file_size = len(content)
        filename = file.filename or "unknown"

        object_name = f"documents/originals/{file_hash}/{filename}"
        upload_bytes(object_name=object_name, data=content, content_type=file_type)

        page_count = 0
        if file_type == "application/pdf" or filename.lower().endswith(".pdf"):
            page_count = get_page_count_from_pdf(content)

        document = Document(
            file_hash=file_hash,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=object_name,
            upload_user_id=current_user.id,
            status="uploaded",
            page_count=page_count if page_count > 0 else None,
        )
        db.add(document)
        await db.flush()

        if file_type == "application/pdf" or filename.lower().endswith(".pdf"):
            try:
                page_paths = process_document_pages(document.id, content)
                for page_number, image_path in page_paths:
                    page = Page(document_id=document.id, page_number=page_number, image_path=image_path)
                    db.add(page)
                document.page_count = len(page_paths)
                document.status = "pages_extracted"
            except Exception as e:
                print(f"Warning: Failed to extract pages: {str(e)}")

        await db.flush()
        trigger_segmentation(document.id)

        upload_date = document.upload_date.isoformat() if document.upload_date else None
        results.append({
            "id": document.id,
            "filename": document.filename,
            "original_filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "storage_path": document.storage_path,
            "file_path": document.storage_path,
            "upload_user_id": document.upload_user_id,
            "uploaded_by": document.upload_user_id,
            "upload_date": upload_date,
            "created_at": upload_date,
            "updated_at": upload_date,
            "status": "processing" if document.status == "pages_extracted" else document.status,
            "page_count": document.page_count,
            "pages": [],
            "detected_docs": [],
            "processed_at": None,
            "error_message": None,
        })

    return results


@app.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    doc_status: Optional[str] = Query(None, alias="status"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base_query = select(Document).where(Document.status != "deleted")

    if doc_status:
        db_status = "pages_extracted" if doc_status == "processing" else doc_status
        base_query = base_query.where(Document.status == db_status)
    if date_from:
        base_query = base_query.where(Document.upload_date >= date_from)
    if date_to:
        base_query = base_query.where(Document.upload_date <= date_to)
    if search:
        base_query = base_query.where(Document.filename.ilike(f"%{search}%"))

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * size
    data_query = (
        base_query
        .options(selectinload(Document.detected_docs))
        .order_by(Document.upload_date.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(data_query)
    documents = result.scalars().all()

    items = []
    for doc in documents:
        s = doc.status
        if s == "pages_extracted":
            s = "processing"
        items.append({
            "id": doc.id,
            "filename": doc.filename,
            "original_filename": doc.filename,
            "file_size": doc.file_size,
            "page_count": doc.page_count,
            "status": s,
            "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
            "uploaded_by": doc.upload_user_id,
            "upload_user_id": doc.upload_user_id,
            "detected_count": len(doc.detected_docs) if doc.detected_docs else 0,
            "created_at": doc.upload_date.isoformat() if doc.upload_date else None,
        })

    total_pages = max(1, (total + size - 1) // size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": total_pages}


@app.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.pages), selectinload(Document.detected_docs))
        .where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document", document_id)

    upload_date = document.upload_date.isoformat() if document.upload_date else None
    status = "processing" if document.status == "pages_extracted" else document.status
    return {
        "id": document.id,
        "filename": document.filename,
        "original_filename": document.filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "storage_path": document.storage_path,
        "file_path": document.storage_path,
        "upload_user_id": document.upload_user_id,
        "uploaded_by": document.upload_user_id,
        "upload_date": upload_date,
        "created_at": upload_date,
        "updated_at": upload_date,
        "status": status,
        "page_count": document.page_count,
        "pages": [{"id": p.id, "document_id": p.document_id, "page_number": p.page_number, "image_path": p.image_path} for p in document.pages],
        "detected_docs": [{"id": d.id, "document_id": d.document_id, "start_page": d.start_page, "end_page": d.end_page, "page_start": d.start_page, "page_end": d.end_page, "status": d.status, "confidence": d.confidence, "doc_type": "invoice", "created_at": None, "updated_at": None} for d in document.detected_docs],
        "processed_at": None,
        "error_message": None,
    }


@app.get("/documents/{document_id}/pages/{page_number}")
async def get_page_url(
    document_id: int,
    page_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Page).where(
            Page.document_id == document_id,
            Page.page_number == page_number,
        )
    )
    page = result.scalar_one_or_none()
    if not page:
        raise NotFoundError("Page", page_number)

    try:
        url = get_presigned_url(page.image_path)
    except Exception:
        url = f"/minio/{page.image_path}"

    return {"page_number": page_number, "url": url, "image_path": page.image_path}


@app.delete("/documents/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document", document_id)

    document.status = "deleted"
    await db.flush()

    return MessageResponse(message=f"Document {document_id} deleted successfully")


@app.get("/documents/{document_id}/segments", response_model=List[DetectedDocResponse])
async def get_document_segments(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document", document_id)

    result = await db.execute(
        select(DetectedDoc).where(DetectedDoc.document_id == document_id)
    )
    return result.scalars().all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
