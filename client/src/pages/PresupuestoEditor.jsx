import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api.js";
import ConceptoCard from "../components/ConceptoCard.jsx";

export default function PresupuestoEditor() {
  const { id } = useParams();
  const [presupuesto, setPresupuesto] = useState(null);
  const [plantillas, setPlantillas] = useState([]);
  const [nuevoConcepto, setNuevoConcepto] = useState("");
  const [error, setError] = useState("");

  async function reload() {
    setPresupuesto(await api.getPresupuesto(id));
  }

  useEffect(() => {
    reload();
    api.listPlantillas().then(setPlantillas);
  }, [id]);

  async function handleConfig(field, value) {
    setPresupuesto(await api.updatePresupuesto(id, { [field]: value }));
  }

  async function handleAddConcepto(e) {
    e.preventDefault();
    setError("");
    if (!nuevoConcepto.trim()) return;
    try {
      setPresupuesto(await api.addConcepto(id, { nombre: nuevoConcepto.trim() }));
      setNuevoConcepto("");
    } catch (err) {
      setError(err.message);
    }
  }

  if (!presupuesto) return <p className="page">Cargando...</p>;

  return (
    <div className="page">
      <section className="card">
        <h2>
          {presupuesto.cliente} — {presupuesto.proyecto}
        </h2>
        <div className="row">
          <label>
            Multiplicador
            <input
              type="number"
              step="0.01"
              value={presupuesto.multiplier}
              onChange={(e) => handleConfig("multiplier", Number(e.target.value))}
            />
          </label>
          <label>
            Tarifa por hora (€)
            <input
              type="number"
              step="0.01"
              value={presupuesto.hourlyRate}
              onChange={(e) => handleConfig("hourlyRate", Number(e.target.value))}
            />
          </label>
        </div>
        <div className="row">
          <a className="button" href={`/api/presupuestos/${id}/pdf`}>
            Descargar PDF
          </a>
          <a className="button" href={`/api/presupuestos/${id}/excel`}>
            Descargar Excel
          </a>
        </div>
      </section>

      <section className="card">
        <h3>Añadir concepto</h3>
        <form onSubmit={handleAddConcepto} className="row">
          <input
            placeholder="Ej. Fontanería, Electricidad..."
            value={nuevoConcepto}
            onChange={(e) => setNuevoConcepto(e.target.value)}
          />
          <button type="submit">Añadir concepto</button>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      {presupuesto.conceptos.map((concepto) => (
        <ConceptoCard
          key={concepto.id}
          concepto={concepto}
          plantillas={plantillas}
          onChange={reload}
        />
      ))}

      <section className="card totales">
        <h3>Totales generales</h3>
        <p>
          <strong>Con horas:</strong> {presupuesto.totalEstimacion1.toFixed(2)} €
        </p>
        <p>
          <strong>Con multiplicador:</strong> {presupuesto.totalEstimacion2.toFixed(2)} €
        </p>
      </section>
    </div>
  );
}
