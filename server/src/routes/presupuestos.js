import express from "express";
import db from "../db.js";

const router = express.Router();

function getFull(id) {
  const presupuesto = db.prepare("SELECT * FROM presupuestos WHERE id = ?").get(id);
  if (!presupuesto) return null;

  const conceptos = db
    .prepare("SELECT * FROM conceptos WHERE presupuestoId = ? ORDER BY orderIndex")
    .all(id);

  let totalEstimacion1 = 0;
  let totalEstimacion2 = 0;

  for (const concepto of conceptos) {
    const componentes = db
      .prepare("SELECT * FROM componentes WHERE conceptoId = ? ORDER BY orderIndex")
      .all(concepto.id);

    let subtotal = 0;
    for (const c of componentes) {
      c.total = c.cantidad * c.precioUnitario;
      subtotal += c.total;
    }

    concepto.componentes = componentes;
    concepto.subtotal = subtotal;
    concepto.estimacion1 = subtotal * 1.2 + concepto.horas * presupuesto.hourlyRate;
    concepto.estimacion2 = subtotal * presupuesto.multiplier;

    totalEstimacion1 += concepto.estimacion1;
    totalEstimacion2 += concepto.estimacion2;
  }

  presupuesto.conceptos = conceptos;
  presupuesto.totalEstimacion1 = totalEstimacion1;
  presupuesto.totalEstimacion2 = totalEstimacion2;
  return presupuesto;
}

router.get("/", (req, res) => {
  const rows = db
    .prepare("SELECT id, cliente, proyecto, createdAt, updatedAt FROM presupuestos ORDER BY updatedAt DESC")
    .all();
  res.json(rows);
});

router.get("/:id", (req, res) => {
  const full = getFull(req.params.id);
  if (!full) return res.status(404).json({ error: "No encontrado" });
  res.json(full);
});

router.post("/", (req, res) => {
  const { cliente, proyecto, multiplier = 1.5, hourlyRate = 35 } = req.body;
  if (!cliente?.trim() || !proyecto?.trim()) {
    return res.status(400).json({ error: "Cliente y proyecto son obligatorios" });
  }
  const result = db
    .prepare("INSERT INTO presupuestos (cliente, proyecto, multiplier, hourlyRate) VALUES (?, ?, ?, ?)")
    .run(cliente.trim(), proyecto.trim(), multiplier, hourlyRate);
  res.status(201).json(getFull(result.lastInsertRowid));
});

router.put("/:id", (req, res) => {
  const { cliente, proyecto, multiplier, hourlyRate } = req.body;
  const existing = db.prepare("SELECT * FROM presupuestos WHERE id = ?").get(req.params.id);
  if (!existing) return res.status(404).json({ error: "No encontrado" });

  db.prepare(
    "UPDATE presupuestos SET cliente = ?, proyecto = ?, multiplier = ?, hourlyRate = ?, updatedAt = datetime('now') WHERE id = ?"
  ).run(
    cliente ?? existing.cliente,
    proyecto ?? existing.proyecto,
    multiplier ?? existing.multiplier,
    hourlyRate ?? existing.hourlyRate,
    req.params.id
  );
  res.json(getFull(req.params.id));
});

router.delete("/:id", (req, res) => {
  db.prepare("DELETE FROM presupuestos WHERE id = ?").run(req.params.id);
  res.status(204).end();
});

router.post("/:id/conceptos", (req, res) => {
  const { nombre, horas = 0 } = req.body;
  if (!nombre?.trim()) return res.status(400).json({ error: "Nombre obligatorio" });

  const { maxOrder } = db
    .prepare("SELECT COALESCE(MAX(orderIndex), -1) AS maxOrder FROM conceptos WHERE presupuestoId = ?")
    .get(req.params.id);

  db.prepare("INSERT INTO conceptos (presupuestoId, nombre, horas, orderIndex) VALUES (?, ?, ?, ?)").run(
    req.params.id,
    nombre.trim(),
    horas,
    maxOrder + 1
  );
  touch(req.params.id);
  res.status(201).json(getFull(req.params.id));
});

