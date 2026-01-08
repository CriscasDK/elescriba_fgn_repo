# CONFIGURACIÓN Y DEPLOYMENT

## 🚀 **Guía de Instalación Completa**

### Requisitos del Sistema

```bash
# Sistema Operativo
Ubuntu 20.04+ / CentOS 8+ / Windows 10+ WSL2

# Software Base
Docker 20.10+
Docker Compose 2.0+
Python 3.12+
Git

# Recursos Mínimos
RAM: 16GB (recomendado 32GB)
CPU: 8 cores (para 8 workers ETL)
Almacenamiento: 1TB SSD
Red: 1Gbps para Azure OpenAI
```

## 📋 **Proceso de Instalación**

### 1. **Clonar y Configurar Proyecto**

```bash
# Clonar repositorio
git clone <repository-url>
cd documentos_judiciales

# Crear ambiente virtual
python3.12 -m venv venv_docs
source venv_docs/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. **Configurar Variables de Entorno**

```bash
# .env.gpt41
AZURE_OPENAI_ENDPOINT="https://your-endpoint.cognitiveservices.azure.com/"
AZURE_OPENAI_API_KEY="your-api-key-here"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini"

# Base de datos
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="documentos_juridicos_gpt4"
DB_USER="docs_user"
DB_PASSWORD="secure_password_here"

# pgAdmin
PGADMIN_EMAIL="admin@documentos.com"
PGADMIN_PASSWORD="admin_password_here"

# ETL Configuration
MAX_WORKERS=8
BATCH_SIZE=100
LOG_LEVEL="INFO"
CHUNK_SIZE=1000
OVERLAP_SIZE=200

# Azure Cognitive Search (para RAG)
SEARCH_ENDPOINT="https://your-search.search.windows.net"
SEARCH_API_KEY="your-search-key"
SEARCH_INDEX_NAME="documentos-juridicos"
```

### 3. **Levantar Servicios Docker**

```bash
# Iniciar servicios
docker-compose up -d

# Verificar servicios
docker ps

# Expected output:
# docs_postgres  - PostgreSQL 15
# docs_pgadmin   - pgAdmin4
# ollama         - Ollama (opcional)
```

### 4. **Configurar Base de Datos**

```bash
# Ejecutar schema inicial
docker exec -it docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -f /scripts/schema.sql

# Verificar tablas
docker exec -it docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "\dt"

# Crear extensiones necesarias
docker exec -it docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;"
docker exec -it docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

## 🔧 **Configuraciones Avanzadas**

### **requirements.txt**
```txt
# Core dependencies
psycopg2-binary==2.9.9
openai==1.51.0
python-dotenv==1.0.0

# Data processing
pandas==2.1.4
numpy==1.24.3
asyncio==3.4.3

# RAG components
semantic-kernel==1.0.3
azure-search-documents==11.4.0
azure-cognitive-search==1.1.0

# Text processing
nltk==3.8.1
spacy==3.7.2
fuzzywuzzy==0.18.0

# Monitoring
logging==0.4.9.6
prometheus-client==0.19.0

# Development
pytest==7.4.3
black==23.11.0
flake8==6.1.0
```

### **docker-compose.yml Completo**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: docs_postgres
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=es_ES.UTF-8"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./scripts:/scripts
    ports:
      - "5432:5432"
    networks:
      - docs_network
    restart: unless-stopped
    command: >
      postgres -c shared_preload_libraries=pg_stat_statements
               -c pg_stat_statements.track=all
               -c max_connections=200
               -c shared_buffers=256MB
               -c effective_cache_size=1GB
    
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: docs_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    volumes:
      - ./data/pgadmin:/var/lib/pgadmin
    ports:
      - "8080:80"
    depends_on:
      - postgres
    networks:
      - docs_network
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    container_name: docs_redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    networks:
      - docs_network
    restart: unless-stopped
    command: redis-server --appendonly yes
    
  ollama:
    image: ollama/ollama
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    networks:
      - docs_network
    restart: unless-stopped
    environment:
      - OLLAMA_KEEP_ALIVE=24h
      
