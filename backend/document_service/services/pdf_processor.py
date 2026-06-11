import io
import os
import sys
import tempfile
from typing import List, Tuple
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from shared.config import get_settings
from .storage import upload_bytes

settings = get_settings()


def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[Tuple[int, bytes]]:
    """
    Convert PDF bytes to list of (page_number, image_bytes) tuples.
    Returns 1-indexed page numbers.
    """
    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt="PNG")
        result = []
        for i, image in enumerate(images, start=1):
            img_bytes_io = io.BytesIO()
            image.save(img_bytes_io, format="PNG")
            result.append((i, img_bytes_io.getvalue()))
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF to images: {str(e)}")


def process_document_pages(
    document_id: int,
    pdf_bytes: bytes,
    dpi: int = 200,
) -> List[Tuple[int, str]]:
    """
    Convert PDF to images, upload each page to MinIO.
    Returns list of (page_number, image_path) tuples.
    """
    pages = convert_pdf_to_images(pdf_bytes, dpi=dpi)
    page_paths = []

    for page_number, image_bytes in pages:
        object_name = f"documents/{document_id}/pages/page_{page_number:04d}.png"
        upload_bytes(
            object_name=object_name,
            data=image_bytes,
            content_type="image/png",
        )
        page_paths.append((page_number, object_name))

    return page_paths


def get_page_count_from_pdf(pdf_bytes: bytes) -> int:
    """Get the number of pages in a PDF."""
    try:
        from pdf2image.pdf2image import pdfinfo_from_bytes
        info = pdfinfo_from_bytes(pdf_bytes)
        return info.get("Pages", 0)
    except Exception:
        try:
            import subprocess
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(pdf_bytes)
                tmp_path = f.name
            result = subprocess.run(
                ["pdfinfo", tmp_path],
                capture_output=True,
                text=True,
            )
            os.unlink(tmp_path)
            for line in result.stdout.split("\n"):
                if line.startswith("Pages:"):
                    return int(line.split(":")[1].strip())
            return 0
        except Exception:
            return 0
