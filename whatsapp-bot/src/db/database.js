const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const config = require('../config');

let db;

function getDb() {
  if (!db) {
    const dbDir = path.dirname(path.resolve(config.dbPath));
    if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true });
    db = new Database(path.resolve(config.dbPath));
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    initSchema();
  }
  return db;
}

function initSchema() {
  db.exec(`
    -- ── Contactos ─────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS contacts (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      wa_phone    TEXT NOT NULL UNIQUE,
      name        TEXT,
      phone       TEXT,
      address     TEXT,
      created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- ── Conversaciones ────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS conversations (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      contact_id   INTEGER REFERENCES contacts(id),
      wa_phone     TEXT NOT NULL,
      category     TEXT,
      status       TEXT DEFAULT 'active',
      created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
      completed_at DATETIME
    );

    -- ── Mensajes (historial completo) ─────────────────────────
    CREATE TABLE IF NOT EXISTS messages (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id INTEGER REFERENCES conversations(id),
      direction       TEXT NOT NULL,
      content         TEXT NOT NULL,
      wa_message_id   TEXT,
      timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- ── Averías / Mantenimiento ───────────────────────────────
    CREATE TABLE IF NOT EXISTS incidents (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id INTEGER REFERENCES conversations(id),
      contact_id      INTEGER REFERENCES contacts(id),
      description     TEXT,
      urgency         TEXT DEFAULT 'normal',
      status          TEXT DEFAULT 'pending',
      notes           TEXT,
      created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- ── Leads comerciales ─────────────────────────────────────
    CREATE TABLE IF NOT EXISTS leads (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id INTEGER REFERENCES conversations(id),
      contact_id      INTEGER REFERENCES contacts(id),
      concept         TEXT,
      product_interest TEXT,
      catalog_info    TEXT,
      status          TEXT DEFAULT 'new',
      created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- ── Tickets (administración / general) ────────────────────
    CREATE TABLE IF NOT EXISTS tickets (
      id              INTEGER PRIMARY KEY AUTOINCREMENT,
      conversation_id INTEGER REFERENCES conversations(id),
      contact_id      INTEGER REFERENCES contacts(id),
      category        TEXT,
      subject         TEXT,
      description     TEXT,
      status          TEXT DEFAULT 'open',
      created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- ── Catálogo de productos y precios ───────────────────────
    CREATE TABLE IF NOT EXISTS catalog (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      category    TEXT NOT NULL,
      name        TEXT NOT NULL,
      description TEXT,
      price_from  REAL,
      price_to    REAL,
      unit        TEXT DEFAULT 'ud.',
      notes       TEXT,
      active      INTEGER DEFAULT 1,
      created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `);
}

// ── Contactos ──────────────────────────────────────────────────
function upsertContact(waPhone, data = {}) {
  const d = getDb();
  const existing = d.prepare('SELECT * FROM contacts WHERE wa_phone = ?').get(waPhone);
  if (!existing) {
    return d.prepare(
      'INSERT INTO contacts (wa_phone, name, phone, address) VALUES (?, ?, ?, ?)'
    ).run(waPhone, data.name || null, data.phone || null, data.address || null);
  }
  d.prepare(
    'UPDATE contacts SET name=COALESCE(?,name), phone=COALESCE(?,phone), address=COALESCE(?,address), updated_at=CURRENT_TIMESTAMP WHERE wa_phone=?'
  ).run(data.name || null, data.phone || null, data.address || null, waPhone);
  return d.prepare('SELECT * FROM contacts WHERE wa_phone = ?').get(waPhone);
}

function getContact(waPhone) {
  return getDb().prepare('SELECT * FROM contacts WHERE wa_phone = ?').get(waPhone);
}

// ── Conversaciones ─────────────────────────────────────────────
function createConversation(waPhone) {
  const result = getDb().prepare(
    'INSERT INTO conversations (wa_phone) VALUES (?)'
  ).run(waPhone);
  return result.lastInsertRowid;
}

