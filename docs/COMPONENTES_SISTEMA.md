# COMPONENTES DEL SISTEMA

## 🗂️ **Estructura de Archivos**

```
documentos_judiciales/
├── 📁 docs/                          # Documentación técnica
│   ├── ARQUITECTURA_GENERAL.md
│   ├── DIAGRAMA_ERD.md
│   ├── FLUJO_ETL.md
│   └── COMPONENTES_SISTEMA.md
├── 📁 scripts/                       # Scripts SQL
│   ├── schema.sql                    # Esquema principal
│   ├── consultas_macrocaso_up.sql    # Análisis macrocaso
│   ├── consultas_busqueda_avanzada.sql
│   ├── consultas_busqueda_palabras.sql
│   ├── consultas_busqueda_frecuentes.sql
│   ├── consultas_busqueda_lenguaje_natural.sql
│   └── consultas_redes_temporal_geografico.sql
├── 📁 json_files/                    # Archivos fuente (11,446)
│   ├── 2015005204_*.json
│   └── ...
├── 📁 logs/                          # Logs del sistema
│   ├── extraction_20250724.log
│   └── errors_20250724.log
├── 📁 venv_docs/                     # Ambiente virtual Python
├── 📁 data/                          # Datos persistentes Docker
│   ├── postgres/
│   └── pgadmin/
├── 🐍 extractor_gpt_mini.py          # ETL principal (831 líneas)
├── 🐍 extractor_*.py                 # Versiones anteriores
├── 🐍 procesar_masivo.py             # Procesamiento batch
├── 🐍 debug_ollama.py                # Debug utilities
├── ⚙️ docker-compose.yml             # Servicios Docker
├── ⚙️ .env.gpt41                     # Configuración Azure
├── 📄 setup_docs.sh                  # Script de instalación
└── 📄 start.sh                       # Script de inicio
```

## 🔧 **Componentes Principales**

### 1. **extractor_gpt_mini.py** (ETL Core)

```python
class DocumentProcessor:
    """
    Procesador principal de documentos judiciales
    """
    
    # Configuración
    MAX_WORKERS = 8
    AZURE_ENDPOINT = "https://fgnfoundrylabo3874907599.cognitiveservices.azure.com/"
    MODEL = "gpt-4o-mini"
    DATABASE = "documentos_juridicos_gpt4"
    
    # Métodos principales
    def process_single_document()      # Procesa un JSON individual
    def extract_entities_gpt4_mini()   # Extrae entidades con IA
    def insert_entities_batch()        # Inserta entidades en lote
    def insert_documento_estructurado() # Inserta documento base
    def preparar_contenido_para_ia()   # Prepara texto para GPT
```

#### Características Técnicas:
- **Concurrencia**: 8 workers con `ThreadPoolExecutor`
- **Rate Limiting**: Control de requests a Azure OpenAI
- **Error Handling**: Reintentos automáticos y logging
- **Memory Management**: Liberación de conexiones DB
- **Cost Tracking**: Seguimiento de costos de IA

### 2. **Schema SQL** (15 Tablas)

```sql
-- Tabla principal
CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    archivo VARCHAR(255) NOT NULL UNIQUE,
    -- 20 campos adicionales
);

-- Entidades extraídas
CREATE TABLE personas (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),           -- víctimas, defensa, victimarios
    descripcion TEXT,
    -- campos adicionales
);

-- 13 tablas adicionales para análisis completo
```

### 3. **Módulos de Consulta SQL**

#### A. **Búsqueda Lexical** (consultas_busqueda_palabras.sql)
```sql
-- Búsqueda por similitud fonética
SELECT * FROM personas 
WHERE SOUNDEX(nombre) = SOUNDEX('búsqueda');

-- Búsqueda con errores de tipeo
SELECT * FROM personas 
WHERE LEVENSHTEIN(nombre, 'búsqueda') <= 2;
```

#### B. **Análisis de Redes** (consultas_redes_temporal_geografico.sql)
```sql
-- Red de conexiones entre personas
WITH conexiones AS (
    SELECT p1.nombre as persona1, p2.nombre as persona2, 
           COUNT(*) as documentos_compartidos
    FROM personas p1, personas p2
    WHERE p1.documento_id = p2.documento_id
    GROUP BY p1.nombre, p2.nombre
)
SELECT * FROM conexiones WHERE documentos_compartidos > 1;
```

#### C. **Análisis Temporal** (consultas_macrocaso_up.sql)
```sql
-- Evolución temporal del caso
SELECT DATE_TRUNC('month', f.fecha) as mes,
       COUNT(DISTINCT f.documento_id) as documentos,
       COUNT(DISTINCT p.id) as personas_involucradas
FROM analisis_fechas f
JOIN personas p ON f.documento_id = p.documento_id
GROUP BY mes ORDER BY mes;
```

## 🐳 **Infraestructura Docker**

### docker-compose.yml
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: docs_postgres
    environment:
      POSTGRES_DB: documentos_juridicos_gpt4
      POSTGRES_USER: docs_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: docs_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@documentos.com
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    ports:
      - "8080:80"
    depends_on:
      - postgres
```

### Configuración de Red
- **PostgreSQL**: Puerto 5432 (local + Docker)
- **pgAdmin**: Puerto 8080 (web interface)
- **Ollama**: Puerto 11434 (AI local opcional)

## ⚙️ **Variables de Entorno**

### .env.gpt41
```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT="https://fgnfoundrylabo3874907599.cognitiveservices.azure.com/"
AZURE_OPENAI_API_KEY="your-api-key"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"

# Base de datos
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="documentos_juridicos_gpt4"
DB_USER="docs_user"
DB_PASSWORD="your-password"

# Configuración ETL
MAX_WORKERS=8
BATCH_SIZE=100
LOG_LEVEL="INFO"
```

## 📊 **Métricas y Monitoreo**

### Logging Structure
```python
import logging

# Configuración de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/extraction_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# Métricas capturadas
- Tiempo de procesamiento por documento
- Costos de Azure OpenAI por request
- Errores y excepciones detalladas
- Progreso de workers individuales
- Estadísticas de entidades extraídas
```

### Dashboard de Métricas (Propuesto)
- Documentos procesados/hora
- Costo acumulado de IA
- Distribución de tipos de entidades
- Errores por categoría
- Tiempo promedio por documento
