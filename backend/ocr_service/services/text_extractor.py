import re
from typing import Optional, Dict, List, Tuple, Any
from datetime import date, datetime
from decimal import Decimal


# Spanish tax ID patterns: CIF (companies) and NIF (individuals)
CIF_PATTERN = re.compile(r"\b[ABCDEFGHJKLMNPQRSUVW]\d{7}[A-J0-9]\b", re.IGNORECASE)
NIF_PATTERN = re.compile(r"\b\d{8}[A-Z]\b", re.IGNORECASE)
NIE_PATTERN = re.compile(r"\b[XYZ]\d{7}[A-Z]\b", re.IGNORECASE)

# Invoice number patterns
INVOICE_NUMBER_PATTERNS = [
    re.compile(r"(?:factura|fra|invoice)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:n[uú]mero|n[oº])[:\s\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:num\.?|no\.?)[:\s]*([A-Z0-9\-\/]{3,20})", re.IGNORECASE),
]

# Date patterns
DATE_PATTERNS = [
    re.compile(r"(?:fecha|date|data)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"),
    re.compile(r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})\b"),
    re.compile(r"\b(\d{1,2})\s+(?:de\s+)?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(\d{4})\b", re.IGNORECASE),
]

MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

# Amount patterns
TOTAL_PATTERN = re.compile(r"(?:total|importe\s+total)[:\s]*([€$]?\s*[\d\.,]+)", re.IGNORECASE)
SUBTOTAL_PATTERN = re.compile(r"(?:subtotal|base\s+imponible|base)[:\s]*([€$]?\s*[\d\.,]+)", re.IGNORECASE)
VAT_PATTERN = re.compile(r"(?:iva|i\.v\.a\.|vat|impuesto)[:\s]*(?:\d{1,3}%?\s*)?([€$]?\s*[\d\.,]+)", re.IGNORECASE)
VAT_RATE_PATTERN = re.compile(r"(?:iva|i\.v\.a\.|tipo)[:\s]*(\d{1,2})\s*%", re.IGNORECASE)

# Provider name hints
PROVIDER_PATTERNS = [
    re.compile(r"(?:proveedor|vendor|supplier|empresa|razón\s+social)[:\s]*([^\n]+)", re.IGNORECASE),
    re.compile(r"(?:de|from)[:\s]*([A-Z][^\n]{5,50}(?:S\.?L\.?|S\.?A\.?|S\.?L\.?U\.?))", re.IGNORECASE),
]


def extract_tax_id(text: str) -> Optional[str]:
    """Extract the first valid Spanish tax ID from text."""
    for pattern in [CIF_PATTERN, NIF_PATTERN, NIE_PATTERN]:
        match = pattern.search(text)
        if match:
            return match.group(0).upper()
    return None


def extract_all_tax_ids(text: str) -> List[str]:
    """Extract all tax IDs from text."""
    ids = []
    for pattern in [CIF_PATTERN, NIF_PATTERN, NIE_PATTERN]:
        ids.extend([m.upper() for m in pattern.findall(text)])
    return list(set(ids))


def extract_invoice_number(text: str) -> Optional[str]:
    """Extract invoice number from text."""
    for pattern in INVOICE_NUMBER_PATTERNS:
        match = pattern.search(text)
        if match:
            inv_num = match.group(1).strip()
            if len(inv_num) >= 3:
                return inv_num
    return None


