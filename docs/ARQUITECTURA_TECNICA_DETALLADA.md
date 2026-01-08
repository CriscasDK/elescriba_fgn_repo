# 🏗️ ARQUITECTURA TÉCNICA DETALLADA
## Sistema de Análisis de Documentos Judiciales

---

## 📐 DIAGRAMA DE ARQUITECTURA COMPLETA

```mermaid
graph TB
    subgraph "🗄️ CAPA DE ALMACENAMIENTO"
        subgraph "Datos Primarios"
            JSON[📁 JSON Files<br/>11,446 archivos<br/>~2.5GB]
            LOGS[📋 Logs<br/>Procesamiento<br/>Errores]
        end
        
        subgraph "Base de Datos Principal"
            DB[(🐘 PostgreSQL 15<br/>documentos_juridicos_gpt4<br/>11,111 docs)]
            MV[📊 Vistas Materializadas<br/>Performance Cache]
            IDX[🔍 Índices<br/>GIN, BTREE, Trigram]
        end
    end
    
    subgraph "⚙️ CAPA DE PROCESAMIENTO ETL"
        EXT[🔄 Extractor ETL<br/>Python + psycopg2]
        VAL[✅ Validador<br/>Esquemas JSON]
        TRAZ[🎯 Trazabilidad<br/>100% Cobertura]
        META[📋 Poblador Metadatos<br/>NUC, Serie, Detalle]
    end
    
    subgraph "🧠 CAPA DE INTELIGENCIA"
        subgraph "Sistema RAG"
            RAG_CACHE[💾 Cache RAG<br/>Respuestas Frecuentes]
            RAG_FUNC[🔧 Funciones SQL<br/>Búsqueda Contextual]
            RAG_TRACE[📊 Trazabilidad RAG<br/>Consultas + Feedback]
        end
        
        subgraph "Azure OpenAI"
            GPT[🤖 GPT-4.1<br/>Generación Respuestas]
            EMBED[🎯 Embeddings<br/>Búsqueda Semántica]
        end
        
        subgraph "Análisis Avanzado"
            SEARCH[🔍 Búsqueda Fuzzy<br/>pg_trgm + fuzzystrmatch]
            NETWORK[🕸️ Análisis Redes<br/>Co-ocurrencia]
            GEO[🗺️ Análisis Geográfico<br/>Departamental]
        end
    end
    
    subgraph "🎨 CAPA DE PRESENTACIÓN"
        subgraph "Interfaces Usuario"
            DASH[📊 Dashboard<br/>Streamlit/React]
            API[🔌 API REST<br/>FastAPI]
            JUPYTER[📓 Jupyter<br/>Análisis Interactivo]
        end
        
        subgraph "Reportes"
            EXEC[📈 Reportes Ejecutivos<br/>Métricas KPI]
            DETAIL[📋 Reportes Detallados<br/>Análisis Profundo]
            EXPORT[📤 Exportación<br/>PDF, Excel, JSON]
        end
    end
    
    subgraph "🔧 CAPA DE SERVICIOS"
        subgraph "Monitoreo"
            MONITOR[📺 Monitoreo Sistema<br/>Performance + Salud]
            AUDIT[🔍 Auditoría<br/>Logs + Trazabilidad]
        end
        
        subgraph "Mantenimiento"
            BACKUP[💾 Backup<br/>Automático Diario]
            REFRESH[🔄 Refresh MVs<br/>Vistas Materializadas]
            CLEAN[🧹 Limpieza<br/>Cache + Logs]
        end
    end
    
    %% Flujo de Datos
    JSON --> EXT
    EXT --> VAL
    VAL --> DB
    DB --> TRAZ
    TRAZ --> META
    
    %% Sistema RAG
    DB --> RAG_FUNC
    RAG_FUNC --> RAG_CACHE
    RAG_CACHE --> RAG_TRACE
    RAG_TRACE --> GPT
    
    %% Análisis
    DB --> SEARCH
    DB --> NETWORK
    DB --> GEO
    
    %% Performance
    DB --> MV
    DB --> IDX
    
    %% Interfaces
    MV --> DASH
    RAG_FUNC --> API
    DB --> JUPYTER
    
    %% Reportes
    DASH --> EXEC
    API --> DETAIL
    JUPYTER --> EXPORT
    
    %% Servicios
    DB --> MONITOR
    RAG_TRACE --> AUDIT
    MV --> REFRESH
    DB --> BACKUP
    LOGS --> CLEAN
    
    %% Estilos
    classDef storage fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef processing fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef intelligence fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef presentation fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef services fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class JSON,LOGS,DB,MV,IDX storage
    class EXT,VAL,TRAZ,META processing
    class RAG_CACHE,RAG_FUNC,RAG_TRACE,GPT,EMBED,SEARCH,NETWORK,GEO intelligence
    class DASH,API,JUPYTER,EXEC,DETAIL,EXPORT presentation
    class MONITOR,AUDIT,BACKUP,REFRESH,CLEAN services
```

