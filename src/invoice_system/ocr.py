from __future__ import annotations

import subprocess
from pathlib import Path


class OCRExtractor:
    """Extrae texto desde txt/pdf/imagen.

    - TXT: lectura directa.
    - PDF: intenta pdftotext (si existe).
    - Imagen: intenta tesseract CLI (si existe).
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
        out_txt = path.with_suffix(".ocr.txt")
        cmd = ["pdftotext", str(path), str(out_txt)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and out_txt.exists():
            text = out_txt.read_text(encoding="utf-8", errors="ignore")
            out_txt.unlink(missing_ok=True)
            return text
        raise RuntimeError(
            "No se pudo extraer texto de PDF. Instala poppler (pdftotext) o integra otro motor OCR."
        )

    def _extract_image(self, path: Path) -> str:
        cmd = ["tesseract", str(path), "stdout", "-l", "spa+eng"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        raise RuntimeError("No se pudo ejecutar tesseract. Verifica instalación e idioma spa+eng.")