function updateConversation(id, data) {
  getDb().prepare(
    'UPDATE conversations SET category=COALESCE(?,category), status=COALESCE(?,status), contact_id=COALESCE(?,contact_id), completed_at=COALESCE(?,completed_at) WHERE id=?'
  ).run(data.category || null, data.status || null, data.contactId || null, data.completedAt || null, id);
}

// ── Mensajes ───────────────────────────────────────────────────
function saveMessage(conversationId, direction, content, waMessageId = null) {
  return getDb().prepare(
    'INSERT INTO messages (conversation_id, direction, content, wa_message_id) VALUES (?, ?, ?, ?)'
  ).run(conversationId, direction, content, waMessageId);
}

function getMessages(conversationId) {
  return getDb().prepare(
    'SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC'
  ).all(conversationId);
}

// ── Incidencias ────────────────────────────────────────────────
function createIncident(data) {
  return getDb().prepare(
    'INSERT INTO incidents (conversation_id, contact_id, description, urgency) VALUES (?, ?, ?, ?)'
  ).run(data.conversationId, data.contactId, data.description, data.urgency || 'normal');
}

// ── Leads ──────────────────────────────────────────────────────
function createLead(data) {
  return getDb().prepare(
    'INSERT INTO leads (conversation_id, contact_id, concept, product_interest, catalog_info) VALUES (?, ?, ?, ?, ?)'
  ).run(data.conversationId, data.contactId, data.concept, data.productInterest || null, data.catalogInfo || null);
}

// ── Tickets ────────────────────────────────────────────────────
function createTicket(data) {
  return getDb().prepare(
    'INSERT INTO tickets (conversation_id, contact_id, category, subject, description) VALUES (?, ?, ?, ?, ?)'
  ).run(data.conversationId, data.contactId, data.category, data.subject, data.description);
}

// ── Catálogo ───────────────────────────────────────────────────
function searchCatalog(keyword) {
  const k = `%${keyword}%`;
  return getDb().prepare(
    'SELECT * FROM catalog WHERE active=1 AND (name LIKE ? OR description LIKE ? OR category LIKE ?)'
  ).all(k, k, k);
}

function getAllCatalog() {
  return getDb().prepare('SELECT * FROM catalog WHERE active=1 ORDER BY category, name').all();
}

function upsertCatalogItem(item) {
  const d = getDb();
  if (item.id) {
    d.prepare(
      'UPDATE catalog SET category=?, name=?, description=?, price_from=?, price_to=?, unit=?, notes=?, active=? WHERE id=?'
    ).run(item.category, item.name, item.description, item.priceFrom, item.priceTo, item.unit, item.notes, item.active ?? 1, item.id);
  } else {
    d.prepare(
      'INSERT INTO catalog (category, name, description, price_from, price_to, unit, notes) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).run(item.category, item.name, item.description, item.priceFrom, item.priceTo, item.unit || 'ud.', item.notes);
  }
}

// ── Dashboard (admin) ──────────────────────────────────────────
function getDashboardStats() {
  const d = getDb();
  return {
    contacts:   d.prepare('SELECT COUNT(*) as n FROM contacts').get().n,
    incidents:  d.prepare("SELECT COUNT(*) as n FROM incidents WHERE status='pending'").get().n,
    leads:      d.prepare("SELECT COUNT(*) as n FROM leads WHERE status='new'").get().n,
    tickets:    d.prepare("SELECT COUNT(*) as n FROM tickets WHERE status='open'").get().n,
    totalConvs: d.prepare('SELECT COUNT(*) as n FROM conversations').get().n,
  };
}

function getRecentActivity(limit = 20) {
  return getDb().prepare(`
    SELECT c.id, c.wa_phone, c.category, c.status, c.created_at,
           ct.name as contact_name
    FROM conversations c
    LEFT JOIN contacts ct ON c.contact_id = ct.id
    ORDER BY c.created_at DESC LIMIT ?
  `).all(limit);
}

module.exports = {
  getDb, upsertContact, getContact,
  createConversation, updateConversation,
  saveMessage, getMessages,
  createIncident, createLead, createTicket,
  searchCatalog, getAllCatalog, upsertCatalogItem,
  getDashboardStats, getRecentActivity,
};