networks:
  docs_network:
    driver: bridge
    
volumes:
  postgres_data:
  pgadmin_data:
  redis_data:
  ollama_data:
```

## 🔒 **Configuración de Seguridad**

### **Firewall Rules**
```bash
# UFW Configuration
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 8080/tcp  # pgAdmin
sudo ufw deny 11434/tcp  # Ollama (internal only)
sudo ufw enable
```

### **SSL/TLS Configuration**
```nginx
# nginx.conf para producción
server {
    listen 443 ssl;
    server_name documentos-juridicos.domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **Database Security**
```sql
-- Crear usuarios con permisos limitados
CREATE ROLE docs_reader WITH LOGIN PASSWORD 'reader_password';
GRANT CONNECT ON DATABASE documentos_juridicos_gpt4 TO docs_reader;
GRANT USAGE ON SCHEMA public TO docs_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO docs_reader;

CREATE ROLE docs_analyst WITH LOGIN PASSWORD 'analyst_password';
GRANT docs_reader TO docs_analyst;
GRANT INSERT, UPDATE ON personas, organizaciones TO docs_analyst;

-- Row Level Security (RLS)
ALTER TABLE documentos ENABLE ROW LEVEL SECURITY;
CREATE POLICY documentos_access_policy ON documentos
FOR ALL TO docs_reader
USING (estado = 'publico' OR current_user = 'docs_user');
```

## 📊 **Monitoreo y Logs**

### **Logging Configuration**
```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """
    Configuración avanzada de logging
    """
    
    # Crear directorio de logs
    os.makedirs('logs', exist_ok=True)
    
    # Configuración del formateador
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Handler para archivo general
    file_handler = RotatingFileHandler(
        'logs/application.log',
        maxBytes=100*1024*1024,  # 100MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler para errores
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=50*1024*1024,   # 50MB
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Handler para ETL específico
    etl_handler = RotatingFileHandler(
        'logs/etl_processing.log',
        maxBytes=200*1024*1024,  # 200MB
        backupCount=15
    )
    etl_handler.setFormatter(formatter)
    etl_handler.setLevel(logging.DEBUG)
    
    # Configurar logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    # Logger específico para ETL
    etl_logger = logging.getLogger('etl')
    etl_logger.addHandler(etl_handler)
    
    return logger
```

### **Health Check Scripts**
```bash
#!/bin/bash
# health_check.sh

echo "=== HEALTH CHECK DOCUMENTOS JUDICIALES ==="
echo "Fecha: $(date)"
echo

# Check Docker containers
echo "1. Estado de Contenedores:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo

# Check database connectivity
echo "2. Conectividad Base de Datos:"
if docker exec docs_postgres pg_isready -U docs_user; then
    echo "✅ PostgreSQL: OK"
else
    echo "❌ PostgreSQL: FAILED"
fi

# Check disk space
echo "3. Espacio en Disco:"
df -h | grep -E "(/$|/var/lib/docker)"

# Check ETL process
echo "4. Proceso ETL:"
if pgrep -f "extractor_gpt_mini.py" > /dev/null; then
    echo "✅ ETL: Running"
    echo "Workers activos: $(pgrep -f "extractor_gpt_mini.py" | wc -l)"
else
    echo "❌ ETL: Not running"
fi

# Check log files
echo "5. Logs Recientes (últimas 5 líneas):"
if [ -f "logs/application.log" ]; then
    tail -5 logs/application.log
else
    echo "No se encontraron logs"
fi

echo
echo "=== FIN HEALTH CHECK ==="
```

## 🔄 **Scripts de Deployment**

### **deploy.sh**
```bash
#!/bin/bash
# deploy.sh - Script de deployment completo

set -e

echo "🚀 Iniciando deployment de Documentos Judiciales..."

# 1. Backup de datos existentes
echo "📦 Creando backup..."
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
docker exec docs_postgres pg_dump -U docs_user documentos_juridicos_gpt4 > backups/$(date +%Y%m%d_%H%M%S)/backup.sql

# 2. Pull latest changes
echo "📥 Actualizando código..."
git pull origin main

# 3. Update dependencies
echo "📚 Actualizando dependencias..."
source venv_docs/bin/activate
pip install -r requirements.txt --upgrade

# 4. Database migrations
echo "🗄️ Aplicando migraciones..."
if [ -f "migrations/latest.sql" ]; then
    docker exec -i docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 < migrations/latest.sql
fi

# 5. Restart services
echo "🔄 Reiniciando servicios..."
docker-compose down
docker-compose up -d

# 6. Wait for services
echo "⏳ Esperando servicios..."
sleep 30

# 7. Health check
echo "🔍 Verificando salud del sistema..."
./scripts/health_check.sh

# 8. Restart ETL if needed
echo "🤖 Reiniciando ETL..."
pkill -f "extractor_gpt_mini.py" || true
sleep 5
source venv_docs/bin/activate
nohup python extractor_gpt_mini.py > logs/etl_$(date +%Y%m%d_%H%M%S).log 2>&1 &

echo "✅ Deployment completado exitosamente!"
```

### **backup.sh**
```bash
#!/bin/bash
# backup.sh - Backup automático

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "📦 Iniciando backup completo..."

# Database backup
echo "🗄️ Backup de base de datos..."
docker exec docs_postgres pg_dump -U docs_user -F c documentos_juridicos_gpt4 > $BACKUP_DIR/database.dump

# Configuration backup
echo "⚙️ Backup de configuración..."
cp .env.gpt41 $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# Logs backup
echo "📋 Backup de logs..."
tar -czf $BACKUP_DIR/logs.tar.gz logs/

# JSON files sample (últimos 100)
echo "📄 Backup de archivos JSON (muestra)..."
find json_files/ -name "*.json" -type f | head -100 | tar -czf $BACKUP_DIR/json_sample.tar.gz -T -

# Create manifest
echo "📄 Creando manifiesto..."
cat > $BACKUP_DIR/manifest.txt << EOF
Backup Created: $(date)
Database Size: $(docker exec docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "SELECT pg_size_pretty(pg_database_size('documentos_juridicos_gpt4'));" -t)
Total Documents: $(docker exec docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "SELECT COUNT(*) FROM documentos;" -t)
Total Personas: $(docker exec docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "SELECT COUNT(*) FROM personas;" -t)
Total Organizaciones: $(docker exec docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "SELECT COUNT(*) FROM organizaciones;" -t)
EOF

echo "✅ Backup completado en: $BACKUP_DIR"

# Cleanup old backups (keep last 10)
find backups/ -maxdepth 1 -type d | sort | head -n -10 | xargs rm -rf

echo "🧹 Limpieza de backups antiguos completada"
```

## 📈 **Métricas de Performance**

### **Prometheus Configuration**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'documentos-juridicos'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### **Performance Monitoring**
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Métricas ETL
documents_processed = Counter('documents_processed_total', 'Total documents processed')
processing_time = Histogram('document_processing_seconds', 'Time spent processing documents')
openai_requests = Counter('openai_requests_total', 'Total OpenAI API requests')
openai_costs = Gauge('openai_costs_usd', 'Current OpenAI costs in USD')
database_connections = Gauge('database_connections_active', 'Active database connections')

class MetricsCollector:
    def __init__(self):
        self.start_time = time.time()
        
    def record_document_processed(self):
        documents_processed.inc()
        
    def record_processing_time(self, seconds):
        processing_time.observe(seconds)
        
    def record_openai_request(self, cost_usd):
        openai_requests.inc()
        openai_costs.set(openai_costs._value._value + cost_usd)
        
    def start_metrics_server(self, port=8000):
        start_http_server(port)
```
