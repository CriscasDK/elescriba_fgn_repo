# 🚀 GUÍA DE DESPLIEGUE: GITHUB → AZURE CONTAINER APPS

## 📋 RESUMEN
Esta guía configura el despliegue automático de tu sistema RAG de documentos judiciales desde GitHub a Azure Container Apps.

## 🏗️ ARQUITECTURA DEL DESPLIEGUE

```
GitHub Repository
       ↓ (push)
GitHub Actions
       ↓ (build)
Docker Image
       ↓ (push)
Azure Container Registry
       ↓ (deploy)
Azure Container Apps
```

## 🔧 CONFIGURACIÓN INICIAL REQUERIDA

### 1. 🔐 Crear Service Principal en Azure
```bash
# Crear service principal para GitHub Actions
az ad sp create-for-rbac \
  --name "github-actions-rag-docs" \
  --role contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID \
  --sdk-auth
```

### 2. 📦 Crear Azure Container Registry
```bash
# Crear resource group
az group create --name rg-documentos-judiciales --location "Brazil South"

# Crear container registry
az acr create \
  --resource-group rg-documentos-judiciales \
  --name ragdocsjudiciales \
  --sku Basic \
  --admin-enabled true

# Obtener credenciales del registry
az acr credential show --name ragdocsjudiciales
```

### 3. 🏃‍♂️ Crear Container Apps Environment
```bash
# Instalar extensión si no está instalada
az extension add --name containerapp --upgrade

# Crear environment
az containerapp env create \
  --name env-documentos-judiciales \
  --resource-group rg-documentos-judiciales \
  --location "Brazil South"
```

### 4. 🔑 Configurar GitHub Secrets
En tu repositorio GitHub, ve a **Settings → Secrets and variables → Actions** y agrega:

| Secret Name | Value | Descripción |
|-------------|-------|-------------|
| `AZURE_CREDENTIALS` | JSON del service principal | Credenciales completas de Azure |
| `REGISTRY_USERNAME` | Username del ACR | Usuario del Container Registry |
| `REGISTRY_PASSWORD` | Password del ACR | Contraseña del Container Registry |

### 5. 🗄️ Configurar Base de Datos PostgreSQL
```bash
# Crear PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group rg-documentos-judiciales \
  --name psql-documentos-judiciales \
  --location "Brazil South" \
  --admin-user docs_admin \
  --admin-password "TuPasswordSeguro123!" \
  --sku-name Standard_B2s \
  --tier Burstable \
  --storage-size 32 \
  --version 14
```

## 🚀 PROCESO DE DESPLIEGUE

### Despliegue Automático
1. **Push a main branch** → Activa GitHub Actions
2. **Build Docker image** → Crea imagen optimizada
3. **Push to ACR** → Sube imagen al registry
4. **Deploy to Container Apps** → Despliega automáticamente
5. **Health check** → Verifica que la app esté funcionando

## 🔒 VARIABLES DE ENTORNO PARA PRODUCCIÓN

### En Azure Container Apps, configura:
```bash
# Configurar variables de entorno
az containerapp update \
  --name rag-documentos-judiciales \
  --resource-group rg-documentos-judiciales \
  --set-env-vars \
    POSTGRES_HOST=psql-documentos-judiciales.postgres.database.azure.com \
    POSTGRES_DB=documentos_juridicos_gpt4 \
    POSTGRES_USER=docs_admin \
    POSTGRES_PASSWORD=secretref:postgres-password \
    OPENAI_API_KEY=secretref:openai-api-key
```

## 📊 PRÓXIMOS PASOS

1. **Completar configuración inicial** en Azure
2. **Configurar secrets** en GitHub  
3. **Hacer push** para activar primer despliegue
4. **Verificar funcionamiento** en la URL generada

---

🎉 **¡Listo!** Con esta configuración tendrás despliegues automáticos cada vez que hagas push a main.