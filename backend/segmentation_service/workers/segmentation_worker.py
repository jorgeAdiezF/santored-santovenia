import sys
import os
import json
import re
import io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from celery import Celery
from shared.config import get_settings

settings = get_settings()

celery_app = Celery(
    "segmentation_worker",
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


def download_pages_from_minio(document_id: int) -> list:
    """Download all page images for a document from MinIO."""
    from minio import Minio
    client = Minio(
        settings.minio_url,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    pages = []
    prefix = f"documents/{document_id}/pages/"
    try:
        objects = list(client.list_objects(settings.minio_bucket, prefix=prefix))
        objects.sort(key=lambda x: x.object_name)
        for obj in objects:
            response = client.get_object(settings.minio_bucket, obj.object_name)
            data = response.read()
            response.close()
            response.release_conn()
            page_num = int(re.search(r"page_(\d+)", obj.object_name).group(1))
            pages.append((page_num, data, obj.object_name))
    except Exception as e:
        print(f"Error downloading pages: {str(e)}")
    return pages


def extract_text_from_image(image_bytes: bytes) -> str:
    """Use pytesseract to extract text from an image."""
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="spa+eng")
        return text
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return ""


def detect_invoice_boundaries(pages_text: list) -> list:
    """
    Heuristic detection of invoice boundaries.
    Returns list of (start_page, end_page, confidence) tuples.
    """
    invoice_number_pattern = re.compile(
        r"(?:factura|invoice|fra|n[uú]m|n[oº])[:\s\.]*[\w\-/]+",
        re.IGNORECASE
    )
    tax_id_pattern = re.compile(
        r"\b[A-Z]\d{7}[A-Z0-9]\b|\b\d{8}[A-Z]\b",
        re.IGNORECASE
    )
    date_pattern = re.compile(
        r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b"
    )

    if not pages_text:
        return []

    segments = []
    current_start = 1
    prev_tax_id = None
    prev_invoice_num = None

    for i, (page_num, text) in enumerate(pages_text):
        tax_ids = tax_id_pattern.findall(text)
        invoice_nums = invoice_number_pattern.findall(text)
        has_date = bool(date_pattern.search(text))

        current_tax_id = tax_ids[0].upper() if tax_ids else None
        current_invoice_num = invoice_nums[0] if invoice_nums else None

        is_new_invoice = False
        confidence = 0.5

        if i > 0:
            if current_tax_id and prev_tax_id and current_tax_id != prev_tax_id:
                is_new_invoice = True
                confidence = 0.9
            elif current_invoice_num and prev_invoice_num and current_invoice_num != prev_invoice_num:
                is_new_invoice = True
                confidence = 0.8
            elif current_invoice_num and has_date and i > 0:
                total_pattern = re.compile(r"total[:\s]*[\d\.,]+", re.IGNORECASE)
                if total_pattern.search(pages_text[i - 1][1]):
                    is_new_invoice = True
                    confidence = 0.75

        if is_new_invoice and i > 0:
            segments.append((current_start, page_num - 1, confidence))
            current_start = page_num

        if current_tax_id:
            prev_tax_id = current_tax_id
        if current_invoice_num:
            prev_invoice_num = current_invoice_num

    if pages_text:
        last_page = pages_text[-1][0]
        if not segments or current_start <= last_page:
            segments.append((current_start, last_page, 0.7))

    if not segments and pages_text:
        segments = [(1, pages_text[-1][0], 0.5)]

    return segments


def publish_ocr_job(document_id: int, segment_id: int) -> None:
    """Publish an OCR job to the queue."""
    import aio_pika
    import asyncio

    async def _publish():
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel()
                await channel.declare_queue("ocr_jobs", durable=True)
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps({
                            "document_id": document_id,
                            "segment_id": segment_id,
                        }).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key="ocr_jobs",
                )
        except Exception as e:
            print(f"Warning: Failed to publish OCR job: {str(e)}")

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_publish())
    except RuntimeError:
        asyncio.run(_publish())


@celery_app.task(name="segmentation_worker.segment_document", bind=True, max_retries=3)
def segment_document(self, document_id: int):
    """Main segmentation task."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select, update
    from shared.models import Document, Page, DetectedDoc

    async def _run():
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            if not document:
                return {"error": f"Document {document_id} not found"}

            await session.execute(
                update(Document).where(Document.id == document_id).values(status="segmenting")
            )
            await session.commit()

            pages = download_pages_from_minio(document_id)
            if not pages:
                result = await session.execute(
                    select(Page).where(Page.document_id == document_id).order_by(Page.page_number)
                )
                db_pages = result.scalars().all()
                pages = [(p.page_number, b"", p.image_path) for p in db_pages]
                pages_text = [(p.page_number, "") for p in db_pages]
            else:
                pages_text = []
                for page_num, image_bytes, _ in pages:
                    text = extract_text_from_image(image_bytes)
                    pages_text.append((page_num, text))

            boundaries = detect_invoice_boundaries(pages_text)

            segment_ids = []
            for start_page, end_page, confidence in boundaries:
                detected_doc = DetectedDoc(
                    document_id=document_id,
                    start_page=start_page,
                    end_page=end_page,
                    status="detected",
                    confidence=confidence,
                )
                session.add(detected_doc)
                await session.flush()
                segment_ids.append(detected_doc.id)

            await session.execute(
                update(Document).where(Document.id == document_id).values(status="segmented")
            )
            await session.commit()

            for segment_id in segment_ids:
                publish_ocr_job(document_id, segment_id)

            return {
                "document_id": document_id,
                "segments_created": len(segment_ids),
                "segment_ids": segment_ids,
            }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
