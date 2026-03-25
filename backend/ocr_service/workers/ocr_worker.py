import sys
import os
import io
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from celery import Celery
from shared.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ocr_worker",
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


def download_segment_pages(document_id: int, start_page: int, end_page: int) -> list:
    """Download pages for a segment from MinIO."""
    from minio import Minio
    client = Minio(
        settings.minio_url,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    pages = []
    for page_num in range(start_page, end_page + 1):
        object_name = f"documents/{document_id}/pages/page_{page_num:04d}.png"
        try:
            response = client.get_object(settings.minio_bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            pages.append((page_num, data))
        except Exception as e:
            print(f"Could not download page {page_num}: {str(e)}")
    return pages


def run_ocr_on_pages(pages: list) -> str:
    """Run OCR on all pages and combine text."""
    import pytesseract
    from PIL import Image

    full_text = []
    for page_num, image_bytes in pages:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image, lang="spa+eng", config="--psm 6")
            full_text.append(text)
        except Exception as e:
            print(f"OCR error on page {page_num}: {str(e)}")
            full_text.append("")

    return "\n".join(full_text)


def find_or_create_provider(session, tax_id: str, provider_name: str = None):
    """Find existing provider by tax_id or create new one."""
    import asyncio
    from sqlalchemy import select
    from shared.models import Provider

    async def _find_or_create():
        if tax_id:
            result = await session.execute(
                select(Provider).where(Provider.tax_id == tax_id)
            )
            provider = result.scalar_one_or_none()
            if provider:
                return provider

        if provider_name:
            result = await session.execute(
                select(Provider).where(Provider.fiscal_name.ilike(f"%{provider_name}%"))
            )
            provider = result.scalar_one_or_none()
            if provider:
                return provider

        new_provider = Provider(
            fiscal_name=provider_name or f"Provider_{tax_id}",
            tax_id=tax_id,
            active=True,
        )
        session.add(new_provider)
        await session.flush()
        return new_provider

    return _find_or_create()


def publish_homologation_job(invoice_id: int, line_ids: list) -> None:
    """Publish homologation job to queue."""
    import aio_pika
    import asyncio

    async def _publish():
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel()
                await channel.declare_queue("homologation_jobs", durable=True)
                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps({
                            "invoice_id": invoice_id,
                            "line_ids": line_ids,
                        }).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    ),
                    routing_key="homologation_jobs",
                )
        except Exception as e:
            print(f"Warning: Failed to publish homologation job: {str(e)}")

    try:
        asyncio.run(_publish())
    except Exception:
        pass


@celery_app.task(name="ocr_worker.process_segment", bind=True, max_retries=3)
def process_segment(self, document_id: int, segment_id: int):
    """Main OCR processing task for a document segment."""
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select, update
    from shared.models import DetectedDoc, Invoice, InvoiceLine, Page, Provider
    from services.image_preprocessor import preprocess_image
    from services.text_extractor import extract_header, extract_table_lines

    async def _run():
        engine = create_async_engine(settings.database_url, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            result = await session.execute(
                select(DetectedDoc).where(DetectedDoc.id == segment_id)
            )
            segment = result.scalar_one_or_none()
            if not segment:
                return {"error": f"Segment {segment_id} not found"}

            await session.execute(
                update(DetectedDoc).where(DetectedDoc.id == segment_id).values(status="processing_ocr")
            )
            await session.commit()

            pages = download_segment_pages(document_id, segment.start_page, segment.end_page)

            preprocessed_pages = []
            for page_num, image_bytes in pages:
                try:
                    preprocessed = preprocess_image(image_bytes)
                    preprocessed_pages.append((page_num, preprocessed))
                except Exception as e:
                    print(f"Preprocessing error on page {page_num}: {str(e)}")
                    preprocessed_pages.append((page_num, image_bytes))

            full_text = run_ocr_on_pages(preprocessed_pages)

            header = extract_header(full_text)
            table_lines = extract_table_lines(full_text)

            provider_id = None
            if header.get("tax_id"):
                result = await session.execute(
                    select(Provider).where(Provider.tax_id == header["tax_id"])
                )
                provider = result.scalar_one_or_none()
                if provider:
                    provider_id = provider.id

            invoice = Invoice(
                detected_doc_id=segment_id,
                provider_id=provider_id,
                tax_id=header.get("tax_id"),
                invoice_number=header.get("invoice_number"),
                invoice_date=header.get("invoice_date"),
                subtotal=header.get("subtotal"),
                vat=header.get("vat"),
                total=header.get("total"),
                currency=header.get("currency", "EUR"),
                status="pending_review",
            )
            session.add(invoice)
            await session.flush()

            page_ids = {}
            result = await session.execute(
                select(Page).where(
                    Page.document_id == document_id,
                    Page.page_number.between(segment.start_page, segment.end_page),
                )
            )
            for page in result.scalars().all():
                page_ids[page.page_number] = page.id

            line_ids = []
            for line_data in table_lines:
                page_id = page_ids.get(segment.start_page)
                invoice_line = InvoiceLine(
                    invoice_id=invoice.id,
                    line_number=line_data["line_number"],
                    supplier_code=line_data.get("supplier_code"),
                    original_description=line_data.get("original_description"),
                    quantity=line_data.get("quantity"),
                    unit=line_data.get("unit"),
                    unit_price=line_data.get("unit_price"),
                    subtotal=line_data.get("subtotal"),
                    page_id=page_id,
                    status="pending_homologation",
                    extraction_confidence=line_data.get("extraction_confidence", 0.5),
                )
                session.add(invoice_line)
                await session.flush()
                line_ids.append(invoice_line.id)

            await session.execute(
                update(DetectedDoc).where(DetectedDoc.id == segment_id).values(status="ocr_complete")
            )
            await session.commit()

            publish_homologation_job(invoice.id, line_ids)

            return {
                "segment_id": segment_id,
                "invoice_id": invoice.id,
                "lines_extracted": len(line_ids),
                "confidence": header.get("confidence", 0.0),
            }

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
