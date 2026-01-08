# 🗄️ MODELO ENTIDAD-RELACIÓN - SISTEMA DOCUMENTOS JURÍDICOS
## Esquema actualizado: 2025-07-29 07:03:47

---

## 📊 RESUMEN DEL ESQUEMA

**Total de tablas:** 25

| Tabla | Columnas | Foreign Keys | Índices | Propósito |
|-------|----------|--------------|---------|----------|
| `analisis_cantidades_valores` | 6 | 1 | 2 | Cantidades numéricas y valores mencionados |
| `analisis_cargos_roles` | 6 | 1 | 2 | Cargos y roles específicos de personas en el documento |
| `analisis_datos_contacto` | 6 | 1 | 2 | Información de contacto como teléfonos, direcciones |
| `analisis_delitos` | 7 | 1 | 5 | Delitos mencionados con detalles específicos |
| `analisis_estructura_documento` | 6 | 1 | 2 | Estructura formal del documento (secciones, elementos) |
| `analisis_fechas` | 6 | 1 | 5 | Fechas relevantes con su tipo y descripción |
| `analisis_lugares` | 9 | 1 | 5 | Lugares geográficos mencionados con detalles de ubicación |
| `analisis_numeros_identificacion` | 6 | 1 | 2 | Números de identificación como oficios, radicados, cédulas |
| `analisis_observaciones` | 4 | 1 | 2 | Observaciones adicionales del análisis |
| `analisis_organizaciones_clasificacion` | 5 | 1 | 5 | Clasificación de organizaciones: legítimas, ilegales, otras |
| `analisis_organizaciones_general` | 4 | 1 | 3 | Lista general de todas las organizaciones mencionadas |
| `analisis_personas_clasificacion` | 5 | 1 | 5 | Clasificación de personas por categorías: víctimas, defensa, etc. |
| `analisis_personas_general` | 4 | 1 | 3 | Lista general de todas las personas mencionadas en el documento |
| `analisis_resumen_contenido` | 7 | 1 | 2 | Resumen ejecutivo del contenido del documento |
| `analisis_tipo_documento` | 5 | 1 | 2 | Almacena el tipo específico y descripción de cada documento |
| `documentos` | 22 | 0 | 5 | Tabla principal de documentos jurídicos |
| `estadisticas` | 8 | 1 | 2 | Estadísticas de procesamiento y calidad del documento. |
| `metadatos` | 28 | 1 | 2 | Metadatos estructurados de cada documento, extraídos y enriquecidos por IA. |
| `organizaciones` | 6 | 1 | 1 | Tabla principal del sistema |
| `personas` | 12 | 1 | 3 | Tabla principal del sistema |
| `rag_analytics` | 12 | 0 | 1 | Tabla principal del sistema |
| `rag_cache` | 10 | 0 | 4 | Tabla principal del sistema |
| `rag_consultas` | 15 | 0 | 5 | Tabla principal del sistema |
| `rag_feedback` | 9 | 2 | 3 | Tabla principal del sistema |
| `rag_respuestas` | 9 | 1 | 2 | Tabla principal del sistema |

---

## 🔄 DIAGRAMA ENTIDAD-RELACIÓN

