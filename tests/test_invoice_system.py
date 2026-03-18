from pathlib import Path

from invoice_system.database import InvoiceDB
from invoice_system.normalizer import ProductNormalizer, normalize_text
from invoice_system.ocr import OCRExtractor
from invoice_system.parser import InvoiceParser
from invoice_system.service import InvoiceIngestionService


def test_normalize_text_accents_and_symbols() -> None:
    assert normalize_text("Leché Entera 1L!!!") == "leche entera 1l"


def test_product_normalizer_similarity() -> None:
    normalizer = ProductNormalizer(similarity_threshold=0.8)
    result = normalizer.pick_canonical_name("leche entera 1 litro", ["leche entera 1l"])
    assert result == "leche entera 1l"


def test_parser_split_multi_invoice() -> None:
    parser = InvoiceParser()
    text = """FACTURA\nProveedor: A\n01/01/2025\n\f\nFACTURA\nProveedor: B\n02/01/2025"""
    chunks = parser.split_potential_multi_invoice_text(text)
    assert len(chunks) == 2


def test_ingestion_updates_latest_price(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    invoice_path = tmp_path / "invoice.txt"
    invoice_path.write_text(
        """
FACTURA
Proveedor: Acme Foods
Factura N: FAC-001
Fecha: 01/01/2025
1 x Leche Entera 1L 1,20 1,20
2 x Pan Molde 2,50 5,00

FACTURA
Proveedor: Acme Foods
Factura N: FAC-002
Fecha: 15/01/2025
1 x Leche Entera 1 Litro 1,40 1,40
""".strip(),
        encoding="utf-8",
    )

    service = InvoiceIngestionService(db_path)
    try:
        processed = service.ingest_file(invoice_path)
        assert processed == 2

        latest = service.db.get_latest_price("leche entera 1l", "Acme Foods")
        assert latest == 1.4

        evolution = service.db.price_evolution("leche entera 1l")
        assert len(evolution) == 2
        assert evolution[0].unit_price == 1.2
        assert evolution[1].unit_price == 1.4
    finally:
        service.close()


def test_database_alias_linking(tmp_path: Path) -> None:
    db = InvoiceDB(tmp_path / "a.db")
    try:
        supplier_id = db.get_or_create_supplier("Proveedor X")
        product_id = db.get_or_create_product("arroz 1kg")
        db.link_alias(supplier_id, "arroz premium 1kg", product_id)

        found = db.find_product_by_alias(supplier_id, "arroz premium 1kg")
        assert found == product_id
    finally:
        db.close()


def test_pdf_uses_ocr_fallback_when_text_layer_is_empty(monkeypatch) -> None:
    ocr = OCRExtractor()

    monkeypatch.setattr(ocr, "_extract_pdf_text_layer", lambda _path: "")
    monkeypatch.setattr(ocr, "_extract_pdf_scanned_with_ocr", lambda _path: "texto ocr")

    result = ocr._extract_pdf(Path("dummy.pdf"))
    assert result == "texto ocr"


def test_pdf_uses_text_layer_when_available(monkeypatch) -> None:
    ocr = OCRExtractor()
    pdf_text = "Proveedor: Demo\nFactura N: 123\nFecha: 01/01/2025"

    monkeypatch.setattr(ocr, "_extract_pdf_text_layer", lambda _path: pdf_text)
    monkeypatch.setattr(ocr, "_extract_pdf_scanned_with_ocr", lambda _path: "no debe usarse")

    result = ocr._extract_pdf(Path("dummy.pdf"))
    assert result == pdf_text
