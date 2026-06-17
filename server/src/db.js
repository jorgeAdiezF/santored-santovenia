import Database from "better-sqlite3";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const db = new Database(path.join(__dirname, "..", "data.db"));

db.pragma("journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS presupuestos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    proyecto TEXT NOT NULL,
    multiplier REAL NOT NULL DEFAULT 1.5,
    hourlyRate REAL NOT NULL DEFAULT 35,
    createdAt TEXT NOT NULL DEFAULT (datetime('now')),
    updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS conceptos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    presupuestoId INTEGER NOT NULL REFERENCES presupuestos(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    horas REAL NOT NULL DEFAULT 0,
    orderIndex INTEGER NOT NULL DEFAULT 0
  );

  CREATE TABLE IF NOT EXISTS componentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conceptoId INTEGER NOT NULL REFERENCES conceptos(id) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    cantidad REAL NOT NULL DEFAULT 0,
    unidad TEXT NOT NULL DEFAULT 'unidad',
    precioUnitario REAL NOT NULL DEFAULT 0,
    orderIndex INTEGER NOT NULL DEFAULT 0
  );

  CREATE TABLE IF NOT EXISTS plantillas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    unidad TEXT NOT NULL DEFAULT 'unidad',
    precioUnitario REAL NOT NULL DEFAULT 0
  );
`);

export default db;
