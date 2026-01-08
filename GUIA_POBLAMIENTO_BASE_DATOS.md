# Guía Completa de Poblamiento de Base de Datos - Sistema Escriba Legal

**Documento para Tercerización - Proceso ETL Completo**

**Fecha:** Enero 2026
**Versión:** 1.0
**Autor:** Equipo Fiscalía - Sistema Escriba Legal

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Pre-requisitos](#pre-requisitos)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Proceso Paso a Paso](#proceso-paso-a-paso)
5. [Scripts Disponibles](#scripts-disponibles)
6. [Troubleshooting](#troubleshooting)
7. [Validación de Resultados](#validación-de-resultados)
8. [FAQ](#faq)

---

## 🎯 Resumen Ejecutivo

Este documento describe el **proceso completo de poblamiento de la base de datos** del Sistema Escriba Legal, utilizado para analizar 11,111 documentos judiciales del caso Unión Patriótica.

### ¿Qué hace este proceso?

Toma **archivos JSON** que contienen análisis de documentos judiciales (previamente procesados con GPT-4 Vision) y los carga en una base de datos PostgreSQL estructurada, extrayendo automáticamente:

- Metadatos de documentos (NUC, radicados, despachos)
- Entidades nombradas (personas, organizaciones, lugares)
- Clasificaciones automáticas (víctimas, responsables, etc.)
- Fechas y eventos relevantes
- Relaciones entre entidades

### Resultados Esperados

```
✅ 11,111 documentos procesados
✅ 12,248 víctimas registradas
✅ ~8,276 personas totales identificadas
✅ ~500 organizaciones clasificadas
✅ ~1,000 lugares georeferenciados
✅ Tasa de éxito: 99.9%
✅ Tiempo estimado: 18-24 horas (con 8 workers)
```

---

## ✅ Pre-requisitos

### 1. Software Necesario

```bash
# Python 3.12+
python --version  # Debe ser >= 3.12

# PostgreSQL 15+
psql --version    # Debe ser >= 15

# Ambiente virtual configurado
source venv_docs/bin/activate
```

### 2. Servicios Cloud Requeridos

#### Azure OpenAI (OBLIGATORIO)
- **Modelo necesario:** GPT-4o-mini (gpt-4o-mini)
- **Endpoint:** https://tu-servicio.openai.azure.com/
- **API Key:** Tu clave de API de Azure OpenAI
- **Uso:** Extracción de entidades de los análisis

#### PostgreSQL Database (OBLIGATORIO)
- **Host:** localhost o servidor remoto
- **Puerto:** 5432 (por defecto)
- **Base de datos:** `documentos_juridicos` (o `documentos_juridicos_gpt4`)
- **Usuario/Contraseña:** Credenciales con permisos de escritura

### 3. Datos de Entrada

```bash
# Carpeta con JSONs procesados
ls json_files/*.json | wc -l
# Debe mostrar: 11111 (o la cantidad que vayas a procesar)

# Estructura de cada JSON:
{
  "archivo": "20150050002000000025001201411090001.pdf",
  "metadatos": {
    "nuc": "23001600000120140112",
    "despacho": "UNIDAD NACIONAL FISCALIA 15 DDHH BOGOTA",
    "cuaderno": "CUADERNO ORIGINAL No. 1",
    "codigo": "OFICIO",
    "serie": "COMUNICACIONES OFICIALES RECIBIDAS",
    ...
  },
  "analisis": "### **ANÁLISIS DEL DOCUMENTO** ...",
  "hash_sha256": "abc123...",
  ...
}
```

### 4. Variables de Entorno

Crear/editar archivo `.env` en la raíz del proyecto:

```bash
# ===================================
# CONFIGURACIÓN BASE DE DATOS
# ===================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=documentos_juridicos
POSTGRES_USER=docs_user
POSTGRES_PASSWORD=tu_password_seguro_aqui

# ===================================
# AZURE OPENAI (OBLIGATORIO)
# ===================================
AZURE_OPENAI_ENDPOINT=https://tu-servicio.openai.azure.com/
AZURE_OPENAI_API_KEY=tu_api_key_aqui
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# ===================================
# CONFIGURACIÓN ETL
# ===================================
BATCH_SIZE=50              # Documentos por lote
MAX_WORKERS=8              # Workers paralelos
RETRY_ATTEMPTS=3           # Reintentos en caso de error
LOG_LEVEL=INFO            # Nivel de logging
```

**⚠️ IMPORTANTE:** Reemplazar los valores de ejemplo con tus credenciales reales.

---

## 🏗️ Arquitectura del Sistema

### Flujo de Datos Completo

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  FASE 1: PROCESAMIENTO OCR (YA COMPLETADO)             │
│                                                         │
│  PDFs (11,111) → GPT-4 Vision → JSONs (11,111)         │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  FASE 2: ETL - CARGA A BASE DE DATOS (ESTA GUÍA)       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. CARGA DE JSON                               │   │
│  │     - Leer archivo JSON                         │   │
│  │     - Validar estructura                        │   │
│  │     - Extraer metadatos                         │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  2. INSERCIÓN DOCUMENTO BASE                    │   │
│  │     - INSERT INTO documentos (...)              │   │
│  │     - Obtener documento_id                      │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  3. EXTRACCIÓN DE ENTIDADES CON IA              │   │
│  │     - Tomar campo 'analisis' del JSON           │   │
│  │     - Enviar a GPT-4 Mini (Azure OpenAI)        │   │
│  │     - Recibir entidades estructuradas en JSON   │   │
│  │     - Validar schema de respuesta               │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  4. INSERCIÓN DE ENTIDADES                      │   │
│  │     - INSERT INTO personas (...)                │   │
│  │     - INSERT INTO organizaciones (...)          │   │
│  │     - INSERT INTO lugares (...)                 │   │
│  │     - INSERT INTO cargos_roles (...)            │   │
│  │     - INSERT INTO fechas_eventos (...)          │   │
│  │     - INSERT INTO metadatos (...)               │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │  5. COMMIT TRANSACCIÓN                          │   │
│  │     - Validar datos insertados                  │   │
│  │     - COMMIT si todo OK                         │   │
│  │     - ROLLBACK si hay error                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  RESULTADO: BASE DE DATOS POSTGRESQL POBLADA            │
│                                                         │
│  📊 Tablas:                                             │
│     - documentos (11,111 registros)                    │
│     - metadatos (11,111 registros)                     │
│     - personas (12,248+ registros)                     │
│     - organizaciones (500+ registros)                  │
│     - lugares (1,000+ registros)                       │
│     - cargos_roles (2,000+ registros)                  │
│     - fechas_eventos (5,000+ registros)                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Componentes Principales

#### 1. **Worker Pool (8 workers paralelos)**
- Procesamiento concurrente de múltiples documentos
- Distribución automática de carga
- Manejo independiente de errores por worker

#### 2. **Extractor de IA (GPT-4 Mini)**
- Modelo: `gpt-4o-mini` (Azure OpenAI)
- Temperatura: 0.1 (consistencia)
- Max tokens: 2000
- Timeout: 30 segundos

#### 3. **Sistema de Base de Datos**
- PostgreSQL 15+ con Apache AGE
- Transacciones ACID
- Índices optimizados para búsquedas

---

## 📝 Proceso Paso a Paso

### PASO 1: Preparar el Entorno

```bash
# 1.1 Clonar el repositorio
git clone https://github.com/fgn-subtics/Escriba-back.git -b develop
cd Escriba-back

# 1.2 Crear ambiente virtual
python3.12 -m venv venv_docs

# 1.3 Activar ambiente virtual
source venv_docs/bin/activate

# 1.4 Instalar dependencias
pip install -r requirements.txt

# Dependencias principales:
# - psycopg2-binary==2.9.9
# - openai==1.51.2
# - python-dotenv==1.0.0
# - tqdm==4.66.1 (para progress bars)
```

### PASO 2: Configurar Variables de Entorno

```bash
# 2.1 Copiar archivo de ejemplo
cp .env.example .env

# 2.2 Editar con tus credenciales
nano .env  # o usar tu editor favorito

# 2.3 Verificar configuración
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('DB:', os.getenv('POSTGRES_DB')); print('OpenAI:', os.getenv('AZURE_OPENAI_ENDPOINT'))"
```

### PASO 3: Verificar Conexiones

```bash
# 3.1 Verificar conexión a PostgreSQL
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"

# 3.2 Verificar tablas existen
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"

# Debe mostrar:
# - documentos
# - metadatos
# - personas
# - organizaciones
# - lugares
# - cargos_roles
# - fechas_eventos

# 3.3 Verificar conexión a Azure OpenAI
python -c "
from openai import AzureOpenAI
import os
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)
print('✅ Conexión Azure OpenAI exitosa')
"
```

### PASO 4: Preparar Datos de Entrada

```bash
# 4.1 Verificar carpeta de JSONs
ls -lh json_files/ | head -10

# 4.2 Contar archivos
TOTAL_FILES=$(ls json_files/*.json | wc -l)
echo "Total de archivos JSON: $TOTAL_FILES"

# 4.3 Verificar estructura de un JSON
python -c "
import json
with open('json_files/$(ls json_files/ | head -1)', 'r') as f:
    data = json.load(f)
    print('Campos disponibles:', list(data.keys()))
    print('Tiene analisis:', 'analisis' in data)
    print('Tiene metadatos:', 'metadatos' in data)
"
```

### PASO 5: Ejecutar Procesamiento (Prueba Pequeña)

```bash
# 5.1 PRUEBA CON 10 DOCUMENTOS PRIMERO
python procesar_masivo.py json_files/ 10

# Salida esperada:
# 🚀 PROCESADOR MASIVO DE DOCUMENTOS JURÍDICOS
# 📁 Directorio: json_files/
# 🔢 Límite: 10 archivos
# 📂 Encontrados 10 archivos JSON para procesar
# 🤖 Usando modelo: gpt-4o-mini
#
# 🚀 INICIANDO PROCESAMIENTO MASIVO...
# ======================================================================
#
# 📄 [   1/  10] 20150050002000000025001201411090001.json
#    ✅ Completado
# ...

# 5.2 Verificar resultados de prueba
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT
    (SELECT COUNT(*) FROM documentos) as docs,
    (SELECT COUNT(*) FROM personas) as personas,
    (SELECT COUNT(*) FROM organizaciones) as orgs;
"

# Debe mostrar ~10 documentos y varias personas/organizaciones
```

### PASO 6: Ejecutar Procesamiento Completo

```bash
# 6.1 Crear sesión tmux (recomendado para procesos largos)
tmux new-session -s etl_escriba

# 6.2 Activar ambiente virtual dentro de tmux
source venv_docs/bin/activate

# 6.3 Ejecutar procesamiento completo
python procesar_masivo.py json_files/

# 6.4 Detach de tmux (dejar corriendo en background)
# Presionar: Ctrl+B, luego D

# 6.5 Re-attach a tmux para ver progreso
tmux attach-session -t etl_escriba

# 6.6 Monitorear logs en tiempo real (otra terminal)
tail -f logs/etl_process.log
```

### PASO 7: Monitoreo Durante el Proceso

```bash
# 7.1 Ver progreso en tiempo real
watch -n 60 "psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -t -c '
SELECT
    (SELECT COUNT(*) FROM documentos) as docs_procesados,
    (SELECT COUNT(*) FROM personas) as personas_extraidas,
    (SELECT COUNT(*) FROM organizaciones) as orgs_extraidas;
'"

# 7.2 Monitorear uso de CPU y memoria
htop  # o top

# 7.3 Verificar procesos Python corriendo
ps aux | grep python | grep procesar_masivo

# 7.4 Verificar conexiones a PostgreSQL
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'documentos_juridicos';
"
```

---

## 🔧 Scripts Disponibles

### 1. `procesar_masivo.py` (Principal)

**Descripción:** Script principal para procesamiento masivo con workers paralelos.

**Uso:**
```bash
# Procesar todos los archivos
python procesar_masivo.py json_files/

# Procesar solo 100 archivos (testing)
python procesar_masivo.py json_files/ 100

# Procesar con logs detallados
python procesar_masivo.py json_files/ --verbose
```

**Características:**
- 8 workers paralelos (configurable)
- Progress bar con tqdm
- Logging detallado
- Estadísticas en tiempo real
- Manejo de errores robusto
- Reintentos automáticos

**Ubicación:** `/procesar_masivo.py`

---

### 2. `extractor_definitivo.py` (Alternativo)

**Descripción:** Extractor más moderno con mejor manejo de errores y logging.

**Uso:**
```bash
python src/core/extractor_definitivo.py --input json_files/ --workers 8
```

**Características:**
- Logging estructurado
- Métricas detalladas
- Validación de schema JSON
- Detección de duplicados
- Cache de consultas

**Ubicación:** `/src/core/extractor_definitivo.py`

---

### 3. Scripts de Utilidad

#### Verificar Estado de BD

```bash
# Script: scripts/verify_database.sh
#!/bin/bash
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB << EOF
SELECT
    'Documentos' as tabla, COUNT(*) as registros
FROM documentos
UNION ALL
SELECT 'Personas', COUNT(*) FROM personas
UNION ALL
SELECT 'Organizaciones', COUNT(*) FROM organizaciones
UNION ALL
SELECT 'Lugares', COUNT(*) FROM lugares
UNION ALL
SELECT 'Metadatos', COUNT(*) FROM metadatos;
EOF
```

#### Limpiar Base de Datos (CUIDADO)

```bash
# Script: scripts/clean_database.sh
#!/bin/bash
echo "⚠️  ADVERTENCIA: Esto eliminará TODOS los datos"
read -p "¿Estás seguro? (escribe 'SI' para confirmar): " confirm

if [ "$confirm" = "SI" ]; then
    psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB << EOF
    TRUNCATE TABLE documentos CASCADE;
    TRUNCATE TABLE metadatos CASCADE;
    TRUNCATE TABLE personas CASCADE;
    TRUNCATE TABLE organizaciones CASCADE;
    TRUNCATE TABLE lugares CASCADE;
    TRUNCATE TABLE cargos_roles CASCADE;
    TRUNCATE TABLE fechas_eventos CASCADE;
    EOF
    echo "✅ Base de datos limpiada"
else
    echo "❌ Operación cancelada"
fi
```

---

## 🐛 Troubleshooting

### Problema 1: Error de Conexión a PostgreSQL

**Síntoma:**
```
psycopg2.OperationalError: could not connect to server
```

**Soluciones:**

```bash
# 1. Verificar que PostgreSQL está corriendo
systemctl status postgresql
# o
docker ps | grep postgres

# 2. Verificar credenciales en .env
cat .env | grep POSTGRES

# 3. Probar conexión manual
psql -h localhost -U docs_user -d documentos_juridicos

# 4. Verificar firewall (si es servidor remoto)
telnet $POSTGRES_HOST 5432
```

---

### Problema 2: Error con Azure OpenAI

**Síntoma:**
```
openai.error.AuthenticationError: Incorrect API key provided
```

**Soluciones:**

```bash
# 1. Verificar API Key
echo $AZURE_OPENAI_API_KEY

# 2. Verificar endpoint
curl -H "api-key: $AZURE_OPENAI_API_KEY" \
  "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2024-02-15-preview"

# 3. Verificar que el deployment existe
# En Azure Portal: Azure OpenAI > tu recurso > Model deployments

# 4. Verificar quotas y límites
# En Azure Portal: verificar que no has alcanzado el límite de tokens
```

---

### Problema 3: Proceso Muy Lento

**Síntoma:**
Procesamiento a menos de 5 documentos/minuto

**Soluciones:**

```bash
# 1. Verificar latencia de red a Azure
ping api.openai.com

# 2. Aumentar workers (si tienes CPU disponible)
# En procesar_masivo.py, cambiar:
MAX_WORKERS = 16  # en lugar de 8

# 3. Reducir timeout de IA
# En el código, ajustar:
timeout = 15  # en lugar de 30

# 4. Verificar índices de BD
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public';
"

# Debe tener índices en:
# - documentos(archivo)
# - documentos(nuc)
# - personas(documento_id)
# - metadatos(documento_id)
```

---

### Problema 4: Memoria Insuficiente

**Síntoma:**
```
MemoryError: Unable to allocate array
```

**Soluciones:**

```bash
# 1. Reducir número de workers
MAX_WORKERS = 4  # en lugar de 8

# 2. Reducir batch size
BATCH_SIZE = 25  # en lugar de 50

# 3. Procesar en lotes más pequeños
python procesar_masivo.py json_files/ 1000
# Luego repetir con los siguientes 1000

# 4. Aumentar swap (Linux)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### Problema 5: Duplicados en Base de Datos

**Síntoma:**
```
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint
```

**Soluciones:**

```bash
# 1. Verificar si el documento ya existe antes de re-procesar
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT archivo FROM documentos WHERE archivo = '20150050002000000025001201411090001.pdf';
"

# 2. Eliminar duplicados
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
DELETE FROM documentos
WHERE id NOT IN (
    SELECT MIN(id)
    FROM documentos
    GROUP BY archivo
);
"

# 3. El script ya maneja duplicados automáticamente
# Solo procesa si el documento NO existe
```

---

## ✅ Validación de Resultados

### Verificaciones Post-Procesamiento

#### 1. Verificar Totales

```sql
-- Conectar a BD
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB

-- Contar registros por tabla
SELECT
    'documentos' as tabla, COUNT(*) as total FROM documentos
UNION ALL
SELECT 'metadatos', COUNT(*) FROM metadatos
UNION ALL
SELECT 'personas', COUNT(*) FROM personas
UNION ALL
SELECT 'organizaciones', COUNT(*) FROM organizaciones
UNION ALL
SELECT 'lugares', COUNT(*) FROM lugares;

-- Resultado esperado:
--     tabla      | total
-- ---------------+-------
--  documentos    | 11111
--  metadatos     | 11111
--  personas      | 12248
--  organizaciones|   500
--  lugares       |  1000
```

#### 2. Verificar Calidad de Datos

```sql
-- 2.1 Verificar que todos los documentos tienen metadatos
SELECT COUNT(*)
FROM documentos d
LEFT JOIN metadatos m ON d.id = m.documento_id
WHERE m.id IS NULL;
-- Debe ser 0

-- 2.2 Verificar completitud de NUCs
SELECT
    COUNT(*) as total,
    COUNT(nuc) as con_nuc,
    ROUND(COUNT(nuc) * 100.0 / COUNT(*), 2) as porcentaje
FROM metadatos;
-- Debe ser ~99.9%

-- 2.3 Verificar clasificación de víctimas
SELECT COUNT(*)
FROM personas
WHERE tipo = 'victima' OR clasificacion_auto LIKE '%victima%';
-- Debe ser ~12,248

-- 2.4 Verificar integridad referencial
SELECT COUNT(*)
FROM personas p
LEFT JOIN documentos d ON p.documento_id = d.id
WHERE d.id IS NULL;
-- Debe ser 0
```

#### 3. Verificar Rendimiento

```sql
-- 3.1 Verificar índices existen
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename;

-- 3.2 Probar velocidad de consultas
EXPLAIN ANALYZE
SELECT * FROM documentos WHERE archivo = '20150050002000000025001201411090001.pdf';
-- Debe usar índice y ser < 10ms

-- 3.3 Verificar tamaño de base de datos
SELECT
    pg_size_pretty(pg_database_size('documentos_juridicos')) as tamano_bd;
-- Debe ser ~2-3 GB
```

#### 4. Generar Reporte de Calidad

```bash
# Script: scripts/generate_quality_report.sh
#!/bin/bash
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB << EOF > quality_report.txt

-- REPORTE DE CALIDAD DE DATOS
-- Generado: $(date)

\echo '========================================='
\echo 'RESUMEN DE REGISTROS'
\echo '========================================='
SELECT
    'documentos' as tabla, COUNT(*) as total FROM documentos
UNION ALL
SELECT 'metadatos', COUNT(*) FROM metadatos
UNION ALL
SELECT 'personas', COUNT(*) FROM personas
UNION ALL
SELECT 'organizaciones', COUNT(*) FROM organizaciones;

\echo ''
\echo '========================================='
\echo 'COMPLETITUD DE CAMPOS CLAVE'
\echo '========================================='
SELECT
    COUNT(*) as total_docs,
    COUNT(nuc) as docs_con_nuc,
    ROUND(COUNT(nuc) * 100.0 / COUNT(*), 2) as porcentaje_nuc,
    COUNT(fecha_creacion) as docs_con_fecha,
    ROUND(COUNT(fecha_creacion) * 100.0 / COUNT(*), 2) as porcentaje_fecha
FROM metadatos;

\echo ''
\echo '========================================='
\echo 'DISTRIBUCIÓN DE VÍCTIMAS'
\echo '========================================='
SELECT
    COUNT(*) as total_victimas,
    COUNT(DISTINCT documento_id) as documentos_con_victimas
FROM personas
WHERE tipo = 'victima' OR clasificacion_auto LIKE '%victima%';

\echo ''
\echo '========================================='
\echo 'TOP 10 DESPACHOS'
\echo '========================================='
SELECT
    despacho,
    COUNT(*) as cantidad
FROM metadatos
WHERE despacho IS NOT NULL
GROUP BY despacho
ORDER BY cantidad DESC
LIMIT 10;

EOF

cat quality_report.txt
```

---

## ❓ FAQ (Preguntas Frecuentes)

### Q1: ¿Cuánto tiempo tarda el proceso completo?

**R:** Con 8 workers paralelos y buena conexión a Azure OpenAI:
- **Tiempo estimado:** 18-24 horas
- **Velocidad promedio:** 7-10 documentos/minuto
- **Factores que afectan:** Latencia de red, CPU disponible, límites de API

### Q2: ¿Puedo pausar y reanudar el proceso?

**R:** Sí, el proceso es idempotente:
```bash
# Pausar: Ctrl+C
# Reanudar: ejecutar el mismo comando
python procesar_masivo.py json_files/

# El script omite documentos ya procesados automáticamente
```

### Q3: ¿Cuánto cuesta en términos de tokens de OpenAI?

**R:** Estimado por documento:
- **Tokens promedio por documento:** 1,500 tokens
- **Total para 11,111 docs:** ~16.7 millones de tokens
- **Costo aproximado (GPT-4 Mini):** $1.67 USD (a $0.10 por 1M tokens)

### Q4: ¿Qué hago si el proceso falla a mitad?

**R:** El proceso es resiliente:
1. Revisa los logs: `tail -100 logs/etl_process.log`
2. Identifica el error específico
3. Re-ejecuta el script (omitirá documentos ya procesados)
4. Si persiste, procesa el documento problemático individualmente

### Q5: ¿Puedo procesar solo documentos específicos?

**R:** Sí, puedes crear una subcarpeta:
```bash
# Copiar solo los JSONs que necesitas
mkdir json_files_subset
cp json_files/documento1.json json_files_subset/
cp json_files/documento2.json json_files_subset/

# Procesar solo ese subset
python procesar_masivo.py json_files_subset/
```

### Q6: ¿Los datos son seguros durante el procesamiento?

**R:** Sí:
- **Transacciones ACID:** Cada documento es una transacción
- **Rollback automático:** Si falla la inserción, se deshacen cambios
- **Hash SHA256:** Verificación de integridad de documentos
- **Logs completos:** Trazabilidad total del proceso

### Q7: ¿Puedo ejecutar esto en un contenedor Docker?

**R:** Sí, ver `README_DEPLOYMENT.md` para instrucciones de Docker.

### Q8: ¿Qué hago si necesito re-procesar todo desde cero?

**R:**
```bash
# 1. Hacer backup primero
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER documentos_juridicos > backup_$(date +%Y%m%d).sql

# 2. Limpiar tablas
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "
TRUNCATE TABLE documentos CASCADE;
"

# 3. Re-ejecutar ETL
python procesar_masivo.py json_files/
```

---

## 📞 Soporte

### Contacto

Para preguntas técnicas o problemas durante el proceso:

- **Email:** soporte@fiscalia.gov.co
- **GitHub Issues:** https://github.com/fgn-subtics/Escriba-back/issues
- **Documentación adicional:** Ver carpeta `/docs` en el repositorio

### Logs y Debugging

Todos los logs se guardan en:
```
logs/
├── etl_process.log          # Log principal
├── errors.log               # Errores específicos
└── performance_metrics.log  # Métricas de rendimiento
```

---

## 📚 Referencias

### Documentación Relacionada

1. **Prompt de OCR con GPT-4 Vision:**
   - Archivo: `DOCUMENTACION_PROMPT_ANALISIS_GPT4_VISION.md`
   - Describe cómo se generaron los JSONs iniciales

2. **Arquitectura del Sistema:**
   - Archivo: `README_ARQUITECTURA.md`
   - Diagrama completo del sistema

3. **Guía de Despliegue:**
   - Archivo: `README_DEPLOYMENT.md`
   - Instrucciones para producción

4. **Flujo ETL Detallado:**
   - Archivo: `docs/FLUJO_ETL.md`
   - Diagrama Mermaid del flujo completo

### Scripts en el Repositorio

```
/procesar_masivo.py                    # Script principal
/src/core/extractor_definitivo.py     # Extractor alternativo
/scripts/verify_database.sh           # Verificación de BD
/scripts/generate_quality_report.sh   # Reporte de calidad
```

---

## ✅ Checklist de Validación Final

Antes de dar por terminado el proceso, verificar:

- [ ] Todos los 11,111 documentos procesados
- [ ] ~12,248 víctimas registradas en tabla `personas`
- [ ] 99.9% de documentos tienen NUC
- [ ] No hay errores críticos en logs
- [ ] Índices de BD creados correctamente
- [ ] Consultas de prueba funcionan (<100ms)
- [ ] Backup de BD realizado
- [ ] Reporte de calidad generado
- [ ] Documentación actualizada

---

**Fin del Documento**

*Guía creada para el proceso de tercerización del Sistema Escriba Legal*
*Fiscalía General de la Nación - Enero 2026*
