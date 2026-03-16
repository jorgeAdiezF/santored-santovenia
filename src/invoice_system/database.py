from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProductPricePoint:
    canonical_product: str
    supplier_name: str
    invoice_date: str
    unit_price: float


class InvoiceDB:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                canonical_name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS product_aliases (
                id INTEGER PRIMARY KEY,
                supplier_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                UNIQUE(supplier_id, alias),
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY,
                supplier_id INTEGER NOT NULL,
                invoice_number TEXT,
                invoice_date TEXT NOT NULL,
                source_file TEXT,
                ingested_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
            );

            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                supplier_raw_description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS latest_prices (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                supplier_id INTEGER NOT NULL,
                invoice_date TEXT NOT NULL,
                unit_price REAL NOT NULL,
                invoice_item_id INTEGER NOT NULL,
                UNIQUE(product_id, supplier_id),
                FOREIGN KEY(product_id) REFERENCES products(id),
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY(invoice_item_id) REFERENCES invoice_items(id)
            );
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def get_or_create_supplier(self, name: str) -> int:
        row = self.conn.execute("SELECT id FROM suppliers WHERE name = ?", (name,)).fetchone()
        if row:
            return int(row["id"])
        cur = self.conn.execute("INSERT INTO suppliers(name) VALUES (?)", (name,))
        self.conn.commit()
        return int(cur.lastrowid)

    def get_or_create_product(self, canonical_name: str) -> int:
        row = self.conn.execute(
            "SELECT id FROM products WHERE canonical_name = ?", (canonical_name,)
        ).fetchone()
        if row:
            return int(row["id"])
        cur = self.conn.execute(
            "INSERT INTO products(canonical_name) VALUES (?)", (canonical_name,)
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def link_alias(self, supplier_id: int, alias: str, product_id: int) -> None:
        self.conn.execute(
            """
            INSERT INTO product_aliases(supplier_id, alias, product_id)
            VALUES (?, ?, ?)
            ON CONFLICT(supplier_id, alias) DO UPDATE SET product_id = excluded.product_id
            """,
            (supplier_id, alias, product_id),
        )
        self.conn.commit()

    def find_product_by_alias(self, supplier_id: int, alias: str) -> int | None:
        row = self.conn.execute(
            "SELECT product_id FROM product_aliases WHERE supplier_id = ? AND alias = ?",
            (supplier_id, alias),
        ).fetchone()
        if row:
            return int(row["product_id"])
        return None

    def create_invoice(
        self, supplier_id: int, invoice_number: str | None, invoice_date: str, source_file: str | None
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO invoices(supplier_id, invoice_number, invoice_date, source_file)
            VALUES (?, ?, ?, ?)
            """,
            (supplier_id, invoice_number, invoice_date, source_file),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_invoice_item(
        self,
        invoice_id: int,
        product_id: int,
        supplier_raw_description: str,
        quantity: float,
        unit_price: float,
        total_price: float,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO invoice_items(invoice_id, product_id, supplier_raw_description, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (invoice_id, product_id, supplier_raw_description, quantity, unit_price, total_price),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_latest_price(
        self,
        product_id: int,
        supplier_id: int,
        invoice_date: str,
        unit_price: float,
        invoice_item_id: int,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO latest_prices(product_id, supplier_id, invoice_date, unit_price, invoice_item_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(product_id, supplier_id) DO UPDATE SET
              invoice_date = excluded.invoice_date,
              unit_price = excluded.unit_price,
              invoice_item_id = excluded.invoice_item_id
            WHERE excluded.invoice_date >= latest_prices.invoice_date
            """,
            (product_id, supplier_id, invoice_date, unit_price, invoice_item_id),
        )
        self.conn.commit()

    def get_latest_price(self, canonical_product: str, supplier_name: str) -> float | None:
        row = self.conn.execute(
            """
            SELECT lp.unit_price
            FROM latest_prices lp
            JOIN products p ON p.id = lp.product_id
            JOIN suppliers s ON s.id = lp.supplier_id
            WHERE p.canonical_name = ? AND s.name = ?
            """,
            (canonical_product, supplier_name),
        ).fetchone()
        return float(row["unit_price"]) if row else None

    def price_evolution(self, canonical_product: str) -> list[ProductPricePoint]:
        rows = self.conn.execute(
            """
            SELECT p.canonical_name, s.name AS supplier_name, i.invoice_date, ii.unit_price
            FROM invoice_items ii
            JOIN products p ON p.id = ii.product_id
            JOIN invoices i ON i.id = ii.invoice_id
            JOIN suppliers s ON s.id = i.supplier_id
            WHERE p.canonical_name = ?
            ORDER BY i.invoice_date
            """,
            (canonical_product,),
        ).fetchall()
        return [
            ProductPricePoint(
                canonical_product=row["canonical_name"],
                supplier_name=row["supplier_name"],
                invoice_date=row["invoice_date"],
                unit_price=float(row["unit_price"]),
            )
            for row in rows
        ]
