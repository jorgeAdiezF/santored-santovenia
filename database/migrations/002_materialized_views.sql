-- Migration 002: Materialized Views and Refresh Functions

BEGIN;

-- Function to refresh last_price_per_material materialized view
CREATE OR REPLACE FUNCTION refresh_last_price_per_material()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY last_price_per_material;
END;
$$;

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM refresh_last_price_per_material();
    RAISE NOTICE 'All materialized views refreshed at %', NOW();
END;
$$;

-- Materialized view: monthly spend summary
CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_spend_summary AS
SELECT
    DATE_TRUNC('month', i.invoice_date) AS month,
    p.id AS provider_id,
    p.fiscal_name AS provider_name,
    COUNT(DISTINCT i.id) AS invoice_count,
    SUM(i.total) AS total_spend,
    SUM(i.vat) AS total_vat,
    i.currency
FROM invoices i
JOIN providers p ON p.id = i.provider_id
WHERE i.status = 'validated'
  AND i.invoice_date IS NOT NULL
GROUP BY DATE_TRUNC('month', i.invoice_date), p.id, p.fiscal_name, i.currency;

CREATE UNIQUE INDEX IF NOT EXISTS idx_monthly_spend_month_provider
    ON monthly_spend_summary(month, provider_id);

-- Materialized view: material purchase stats
CREATE MATERIALIZED VIEW IF NOT EXISTS material_purchase_stats AS
SELECT
    mm.id AS material_id,
    mm.master_code,
    mm.family,
    mm.subfamily,
    mm.normalized_description,
    COUNT(ph.id) AS purchase_count,
    SUM(ph.quantity) AS total_quantity,
    AVG(ph.unit_price_standard) AS avg_unit_price,
    MIN(ph.unit_price_standard) AS min_unit_price,
    MAX(ph.unit_price_standard) AS max_unit_price,
    MIN(ph.purchase_date) AS first_purchase,
    MAX(ph.purchase_date) AS last_purchase
FROM materials_master mm
LEFT JOIN price_history ph ON ph.material_id = mm.id
GROUP BY mm.id, mm.master_code, mm.family, mm.subfamily, mm.normalized_description;

CREATE UNIQUE INDEX IF NOT EXISTS idx_material_purchase_stats_material_id
    ON material_purchase_stats(material_id);

-- Function to refresh monthly spend summary
CREATE OR REPLACE FUNCTION refresh_monthly_spend_summary()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_spend_summary;
END;
$$;

-- Function to refresh material purchase stats
CREATE OR REPLACE FUNCTION refresh_material_purchase_stats()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY material_purchase_stats;
END;
$$;

-- Update refresh_all to include new views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM refresh_last_price_per_material();
    PERFORM refresh_monthly_spend_summary();
    PERFORM refresh_material_purchase_stats();
    RAISE NOTICE 'All materialized views refreshed at %', NOW();
END;
$$;

-- Trigger function to refresh price materialized view after price_history insert
CREATE OR REPLACE FUNCTION trigger_refresh_price_view()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    -- Use a deferred refresh to avoid locking on each insert
    -- In production, this would be done via a scheduled job
    PERFORM pg_notify('refresh_materialized_views', 'price_history');
    RETURN NEW;
END;
$$;

-- Trigger on price_history
DROP TRIGGER IF EXISTS trg_price_history_refresh ON price_history;
CREATE TRIGGER trg_price_history_refresh
    AFTER INSERT OR UPDATE ON price_history
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_refresh_price_view();

-- Audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_events (event_type, entity_type, entity_id, old_value, new_value)
        VALUES (
            'UPDATE',
            TG_TABLE_NAME,
            NEW.id,
            row_to_json(OLD),
            row_to_json(NEW)
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_events (event_type, entity_type, entity_id, old_value)
        VALUES (
            'DELETE',
            TG_TABLE_NAME,
            OLD.id,
            row_to_json(OLD)
        );
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

-- Apply audit triggers to key tables
DROP TRIGGER IF EXISTS trg_audit_invoices ON invoices;
CREATE TRIGGER trg_audit_invoices
    AFTER UPDATE OR DELETE ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

DROP TRIGGER IF EXISTS trg_audit_invoice_lines ON invoice_lines;
CREATE TRIGGER trg_audit_invoice_lines
    AFTER UPDATE OR DELETE ON invoice_lines
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

COMMIT;
