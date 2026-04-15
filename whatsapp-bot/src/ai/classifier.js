const Anthropic = require('@anthropic-ai/sdk');
const config = require('../config');

const client = new Anthropic({ apiKey: config.anthropic.apiKey });

const CATEGORIES = {
  AVERIA:        'AVERIA',
  COMERCIAL:     'COMERCIAL',
  ADMINISTRATIVO:'ADMINISTRATIVO',
  GENERAL:       'GENERAL',
};

const CATEGORY_DESCRIPTIONS = {
  AVERIA:        'Avería o necesidad de mantenimiento → Servicio Técnico',
  COMERCIAL:     'Solicitud comercial, presupuesto o información de productos → Comercial',
  ADMINISTRATIVO:'Consulta administrativa (facturas, pagos, citas, contratos) → Administración',
  GENERAL:       'Otras comunicaciones → Administración general',
};

async function classifyMessage(text) {
  const response = await client.messages.create({
    model: config.anthropic.model,
    max_tokens: 20,
    system: [
      {
        type: 'text',
        text: `Clasifica el mensaje de WhatsApp de un cliente de una empresa de fabricación metálica y automatismos de accesos (puertas automáticas, cancelas, vallas, barreras).

Categorías:
- AVERIA: avería, no funciona, estropeado, roto, mantenimiento, revisión urgente, fallo
- COMERCIAL: precio, presupuesto, cuánto cuesta, quiero instalar, información de productos, comprar
- ADMINISTRATIVO: factura, pago, cita, contrato, renovar, baja, administrativo
- GENERAL: cualquier otra cosa, queja, sugerencia, información general

Responde ÚNICAMENTE con una de estas palabras: AVERIA, COMERCIAL, ADMINISTRATIVO, GENERAL`,
        cache_control: { type: 'ephemeral' },
      }
    ],
    messages: [{ role: 'user', content: text }],
  });

  const raw = response.content[0].text.trim().toUpperCase();
  return CATEGORIES[raw] || CATEGORIES.GENERAL;
}

module.exports = { classifyMessage, CATEGORIES, CATEGORY_DESCRIPTIONS };
