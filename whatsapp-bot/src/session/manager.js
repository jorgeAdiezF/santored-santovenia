const config = require('../config');

// Sesiones en memoria (se persiste lo esencial en la BD)
// Map: waPhone → session
const sessions = new Map();

function getSession(waPhone) {
  const session = sessions.get(waPhone);
  if (!session) return null;
  // Expirar sesión si lleva más de TTL sin actividad
  if (Date.now() - session.lastActivity > config.sessionTTL) {
    sessions.delete(waPhone);
    return null;
  }
  return session;
}

function createSession(waPhone, conversationId) {
  const session = {
    waPhone,
    conversationId,
    phase: 'greeting',      // greeting | collecting | completed
    category: null,
    collected: {},          // datos recogidos incrementalmente
    history: [],            // historial para contexto de Claude
    lastActivity: Date.now(),
  };
  sessions.set(waPhone, session);
  return session;
}

function updateSession(waPhone, updates) {
  const session = sessions.get(waPhone);
  if (!session) return null;
  Object.assign(session, updates, { lastActivity: Date.now() });
  return session;
}

function endSession(waPhone) {
  sessions.delete(waPhone);
}

function addToHistory(waPhone, direction, content) {
  const session = sessions.get(waPhone);
  if (!session) return;
  session.history.push({ direction, content, timestamp: new Date() });
  // Mantener últimas 20 interacciones para no superar tokens
  if (session.history.length > 20) session.history.shift();
  session.lastActivity = Date.now();
}

module.exports = { getSession, createSession, updateSession, endSession, addToHistory };
