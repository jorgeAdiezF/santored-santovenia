"""Quality validation for extracted invoice lines."""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional, Union

# ---------------------------------------------------------------------------
# Patterns that indicate a text row is NOT a product line
# ---------------------------------------------------------------------------

NON_PRODUCT_PATTERNS = [
    r"\bp[aá]gina\b",
    r"\bdomicilio fiscal\b",
    r"\bregistro mercantil\b",
    r"\bbanco de\b",
    r"\bwww\.",
    r"\bbase imponible\b",
    r"\btotal factura\b",
    r"\bprotecci[oó]n de datos\b",
    r"\bforma de pago\b",
    r"\bvencimiento\b",
    r"\bpromociones aplicadas\b",
    r"\bdesglose impuestos\b",
    r"\bn\.?i\.?f\.?\b",
    # Financial / bank references
    r"\bIBAN\b",
    r"\bBIC\b",
    r"\bSWIFT\b",
    r"\btransferencia\b",
    r"\bcuenta\s+bancaria\b",
    r"\bEntidad\s+\d+\b",
    r"\bES\d{2}\s*[\d\s]{20}\b",
    # Legal boilerplate
    r"\bcondiciones\s+de\s+(pago|entrega|venta)\b",
    r"\bplazo\s+de\s+pago\b",
    r"\bretenci[oó]n\b",
    r"\brecargo\s+de\s+equivalencia\b",
    r"\bconfidencial\b",
    r"\bley\s+org[aá]nica\b",
    r"\brgpd\b",
    r"\bpol[ií]tica\s+de\s+privacidad\b",
    r"\borgano\s+judicial\b",
    r"\bnotario\b",
    # Discount / adjustment rows (not products)
    r"^\s*descuento\s*(%|\d)",
    r"\bdescuento\s+comercial\b",
    r"\bpor\s+ciento\s+descuento\b",
    r"\brapido\s+pago\b",
    r"\bpronto\s+pago\b",
    # Totals / taxes (already filtered but reinforce)
    r"\btotal\s+con\s+iva\b",
    r"\bcuota\s+iva\b",
    r"\btipo\s+impositivo\b",
    r"\bimporte\s+total\b",
    r"\bbase\s+gravable\b",
    # Footers and headers
    r"\bpor\s+favor\s+conserve\b",
    r"\boriginal\b.*\bduplicado\b",
    r"\bcomprobante\b",
]

_NON_PRODUCT_RE = re.compile(
    "|".join(NON_PRODUCT_PATTERNS),
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def item_quality_flags(
    raw_description: Optional[str],
    canonical_name: Optional[str],
    quantity: Optional[Union[Decimal, float, int]],
    unit_price: Optional[Union[Decimal, float, int]],
    total_price: Optional[Union[Decimal, float, int]],
) -> list:
    """
    Inspect an extracted invoice line and return a list of human-readable
    quality-issue flags.  An empty list means the line looks good.

    Flags use Spanish phrasing so that they are meaningful to the end-user
    who reviews the invoice in the UI.
    """
    flags = []

    desc = (raw_description or "").strip()
    canonical = (canonical_name or "").strip()

    # ---- 1. Non-product text (footers, legal boilerplate, etc.) ------------
    if desc and _NON_PRODUCT_RE.search(desc):
        flags.append("parece pie de página o texto fiscal")

    # ---- 2. Empty or very short description ---------------------------------
    if not desc:
        flags.append("descripción vacía")
    elif len(desc) < 4:
        flags.append("descripción demasiado corta")

    # ---- 3. Canonical name missing ------------------------------------------
    if desc and not canonical:
        flags.append("sin nombre canónico (no homologado)")

    # ---- 4. Quantity checks -------------------------------------------------
    if quantity is None:
        flags.append("cantidad no detectada")
    else:
        try:
            qty_val = float(quantity)
        except (TypeError, ValueError):
            qty_val = None
        if qty_val is not None:
            if qty_val <= 0:
                flags.append("cantidad inusual (≤ 0)")
            elif qty_val > 100_000:
                flags.append("cantidad inusual (demasiado grande)")

    # ---- 5. Unit price checks -----------------------------------------------
    if unit_price is None:
        flags.append("precio unitario no detectado")
    else:
        try:
            price_val = float(unit_price)
        except (TypeError, ValueError):
            price_val = None
        if price_val is not None:
            if price_val < 0:
                flags.append("precio unitario negativo")
            elif price_val == 0:
                flags.append("precio unitario cero")
            elif price_val > 1_000_000:
                flags.append("precio unitario inusual (demasiado alto)")

    # ---- 6. Total / subtotal checks -----------------------------------------
    if total_price is None:
        flags.append("importe total no detectado")
    else:
        try:
            total_val = float(total_price)
        except (TypeError, ValueError):
            total_val = None
        if total_val is not None and total_val < 0:
            flags.append("importe total negativo")

    # ---- 7. Qty × price ≈ total consistency ---------------------------------
    if quantity is not None and unit_price is not None and total_price is not None:
        try:
            qty_f = float(quantity)
            price_f = float(unit_price)
            total_f = float(total_price)
            if qty_f > 0 and price_f > 0 and total_f > 0:
                expected = qty_f * price_f
                # Allow 2 % relative tolerance (handles rounding in PDFs)
                rel_err = abs(expected - total_f) / max(abs(total_f), 0.01)
                if rel_err > 0.02:
                    flags.append(
                        f"cantidad x precio ({expected:.2f}) no coincide con total ({total_f:.2f})"
                    )
        except (TypeError, ValueError, ZeroDivisionError):
            pass

    return flags


def confidence_from_flags(flags: list) -> float:
    """
    Convert a list of quality flags (from item_quality_flags) into a
    0-1 confidence score for the invoice line.
    """
    if not flags:
        return 0.92

    # Almost certainly not a real product line
    if any(
        ("parece pie" in f or "texto fiscal" in f)
        for f in flags
    ):
        return 0.05

    # Quantity × price mismatch: very suspicious — likely OCR column misalignment
    if any("cantidad x precio" in f for f in flags):
        return 0.35

    # Unusual values or oversized numbers
    if any(("demasiado" in f or "inusual" in f) for f in flags):
        return 0.65

    # General penalty: 0.15 per flag, floored at 0.4
    return max(0.4, 0.92 - len(flags) * 0.15)
