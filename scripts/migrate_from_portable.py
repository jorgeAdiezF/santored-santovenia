#!/usr/bin/env python3
"""
migrate_from_portable.py

Migrates data from the portable app's SQLite database to the new PostgreSQL system.

Usage:
    python migrate_from_portable.py --sqlite path/to/invoices.db --db-url postgresql://user:pass@host/db

Or via environment variables:
    SQLITE_PATH=path/to/invoices.db DATABASE_URL=postgresql://... python migrate_from_portable.py
"""

import argparse
import os
import sqlite3
import sys
from typing import Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2 is required. Install with: pip install psycopg2-binary")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_db_url(url: str) -> str:
    """Convert asyncpg-style URL to psycopg2-compatible URL."""
    return url.replace("postgresql+asyncpg://", "postgresql://")


def _detect_family(canonical_name: Optional[str]) -> str:
    """Infer material family from the canonical_name prefix."""
    if not canonical_name:
        return "Sin clasificar"
    if canonical_name.startswith("01 "):
        return "Hierro y metálicos"
    if canonical_name.startswith("02 "):
        return "Mecanización y motores"
    if canonical_name.startswith("08 "):
        return "Portes y transportes"
    return "Sin clasificar"


def _sqlite_rows(sqlite_conn: sqlite3.Connection, query: str, params=()):
    """Return all rows from SQLite as a list of sqlite3.Row objects."""
    cur = sqlite_conn.cursor()
    cur.execute(query, params)
    return cur.fetchall()


# ---------------------------------------------------------------------------
# Per-table migration functions
# ---------------------------------------------------------------------------

