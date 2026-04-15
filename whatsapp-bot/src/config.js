require('dotenv').config();

module.exports = {
  port: process.env.PORT || 3000,
  nodeEnv: process.env.NODE_ENV || 'development',

  whatsapp: {
    token: process.env.WHATSAPP_TOKEN,
    phoneId: process.env.WHATSAPP_PHONE_ID,
    verifyToken: process.env.WHATSAPP_VERIFY_TOKEN || 'santored_verify_2024',
  },

  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY,
    model: 'claude-haiku-4-5-20251001',
    modelPro: 'claude-sonnet-4-6',
  },

  company: {
    name: process.env.COMPANY_NAME || 'Santored Santovenia',
    phone: process.env.COMPANY_PHONE || '+34 900 000 000',
    email: process.env.COMPANY_EMAIL || 'info@santored.com',
    sector: 'fabricación metálica y automatismos de accesos (puertas automáticas, vallas, cancelas, barreras)',
  },

  smtp: {
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT) || 587,
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },

  emails: {
    admin:      process.env.EMAIL_ADMIN      || 'admin@santored.com',
    tecnico:    process.env.EMAIL_TECNICO    || 'tecnico@santored.com',
    comercial:  process.env.EMAIL_COMERCIAL  || 'comercial@santored.com',
    general:    process.env.EMAIL_ADMIN      || 'admin@santored.com',
  },

  dbPath: process.env.DB_PATH || './data/bot.db',

  // Tiempo máximo de inactividad de sesión (30 min)
  sessionTTL: 30 * 60 * 1000,
};