def parse_amount(amount_str: str) -> Optional[Decimal]:
    """Parse a Spanish-formatted amount string to Decimal."""
    if not amount_str:
        return None
    cleaned = re.sub(r"[€$\s]", "", amount_str)
    # Handle European format (1.234,56) vs US format (1,234.56)
    if re.match(r"^\d{1,3}(\.\d{3})*(,\d{2})?$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif re.match(r"^\d{1,3}(,\d{3})*(\.\d{2})?$", cleaned):
        cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
        cleaned = re.sub(r"\.(?=.*\.)", "", cleaned)

    try:
        return Decimal(cleaned)
    except Exception:
        return None


def extract_date(text: str) -> Optional[date]:
    """Extract invoice date from text."""
    match = DATE_PATTERNS[0].search(text)
    if match:
        date_str = match.group(1)
        parts = re.split(r"[\/\-\.]", date_str)
        if len(parts) == 3:
            try:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                if year < 100:
                    year += 2000
                return date(year, month, day)
            except ValueError:
                pass

    match = DATE_PATTERNS[1].search(text)
    if match:
        try:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return date(year, month, day)
        except ValueError:
            pass

    match = DATE_PATTERNS[2].search(text)
    if match:
        try:
            day = int(match.group(1))
            month = MONTHS_ES.get(match.group(2).lower(), 0)
            year = int(match.group(3))
            if month > 0:
                return date(year, month, day)
        except ValueError:
            pass

    return None


def extract_header(text: str) -> Dict[str, Any]:
    """Extract all invoice header fields from OCR text."""
    result = {
        "tax_id": None,
        "invoice_number": None,
        "invoice_date": None,
        "subtotal": None,
        "vat": None,
        "total": None,
        "currency": "EUR",
        "provider_name": None,
        "confidence": 0.0,
    }

    confidence_factors = 0
    total_factors = 5

    tax_id = extract_tax_id(text)
    if tax_id:
        result["tax_id"] = tax_id
        confidence_factors += 1

    invoice_number = extract_invoice_number(text)
    if invoice_number:
        result["invoice_number"] = invoice_number
        confidence_factors += 1

    invoice_date = extract_date(text)
    if invoice_date:
        result["invoice_date"] = invoice_date
        confidence_factors += 1

    total_match = TOTAL_PATTERN.search(text)
    if total_match:
        result["total"] = parse_amount(total_match.group(1))
        if result["total"]:
            confidence_factors += 1

    subtotal_match = SUBTOTAL_PATTERN.search(text)
    if subtotal_match:
        result["subtotal"] = parse_amount(subtotal_match.group(1))

    vat_match = VAT_PATTERN.search(text)
    if vat_match:
        result["vat"] = parse_amount(vat_match.group(1))
        if result["vat"]:
            confidence_factors += 1

    if "$" in text or "USD" in text:
        result["currency"] = "USD"

    result["confidence"] = confidence_factors / total_factors

    return result


def extract_table_lines(text: str) -> List[Dict[str, Any]]:
    """
    Extract invoice line items from OCR text using column detection heuristics.
    Returns list of line dicts.
    """
    lines = text.split("\n")
    table_lines = []

    line_item_pattern = re.compile(
        r"^(.{5,50})\s+"
        r"(\d+[\.,]?\d*)\s+"
        r"([a-zA-Z/]+)?\s*"
        r"(\d+[\.,]\d+)\s+"
        r"(\d+[\.,]\d+)\s*$"
    )

    code_desc_pattern = re.compile(
        r"^([A-Z0-9\-\.]{3,20})\s+(.{5,80})\s+(\d+[\.,]?\d*)\s+([a-zA-Z/]+)?\s*(\d+[\.,]\d+)",
        re.IGNORECASE,
    )

    line_number = 0
    in_table = False

    for raw_line in lines:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        if re.search(r"descripci[oó]n|description|concepto|cantidad|precio|importe", raw_line, re.IGNORECASE):
            in_table = True
            continue

        if re.search(r"(?:total|iva|subtotal)\s*:?\s*[\d\.,]+", raw_line, re.IGNORECASE):
            in_table = False
            continue

        match = code_desc_pattern.match(raw_line)
        if match:
            line_number += 1
            quantity_str = match.group(3).replace(",", ".")
            price_str = match.group(5).replace(",", ".")

            try:
                quantity = Decimal(quantity_str)
            except Exception:
                quantity = Decimal("1")

            try:
                unit_price = Decimal(price_str)
            except Exception:
                unit_price = Decimal("0")

            table_lines.append({
                "line_number": line_number,
                "supplier_code": match.group(1),
                "original_description": match.group(2).strip(),
                "quantity": quantity,
                "unit": match.group(4) or "ud",
                "unit_price": unit_price,
                "subtotal": quantity * unit_price,
                "extraction_confidence": 0.7,
            })
            continue

        if in_table:
            match = line_item_pattern.match(raw_line)
            if match:
                line_number += 1
                try:
                    qty = Decimal(match.group(2).replace(",", "."))
                    price = Decimal(match.group(4).replace(",", "."))
                    subtotal = Decimal(match.group(5).replace(",", "."))
                except Exception:
                    continue

                table_lines.append({
                    "line_number": line_number,
                    "supplier_code": None,
                    "original_description": match.group(1).strip(),
                    "quantity": qty,
                    "unit": match.group(3) or "ud",
                    "unit_price": price,
                    "subtotal": subtotal,
                    "extraction_confidence": 0.6,
                })

    return table_lines
