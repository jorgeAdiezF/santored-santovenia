import re
from typing import Optional, Dict, List, Tuple, Any
from datetime import date, datetime
from decimal import Decimal


# Spanish tax ID patterns: CIF (companies) and NIF (individuals)
CIF_PATTERN = re.compile(r"\b[ABCDEFGHJKLMNPQRSUVW]\d{7}[A-J0-9]\b", re.IGNORECASE)
NIF_PATTERN = re.compile(r"\b\d{8}[A-Z]\b", re.IGNORECASE)
NIE_PATTERN = re.compile(r"\b[XYZ]\d{7}[A-Z]\b", re.IGNORECASE)

# Invoice number patterns – extended with additional formats from real Spanish invoices
INVOICE_NUMBER_PATTERNS = [
    # Original patterns
    re.compile(r"(?:factura|fra|invoice)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:n[uú]mero|n[oº])[:\s\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:num\.?|no\.?)[:\s]*([A-Z0-9\-\/]{3,20})", re.IGNORECASE),
    # Additional patterns from real Spanish invoice formats
    re.compile(r"(?:n[uú]m(?:ero)?\.?\s+(?:de\s+)?factura)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:fra\.?|fac\.?|f\.?)[:\s#nº\.]*([A-Z0-9\-\/]{3,25})", re.IGNORECASE),
    re.compile(r"(?:albar[aá]n|albaran)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:pedido|order)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"\bSerie[:\s]+([A-Z])\s+N[uú]m(?:ero)?[:\s]+(\d+)", re.IGNORECASE),
    re.compile(r"(?:referencia|ref\.?)[:\s]*([A-Z0-9\-\/]{4,25})", re.IGNORECASE),
    re.compile(r"\b([A-Z]{1,3}[-\/]?\d{4,10})\b"),                 # e.g. F-2024001, A/20240123
    re.compile(r"\b(\d{4}[-\/]\d{3,8})\b"),                        # e.g. 2024/00123
    re.compile(r"(?:documento|doc\.?)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:recibo|ticket)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:nota\s+de\s+cargo|nota\s+cargo)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:nota\s+de\s+abono|nota\s+abono)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:rectificativa|rectificativa\s+n[uú]m)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:simplificada|factura\s+simplificada)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:proforma|pro-forma)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:invoice\s+number|invoice\s+no\.?)[:\s#]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:bill\s+number|bill\s+no\.?)[:\s#]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"\bN[ºo°]?\s*[:.]?\s*([A-Z]{0,3}\d{4,12}[A-Z]?)\b", re.IGNORECASE),
    re.compile(r"(?:n[uú]m\.\s*doc(?:umento)?)[:\s]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:c[oó]digo\s+(?:de\s+)?factura)[:\s]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:folio)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"(?:identificador|id\.?)[:\s]*([A-Z0-9\-\/]{5,25})", re.IGNORECASE),
    re.compile(r"(?:liquidaci[oó]n)[:\s#nº\.]*([A-Z0-9\-\/]+)", re.IGNORECASE),
    re.compile(r"\b([A-Z]{2,4}\d{2}[-\/]\d{4,8})\b"),              # e.g. FA24/00001
]

# ---------------------------------------------------------------------------
# Known supplier patterns trained on real Spanish invoices
# ---------------------------------------------------------------------------

KNOWN_SUPPLIERS = [
    (re.compile(r"SAINT[-\s]?GOBAIN\s+IDAPLAC|DISTRIPLAC", re.I), "SAINT-GOBAIN IDAPLAC, S.L.U."),
    (re.compile(r"LEASYS\s+S\.?P\.?A", re.I), "LEASYS S.P.A. Sucursal en España"),
    (re.compile(r"FUNDICI[ÓO]N\s+Y\s+FORJA\s+PACHECO|PACHECO\s+FORJA", re.I), "Fundición y Forja Pacheco, S.L."),
    (re.compile(r"BRICO\s*DEPOT|EURO\s*DEPOT|BRICOMAN|BRICOLAJE\s+BRICOMAN|OBRAMAT", re.I), "BRICOLAJE BRICOMAN, S.L.U."),
    (re.compile(r"ORANGE\s+ESPAGNE", re.I), "Orange Espagne, S.A."),
    (re.compile(r"SUMINISTROS\s+INDUSTRIALES\s+74", re.I), "SUMINISTROS INDUSTRIALES 74, S.L."),
    (re.compile(r"\bERREKA\b|MATZ[-\s]?ERREKA", re.I), "Matz-Erreka, S. Coop"),
    (re.compile(r"AXIS\s+LE[OÓ]N", re.I), "AXIS LEON, S.L."),
    (re.compile(r"MARCELIANO\s+CUESTA|NOTARIO", re.I), "MARCELIANO CUESTA MTNZ-AGUSTIN CABRERA BLANCO, S.C."),
    (re.compile(r"LEROY\s+MERLIN", re.I), "Leroy Merlin España, S.L.U."),
    (re.compile(r"COMERCIAL\s+DE\s+LAMINADOS|LAMINADOS\s+IB[EÉ]RICA", re.I), "Comercial de Laminados Ibérica, S.A.U."),
    (re.compile(r"HIERROS\s+Y\s+TRANSFORMADOS\s+DE\s+LE[OÓ]N", re.I), "HIERROS Y TRANSFORMADOS DE LEÓN, S.L."),
    (re.compile(r"METALES\s+SANTA\s+OLAJA|SERIE\s+ALFIL|Ctra\.\s*Villarroa[ñn]e", re.I), "Metales Santa Olaja, S.A."),
    (re.compile(r"FERRETERIA\s+BANEZANA|FERRETER[IÍ]A\s+BA[ÑN]EZANA", re.I), "FERRETERÍA BAÑEZANA"),
    (re.compile(r"REPSOL|E\.S\.\s*ARMUNIA|TERA\s+GASOLINERA", re.I), "Repsol Soluciones Energéticas, S.A."),
    (re.compile(r"SABADELL|BANCO\s+DE\s+SABADELL", re.I), "Banco de Sabadell, S.A."),
    (re.compile(r"\bCRENGO\s+ESPAGNE\b", re.I), "Crengo Espagne, S.A.U."),
    (re.compile(r"W[ÜU]RTH\s+ESPA[ÑN]A", re.I), "WÜRTH ESPAÑA, S.A."),
    (re.compile(r"LA\s+FLOR\s+DEL\s+ORBIGO", re.I), "LA FLOR DEL ORBIGO, S.L."),
    (re.compile(r"HERGADI\s*S\.?L\.?", re.I), "HERGADI, S.L."),
    (re.compile(r"Alquiler\s+y\s+venta\s+de\s+maquinaria\s+74", re.I), "Alquiler y venta de maquinaria 74, S.L."),
    (re.compile(r"CUMBRE\s+LEON|Rodriguez\s+del\s+Valle", re.I), "CUMBRE LEON ASESORES"),
]

# ---------------------------------------------------------------------------
# Bank / institution detection — these should never be stored as providers
# ---------------------------------------------------------------------------
_BANK_INSTITUTION_RE = re.compile(
    r"\b(banco|bank|caixa|caja\s+de|sabadell|santander|bbva|caixabank|"
    r"la\s+caixa|bankia|bankinter|abanca|unicaja|kutxabank|ibercaja|"
    r"cajamar|ing\s+direct|openbank|hacienda|agencia\s+tributaria|"
    r"seguridad\s+social|ayuntamiento|diputaci[oó]n|junta\s+de|"
    r"ministerio|patrimonio|administraci[oó]n|tesoreria|recaudaci[oó]n)\b",
    re.IGNORECASE,
)


def is_bank_or_institution(name: str) -> bool:
    """True if name looks like a bank or public institution (not a real supplier)."""
    return bool(_BANK_INSTITUTION_RE.search(name or ""))


def is_invoice_number_valid(invoice_number: str) -> bool:
    """
    False if the extracted 'invoice number' is actually a date, phone,
    postal code, year, or other non-invoice value.
    """
    if not invoice_number or len(invoice_number) < 3:
        return False
    n = invoice_number.strip()
    # Date formats: DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD …
    if re.match(r"^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}$", n):
        return False
    # Pure year (1900-2099)
    if re.match(r"^(19|20)\d{2}$", n):
        return False
    # Spanish/EU phone (9-12 digits, no letters)
    if re.match(r"^\+?[\d\s\-]{9,14}$", n) and not re.search(r"[A-Za-z]", n):
        return False
    # Postal code (exactly 5 digits)
    if re.match(r"^\d{5}$", n):
        return False
    # Percentage
    if re.match(r"^\d{1,3}%$", n):
        return False
    # Too long (> 30 chars) — probably noise
    if len(n) > 30:
        return False
    return True


def extract_supplier_name(text: str) -> Optional[str]:
    """
    Try known supplier patterns first, then fall back to heuristics.
    Returns canonical supplier name or None.
    """
    # 1. Try known suppliers
    for pattern, canonical in KNOWN_SUPPLIERS:
        if pattern.search(text):
            return canonical
    # 2. Try "Proveedor: X" pattern
    m = re.search(r"Proveedor\s*:\s*(.+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:100]
    # 3. Return None (let the caller handle)
    return None

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
    total_factors = 6  # increased to account for provider detection

    tax_id = extract_tax_id(text)
    if tax_id:
        result["tax_id"] = tax_id
        confidence_factors += 1

    invoice_number = extract_invoice_number(text)
    if invoice_number and is_invoice_number_valid(invoice_number):
        result["invoice_number"] = invoice_number
        confidence_factors += 1
    elif invoice_number:
        # Found something but it looks like a date/phone — discard
        invoice_number = None

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

    # Supplier detection via known-supplier patterns and heuristics
    provider_name = extract_supplier_name(text)
    if provider_name:
        result["provider_name"] = provider_name
        confidence_factors += 1
    else:
        # Fall back to legacy PROVIDER_PATTERNS if extract_supplier_name found nothing
        for pattern in PROVIDER_PATTERNS:
            match = pattern.search(text)
            if match:
                result["provider_name"] = match.group(1).strip()[:100]
                confidence_factors += 1
                break

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