def migrate_providers(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
) -> dict:
    """
    Migrate sqlite.suppliers → pg.providers.
    Returns supplier_id_map: {sqlite_id: pg_id}.
    """
    supplier_id_map: dict = {}
    rows = _sqlite_rows(sqlite_conn, "SELECT id, name FROM suppliers ORDER BY id")

    cur = pg_conn.cursor()
    inserted = 0
    skipped = 0

    for row in rows:
        sqlite_id, name = row["id"], row["name"]

        # Idempotency: skip if a provider with the same fiscal_name already exists.
        cur.execute(
            "SELECT id FROM providers WHERE fiscal_name = %s",
            (name,),
        )
        existing = cur.fetchone()
        if existing:
            supplier_id_map[sqlite_id] = existing[0]
            skipped += 1
            continue

        cur.execute(
            """
            INSERT INTO providers (fiscal_name, trade_name, active)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (name, name, True),
        )
        pg_id = cur.fetchone()[0]
        supplier_id_map[sqlite_id] = pg_id
        inserted += 1

    pg_conn.commit()
    print(f"  providers: {inserted} inserted, {skipped} already existed → {len(supplier_id_map)} total mapped")
    return supplier_id_map


def migrate_materials(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
) -> dict:
    """
    Migrate sqlite.products → pg.materials_master.
    Returns product_id_map: {sqlite_id: pg_id}.
    """
    product_id_map: dict = {}
    rows = _sqlite_rows(sqlite_conn, "SELECT id, canonical_name FROM products ORDER BY id")

    cur = pg_conn.cursor()
    inserted = 0
    skipped = 0

    for row in rows:
        sqlite_id = row["id"]
        canonical_name = row["canonical_name"]
        master_code = f"MAT-{sqlite_id:05d}"
        family = _detect_family(canonical_name)

        # Idempotency: skip if master_code already exists.
        cur.execute(
            "SELECT id FROM materials_master WHERE master_code = %s",
            (master_code,),
        )
        existing = cur.fetchone()
        if existing:
            product_id_map[sqlite_id] = existing[0]
            skipped += 1
            continue

        cur.execute(
            """
            INSERT INTO materials_master
                (master_code, family, normalized_description, base_unit, active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (master_code, family, canonical_name or "", "ud", True),
        )
        pg_id = cur.fetchone()[0]
        product_id_map[sqlite_id] = pg_id
        inserted += 1

    pg_conn.commit()
    print(f"  materials_master: {inserted} inserted, {skipped} already existed → {len(product_id_map)} total mapped")
    return product_id_map


def migrate_aliases(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    supplier_id_map: dict,
    product_id_map: dict,
) -> None:
    """
    Migrate sqlite.product_aliases → pg.materials_aliases.
    """
    rows = _sqlite_rows(
        sqlite_conn,
        "SELECT id, supplier_id, alias, product_id FROM product_aliases ORDER BY id",
    )

    cur = pg_conn.cursor()
    inserted = 0
    skipped = 0
    warnings = 0

    for row in rows:
        sqlite_supplier_id = row["supplier_id"]
        sqlite_product_id = row["product_id"]
        alias = row["alias"]

        if sqlite_product_id not in product_id_map:
            print(f"  WARNING: product_aliases row {row['id']}: unknown product_id {sqlite_product_id}, skipping")
            warnings += 1
            continue
        if sqlite_supplier_id not in supplier_id_map:
            print(f"  WARNING: product_aliases row {row['id']}: unknown supplier_id {sqlite_supplier_id}, skipping")
            warnings += 1
            continue

        material_id = product_id_map[sqlite_product_id]
        provider_id = supplier_id_map[sqlite_supplier_id]

        # Idempotency: skip if identical alias already exists for this material + provider.
        cur.execute(
            """
            SELECT id FROM materials_aliases
            WHERE material_id = %s AND provider_id = %s AND supplier_description = %s
            """,
            (material_id, provider_id, alias),
        )
        if cur.fetchone():
            skipped += 1
            continue

        cur.execute(
            """
            INSERT INTO materials_aliases
                (material_id, provider_id, supplier_description, confidence)
            VALUES (%s, %s, %s, %s)
            """,
            (material_id, provider_id, alias, 0.9),
        )
        inserted += 1

    pg_conn.commit()
    print(f"  materials_aliases: {inserted} inserted, {skipped} already existed, {warnings} warnings")


def migrate_invoices(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    supplier_id_map: dict,
) -> dict:
    """
    Migrate sqlite.invoices → pg.invoices.
    Returns invoice_id_map: {sqlite_id: pg_id}.
    """
    invoice_id_map: dict = {}
    rows = _sqlite_rows(
        sqlite_conn,
        """
        SELECT id, supplier_id, invoice_number, invoice_date,
               entity_name, customer_name, raw_text, source_file, ingested_at
        FROM invoices
        ORDER BY id
        """,
    )

    cur = pg_conn.cursor()
    inserted = 0
    skipped = 0
    warnings = 0

    for row in rows:
        sqlite_id = row["id"]
        sqlite_supplier_id = row["supplier_id"]

        if sqlite_supplier_id not in supplier_id_map:
            print(f"  WARNING: invoices row {sqlite_id}: unknown supplier_id {sqlite_supplier_id}, skipping")
            warnings += 1
            continue

        provider_id = supplier_id_map[sqlite_supplier_id]
        invoice_number = row["invoice_number"]
        invoice_date = row["invoice_date"]  # stored as text in SQLite; psycopg2 will cast DATE from string

        # Idempotency: skip if invoice_number + provider_id pair already exists.
        cur.execute(
            """
            SELECT id FROM invoices
            WHERE provider_id = %s AND invoice_number = %s
            """,
            (provider_id, invoice_number),
        )
        existing = cur.fetchone()
        if existing:
            invoice_id_map[sqlite_id] = existing[0]
            skipped += 1
            continue

        cur.execute(
            """
            INSERT INTO invoices
                (detected_doc_id, provider_id, invoice_number, invoice_date,
                 currency, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                None,           # detected_doc_id — no document files in portable app
                provider_id,
                invoice_number,
                invoice_date or None,
                "EUR",
                "consolidated",
            ),
        )
        pg_id = cur.fetchone()[0]
        invoice_id_map[sqlite_id] = pg_id
        inserted += 1

    pg_conn.commit()
    print(f"  invoices: {inserted} inserted, {skipped} already existed, {warnings} warnings → {len(invoice_id_map)} total mapped")
    return invoice_id_map


def migrate_invoice_lines(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    invoice_id_map: dict,
    product_id_map: dict,
) -> dict:
    """
    Migrate sqlite.invoice_items → pg.invoice_lines.
    Returns item_id_map: {sqlite_id: pg_id}.
    """
    item_id_map: dict = {}
    rows = _sqlite_rows(
        sqlite_conn,
        """
        SELECT id, invoice_id, product_id, supplier_reference,
               supplier_raw_description, quantity, unit_price, total_price
        FROM invoice_items
        ORDER BY invoice_id, id
        """,
    )

    cur = pg_conn.cursor()
    inserted = 0
    skipped = 0
    warnings = 0

    # Track line_number per invoice
    line_counters: dict = {}

    for row in rows:
        sqlite_id = row["id"]
        sqlite_invoice_id = row["invoice_id"]

        if sqlite_invoice_id not in invoice_id_map:
            print(f"  WARNING: invoice_items row {sqlite_id}: unknown invoice_id {sqlite_invoice_id}, skipping")
            warnings += 1
            continue

        pg_invoice_id = invoice_id_map[sqlite_invoice_id]

        # Idempotency: detect by invoice_id + supplier_reference + original_description combo.
        supplier_code = row["supplier_reference"]
        original_description = row["supplier_raw_description"]
        quantity = row["quantity"]
        unit_price = row["unit_price"]
        subtotal = row["total_price"]

        cur.execute(
            """
            SELECT id FROM invoice_lines
            WHERE invoice_id = %s
              AND (supplier_code = %s OR (supplier_code IS NULL AND %s IS NULL))
              AND (original_description = %s OR (original_description IS NULL AND %s IS NULL))
            """,
            (pg_invoice_id, supplier_code, supplier_code, original_description, original_description),
        )
        existing = cur.fetchone()
        if existing:
            item_id_map[sqlite_id] = existing[0]
            skipped += 1
            continue

        # Assign sequential line_number per invoice
        line_counters[pg_invoice_id] = line_counters.get(pg_invoice_id, 0) + 1
        line_number = line_counters[pg_invoice_id]

        cur.execute(
            """
            INSERT INTO invoice_lines
                (invoice_id, line_number, supplier_code, original_description,
                 quantity, unit, unit_price, subtotal,
                 status, extraction_confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                pg_invoice_id,
                line_number,
                supplier_code or None,
                original_description or None,
                quantity,
                "ud",
                unit_price,
                subtotal,
                "consolidated",
                0.85,
            ),
        )
        pg_id = cur.fetchone()[0]
        item_id_map[sqlite_id] = pg_id
        inserted += 1

    pg_conn.commit()
    print(f"  invoice_lines: {inserted} inserted, {skipped} already existed, {warnings} warnings → {len(item_id_map)} total mapped")
    return item_id_map


def migrate_price_history(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    product_id_map: dict,
    supplier_id_map: dict,
    item_id_map: dict,
) -> None:
    """
    Migrate sqlite.latest_prices → pg.price_history.
    Quantity is resolved from sqlite.invoice_items via invoice_item_id.
    """
    # Build a fast quantity lookup from SQLite invoice_items
    qty_rows = _sqlite_rows(sqlite_conn, "SELECT id, quantity FROM invoice_items")
    sqlite_item_qty: dict = {r["id"]: r["quantity"] for r in qty_rows}

    rows = _sqlite_rows(
        sqlite_conn,
        """
        SELECT id, product_id, supplier_id, invoice_date, unit_price, invoice_item_id
        FROM latest_prices
        ORDER BY id
        """,
    )

    cur = pg_conn.cursor()
    inserted = 0
    skipped = 0
    warnings = 0

    for row in rows:
        sqlite_id = row["id"]
        sqlite_product_id = row["product_id"]
        sqlite_supplier_id = row["supplier_id"]
        sqlite_item_id = row["invoice_item_id"]

        if sqlite_product_id not in product_id_map:
            print(f"  WARNING: latest_prices row {sqlite_id}: unknown product_id {sqlite_product_id}, skipping")
            warnings += 1
            continue
        if sqlite_supplier_id not in supplier_id_map:
            print(f"  WARNING: latest_prices row {sqlite_id}: unknown supplier_id {sqlite_supplier_id}, skipping")
            warnings += 1
            continue

        material_id = product_id_map[sqlite_product_id]
        provider_id = supplier_id_map[sqlite_supplier_id]
        invoice_line_id = item_id_map.get(sqlite_item_id) if sqlite_item_id is not None else None
        unit_price = row["unit_price"]
        invoice_date = row["invoice_date"]
        quantity = sqlite_item_qty.get(sqlite_item_id) if sqlite_item_id is not None else None

        # Idempotency: skip if exact duplicate already present (same material, provider, date, price).
        cur.execute(
            """
            SELECT id FROM price_history
            WHERE material_id = %s
              AND provider_id = %s
              AND purchase_date = %s
              AND unit_price_original = %s
            """,
            (material_id, provider_id, invoice_date or None, unit_price),
        )
        if cur.fetchone():
            skipped += 1
            continue

        if not invoice_date:
            print(f"  WARNING: latest_prices row {sqlite_id}: missing invoice_date, skipping")
            warnings += 1
            continue

        cur.execute(
            """
            INSERT INTO price_history
                (material_id, provider_id, invoice_line_id,
                 unit_price_original, unit,
                 unit_price_standard, standard_unit,
                 quantity, purchase_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                material_id,
                provider_id,
                invoice_line_id,
                unit_price,
                "ud",
                unit_price,   # no conversion needed; source unit is unknown
                "ud",
                quantity,
                invoice_date,
            ),
        )
        inserted += 1

    pg_conn.commit()
    print(f"  price_history: {inserted} inserted, {skipped} already existed, {warnings} warnings")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_migration(sqlite_path: str, db_url: str) -> None:
    print(f"Opening SQLite database: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    print(f"Connecting to PostgreSQL …")
    pg_conn = psycopg2.connect(db_url)
    pg_conn.autocommit = False

    # Counters for final summary (re-queried after migration)
    counts: dict = {}

    # ------------------------------------------------------------------ #
    # 1. suppliers → providers
    # ------------------------------------------------------------------ #
    print("\n[1/6] Migrating suppliers → providers …")
    try:
        supplier_id_map = migrate_providers(sqlite_conn, pg_conn)
        counts["providers"] = len(supplier_id_map)
    except Exception as exc:
        pg_conn.rollback()
        print(f"  ERROR during providers migration: {exc}")
        supplier_id_map = {}
        counts["providers"] = 0

    # ------------------------------------------------------------------ #
    # 2. products → materials_master
    # ------------------------------------------------------------------ #
    print("\n[2/6] Migrating products → materials_master …")
    try:
        product_id_map = migrate_materials(sqlite_conn, pg_conn)
        counts["materials"] = len(product_id_map)
    except Exception as exc:
        pg_conn.rollback()
        print(f"  ERROR during materials_master migration: {exc}")
        product_id_map = {}
        counts["materials"] = 0

    # ------------------------------------------------------------------ #
    # 3. product_aliases → materials_aliases
    # ------------------------------------------------------------------ #
    print("\n[3/6] Migrating product_aliases → materials_aliases …")
    try:
        migrate_aliases(sqlite_conn, pg_conn, supplier_id_map, product_id_map)
    except Exception as exc:
        pg_conn.rollback()
        print(f"  ERROR during materials_aliases migration: {exc}")

    # ------------------------------------------------------------------ #
    # 4. invoices → invoices
    # ------------------------------------------------------------------ #
    print("\n[4/6] Migrating invoices → invoices …")
    try:
        invoice_id_map = migrate_invoices(sqlite_conn, pg_conn, supplier_id_map)
        counts["invoices"] = len(invoice_id_map)
    except Exception as exc:
        pg_conn.rollback()
        print(f"  ERROR during invoices migration: {exc}")
        invoice_id_map = {}
        counts["invoices"] = 0

    # ------------------------------------------------------------------ #
    # 5. invoice_items → invoice_lines
    # ------------------------------------------------------------------ #
    print("\n[5/6] Migrating invoice_items → invoice_lines …")
    try:
        item_id_map = migrate_invoice_lines(
            sqlite_conn, pg_conn, invoice_id_map, product_id_map
        )
        counts["lines"] = len(item_id_map)
    except Exception as exc:
        pg_conn.rollback()
        print(f"  ERROR during invoice_lines migration: {exc}")
        item_id_map = {}
        counts["lines"] = 0

    # ------------------------------------------------------------------ #
    # 6. latest_prices → price_history
    # ------------------------------------------------------------------ #
    print("\n[6/6] Migrating latest_prices → price_history …")
    try:
        migrate_price_history(
            sqlite_conn, pg_conn, product_id_map, supplier_id_map, item_id_map
        )
    except Exception as exc:
        pg_conn.rollback()
        print(f"  ERROR during price_history migration: {exc}")

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print(
        f"\nMigrated {counts.get('providers', 0)} providers, "
        f"{counts.get('materials', 0)} materials, "
        f"{counts.get('invoices', 0)} invoices, "
        f"{counts.get('lines', 0)} lines"
    )

    sqlite_conn.close()
    pg_conn.close()
    print("Done.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate data from the portable-app SQLite DB to PostgreSQL."
    )
    parser.add_argument(
        "--sqlite",
        default=os.environ.get("SQLITE_PATH"),
        help="Path to the SQLite database file (or set SQLITE_PATH env var)",
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL"),
        help="PostgreSQL connection URL (or set DATABASE_URL env var). "
             "Supports postgresql+asyncpg:// prefix (converted automatically).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.sqlite:
        print("ERROR: SQLite path is required. Use --sqlite or set SQLITE_PATH.")
        sys.exit(1)
    if not os.path.isfile(args.sqlite):
        print(f"ERROR: SQLite file not found: {args.sqlite}")
        sys.exit(1)
    if not args.db_url:
        print("ERROR: PostgreSQL URL is required. Use --db-url or set DATABASE_URL.")
        sys.exit(1)

    db_url = _normalize_db_url(args.db_url)
    run_migration(args.sqlite, db_url)


if __name__ == "__main__":
    main()
