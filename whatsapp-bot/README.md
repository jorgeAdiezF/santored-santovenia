# Bot WhatsApp — Atención Automática
**Santored Santovenia · Fabricación Metálica y Automatismos de Accesos**

## Arquitectura

```
WhatsApp (cliente)
      │
      ▼ POST /webhook
  Express Server
      │
      ▼
 Session Manager ──→ (estado conversación en memoria)
      │
      ▼
  Flow Router
      │
      ├─ Clasificador (Claude Haiku) ──→ AVERIA / COMERCIAL / ADMIN / GENERAL
      │
      ├─ Catálogo SQLite ──→ (si COMERCIAL, busca productos relevantes)
      │
      ▼
  Agente Conversacional (Claude Sonnet)
      │ system prompt con cache (ahorra tokens)
      ▼
  Respuesta WhatsApp
      │
      ▼ (al completar)
  Guardar en SQLite ──→ contacts / incidents / leads / tickets
      │
      ▼
  Email al equipo ──→ Técnico / Comercial / Administración
```

## Instalación

```bash
cd whatsapp-bot
npm install
cp .env.example .env
# Editar .env con tus credenciales
npm run seed          # Cargar catálogo de productos de ejemplo
npm run dev           # Arrancar en modo desarrollo
```

## Variables de entorno

| Variable | Descripción |
|---|---|
| `WHATSAPP_TOKEN` | Access Token permanente de Meta |
| `WHATSAPP_PHONE_ID` | Phone Number ID de Meta |
| `WHATSAPP_VERIFY_TOKEN` | Token secreto para verificar webhook |
| `ANTHROPIC_API_KEY` | Clave API de Anthropic (Claude) |
| `SMTP_*` | Configuración SMTP para emails |
| `EMAIL_TECNICO` | Email del servicio técnico |
| `EMAIL_COMERCIAL` | Email del equipo comercial |
| `EMAIL_ADMIN` | Email de administración |

## Configurar webhook en Meta

1. Ir a [developers.facebook.com](https://developers.facebook.com)
2. App → WhatsApp → Configuration
3. Webhook URL: `https://tu-dominio.com/webhook`
4. Verify Token: el valor de `WHATSAPP_VERIFY_TOKEN`
5. Suscribir al campo `messages`

## Simular en desarrollo (sin credenciales Meta)

```bash
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{"phone": "34600000001", "message": "Hola, mi puerta automática no abre"}'
```

## Panel de administración

Acceder a `http://localhost:3000/admin`

- KPIs en tiempo real (averías, leads, tickets, contactos)
- Historial de conversaciones
- Catálogo editable de productos y precios

## Categorías y routing

| Intención | Tabla BD | Email destino |
|---|---|---|
| AVERIA | `incidents` | Servicio Técnico |
| COMERCIAL | `leads` | Comercial |
| ADMINISTRATIVO | `tickets` | Administración |
| GENERAL | `tickets` | Administración |

## Próximas integraciones (roadmap)

- [ ] Integración con Google Calendar para gestión de citas
- [ ] Interfaz de respuesta desde el panel admin
- [ ] Historial de conversaciones completo en el panel
- [ ] Exportación CSV de leads/incidencias
- [ ] Métricas de tiempo de respuesta y satisfacción
