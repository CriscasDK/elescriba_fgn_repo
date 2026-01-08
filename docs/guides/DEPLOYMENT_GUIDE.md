# 🚀 Guía de Despliegue - Sistema RAG

## 🎯 Resumen Ejecutivo

**Tiempo estimado de despliegue:** 30-45 minutos  
**Prerrequisitos:** Docker, Python 3.12+, PostgreSQL, Azure OpenAI account  
**Complejidad:** Intermedia  
**Entornos soportados:** Desarrollo, Staging, Producción  

## 📋 Checklist Pre-Despliegue

### ✅ Requisitos del Sistema

| Componente | Versión Mínima | Verificación |
|------------|----------------|--------------|
| **Python** | 3.12+ | `python --version` |
| **Docker** | 20.0+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker compose version` |
| **PostgreSQL Client** | 15+ | `psql --version` |
| **Git** | 2.0+ | `git --version` |

### ✅ Recursos del Servidor

| Recurso | Mínimo | Recomendado | Producción |
|---------|--------|-------------|------------|
| **RAM** | 4 GB | 8 GB | 16 GB |
| **CPU** | 2 cores | 4 cores | 8 cores |
| **Disco** | 20 GB | 50 GB | 200 GB |
| **Red** | 10 Mbps | 100 Mbps | 1 Gbps |

### ✅ Cuentas y Servicios

- [ ] **Azure OpenAI Account** con GPT-4o-mini habilitado
- [ ] **API Key** de Azure OpenAI con permisos suficientes
- [ ] **Endpoint** de Azure OpenAI configurado
- [ ] **Acceso a puertos** 5432 (PostgreSQL) y 8080 (pgAdmin)
- [ ] **Permisos de escritura** en directorio de instalación

## 🛠️ Procedimiento de Instalación

### 📦 Fase 1: Preparación del Entorno

```bash
# 1. Clonar repositorio (si aplica)
git clone <repository_url>
cd documentos_judiciales

# 2. Verificar requisitos del sistema
python --version  # Debe ser 3.12+
docker --version
docker compose version

# 3. Crear entorno virtual Python
python -m venv venv_docs
source venv_docs/bin/activate  # Linux/Mac
# venv_docs\Scripts\activate   # Windows

# 4. Actualizar pip
pip install --upgrade pip
```

### ⚙️ Fase 2: Configuración de Variables

```bash
# 1. Crear archivo de configuración
cp .env.example .env  # Si existe plantilla
# O crear nuevo .env

cat > .env << 'EOF'
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://tu-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=tu_api_key_aqui
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=documentos_juridicos_gpt4
POSTGRES_USER=docs_user
POSTGRES_PASSWORD=docs_password_2024

# Sistema Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_WORKERS=8
BATCH_SIZE=50
EOF

# 2. Cargar variables
source .env
```

### 🐳 Fase 3: Despliegue de Servicios

```bash
# 1. Crear estructura de directorios
mkdir -p data/postgres data/pgadmin logs json_files scripts

# 2. Configurar permisos para pgAdmin
chmod 777 data/pgadmin  # Solo para desarrollo local

# 3. Iniciar servicios con Docker Compose
docker compose up -d

# 4. Verificar que servicios estén ejecutándose
docker compose ps

# Output esperado:
# NAME                    COMMAND                  SERVICE             STATUS
# docs_postgres          "docker-entrypoint.s…"   postgres            Up
# docs_pgadmin           "/entrypoint.sh"         pgadmin             Up
```

### 📊 Fase 4: Inicialización de Base de Datos

```bash
# 1. Esperar que PostgreSQL esté listo
echo "Esperando PostgreSQL..."
sleep 15

# 2. Verificar conexión
PGPASSWORD=docs_password_2024 psql -h localhost -U docs_user -d documentos_juridicos_gpt4 -c "SELECT version();"

# 3. Crear schema si no existe (solo para DB nueva)
PGPASSWORD=docs_password_2024 psql -h localhost -U docs_user -d documentos_juridicos_gpt4 -f scripts/schema.sql

# 4. Aplicar funciones RAG
PGPASSWORD=docs_password_2024 psql -h localhost -U docs_user -d documentos_juridicos_gpt4 -f rag_trazabilidad_sistema.sql

# 5. Aplicar correcciones de funciones
PGPASSWORD=docs_password_2024 psql -h localhost -U docs_user -d documentos_juridicos_gpt4 -f fix_all_rag_functions.sql
```

### 🐍 Fase 5: Instalación de Dependencias Python

```bash
# 1. Instalar dependencias principales
pip install psycopg2-binary==2.9.9
pip install openai>=1.51.2
pip install httpx>=0.24.0
pip install python-dotenv>=1.0.0
pip install cachetools>=5.0.0

