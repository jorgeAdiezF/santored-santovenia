const Anthropic = require('@anthropic-ai/sdk');
const config = require('../config');

const client = new Anthropic({ apiKey: config.anthropic.apiKey });

// Datos necesarios por categoría
const REQUIRED_FIELDS = {
  AVERIA:         ['name', 'phone', 'address', 'problem'],
  COMERCIAL:      ['name', 'phone', 'concept'],
  ADMINISTRATIVO: ['name', 'phone', 'subject'],
  GENERAL:        ['name', 'phone', 'reason'],
};

const FIELD_LABELS = {
  name:    'nombre completo',
  phone:   'número de teléfono de contacto',
  address: 'dirección completa (calle, número, localidad)',
  problem: 'descripción del problema o avería',
  concept: 'descripción de lo que necesitas o buscas',
  subject: 'asunto o motivo de la consulta',
  reason:  'motivo del contacto',
};

function buildSystemPrompt(category, collected, catalogInfo) {
  const required = REQUIRED_FIELDS[category] || REQUIRED_FIELDS.GENERAL;
  const missing = required.filter(f => !collected[f]);
  const collectedStr = Object.entries(collected)
    .filter(([,v]) => v)
    .map(([k,v]) => `  - ${FIELD_LABELS[k] || k}: ${v}`)
    .join('\n') || '  (ninguno aún)';

  const missingStr = missing.length > 0
    ? missing.map(f => `  - ${FIELD_LABELS[f]}`).join('\n')
    : '  TODOS los datos han sido recogidos';

  const completionInstruction = missing.length === 0
    ? `\n\nTODOS LOS DATOS ESTÁN RECOGIDOS. Despídete amablemente, confirma que has registrado la solicitud y que el equipo se pondrá en contacto. Luego responde SOLO con esta línea final:\nDATA_COMPLETE:${JSON.stringify({ contact: { name: collected.name, phone: collected.phone, address: collected.address || null }, details: { problem: collected.problem, concept: collected.concept, subject: collected.subject, reason: collected.reason } })}`
    : '';

  const catalogSection = catalogInfo
    ? `\nINFORMACIÓN DE CATÁLOGO DISPONIBLE (comparte si es relevante):\n${catalogInfo}\n`
    : '';

  return `Eres el asistente virtual de ${config.company.name}, empresa especializada en ${config.company.sector}.

CATEGORÍA DE ESTA CONSULTA: ${category}
${getCategoryInstructions(category)}

DATOS YA RECOGIDOS:
${collectedStr}

DATOS QUE FALTAN POR RECOGER:
${missingStr}
${catalogSection}
INSTRUCCIONES:
- Habla en español, tono amable y profesional pero cercano (tuteo).
- Recoge los datos que faltan de forma natural, sin parecer un formulario.
- Pide máximo 2 datos por mensaje.
- No menciones la categoría de la consulta al cliente.
- Si el cliente pregunta precios o productos y tienes info del catálogo, compártela brevemente.
- Mensajes cortos y directos (WhatsApp, no email).
- NO uses asteriscos, ni markdown. Texto plano.${completionInstruction}`;
}

function getCategoryInstructions(category) {
  switch(category) {
    case 'AVERIA':
      return 'El cliente tiene una avería o necesita mantenimiento. Transmite urgencia y empatía. Necesitas su dirección exacta para enviar al técnico.';
    case 'COMERCIAL':
      return 'El cliente tiene interés comercial. Sé proactivo y ayúdale a concretar qué necesita. Si hay precios en el catálogo, compártelos indicando que son orientativos.';
    case 'ADMINISTRATIVO':
      return 'Es una consulta administrativa. Sé eficiente y conciso. Recoge el asunto claramente.';
    default:
      return 'Es una comunicación general. Atiende con amabilidad y recoge el motivo del contacto.';
  }
}

async function runConversationTurn(category, history, userMessage, collected, catalogInfo) {
  const systemPrompt = buildSystemPrompt(category, collected, catalogInfo);

  // Construir historial de mensajes para Claude
  const messages = [
    ...history.map(m => ({
      role: m.direction === 'inbound' ? 'user' : 'assistant',
      content: m.content,
    })),
    { role: 'user', content: userMessage },
  ];

  const response = await client.messages.create({
    model: config.anthropic.modelPro,
    max_tokens: 400,
    system: [
      {
        type: 'text',
        text: systemPrompt,
        cache_control: { type: 'ephemeral' },
      }
    ],
    messages,
  });

  const text = response.content[0].text.trim();

  // Detectar si Claude indica datos completos
  if (text.includes('DATA_COMPLETE:')) {
    const jsonStr = text.split('DATA_COMPLETE:')[1].trim();
    const conversationalPart = text.split('DATA_COMPLETE:')[0].trim();
    try {
      const data = JSON.parse(jsonStr);
      return { reply: conversationalPart, complete: true, data };
    } catch {
      return { reply: conversationalPart, complete: false };
    }
  }

  return { reply: text, complete: false };
}

// Extracción incremental de datos del historial de mensajes
async function extractCollectedData(category, history) {
  if (history.length === 0) return {};

  const required = REQUIRED_FIELDS[category] || REQUIRED_FIELDS.GENERAL;
  const historyText = history
    .map(m => `${m.direction === 'inbound' ? 'Cliente' : 'Bot'}: ${m.content}`)
    .join('\n');

  const response = await client.messages.create({
    model: config.anthropic.model,
    max_tokens: 200,
    system: [{
      type: 'text',
      text: `Extrae los datos del cliente de esta conversación de WhatsApp. Devuelve SOLO un JSON con los campos encontrados (omite los que no se mencionan). Campos posibles: name (nombre), phone (teléfono), address (dirección), problem (descripción avería), concept (interés comercial), subject (asunto), reason (motivo). No inventes datos.`,
      cache_control: { type: 'ephemeral' },
    }],
    messages: [{ role: 'user', content: historyText }],
  });

  try {
    const raw = response.content[0].text.trim().replace(/```json|```/g, '').trim();
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

module.exports = { runConversationTurn, extractCollectedData, REQUIRED_FIELDS };