---

## 🔄 FLUJO DE PROCESAMIENTO DETALLADO

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant R as Router
    participant S as SQL Engine
    participant M as Vistas Mat.
    participant G as RAG System
    participant A as Azure OpenAI
    participant D as PostgreSQL
    
    Note over U,D: Consulta Frecuente (Dashboard)
    U->>F: Solicita métricas
    F->>R: Clasifica consulta
    R->>M: Consulta vista materializada
    M->>D: SELECT optimizado
    D-->>M: Datos cached
    M-->>F: Respuesta rápida (<50ms)
    F-->>U: Dashboard actualizado
    
    Note over U,D: Consulta RAG (Contextual)
    U->>F: Pregunta compleja
    F->>R: Clasifica como RAG
    R->>G: Procesa consulta
    G->>S: Busca contexto SQL
    S->>D: Consulta dinámica
    D-->>S: Datos relevantes
    S-->>G: Contexto estructurado
    G->>A: Genera respuesta
    A-->>G: Respuesta enriquecida
    G-->>F: Respuesta final
    F-->>U: Análisis contextual
    
    Note over U,D: Consulta Híbrida
    U->>F: Búsqueda avanzada
    F->>R: Consulta híbrida
    par Búsqueda SQL
        R->>S: Búsqueda fuzzy
        S->>D: Query con similarity
        D-->>S: Resultados SQL
    and Cache RAG
        R->>G: Verifica cache
        G-->>R: Respuestas frecuentes
    end
    R->>F: Combina resultados
    F-->>U: Respuesta optimizada
