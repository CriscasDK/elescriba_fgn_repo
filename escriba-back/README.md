# 🏛️ ESCRIBA-BACK - Backend API

**Sistema RAG de Análisis de Documentos Jurídicos - Backend**

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://postgresql.org)
[![Azure](https://img.shields.io/badge/Azure-OpenAI-orange)](https://azure.microsoft.com)

---

## 📋 **Descripción**

Backend API REST del sistema ESCRIBA (Explorador de Sistema de Consultas y Relaciones Inteligentes Basado en Análisis). Proporciona endpoints para:

- Consultas de base de datos (BD)
- Consultas RAG con Azure OpenAI
- Consultas híbridas (BD + RAG)
- Visualización de grafos 3D (Apache AGE)
- Gestión de documentos jurídicos

---

## 🚀 **Estado Actual**

⚠️ **ESTRUCTURA BASE** - En desarrollo

Este repositorio contiene la estructura base para migración del monolito actual a arquitectura separada Frontend/Backend.

**Progreso:**
- ✅ Estructura de directorios creada
- ✅ Módulos core copiados
- ✅ Tests de integración disponibles
- ⏳ API REST en desarrollo
- ⏳ Dockerización pendiente
- ⏳ Deploy Azure pendiente

---

## 📁 **Estructura del Proyecto**

```
escriba-back/
├── src/
│   ├── api/
│   │   ├── main.py                  # FastAPI app (pendiente)
│   │   ├── dependencies.py          # Auth, DB (pendiente)
│   │   └── routes/
│   │       ├── consultas.py         # Endpoints consultas (pendiente)
│   │       ├── grafos.py            # Endpoints grafos (pendiente)
│   │       └── documentos.py        # Endpoints docs (pendiente)
│   │
│   ├── core/
│   │   ├── consultas.py             # ✅ Lógica de consultas (copiado)
│   │   └── graph/                   # ✅ Grafos AGE (copiado)
│   │       └── context_graph_builder.py
│   │
│   ├── services/
│   │   ├── rag_service.py           # Azure OpenAI (pendiente)
│   │   ├── search_service.py        # Azure Search (pendiente)
│   │   └── database_service.py      # PostgreSQL (pendiente)
│   │
│   ├── database/
│   │   ├── models.py                # SQLAlchemy models (pendiente)
│   │   └── connection.py            # DB connection (pendiente)
│   │
│   └── utils/
│       └── logging_config.py        # ✅ Logging unificado (copiado)
│
├── tests/
│   ├── integration/                 # ✅ Tests integración (36 tests)
│   └── unit/                        # ⏳ Tests unitarios (pendiente)
│
├── config/
│   ├── .env.template                # ✅ Template variables entorno
│   └── constants.py                 # ✅ Constantes centralizadas
│
├── docs/
│   └── API.md                       # Documentación API (pendiente)
│
├── Dockerfile                       # Docker config (pendiente)
├── requirements.txt                 # Dependencias Python (pendiente)
└── README.md                        # Este archivo
```

---

## 🔧 **Tecnologías**

### Core:
- **Python 3.12**
- **FastAPI** - Framework API REST
- **PostgreSQL 15** - Base de datos principal
- **Apache AGE** - Base de datos de grafos
- **SQLAlchemy** - ORM

### Azure Services:
- **Azure OpenAI GPT-4** - Generación de respuestas RAG
- **Azure Cognitive Search** - Búsqueda semántica vectorial
- **Azure Database for PostgreSQL** - BD en producción
- **Azure Blob Storage** - Almacenamiento de PDFs

### Otros:
- **psycopg2** - Driver PostgreSQL
- **python-dotenv** - Variables de entorno
- **uvicorn** - ASGI server

---

## 📊 **Datos del Sistema**

### Base de Datos PostgreSQL:
- **Documentos:** 11,111 procesados
- **Víctimas:** 68,039 extraídas
- **Metadatos:** 11,111 registros
- **Lugares:** 24,147 análisis
- **Relaciones:** 86,987 (grafos AGE)

### Performance Esperada:
- Consultas BD: <5 segundos
- Consultas RAG: ~20 segundos
- Consultas Híbridas: <30 segundos
- Precisión clasificador: 97%

---

## 🚧 **Plan de Migración**

### FASE 1: API REST Básica (Semana 1)
- [ ] Crear `src/api/main.py` con FastAPI
- [ ] Endpoint `POST /api/v1/consultas/bd`
- [ ] Endpoint `POST /api/v1/consultas/rag`
- [ ] Endpoint `POST /api/v1/consultas/hibrida`
- [ ] Endpoint `GET /api/v1/grafos/{victima_nombre}`
- [ ] Middleware de autenticación
- [ ] Documentación OpenAPI/Swagger

### FASE 2: Servicios y Modelos (Semana 2)
- [ ] Crear modelos SQLAlchemy en `database/models.py`
- [ ] Servicio RAG en `services/rag_service.py`
- [ ] Servicio Search en `services/search_service.py`
- [ ] Servicio Database en `services/database_service.py`
- [ ] Connection pooling PostgreSQL

### FASE 3: Tests y Validación (Semana 2)
- [ ] Adaptar tests de integración existentes
- [ ] Tests unitarios de endpoints
- [ ] Tests de servicios
- [ ] Validación con datos reales

### FASE 4: Dockerización y Deploy (Semana 3)
- [ ] Crear Dockerfile multi-stage
- [ ] docker-compose para desarrollo local
- [ ] CI/CD con GitHub Actions
- [ ] Deploy a Azure Container Apps
- [ ] Monitoreo y logs

---

## 🔐 **Configuración**

### Variables de Entorno (.env):

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=documentos_juridicos_gpt4
POSTGRES_USER=docs_user
POSTGRES_PASSWORD=your_password

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Cognitive Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your_key
AZURE_SEARCH_INDEX_CHUNKS=exhaustive-legal-chunks-v2
AZURE_SEARCH_INDEX_DOCS=exhaustive-legal-index

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
DEBUG=False
```

---

## 📚 **Documentación Relacionada**

### Documentos en proyecto principal:
- `../RESUMEN_SANITIZACION_COMPLETA.md` - Estado de sanitización v4.0
- `../FASE6_REFACTORIZACION_PROGRESO.md` - Plan de refactorización
- `../SESION_30OCT_COMPLETA.md` - Resumen sesión actual

### Por crear:
- `docs/API.md` - Documentación completa de API
- `docs/ARCHITECTURE.md` - Arquitectura del sistema
- `docs/DEPLOYMENT.md` - Guía de deployment

---

## 🧪 **Tests**

```bash
# Ejecutar todos los tests
pytest tests/

# Tests de integración
pytest tests/integration/ -v

# Tests unitarios
pytest tests/unit/ -v

# Con coverage
pytest --cov=src tests/
```

### Tests Disponibles:
- ✅ `test_geographical_query.py` - 997 víctimas Antioquia
- ✅ `test_hybrid_detailed.py` - 8 menciones Oswaldo Olivo
- ✅ `test_estabilizacion.py` - Suite completa (6/7 PASS)

---

## 🔗 **Repositorios Relacionados**

- **ESCRIBA-FRONT**: Frontend Dash (interfaz de usuario)
- **Proyecto Monolítico**: `/home/lab4/scripts/documentos_judiciales/`

---

## 📝 **Estado de Desarrollo**

**Última actualización:** 30 de Octubre, 2025
**Versión:** 1.0.0-alpha (estructura base)
**Branch:** `main`

### Próximos Pasos:
1. Crear API REST con FastAPI
2. Implementar endpoints básicos
3. Tests de API
4. Dockerización
5. Deploy a Azure

---

## 👥 **Contribución**

Este proyecto está en fase de migración. Para contribuir:

1. Revisar plan de migración en documentación
2. Coordinar con equipo de desarrollo
3. Seguir guías de estilo de código
4. Agregar tests para nuevo código

---

## 📄 **Licencia**

[Información de licencia de la Fiscalía]

---

**🏛️ Fiscalía General de la Nación - Colombia**
**Sistema ESCRIBA - Backend API v1.0**
