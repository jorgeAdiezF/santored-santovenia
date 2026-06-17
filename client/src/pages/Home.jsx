import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api.js";

export default function Home() {
  const [presupuestos, setPresupuestos] = useState([]);
  const [cliente, setCliente] = useState("");
  const [proyecto, setProyecto] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.listPresupuestos().then(setPresupuestos);
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      const nuevo = await api.createPresupuesto({ cliente, proyecto });
      navigate(`/presupuestos/${nuevo.id}`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    if (!confirm("¿Eliminar este presupuesto?")) return;
    await api.deletePresupuesto(id);
    setPresupuestos((prev) => prev.filter((p) => p.id !== id));
  }

  return (
    <div className="page">
      <section className="card">
        <h2>Nuevo presupuesto</h2>
        <form onSubmit={handleCreate} className="row">
          <input
            placeholder="Cliente"
            value={cliente}
            onChange={(e) => setCliente(e.target.value)}
            required
          />
          <input
            placeholder="Proyecto / Obra"
            value={proyecto}
            onChange={(e) => setProyecto(e.target.value)}
            required
          />
          <button type="submit">Crear</button>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      <section className="card">
        <h2>Histórico</h2>
        {presupuestos.length === 0 && <p>No hay presupuestos todavía.</p>}
        <table>
          <thead>
            <tr>
              <th>Cliente</th>
              <th>Proyecto</th>
              <th>Actualizado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {presupuestos.map((p) => (
              <tr key={p.id}>
                <td>{p.cliente}</td>
                <td>{p.proyecto}</td>
                <td>{new Date(p.updatedAt).toLocaleString("es-ES")}</td>
                <td className="actions">
                  <button onClick={() => navigate(`/presupuestos/${p.id}`)}>Abrir</button>
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
