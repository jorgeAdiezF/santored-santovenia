from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


class OCRExtractor:
    """Extrae texto desde txt/pdf/imagen.

    Estrategia para PDF:
    1) Intenta `pdftotext` (rápido para PDFs con capa de texto).
    2) Si no hay texto útil, aplica OCR sobre PDF escaneado:
       - Convierte páginas con `pdftoppm`.
       - Ejecuta `tesseract` por cada página.

    Esto cubre tanto facturas digitales como facturas escaneadas en PDF.
    """

    def extract_text(self, file_path: str | Path) -> str:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            return self._extract_pdf(path)
        if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}:
            return self._extract_image(path)
        raise ValueError(f"Formato no soportado: {suffix}")

    def _extract_pdf(self, path: Path) -> str:
        text = self._extract_pdf_text_layer(path)
        if self._is_meaningful_text(text):
            return text
        return self._extract_pdf_scanned_with_ocr(path)

    def _extract_pdf_text_layer(self, path: Path) -> str:
        if shutil.which("pdftotext") is None:
            return ""

        out_txt = path.with_suffix(".ocr.txt")
        cmd = ["pdftotext", str(path), str(out_txt)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and out_txt.exists():
            text = out_txt.read_text(encoding="utf-8", errors="ignore")
            out_txt.unlink(missing_ok=True)
            return text
        return ""

    def _extract_pdf_scanned_with_ocr(self, path: Path) -> str:
        if shutil.which("pdftoppm") is None:
            raise RuntimeError(
                "PDF escaneado detectado pero falta `pdftoppm` (poppler). "
                "Instálalo para convertir páginas PDF a imagen antes del OCR."
            )
        if shutil.which("tesseract") is None:
            raise RuntimeError(
                "PDF escaneado detectado pero falta `tesseract`. "
                "Instálalo para ejecutar OCR sobre las páginas del PDF."
            )

        with tempfile.TemporaryDirectory(prefix="invoice_pdf_ocr_") as tmp_dir:
            prefix = Path(tmp_dir) / "page"
            cmd = ["pdftoppm", "-png", str(path), str(prefix)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("No se pudo convertir el PDF escaneado a imágenes con pdftoppm.")

            page_images = sorted(Path(tmp_dir).glob("page-*.png"))
            if not page_images:
                raise RuntimeError("No se generaron imágenes de páginas desde el PDF.")

            page_texts: list[str] = []
            for page in page_images:
                page_texts.append(self._extract_image(page))

        return "\n\f\n".join(page_texts)

    def _extract_image(self, path: Path) -> str:
        cmd = ["tesseract", str(path), "stdout", "-l", "spa+eng"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        raise RuntimeError("No se pudo ejecutar tesseract. Verifica instalación e idioma spa+eng.")

    @staticmethod
    def _is_meaningful_text(text: str, min_chars: int = 30) -> bool:
        compact = "".join(ch for ch in text if not ch.isspace())
        return len(compact) >= min_chars