```mermaid
erDiagram
    ANALISIS_CANTIDADES_VALORES {
        integer id PK NOT NULL
        integer documento_id
        character varying tipo
        numeric cantidad
        text descripcion
        timestamp without time zone created_at
    }

    ANALISIS_CARGOS_ROLES {
        integer id PK NOT NULL
        integer documento_id
        character varying cargo
        character varying persona
        character varying entidad
        timestamp without time zone created_at
    }

    ANALISIS_DATOS_CONTACTO {
        integer id PK NOT NULL
        integer documento_id
        character varying tipo
        text valor
        character varying entidad
        timestamp without time zone created_at
    }

    ANALISIS_DELITOS {
        integer id PK NOT NULL
        integer documento_id
        character varying tipo_delito
        date fecha_hecho
        character varying lugar_hecho
        text descripcion
        timestamp without time zone created_at
    }

    ANALISIS_ESTRUCTURA_DOCUMENTO {
        integer id PK NOT NULL
        integer documento_id
        jsonb secciones_principales
        jsonb elementos_formales
        jsonb elementos_visuales
        timestamp without time zone created_at
    }

    ANALISIS_FECHAS {
        integer id PK NOT NULL
        integer documento_id
        date fecha
        character varying tipo
        text descripcion
        timestamp without time zone created_at
    }

    ANALISIS_LUGARES {
        integer id PK NOT NULL
        integer documento_id
        character varying nombre
        character varying tipo
        text direccion
        character varying municipio
        character varying departamento
        character varying pais
        timestamp without time zone created_at
    }

    ANALISIS_NUMEROS_IDENTIFICACION {
        integer id PK NOT NULL
        integer documento_id
        character varying tipo
        character varying numero
        text descripcion
        timestamp without time zone created_at
    }

    ANALISIS_OBSERVACIONES {
        integer id PK NOT NULL
        integer documento_id
        text observaciones
        timestamp without time zone created_at
    }

    ANALISIS_ORGANIZACIONES_CLASIFICACION {
        integer id PK NOT NULL
        integer documento_id
        character varying nombre
        character varying tipo_clasificacion
        timestamp without time zone created_at
    }

    ANALISIS_ORGANIZACIONES_GENERAL {
        integer id PK NOT NULL
        integer documento_id
        character varying nombre
        timestamp without time zone created_at
    }

    ANALISIS_PERSONAS_CLASIFICACION {
        integer id PK NOT NULL
        integer documento_id
        character varying nombre
        character varying tipo_clasificacion
        timestamp without time zone created_at
    }

    ANALISIS_PERSONAS_GENERAL {
        integer id PK NOT NULL
        integer documento_id
        character varying nombre
        timestamp without time zone created_at
    }

    ANALISIS_RESUMEN_CONTENIDO {
        integer id PK NOT NULL
        integer documento_id
        text proposito_principal
        text contexto_asunto_central
        jsonb conclusiones_puntos_clave
        jsonb acciones_solicitadas
        timestamp without time zone created_at
    }

    ANALISIS_TIPO_DOCUMENTO {
        integer id PK NOT NULL
        integer documento_id
        character varying tipo_especifico
        text descripcion
        timestamp without time zone created_at
    }

    DOCUMENTOS {
        integer id PK NOT NULL
        character varying archivo NOT NULL
        text ruta
        character varying nuc
        timestamp without time zone procesado
        character varying estado
        character varying cuaderno
        character varying codigo
        character varying despacho
        text entidad_productora
        character varying serie
        character varying subserie
        integer folio_inicial
        integer folio_final
        integer paginas
        numeric tamaño_mb
        numeric costo_estimado
        character varying hash_sha256
        text texto_extraido
        text analisis
        timestamp without time zone created_at
        timestamp without time zone updated_at
    }

    ESTADISTICAS {
        integer id PK NOT NULL
        integer documento_id
        integer normal
        integer ilegible
        integer posiblemente
        integer total_palabras
        numeric porcentaje_inferencias
        timestamp without time zone created_at
    }

    METADATOS {
        integer id PK NOT NULL
        integer documento_id
        character varying nuc
        character varying cuaderno
        character varying codigo
        character varying despacho
        text detalle
        text entidad_productora
        character varying serie
        character varying subserie
        integer folio_inicial
        integer folio_final
        timestamp without time zone fecha_creacion
        text observaciones
        character varying hash_sha256
        character varying firma_digital
        timestamp without time zone timestamp_auth
        character varying equipo_id_auth
        character varying producer
        text anexos
        jsonb authentication_info
        timestamp without time zone created_at
        text soporte
        text idioma
        text descriptores
        text fecha_inicio
        text fecha_fin
        text timestamp_batch
    }

    ORGANIZACIONES {
        integer id PK NOT NULL
        integer documento_id
        character varying nombre NOT NULL
        character varying tipo
        text descripcion
        timestamp without time zone created_at
    }

    PERSONAS {
        integer id PK NOT NULL
        integer documento_id
        character varying nombre NOT NULL
        character varying tipo_persona
        character varying cedula
        character varying alias
        character varying lugar_nacimiento
        date fecha_nacimiento
        text observaciones
        timestamp without time zone created_at
        character varying tipo
        text descripcion
    }

    RAG_ANALYTICS {
        integer id PK NOT NULL
        date fecha
        integer total_consultas
        integer consultas_exitosas
        integer consultas_fallidas
        integer tiempo_promedio_ms
        numeric costo_total_tokens
        real calificacion_promedio
        jsonb temas_frecuentes
        jsonb errores_comunes
        jsonb sugerencias_mejora
        timestamp without time zone updated_at
    }

    RAG_CACHE {
        integer id PK NOT NULL
        character varying pregunta_hash
        text pregunta_normalizada NOT NULL
        text respuesta_cacheada NOT NULL
        jsonb fuentes_cache
        integer veces_utilizada
        real calificacion_promedio
        timestamp without time zone ultima_utilizacion
        timestamp without time zone expires_at
        timestamp without time zone created_at
    }

    RAG_CONSULTAS {
        integer id PK NOT NULL
        uuid sesion_id
        character varying usuario_id
        text pregunta_original NOT NULL
        text pregunta_normalizada
        character varying tipo_consulta
        character varying metodo_resolucion
        jsonb contexto_utilizado
        integer tokens_prompt
        integer tokens_respuesta
        numeric costo_estimado
        integer tiempo_respuesta_ms
        timestamp without time zone timestamp_consulta
        inet ip_cliente
        text user_agent
    }

    RAG_FEEDBACK {
        integer id PK NOT NULL
        integer consulta_id
        integer respuesta_id
        integer calificacion
        text feedback_texto
        jsonb aspectos_evaluados
        text respuesta_esperada
        timestamp without time zone timestamp_feedback
        inet ip_cliente
    }

    RAG_RESPUESTAS {
        integer id PK NOT NULL
        integer consulta_id
        text respuesta_texto NOT NULL
        jsonb fuentes_utilizadas
        real confianza_score
        character varying metodo_generacion
        jsonb datos_estructurados
        jsonb metadatos_llm
        timestamp without time zone created_at
    }

    DOCUMENTOS ||--o{ ANALISIS_CANTIDADES_VALORES : analisis_cantidades_valores_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_CARGOS_ROLES : analisis_cargos_roles_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_DATOS_CONTACTO : analisis_datos_contacto_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_DELITOS : analisis_delitos_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_ESTRUCTURA_DOCUMENTO : analisis_estructura_documento_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_FECHAS : analisis_fechas_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_LUGARES : analisis_lugares_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_NUMEROS_IDENTIFICACION : analisis_numeros_identificacion_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_OBSERVACIONES : analisis_observaciones_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_ORGANIZACIONES_CLASIFICACION : analisis_organizaciones_clasificacion_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_ORGANIZACIONES_GENERAL : analisis_organizaciones_general_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_PERSONAS_CLASIFICACION : analisis_personas_clasificacion_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_PERSONAS_GENERAL : analisis_personas_general_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_RESUMEN_CONTENIDO : analisis_resumen_contenido_documento_id_fkey
    DOCUMENTOS ||--o{ ANALISIS_TIPO_DOCUMENTO : analisis_tipo_documento_documento_id_fkey
    DOCUMENTOS ||--o{ ESTADISTICAS : estadisticas_documento_id_fkey
    DOCUMENTOS ||--o{ METADATOS : metadatos_documento_id_fkey
    DOCUMENTOS ||--o{ ORGANIZACIONES : organizaciones_documento_id_fkey
    DOCUMENTOS ||--o{ PERSONAS : personas_documento_id_fkey
    RAG_CONSULTAS ||--o{ RAG_FEEDBACK : rag_feedback_consulta_id_fkey
    RAG_RESPUESTAS ||--o{ RAG_FEEDBACK : rag_feedback_respuesta_id_fkey
    RAG_CONSULTAS ||--o{ RAG_RESPUESTAS : rag_respuestas_consulta_id_fkey
```