# 2. O instalar desde requirements.txt si existe
pip install -r requirements.txt

# 3. Verificar instalación
python -c "
import psycopg2
import openai
import httpx
print('✅ Todas las dependencias instaladas correctamente')
"
```

### ✅ Fase 6: Verificación del Despliegue

```bash
# 1. Ejecutar verificación completa del sistema
python verificar_sistema_rag.py

# Output esperado:
# ✅ Importaciones de librerías exitosas
# ✅ Variables de entorno configuradas correctamente
# ✅ Conexión a PostgreSQL establecida
# ✅ Azure OpenAI configurado correctamente
# ✅ Funciones RAG disponibles
# ✅ Documentos en la base de datos: X
# 🎉 SISTEMA RAG COMPLETAMENTE OPERATIVO

# 2. Test básico de Azure OpenAI
python test_azure_fixed.py

# 3. Test del sistema RAG completo
python test_rag_final.py
```

## 🎯 Configuraciones por Entorno

### 🔧 Desarrollo

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: documentos_juridicos_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5433:5432"  # Puerto diferente para no conflictos
    volumes:
      - ./data/postgres_dev:/var/lib/postgresql/data
    
  pgadmin:
    image: dpage/pgadmin4:latest
    environment:
      PGADMIN_DEFAULT_EMAIL: dev@example.com
      PGADMIN_DEFAULT_PASSWORD: dev_password
    ports:
      - "8081:80"
```

```bash
# Variables para desarrollo
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=documentos_juridicos_dev
export POSTGRES_USER=dev_user
export POSTGRES_PASSWORD=dev_password
```

### 🚀 Staging

```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: documentos_juridicos_staging
      POSTGRES_USER: staging_user
      POSTGRES_PASSWORD: ${STAGING_DB_PASSWORD}  # Variable segura
    ports:
      - "5432:5432"
    volumes:
      - postgres_staging_data:/var/lib/postgresql/data
    restart: unless-stopped
    
volumes:
  postgres_staging_data:
```

### 🏭 Producción

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - /opt/postgres_data:/var/lib/postgresql/data  # Volumen persistente
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    # Configuraciones de seguridad
    security_opt:
      - no-new-privileges:true
    user: postgres
```

**Configuración adicional para producción:**

```bash
# /etc/systemd/system/documentos-rag.service
[Unit]
Description=Sistema RAG Documentos Judiciales
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/documentos_judiciales
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

## 🔐 Configuración de Seguridad

### 🛡️ Hardening de PostgreSQL

```sql
-- Crear usuario específico para aplicación
CREATE USER rag_app WITH PASSWORD 'secure_password_2025';

-- Otorgar permisos mínimos necesarios
GRANT CONNECT ON DATABASE documentos_juridicos_gpt4 TO rag_app;
GRANT USAGE ON SCHEMA public TO rag_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO rag_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO rag_app;

-- Configurar pg_hba.conf para conexiones seguras
# host    documentos_juridicos_gpt4    rag_app    127.0.0.1/32    md5
# host    documentos_juridicos_gpt4    rag_app    ::1/128         md5
```

### 🔒 Variables de Entorno Seguras

```bash
# Usar archivos .env con permisos restrictivos
chmod 600 .env

# Para producción, usar secretos del sistema
# Ejemplo con Docker Swarm secrets
echo "tu_api_key_real" | docker secret create azure_openai_key -
echo "password_seguro" | docker secret create postgres_password -
```

### 🚧 Configuración de Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22          # SSH
sudo ufw allow 5432/tcp    # PostgreSQL (solo desde IPs específicas)
sudo ufw allow 8080/tcp    # pgAdmin (solo desarrollo)
sudo ufw enable

# Restringir PostgreSQL a IPs específicas
sudo ufw allow from 192.168.1.0/24 to any port 5432
```

## 📊 Monitoreo Post-Despliegue

### 🔍 Scripts de Verificación Automática

```bash
# health_check.sh
#!/bin/bash

echo "🏥 Verificación de salud del sistema"

# 1. Verificar servicios Docker
if docker compose ps | grep -q "Up"; then
    echo "✅ Servicios Docker ejecutándose"
else
    echo "❌ Problemas con servicios Docker"
    exit 1
fi

# 2. Verificar PostgreSQL
if PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ PostgreSQL accesible"
else
    echo "❌ PostgreSQL no responde"
    exit 1
fi

