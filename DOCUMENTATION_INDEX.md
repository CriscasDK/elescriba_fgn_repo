# 📚 Índice de Documentación - Sistema Escriba Legal

> **Centro de documentación completa del Sistema de Análisis Inteligente de Documentos Judiciales**

---

## 🚀 Inicio Rápido

| Documento | Descripción | Para Quién |
|-----------|-------------|------------|
| **[README.md](README.md)** | 🏠 Visión general del proyecto + Quick Start | Todos |
| **[GUIA_POBLAMIENTO_BASE_DATOS.md](GUIA_POBLAMIENTO_BASE_DATOS.md)** | ⭐ Cómo poblar la BD desde cero | **Tercerizadores/Nuevos Dev** |
| **[DOCUMENTACION_PROMPT_ANALISIS_GPT4_VISION.md](DOCUMENTACION_PROMPT_ANALISIS_GPT4_VISION.md)** | ⭐ Prompt GPT-4 Vision para OCR | **Tercerizadores/Nuevos Dev** |

---

## 📂 Documentación por Categoría

### 🏗️ Arquitectura

Documentación técnica sobre la arquitectura del sistema.

| Documento | Descripción |
|-----------|-------------|
| [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) | Arquitectura completa del sistema |
| [docs/architecture/TECHNICAL_GUIDE.md](docs/architecture/TECHNICAL_GUIDE.md) | Guía técnica detallada y stack tecnológico |
| [docs/architecture/STRUCTURE_REFERENCE.md](docs/architecture/STRUCTURE_REFERENCE.md) | Estructura del proyecto y directorios |
| [docs/architecture/RAG_SYSTEM.md](docs/architecture/RAG_SYSTEM.md) | Sistema RAG y trazabilidad legal |
| [docs/architecture/RAG_OPTIMIZATIONS.md](docs/architecture/RAG_OPTIMIZATIONS.md) | Optimizaciones implementadas en RAG |

### 🚀 Deployment

Guías para despliegue en diferentes entornos.

| Documento | Descripción |
|-----------|-------------|
| [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) | **Guía principal de despliegue** |
| [docs/deployment/AZURE_DEPLOYMENT.md](docs/deployment/AZURE_DEPLOYMENT.md) | Deployment específico en Azure Container Apps |
| [docs/deployment/BACKUP_RESTORE.md](docs/deployment/BACKUP_RESTORE.md) | Estrategias de backup y restauración |

### 📖 Guías

Manuales paso a paso para diferentes tareas.

| Documento | Descripción |
|-----------|-------------|
| [docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md) | Manual de usuario del sistema |
| [docs/guides/INTEGRATION_GUIDE.md](docs/guides/INTEGRATION_GUIDE.md) | Integración con otros sistemas |
| [docs/guides/RESTART_GUIDE.md](docs/guides/RESTART_GUIDE.md) | Reiniciar servicios y troubleshooting básico |
| [docs/guides/FRONTEND_GUIDE.md](docs/guides/FRONTEND_GUIDE.md) | Desarrollo frontend con Dash |
| [docs/guides/QUERY_ROUTER.md](docs/guides/QUERY_ROUTER.md) | Sistema de enrutamiento de consultas |
| [docs/guides/FAQ.md](docs/guides/FAQ.md) | Preguntas frecuentes |
| [docs/guides/EXTRACTOR_OPTIMIZED.md](docs/guides/EXTRACTOR_OPTIMIZED.md) | Extractor optimizado de documentos |
| [docs/guides/EXTRACTOR_TECHNICAL.md](docs/guides/EXTRACTOR_TECHNICAL.md) | Documentación técnica del extractor |
| [docs/guides/AZURE_SEARCH_POPULATION.md](docs/guides/AZURE_SEARCH_POPULATION.md) | Poblamiento de Azure AI Search |
| [docs/guides/BEST_PRACTICES.md](docs/guides/BEST_PRACTICES.md) | Mejores prácticas de desarrollo |
| [docs/guides/AI_EXTRACTION.md](docs/guides/AI_EXTRACTION.md) | Instrucciones extracción con IA |

