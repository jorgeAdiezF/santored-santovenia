from __future__ import annotations

import argparse

from .service import InvoiceIngestionService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingesta automática de facturas")
    parser.add_argument("inputs", nargs="+", help="Archivos de factura (txt/pdf/imagen)")
    parser.add_argument("--db", default="invoices.db", help="Ruta de SQLite")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    service = InvoiceIngestionService(args.db)
    try:
        total = 0
        for path in args.inputs:
            total += service.ingest_file(path)
        print(f"Facturas procesadas: {total}")
    finally:
        service.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
