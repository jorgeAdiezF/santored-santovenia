import { useEffect, useState } from "react";
import { api } from "../api.js";

const UNIDADES = ["m.l.", "m²", "kg", "unidad", "total", "otro"];

export default function Plantillas() {
  const [plantillas, setPlantillas] = useState([]);
  const [form, setForm] = useState({ nombre: "", unidad: "unidad", precioUnitario: 0 });

  useEffect(() => {
    api.listPlantillas().then(setPlantillas);
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    if (!form.nombre.trim()) return;
    const nueva = await api.createPlantilla(form);
    setPlantillas((prev) => [...prev, nueva]);
    setForm({ nombre: "", unidad: "unidad", precioUnitario: 0 });
  }

  async function handleDelete(id) {
    await api.deletePlantilla(id);
    setPlantillas((prev) => prev.filter((p) => p.id !== id));
  }

  return (
    <div className="page">
      <section className="card">
        <h2>Catálogo de componentes reutilizables</h2>
        <p className="hint">
          Guarda aquí materiales/precios habituales para añadirlos rápido a cualquier presupuesto.
        </p>
        <form onSubmit={handleAdd} className="row">
          <input
            placeholder="Nombre del componente"
            value={form.nombre}
            onChange={(e) => setForm({ ...form, nombre: e.target.value })}
            required
          />
          <select
            value={form.unidad}
            onChange={(e) => setForm({ ...form, unidad: e.target.value })}
          >
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
          <button type="submit">Añadir</button>
        </form>

        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Unidad</th>
              <th>Precio</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {plantillas.map((p) => (
              <tr key={p.id}>
                <td>{p.nombre}</td>
                <td>{p.unidad}</td>
                <td>{p.precioUnitario.toFixed(2)} €</td>
                <td>
                  <button className="danger" onClick={() => handleDelete(p.id)}>
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