### 🔌 API

Documentación de la API REST.

| Documento | Descripción |
|-----------|-------------|
| [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md) | Referencia completa de endpoints |

### 🔒 Seguridad

Políticas y documentación de seguridad.

| Documento | Descripción |
|-----------|-------------|
| [docs/security/SECURITY.md](docs/security/SECURITY.md) | Políticas de seguridad del proyecto |
| [docs/security/CREDENTIALS_TEMPLATE.md](docs/security/CREDENTIALS_TEMPLATE.md) | Template para configuración de credenciales |
| [docs/security/SECURITY_AUDIT.md](docs/security/SECURITY_AUDIT.md) | Auditoría de seguridad urgente |
| [docs/security/REMOVED_FILES.md](docs/security/REMOVED_FILES.md) | Archivos removidos por seguridad |

### 🛠️ Troubleshooting

Solución de problemas comunes.

| Documento | Descripción |
|-----------|-------------|
| [docs/troubleshooting/TROUBLESHOOTING.md](docs/troubleshooting/TROUBLESHOOTING.md) | **Guía principal de troubleshooting** |
| [docs/troubleshooting/GRAPHS_TROUBLESHOOTING.md](docs/troubleshooting/GRAPHS_TROUBLESHOOTING.md) | Problemas específicos de grafos |

### 🔗 Integraciones

Documentación de integraciones con librerías externas.

| Documento | Descripción |
|-----------|-------------|
| [docs/integrations/G6_INTEGRATION_PLANNING.md](docs/integrations/G6_INTEGRATION_PLANNING.md) | Planificación integración AntV G6 |
| [docs/integrations/G6_INTEGRATION_COMPLETED.md](docs/integrations/G6_INTEGRATION_COMPLETED.md) | **Integración G6 completada** |
| [docs/integrations/CYTOSCAPE_PROTOTYPE_RESULTS.md](docs/integrations/CYTOSCAPE_PROTOTYPE_RESULTS.md) | Resultados prototipo Cytoscape.js |

---

## 🎯 Guías por Rol

### 👨‍💻 Para Desarrolladores Nuevos / Tercerizadores

**Ruta de aprendizaje recomendada:**

