# Presupuestos — app de presupuestos de obra

Reemplaza el Excel con macros (`presupbien.xlsm`) por una aplicación web moderna,
manteniendo la misma lógica de cálculo:

- Cada **presupuesto** tiene cliente, proyecto, un multiplicador (def. 1.5) y una
  tarifa por hora (def. 35 €).
- Cada presupuesto tiene varios **conceptos** (ej. "Fontanería"), cada uno con horas
  de trabajo y una lista de **componentes** (cantidad, unidad, precio unitario).
- Por cada concepto se calculan dos estimaciones, igual que en la macro original:
  - `Estimación 1 = subtotal * 1.2 + horas * tarifa_por_hora`
  - `Estimación 2 = subtotal * multiplicador`
- Se suman los totales generales de ambas estimaciones.

## Mejoras respecto al Excel original

- Editar y eliminar conceptos/componentes en cualquier momento (no solo añadir).
- Histórico de presupuestos guardado en base de datos (SQLite), consultable y eliminable.
- Catálogo de componentes reutilizables (plantillas) para añadir materiales habituales
  con un clic.
- Exportación a PDF y a Excel (.xlsx) con un botón.

## Estructura

- `server/`: API REST en Node.js + Express + SQLite (better-sqlite3).
- `client/`: interfaz web en React + Vite.

## Cómo ejecutarlo

```bash
# Backend
cd server
npm install
npm run dev      # http://localhost:4000

# Frontend (en otra terminal)
cd client
npm install
npm run dev       # http://localhost:5173
```

Abre http://localhost:5173 en el navegador. El frontend ya tiene configurado un proxy
hacia el backend, así que no hace falta configurar CORS para el desarrollo.
