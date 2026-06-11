"""
PDF table extraction using coordinate-aware methods.

Strategy A (digital PDFs): pdfplumber - extracts tables as matrices
Strategy B (scanned PDFs): pytesseract image_to_data - word coordinates → column clustering
"""
from __future__ import annotations

import io
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Optional

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lower-case, strip accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).lower().strip()


def extract_unit_from_text(text: str) -> str:
    """
    Detect unit of measure from a string.
    Returns one of: UN, M2, ML, KG, M, UD, PQ, H, L, ud (default).
    """
    if not text:
        return "ud"
    pattern = re.compile(
        r"\b(UN|UD|PQ|M2|M3|ML|KG|GR|M|H|L|UDS|UNID)\b",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return match.group(1).upper()
    return "ud"


def _parse_amount(s: str) -> Optional[Decimal]:
    """
    Parse a numeric string that may use Spanish formatting (1.234,56) or
    international formatting (1234.56).  Returns Decimal or None.
    """
    if not s:
        return None
    cleaned = re.sub(r"[€$\s]", "", s).strip()
    if not cleaned:
        return None
    # European format: 1.234,56
    if re.match(r"^\d{1,3}(\.\d{3})*(,\d+)?$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    # US format: 1,234.56
    elif re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?$", cleaned):
        cleaned = cleaned.replace(",", "")
    else:
        # Last resort: replace comma with dot, remove extra dots
        cleaned = cleaned.replace(",", ".")
        # Keep only last dot if there are multiple
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _is_numeric_cell(s: str) -> bool:
    """Return True if the cell value looks like a number."""
    if not s:
        return False
    stripped = re.sub(r"[\s€$.,]", "", s)
    return bool(stripped) and stripped.lstrip("-").isdigit()


# ---------------------------------------------------------------------------
# Strategy A – digital PDFs via pdfplumber
# ---------------------------------------------------------------------------

class DigitalPDFExtractor:
    """Extract invoice lines from PDFs that have an embedded text layer."""

    # Column header keywords (normalised)
    _INVOICE_KEYWORDS = {
        "precio", "importe", "total", "cantidad", "descripcion",
        "unitario", "pvp", "pvp unit", "dto", "dto.", "unidad",
        "importe", "neto", "bruto", "concepto",
    }

    def can_extract(self, pdf_bytes: bytes) -> bool:
        """Return True if PDF has a meaningful text layer (>50 chars/page avg)."""
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                if not pdf.pages:
                    return False
                total_chars = sum(
                    len(page.extract_text() or "") for page in pdf.pages
                )
                avg_chars = total_chars / len(pdf.pages)
                return avg_chars > 50
        except Exception:
            return False

    def extract_text(self, pdf_bytes: bytes) -> str:
        """Extract full text preserving layout using pdfplumber."""
        try:
            import pdfplumber
            parts = []
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text(layout=True) or ""
                    parts.append(text)
            return "\n".join(parts)
        except Exception:
            return ""

    def extract_tables(self, pdf_bytes: bytes) -> list:
        """
        Extract all tables from all pages as list of matrices.
        Each table is list of rows, each row is list of cell strings (or None).
        Filters out tables with <2 rows or <3 columns.
        """
        tables = []
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    for table in page.extract_tables():
                        if not table:
                            continue
                        # Normalise: ensure all cells are str or None
                        clean = []
                        for row in table:
                            clean.append([
                                cell.strip() if isinstance(cell, str) else cell
                                for cell in row
                            ])
                        # Filter too-small tables
                        num_rows = len(clean)
                        num_cols = max((len(r) for r in clean), default=0)
                        if num_rows >= 2 and num_cols >= 3:
                            tables.append(clean)
        except Exception:
            pass
        return tables

    def _score_as_invoice_table(self, table: list) -> float:
        """
        Return a 0-1 confidence that this table contains invoice line items.
        Checks whether any row (usually the header row) contains column headers
        that resemble invoice columns.
        """
        if not table:
            return 0.0
        # Look at first 3 rows for header keywords
        header_rows = table[:3]
        found_keywords = 0
        for row in header_rows:
            for cell in row:
                if cell:
                    normalised = _normalize(str(cell))
                    for kw in self._INVOICE_KEYWORDS:
                        if kw in normalised:
                            found_keywords += 1
                            break
        if found_keywords >= 2:
            return 0.9
        if found_keywords == 1:
            return 0.6
        # No header keywords found – check if rows have the right numeric shape
        numeric_rows = 0
        for row in table[1:]:
            numeric_count = sum(1 for cell in row if _is_numeric_cell(str(cell or "")))
            if numeric_count >= 2:
                numeric_rows += 1
        if numeric_rows >= 2:
            return 0.45
        return 0.0

    def _parse_table_rows(self, table: list) -> list:
        """
        Convert a raw pdfplumber table matrix into invoice line dicts.
        Heuristically identifies description, code, qty, unit, price, total columns.
        """
        if not table:
            return []

        # Determine header row index (first row that has header keywords)
        header_idx = 0
        for i, row in enumerate(table[:3]):
            row_text = " ".join(str(c or "") for c in row)
            if re.search(r"descripci[oó]n|cantidad|precio|importe|concepto", row_text, re.I):
                header_idx = i
                break

        col_count = max((len(r) for r in table), default=0)

        # Map column indices to roles by inspecting the header row
        header_row = table[header_idx] if header_idx < len(table) else []
        col_roles: dict[int, str] = {}

        for idx, cell in enumerate(header_row):
            if cell is None:
                continue
            norm = _normalize(str(cell))
            if any(kw in norm for kw in ("descripcion", "concepto", "articulo", "detalle")):
                col_roles[idx] = "description"
            elif any(kw in norm for kw in ("codigo", "referencia", "ref", "cod")):
                col_roles[idx] = "code"
            elif any(kw in norm for kw in ("cantidad", "cant", "ud", "unidades", "qtd")):
                col_roles[idx] = "quantity"
            elif any(kw in norm for kw in ("unidad", "um", "u/m")):
                col_roles[idx] = "unit"
            elif any(kw in norm for kw in ("precio unit", "precio", "pvp", "p.unit", "p unit")):
                col_roles[idx] = "unit_price"
            elif any(kw in norm for kw in ("importe", "total", "neto", "subtotal")):
                col_roles[idx] = "total"

        # If we couldn't map from headers, use positional heuristics on data rows
        if len(col_roles) < 2:
            col_roles = self._infer_column_roles(table, header_idx, col_count)

        lines = []
        line_number = 0
        data_rows = table[header_idx + 1:]

        for row in data_rows:
            if not row:
                continue
            row_text = " ".join(str(c or "") for c in row)
            # Skip footer / summary rows
            if re.search(r"\b(total factura|base imponible|iva|impuesto|subtotal)\b", row_text, re.I):
                continue
            # Skip blank rows
            if not row_text.strip():
                continue

            line_dict = self._map_row_to_line(row, col_roles, col_count)
            if line_dict is None:
                continue

            line_number += 1
            line_dict["line_number"] = line_number
            lines.append(line_dict)

        return lines

    def _infer_column_roles(self, table: list, header_idx: int, col_count: int) -> dict:
        """
        Infer column roles from data when no headers were detected.
        Approach: find which columns are mostly numeric, which is longest text, etc.
        """
        col_roles: dict[int, str] = {}
        if col_count == 0:
            return col_roles

        # Aggregate column stats from data rows
        col_num_count = [0] * col_count
        col_text_len = [0] * col_count
        col_cell_count = [0] * col_count
        col_short_alphanum = [0] * col_count

        for row in table[header_idx + 1:]:
            for idx, cell in enumerate(row):
                if idx >= col_count:
                    break
                val = str(cell or "").strip()
                if not val:
                    continue
                col_cell_count[idx] += 1
                col_text_len[idx] += len(val)
                if _is_numeric_cell(val):
                    col_num_count[idx] += 1
                if re.match(r"^[A-Z0-9\.\-]{2,20}$", val, re.I):
                    col_short_alphanum[idx] += 1

        total_data_rows = max(1, len(table) - header_idx - 1)

        # Identify numeric columns
        numeric_cols = [
            i for i in range(col_count)
            if col_cell_count[i] > 0 and col_num_count[i] / col_cell_count[i] > 0.5
        ]
        # Longest text column → description
        avg_text = [
            (col_text_len[i] / col_cell_count[i]) if col_cell_count[i] > 0 else 0
            for i in range(col_count)
        ]
        desc_col = max(range(col_count), key=lambda i: avg_text[i]) if col_count else None
        if desc_col is not None:
            col_roles[desc_col] = "description"

        # Among numeric cols, last = total, second-to-last = unit_price, before that = quantity
        num_cols_sorted = sorted(numeric_cols)
        if len(num_cols_sorted) >= 1:
            col_roles[num_cols_sorted[-1]] = "total"
        if len(num_cols_sorted) >= 2:
            col_roles[num_cols_sorted[-2]] = "unit_price"
        if len(num_cols_sorted) >= 3:
            col_roles[num_cols_sorted[-3]] = "quantity"

        # First short-alphanumeric column (not already assigned) → code
        for i in range(col_count):
            if i not in col_roles and col_cell_count[i] > 0:
                rate = col_short_alphanum[i] / col_cell_count[i]
                if rate > 0.5 and avg_text[i] < 20:
                    col_roles[i] = "code"
                    break

        return col_roles

    def _map_row_to_line(self, row: list, col_roles: dict, col_count: int) -> Optional[dict]:
        """Map a single data row to an invoice line dict using col_roles."""
        get = lambda role: next(
            (str(row[i] or "").strip() for i, r in col_roles.items() if r == role and i < len(row)),
            None,
        )

        description = get("description")
        code = get("code")
        qty_str = get("quantity")
        unit_str = get("unit")
        price_str = get("unit_price")
        total_str = get("total")

        # Need at least a description or total
        if not description and not total_str:
            return None

        # Skip rows that are clearly not product lines
        if description and len(description) < 2:
            return None

        quantity = _parse_amount(qty_str) if qty_str else None
        unit_price = _parse_amount(price_str) if price_str else None
        total = _parse_amount(total_str) if total_str else None

        # If we have total but not unit_price, try to compute
        if total and quantity and not unit_price and quantity != 0:
            unit_price = total / quantity

        # If we have unit_price and quantity but not total, compute
        if unit_price and quantity and not total:
            total = unit_price * quantity

        # Determine confidence: uncertain if key fields are missing
        confidence = 0.85
        if not quantity or not unit_price:
            confidence = 0.5

        unit = unit_str or (extract_unit_from_text(description or "") if description else "ud")

        return {
            "line_number": 0,  # will be set by caller
            "supplier_code": code,
            "original_description": description or "",
            "quantity": quantity,
            "unit": unit,
            "unit_price": unit_price,
            "subtotal": total,
            "extraction_confidence": confidence,
        }

    def extract_invoice_lines(self, pdf_bytes: bytes) -> list:
        """
        Main method. Tries to find a table that looks like invoice lines
        (has columns resembling description, quantity, price, total).
        Returns list of line dicts with keys:
          line_number, supplier_code, original_description, quantity, unit,
          unit_price, subtotal, extraction_confidence
        """
        try:
            tables = self.extract_tables(pdf_bytes)
            if not tables:
                return []

            # Score each table and pick the best one above the threshold
            best_table = None
            best_score = 0.0
            for table in tables:
                score = self._score_as_invoice_table(table)
                if score > best_score:
                    best_score = score
                    best_table = table

            if best_score < 0.4 or best_table is None:
                return []

            return self._parse_table_rows(best_table)
        except Exception as exc:
            print(f"DigitalPDFExtractor error: {exc}")
            return []


# ---------------------------------------------------------------------------
# Strategy B – scanned PDFs via pytesseract image_to_data
# ---------------------------------------------------------------------------

class ScannedPDFExtractor:
    """Extract invoice lines from scanned/image PDFs using word-coordinate clustering."""

    # Pytesseract confidence threshold
    _CONF_THRESHOLD = 30
    # Row grouping tolerance in pixels
    _ROW_Y_TOLERANCE = 15
    # Column gap threshold in pixels
    _COL_GAP_THRESHOLD = 40

    _HEADER_KEYWORDS = re.compile(
        r"\b(descripci[oó]n|precio|cantidad|importe|concepto|referencia|codigo|unidad|"
        r"cod\.|ref\.|c[oó]digo|description|qty|amount)\b",
        re.IGNORECASE,
    )
    _FOOTER_KEYWORDS = re.compile(
        r"\b(total|iva|i\.v\.a\.|subtotal|base imponible|importe total|vencimiento|"
        r"forma de pago|observaciones|firma)\b",
        re.IGNORECASE,
    )

    def extract_invoice_lines_from_image(self, image_bytes: bytes) -> list:
        """
        Uses pytesseract.image_to_data() to get word positions.
        Groups words into rows by Y coordinate (tolerance: 15px).
        Within each row, groups words into columns by X gaps (gap > 40px = new column).
        Identifies columns by position: leftmost=code, next=description (may span
        multiple words), then numeric columns at right = qty, unit, price, total.
        Returns same format as DigitalPDFExtractor.extract_invoice_lines().
        """
        try:
            import pytesseract
            from pytesseract import Output
            from PIL import Image

            image = Image.open(io.BytesIO(image_bytes))
            data = pytesseract.image_to_data(
                image,
                output_type=Output.DICT,
                lang="spa+eng",
                config="--psm 6",
            )
        except Exception as exc:
            print(f"ScannedPDFExtractor pytesseract error: {exc}")
            return []

        # Filter out low-confidence and empty words
        n_boxes = len(data["level"])
        words = []
        for i in range(n_boxes):
            try:
                conf = int(data["conf"][i])
            except (ValueError, TypeError):
                continue
            if conf < self._CONF_THRESHOLD:
                continue
            text = str(data["text"][i]).strip()
            if not text:
                continue
            words.append({
                "text": text,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            })

        if not words:
            return []

        # Group words into rows by top coordinate
        rows_by_y = self._group_words_into_rows(words)

        # Convert each row-group into columns
        structured_rows = []
        for top_key, row_words in sorted(rows_by_y.items()):
            cols = self._split_into_columns(row_words)
            if cols:
                structured_rows.append(cols)

        if not structured_rows:
            return []

        # Detect the table body: rows with >=3 columns and >=2 numeric values
        # Skip header rows (contain description/precio/cantidad keywords)
        # Skip footer rows (contain total/iva/subtotal keywords)
        line_rows = []
        for cols in structured_rows:
            row_text = " ".join(cols)
            if self._HEADER_KEYWORDS.search(row_text):
                continue
            if self._FOOTER_KEYWORDS.search(row_text):
                continue
            if len(cols) < 3:
                continue
            numeric_count = sum(1 for c in cols if self._is_numeric(c))
            if numeric_count < 2:
                continue
            line_rows.append(cols)

        return self._convert_rows_to_lines(line_rows)

    def _group_words_into_rows(self, words: list) -> dict:
        """Group words by their Y (top) coordinate within ±15px tolerance."""
        rows: dict[int, list] = {}
        for word in words:
            top = word["top"]
            # Find an existing bucket within tolerance
            matched_key = None
            for key in rows:
                if abs(key - top) <= self._ROW_Y_TOLERANCE:
                    matched_key = key
                    break
            if matched_key is not None:
                rows[matched_key].append(word)
            else:
                rows[top] = [word]
        return rows

    def _split_into_columns(self, row_words: list) -> list:
        """
        Sort words by left coordinate and split into columns wherever the gap
        between word_end and next_word_start exceeds _COL_GAP_THRESHOLD.
        Returns list of column strings.
        """
        sorted_words = sorted(row_words, key=lambda w: w["left"])
        if not sorted_words:
            return []

        columns = []
        current_col_words = [sorted_words[0]]

        for i in range(1, len(sorted_words)):
            prev = sorted_words[i - 1]
            curr = sorted_words[i]
            prev_end = prev["left"] + prev["width"]
            gap = curr["left"] - prev_end
            if gap > self._COL_GAP_THRESHOLD:
                columns.append(" ".join(w["text"] for w in current_col_words))
                current_col_words = [curr]
            else:
                current_col_words.append(curr)

        if current_col_words:
            columns.append(" ".join(w["text"] for w in current_col_words))

        return columns

    @staticmethod
    def _is_numeric(s: str) -> bool:
        """Return True if the string looks like a number (ignoring spaces, commas, dots)."""
        stripped = re.sub(r"[\s,.]", "", s)
        return bool(stripped) and stripped.lstrip("-").isdigit()

    def _convert_rows_to_lines(self, rows: list) -> list:
        """
        Convert structured column rows into invoice line dicts.
        Column assignment by position:
          - leftmost → code
          - second (or widest) → description
          - numeric columns at right → qty, price, total (right-to-left)
        """
        lines = []
        for line_number, cols in enumerate(rows, start=1):
            # Separate numeric and text columns
            numeric_indices = [i for i, c in enumerate(cols) if self._is_numeric(c)]
            text_indices = [i for i, c in enumerate(cols) if not self._is_numeric(c)]

            # Description: longest text column
            description = ""
            code = None
            if text_indices:
                desc_idx = max(text_indices, key=lambda i: len(cols[i]))
                description = cols[desc_idx]
                # Code: first text column that is short alphanumeric (if different from desc)
                for i in text_indices:
                    val = cols[i]
                    if i != desc_idx and re.match(r"^[A-Z0-9\.\-\/]{2,20}$", val, re.I):
                        code = val
                        break
                    elif i != desc_idx and len(val) < len(description) and val:
                        code = val

            # Numeric columns right to left: total, unit_price, quantity
            qty = None
            unit_price = None
            total = None
            unit = "ud"

            num_cols_sorted = sorted(numeric_indices)
            if len(num_cols_sorted) >= 1:
                total = _parse_amount(cols[num_cols_sorted[-1]])
            if len(num_cols_sorted) >= 2:
                unit_price = _parse_amount(cols[num_cols_sorted[-2]])
            if len(num_cols_sorted) >= 3:
                qty = _parse_amount(cols[num_cols_sorted[-3]])

            # Try to infer missing values
            if total and qty and not unit_price and qty != 0:
                unit_price = total / qty
            if unit_price and qty and not total:
                total = unit_price * qty

            if description:
                unit = extract_unit_from_text(description)

            lines.append({
                "line_number": line_number,
                "supplier_code": code,
                "original_description": description,
                "quantity": qty,
                "unit": unit,
                "unit_price": unit_price,
                "subtotal": total,
                "extraction_confidence": 0.65,
            })

        return lines
