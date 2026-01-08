# 🔄 FLUJOS DE TRABAJO Y PROCESOS
## Sistema de Documentos Judiciales

---

## 🎯 FLUJO PRINCIPAL DE PROCESAMIENTO

```mermaid
flowchart TD
    subgraph "📥 INGESTA DE DATOS"
        A[Archivos JSON<br/>11,446 files] --> B[Validación Schema]
        B --> C{Schema Válido?}
        C -->|NO| D[Log Error + Skip]
        C -->|SÍ| E[Extracción Metadatos]
        D --> F[Reporte Errores]
        E --> G[Validación Integridad]
    end
    
    subgraph "🏗️ PROCESAMIENTO ETL"
        G --> H[Limpieza Datos]
        H --> I[Normalización Entidades]
        I --> J[Poblado Base Datos]
        J --> K[Generación NUC/Serie]
        K --> L[Validación Trazabilidad]
    end
    
    subgraph "✅ CONTROL CALIDAD"
        L --> M{Trazabilidad OK?}
        M -->|NO| N[Proceso Corrección]
        M -->|SÍ| O[Índices y Vistas]
        N --> P[Reintento Automático]
        P --> M
        O --> Q[Sistema Listo]
    end
    
    subgraph "🔄 OPERACIÓN CONTINUA"
        Q --> R[Monitoreo Performance]
        R --> S[Refresh Vistas Mat.]
        S --> T[Backup Automático]
        T --> U[Mantenimiento DB]
        U --> R
    end
    
    style A fill:#e3f2fd
    style Q fill:#e8f5e8
    style F fill:#ffebee
    style N fill:#fff3e0
```

---

## 🧠 FLUJO SISTEMA RAG

```mermaid
flowchart LR
    subgraph "📝 ENTRADA USUARIO"
        A[Usuario Formula<br/>Pregunta] --> B[Router Consultas]
        B --> C{Tipo Consulta?}
    end
    
    subgraph "⚡ CONSULTAS FRECUENTES"
        C -->|Frecuente| D[Cache RAG]
        D --> E{En Cache?}
        E -->|SÍ| F[Respuesta Inmediata]
        E -->|NO| G[Vista Materializada]
        G --> H[Consulta SQL Optimizada]
        H --> I[Actualizar Cache]
        I --> F
    end
    
    subgraph "🔍 CONSULTAS RAG"
        C -->|Contextual| J[Análisis Consulta]
        J --> K[Extracción Contexto DB]
        K --> L[Construcción Prompt]
        L --> M[Azure OpenAI GPT-4]
        M --> N[Post-procesamiento]
        N --> O[Validación Respuesta]
        O --> P[Respuesta Enriquecida]
    end
    
    subgraph "🔄 CONSULTAS HÍBRIDAS"
        C -->|Compleja| Q[Búsqueda Fuzzy SQL]
        Q --> R[Análisis Semántico]
        R --> S[Combinación Resultados]
        S --> T[IA + SQL Híbrido]
        T --> U[Respuesta Integrada]
    end
    
    subgraph "📊 RETROALIMENTACIÓN"
        F --> V[Log Consulta]
        P --> V
        U --> V
        V --> W[Métricas Performance]
        W --> X[Feedback Usuario]
        X --> Y[Mejora Continua]
        Y --> D
    end
    
    style A fill:#e3f2fd
    style F fill:#e8f5e8
    style P fill:#e8f5e8
    style U fill:#e8f5e8
    style Y fill:#fff3e0
```

---

## 🔍 FLUJO DE BÚSQUEDAS AVANZADAS

