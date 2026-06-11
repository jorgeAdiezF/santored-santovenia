-- 003_seed_materials_master.sql
-- Seed initial materials catalogue for the invoice processing system.
-- Based on product taxonomy from the reference portable application.
-- Safe to re-run: uses INSERT ... ON CONFLICT DO NOTHING.

BEGIN;

-- ============================================================
-- Family: 01 HIERROS Y ACEROS
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-01-001', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Redondo liso',                'Ø6mm – Ø50mm',   NULL,    'kg'),
  ('FAM-01-002', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Redondo corrugado B-500-S',   'Ø6mm – Ø32mm',   NULL,    'kg'),
  ('FAM-01-003', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Cuadrado macizo',              '10–100mm',       NULL,    'kg'),
  ('FAM-01-004', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Pletina plana',               NULL,             '3–20mm','kg'),
  ('FAM-01-005', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Ángulo igual',                '20×20–150×150',  NULL,    'kg'),
  ('FAM-01-006', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Ángulo desigual',             NULL,             NULL,    'kg'),
  ('FAM-01-007', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Tubo cuadrado',               '20×20–150×150',  '1.5–6mm','kg'),
  ('FAM-01-008', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Tubo rectangular',            '40×20–200×100',  '1.5–6mm','kg'),
  ('FAM-01-009', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'Tubo redondo',                'Ø20–Ø114',       '1.5–5mm','kg'),
  ('FAM-01-010', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'IPN / IPE',                   'IPE-100–IPE-600', NULL,   'kg'),
  ('FAM-01-011', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'HEB / HEA',                   'HEB-100–HEB-600', NULL,   'kg'),
  ('FAM-01-012', '01 HIERROS Y ACEROS', 'Perfiles laminados', 'UPN canal',                   'UPN-60–UPN-400',  NULL,   'kg'),
  ('FAM-01-013', '01 HIERROS Y ACEROS', 'Chapas y laminados', 'Chapa negra laminada en frío', NULL,            '0.5–12mm','kg'),
  ('FAM-01-014', '01 HIERROS Y ACEROS', 'Chapas y laminados', 'Chapa galvanizada',           NULL,             '0.5–3mm','kg'),
  ('FAM-01-015', '01 HIERROS Y ACEROS', 'Chapas y laminados', 'Chapa estriada',              NULL,             '3–6mm', 'kg'),
  ('FAM-01-016', '01 HIERROS Y ACEROS', 'Aceros especiales',  'Acero inoxidable AISI-304',   NULL,             NULL,    'kg'),
  ('FAM-01-017', '01 HIERROS Y ACEROS', 'Aceros especiales',  'Acero inoxidable AISI-316',   NULL,             NULL,    'kg'),
  ('FAM-01-018', '01 HIERROS Y ACEROS', 'Forja y fundición',  'Pieza de fundición gris',     NULL,             NULL,    'ud'),
  ('FAM-01-019', '01 HIERROS Y ACEROS', 'Forja y fundición',  'Pieza forjada',               NULL,             NULL,    'ud'),
  ('FAM-01-020', '01 HIERROS Y ACEROS', 'Malla y alambre',    'Malla electrosoldada',        '2000×1000',      '3–6mm', 'm2')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 02 MATERIAL ELÉCTRICO
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-02-001', '02 MATERIAL ELÉCTRICO', 'Cables',          'Cable unipolar flexible H07V-K',   'Ø1.5–25mm²', NULL, 'm'),
  ('FAM-02-002', '02 MATERIAL ELÉCTRICO', 'Cables',          'Cable manguera H05VV-F / H07RN-F', NULL,         NULL, 'm'),
  ('FAM-02-003', '02 MATERIAL ELÉCTRICO', 'Cables',          'Cable libre de halógenos AS',      '1.5–6mm²',   NULL, 'm'),
  ('FAM-02-004', '02 MATERIAL ELÉCTRICO', 'Cables',          'Cable apantallado RS-485',         NULL,         NULL, 'm'),
  ('FAM-02-005', '02 MATERIAL ELÉCTRICO', 'Tubos y canales', 'Tubo corrugado PVC',               'Ø16–63mm',   NULL, 'm'),
  ('FAM-02-006', '02 MATERIAL ELÉCTRICO', 'Tubos y canales', 'Tubo rígido PVC',                  'Ø16–63mm',   NULL, 'm'),
  ('FAM-02-007', '02 MATERIAL ELÉCTRICO', 'Tubos y canales', 'Canal cableado Unex',              '40×25–200×60',NULL,'m'),
  ('FAM-02-008', '02 MATERIAL ELÉCTRICO', 'Cuadros y cajas', 'Caja de distribución estanca',     NULL,         NULL, 'ud'),
  ('FAM-02-009', '02 MATERIAL ELÉCTRICO', 'Cuadros y cajas', 'Cuadro eléctrico 24 módulos',      NULL,         NULL, 'ud'),
  ('FAM-02-010', '02 MATERIAL ELÉCTRICO', 'Protecciones',    'Interruptor automático magnetotérmico 10A',NULL, NULL,'ud'),
  ('FAM-02-011', '02 MATERIAL ELÉCTRICO', 'Protecciones',    'Diferencial 25A 30mA 2P',          NULL,         NULL, 'ud'),
  ('FAM-02-012', '02 MATERIAL ELÉCTRICO', 'Iluminación',     'Luminaria LED industrial 150W',    NULL,         NULL, 'ud'),
  ('FAM-02-013', '02 MATERIAL ELÉCTRICO', 'Iluminación',     'Proyector LED exterior 50W',       NULL,         NULL, 'ud'),
  ('FAM-02-014', '02 MATERIAL ELÉCTRICO', 'Iluminación',     'Tubo LED T8 1500mm',               NULL,         NULL, 'ud')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 03 TORNILLERÍA Y FERRETERÍA
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-03-001', '03 TORNILLERÍA Y FERRETERÍA', 'Tornillería', 'Tornillo DIN-933 hexagonal ZN',     'M6×16 – M20×100', NULL, 'ud'),
  ('FAM-03-002', '03 TORNILLERÍA Y FERRETERÍA', 'Tornillería', 'Tornillo autoperforante TEK',       '4.2–6.3mm', NULL, 'caja'),
  ('FAM-03-003', '03 TORNILLERÍA Y FERRETERÍA', 'Tornillería', 'Perno de anclaje químico',          'M8–M20',    NULL, 'ud'),
  ('FAM-03-004', '03 TORNILLERÍA Y FERRETERÍA', 'Tornillería', 'Tornillo estructural ASTM-A325',    NULL,        NULL, 'kg'),
  ('FAM-03-005', '03 TORNILLERÍA Y FERRETERÍA', 'Anclajes',    'Taco plástico con tornillo',        'Ø5–14mm',   NULL, 'caja'),
  ('FAM-03-006', '03 TORNILLERÍA Y FERRETERÍA', 'Anclajes',    'Perno expansivo metálico',          'M8–M20',    NULL, 'ud'),
  ('FAM-03-007', '03 TORNILLERÍA Y FERRETERÍA', 'Anclajes',    'Resina de anclaje epoxi 300ml',     NULL,        NULL, 'ud'),
  ('FAM-03-008', '03 TORNILLERÍA Y FERRETERÍA', 'Soldadura',   'Electrodo básico 7018 rutílico',    'Ø2.5–4mm',  NULL, 'kg'),
  ('FAM-03-009', '03 TORNILLERÍA Y FERRETERÍA', 'Soldadura',   'Hilo macizo MIG/MAG',               'Ø0.8–1.2mm',NULL, 'kg'),
  ('FAM-03-010', '03 TORNILLERÍA Y FERRETERÍA', 'Soldadura',   'Gas protector argón+CO2 (mezcla)', NULL,        NULL, 'kg'),
  ('FAM-03-011', '03 TORNILLERÍA Y FERRETERÍA', 'Fijaciones',  'Grapa para tubo/cable',             'Ø12–63mm',  NULL, 'ud'),
  ('FAM-03-012', '03 TORNILLERÍA Y FERRETERÍA', 'Fijaciones',  'Cinta perforada zincada',           '17×0.8mm',  NULL, 'm'),
  ('FAM-03-013', '03 TORNILLERÍA Y FERRETERÍA', 'Fijaciones',  'Cadena de eslabones zincada',       NULL,        NULL, 'm'),
  ('FAM-03-014', '03 TORNILLERÍA Y FERRETERÍA', 'Remaches',    'Remache ciego de aluminio',         'Ø3.2–6.4mm',NULL, 'caja')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 04 CONSUMIBLES
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-04-001', '04 CONSUMIBLES', 'Abrasivos',    'Disco de corte metal A60T',         'Ø115–230×2.5mm', NULL, 'ud'),
  ('FAM-04-002', '04 CONSUMIBLES', 'Abrasivos',    'Disco de desbaste metal 6mm',       'Ø115–230×6mm',   NULL, 'ud'),
  ('FAM-04-003', '04 CONSUMIBLES', 'Abrasivos',    'Disco de corte piedra/hormigón',    'Ø115–230×3mm',   NULL, 'ud'),
  ('FAM-04-004', '04 CONSUMIBLES', 'Abrasivos',    'Hoja de sierra para madera',        '300–700mm',      NULL, 'ud'),
  ('FAM-04-005', '04 CONSUMIBLES', 'Abrasivos',    'Papel de lija rollo/hoja',          'P40–P400',       NULL, 'ud'),
  ('FAM-04-006', '04 CONSUMIBLES', 'Químicos',     'Desengrasante industrial',          NULL,             NULL, 'l'),
  ('FAM-04-007', '04 CONSUMIBLES', 'Químicos',     'Antioxidante / imprimación epoxi',  NULL,             NULL, 'l'),
  ('FAM-04-008', '04 CONSUMIBLES', 'Químicos',     'Lubricante WD-40 spray 400ml',      NULL,             NULL, 'ud'),
  ('FAM-04-009', '04 CONSUMIBLES', 'Químicos',     'Cinta adhesiva americana',          '48mm×50m',       NULL, 'ud'),
  ('FAM-04-010', '04 CONSUMIBLES', 'Químicos',     'Silicona neutra / ácida',           '310ml',          NULL, 'ud'),
  ('FAM-04-011', '04 CONSUMIBLES', 'Gases',        'Botella oxígeno 10l',               NULL,             NULL, 'ud'),
  ('FAM-04-012', '04 CONSUMIBLES', 'Gases',        'Botella acetileno 10l',             NULL,             NULL, 'ud')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 05 OBRA SECA Y PREFABRICADOS
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-05-001', '05 OBRA SECA Y PREFABRICADOS', 'Pladur/Cartón-yeso', 'Placa de yeso laminado (PYL) N',   '1200×2600',  '12.5mm','m2'),
  ('FAM-05-002', '05 OBRA SECA Y PREFABRICADOS', 'Pladur/Cartón-yeso', 'Placa de yeso laminado (PYL) H',   '1200×2600',  '12.5mm','m2'),
  ('FAM-05-003', '05 OBRA SECA Y PREFABRICADOS', 'Pladur/Cartón-yeso', 'Placa de yeso laminado (PYL) F',   '1200×2600',  '12.5mm','m2'),
  ('FAM-05-004', '05 OBRA SECA Y PREFABRICADOS', 'Pladur/Cartón-yeso', 'Perfil montante/canal 46/48/70/90mm',NULL,        NULL,    'm'),
  ('FAM-05-005', '05 OBRA SECA Y PREFABRICADOS', 'Mortero y hormigón', 'Cemento portland CEM II 32.5',     NULL,         NULL,    'saco'),
  ('FAM-05-006', '05 OBRA SECA Y PREFABRICADOS', 'Mortero y hormigón', 'Mortero seco M5 / M10',            NULL,         NULL,    'saco'),
  ('FAM-05-007', '05 OBRA SECA Y PREFABRICADOS', 'Mortero y hormigón', 'Hormigón preparado HA-25',         NULL,         NULL,    'm3'),
  ('FAM-05-008', '05 OBRA SECA Y PREFABRICADOS', 'Aislamiento',        'Lana mineral MW 50mm',             '1200×4000',  '50mm',  'm2'),
  ('FAM-05-009', '05 OBRA SECA Y PREFABRICADOS', 'Aislamiento',        'Panel de poliestireno XPS',        '1250×600',   '40mm',  'm2'),
  ('FAM-05-010', '05 OBRA SECA Y PREFABRICADOS', 'Prefabricados',      'Vigueta prefabricada de hormigón', NULL,         NULL,    'ud')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 06 MADERA Y DERIVADOS
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-06-001', '06 MADERA Y DERIVADOS', 'Tableros',     'Tablero aglomerado melamina',      '2440×1220',  '16mm', 'm2'),
  ('FAM-06-002', '06 MADERA Y DERIVADOS', 'Tableros',     'Tablero DM / MDF',                 '2440×1220',  '16mm', 'm2'),
  ('FAM-06-003', '06 MADERA Y DERIVADOS', 'Tableros',     'Tablero contrachapado fenólico',   '2500×1220',  '18mm', 'm2'),
  ('FAM-06-004', '06 MADERA Y DERIVADOS', 'Tableros',     'OSB-3',                            '2500×1250',  '18mm', 'm2'),
  ('FAM-06-005', '06 MADERA Y DERIVADOS', 'Madera natural','Tabla de pino',                   NULL,         '22mm', 'm3'),
  ('FAM-06-006', '06 MADERA Y DERIVADOS', 'Madera natural','Viga/rollizo de pino',            NULL,         NULL,   'm3'),
  ('FAM-06-007', '06 MADERA Y DERIVADOS', 'Accesorios',   'Tarugos/espigas de madera',        'Ø8×40mm',    NULL,   'caja'),
  ('FAM-06-008', '06 MADERA Y DERIVADOS', 'Accesorios',   'Ribete PVC / ABS',                 '22mm',       '0.4mm','m')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 07 EPI Y SEGURIDAD
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-07-001', '07 EPI Y SEGURIDAD', 'Protección cabeza',   'Casco de seguridad ABS',                NULL, NULL, 'ud'),
  ('FAM-07-002', '07 EPI Y SEGURIDAD', 'Protección ocular',   'Gafas de seguridad panorámica',         NULL, NULL, 'ud'),
  ('FAM-07-003', '07 EPI Y SEGURIDAD', 'Protección auditiva', 'Tapones auditivos desechables',         NULL, NULL, 'caja'),
  ('FAM-07-004', '07 EPI Y SEGURIDAD', 'Protección auditiva', 'Orejeras antirruido',                   NULL, NULL, 'ud'),
  ('FAM-07-005', '07 EPI Y SEGURIDAD', 'Protección vías resp.','Mascarilla FFP2 / FFP3',               NULL, NULL, 'caja'),
  ('FAM-07-006', '07 EPI Y SEGURIDAD', 'Protección manos',    'Guantes de trabajo anticorte niv. 5',  NULL, NULL, 'par'),
  ('FAM-07-007', '07 EPI Y SEGURIDAD', 'Protección pies',     'Bota seguridad S3 con puntera',        NULL, NULL, 'par'),
  ('FAM-07-008', '07 EPI Y SEGURIDAD', 'Protección cuerpo',   'Chaleco reflectante alta visibilidad', NULL, NULL, 'ud'),
  ('FAM-07-009', '07 EPI Y SEGURIDAD', 'Señalización',        'Cono de señalización vial 50cm',       NULL, NULL, 'ud'),
  ('FAM-07-010', '07 EPI Y SEGURIDAD', 'Señalización',        'Cinta de balizamiento bicolor',        NULL, NULL, 'rollo')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 08 MAQUINARIA Y HERRAMIENTAS
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-08-001', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta manual', 'Llave fija/combinada',          NULL, NULL, 'ud'),
  ('FAM-08-002', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta manual', 'Juego de llaves Allen',         NULL, NULL, 'juego'),
  ('FAM-08-003', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta manual', 'Alicate universal/de corte',    NULL, NULL, 'ud'),
  ('FAM-08-004', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta manual', 'Paleta de albañil/espátula',    NULL, NULL, 'ud'),
  ('FAM-08-005', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta eléctrica','Taladro percutor 13mm',       NULL, NULL, 'ud'),
  ('FAM-08-006', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta eléctrica','Amoladora angular 115/230mm', NULL, NULL, 'ud'),
  ('FAM-08-007', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta eléctrica','Soldadora inverter MMA',      NULL, NULL, 'ud'),
  ('FAM-08-008', '08 MAQUINARIA Y HERRAMIENTAS', 'Herramienta eléctrica','Sierra circular 190mm',       NULL, NULL, 'ud'),
  ('FAM-08-009', '08 MAQUINARIA Y HERRAMIENTAS', 'Medición',             'Nivel de burbuja 100cm',      NULL, NULL, 'ud'),
  ('FAM-08-010', '08 MAQUINARIA Y HERRAMIENTAS', 'Medición',             'Cinta métrica 5/10m',         NULL, NULL, 'ud'),
  ('FAM-08-011', '08 MAQUINARIA Y HERRAMIENTAS', 'Alquiler maquinaria',  'Alquiler dumper / mini-dumper',NULL,NULL, 'día'),
  ('FAM-08-012', '08 MAQUINARIA Y HERRAMIENTAS', 'Alquiler maquinaria',  'Alquiler andamio multidireccional',NULL,NULL,'sem')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 09 FONTANERÍA Y SANEAMIENTO
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-09-001', '09 FONTANERÍA Y SANEAMIENTO', 'Tuberías agua',   'Tubo cobre F22/M22',            'Ø15–54mm',  NULL, 'm'),
  ('FAM-09-002', '09 FONTANERÍA Y SANEAMIENTO', 'Tuberías agua',   'Tubo PVC presión PN-10',        'Ø25–110mm', NULL, 'm'),
  ('FAM-09-003', '09 FONTANERÍA Y SANEAMIENTO', 'Tuberías agua',   'Tubo multicapa PEX-Al-PEX',     'Ø16–32mm',  NULL, 'm'),
  ('FAM-09-004', '09 FONTANERÍA Y SANEAMIENTO', 'Saneamiento',     'Tubo saneamiento PVC SN4',      'Ø100–315mm',NULL, 'm'),
  ('FAM-09-005', '09 FONTANERÍA Y SANEAMIENTO', 'Saneamiento',     'Arqueta de registro PP',        '30×30–50×50',NULL,'ud'),
  ('FAM-09-006', '09 FONTANERÍA Y SANEAMIENTO', 'Grifería',        'Grifo de esfera 1/2" – 1"',     NULL,        NULL, 'ud'),
  ('FAM-09-007', '09 FONTANERÍA Y SANEAMIENTO', 'Grifería',        'Válvula de compuerta',          '1/2" – 2"', NULL, 'ud')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 10 PINTURA Y ACABADOS
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-10-001', '10 PINTURA Y ACABADOS', 'Pinturas interiores', 'Pintura plástica blanca mate interior', NULL, NULL, 'l'),
  ('FAM-10-002', '10 PINTURA Y ACABADOS', 'Pinturas interiores', 'Pintura plástica satinada interior',    NULL, NULL, 'l'),
  ('FAM-10-003', '10 PINTURA Y ACABADOS', 'Pinturas exteriores', 'Pintura acrílica exterior fachadas',    NULL, NULL, 'l'),
  ('FAM-10-004', '10 PINTURA Y ACABADOS', 'Pinturas especiales', 'Pintura antioxidante/anticorrosiva',    NULL, NULL, 'l'),
  ('FAM-10-005', '10 PINTURA Y ACABADOS', 'Pinturas especiales', 'Esmalte sintético brillante',           NULL, NULL, 'l'),
  ('FAM-10-006', '10 PINTURA Y ACABADOS', 'Accesorios',          'Rodillo de pelo 18cm',                  NULL, NULL, 'ud'),
  ('FAM-10-007', '10 PINTURA Y ACABADOS', 'Accesorios',          'Brocha de cerda natural 3"',             NULL, NULL, 'ud'),
  ('FAM-10-008', '10 PINTURA Y ACABADOS', 'Accesorios',          'Cinta de carrocero 50m',                NULL, NULL, 'ud'),
  ('FAM-10-009', '10 PINTURA Y ACABADOS', 'Acabados suelo',      'Barniz parquet satinado monocomponente',NULL, NULL, 'l'),
  ('FAM-10-010', '10 PINTURA Y ACABADOS', 'Acabados suelo',      'Resina epoxi para suelo industrial 2K', NULL, NULL, 'kit')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 11 CERRAJERÍA Y CARPINTERÍA METÁLICA
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-11-001', '11 CERRAJERÍA Y CARPINTERÍA METÁLICA', 'Puertas y accesos', 'Puerta industrial seccional motorizada', NULL, NULL, 'ud'),
  ('FAM-11-002', '11 CERRAJERÍA Y CARPINTERÍA METÁLICA', 'Puertas y accesos', 'Puerta metálica cortafuegos RF-60',      NULL, NULL, 'ud'),
  ('FAM-11-003', '11 CERRAJERÍA Y CARPINTERÍA METÁLICA', 'Puertas y accesos', 'Cerradura de seguridad con cilindro',    NULL, NULL, 'ud'),
  ('FAM-11-004', '11 CERRAJERÍA Y CARPINTERÍA METÁLICA', 'Rejas y vallas',    'Reja de acero galvanizado a medida',      NULL, NULL, 'm2'),
  ('FAM-11-005', '11 CERRAJERÍA Y CARPINTERÍA METÁLICA', 'Estructuras',       'Escalera de servicio de acero',           NULL, NULL, 'ud')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 12 COMBUSTIBLES Y LUBRICANTES
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-12-001', '12 COMBUSTIBLES Y LUBRICANTES', 'Combustibles', 'Gasóleo B (uso agrícola/industrial)',NULL, NULL, 'l'),
  ('FAM-12-002', '12 COMBUSTIBLES Y LUBRICANTES', 'Combustibles', 'Gasolina 95 E5',                    NULL, NULL, 'l'),
  ('FAM-12-003', '12 COMBUSTIBLES Y LUBRICANTES', 'Lubricantes',  'Aceite hidráulico ISO-46',           NULL, NULL, 'l'),
  ('FAM-12-004', '12 COMBUSTIBLES Y LUBRICANTES', 'Lubricantes',  'Grasa de litio multipropósito',      NULL, NULL, 'kg')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 13 CUBIERTAS Y CERRAMIENTOS
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-13-001', '13 CUBIERTAS Y CERRAMIENTOS', 'Chapa metálica', 'Chapa grecada acero galvanizado',    NULL, '0.5–0.8mm','m2'),
  ('FAM-13-002', '13 CUBIERTAS Y CERRAMIENTOS', 'Chapa metálica', 'Panel sándwich cubierta',            NULL, '40–80mm',  'm2'),
  ('FAM-13-003', '13 CUBIERTAS Y CERRAMIENTOS', 'Impermeabilización','Lámina impermeabilizante EPDM',   NULL, '1.2mm',    'm2'),
  ('FAM-13-004', '13 CUBIERTAS Y CERRAMIENTOS', 'Impermeabilización','Lámina asfáltica autoprotegida',  NULL, '4mm',      'm2'),
  ('FAM-13-005', '13 CUBIERTAS Y CERRAMIENTOS', 'Prefabricados',   'Bloque de hormigón split 40×20×15', NULL, NULL,       'ud')
ON CONFLICT (master_code) DO NOTHING;

-- ============================================================
-- Family: 14 SERVICIOS EXTERNOS
-- ============================================================
INSERT INTO materials_master (master_code, family, subfamily, normalized_description, dimensions, thickness, base_unit)
VALUES
  ('FAM-14-001', '14 SERVICIOS EXTERNOS', 'Telecomunicaciones', 'Servicio telefonía móvil empresas',  NULL, NULL, 'mes'),
  ('FAM-14-002', '14 SERVICIOS EXTERNOS', 'Telecomunicaciones', 'Servicio banda ancha fibra óptica',  NULL, NULL, 'mes'),
  ('FAM-14-003', '14 SERVICIOS EXTERNOS', 'Financieros',        'Servicio leasing vehículo/máquina',  NULL, NULL, 'mes'),
  ('FAM-14-004', '14 SERVICIOS EXTERNOS', 'Asesoría',           'Honorarios asesoría laboral/fiscal', NULL, NULL, 'mes'),
  ('FAM-14-005', '14 SERVICIOS EXTERNOS', 'Asesoría',           'Honorarios notariales y registrales',NULL, NULL, 'ud'),
  ('FAM-14-006', '14 SERVICIOS EXTERNOS', 'Transporte',         'Flete transporte mercancía general', NULL, NULL, 'envío')
ON CONFLICT (master_code) DO NOTHING;

COMMIT;

-- Verify counts
DO $$
DECLARE
  total_rows INT;
BEGIN
  SELECT COUNT(*) INTO total_rows FROM materials_master WHERE master_code LIKE 'FAM-%';
  RAISE NOTICE 'Seed: % materials_master rows inserted/confirmed', total_rows;
END;
$$;
