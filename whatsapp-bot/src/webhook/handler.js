const { handleMessage } = require('../flows/router');
const { sendText } = require('../whatsapp/sender');
const db = require('../db/database');
const config = require('../config');

// ── Verificación de webhook (GET) ─────────────────────────────
function verifyWebhook(req, res) {
  const mode      = req.query['hub.mode'];
  const token     = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];

  if (mode === 'subscribe' && token === config.whatsapp.verifyToken) {
    console.log('✅ Webhook verificado por Meta');
    return res.status(200).send(challenge);
  }
  console.warn('⚠️  Verificación fallida — token incorrecto');
  res.sendStatus(403);
}

// ── Recepción de mensajes (POST) ──────────────────────────────
async function receiveMessage(req, res) {
  // Meta espera 200 rápido; procesamos en background
  res.sendStatus(200);

  try {
    const body = req.body;
    if (body.object !== 'whatsapp_business_account') return;

    for (const entry of (body.entry || [])) {
      for (const change of (entry.changes || [])) {
        if (change.field !== 'messages') continue;

        const value = change.value;
        const messages = value.messages || [];

        for (const msg of messages) {
          if (msg.type !== 'text') {
            // Mensajes de voz, imagen, etc. — responder amablemente
            await sendText(msg.from, `Hola, actualmente solo puedo procesar mensajes de texto. Escríbeme lo que necesitas y te ayudo enseguida 😊`);
            continue;
          }

          const waPhone = msg.from;
          const text    = msg.text.body.trim();
          const waId    = msg.id;

          console.log(`📩 [${waPhone}]: ${text}`);

          // Obtener o crear conversación en BD
          let convId = getActiveConversationId(waPhone);
          if (!convId) {
            convId = db.createConversation(waPhone);
          }

          // Guardar mensaje entrante
          db.saveMessage(convId, 'inbound', text, waId);

          // Procesar con el router
          const { reply } = await handleMessage(waPhone, text, convId);

          // Enviar respuesta
          await sendText(waPhone, reply);

          // Guardar respuesta
          db.saveMessage(convId, 'outbound', reply);
        }
      }
    }
  } catch (err) {
    console.error('❌ Error procesando webhook:', err);
  }
}

// Cache simple de conversaciones activas (waPhone → convId)
const activeConvs = new Map();

function getActiveConversationId(waPhone) {
  return activeConvs.get(waPhone) || null;
}

// Limpiar conversación al completarse (llamado desde router)
function clearActiveConversation(waPhone) {
  activeConvs.delete(waPhone);
}

// Patch: registrar convId cuando se crea
const originalCreate = db.createConversation.bind(db);
db.createConversation = (waPhone) => {
  const id = originalCreate(waPhone);
  activeConvs.set(waPhone, id);
  return id;
};

module.exports = { verifyWebhook, receiveMessage };
