import express from "express";
import cors from "cors";
import presupuestosRouter, { getFull } from "./routes/presupuestos.js";
import plantillasRouter from "./routes/plantillas.js";
import { buildPresupuestoPdf } from "./pdf.js";
import { buildPresupuestoExcel } from "./excel.js";

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api/presupuestos", presupuestosRouter);
app.use("/api/plantillas", plantillasRouter);

app.get("/api/presupuestos/:id/pdf", (req, res) => {
  const full = getFull(req.params.id);
  if (!full) return res.status(404).json({ error: "No encontrado" });
  buildPresupuestoPdf(full, res);
});

app.get("/api/presupuestos/:id/excel", async (req, res) => {
  const full = getFull(req.params.id);
  if (!full) return res.status(404).json({ error: "No encontrado" });
  await buildPresupuestoExcel(full, res);
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`Servidor escuchando en http://localhost:${PORT}`));