# 3. Verificar funciones RAG
FUNC_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -t -c "
SELECT COUNT(*) FROM information_schema.routines 
WHERE routine_schema = 'public' AND routine_name LIKE 'rag_%'")

if [ "$FUNC_COUNT" -ge 3 ]; then
    echo "✅ Funciones RAG disponibles ($FUNC_COUNT)"
else
    echo "❌ Funciones RAG faltantes"
    exit 1
fi

# 4. Verificar datos
DOC_COUNT=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT COUNT(*) FROM documentos")

if [ "$DOC_COUNT" -gt 1000 ]; then
    echo "✅ Base de datos poblada ($DOC_COUNT documentos)"
else
    echo "⚠️ Pocos documentos en base de datos ($DOC_COUNT)"
fi

echo "🎉 Verificación completada"
```

### 📈 Configuración de Logs

```python
# logging_config.py
import logging
import sys
from datetime import datetime

def setup_logging():
    """Configurar logging para producción"""
    
    # Formato de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(
        f'logs/rag_system_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)
    
    # Configurar logger principal
    logger = logging.getLogger('rag_system')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

## 🔄 Procedimientos de Actualización

### 📦 Actualización de Código

```bash
# update_system.sh
#!/bin/bash

echo "🔄 Iniciando actualización del sistema"

# 1. Backup de seguridad
pg_dump -h localhost -U $POSTGRES_USER -d $POSTGRES_DB | gzip > "backup_pre_update_$(date +%Y%m%d_%H%M%S).sql.gz"

# 2. Parar servicios
docker compose down

# 3. Actualizar código
git pull origin main

# 4. Actualizar dependencias
source venv_docs/bin/activate
pip install -r requirements.txt --upgrade

# 5. Aplicar migraciones SQL si existen
if [ -f "migrations/update_$(date +%Y%m%d).sql" ]; then
    echo "Aplicando migraciones..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB -f "migrations/update_$(date +%Y%m%d).sql"
fi

# 6. Reiniciar servicios
docker compose up -d

# 7. Verificar sistema
sleep 10
python verificar_sistema_rag.py

echo "✅ Actualización completada"
```

### 🗃️ Backup Automático

```bash
# backup_daily.sh
#!/bin/bash

BACKUP_DIR="/opt/backups/rag_system"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Backup de base de datos
pg_dump -h localhost -U $POSTGRES_USER -d $POSTGRES_DB | gzip > "$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql.gz"

# Backup de configuración
tar -czf "$BACKUP_DIR/config_backup_$(date +%Y%m%d_%H%M%S).tar.gz" .env docker-compose.yml scripts/

# Limpiar backups antiguos
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "✅ Backup completado: $BACKUP_DIR"

# Configurar cron para backup automático
# 0 2 * * * /opt/documentos_judiciales/backup_daily.sh
```

## 🚨 Rollback y Recuperación

### ⏪ Procedimiento de Rollback

```bash
# rollback.sh
#!/bin/bash

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Uso: ./rollback.sh <archivo_backup.sql.gz>"
    exit 1
fi

echo "⚠️ Iniciando rollback con $BACKUP_FILE"
read -p "¿Continuar? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 1. Parar servicios
    docker compose down
    
    # 2. Backup del estado actual
    pg_dump -h localhost -U $POSTGRES_USER -d $POSTGRES_DB | gzip > "backup_before_rollback_$(date +%Y%m%d_%H%M%S).sql.gz"
    
    # 3. Restaurar backup
    dropdb -h localhost -U $POSTGRES_USER $POSTGRES_DB
    createdb -h localhost -U $POSTGRES_USER $POSTGRES_DB
    zcat $BACKUP_FILE | psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB
    
    # 4. Reiniciar servicios
    docker compose up -d
    
    # 5. Verificar sistema
    sleep 15
    python verificar_sistema_rag.py
    
    echo "✅ Rollback completado"
else
    echo "❌ Rollback cancelado"
fi
```

---

## 📞 Soporte y Contacto

**📋 Documentación relacionada:**
- `TECHNICAL_GUIDE.md` - Documentación técnica completa
- `TROUBLESHOOTING.md` - Solución de problemas
- `README.md` - Información general del proyecto

**🔧 Comandos útiles:**
```bash
# Verificación rápida
python verificar_sistema_rag.py

# Logs en tiempo real
docker compose logs -f postgres

# Estado de servicios
docker compose ps

# Reinicio completo
docker compose restart
```

**📅 Creado:** Julio 25, 2025  
**🔄 Última actualización:** Julio 25, 2025  
**👨‍💻 Responsable:** Sistema RAG Team
