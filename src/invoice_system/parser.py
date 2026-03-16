from __future__ import annotations

import re
from datetime import date, datetime

from .models import ParsedInvoice, ParsedInvoiceLine

DATE_PATTERNS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]


class InvoiceParser:
    def split_potential_multi_invoice_text(self, text: str) -> list[str]:
        parts = [
            p.strip()
            for p in re.split(
                r"\f|(?=^\s*FACTURA\s*$)",
                text,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            if p.strip()
        ]
        return parts if parts else [text]

    def parse_one(self, text: str, source_file: str | None = None) -> ParsedInvoice:
        supplier = self._extract_supplier(text)
        invoice_date = self._extract_date(text)
        invoice_number = self._extract_invoice_number(text)
        lines = self._extract_lines(text)
        return ParsedInvoice(
            supplier_name=supplier,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            lines=lines,
            source_file=source_file,
        )

    def _extract_supplier(self, text: str) -> str:
        m = re.search(r"Proveedor\s*:\s*(.+)", text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return "PROVEEDOR_DESCONOCIDO"

    def _extract_date(self, text: str) -> date:
        for m in re.finditer(r"(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})", text):
            raw = m.group(1)
            for fmt in DATE_PATTERNS:
                try:
                    return datetime.strptime(raw, fmt).date()
                except ValueError:
                    continue
        return date.today()

    def _extract_invoice_number(self, text: str) -> str | None:
        m = re.search(r"Factura\s*(?:N[ºo°]|#|num(?:ero)?)\s*:?\s*([A-Za-z0-9\-/]+)", text, flags=re.IGNORECASE)
        return m.group(1).strip() if m else None

    def _extract_lines(self, text: str) -> list[ParsedInvoiceLine]:
        lines: list[ParsedInvoiceLine] = []
        for raw_line in text.splitlines():
            m = re.search(
                r"^(?P<qty>\d+[\.,]?\d*)\s+[xX]\s+(?P<desc>.+?)\s+(?P<unit>\d+[\.,]\d{2})\s+(?P<total>\d+[\.,]\d{2})$",
                raw_line.strip(),
            )
            if not m:
                continue
            qty = float(m.group("qty").replace(",", "."))
            unit = float(m.group("unit").replace(",", "."))
            total = float(m.group("total").replace(",", "."))
            lines.append(
                ParsedInvoiceLine(
                    raw_description=m.group("desc").strip(),
                    quantity=qty,
                    unit_price=unit,
                    total_price=total,
                )
            )
        return lines
