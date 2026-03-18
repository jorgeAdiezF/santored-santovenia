from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class ParsedInvoiceLine:
    raw_description: str
    quantity: float
    unit_price: float
    total_price: float


@dataclass(slots=True)
class ParsedInvoice:
    supplier_name: str
    invoice_number: str | None
    invoice_date: date
    lines: list[ParsedInvoiceLine] = field(default_factory=list)
    source_file: str | None = None
