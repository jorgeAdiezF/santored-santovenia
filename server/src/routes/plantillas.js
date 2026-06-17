import express from "express";
import db from "../db.js";

const router = express.Router();

router.get("/", (req, res) => {
  res.json(db.prepare("SELECT * FROM plantillas ORDER BY nombre").all());
});

router.post("/", (req, res) => {
  const { nombre, unidad = "unidad", precioUnitario = 0 } = req.body;
  if (!nombre?.trim()) return res.status(400).json({ error: "Nombre obligatorio" });
  const result = db
    .prepare("INSERT INTO plantillas (nombre, unidad, precioUnitario) VALUES (?, ?, ?)")
    .run(nombre.trim(), unidad, precioUnitario);
  res.status(201).json(db.prepare("SELECT * FROM plantillas WHERE id = ?").get(result.lastInsertRowid));
});

router.put("/:id", (req, res) => {
  const existing = db.prepare("SELECT * FROM plantillas WHERE id = ?").get(req.params.id);
  if (!existing) return res.status(404).json({ error: "No encontrado" });
  const { nombre, unidad, precioUnitario } = req.body;
  db.prepare("UPDATE plantillas SET nombre = ?, unidad = ?, precioUnitario = ? WHERE id = ?").run(
    nombre ?? existing.nombre,
    unidad ?? existing.unidad,
    precioUnitario ?? existing.precioUnitario,
    req.params.id
  );
  res.json(db.prepare("SELECT * FROM plantillas WHERE id = ?").get(req.params.id));
});

router.delete("/:id", (req, res) => {
  db.prepare("DELETE FROM plantillas WHERE id = ?").run(req.params.id);
  res.status(204).end();
});

export default router;