```mermaid
stateDiagram-v2
    [*] --> Entrada_Usuario
    
    state "Clasificación Automática" as Clasificacion {
        Entrada_Usuario --> Analisis_Texto
        Analisis_Texto --> Detectar_Tipo
        
        state Detectar_Tipo {
            [*] --> Simple
            [*] --> Contextual
            [*] --> Geografica
            [*] --> Temporal
            [*] --> Entidades
        }
    }
    
    state "Procesamiento Especializado" as Procesamiento {
        Simple --> Busqueda_Directa
        Contextual --> RAG_Processing
        Geografica --> Analisis_Geografico
        Temporal --> Analisis_Temporal
        Entidades --> Extraccion_Entidades
        
        Busqueda_Directa --> SQL_Optimizado
        RAG_Processing --> IA_Contextual
        Analisis_Geografico --> Consultas_Geo
        Analisis_Temporal --> Consultas_Temporales
        Extraccion_Entidades --> Reconocimiento_NER
    }
    
    state "Agregación Resultados" as Agregacion {
        SQL_Optimizado --> Fusion_Resultados
        IA_Contextual --> Fusion_Resultados
        Consultas_Geo --> Fusion_Resultados
        Consultas_Temporales --> Fusion_Resultados
        Reconocimiento_NER --> Fusion_Resultados
        
        Fusion_Resultados --> Ranking_Relevancia
        Ranking_Relevancia --> Formato_Respuesta
    }
    
    Agregacion --> [*]
    
    note right of Entrada_Usuario
        Input: Texto libre
        Análisis NLP básico
        Detección intención
    end note
    
    note right of Fusion_Resultados
        Combinación inteligente
        Ponderación por relevancia
        Deduplicación automática
    end note
```

---

## 📈 FLUJO DE MONITOREO Y MANTENIMIENTO

```mermaid
timeline
    title Timeline de Mantenimiento Automático
    
    section Tiempo Real
        Logs Sistema : Errores
                    : Performance
                    : Consultas RAG
        
        Alertas     : Latencia Alta
                   : Errores Críticos
                   : Espacio Disco
    
    section Cada Hora
        Cache       : Limpieza automática
                   : Estadísticas uso
        
        Vistas Mat. : Refresh principales
                   : mv_dashboard_principal
    
    section Cada 6 Horas
        Analytics   : Métricas KPI
                   : Reportes uso
                   : mv_top_entidades
    
    section Diario
        Backup      : Base de datos completa
                   : Archivos configuración
                   : Logs sistema
        
        Limpieza    : Logs antiguos
                   : Cache obsoleto
                   : Temp files
    
    section Semanal
        Optimización : Análisis índices
                    : VACUUM ANALYZE
                    : Estadísticas tabla
        
        Reportes     : Dashboard ejecutivo
                    : Métricas rendimiento
                    : Análisis tendencias
    
    section Mensual
        Auditoría    : Revisión seguridad
                    : Análisis capacidad
                    : Plan escalamiento
        
        Updates      : Actualización dependencias
                    : Patches seguridad
                    : Optimizaciones nuevas
```

---

## 🛠️ FLUJO DE DESARROLLO Y DEPLOY

```mermaid
gitgraph
    commit id: "Init Sistema Base"
    
    branch feature/rag-system
    checkout feature/rag-system
    commit id: "Implement RAG Core"
    commit id: "Add Azure OpenAI"
    commit id: "Cache System"
    
    checkout main
    merge feature/rag-system
    commit id: "Release v1.0"
    
    branch feature/performance
    checkout feature/performance
    commit id: "Materialized Views"
    commit id: "Query Optimization"
    commit id: "Índices Avanzados"
    
    checkout main
    merge feature/performance
    commit id: "Release v1.1"
    
    branch feature/sql-validation
    checkout feature/sql-validation
    commit id: "SQL Validator"
    commit id: "42 Queries Analysis"
    commit id: "Test Suite Complete"
    
    checkout main
    merge feature/sql-validation
    commit id: "Release v1.2"
    
    branch feature/documentation
    checkout feature/documentation
    commit id: "Architecture Docs"
    commit id: "API Documentation"
    commit id: "User Guides"
    
    checkout main
    merge feature/documentation
    commit id: "Release v2.0 CURRENT"
    
    branch feature/api-rest
    checkout feature/api-rest
    commit id: "FastAPI Setup"
    commit id: "Endpoints Core"
    
    branch feature/dashboard
    checkout feature/dashboard
    commit id: "Streamlit Dashboard"
    commit id: "Interactive Charts"
    
    checkout main
    commit id: "Future v2.1" type: HIGHLIGHT
```

