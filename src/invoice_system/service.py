from __future__ import annotations

from pathlib import Path

from .database import InvoiceDB
from .normalizer import ProductNormalizer, normalize_text
from .ocr import OCRExtractor
from .parser import InvoiceParser


class InvoiceIngestionService:
    def __init__(self, db_path: str | Path) -> None:
        self.db = InvoiceDB(db_path)
        self.ocr = OCRExtractor()
        self.parser = InvoiceParser()
        self.normalizer = ProductNormalizer()

    def close(self) -> None:
        self.db.close()

    def ingest_file(self, file_path: str | Path) -> int:
        text = self.ocr.extract_text(file_path)
        chunks = self.parser.split_potential_multi_invoice_text(text)
        total_invoices = 0
        for chunk in chunks:
            parsed = self.parser.parse_one(chunk, source_file=str(file_path))
            self._persist_invoice(parsed)
            total_invoices += 1
        return total_invoices

    def _persist_invoice(self, parsed) -> None:
        supplier_id = self.db.get_or_create_supplier(parsed.supplier_name)
        invoice_id = self.db.create_invoice(
            supplier_id=supplier_id,
            invoice_number=parsed.invoice_number,
            invoice_date=parsed.invoice_date.isoformat(),
            source_file=parsed.source_file,
        )

        known_rows = self.db.conn.execute("SELECT canonical_name FROM products").fetchall()
        known = [row["canonical_name"] for row in known_rows]

        for line in parsed.lines:
            alias = normalize_text(line.raw_description)
            existing = self.db.find_product_by_alias(supplier_id, alias)
            if existing is None:
                canonical_name = self.normalizer.pick_canonical_name(alias, known)
                product_id = self.db.get_or_create_product(canonical_name)
                self.db.link_alias(supplier_id, alias, product_id)
                if canonical_name not in known:
                    known.append(canonical_name)
            else:
                product_id = existing

            item_id = self.db.add_invoice_item(
                invoice_id=invoice_id,
                product_id=product_id,
                supplier_raw_description=line.raw_description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                total_price=line.total_price,
            )
            self.db.update_latest_price(
                product_id=product_id,
                supplier_id=supplier_id,
                invoice_date=parsed.invoice_date.isoformat(),
                unit_price=line.unit_price,
                invoice_item_id=item_id,
            )
