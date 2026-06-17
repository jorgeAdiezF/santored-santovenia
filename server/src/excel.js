import ExcelJS from "exceljs";

export async function buildPresupuestoExcel(presupuesto, res) {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet("Presupuesto");

  sheet.columns = [
    { width: 35 },
    { width: 12 },
    { width: 10 },
    { width: 16 },
    { width: 16 },
  ];

  sheet.addRow([`Cliente: ${presupuesto.cliente}`]).font = { bold: true };
  sheet.addRow([`Obra: ${presupuesto.proyecto}`]).font = { bold: true };
  sheet.addRow([]);

  for (const concepto of presupuesto.conceptos) {
    const row = sheet.addRow([concepto.nombre]);
    row.font = { bold: true };
    row.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFC8C8C8" } };

    const header = sheet.addRow(["Componente", "Cantidad", "Unidad", "Precio Unitario", "Total"]);
    header.font = { bold: true };
    header.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFDCDCDC" } };

    for (const c of concepto.componentes) {
      sheet.addRow([c.nombre, c.cantidad, c.unidad, c.precioUnitario, c.total]);
    }

    sheet.addRow(["", "", "", "Estimación 1 (con horas):", concepto.estimacion1]).font = { bold: true };
    sheet.addRow(["", "", "", "Estimación 2 (con multiplicador):", concepto.estimacion2]).font = {
      bold: true,
    };
    sheet.addRow([]);
  }

  sheet.addRow(["", "", "", "TOTAL GENERAL (con horas):", presupuesto.totalEstimacion1]).font = {
    bold: true,
  };
  sheet.addRow(["", "", "", "TOTAL GENERAL (con multiplicador):", presupuesto.totalEstimacion2]).font = {
    bold: true,
  };

  res.setHeader(
    "Content-Type",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  );
  res.setHeader(
    "Content-Disposition",
    `attachment; filename="${presupuesto.cliente}_${presupuesto.proyecto}.xlsx"`
  );
  await workbook.xlsx.write(res);
  res.end();
}
