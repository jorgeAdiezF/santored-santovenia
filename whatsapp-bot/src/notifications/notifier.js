const nodemailer = require('nodemailer');
const config = require('../config');

let transporter = null;

function getTransporter() {
  if (!transporter) {
    transporter = nodemailer.createTransport({
      host: config.smtp.host,
      port: config.smtp.port,
      secure: config.smtp.port === 465,
      auth: { user: config.smtp.user, pass: config.smtp.pass },
    });
  }
  return transporter;
}

const ROUTING = {
  AVERIA:         { to: config.emails.tecnico,   dept: 'Servicio Técnico',  emoji: '🔧' },
  COMERCIAL:      { to: config.emails.comercial,  dept: 'Comercial',         emoji: '💼' },
  ADMINISTRATIVO: { to: config.emails.admin,      dept: 'Administración',    emoji: '📋' },
  GENERAL:        { to: config.emails.general,    dept: 'General',           emoji: '💬' },
};

async function notifyTeam(category, payload) {
  const route = ROUTING[category] || ROUTING.GENERAL;
  const { contact, details, conversationId } = payload;

  const subject = `${route.emoji} Nueva solicitud WhatsApp [${category}] — ${contact.name || contact.waPhone}`;

  const html = buildEmailHtml(category, route, contact, details, conversationId);
  const text = buildEmailText(category, route, contact, details, conversationId);

  if (!config.smtp.user || !config.smtp.pass) {
    // En desarrollo, solo log
    console.log(`\n📧 [NOTIFICACIÓN EMAIL SIMULADA]`);
    console.log(`   Para: ${route.to} (${route.dept})`);
    console.log(`   Asunto: ${subject}`);
    console.log(`   Contacto: ${JSON.stringify(contact)}`);
    console.log(`   Detalles: ${JSON.stringify(details)}\n`);
    return;
  }

  try {
    await getTransporter().sendMail({
      from: `"Bot WhatsApp ${config.company.name}" <${config.smtp.user}>`,
      to: route.to,
      cc: category !== 'ADMINISTRATIVO' ? config.emails.admin : undefined,
      subject,
      text,
      html,
    });
    console.log(`✅ Email enviado a ${route.dept} (${route.to})`);
  } catch (err) {
    console.error(`❌ Error enviando email:`, err.message);
  }
}

function buildEmailHtml(category, route, contact, details, conversationId) {
  const colors = {
    AVERIA: '#ef4444', COMERCIAL: '#3b82f6',
    ADMINISTRATIVO: '#8b5cf6', GENERAL: '#6b7280',
  };
  const color = colors[category] || '#6b7280';

  return `
<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#f3f4f6;padding:20px">
<div style="max-width:560px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)">
  <div style="background:${color};color:white;padding:20px 24px">
    <h2 style="margin:0;font-size:20px">${route.emoji} Nueva solicitud: ${category}</h2>
    <p style="margin:4px 0 0;opacity:.85;font-size:14px">Departamento: ${route.dept} | Conv. #${conversationId}</p>
  </div>
  <div style="padding:24px">
    <h3 style="color:#374151;font-size:14px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:12px">Datos del Contacto</h3>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      ${contact.name    ? `<tr><td style="padding:6px 0;color:#6b7280;width:120px">Nombre:</td><td style="padding:6px 0;font-weight:600">${contact.name}</td></tr>` : ''}
      ${contact.phone   ? `<tr><td style="padding:6px 0;color:#6b7280">Teléfono:</td><td style="padding:6px 0;font-weight:600"><a href="tel:${contact.phone}">${contact.phone}</a></td></tr>` : ''}
      ${contact.waPhone ? `<tr><td style="padding:6px 0;color:#6b7280">WhatsApp:</td><td style="padding:6px 0;font-weight:600">${contact.waPhone}</td></tr>` : ''}
      ${contact.address ? `<tr><td style="padding:6px 0;color:#6b7280">Dirección:</td><td style="padding:6px 0">${contact.address}</td></tr>` : ''}
    </table>

    ${buildDetailsSection(category, details)}

    <div style="margin-top:20px;padding:14px;background:#f9fafb;border-radius:8px;font-size:13px;color:#6b7280">
      Recibido vía WhatsApp Bot — ${new Date().toLocaleString('es-ES')} | ${config.company.name}
    </div>
  </div>
</div>
</body></html>`;
}

function buildDetailsSection(category, details) {
  const sections = {
    AVERIA:         [['Descripción de la avería', details?.problem]],
    COMERCIAL:      [['Interés / Concepto', details?.concept], ['Info catálogo enviada', details?.catalogInfo]],
    ADMINISTRATIVO: [['Asunto', details?.subject]],
    GENERAL:        [['Motivo', details?.reason]],
  };
  const rows = (sections[category] || []).filter(([,v]) => v);
  if (rows.length === 0) return '';
  return `
    <h3 style="color:#374151;font-size:14px;text-transform:uppercase;letter-spacing:.05em;margin:20px 0 12px">Detalles</h3>
    ${rows.map(([k,v]) => `<div style="margin-bottom:10px"><div style="font-size:12px;color:#9ca3af;margin-bottom:2px">${k}</div><div style="font-size:14px;color:#111827;background:#f9fafb;padding:10px 12px;border-radius:6px;border-left:3px solid #f97316">${v}</div></div>`).join('')}`;
}

function buildEmailText(category, route, contact, details, conversationId) {
  return [
    `NUEVA SOLICITUD WHATSAPP [${category}] — ${route.dept}`,
    `Conversación #${conversationId} — ${new Date().toLocaleString('es-ES')}`,
    '',
    'CONTACTO:',
    contact.name    ? `  Nombre:    ${contact.name}` : '',
    contact.phone   ? `  Teléfono:  ${contact.phone}` : '',
    contact.waPhone ? `  WhatsApp:  ${contact.waPhone}` : '',
    contact.address ? `  Dirección: ${contact.address}` : '',
    '',
    'DETALLES:',
    details?.problem  ? `  Avería:  ${details.problem}` : '',
    details?.concept  ? `  Interés: ${details.concept}` : '',
    details?.subject  ? `  Asunto:  ${details.subject}` : '',
    details?.reason   ? `  Motivo:  ${details.reason}` : '',
  ].filter(l => l !== '').join('\n');
}

module.exports = { notifyTeam };
