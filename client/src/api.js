const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Error ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listPresupuestos: () => request("/presupuestos"),
  getPresupuesto: (id) => request(`/presupuestos/${id}`),
  createPresupuesto: (data) =>
    request("/presupuestos", { method: "POST", body: JSON.stringify(data) }),
  updatePresupuesto: (id, data) =>
    request(`/presupuestos/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deletePresupuesto: (id) => request(`/presupuestos/${id}`, { method: "DELETE" }),

  addConcepto: (presupuestoId, data) =>
    request(`/presupuestos/${presupuestoId}/conceptos`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateConcepto: (conceptoId, data) =>
    request(`/presupuestos/conceptos/${conceptoId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteConcepto: (conceptoId) =>
    request(`/presupuestos/conceptos/${conceptoId}`, { method: "DELETE" }),

  addComponente: (conceptoId, data) =>
    request(`/presupuestos/conceptos/${conceptoId}/componentes`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateComponente: (componenteId, data) =>
    request(`/presupuestos/componentes/${componenteId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteComponente: (componenteId) =>
    request(`/presupuestos/componentes/${componenteId}`, { method: "DELETE" }),

  listPlantillas: () => request("/plantillas"),
  createPlantilla: (data) =>
    request("/plantillas", { method: "POST", body: JSON.stringify(data) }),
  updatePlantilla: (id, data) =>
    request(`/plantillas/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deletePlantilla: (id) => request(`/plantillas/${id}`, { method: "DELETE" }),
};
