# Migration: portable app SQLite → PostgreSQL

This script migrates historical data from the portable invoice app's SQLite
database into the new PostgreSQL system.

## Prerequisites

- Python 3.8+
- `psycopg2` (or `psycopg2-binary`) installed:
  ```
  pip install psycopg2-binary
  ```
- The target PostgreSQL database must already have the schema applied
  (`database/migrations/001_initial_schema.sql`).

## Running the migration

### Option A — command-line arguments

```bash
python scripts/migrate_from_portable.py \
  --sqlite /path/to/invoices.db \
  --db-url postgresql://user:password@host:5432/dbname
```

### Option B — environment variables

```bash
export SQLITE_PATH=/path/to/invoices.db
export DATABASE_URL=postgresql://user:password@host:5432/dbname
python scripts/migrate_from_portable.py
```

`DATABASE_URL` values with the `postgresql+asyncpg://` prefix are accepted and
converted automatically.

## What gets migrated

| SQLite source      | PostgreSQL target    | Notes                                              |
|--------------------|----------------------|----------------------------------------------------|
| `suppliers`        | `providers`          | fiscal_name = trade_name = supplier name           |
| `products`         | `materials_master`   | master_code auto-generated as `MAT-NNNNN`; family inferred from name prefix |
| `product_aliases`  | `materials_aliases`  | confidence fixed at 0.9                            |
| `invoices`         | `invoices`           | status = "consolidated"; detected_doc_id = NULL    |
| `invoice_items`    | `invoice_lines`      | unit = "ud"; status = "consolidated"; confidence = 0.85 |
| `latest_prices`    | `price_history`      | unit = standard_unit = "ud"; quantity from invoice_items |

`pending_reviews` has no equivalent target table and is not migrated.

## Idempotency

The script is safe to run multiple times. Before each insert it checks for an
existing matching row and skips it if found:

- **providers** — matched on `fiscal_name`
- **materials_master** — matched on `master_code` (`MAT-NNNNN`)
- **materials_aliases** — matched on `material_id + provider_id + supplier_description`
- **invoices** — matched on `provider_id + invoice_number`
- **invoice_lines** — matched on `invoice_id + supplier_code + original_description`
- **price_history** — matched on `material_id + provider_id + purchase_date + unit_price_original`

## Progress output

The script prints step-by-step progress and a final summary line, for example:

```
[1/6] Migrating suppliers → providers …
  providers: 12 inserted, 0 already existed → 12 total mapped

[2/6] Migrating products → materials_master …
  materials_master: 340 inserted, 0 already existed → 340 total mapped
...
Migrated 12 providers, 340 materials, 850 invoices, 4210 lines
Done.
```

Warnings about unmapped foreign keys are printed but do not stop the migration.
Each table is committed independently, so a failure in one section does not roll
back previously committed data.
