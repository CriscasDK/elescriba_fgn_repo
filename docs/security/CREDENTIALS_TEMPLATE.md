# 🔐 PLANTILLA DE CREDENCIALES Y ACCESOS

**IMPORTANTE:** Este es un archivo de template. NO incluir credenciales reales aquí.

**Configurar credenciales en:** `.env` (no versionado en git)

---

## 🌐 ACCESOS WEB

### 🖥️ **pgAdmin 4 - Administración BD**
- **URL:** http://localhost:8080
- **Usuario:** Configurar en instalación
- **Password:** Configurar en instalación
- **Descripción:** Interface web para administrar PostgreSQL

### 🤖 **API RAG - Búsquedas Semánticas**
- **URL:** http://localhost:8001
- **Documentación:** http://localhost:8001/docs
- **Endpoint principal:** GET /buscar?consulta={texto}&top_k={numero}

### 📊 **Dashboard Principal**
- **URL:** http://localhost:8050
- **Descripción:** Aplicación Dash principal

---

## 🗄️ CONFIGURACIÓN DE BASE DE DATOS

### 📋 **PostgreSQL**

```bash
# Configurar en .env:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=documentos_juridicos
POSTGRES_USER=docs_user
POSTGRES_PASSWORD=TU_PASSWORD_SEGURO_AQUI
```

**Cadena de conexión:**
```
postgresql://docs_user:PASSWORD@localhost:5432/documentos_juridicos
```

---

## ☁️ SERVICIOS EN LA NUBE (AZURE)

### 🤖 **Azure OpenAI**

```bash
# Configurar en .env:
AZURE_OPENAI_ENDPOINT=https://tu-servicio.openai.azure.com/
AZURE_OPENAI_API_KEY=TU_API_KEY_AQUI
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Cómo obtener credenciales:**
1. Portal Azure: https://portal.azure.com
2. Navegar a: Azure OpenAI > tu recurso
3. Keys and Endpoint > Copiar Key 1 o Key 2

---

### 🔍 **Azure AI Search**

```bash
# Configurar en .env:
AZURE_SEARCH_ENDPOINT=https://tu-search.search.windows.net
AZURE_SEARCH_KEY=TU_SEARCH_KEY_AQUI
AZURE_SEARCH_INDEX=documentos-juridicos
```

**Cómo obtener credenciales:**
1. Portal Azure: https://portal.azure.com
2. Navegar a: Azure Cognitive Search > tu servicio
3. Keys > Copiar Admin Key

---

## 🔐 MEJORES PRÁCTICAS DE SEGURIDAD

### ✅ DO (Hacer)

1. **Usar siempre variables de entorno**
   ```python
   import os
   api_key = os.getenv('AZURE_OPENAI_API_KEY')
   ```

2. **Mantener .env fuera de Git**
   ```bash
   # Verificar .gitignore incluye:
   .env
   .env.*
   *.key
   credentials.*
   ```

3. **Rotar credenciales regularmente**
   - Azure Keys: Cada 90 días
   - DB Passwords: Cada 6 meses

4. **Usar Azure Key Vault en producción**
   ```python
   from azure.identity import DefaultAzureCredential
   from azure.keyvault.secrets import SecretClient

   credential = DefaultAzureCredential()
   client = SecretClient(vault_url="https://tu-keyvault.vault.azure.net/", credential=credential)
   secret = client.get_secret("AZURE-OPENAI-KEY")
   ```

### ❌ DON'T (No Hacer)

1. **NUNCA hardcodear credenciales**
   ```python
   # ❌ MAL
   api_key = "1oSTnxg0CC9O4oIaB2a6..."
   ```

2. **NUNCA commitear archivos .env**
   ```bash
   # Verificar antes de commit:
   git status | grep ".env"
   ```

3. **NUNCA compartir credenciales por email/chat**
   - Usar sistemas seguros (Azure Key Vault, 1Password, etc.)

---

## 📋 CHECKLIST DE CONFIGURACIÓN

### Primera Vez

- [ ] Crear archivo `.env` desde `.env.example`
- [ ] Obtener credenciales de Azure Portal
- [ ] Configurar credenciales de PostgreSQL
- [ ] Verificar `.gitignore` incluye `.env`
- [ ] Probar conexiones a servicios
- [ ] Documentar ubicación de credenciales (internamente)

### Cada Deployment

- [ ] Verificar variables de entorno cargadas
- [ ] Probar conexión a Azure OpenAI
- [ ] Probar conexión a Azure Search
- [ ] Probar conexión a PostgreSQL
- [ ] Verificar logs sin errores de autenticación

---

## 🆘 TROUBLESHOOTING

### Error: "Authentication failed"

```bash
# Verificar que las variables están cargadas:
python -c "import os; print(os.getenv('AZURE_OPENAI_API_KEY'))"

# Si retorna None, cargar .env:
source .env  # o usar python-dotenv
```

### Error: "Connection refused"

```bash
# Verificar servicios corriendo:
docker ps  # Para PostgreSQL en Docker
netstat -an | grep 5432  # Para PostgreSQL local
```

---

## 📞 SOPORTE

Para obtener credenciales o ayuda con configuración:

- **DevOps:** devops@fiscalia.gov.co
- **Administrador Azure:** azure-admin@fiscalia.gov.co
- **Documentación:** Ver README_DEPLOYMENT.md

---

**Este es un archivo template. Reemplazar valores de ejemplo con configuración real en tu .env local.**
