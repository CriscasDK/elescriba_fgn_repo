# FLUJO DE PROCESAMIENTO ETL

```mermaid
flowchart TD
    subgraph "🔄 Inicio del Proceso"
        A[JSON Files Directory] --> B{Verificar Archivos}
        B -->|11,446 files| C[Inicializar Pool de Workers]
        C --> D[8 Workers Paralelos]
    end
    
    subgraph "📋 Procesamiento por Documento"
        D --> E[Cargar JSON]
        E --> F{Documento Existe?}
        F -->|No| G[Insertar Documento]
        F -->|Sí| H[Obtener documento_id]
        G --> I[Extraer Metadatos]
        H --> J[Preparar Contenido para IA]
        I --> J
    end
    
    subgraph "🤖 Extracción con IA"
        J --> K{Seleccionar Fuente}
        K -->|Análisis| L[Usar campo 'analisis']
        K -->|Texto| M[Usar 'texto_extraido']
        K -->|Ambos| N[Combinar contenidos]
        L --> O[Truncar a 15,000 chars]
        M --> O
        N --> O
        O --> P[Enviar a GPT-4 Mini]
    end
    
    subgraph "🧠 Procesamiento GPT-4 Mini"
        P --> Q[Prompt Estructurado]
        Q --> R[Extracción de Entidades]
        R --> S[Clasificación Automática]
        S --> T[Validación de Schema JSON]
        T --> U{Respuesta Válida?}
        U -->|No| V[Reintentar]
        U -->|Sí| W[Entities Dict]
        V --> P
    end
    
    subgraph "💾 Inserción en Base de Datos"
        W --> X[Procesar Personas]
        X --> Y[Procesar Organizaciones]
        Y --> Z[Procesar Lugares]
        Z --> AA[Procesar Cargos/Roles]
        AA --> BB[Procesar Fechas]
        BB --> CC[Procesar Números ID]
        CC --> DD[Procesar Cantidades]
        DD --> EE[Procesar Contactos]
        EE --> FF[Procesar Estructura]
        FF --> GG[Procesar Resumen]
        GG --> HH[Commit Transaction]
    end
    
    subgraph "📊 Clasificación de Entidades"
        II[Lista General] --> JJ[Sin Tipo Específico]
        KK[Clasificación] --> LL[Víctimas]
        KK --> MM[Defensa]
        KK --> NN[Victimarios]
        KK --> OO[Actores Políticos]
        KK --> PP[Asociados Grupos Ilegales]
        KK --> QQ[Fuerzas Legítimas]
        KK --> RR[Fuerzas Ilegales]
    end
    
    subgraph "⚠️ Manejo de Errores"
        SS[Error de Duplicado] --> TT[Usar documento_id existente]
        UU[Error de IA] --> VV[Reintentar hasta 3 veces]
        WW[Error de DB] --> XX[Log y continuar]
        YY[Error de JSON] --> ZZ[Log y saltar archivo]
    end
    
    subgraph "📈 Monitoreo y Logs"
        AAA[Métricas por Worker]
        BBB[Tiempo de Procesamiento]
        CCC[Costos de IA]
        DDD[Errores y Excepciones]
        EEE[Progreso Global]
    end
    
    %% Conexiones
    X --> II
    X --> KK
    Y --> II
    Y --> KK
    
    HH --> FFF{Más Archivos?}
    FFF -->|Sí| E
    FFF -->|No| GGG[Proceso Completado]
    
    %% Errores
    F --> SS
    P --> UU
    HH --> WW
    E --> YY
    
    %% Monitoreo
    D --> AAA
    P --> BBB
    P --> CCC
    SS --> DDD
    D --> EEE
    
    style A fill:#e1f5fe
    style P fill:#f3e5f5
    style HH fill:#e8f5e8
    style SS fill:#ffebee
    style GGG fill:#e0f2f1
```

## Detalles del Flujo

### 1. Inicialización
- Escaneo de directorio `json_files/`
- Configuración de 8 workers paralelos
- Conexión a Azure OpenAI y PostgreSQL

### 2. Procesamiento por Worker
- Cada worker procesa archivos independientemente
- Manejo de concurrencia en base de datos
- Load balancing automático

### 3. Extracción de Entidades
- GPT-4 Mini con prompt estructurado
- Schema JSON predefinido
- Timeout de 30 segundos por request

### 4. Inserción Transaccional
- Una transacción por documento
- Rollback en caso de error crítico
- Commit solo si todo es exitoso

### 5. Monitoreo en Tiempo Real
- Logs detallados por worker
- Métricas de rendimiento
- Alertas de errores
