import sys
import os
import hashlib
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date

import aio_pika

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "document_service"}


async def publish_to_queue(queue_name: str, message: dict) -> None:
    try:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(queue_name, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue_name,
            )
    except Exception as e:
        print(f"Warning: Failed to publish to queue {queue_name}: {str(e)}")


@app.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()

    file_hash = hashlib.sha256(content).hexdigest()

    existing = await db.execute(select(Document).where(Document.file_hash == file_hash))
    if existing.scalar_one_or_none():
        raise ConflictError(f"Document with hash {file_hash} already exists")

    file_type = file.content_type or "application/octet-stream"
    file_size = len(content)
    filename = file.filename or "unknown"

    object_name = f"documents/originals/{file_hash}/{filename}"
    upload_bytes(
        object_name=object_name,
        data=content,
        content_type=file_type,
    )

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
                page = Page(
                    document_id=document.id,
                    page_number=page_number,
                    image_path=image_path,
                )
                db.add(page)
            document.page_count = len(page_paths)
            document.status = "pages_extracted"
        except Exception as e:
            print(f"Warning: Failed to extract pages: {str(e)}")

    await db.flush()

    await publish_to_queue("segmentation_jobs", {
        "document_id": document.id,
        "filename": filename,
        "file_hash": file_hash,
    })

    return document


@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Document)

    if status:
        query = query.where(Document.status == status)
    if date_from:
        query = query.where(Document.upload_date >= date_from)
    if date_to:
        query = query.where(Document.upload_date <= date_to)

    query = query.order_by(Document.upload_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise NotFoundError("Document", document_id)
    return document


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
