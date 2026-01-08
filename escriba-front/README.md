# 🖥️ ESCRIBA-FRONT - Frontend Dash

**Sistema RAG de Análisis de Documentos Jurídicos - Frontend**

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.14-green)](https://dash.plotly.com)
[![Plotly](https://img.shields.io/badge/Plotly-5.18-blue)](https://plotly.com)

---

## 📋 **Descripción**

Frontend interactivo del sistema ESCRIBA (Explorador de Sistema de Consultas y Relaciones Inteligentes Basado en Análisis). Interfaz web moderna construida con Dash/Plotly que proporciona:

- Panel de consultas inteligentes (BD/RAG/Híbrida)
- Visualización de grafos 3D de relaciones
- Historial conversacional contextual
- Filtros avanzados (geografía, fechas, NUC)
- Exploración de documentos jurídicos

---

## 🚀 **Estado Actual**

⚠️ **ESTRUCTURA BASE** - En desarrollo

Este repositorio contiene la estructura base modularizada extraída del monolito actual.

**Progreso:**
- ✅ Estructura de directorios creada
- ✅ Layout modularizado (354 líneas)
- ✅ Callbacks de historial (102 líneas)
- ✅ Callbacks de grafos 3D (374 líneas)
- ✅ Utilidades (municipios, contexto, entidades, PDF)
- ⏳ Integración con API REST pendiente
- ⏳ Dockerización pendiente
- ⏳ Deploy Azure pendiente

---

## 📁 **Estructura del Proyecto**

```
escriba-front/
├── src/
│   ├── app.py                       # Entry point (pendiente)
│   │
│   ├── layouts/
│   │   └── layout.py                # ✅ Layout principal (354 líneas)
│   │
│   ├── callbacks/
│   │   ├── __init__.py
│   │   ├── history.py               # ✅ Callbacks historial (102 líneas)
│   │   ├── graph.py                 # ✅ Callbacks grafos 3D (374 líneas)
│   │   └── main_query.py            # ✅ Callback chunks + stub principal
│   │
│   ├── components/
│   │   ├── panels.py                # Componentes paneles (pendiente)
│   │   ├── filters.py               # Componentes filtros (pendiente)
│   │   └── graphs.py                # Componentes grafos (pendiente)
│   │
│   ├── services/
│   │   └── api_client.py            # Cliente HTTP para backend (pendiente)
│   │
│   └── utils/
│       ├── municipios.py            # ✅ Carga municipios BD
│       ├── context.py               # ✅ Reescritura contextual
│       ├── entities.py              # ✅ Extracción entidades
│       └── pdf_handlers.py          # ✅ Manejo PDFs
│
├── assets/
│   ├── style.css                    # CSS personalizado (pendiente)
│   └── logo.png                     # Logo Fiscalía (pendiente)
│
├── config/
│   └── api_config.py                # Configuración API backend (pendiente)
│
├── tests/
│   └── test_components.py           # Tests UI (pendiente)
│
├── docs/
│   └── USER_GUIDE.md                # Guía de usuario (pendiente)
│
├── Dockerfile                       # Docker config (pendiente)
├── requirements.txt                 # Dependencias Python (pendiente)
└── README.md                        # Este archivo
```

---

## 🔧 **Tecnologías**

### Core:
- **Python 3.12**
- **Dash 2.14** - Framework web interactivo
- **Plotly 5.18** - Visualizaciones interactivas
- **Dash Bootstrap Components** - UI components

### Visualización:
- **Plotly 3D Graphs** - Grafos de relaciones
- **Dash DataTable** - Tablas interactivas
- **Dash Core Components** - Controles UI

### Comunicación:
- **requests** - Cliente HTTP para API REST
- **websockets** - Conexiones en tiempo real (futuro)

---

## ✨ **Funcionalidades**

### 1. Panel de Consultas Inteligentes
- **Clasificación automática**: BD / RAG / Híbrida (97% precisión)
- **Contexto conversacional**: Reescritura automática con historial
- **Límite de secuencia**: Evita drift semántico (3 reescrituras max)

### 2. Visualización de Grafos 3D
- **Red de relaciones** víctima-victimario-organizaciones
- **Búsqueda contextual** desde resultados
- **Consultas predefinidas** (nodos más conectados, familias)
- **Búsqueda libre** por nombre

### 3. Filtros Avanzados
- **NUC** (Número Único de Caso)
- **Geografía** (departamento, municipio)
- **Fechas** (rango de fechas)
- **Tipo de documento**
- **Despacho**

### 4. Historial Conversacional
- **Almacenamiento** de conversaciones
- **Límite configurable** de turnos (slider)
- **Visualización** tipo chat
- **Borrado** de historial

### 5. Exploración de Documentos
- **Vista detallada** de documentos
- **Descarga de PDFs** originales
- **Fuentes** con confianza (90% promedio)
- **Chunks** expandibles

---

## 🎨 **Componentes del Layout**

### Sección Superior:
- Botón flotante "🌐 Grafo 3D"
- Barra de consulta con botón enviar
- Checkbox "Usar contexto conversacional"

### Sección de Filtros:
- Dropdown NUC
- Dropdown Departamento
- Dropdown Municipio
- Dropdown Tipo de Documento
- Dropdown Despacho
- Date Picker (rango)

### Paneles de Resultados:
1. **Panel IA** (RAG):
   - Respuesta generada por GPT-4
   - Confianza y fuentes
   - Botón "Ver Red Contextual"

2. **Panel BD** (SQL):
   - Lista de víctimas
   - Paginación
   - Botones individuales para grafos

3. **Panel Fuentes**:
   - Documentos relevantes
   - Chunks con confianza
   - Descarga de PDFs

### Historial Conversacional:
- Panel colapsable lateral
- Slider de turnos máximos
- Botón "Limpiar Historial"
- Visualización de conversaciones

### Grafo 3D:
- Sección inline expandible
- Tabs: Predefinidas / Búsqueda / Contextual
- Configuración colapsable
- Visualización Plotly 3D

---

## 🚧 **Plan de Migración**

### FASE 1: Adaptación para API REST (Semana 1-2)
- [ ] Crear `src/app.py` entry point
- [ ] Crear `services/api_client.py` para consumir backend
- [ ] Adaptar callbacks para usar API REST:
  - `callbacks/main_query.py` → API calls
  - `callbacks/graph.py` → API calls
  - `callbacks/history.py` → Local storage
- [ ] Manejar autenticación/tokens
- [ ] Error handling y loading states

### FASE 2: Componentes y Optimización (Semana 2)
- [ ] Extraer componentes reutilizables:
  - `components/panels.py`
  - `components/filters.py`
  - `components/graphs.py`
- [ ] CSS personalizado en `assets/`
- [ ] Optimizar re-rendering
- [ ] Cache local de resultados

### FASE 3: Tests y Validación (Semana 2)
- [ ] Tests de componentes
- [ ] Tests de callbacks
- [ ] Validación funcional completa
- [ ] Performance testing

### FASE 4: Dockerización y Deploy (Semana 3)
- [ ] Crear Dockerfile
- [ ] docker-compose para desarrollo
- [ ] CI/CD con GitHub Actions
- [ ] Deploy a Azure Static Web Apps / Container Apps

---

## 🔐 **Configuración**

### Variables de Entorno (.env):

```env
# Backend API
BACKEND_API_URL=http://localhost:8000
BACKEND_API_KEY=your_api_key

# Dash Configuration
DASH_HOST=0.0.0.0
DASH_PORT=8050
DASH_DEBUG=False

# Features
ENABLE_CONTEXT=True
ENABLE_GRAPHS=True
MAX_HISTORY_TURNS=10
```

---

## 🚀 **Desarrollo Local**

```bash
# Clonar repositorio
git clone [repo-url]
cd escriba-front

# Crear ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp config/.env.template .env
# Editar .env con tus valores

# Ejecutar aplicación
python src/app.py

# Abrir en navegador
# http://localhost:8050
```

---

## 📊 **Métricas de Código**

### Código Extraído y Organizado:
- **Layout:** 354 líneas
- **Callbacks historial:** 102 líneas
- **Callbacks grafos:** 374 líneas
- **Utilidades:** 292 líneas
- **Total:** 1,122 líneas organizadas en módulos

### Reducción Esperada:
- **app.py original:** 1,773 líneas
- **app.py refactorizado:** ~50 líneas (97% reducción)

---

## 🧪 **Tests**

```bash
# Ejecutar todos los tests
pytest tests/

# Tests de componentes específicos
pytest tests/test_components.py -v

# Con coverage
pytest --cov=src tests/
```

---

## 🔗 **Integración con Backend**

### Endpoints Esperados:

```python
# Consultas
POST /api/v1/consultas/bd
POST /api/v1/consultas/rag
POST /api/v1/consultas/hibrida

# Grafos
GET /api/v1/grafos/{victima_nombre}
GET /api/v1/grafos/predefined/{query_type}

# Documentos
GET /api/v1/documentos/{doc_id}
GET /api/v1/documentos/{doc_id}/pdf

# Filtros
GET /api/v1/filters/nucs
GET /api/v1/filters/departamentos
GET /api/v1/filters/municipios
```

### Ejemplo de Uso:

```python
# services/api_client.py
import requests

class EscribaAPIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def consulta_hibrida(self, consulta, filtros, historial):
        response = requests.post(
            f"{self.base_url}/api/v1/consultas/hibrida",
            json={
                "consulta": consulta,
                "filtros": filtros,
                "historial": historial
            }
        )
        return response.json()
```

---

## 📚 **Documentación Relacionada**

### Documentos en proyecto principal:
- `../RESUMEN_SANITIZACION_COMPLETA.md` - Estado sanitización v4.0
- `../FASE6_REFACTORIZACION_PROGRESO.md` - Plan de refactorización
- `../SESION_30OCT_COMPLETA.md` - Resumen sesión actual

### Por crear:
- `docs/USER_GUIDE.md` - Guía completa de usuario
- `docs/COMPONENTS.md` - Documentación de componentes
- `docs/CALLBACKS.md` - Documentación de callbacks

---

## 🎯 **Componentes Destacados**

### 1. Reescritura Contextual (utils/context.py)
```python
def reescribir_query_con_contexto(consulta, historial):
    """
    Soluciona limitación RAG con preguntas secuenciales:
    - "Oswaldo Olivo" → "su relación con Rosa"
    - Se convierte en: "Oswaldo Olivo y su relación con Rosa"

    Límite: 3 reescrituras para evitar drift semántico
    """
```

### 2. Callbacks de Historial (callbacks/history.py)
- 5 callbacks modulares
- Manejo de límite de turnos
- Visualización tipo chat
- Persistencia en dcc.Store

### 3. Callbacks de Grafos (callbacks/graph.py)
- 4 callbacks para grafos 3D
- Integración con Apache AGE
- Visualización Plotly interactiva
- 3 modos de consulta

---

## 🔗 **Repositorios Relacionados**

- **ESCRIBA-BACK**: Backend API REST (FastAPI)
- **Proyecto Monolítico**: `/home/lab4/scripts/documentos_judiciales/`

---

## 📝 **Estado de Desarrollo**

**Última actualización:** 30 de Octubre, 2025
**Versión:** 1.0.0-alpha (estructura base)
**Branch:** `main`

### Próximos Pasos:
1. Crear app.py entry point
2. Implementar API client
3. Adaptar callbacks para API REST
4. Tests de integración
5. Dockerización
6. Deploy a Azure

---

## 👥 **Contribución**

Este proyecto está en fase de migración. Para contribuir:

1. Revisar plan de migración en documentación
2. Coordinar con equipo de desarrollo
3. Seguir guías de estilo de código
4. Agregar tests para nuevos componentes

---

## 📄 **Licencia**

[Información de licencia de la Fiscalía]

---

**🖥️ Fiscalía General de la Nación - Colombia**
**Sistema ESCRIBA - Frontend Dash v1.0**