---

## 🔄 FLUJO DE ESCALAMIENTO

```mermaid
graph TB
    subgraph "📊 MONITOREO MÉTRICAS"
        A[CPU > 80%] --> D[Trigger Escalamiento]
        B[RAM > 85%] --> D
        C[Latencia > 500ms] --> D
        D --> E{Tipo Escalamiento?}
    end
    
    subgraph "⬆️ ESCALAMIENTO VERTICAL"
        E -->|Recursos| F[Aumentar CPU/RAM]
        F --> G[Optimizar Consultas]
        G --> H[Tune PostgreSQL]
        H --> I[Monitor Mejora]
    end
    
    subgraph "➡️ ESCALAMIENTO HORIZONTAL"
        E -->|Distribución| J[Read Replicas]
        J --> K[Load Balancer]
        K --> L[Particionado DB]
        L --> M[Microservicios]
    end
    
    subgraph "☁️ MIGRACIÓN CLOUD"
        E -->|Cloud| N[Containerización]
        N --> O[Kubernetes Deploy]
        O --> P[Auto-scaling]
        P --> Q[Multi-región]
    end
    
    subgraph "📈 VALIDACIÓN RESULTADOS"
        I --> R[Test Performance]
        M --> R
        Q --> R
        R --> S{Métricas OK?}
        S -->|NO| T[Rollback Seguro]
        S -->|SÍ| U[Producción Estable]
        T --> A
        U --> V[Documentar Cambios]
    end
    
    style D fill:#fff3e0
    style U fill:#e8f5e8
    style T fill:#ffebee
```

---

## 🚀 FLUJO DE DISASTER RECOVERY

```mermaid
flowchart LR
    subgraph "🚨 DETECCIÓN PROBLEMAS"
        A[Sistema Down] --> B[Alertas Automáticas]
        C[Corrupción Datos] --> B
        D[Hack/Seguridad] --> B
        B --> E[Evaluación Criticidad]
    end
    
    subgraph "🔄 RECUPERACIÓN INMEDIATA"
        E --> F{Severidad?}
        F -->|CRÍTICA| G[Failover Inmediato]
        F -->|ALTA| H[Backup Hot]
        F -->|MEDIA| I[Reparación Online]
        
        G --> J[Servidor Secundario]
        H --> K[Restore Incremental]
        I --> L[Fix en Caliente]
    end
    
    subgraph "🛠️ RESTAURACIÓN COMPLETA"
        J --> M[Validar Integridad]
        K --> M
        L --> M
        M --> N[Test Funcional]
        N --> O{Sistema OK?}
        O -->|NO| P[Restauración Manual]
        O -->|SÍ| Q[Producción Online]
        P --> M
    end
    
    subgraph "📋 POST-MORTEM"
        Q --> R[Análisis Causa Raíz]
        R --> S[Documentar Incidente]
        S --> T[Mejoras Proceso]
        T --> U[Actualizar Runbooks]
        U --> V[Training Equipo]
    end
    
    style G fill:#ffebee
    style Q fill:#e8f5e8
    style V fill:#e3f2fd
```

---

## 📋 CHECKLIST OPERACIONES DIARIAS

### ✅ Morning Checks (9:00 AM)
- [ ] Verificar estado servicios principales
- [ ] Revisar logs de errores nocturnos  
- [ ] Validar backup nocturno exitoso
- [ ] Comprobar espacio en disco disponible
- [ ] Verificar performance vistas materializadas

### ⚡ Midday Maintenance (12:00 PM)
- [ ] Refresh vistas materializadas críticas
- [ ] Limpiar cache RAG obsoleto
- [ ] Verificar métricas performance
- [ ] Revisar consultas lentas del día

### 🌙 Evening Tasks (18:00 PM)
- [ ] Análisis consultas RAG del día
- [ ] Reporte métricas KPI
- [ ] Preparar backup nocturno
- [ ] Revisar alertas pendientes
- [ ] Planning mantenimiento semanal

---

**📅 Última actualización:** Julio 28, 2025  
**🔖 Versión:** 2.0 Procesos Final
