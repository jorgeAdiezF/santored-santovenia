require('dotenv').config();
const express = require('express');
const { verifyWebhook, receiveMessage } = require('./webhook/handler');
const { renderDashboard, handleCatalogPost } = require('./admin/dashboard');
const config = require('./config');

const app = express();

// ── Middlewares ───────────────────────────────────────────────
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ── Health check ──────────────────────────────────────────────
app.get('/', (req, res) => {
  res.json({
    status: 'ok',
    service: `Bot WhatsApp — ${config.company.name}`,
    timestamp: new Date().toISOString(),
  });
});

// ── Webhook Meta/WhatsApp ─────────────────────────────────────
app.get('/webhook', verifyWebhook);
app.post('/webhook', receiveMessage);

// ── Panel de administración ───────────────────────────────────
app.get('/admin', renderDashboard);
app.post('/admin/catalog', handleCatalogPost);

// ── Modo simulación (desarrollo sin credenciales Meta) ────────
if (config.nodeEnv === 'development') {
  app.post('/simulate', async (req, res) => {
    const { phone = '34600000001', message } = req.body;
    if (!message) return res.status(400).json({ error: 'message requerido' });

    // Simular webhook de Meta
    const fakeWebhook = {
      object: 'whatsapp_business_account',
      entry: [{
        changes: [{
          field: 'messages',
          value: {
            messages: [{
              from: phone,
              id: `sim_${Date.now()}`,
              type: 'text',
              text: { body: message },
            }],
          },
        }],
      }],
    };

    req.body = fakeWebhook;
    // Capturar respuesta simulada
    const { handleMessage } = require('./flows/router');
    const db = require('./db/database');
    const sessionMgr = require('./session/manager');

    let convId = db.createConversation(phone);
    db.saveMessage(convId, 'inbound', message);
    const result = await handleMessage(phone, message, convId);
    db.saveMessage(convId, 'outbound', result.reply);

    res.json({
      from: phone,
      message,
      reply: result.reply,
      action: result.action,
      category: result.category || null,
    });
  });

  console.log('🧪 Modo desarrollo: endpoint POST /simulate disponible');
}

// ── Arranque ──────────────────────────────────────────────────
app.listen(config.port, () => {
  console.log(`\n🚀 Bot WhatsApp arrancado en puerto ${config.port}`);
  console.log(`   Empresa:   ${config.company.name}`);
  console.log(`   Entorno:   ${config.nodeEnv}`);
  console.log(`   Webhook:   POST /webhook`);
  console.log(`   Admin:     http://localhost:${config.port}/admin`);
  if (config.nodeEnv === 'development') {
    console.log(`   Simular:   POST /simulate { phone, message }`);
  }
  console.log('');
});

module.exports = app;