router.put("/conceptos/:conceptoId", (req, res) => {
  const { nombre, horas } = req.body;
  const concepto = db.prepare("SELECT * FROM conceptos WHERE id = ?").get(req.params.conceptoId);
  if (!concepto) return res.status(404).json({ error: "No encontrado" });

  db.prepare("UPDATE conceptos SET nombre = ?, horas = ? WHERE id = ?").run(
    nombre ?? concepto.nombre,
    horas ?? concepto.horas,
    req.params.conceptoId
  );
  touch(concepto.presupuestoId);
  res.json(getFull(concepto.presupuestoId));
});

router.delete("/conceptos/:conceptoId", (req, res) => {
  const concepto = db.prepare("SELECT * FROM conceptos WHERE id = ?").get(req.params.conceptoId);
  if (!concepto) return res.status(404).json({ error: "No encontrado" });
  db.prepare("DELETE FROM conceptos WHERE id = ?").run(req.params.conceptoId);
  touch(concepto.presupuestoId);
  res.json(getFull(concepto.presupuestoId));
});

router.post("/conceptos/:conceptoId/componentes", (req, res) => {
  const { nombre, cantidad = 0, unidad = "unidad", precioUnitario = 0 } = req.body;
  const concepto = db.prepare("SELECT * FROM conceptos WHERE id = ?").get(req.params.conceptoId);
  if (!concepto) return res.status(404).json({ error: "Concepto no encontrado" });
  if (!nombre?.trim()) return res.status(400).json({ error: "Nombre obligatorio" });

  const { maxOrder } = db
    .prepare("SELECT COALESCE(MAX(orderIndex), -1) AS maxOrder FROM componentes WHERE conceptoId = ?")
    .get(req.params.conceptoId);

  db.prepare(
    "INSERT INTO componentes (conceptoId, nombre, cantidad, unidad, precioUnitario, orderIndex) VALUES (?, ?, ?, ?, ?, ?)"
  ).run(req.params.conceptoId, nombre.trim(), cantidad, unidad, precioUnitario, maxOrder + 1);

  touch(concepto.presupuestoId);
  res.status(201).json(getFull(concepto.presupuestoId));
});

router.put("/componentes/:componenteId", (req, res) => {
  const { nombre, cantidad, unidad, precioUnitario } = req.body;
  const componente = db.prepare("SELECT * FROM componentes WHERE id = ?").get(req.params.componenteId);
  if (!componente) return res.status(404).json({ error: "No encontrado" });
  const concepto = db.prepare("SELECT * FROM conceptos WHERE id = ?").get(componente.conceptoId);

  db.prepare(
    "UPDATE componentes SET nombre = ?, cantidad = ?, unidad = ?, precioUnitario = ? WHERE id = ?"
  ).run(
    nombre ?? componente.nombre,
    cantidad ?? componente.cantidad,
    unidad ?? componente.unidad,
    precioUnitario ?? componente.precioUnitario,
    req.params.componenteId
  );
  touch(concepto.presupuestoId);
  res.json(getFull(concepto.presupuestoId));
});

router.delete("/componentes/:componenteId", (req, res) => {
  const componente = db.prepare("SELECT * FROM componentes WHERE id = ?").get(req.params.componenteId);
  if (!componente) return res.status(404).json({ error: "No encontrado" });
  const concepto = db.prepare("SELECT * FROM conceptos WHERE id = ?").get(componente.conceptoId);
  db.prepare("DELETE FROM componentes WHERE id = ?").run(req.params.componenteId);
  touch(concepto.presupuestoId);
  res.json(getFull(concepto.presupuestoId));
});

function touch(presupuestoId) {
  db.prepare("UPDATE presupuestos SET updatedAt = datetime('now') WHERE id = ?").run(presupuestoId);
}

export { getFull };
export default router;