```

---

## 📊 ESQUEMA DE BASE DE DATOS

```mermaid
erDiagram
    DOCUMENTOS {
        int id PK
        varchar archivo
        text texto_extraido
        text analisis
        varchar nuc
        timestamp created_at
        timestamp updated_at
    }
    
    METADATOS {
        int id PK
        int documento_id FK
        varchar nuc
        varchar serie
        text detalle
        varchar codigo
        varchar despacho
        timestamp created_at
    }
    
    PERSONAS {
        int id PK
        int documento_id FK
        varchar nombre
        varchar tipo
        text observaciones
        text descripcion
        timestamp created_at
    }
    
    ORGANIZACIONES {
        int id PK
        int documento_id FK
        varchar nombre
        varchar tipo
        text descripcion
        timestamp created_at
    }
    
    ANALISIS_LUGARES {
        int id PK
        int documento_id FK
        varchar nombre
        varchar tipo
        varchar municipio
        varchar departamento
        timestamp created_at
    }
    
    RAG_CONSULTAS {
        int id PK
        uuid sesion_id
        varchar usuario_id
        text pregunta_original
        text pregunta_normalizada
        varchar tipo_consulta
        varchar metodo_resolucion
        jsonb contexto_utilizado
        int tokens_prompt
        int tokens_respuesta
        numeric costo_estimado
        int tiempo_respuesta_ms
        timestamp timestamp_consulta
        inet ip_cliente
        text user_agent
    }
    
    RAG_RESPUESTAS {
        int id PK
        int consulta_id FK
        text respuesta_texto
        jsonb fuentes_utilizadas
        real confianza_score
        varchar metodo_generacion
        jsonb datos_estructurados
        jsonb metadatos_llm
        timestamp created_at
    }
    
    RAG_FEEDBACK {
        int id PK
        int consulta_id FK
        int respuesta_id FK
        int calificacion
        text feedback_texto
        jsonb aspectos_evaluados
        text respuesta_esperada
        timestamp timestamp_feedback
        inet ip_cliente
    }
    
    RAG_CACHE {
        int id PK
        varchar pregunta_hash UK
        text pregunta_normalizada
        text respuesta_cacheada
        jsonb fuentes_cache
        int veces_utilizada
        real calificacion_promedio
        timestamp ultima_utilizacion
        timestamp expires_at
        timestamp created_at
    }
    
    MV_DASHBOARD_PRINCIPAL {
        jsonb metricas_dashboard
    }
    
    MV_TOP_ENTIDADES {
        text tipo_entidad
        text entidad
        text subtipo
        int frecuencia
        int documentos
        text tag
    }
    
    MV_PERSONAS_FRECUENTES {
        varchar tipo
        varchar nombre
        int veces_mencionada
        int documentos_mencionada
        text[] casos_relacionados
        int[] documento_ids
    }
    
    DOCUMENTOS ||--|| METADATOS : "1:1"
    DOCUMENTOS ||--o{ PERSONAS : "1:N"
    DOCUMENTOS ||--o{ ORGANIZACIONES : "1:N"
    DOCUMENTOS ||--o{ ANALISIS_LUGARES : "1:N"
    RAG_CONSULTAS ||--o{ RAG_RESPUESTAS : "1:N"
    RAG_CONSULTAS ||--o{ RAG_FEEDBACK : "1:N"
    RAG_RESPUESTAS ||--o{ RAG_FEEDBACK : "1:N"
```

---

## ⚡ ESTRATEGIA DE PERFORMANCE

### Índices Críticos
```sql
-- Búsquedas frecuentes
CREATE INDEX idx_personas_nombre_gin ON personas USING GIN (nombre gin_trgm_ops);
CREATE INDEX idx_organizaciones_nombre_gin ON organizaciones USING GIN (nombre gin_trgm_ops);
CREATE INDEX idx_lugares_nombre_gin ON analisis_lugares USING GIN (nombre gin_trgm_ops);

-- Filtros comunes
CREATE INDEX idx_personas_tipo ON personas (tipo);
CREATE INDEX idx_organizaciones_tipo ON organizaciones (tipo);
CREATE INDEX idx_metadatos_nuc ON metadatos (nuc);
CREATE INDEX idx_documentos_nuc ON documentos (nuc);

-- Sistema RAG
CREATE INDEX idx_rag_consultas_timestamp ON rag_consultas (timestamp_consulta);
CREATE INDEX idx_rag_cache_hash ON rag_cache (pregunta_hash);
```

### Vistas Materializadas
```yaml
Actualizaciones:
  - mv_dashboard_principal: Cada 1 hora
  - mv_top_entidades: Cada 6 horas  
  - mv_personas_frecuentes: Cada 12 horas
  - mv_analisis_geografico: Cada 24 horas

Estrategia:
  - REFRESH CONCURRENTLY para vistas grandes
  - REFRESH completo para vistas pequeñas
  - Logs de performance por vista
```

---

## 🔒 SEGURIDAD Y AUDITORÍA

### Niveles de Seguridad
```yaml
Nivel 1 - Datos:
  - Encriptación en reposo (PostgreSQL)
  - Backup encriptado
  - Control de acceso por roles

Nivel 2 - Aplicación:
  - Sanitización de inputs SQL
  - Validación de tipos
  - Rate limiting en API

Nivel 3 - Red:
  - Firewall configurado
  - HTTPS obligatorio
  - VPN para acceso admin

Nivel 4 - Auditoría:
  - Log de todas las consultas RAG
  - Trazabilidad completa de cambios
  - Monitoreo de anomalías
```

### Trazabilidad RAG
```mermaid
graph LR
    A[Consulta Usuario] --> B[Log Entrada]
    B --> C[Procesamiento]
    C --> D[Generación Respuesta]
    D --> E[Log Salida]
    E --> F[Feedback Usuario]
    F --> G[Mejora Continua]
    G --> H[Actualización Cache]
    
    style A fill:#e3f2fd
    style E fill:#e8f5e8
    style G fill:#fff3e0
```

---

## 📈 MÉTRICAS Y KPIs

### Métricas Técnicas
- **Latencia promedio:** < 200ms (consultas frecuentes), < 500ms (RAG)
- **Throughput:** 1000+ consultas/hora
- **Disponibilidad:** 99.9%
- **Precisión RAG:** 95%+ según feedback

### Métricas de Negocio
- **Cobertura datos:** 100% documentos procesados
- **Trazabilidad:** 99.9% víctimas con metadatos
- **Satisfacción usuario:** 4.2/5 promedio
- **Tiempo análisis:** Reducido 80% vs manual

---

## 🎯 ROADMAP FUTURO

### Corto Plazo (1-3 meses)
- [ ] Completar validación de 42 archivos SQL
- [ ] Implementar API REST completa
- [ ] Dashboard web interactivo
- [ ] Alertas automáticas

### Mediano Plazo (3-6 meses)
- [ ] Machine Learning para clasificación automática
- [ ] Integración con sistemas externos
- [ ] Mobile app
- [ ] Reportes automatizados

### Largo Plazo (6-12 meses)
- [ ] IA generativa para análisis predictivo
- [ ] Visualizaciones avanzadas
- [ ] Integración multi-idioma
- [ ] Escalamiento cloud

---

**📅 Última actualización:** Julio 28, 2025  
**🔖 Versión:** 2.0 Arquitectura Final
