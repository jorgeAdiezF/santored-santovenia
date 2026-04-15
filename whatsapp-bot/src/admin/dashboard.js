const db = require('../db/database');
const config = require('../config');

function renderDashboard(req, res) {
  const stats   = db.getDashboardStats();
  const recent  = db.getRecentActivity(30);
  const catalog = db.getAllCatalog();

  res.send(`<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Panel Admin — Bot WhatsApp</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',system-ui,sans-serif;background:#f1f5f9;color:#1e293b}
    .hdr{background:linear-gradient(135deg,#0f172a,#1e3a5f);color:white;padding:20px 24px}
    .hdr h1{font-size:20px;font-weight:800}
    .hdr p{font-size:12px;opacity:.7;margin-top:3px}
    .main{max-width:1100px;margin:0 auto;padding:20px 16px}
    .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:24px}
    .stat{background:white;border-radius:12px;padding:16px;border-left:4px solid #f97316;box-shadow:0 1px 3px rgba(0,0,0,.07)}
    .stat .n{font-size:28px;font-weight:900;color:#f97316}
    .stat .l{font-size:12px;color:#64748b;margin-top:2px}
    .card{background:white;border-radius:12px;padding:20px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.07)}
    .card h2{font-size:15px;font-weight:700;color:#374151;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #f1f5f9}
    table{width:100%;border-collapse:collapse;font-size:13px}
    th{background:#f8fafc;padding:8px 12px;text-align:left;font-weight:600;color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
    td{padding:9px 12px;border-bottom:1px solid #f8fafc}
    tr:last-child td{border-bottom:none}
    .badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}
    .badge-AVERIA{background:#fee2e2;color:#dc2626}
    .badge-COMERCIAL{background:#dbeafe;color:#2563eb}
    .badge-ADMINISTRATIVO{background:#ede9fe;color:#7c3aed}
    .badge-GENERAL{background:#f3f4f6;color:#374151}
    .badge-active{background:#dcfce7;color:#16a34a}
    .badge-completed{background:#f3f4f6;color:#6b7280}
    .cat-badge{display:inline-block;padding:1px 7px;border-radius:5px;font-size:10px;font-weight:700;background:#fff7ed;color:#c2410c;border:1px solid #fed7aa}
    .form-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:12px}
    input,select,textarea{width:100%;padding:8px 10px;border:1.5px solid #e2e8f0;border-radius:7px;font-size:13px;outline:none}
    input:focus,select:focus,textarea:focus{border-color:#f97316}
    .btn{padding:8px 16px;border-radius:7px;border:none;cursor:pointer;font-weight:600;font-size:13px}
    .btn-p{background:#f97316;color:white}.btn-p:hover{background:#ea580c}
    .btn-s{background:#f1f5f9;color:#374151}.btn-s:hover{background:#e2e8f0}
  </style>
</head>
<body>
<div class="hdr">
  <h1>⚙️ Panel de Administración — Bot WhatsApp</h1>
  <p>${config.company.name} · ${new Date().toLocaleString('es-ES')}</p>
</div>
<div class="main">
  <!-- KPIs -->
  <div class="stats">
    <div class="stat"><div class="n">${stats.totalConvs}</div><div class="l">Conversaciones totales</div></div>
    <div class="stat" style="border-color:#ef4444"><div class="n" style="color:#ef4444">${stats.incidents}</div><div class="l">Averías pendientes</div></div>
    <div class="stat" style="border-color:#3b82f6"><div class="n" style="color:#3b82f6">${stats.leads}</div><div class="l">Leads nuevos</div></div>
    <div class="stat" style="border-color:#8b5cf6"><div class="n" style="color:#8b5cf6">${stats.tickets}</div><div class="l">Tickets abiertos</div></div>
    <div class="stat" style="border-color:#10b981"><div class="n" style="color:#10b981">${stats.contacts}</div><div class="l">Contactos totales</div></div>
  </div>

  <!-- Actividad reciente -->
  <div class="card">
    <h2>📋 Actividad Reciente (últimas 30 conversaciones)</h2>
    <div style="overflow-x:auto">
      <table>
        <thead><tr>
          <th>#</th><th>WhatsApp</th><th>Contacto</th><th>Categoría</th><th>Estado</th><th>Fecha</th>
        </tr></thead>
        <tbody>
          ${recent.map(r => `<tr>
            <td style="color:#9ca3af">#${r.id}</td>
            <td style="font-family:monospace">${r.wa_phone}</td>
            <td>${r.contact_name || '<span style="color:#9ca3af">—</span>'}</td>
            <td>${r.category ? `<span class="badge badge-${r.category}">${r.category}</span>` : '<span style="color:#9ca3af">—</span>'}</td>
            <td><span class="badge badge-${r.status}">${r.status}</span></td>
            <td style="color:#6b7280;font-size:12px">${new Date(r.created_at).toLocaleString('es-ES')}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Catálogo -->
  <div class="card">
    <h2>📦 Catálogo de Productos y Precios</h2>
    <form method="POST" action="/admin/catalog" style="background:#f8fafc;padding:14px;border-radius:10px;margin-bottom:16px">
      <div style="font-weight:600;font-size:13px;margin-bottom:10px;color:#374151">Añadir / Editar Producto</div>
      <div class="form-row">
        <div><label style="font-size:11px;color:#6b7280;display:block;margin-bottom:3px">Categoría</label>
          <input name="category" placeholder="Ej: Puertas automáticas" required/></div>
        <div><label style="font-size:11px;color:#6b7280;display:block;margin-bottom:3px">Nombre</label>
          <input name="name" placeholder="Nombre del producto" required/></div>
        <div><label style="font-size:11px;color:#6b7280;display:block;margin-bottom:3px">Precio desde (€)</label>
          <input name="price_from" type="number" step="0.01" placeholder="0.00"/></div>
        <div><label style="font-size:11px;color:#6b7280;display:block;margin-bottom:3px">Precio hasta (€)</label>
          <input name="price_to" type="number" step="0.01" placeholder="0.00"/></div>
        <div><label style="font-size:11px;color:#6b7280;display:block;margin-bottom:3px">Unidad</label>
          <input name="unit" placeholder="ud., ml, instalación…" value="ud."/></div>
      </div>
      <div style="margin-bottom:10px"><label style="font-size:11px;color:#6b7280;display:block;margin-bottom:3px">Descripción</label>
        <textarea name="description" rows="2" style="resize:vertical" placeholder="Descripción completa del producto/servicio"></textarea></div>
      <div style="margin-bottom:12px"><label style="font-size:11px;color:#6b7280;display:block;margin-bottom:3px">Notas internas</label>
        <input name="notes" placeholder="Plazo, condiciones, observaciones…"/></div>
      <button class="btn btn-p" type="submit">+ Añadir al catálogo</button>
    </form>

    <div style="overflow-x:auto">
      <table>
        <thead><tr>
          <th>Categoría</th><th>Producto</th><th>Descripción</th><th>Precio</th><th>Unidad</th><th>Notas</th>
        </tr></thead>
        <tbody>
          ${catalog.map(p => `<tr>
            <td><span class="cat-badge">${p.category}</span></td>
            <td style="font-weight:600">${p.name}</td>
            <td style="color:#6b7280;max-width:240px;white-space:normal">${p.description || ''}</td>
            <td style="white-space:nowrap;color:#059669;font-weight:600">${p.price_from ? `${p.price_from}€ — ${p.price_to || '?'}€` : '—'}</td>
            <td>${p.unit || ''}</td>
            <td style="color:#6b7280;font-size:12px">${p.notes || ''}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>
</div>
</body></html>`);
}

function handleCatalogPost(req, res) {
  const { category, name, description, price_from, price_to, unit, notes } = req.body;
  if (!category || !name) return res.redirect('/admin?error=missing');
  db.upsertCatalogItem({
    category, name, description,
    priceFrom: parseFloat(price_from) || null,
    priceTo: parseFloat(price_to) || null,
    unit: unit || 'ud.',
    notes,
  });
  res.redirect('/admin');
}

module.exports = { renderDashboard, handleCatalogPost };