1. **[README.md](README.md)** - Visión general y Quick Start
2. **[GUIA_POBLAMIENTO_BASE_DATOS.md](GUIA_POBLAMIENTO_BASE_DATOS.md)** ⭐ - Población de BD
3. **[DOCUMENTACION_PROMPT_ANALISIS_GPT4_VISION.md](DOCUMENTACION_PROMPT_ANALISIS_GPT4_VISION.md)** ⭐ - Prompt OCR
4. **[docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** - Arquitectura
5. **[docs/architecture/TECHNICAL_GUIDE.md](docs/architecture/TECHNICAL_GUIDE.md)** - Detalles técnicos
6. **[docs/guides/FAQ.md](docs/guides/FAQ.md)** - Preguntas frecuentes
7. **[docs/troubleshooting/TROUBLESHOOTING.md](docs/troubleshooting/TROUBLESHOOTING.md)** - Problemas comunes

### 🚀 Para DevOps / Administradores

**Ruta de deployment:**

1. **[README.md](README.md)** - Requisitos previos
2. **[docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md)** - Guía principal
3. **[docs/deployment/AZURE_DEPLOYMENT.md](docs/deployment/AZURE_DEPLOYMENT.md)** - Azure específico
4. **[docs/security/CREDENTIALS_TEMPLATE.md](docs/security/CREDENTIALS_TEMPLATE.md)** - Configuración
5. **[docs/deployment/BACKUP_RESTORE.md](docs/deployment/BACKUP_RESTORE.md)** - Backups
6. **[docs/troubleshooting/TROUBLESHOOTING.md](docs/troubleshooting/TROUBLESHOOTING.md)** - Diagnósticos

### 🔐 Para Seguridad

**Documentación de seguridad:**

1. **[docs/security/SECURITY.md](docs/security/SECURITY.md)** - Políticas generales
2. **[docs/security/SECURITY_AUDIT.md](docs/security/SECURITY_AUDIT.md)** - Auditoría urgente
3. **[docs/security/CREDENTIALS_TEMPLATE.md](docs/security/CREDENTIALS_TEMPLATE.md)** - Gestión credenciales
4. **[docs/security/REMOVED_FILES.md](docs/security/REMOVED_FILES.md)** - Archivos sensibles removidos

### 🎓 Para Usuarios Finales

**Uso del sistema:**

1. **[README.md](README.md)** - Introducción
2. **[docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md)** - Manual de usuario
3. **[docs/guides/FAQ.md](docs/guides/FAQ.md)** - Preguntas frecuentes

---

## 🔍 Búsqueda Rápida

### ❌ Problemas Comunes

| Problema | Documento |
|----------|-----------|
| Error de conexión Azure OpenAI | [docs/troubleshooting/TROUBLESHOOTING.md](docs/troubleshooting/TROUBLESHOOTING.md) |
| Grafos no se visualizan | [docs/troubleshooting/GRAPHS_TROUBLESHOOTING.md](docs/troubleshooting/GRAPHS_TROUBLESHOOTING.md) |
| Base de datos vacía | [GUIA_POBLAMIENTO_BASE_DATOS.md](GUIA_POBLAMIENTO_BASE_DATOS.md) |
| Errores de deployment | [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) |

### ⚙️ Configuraciones Específicas

| Tarea | Documento |
|-------|-----------|
| Configurar Azure OpenAI | [docs/security/CREDENTIALS_TEMPLATE.md](docs/security/CREDENTIALS_TEMPLATE.md) |
| Configurar PostgreSQL | [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) |
| Configurar Docker | [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) |
| Configurar Azure AI Search | [docs/guides/AZURE_SEARCH_POPULATION.md](docs/guides/AZURE_SEARCH_POPULATION.md) |

### 🛠️ Tareas Comunes

| Tarea | Documento |
|-------|-----------|
| Poblar base de datos | [GUIA_POBLAMIENTO_BASE_DATOS.md](GUIA_POBLAMIENTO_BASE_DATOS.md) |
| Crear backup | [docs/deployment/BACKUP_RESTORE.md](docs/deployment/BACKUP_RESTORE.md) |
| Desplegar en Azure | [docs/deployment/AZURE_DEPLOYMENT.md](docs/deployment/AZURE_DEPLOYMENT.md) |
| Integrar con API externa | [docs/guides/INTEGRATION_GUIDE.md](docs/guides/INTEGRATION_GUIDE.md) |
| Añadir nuevo endpoint API | [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md) |

---

## 📊 Estadísticas de Documentación

- **Total documentos**: ~30 archivos MD
- **Categorías**: 7 (Arquitectura, Deployment, Guías, API, Seguridad, Troubleshooting, Integraciones)
- **Última actualización**: Enero 2026
- **Estado**: ✅ Documentación completa y organizada

---

## 🔄 Actualizaciones

### Enero 2026
- ✅ Reorganización completa en estructura /docs
- ✅ Nuevo README.md unificado
- ✅ Eliminación de 24 archivos obsoletos
- ✅ Creación de categorías temáticas
- ✅ Índice actualizado

### Octubre 2025
- Sistema v4.0 sanitizado
- Repositorios GitHub creados
- Documentación API REST

---

**¿No encuentras lo que buscas?**

1. Revisa el [README.md](README.md) principal
2. Consulta este índice por categoría
3. Busca por rol (Desarrollador, DevOps, Usuario, Seguridad)
4. Contacta al equipo de desarrollo

---

**Sistema Escriba Legal** - Fiscalía General de la Nación de Colombia
