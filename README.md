# Sistema Inteligente de Procesamiento de Facturas

Sistema para convertir facturas de compra (PDF digital o escaneado) en una base de datos estructurada, histórica y consultable. Permite control de compras, análisis de evolución de precios, comparación de proveedores e imputación de materiales a destinos.

## Arquitectura

```
Frontend (React)  →  API Gateway (8000)  →  Microservicios FastAPI
                                         →  Workers Celery (async)
                                         →  PostgreSQL + MinIO + Redis
```

| Servicio | Puerto | Función |
|---|---|---|
| `api_gateway` | 8000 | Proxy JWT, API externa v1, rate limiting |
| `auth_service` | 8001 | Autenticación JWT, usuarios y roles |
| `document_service` | 8002 | Carga de PDFs, almacenamiento MinIO |
| `segmentation_service` | 8003 | Detección de facturas en lotes |
| `ocr_service` | 8004 | OCR con Tesseract, extracción de campos |
| `materials_service` | 8005 | Catálogo de materiales y proveedores |
| `homologation_service` | 8006 | Motor de equivalencias (rapidfuzz + TF-IDF) |
| `review_service` | 8007 | Revisión manual de facturas |
| `destinations_service` | 8008 | Destinos de materiales |
| `analytics_service` | 8009 | Histórico de precios, dashboard |
| `frontend` | 3000 | Interfaz React + Ant Design |

**Infraestructura:** PostgreSQL 16, Redis 7, RabbitMQ 3, MinIO

## Requisitos

- Docker 24+ y Docker Compose 2.20+
- 4 GB RAM mínimo (8 GB recomendado para OCR)
- 10 GB espacio en disco

## Arranque rápido

```bash
# 1. Clonar y configurar
git clone https://github.com/jorgeAdiezF/santored-santovenia.git
cd santored-santovenia
cp .env.example .env

# 2. Editar .env con un JWT_SECRET seguro
#    JWT_SECRET=cambia_esto_por_una_clave_segura_de_32_chars

# 3. Levantar todo
make up

# 4. Verificar que los servicios arrancan
make ps
```

La interfaz estará disponible en **http://localhost:3000**

Credenciales iniciales: `admin` / `admin123`

## Variables de entorno

Editar `.env` antes del primer arranque:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `JWT_SECRET` | Clave para firmar tokens JWT | `supersecretjwtkey...` (**cambiar**) |
| `CORS_ORIGINS` | Orígenes permitidos en producción | `http://localhost:3000` |
| `ENVIRONMENT` | `development` (CORS abierto) o `production` | `development` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `invoices_pass` |
| `MINIO_ROOT_PASSWORD` | Contraseña de MinIO | `minioadmin123` |

## Flujo de trabajo

```
1. Subir PDF  →  document_service guarda en MinIO
2. Auto       →  segmentation_worker detecta facturas dentro del PDF
3. Auto       →  ocr_worker extrae cabecera y líneas (Tesseract)
4. Manual     →  Usuario revisa y corrige datos en el frontend
5. Auto/Manual→  homologation_worker vincula líneas a materiales maestros
6. Manual     →  Usuario asigna destino a cada línea
7. Auto       →  price_history se actualiza; vistas materializadas se refrescan
```

## Comandos útiles

```bash
make up              # Levantar todos los servicios
make down            # Parar todos los servicios
make logs            # Ver logs en tiempo real
make ps              # Estado de los contenedores
make test-unit       # Ejecutar los 69 tests unitarios
make test-coverage   # Tests con informe de cobertura
make shell-db        # Consola PostgreSQL
make shell-redis     # Consola Redis
make minio-init      # Recrear buckets de MinIO manualmente

# Escalar workers para mayor carga
make scale-workers   # segmentation x2, ocr x3

# Monitorización de colas Celery
make flower          # Abre Flower en :5555
```

## API externa (integración con otros sistemas)

La API pública está disponible en `http://localhost:8000/api/v1/`:

```
GET /api/v1/materials                    # Catálogo de materiales
GET /api/v1/materials/{id}/last-price    # Último precio válido de un material
GET /api/v1/materials/{id}/history       # Histórico de precios
GET /api/v1/providers                    # Lista de proveedores
GET /api/v1/destinations                 # Lista de destinos
```

Documentación interactiva (Swagger): `http://localhost:8000/docs`

## Estructura del repositorio

```
├── backend/
│   ├── shared/          # Modelos ORM, auth JWT, schemas Pydantic, config
│   ├── auth_service/
│   ├── document_service/
│   ├── segmentation_service/
│   ├── ocr_service/
│   ├── materials_service/
│   ├── homologation_service/
│   ├── review_service/
│   ├── destinations_service/
│   ├── analytics_service/
│   └── api_gateway/
├── frontend/            # React 18 + TypeScript + Ant Design
├── database/
│   └── migrations/      # Schema PostgreSQL y vistas materializadas
├── .github/workflows/   # CI/CD GitHub Actions
├── docker-compose.yml
├── Makefile
└── pytest.ini
```

## Tests

```bash
# Instalar dependencias de test
pip install pytest pytest-asyncio httpx aiosqlite

# Ejecutar suite completa (69 tests)
pytest backend/ -v

# Tests de un servicio específico
pytest backend/materials_service/tests/ -v
```

Los tests usan SQLite en memoria y mocks de servicios externos — no requieren Docker.

## CI/CD

- **Push a cualquier rama**: ejecuta tests Python, build TypeScript y build Docker de los servicios principales
- **Tag `v*`**: publica imágenes Docker en GitHub Container Registry (ghcr.io)

## Producción

Antes de desplegar en producción:

1. Cambiar **todos** los secretos en `.env`
2. Establecer `ENVIRONMENT=production` (restringe CORS a `CORS_ORIGINS`)
3. Usar un certificado TLS en el API Gateway o un reverse proxy (nginx/Traefik)
4. Considerar escalar los workers OCR (`make scale-workers`)