---

## 📋 DETALLES DE TABLAS

### 📄 Tabla: `analisis_cantidades_valores`

**Descripción:** Cantidades numéricas y valores mencionados

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_cantidades_valores_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `tipo` | character varying(100) | ✅ |  |  |  |
| `cantidad` | numeric | ✅ |  |  |  |
| `descripcion` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_cantidades_valores_doc_id`

---

### 📄 Tabla: `analisis_cargos_roles`

**Descripción:** Cargos y roles específicos de personas en el documento

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_cargos_roles_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `cargo` | character varying(200) | ✅ |  |  |  |
| `persona` | character varying(500) | ✅ |  |  |  |
| `entidad` | character varying(500) | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_cargos_roles_doc_id`

---

### 📄 Tabla: `analisis_datos_contacto`

**Descripción:** Información de contacto como teléfonos, direcciones

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_datos_contacto_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `tipo` | character varying(100) | ✅ |  |  |  |
| `valor` | text | ✅ |  |  |  |
| `entidad` | character varying(500) | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_datos_contacto_doc_id`

---

### 📄 Tabla: `analisis_delitos`

**Descripción:** Delitos mencionados con detalles específicos

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_delitos_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `tipo_delito` | character varying(200) | ✅ |  |  |  |
| `fecha_hecho` | date | ✅ |  |  |  |
| `lugar_hecho` | character varying(500) | ✅ |  |  |  |
| `descripcion` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_delitos_doc_id`
- `idx_analisis_delitos_fecha`
- `idx_analisis_delitos_lugar`
- `idx_analisis_delitos_tipo`

