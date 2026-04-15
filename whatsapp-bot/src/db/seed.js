// Semilla de catálogo de productos tipo para Santored Santovenia
require('dotenv').config();
const { upsertCatalogItem, getDb } = require('./database');

const items = [
  // PUERTAS AUTOMÁTICAS
  { category: 'Puertas automáticas', name: 'Puerta corredera automática 1 hoja', description: 'Puerta corredera de 1 hoja hasta 4m. Motor Came/Faac. Incluye detector de presencia.', priceFrom: 1200, priceTo: 2200, unit: 'instalación', notes: 'Precio orientativo. Requiere visita técnica para presupuesto exacto.' },
  { category: 'Puertas automáticas', name: 'Puerta corredera automática 2 hojas', description: 'Puerta corredera de 2 hojas hasta 8m. Motor industrial. Para naves y garajes.', priceFrom: 2000, priceTo: 3800, unit: 'instalación', notes: 'Incluye mando y detector perimetral.' },
  { category: 'Puertas automáticas', name: 'Puerta basculante automática', description: 'Puerta basculante para garaje o nave. Motor techo. Apertura rápida.', priceFrom: 900, priceTo: 1800, unit: 'instalación', notes: 'Incluye 2 mandos y kit seguridad.' },
  { category: 'Puertas automáticas', name: 'Puerta seccional industrial', description: 'Puerta seccional para naves industriales. Panel sandwich. Motor trifásico.', priceFrom: 2500, priceTo: 6000, unit: 'instalación', notes: 'Bajo pedido. Plazo 15-20 días.' },

  // CANCELAS Y VALLAS
  { category: 'Cancelas y vallas', name: 'Cancela batiente 1 hoja', description: 'Cancela de 1 hoja en acero o aluminio. Motor subterráneo o aéreo.', priceFrom: 800, priceTo: 1600, unit: 'instalación', notes: 'Ancho máximo 4m por hoja.' },
  { category: 'Cancelas y vallas', name: 'Cancela batiente 2 hojas', description: 'Cancela de 2 hojas para entrada de vehículos. Motor Came/BFT. Incluye fotocélulas.', priceFrom: 1500, priceTo: 3200, unit: 'instalación', notes: 'Requiere estudio de suelo.' },
  { category: 'Cancelas y vallas', name: 'Cancela corredera', description: 'Cancela corredera guiada o colgada. Ideal para solares y comunidades.', priceFrom: 1200, priceTo: 3000, unit: 'instalación', notes: 'Precio según peso y longitud de hoja.' },
  { category: 'Cancelas y vallas', name: 'Valla metálica de seguridad', description: 'Fabricación e instalación de valla metálica a medida. Tubo cuadrado + panel.', priceFrom: 45, priceTo: 120, unit: 'm²', notes: 'Precio por metro lineal según altura.' },

  // BARRERAS Y CONTROL ACCESO
  { category: 'Barreras y control de acceso', name: 'Barrera de parking', description: 'Barrera automática para parkings y aparcamientos. Brazo 3-6m. Motor rápido.', priceFrom: 900, priceTo: 2000, unit: 'unidad instalada', notes: 'Con o sin tarjeta/mando.' },
  { category: 'Barreras y control de acceso', name: 'Videoportero con apertura automática', description: 'Sistema videoportero con apertura automática de puerta o cancela.', priceFrom: 400, priceTo: 1200, unit: 'instalación', notes: 'Incluye monitor interior y cámara exterior.' },
  { category: 'Barreras y control de acceso', name: 'Control de acceso por tarjeta/huella', description: 'Lector de tarjeta RFID o huella dactilar para acceso restringido.', priceFrom: 350, priceTo: 900, unit: 'punto de acceso', notes: 'Gestión desde software o app.' },

  // FABRICACIÓN METÁLICA
  { category: 'Fabricación metálica', name: 'Estructura metálica a medida', description: 'Fabricación de estructuras en acero al carbono o inoxidable. Corte, dobla y soldadura.', priceFrom: 80, priceTo: 250, unit: 'kg', notes: 'Precio por kg fabricado e instalado. Requiere planos o medición.' },
  { category: 'Fabricación metálica', name: 'Escalera metálica', description: 'Fabricación e instalación de escalera metálica interior/exterior.', priceFrom: 1200, priceTo: 4500, unit: 'tramo', notes: 'Precio según escalones, ancho y acabado.' },
  { category: 'Fabricación metálica', name: 'Barandilla y pasamanos', description: 'Barandilla en acero, aluminio o inoxidable. Diseño a medida o estándar.', priceFrom: 120, priceTo: 380, unit: 'ml', notes: 'Precio por metro lineal instalado.' },

  // MANTENIMIENTO
  { category: 'Mantenimiento', name: 'Contrato mantenimiento anual puertas', description: 'Revisión anual + 2 visitas preventivas + mano de obra urgencias incluida.', priceFrom: 150, priceTo: 400, unit: 'año/puerta', notes: 'Descuento 15% en repuestos. Respuesta 24h.' },
  { category: 'Mantenimiento', name: 'Visita técnica urgente', description: 'Desplazamiento y diagnóstico urgente (mismo día o siguiente).', priceFrom: 90, priceTo: 150, unit: 'visita', notes: 'Mano de obra y piezas aparte. L-V 8-18h.' },
];

console.log('Insertando catálogo de productos...');
items.forEach(item => {
  upsertCatalogItem(item);
  console.log(`  ✓ ${item.category} — ${item.name}`);
});
console.log(`\n✅ ${items.length} productos cargados en el catálogo.`);
process.exit(0);
