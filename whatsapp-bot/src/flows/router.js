const { classifyMessage } = require('../ai/classifier');
const { runConversationTurn, extractCollectedData } = require('../ai/agent');
const { searchCatalog } = require('../db/database');
const sessionMgr = require('../session/manager');
const db = require('../db/database');
const notifier = require('../notifications/notifier');
const config = require('../config');

// Mensaje de bienvenida (primera vez o sesión expirada)
const WELCOME = `¡Hola! 👋 Soy el asistente virtual de ${config.company.name}.

¿En qué puedo ayudarte hoy?
• 🔧 Reportar una avería o pedir mantenimiento
• 💼 Información comercial o presupuesto
• 📋 Consulta administrativa
• 💬 Cualquier otra consulta

Cuéntame qué necesitas.`;

async function handleMessage(waPhone, messageText, conversationId) {
  let session = sessionMgr.getSession(waPhone);

  // ── Primera interacción o sesión expirada ─────────────────────
  if (!session) {
    session = sessionMgr.createSession(waPhone, conversationId);
    sessionMgr.addToHistory(waPhone, 'outbound', WELCOME);
    return { reply: WELCOME, action: 'welcome' };
  }

  // Guardar mensaje entrante en historial
  sessionMgr.addToHistory(waPhone, 'inbound', messageText);

  // ── Clasificar si aún no tenemos categoría ────────────────────
  if (!session.category) {
    const category = await classifyMessage(messageText);
    sessionMgr.updateSession(waPhone, { category, phase: 'collecting' });
    session = sessionMgr.getSession(waPhone);
    db.updateConversation(conversationId, { category });
  }

  // ── Buscar en catálogo si es consulta comercial ───────────────
  let catalogInfo = null;
  if (session.category === 'COMERCIAL') {
    const results = await searchCatalog(messageText);
    if (results.length > 0) {
      catalogInfo = results.slice(0, 4).map(r =>
        `${r.name}: ${r.description}${r.price_from ? ` — Desde ${r.price_from}€ ${r.unit}` : ''}${r.notes ? ` (${r.notes})` : ''}`
      ).join('\n');
    }
  }

  // ── Extraer datos recogidos del historial ─────────────────────
  const collected = await extractCollectedData(session.category, session.history);
  sessionMgr.updateSession(waPhone, { collected });
  session = sessionMgr.getSession(waPhone);

  // ── Turno conversacional con Claude ──────────────────────────
  const { reply, complete, data } = await runConversationTurn(
    session.category,
    session.history.slice(0, -1), // sin el último mensaje (ya es 'user')
    messageText,
    session.collected,
    catalogInfo,
  );

  sessionMgr.addToHistory(waPhone, 'outbound', reply);

  if (complete && data) {
    await finalizeConversation(waPhone, session, conversationId, data);
    return { reply, action: 'completed', category: session.category };
  }

  return { reply, action: 'collecting' };
}

async function finalizeConversation(waPhone, session, conversationId, data) {
  // Guardar o actualizar contacto
  const contact = db.upsertContact(waPhone, data.contact);
  const contactId = contact?.lastInsertRowid || db.getContact(waPhone)?.id;

  db.updateConversation(conversationId, {
    contactId,
    status: 'completed',
    completedAt: new Date().toISOString(),
  });

  // Guardar en la tabla específica según categoría
  switch (session.category) {
    case 'AVERIA':
      db.createIncident({
        conversationId,
        contactId,
        description: data.details?.problem || 'Sin descripción',
        urgency: detectUrgency(data.details?.problem),
      });
      break;

    case 'COMERCIAL':
      db.createLead({
        conversationId,
        contactId,
        concept: data.details?.concept || '',
        catalogInfo: data.details?.catalogInfo || null,
      });
      break;

    case 'ADMINISTRATIVO':
      db.createTicket({
        conversationId,
        contactId,
        category: 'ADMINISTRATIVO',
        subject: data.details?.subject || 'Consulta administrativa',
        description: JSON.stringify(data.details),
      });
      break;

    case 'GENERAL':
    default:
      db.createTicket({
        conversationId,
        contactId,
        category: 'GENERAL',
        subject: data.details?.reason || 'Comunicación general',
        description: JSON.stringify(data.details),
      });
      break;
  }

  // Enviar notificación al equipo correspondiente
  await notifier.notifyTeam(session.category, {
    contact: { ...data.contact, waPhone },
    details: data.details,
    conversationId,
  });

  sessionMgr.endSession(waPhone);
}

function detectUrgency(problemText) {
  if (!problemText) return 'normal';
  const urgentWords = /urgent|inmediato|ahora|bloqueado|atrapado|emergencia|no abre|no cierra|accidente/i;
  return urgentWords.test(problemText) ? 'high' : 'normal';
}

module.exports = { handleMessage, WELCOME };