---

### 📄 Tabla: `analisis_estructura_documento`

**Descripción:** Estructura formal del documento (secciones, elementos)

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_estructura_documento_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `secciones_principales` | jsonb | ✅ |  |  |  |
| `elementos_formales` | jsonb | ✅ |  |  |  |
| `elementos_visuales` | jsonb | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_estructura_documento_doc_id`

---

### 📄 Tabla: `analisis_fechas`

**Descripción:** Fechas relevantes con su tipo y descripción

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_fechas_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `fecha` | date | ✅ |  |  |  |
| `tipo` | character varying(100) | ✅ |  |  |  |
| `descripcion` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_fechas_doc_id`
- `idx_analisis_fechas_doc_tipo`
- `idx_analisis_fechas_fecha`
- `idx_analisis_fechas_tipo`

---

### 📄 Tabla: `analisis_lugares`

**Descripción:** Lugares geográficos mencionados con detalles de ubicación

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_lugares_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nombre` | character varying(500) | ✅ |  |  |  |
| `tipo` | character varying(100) | ✅ |  |  |  |
| `direccion` | text | ✅ |  |  |  |
| `municipio` | character varying(100) | ✅ |  |  |  |
| `departamento` | character varying(100) | ✅ |  |  |  |
| `pais` | character varying(100) | ✅ |  | 'Colombia'::character varying |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_lugares_departamento`
- `idx_analisis_lugares_doc_id`
- `idx_analisis_lugares_municipio`
- `idx_analisis_lugares_nombre`

---

### 📄 Tabla: `analisis_numeros_identificacion`

**Descripción:** Números de identificación como oficios, radicados, cédulas

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_numeros_identificacion_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `tipo` | character varying(100) | ✅ |  |  |  |
| `numero` | character varying(100) | ✅ |  |  |  |
| `descripcion` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_numeros_identificacion_doc_id`

---

### 📄 Tabla: `analisis_observaciones`

**Descripción:** Observaciones adicionales del análisis

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_observaciones_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `observaciones` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_observaciones_doc_id`

---

### 📄 Tabla: `analisis_organizaciones_clasificacion`

