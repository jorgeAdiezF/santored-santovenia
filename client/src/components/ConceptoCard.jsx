import { useState } from "react";
import { api } from "../api.js";

const UNIDADES = ["m.l.", "m²", "kg", "unidad", "total", "otro"];

export default function ConceptoCard({ concepto, plantillas, onChange }) {
  const [nombre, setNombre] = useState(concepto.nombre);
  const [horas, setHoras] = useState(concepto.horas);
  const [form, setForm] = useState({ nombre: "", cantidad: 1, unidad: "unidad", precioUnitario: 0 });
  const [plantillaId, setPlantillaId] = useState("");

  async function saveConcepto() {
    await api.updateConcepto(concepto.id, { nombre, horas: Number(horas) });
    onChange();
  }

  async function deleteConcepto() {
    if (!confirm(`¿Eliminar el concepto "${concepto.nombre}"?`)) return;
    await api.deleteConcepto(concepto.id);
    onChange();
  }

  async function addComponente(e) {
    e.preventDefault();
    if (!form.nombre.trim()) return;
    await api.addComponente(concepto.id, form);
    setForm({ nombre: "", cantidad: 1, unidad: "unidad", precioUnitario: 0 });
    onChange();
  }

  async function addFromPlantilla() {
    const plantilla = plantillas.find((p) => String(p.id) === plantillaId);
    if (!plantilla) return;
    await api.addComponente(concepto.id, {
      nombre: plantilla.nombre,
      cantidad: 1,
      unidad: plantilla.unidad,
      precioUnitario: plantilla.precioUnitario,
    });
    setPlantillaId("");
    onChange();
  }

  async function updateComponente(componenteId, field, value) {
    await api.updateComponente(componenteId, { [field]: value });
    onChange();
  }

  async function deleteComponente(componenteId) {
    await api.deleteComponente(componenteId);
    onChange();
  }

  return (
    <section className="card concepto">
      <div className="row">
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} onBlur={saveConcepto} />
        <label>
          Horas
          <input
            type="number"
            step="0.5"
            value={horas}
            onChange={(e) => setHoras(e.target.value)}
            onBlur={saveConcepto}
          />
        </label>
        <button className="danger" onClick={deleteConcepto}>
          Eliminar concepto
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Componente</th>
            <th>Cantidad</th>
            <th>Unidad</th>
            <th>Precio unitario</th>
            <th>Total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {concepto.componentes.map((c) => (
            <tr key={c.id}>
              <td>
                <input
                  defaultValue={c.nombre}
                  onBlur={(e) => updateComponente(c.id, "nombre", e.target.value)}
                />
              </td>
              <td>
                <input
                  type="number"
                  step="0.01"
                  defaultValue={c.cantidad}
                  onBlur={(e) => updateComponente(c.id, "cantidad", Number(e.target.value))}
                />
              </td>
              <td>
                <select
                  defaultValue={c.unidad}
                  onChange={(e) => updateComponente(c.id, "unidad", e.target.value)}
                >
                  {UNIDADES.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <input
                  type="number"
                  step="0.01"
                  defaultValue={c.precioUnitario}
                  onBlur={(e) => updateComponente(c.id, "precioUnitario", Number(e.target.value))}
                />
              </td>
              <td>{c.total.toFixed(2)} €</td>
              <td>
                <button className="danger" onClick={() => deleteComponente(c.id)}>
                  X
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <form onSubmit={addComponente} className="row">
        <input
          placeholder="Nuevo componente"
          value={form.nombre}
          onChange={(e) => setForm({ ...form, nombre: e.target.value })}
        />
        <input
          type="number"
          step="0.01"
          placeholder="Cantidad"
          value={form.cantidad}
          onChange={(e) => setForm({ ...form, cantidad: Number(e.target.value) })}
        />
        <select value={form.unidad} onChange={(e) => setForm({ ...form, unidad: e.target.value })}>
          {UNIDADES.map((u) => (
            <option key={u} value={u}>
              {u}
            </option>
          ))}
        </select>
        <input
          type="number"
          step="0.01"
          placeholder="Precio unitario"
          value={form.precioUnitario}
          onChange={(e) => setForm({ ...form, precioUnitario: Number(e.target.value) })}
        />
        <button type="submit">Añadir componente</button>
      </form>

      {plantillas.length > 0 && (
        <div className="row">
          <select value={plantillaId} onChange={(e) => setPlantillaId(e.target.value)}>
            <option value="">Añadir desde catálogo...</option>
            {plantillas.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre} ({p.precioUnitario.toFixed(2)} €/{p.unidad})
              </option>
            ))}
          </select>
          <button type="button" onClick={addFromPlantilla} disabled={!plantillaId}>
            Añadir
          </button>
        </div>
      )}

      <div className="estimaciones">
        <p>Subtotal: {concepto.subtotal.toFixed(2)} €</p>
        <p>
          <strong>Estimación 1 (con horas):</strong> {concepto.estimacion1.toFixed(2)} €
        </p>
        <p>
          <strong>Estimación 2 (con multiplicador):</strong> {concepto.estimacion2.toFixed(2)} €
        </p>
      </div>
    </section>
  );
}
