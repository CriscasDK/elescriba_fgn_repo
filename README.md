# Sistema Escriba Legal
## Sistema Inteligente de Análisis de Documentos Judiciales

![Estado del Proyecto](https://img.shields.io/badge/Estado-Producci%C3%B3n-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-GPT4-green)
![Dash](https://img.shields.io/badge/Dash-2.17-blue)

---

## 🎯 Descripción

**Sistema Escriba Legal** es una plataforma completa de análisis inteligente de documentos judiciales del caso Unión Patriótica. Combina consultas a base de datos estructurada con análisis semántico mediante IA (RAG - Retrieval Augmented Generation) para proporcionar respuestas precisas y contextualizadas.

### Datos Procesados

- **11,111 documentos judiciales** procesados con GPT-4 Vision
- **12,248 víctimas** documentadas
- **100,025+ chunks** vectorizados en Azure AI Search
- **Base de datos PostgreSQL 15** con extensión Apache AGE para grafos

---

## ✨ Características Principales

- 🤖 **Chat Inteligente Unificado** - Una sola interfaz para consultas BD + RAG + Híbridas
- 🧠 **Clasificador Automático** - Decide qué motor usar según la consulta
- 🔍 **Sistema RAG Vectorizado** - Azure AI Search + GPT-4 para análisis semántico
- 📊 **Visualización de Grafos 3D** - Relaciones entre entidades con Plotly y AntV G6
- 🏛️ **Filtros Avanzados** - Por NUC, fechas, despachos y tipos de documento
- ⚡ **Consultas Optimizadas** - BD <200ms, RAG <3s
- 🎨 **Interfaz Moderna** - Dash 2.17 con diseño profesional

---

## 🏗️ Stack Tecnológico

### Backend
- **Python 3.12+** - Lenguaje principal
- **PostgreSQL 15** - Base de datos con extensión Apache AGE
- **Azure OpenAI GPT-4o-mini** - Modelos de IA
- **Azure AI Search** - Vectorización y búsqueda semántica

### Frontend
- **Dash 2.17** - Framework web interactivo
- **Plotly** - Visualizaciones 3D de grafos
- **Bootstrap** - UI moderna y responsiva

### DevOps
- **Docker & Docker Compose** - Containerización
- **Azure Container Apps** - Deployment cloud
- **GitHub** - Control de versiones

---

## 🚀 Quick Start

### Requisitos Previos

- Python 3.12+
- Docker y Docker Compose
- Cuenta Azure OpenAI
- Cuenta Azure AI Search

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/fgn-subtics/Escriba-back.git
cd Escriba-back

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Azure

# 3. Iniciar servicios con Docker
docker-compose up -d

# 4. Acceder a la aplicación
# Dash: http://localhost:8050
# pgAdmin: http://localhost:8080
```

---

## 📚 Documentación

### 📖 Para Tercerizadores / Nuevos Desarrolladores

**Documentos esenciales para entender y extender el sistema:**

1. **[GUIA_POBLAMIENTO_BASE_DATOS.md](GUIA_POBLAMIENTO_BASE_DATOS.md)** ⭐
   - Cómo poblar la base de datos desde cero
   - Scripts ETL y procesos de extracción
   - Troubleshooting de población

2. **[DOCUMENTACION_PROMPT_ANALISIS_GPT4_VISION.md](DOCUMENTACION_PROMPT_ANALISIS_GPT4_VISION.md)** ⭐
   - Prompt usado para procesar 11,111 documentos con GPT-4 Vision
   - Formato de análisis estructurado
   - Ejemplos de procesamiento OCR

3. **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** 📑
   - Índice completo de toda la documentación
   - Navegación por roles (Desarrollador, DevOps, Usuario)

### 📂 Documentación Organizada

La documentación completa está organizada en `/docs`:

#### Arquitectura
- [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) - Arquitectura del sistema
- [`docs/architecture/TECHNICAL_GUIDE.md`](docs/architecture/TECHNICAL_GUIDE.md) - Guía técnica detallada
- [`docs/architecture/RAG_SYSTEM.md`](docs/architecture/RAG_SYSTEM.md) - Sistema RAG y trazabilidad

#### Deployment
- [`docs/deployment/DEPLOYMENT.md`](docs/deployment/DEPLOYMENT.md) - Guía de despliegue completa
- [`docs/deployment/AZURE_DEPLOYMENT.md`](docs/deployment/AZURE_DEPLOYMENT.md) - Deployment en Azure
- [`docs/deployment/BACKUP_RESTORE.md`](docs/deployment/BACKUP_RESTORE.md) - Backups y restauración

#### Guías
- [`docs/guides/USER_GUIDE.md`](docs/guides/USER_GUIDE.md) - Guía de usuario
- [`docs/guides/INTEGRATION_GUIDE.md`](docs/guides/INTEGRATION_GUIDE.md) - Integración con otros sistemas
- [`docs/guides/FAQ.md`](docs/guides/FAQ.md) - Preguntas frecuentes
- Ver más en [`docs/guides/`](docs/guides/)

#### API
- [`docs/api/API_REFERENCE.md`](docs/api/API_REFERENCE.md) - Referencia completa de API REST

#### Seguridad
- [`docs/security/SECURITY.md`](docs/security/SECURITY.md) - Políticas de seguridad
- [`docs/security/CREDENTIALS_TEMPLATE.md`](docs/security/CREDENTIALS_TEMPLATE.md) - Template de credenciales
- [`docs/security/SECURITY_AUDIT.md`](docs/security/SECURITY_AUDIT.md) - Auditoría de seguridad

#### Troubleshooting
- [`docs/troubleshooting/TROUBLESHOOTING.md`](docs/troubleshooting/TROUBLESHOOTING.md) - Solución de problemas
- [`docs/troubleshooting/GRAPHS_TROUBLESHOOTING.md`](docs/troubleshooting/GRAPHS_TROUBLESHOOTING.md) - Problemas de grafos

#### Integraciones
- [`docs/integrations/G6_INTEGRATION_COMPLETED.md`](docs/integrations/G6_INTEGRATION_COMPLETED.md) - Integración AntV G6

---

## 🛠️ Uso

### Iniciar Aplicación

```bash
# Opción 1: Con scripts de inicio
./start_total.sh

# Opción 2: Manualmente
# Backend API (puerto 8010)
python src/api/rag_api.py

# Frontend Dash (puerto 8050)
python app_dash.py
```

### Acceder a Servicios

- **Dashboard Principal**: http://localhost:8050
- **API REST**: http://localhost:8010/docs
- **pgAdmin**: http://localhost:8080 (admin@example.com / admin_2025)

---

## 📊 Arquitectura

```
┌──────────────────────────────────────────────────────────┐
│                    USUARIO FINAL                         │
└────────────────┬─────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────┐
│              DASH FRONTEND (Puerto 8050)                 │
│  - Chat Interface                                        │
│  - Visualización de Grafos 3D                           │
│  - Filtros Avanzados                                     │
└────────────────┬─────────────────────────────────────────┘
                 │
                 v
┌──────────────────────────────────────────────────────────┐
│          CLASIFICADOR INTELIGENTE (LLM)                  │
│  Decide: BD | RAG | Híbrida                             │
└─────────┬────────────────────────┬───────────────────────┘
          │                        │
          v                        v
┌──────────────────┐    ┌──────────────────────────┐
│  PostgreSQL 15   │    │   Azure AI Search        │
│  + Apache AGE    │    │   + Azure OpenAI         │
│  (Consultas BD)  │    │   (Análisis Semántico)   │
└──────────────────┘    └──────────────────────────┘
```

---

## 🤝 Contribución

Este es un proyecto de la Fiscalía General de la Nación de Colombia para el análisis del caso Unión Patriótica.

### Repositorios

- **Backend**: https://github.com/fgn-subtics/Escriba-back
- **Frontend**: https://github.com/fgn-subtics/Escriba_front

---

## 📄 Licencia

Proyecto desarrollado para la Fiscalía General de la Nación de Colombia.

---

## 📞 Soporte

Para preguntas técnicas o problemas:

1. Consultar [`docs/troubleshooting/TROUBLESHOOTING.md`](docs/troubleshooting/TROUBLESHOOTING.md)
2. Revisar [`docs/guides/FAQ.md`](docs/guides/FAQ.md)
3. Consultar el índice completo: [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md)

---

**Sistema Escriba Legal v4.0** - Fiscalía General de la Nación de Colombia
