-- Invoice Processing System - Initial Schema
-- Migration 001

BEGIN;

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    name VARCHAR(200),
    email VARCHAR(200) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- Providers table
CREATE TABLE IF NOT EXISTS providers (
    id SERIAL PRIMARY KEY,
    fiscal_name VARCHAR(200) NOT NULL,
    trade_name VARCHAR(200),
    tax_id VARCHAR(50) UNIQUE,
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- Provider aliases
CREATE TABLE IF NOT EXISTS provider_aliases (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    alias_text VARCHAR(300) NOT NULL
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    filename VARCHAR(300) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    storage_path VARCHAR(500) NOT NULL,
    upload_user_id INTEGER REFERENCES users(id),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'uploaded',
    page_count INTEGER
);

-- Pages table
CREATE TABLE IF NOT EXISTS pages (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    UNIQUE(document_id, page_number)
);

-- Detected documents (segments)
CREATE TABLE IF NOT EXISTS detected_docs (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    start_page INTEGER NOT NULL,
    end_page INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'detected',
    confidence FLOAT DEFAULT 0.0
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    id SERIAL PRIMARY KEY,
    detected_doc_id INTEGER REFERENCES detected_docs(id),
    provider_id INTEGER REFERENCES providers(id),
    tax_id VARCHAR(50),
    invoice_number VARCHAR(100),
    invoice_date DATE,
    subtotal NUMERIC(15, 2),
    vat NUMERIC(15, 2),
    total NUMERIC(15, 2),
    currency VARCHAR(10) DEFAULT 'EUR',
    status VARCHAR(50) DEFAULT 'pending_review',
    validated_at TIMESTAMP WITH TIME ZONE,
    validated_by INTEGER REFERENCES users(id)
);

-- Invoice lines table
CREATE TABLE IF NOT EXISTS invoice_lines (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    supplier_code VARCHAR(100),
    original_description TEXT,
    quantity NUMERIC(15, 4),
    unit VARCHAR(50),
    unit_price NUMERIC(15, 4),
    discount NUMERIC(5, 2) DEFAULT 0,
    subtotal NUMERIC(15, 2),
    tax_rate NUMERIC(5, 2) DEFAULT 0,
    page_id INTEGER REFERENCES pages(id),
    status VARCHAR(50) DEFAULT 'pending_homologation',
    extraction_confidence FLOAT DEFAULT 0.0
);

-- Materials master catalog
CREATE TABLE IF NOT EXISTS materials_master (
    id SERIAL PRIMARY KEY,
    master_code VARCHAR(100) UNIQUE NOT NULL,
    family VARCHAR(100),
    subfamily VARCHAR(100),
    normalized_description TEXT NOT NULL,
    dimensions VARCHAR(200),
    thickness VARCHAR(50),
    finish VARCHAR(100),
    base_unit VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Materials aliases (provider-specific codes/descriptions)
CREATE TABLE IF NOT EXISTS materials_aliases (
    id SERIAL PRIMARY KEY,
    material_id INTEGER NOT NULL REFERENCES materials_master(id) ON DELETE CASCADE,
    provider_id INTEGER REFERENCES providers(id),
    supplier_code VARCHAR(100),
    supplier_description TEXT,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Destinations (delivery/cost centers)
CREATE TABLE IF NOT EXISTS destinations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Invoice line destinations
CREATE TABLE IF NOT EXISTS invoice_line_destinations (
    id SERIAL PRIMARY KEY,
    invoice_line_id INTEGER NOT NULL REFERENCES invoice_lines(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id),
    notes TEXT,
    UNIQUE(invoice_line_id, destination_id)
);

-- Price history
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    material_id INTEGER NOT NULL REFERENCES materials_master(id),
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    invoice_line_id INTEGER REFERENCES invoice_lines(id),
    unit_price_original NUMERIC(15, 4) NOT NULL,
    unit VARCHAR(50),
    unit_price_standard NUMERIC(15, 4),
    standard_unit VARCHAR(50),
    quantity NUMERIC(15, 4),
    purchase_date DATE NOT NULL
);

-- Audit events
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    user_id INTEGER REFERENCES users(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    old_value JSONB,
    new_value JSONB,
    notes TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date);
CREATE INDEX IF NOT EXISTS idx_pages_document_id ON pages(document_id);
CREATE INDEX IF NOT EXISTS idx_detected_docs_document_id ON detected_docs(document_id);
CREATE INDEX IF NOT EXISTS idx_detected_docs_status ON detected_docs(status);
CREATE INDEX IF NOT EXISTS idx_invoices_provider_id ON invoices(provider_id);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_invoice_lines_invoice_id ON invoice_lines(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_lines_status ON invoice_lines(status);
CREATE INDEX IF NOT EXISTS idx_materials_aliases_material_id ON materials_aliases(material_id);
CREATE INDEX IF NOT EXISTS idx_materials_aliases_provider_id ON materials_aliases(provider_id);
CREATE INDEX IF NOT EXISTS idx_materials_master_family ON materials_master(family);
CREATE INDEX IF NOT EXISTS idx_price_history_material_id ON price_history(material_id);
CREATE INDEX IF NOT EXISTS idx_price_history_provider_id ON price_history(provider_id);
CREATE INDEX IF NOT EXISTS idx_price_history_purchase_date ON price_history(purchase_date);
CREATE INDEX IF NOT EXISTS idx_audit_events_entity ON audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_provider_aliases_provider_id ON provider_aliases(provider_id);

-- Materialized view: last price per material
CREATE MATERIALIZED VIEW IF NOT EXISTS last_price_per_material AS
SELECT DISTINCT ON (ph.material_id, ph.provider_id)
    ph.material_id,
    ph.provider_id,
    ph.unit_price_standard,
    ph.standard_unit,
    ph.purchase_date,
    p.fiscal_name AS provider_name,
    mm.normalized_description AS material_description
FROM price_history ph
JOIN providers p ON p.id = ph.provider_id
JOIN materials_master mm ON mm.id = ph.material_id
ORDER BY ph.material_id, ph.provider_id, ph.purchase_date DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_last_price_material_provider
    ON last_price_per_material(material_id, provider_id);

-- Initial data: Roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'System administrator with full access'),
    ('purchases', 'Purchases department - can review and validate invoices'),
    ('production', 'Production department - can assign destinations'),
    ('analytics', 'Analytics - read-only access to reports')
ON CONFLICT (name) DO NOTHING;

-- Initial admin user (password: admin123)
-- Hash generated with bcrypt cost factor 12
INSERT INTO users (username, password_hash, role_id, name, email, active)
SELECT
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewkE6mLXCK.cJQ2.',
    r.id,
    'System Administrator',
    'admin@invoices.local',
    TRUE
FROM roles r WHERE r.name = 'admin'
ON CONFLICT (username) DO NOTHING;

COMMIT;
