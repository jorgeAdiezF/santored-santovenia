# Sistema automático de lectura de facturas

Este repositorio implementa una base funcional para:

- Leer facturas escaneadas (imagen/PDF con OCR) y también archivos de texto.
- Extraer por factura: **proveedor**, **fecha** y **líneas de productos**.
- Procesar un archivo con **una o múltiples facturas** (por ejemplo PDF/txt con varios escaneos).
- Normalizar nombres de producto aunque cada proveedor use descripciones distintas.
- Guardar histórico en base de datos SQLite para analizar la **evolución de precios**.
- Mantener actualizado el **último precio de compra por producto y proveedor**.

## Arquitectura

- `src/invoice_system/ocr.py`: extracción OCR/texto por formato.
- `src/invoice_system/parser.py`: parser de facturas y separación de facturas múltiples.
- `src/invoice_system/normalizer.py`: normalización y similitud de nombres de producto.
- `src/invoice_system/database.py`: modelo de datos SQLite + consultas de evolución.
- `src/invoice_system/service.py`: orquestación de ingesta y persistencia.
- `src/invoice_system/cli.py`: CLI para procesar lotes.

## Modelo de datos (SQLite)

Tablas principales:

- `suppliers`: proveedores.
- `products`: producto canónico normalizado.
- `product_aliases`: equivalencias proveedor -> producto canónico.
- `invoices`: cabecera de factura.
- `invoice_items`: detalle de productos facturados.
- `latest_prices`: último precio por producto y proveedor.

## Uso

### 1. Ejecutar tests

```bash
python -m pytest -q
```

### 2. Ingestar facturas

```bash
python -m invoice_system.cli --db invoices.db factura1.pdf factura2.png lote_facturas.txt
```

Salida esperada:

```text
Facturas procesadas: N
```

## Formato esperado del parser base

El parser incluido reconoce líneas con patrón:

```text
<qty> x <descripcion> <precio_unitario> <precio_total>
```

Ejemplo:

```text
1 x Leche Entera 1L 1,20 1,20
```

Y cabeceras tipo:

```text
Proveedor: Acme Foods
Factura N: FAC-001
Fecha: 01/01/2025
```

> Nota: para producción real conviene sustituir/extender el parser por plantillas por proveedor o por un extractor con LLM + validación.

## Dependencias externas opcionales

- `tesseract` para OCR de imágenes.
- `pdftotext` (poppler) para extracción de texto de PDF.

Si no están instaladas, la ingesta OCR de esos formatos fallará con un mensaje explícito.