**Descripción:** Clasificación de organizaciones: legítimas, ilegales, otras

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_organizaciones_clasificacion_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nombre` | character varying(500) | ✅ |  |  |  |
| `tipo_clasificacion` | character varying(50) | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_organizaciones_clasificacion_doc_id`
- `idx_analisis_organizaciones_clasificacion_nombre`
- `idx_analisis_organizaciones_clasificacion_tipo`
- `idx_analisis_organizaciones_doc_tipo`

---

### 📄 Tabla: `analisis_organizaciones_general`

**Descripción:** Lista general de todas las organizaciones mencionadas

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_organizaciones_general_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nombre` | character varying(500) | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_organizaciones_general_doc_id`
- `idx_analisis_organizaciones_general_nombre`

---

### 📄 Tabla: `analisis_personas_clasificacion`

**Descripción:** Clasificación de personas por categorías: víctimas, defensa, etc.

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_personas_clasificacion_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nombre` | character varying(500) | ✅ |  |  |  |
| `tipo_clasificacion` | character varying(50) | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_personas_clasificacion_doc_id`
- `idx_analisis_personas_clasificacion_nombre`
- `idx_analisis_personas_clasificacion_tipo`
- `idx_analisis_personas_doc_tipo`

---

### 📄 Tabla: `analisis_personas_general`

**Descripción:** Lista general de todas las personas mencionadas en el documento

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_personas_general_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nombre` | character varying(500) | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_personas_general_doc_id`
- `idx_analisis_personas_general_nombre`

---

### 📄 Tabla: `analisis_resumen_contenido`

**Descripción:** Resumen ejecutivo del contenido del documento

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_resumen_contenido_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `proposito_principal` | text | ✅ |  |  |  |
| `contexto_asunto_central` | text | ✅ |  |  |  |
| `conclusiones_puntos_clave` | jsonb | ✅ |  |  |  |
| `acciones_solicitadas` | jsonb | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_resumen_contenido_doc_id`

---

### 📄 Tabla: `analisis_tipo_documento`

**Descripción:** Almacena el tipo específico y descripción de cada documento

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('analisis_tipo_documento_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `tipo_especifico` | character varying(255) | ✅ |  |  |  |
| `descripcion` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_analisis_tipo_documento_doc_id`

---

### 📄 Tabla: `documentos`

**Descripción:** Tabla principal de documentos jurídicos

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('documentos_id_seq'::regclass) |  |
| `archivo` | character varying(255) | ❌ |  |  |  |
| `ruta` | text | ✅ |  |  |  |
| `nuc` | character varying(50) | ✅ |  |  |  |
| `procesado` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |
| `estado` | character varying(50) | ✅ |  |  |  |
| `cuaderno` | character varying(50) | ✅ |  |  |  |
| `codigo` | character varying(20) | ✅ |  |  |  |
| `despacho` | character varying(20) | ✅ |  |  |  |
| `entidad_productora` | text | ✅ |  |  |  |
| `serie` | character varying(20) | ✅ |  |  |  |
| `subserie` | character varying(20) | ✅ |  |  |  |
| `folio_inicial` | integer | ✅ |  |  |  |
| `folio_final` | integer | ✅ |  |  |  |
| `paginas` | integer | ✅ |  |  |  |
| `tamaño_mb` | numeric | ✅ |  |  |  |
| `costo_estimado` | numeric | ✅ |  |  |  |
| `hash_sha256` | character varying(64) | ✅ |  |  |  |
| `texto_extraido` | text | ✅ |  |  |  |
| `analisis` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |
| `updated_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Índices:

- `documentos_archivo_key`
- `documentos_hash_sha256_key`
- `idx_documentos_archivo`
- `idx_documentos_nuc`

---

### 📄 Tabla: `estadisticas`

**Descripción:** Estadísticas de procesamiento y calidad del documento.

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('estadisticas_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `normal` | integer | ✅ |  | 0 |  |
| `ilegible` | integer | ✅ |  | 0 |  |
| `posiblemente` | integer | ✅ |  | 0 |  |
| `total_palabras` | integer | ✅ |  | 0 |  |
| `porcentaje_inferencias` | numeric | ✅ |  | 0.0 |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_estadisticas_documento_id`

