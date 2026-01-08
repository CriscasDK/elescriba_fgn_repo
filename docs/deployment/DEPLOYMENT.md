# Guía de Despliegue - Sistema Escriba Legal

Esta guía proporciona instrucciones completas para desplegar el Sistema de Análisis Inteligente de Documentos Judiciales en diferentes entornos.

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración Rápida con Docker](#configuración-rápida-con-docker)
3. [Despliegue en Producción](#despliegue-en-producción)
4. [Despliegue en Azure Container Apps](#despliegue-en-azure-container-apps)
5. [Variables de Entorno](#variables-de-entorno)
6. [Troubleshooting](#troubleshooting)

---

## Requisitos Previos

### Servicios Cloud Requeridos

El sistema requiere los siguientes servicios de Azure:

1. **Azure OpenAI** (Obligatorio)
   - Modelo: GPT-4o-mini o superior
   - Endpoint y API Key necesarios

2. **Azure AI Search** (Obligatorio para RAG)
   - Índice configurado con embeddings
   - Admin Key para indexación

3. **PostgreSQL 15+**
   - Opción 1: Docker local (desarrollo)
   - Opción 2: Azure Database for PostgreSQL (producción)

### Software Necesario

- **Docker** 20.10+ y **Docker Compose** 2.0+
- **Git** para clonar el repositorio
- **Python 3.12+** (solo para desarrollo local sin Docker)

---

## Configuración Rápida con Docker

### 1. Clonar el Repositorio

```bash
git clone https://github.com/rodrigobazurto/sistema-documentos-judiciales.git
cd sistema-documentos-judiciales
```

### 2. Configurar Variables de Entorno

Copiar el archivo de ejemplo y editarlo con tus credenciales:

```bash
cp .env.example .env
nano .env  # o usar tu editor preferido
```

**Variables críticas a configurar:**

```bash
# Azure OpenAI (OBLIGATORIO)
AZURE_OPENAI_ENDPOINT=https://tu-servicio.openai.azure.com/
AZURE_OPENAI_API_KEY=tu_api_key_aqui
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Azure AI Search (OBLIGATORIO para RAG)
AZURE_SEARCH_ENDPOINT=https://tu-search.search.windows.net
AZURE_SEARCH_KEY=tu_search_key_aqui
AZURE_SEARCH_INDEX=documentos-juridicos

# PostgreSQL (Configuración por defecto funciona con Docker)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=documentos_juridicos
POSTGRES_USER=docs_user
POSTGRES_PASSWORD=CAMBIAR_EN_PRODUCCION
```

### 3. Iniciar Servicios

**Opción A: Desarrollo completo (con base de datos local)**

```bash
docker-compose up -d
```

Esto inicia:
- PostgreSQL en puerto 5432
- pgAdmin en puerto 8080
- Aplicación Dash en puerto 8050

**Opción B: Solo aplicación (usando BD externa)**

```bash
docker-compose up -d app
```

### 4. Acceder al Sistema

- **Aplicación principal**: http://localhost:8050
- **pgAdmin** (administración BD): http://localhost:8080
  - Usuario: admin@example.com
  - Contraseña: admin_2025

### 5. Verificar Estado

```bash
# Ver logs de la aplicación
docker-compose logs -f app

# Ver estado de contenedores
docker-compose ps

# Verificar base de datos
docker-compose exec postgres psql -U docs_user -d documentos_juridicos -c "SELECT COUNT(*) FROM documentos;"
```

---

## Despliegue en Producción

### Arquitectura Recomendada

```
Internet
    ↓
[Load Balancer / CDN]
    ↓
[Container Apps / ECS / EKS]
    ├── App Container (Dash) - Puerto 8050
    └── Backend Container (FastAPI) - Puerto 8010
        ↓
[Azure Database for PostgreSQL]
        ↓
[Azure AI Search + OpenAI]
```

### Preparación

1. **Construir imágenes Docker**

```bash
# Imagen principal (Dash)
docker build -t escriba-legal:latest .

# Verificar imagen
docker images | grep escriba-legal
```

2. **Tagear para registry**

```bash
# Para Azure Container Registry
docker tag escriba-legal:latest turegistry.azurecr.io/escriba-legal:v1.0

# Para Docker Hub
docker tag escriba-legal:latest tuusuario/escriba-legal:v1.0
```

3. **Push al registry**

```bash
# Login a Azure Container Registry
az acr login --name turegistry

# Push
docker push turegistry.azurecr.io/escriba-legal:v1.0
```

### Variables de Entorno en Producción

**Nunca incluir secretos en la imagen Docker**. Usar uno de estos métodos:

#### Opción 1: Azure Key Vault (Recomendado)

```python
# El código ya soporta Azure Key Vault
# Configurar estas variables:
AZURE_KEY_VAULT_NAME=tu-keyvault
AZURE_TENANT_ID=tu-tenant-id
AZURE_CLIENT_ID=tu-client-id
AZURE_CLIENT_SECRET=tu-client-secret
```

#### Opción 2: Variables de entorno del contenedor

En Azure Container Apps, configurar en "Environment variables":

```yaml
environmentVariables:
  - name: AZURE_OPENAI_ENDPOINT
    value: https://...
  - name: AZURE_OPENAI_API_KEY
    secretRef: openai-key
  - name: POSTGRES_HOST
    value: tu-servidor.postgres.database.azure.com
```

### Seguridad en Producción

1. **Cambiar contraseñas por defecto**
   ```bash
   # PostgreSQL
   POSTGRES_PASSWORD=GenerarPasswordSeguro123!

   # pgAdmin (si se usa)
   PGADMIN_DEFAULT_PASSWORD=OtroPasswordSeguro456!
   ```

2. **Configurar SSL para PostgreSQL**
   ```bash
   POSTGRES_SSLMODE=require
   ```

3. **Restringir CORS** (en app_dash.py si es necesario)

4. **Habilitar autenticación** si el sistema es público

---

## Despliegue en Azure Container Apps

### 1. Crear recursos de Azure

```bash
# Variables
RESOURCE_GROUP="rg-escriba-legal"
LOCATION="eastus"
ACR_NAME="escribalegalacr"
APP_NAME="escriba-legal-app"

# Crear resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Crear Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic

# Crear Container Apps environment
az containerapp env create \
  --name escriba-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

### 2. Build y push de imagen

```bash
# Build en Azure (recomendado)
az acr build \
  --registry $ACR_NAME \
  --image escriba-legal:v1.0 \
  --file Dockerfile .
```

### 3. Crear Container App

```bash
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment escriba-env \
  --image $ACR_NAME.azurecr.io/escriba-legal:v1.0 \
  --target-port 8050 \
  --ingress external \
  --cpu 2 \
  --memory 4Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=secretref:openai-endpoint \
    POSTGRES_HOST=tu-servidor.postgres.database.azure.com
```

### 4. Configurar secretos

```bash
az containerapp secret set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    openai-endpoint=https://tu-endpoint.openai.azure.com/ \
    openai-key=tu_api_key_aqui \
    postgres-password=tu_password_aqui
```

### 5. Obtener URL pública

```bash
az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn
```

---

## Variables de Entorno

### Referencia Completa

| Variable | Descripción | Requerido | Por Defecto |
|----------|-------------|-----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Endpoint de Azure OpenAI | ✅ Sí | - |
| `AZURE_OPENAI_API_KEY` | API Key de Azure OpenAI | ✅ Sí | - |
| `AZURE_OPENAI_API_VERSION` | Versión API | No | `2024-02-15-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Nombre del modelo | ✅ Sí | `gpt-4o-mini` |
| `AZURE_SEARCH_ENDPOINT` | Endpoint Azure Search | ✅ Sí (RAG) | - |
| `AZURE_SEARCH_KEY` | Admin Key Azure Search | ✅ Sí (RAG) | - |
| `AZURE_SEARCH_INDEX` | Nombre del índice | No | `documentos-juridicos` |
| `POSTGRES_HOST` | Host PostgreSQL | ✅ Sí | `localhost` |
| `POSTGRES_PORT` | Puerto PostgreSQL | No | `5432` |
| `POSTGRES_DB` | Nombre de base de datos | ✅ Sí | `documentos_juridicos` |
| `POSTGRES_USER` | Usuario PostgreSQL | ✅ Sí | `docs_user` |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL | ✅ Sí | - |
| `DASH_HOST` | Host para Dash | No | `0.0.0.0` |
| `DASH_PORT` | Puerto para Dash | No | `8050` |
| `DASH_DEBUG` | Modo debug | No | `False` |

### Validación de Variables

El sistema incluye validación automática. Si faltan variables críticas, verás errores como:

```
❌ Error: AZURE_OPENAI_ENDPOINT no está configurado
❌ Error: POSTGRES_HOST no está configurado
```

---

## Troubleshooting

### Problema: Contenedor no inicia

**Síntoma**: `docker-compose ps` muestra status "Exited"

**Solución**:
```bash
# Ver logs detallados
docker-compose logs app

# Verificar variables de entorno
docker-compose config

# Recrear contenedor
docker-compose up -d --force-recreate app
```

### Problema: Error de conexión a PostgreSQL

**Síntoma**: `psycopg2.OperationalError: could not connect to server`

**Soluciones**:

1. Verificar que PostgreSQL está corriendo:
   ```bash
   docker-compose ps postgres
   ```

2. Verificar credenciales en `.env`:
   ```bash
   grep POSTGRES .env
   ```

3. Probar conexión manualmente:
   ```bash
   docker-compose exec postgres psql -U docs_user -d documentos_juridicos
   ```

### Problema: Error con Azure OpenAI

**Síntoma**: `401 Unauthorized` o `403 Forbidden`

**Soluciones**:

1. Verificar API Key:
   ```bash
   curl -H "api-key: TU_API_KEY" \
     "https://tu-endpoint.openai.azure.com/openai/deployments?api-version=2024-02-15-preview"
   ```

2. Verificar que el deployment existe en Azure Portal

3. Verificar quotas y límites de rate

### Problema: Datos no cargan en la interfaz

**Síntoma**: Interfaz vacía o sin resultados

**Soluciones**:

1. Verificar que hay datos en la BD:
   ```bash
   docker-compose exec postgres psql -U docs_user -d documentos_juridicos \
     -c "SELECT COUNT(*) FROM documentos;"
   ```

2. Si la BD está vacía, necesitas cargar los datos:
   ```bash
   # Ver documentación de ETL en README_ARQUITECTURA.md
   python extractor_final.py
   ```

### Problema: Puerto ya en uso

**Síntoma**: `Error: bind: address already in use`

**Soluciones**:

1. Cambiar puerto en docker-compose.yml:
   ```yaml
   ports:
     - "8051:8050"  # Usar puerto 8051 en lugar de 8050
   ```

2. O detener el servicio que usa el puerto:
   ```bash
   lsof -i :8050
   kill -9 PID
   ```

### Problema: Performance lenta

**Soluciones**:

1. Aumentar recursos de Docker:
   ```bash
   # En docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

2. Verificar índices de BD:
   ```sql
   SELECT schemaname, tablename, indexname
   FROM pg_indexes
   WHERE schemaname = 'public';
   ```

3. Revisar logs de queries lentas:
   ```bash
   docker-compose logs app | grep "took"
   ```

---

## Monitoreo

### Logs

```bash
# Logs en tiempo real
docker-compose logs -f app

# Últimas 100 líneas
docker-compose logs --tail=100 app

# Logs de todos los servicios
docker-compose logs -f
```

### Healthcheck

El Dockerfile incluye healthcheck automático:

```bash
# Verificar salud del contenedor
docker inspect --format='{{.State.Health.Status}}' <container_id>

# Ver historial de healthchecks
docker inspect --format='{{json .State.Health}}' <container_id> | jq
```

### Métricas

Para Azure Container Apps:

```bash
# Ver métricas CPU/Memoria
az monitor metrics list \
  --resource /subscriptions/.../containerApps/$APP_NAME \
  --metric CpuUsage,MemoryUsage
```

---

## Backups

### Base de Datos

```bash
# Backup manual
docker-compose exec postgres pg_dump -U docs_user documentos_juridicos | gzip > backup_$(date +%Y%m%d).sql.gz

# Restaurar backup
gunzip -c backup_20260107.sql.gz | docker-compose exec -T postgres psql -U docs_user documentos_juridicos
```

### Backups Automatizados (Producción)

Para Azure Database for PostgreSQL, configurar backups automáticos en el portal.

---

## Actualizaciones

### Actualizar a nueva versión

```bash
# Pull última versión
git pull origin main

# Rebuild imagen
docker-compose build

# Recrear contenedores
docker-compose up -d --force-recreate
```

---

## Soporte

Para problemas adicionales:

1. Revisar documentación en `/docs`
2. Crear issue en GitHub: https://github.com/rodrigobazurto/sistema-documentos-judiciales/issues
3. Contactar: rodrigo@example.com

---

**Última actualización**: Enero 2026
**Versión del sistema**: v4.0
