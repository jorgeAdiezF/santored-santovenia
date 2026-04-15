const axios = require('axios');
const config = require('../config');

const BASE_URL = `https://graph.facebook.com/v19.0/${config.whatsapp.phoneId}/messages`;

async function sendText(to, text) {
  // En dev sin token configurado, solo loguear
  if (!config.whatsapp.token || config.nodeEnv === 'development') {
    console.log(`📤 [WhatsApp → ${to}]: ${text.substring(0, 80)}${text.length > 80 ? '...' : ''}`);
    return { simulated: true };
  }

  try {
    const response = await axios.post(BASE_URL, {
      messaging_product: 'whatsapp',
      recipient_type: 'individual',
      to,
      type: 'text',
      text: { body: text, preview_url: false },
    }, {
      headers: {
        Authorization: `Bearer ${config.whatsapp.token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (err) {
    const msg = err.response?.data?.error?.message || err.message;
    console.error(`❌ Error WhatsApp sender: ${msg}`);
    throw err;
  }
}

async function sendTypingIndicator(to) {
  // Indica "escribiendo..." (solo en producción)
  if (!config.whatsapp.token || config.nodeEnv === 'development') return;
  try {
    await axios.post(BASE_URL, {
      messaging_product: 'whatsapp',
      status: 'read',
      message_id: to, // workaround — normalmente va el message_id real
    }, {
      headers: { Authorization: `Bearer ${config.whatsapp.token}` },
    });
  } catch {} // No crítico
}

module.exports = { sendText, sendTypingIndicator };