---

### 📄 Tabla: `metadatos`

**Descripción:** Metadatos estructurados de cada documento, extraídos y enriquecidos por IA.

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('metadatos_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nuc` | character varying(50) | ✅ |  |  |  |
| `cuaderno` | character varying(50) | ✅ |  |  |  |
| `codigo` | character varying(20) | ✅ |  |  |  |
| `despacho` | character varying(50) | ✅ |  |  |  |
| `detalle` | text | ✅ |  |  |  |
| `entidad_productora` | text | ✅ |  |  |  |
| `serie` | character varying(20) | ✅ |  |  |  |
| `subserie` | character varying(20) | ✅ |  |  |  |
| `folio_inicial` | integer | ✅ |  |  |  |
| `folio_final` | integer | ✅ |  |  |  |
| `fecha_creacion` | timestamp without time zone | ✅ |  |  |  |
| `observaciones` | text | ✅ |  |  |  |
| `hash_sha256` | character varying(64) | ✅ |  |  |  |
| `firma_digital` | character varying(255) | ✅ |  |  |  |
| `timestamp_auth` | timestamp without time zone | ✅ |  |  |  |
| `equipo_id_auth` | character varying(255) | ✅ |  |  |  |
| `producer` | character varying(255) | ✅ |  |  |  |
| `anexos` | text | ✅ |  |  |  |
| `authentication_info` | jsonb | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |
| `soporte` | text | ✅ |  |  |  |
| `idioma` | text | ✅ |  |  |  |
| `descriptores` | text | ✅ |  |  |  |
| `fecha_inicio` | text | ✅ |  |  |  |
| `fecha_fin` | text | ✅ |  |  |  |
| `timestamp_batch` | text | ✅ |  |  |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_metadatos_documento_id`

---

### 📄 Tabla: `organizaciones`

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('organizaciones_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nombre` | character varying(255) | ❌ |  |  |  |
| `tipo` | character varying(50) | ✅ |  |  |  |
| `descripcion` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:


---

### 📄 Tabla: `personas`

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('personas_id_seq'::regclass) |  |
| `documento_id` | integer | ✅ |  |  |  |
| `nombre` | character varying(255) | ❌ |  |  |  |
| `tipo_persona` | character varying(50) | ✅ |  |  |  |
| `cedula` | character varying(20) | ✅ |  |  |  |
| `alias` | character varying(255) | ✅ |  |  |  |
| `lugar_nacimiento` | character varying(255) | ✅ |  |  |  |
| `fecha_nacimiento` | date | ✅ |  |  |  |
| `observaciones` | text | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | CURRENT_TIMESTAMP |  |
| `tipo` | character varying(50) | ✅ |  |  |  |
| `descripcion` | text | ✅ |  |  |  |

#### Foreign Keys:

- `documento_id` → `documentos.id`

#### Índices:

- `idx_personas_nombre`
- `idx_personas_tipo`

---

### 📄 Tabla: `rag_analytics`

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('rag_analytics_id_seq'::regclass) |  |
| `fecha` | date | ✅ |  | CURRENT_DATE |  |
| `total_consultas` | integer | ✅ |  | 0 |  |
| `consultas_exitosas` | integer | ✅ |  | 0 |  |
| `consultas_fallidas` | integer | ✅ |  | 0 |  |
| `tiempo_promedio_ms` | integer | ✅ |  | 0 |  |
| `costo_total_tokens` | numeric | ✅ |  | 0 |  |
| `calificacion_promedio` | real | ✅ |  | 0 |  |
| `temas_frecuentes` | jsonb | ✅ |  |  |  |
| `errores_comunes` | jsonb | ✅ |  |  |  |
| `sugerencias_mejora` | jsonb | ✅ |  |  |  |
| `updated_at` | timestamp without time zone | ✅ |  | now() |  |

#### Índices:


---

### 📄 Tabla: `rag_cache`

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('rag_cache_id_seq'::regclass) |  |
| `pregunta_hash` | character varying(64) | ✅ |  |  |  |
| `pregunta_normalizada` | text | ❌ |  |  |  |
| `respuesta_cacheada` | text | ❌ |  |  |  |
| `fuentes_cache` | jsonb | ✅ |  |  |  |
| `veces_utilizada` | integer | ✅ |  | 1 |  |
| `calificacion_promedio` | real | ✅ |  |  |  |
| `ultima_utilizacion` | timestamp without time zone | ✅ |  | now() |  |
| `expires_at` | timestamp without time zone | ✅ |  | (now() + '30 days'::interval) |  |
| `created_at` | timestamp without time zone | ✅ |  | now() |  |

#### Índices:

- `idx_rag_cache_hash`
- `idx_rag_cache_utilizacion`
- `rag_cache_pregunta_hash_key`

---

### 📄 Tabla: `rag_consultas`

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('rag_consultas_id_seq'::regclass) |  |
| `sesion_id` | uuid | ✅ |  | gen_random_uuid() |  |
| `usuario_id` | character varying(100) | ✅ |  |  |  |
| `pregunta_original` | text | ❌ |  |  |  |
| `pregunta_normalizada` | text | ✅ |  |  |  |
| `tipo_consulta` | character varying(50) | ✅ |  |  |  |
| `metodo_resolucion` | character varying(50) | ✅ |  |  |  |
| `contexto_utilizado` | jsonb | ✅ |  |  |  |
| `tokens_prompt` | integer | ✅ |  |  |  |
| `tokens_respuesta` | integer | ✅ |  |  |  |
| `costo_estimado` | numeric | ✅ |  |  |  |
| `tiempo_respuesta_ms` | integer | ✅ |  |  |  |
| `timestamp_consulta` | timestamp without time zone | ✅ |  | now() |  |
| `ip_cliente` | inet | ✅ |  |  |  |
| `user_agent` | text | ✅ |  |  |  |

#### Índices:

- `idx_rag_consultas_contexto`
- `idx_rag_consultas_timestamp`
- `idx_rag_consultas_tipo`
- `idx_rag_consultas_usuario`

---

### 📄 Tabla: `rag_feedback`

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('rag_feedback_id_seq'::regclass) |  |
| `consulta_id` | integer | ✅ |  |  |  |
| `respuesta_id` | integer | ✅ |  |  |  |
| `calificacion` | integer | ✅ |  |  |  |
| `feedback_texto` | text | ✅ |  |  |  |
| `aspectos_evaluados` | jsonb | ✅ |  |  |  |
| `respuesta_esperada` | text | ✅ |  |  |  |
| `timestamp_feedback` | timestamp without time zone | ✅ |  | now() |  |
| `ip_cliente` | inet | ✅ |  |  |  |

#### Foreign Keys:

- `consulta_id` → `rag_consultas.id`
- `respuesta_id` → `rag_respuestas.id`

#### Índices:

- `idx_rag_feedback_aspectos`
- `idx_rag_feedback_calificacion`

---

### 📄 Tabla: `rag_respuestas`

#### Columnas:

| Columna | Tipo | Nulo | PK | Default | Comentario |
|---------|------|------|----|---------|-----------|
| `id` | integer | ❌ | ✅ | nextval('rag_respuestas_id_seq'::regclass) |  |
| `consulta_id` | integer | ✅ |  |  |  |
| `respuesta_texto` | text | ❌ |  |  |  |
| `fuentes_utilizadas` | jsonb | ✅ |  |  |  |
| `confianza_score` | real | ✅ |  |  |  |
| `metodo_generacion` | character varying(50) | ✅ |  |  |  |
| `datos_estructurados` | jsonb | ✅ |  |  |  |
| `metadatos_llm` | jsonb | ✅ |  |  |  |
| `created_at` | timestamp without time zone | ✅ |  | now() |  |

#### Foreign Keys:

- `consulta_id` → `rag_consultas.id`

#### Índices:

- `idx_rag_respuestas_fuentes`

---

