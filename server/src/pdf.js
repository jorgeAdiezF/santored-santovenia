import PDFDocument from "pdfkit";

const money = (n) => `${n.toFixed(2)} €`;

export function buildPresupuestoPdf(presupuesto, res) {
  const doc = new PDFDocument({ margin: 50 });
  res.setHeader("Content-Type", "application/pdf");
  res.setHeader(
    "Content-Disposition",
    `attachment; filename="${presupuesto.cliente}_${presupuesto.proyecto}.pdf"`
  );
  doc.pipe(res);

  doc.fontSize(20).text("Presupuesto", { align: "center" });
  doc.moveDown();
  doc.fontSize(12).text(`Cliente: ${presupuesto.cliente}`);
  doc.text(`Obra: ${presupuesto.proyecto}`);
  doc.text(`Fecha: ${new Date(presupuesto.createdAt).toLocaleDateString("es-ES")}`);
  doc.moveDown();

  for (const concepto of presupuesto.conceptos) {
    doc.fontSize(14).fillColor("#222").text(concepto.nombre, { underline: true });
    doc.moveDown(0.3);
    doc.fontSize(10).fillColor("#000");

    for (const c of concepto.componentes) {
      doc.text(
        `${c.nombre}  —  ${c.cantidad} ${c.unidad} x ${money(c.precioUnitario)} = ${money(c.total)}`
      );
    }

    doc.moveDown(0.3);
    doc.fontSize(11).text(`Subtotal: ${money(concepto.subtotal)}`);
    doc.text(`Horas de trabajo: ${concepto.horas} h`);
    doc.font("Helvetica-Bold");
    doc.text(`Estimación 1 (con horas): ${money(concepto.estimacion1)}`);
    doc.text(`Estimación 2 (con multiplicador): ${money(concepto.estimacion2)}`);
    doc.font("Helvetica");
    doc.moveDown();
  }

  doc.moveDown();
  doc.fontSize(13).font("Helvetica-Bold");
  doc.text(`TOTAL GENERAL (con horas): ${money(presupuesto.totalEstimacion1)}`);
  doc.text(`TOTAL GENERAL (con multiplicador): ${money(presupuesto.totalEstimacion2)}`);

  doc.end();
}
