# 🚨 AUDITORÍA DE SEGURIDAD URGENTE

**Fecha:** 07 de Enero, 2026
**Severidad:** CRÍTICA
**Estado:** ACCIÓN INMEDIATA REQUERIDA

---

## ⚠️ RESUMEN EJECUTIVO

Se han detectado **credenciales reales expuestas** en el repositorio público de GitHub de la Fiscalía. Se requiere acción inmediata para mitigar riesgos de seguridad.

**Repositorio afectado:** https://github.com/fgn-subtics/Escriba-back/tree/develop

---

## 🔴 CREDENCIALES EXPUESTAS

### Archivos Comprometidos

Los siguientes archivos contienen credenciales reales y están en el repositorio público:

```
1. CREDENCIALES_SISTEMA_13AGO2025.md
   - Contraseñas de PostgreSQL
   - Usuarios y passwords de pgAdmin
   - Información de servicios internos

2. scripts/crear_indice_chunks_mel.py
   - AZURE_OPENAI_API_KEY (hardcoded)
   - AZURE_SEARCH_KEY (hardcoded)
   - Endpoints de Azure

3. scripts/poblar_3_chunks_mel.py
   - AZURE_OPENAI_API_KEY (hardcoded)
   - AZURE_SEARCH_KEY (hardcoded)

4. src/api/api_rag_simple.py
   - AZURE_OPENAI_API_KEY (hardcoded)
   - AZURE_SEARCH_KEY (hardcoded)
```

### Credenciales Específicas Detectadas

```
⚠️ Azure OpenAI API Key:
1oSTnxg0CC9O4oIaB2a6POpWSvOIFxXP6qwR5QlgbDW2ve79fE7KJQQJ99BCACHYHv6XJ3w3AAAAACOGNk1S

⚠️ Azure Search Key:
U2oDwFkJnRw0nDQNr9baaevAYHmBEB7zcC2hEGDts7AzSeDuiZdI

⚠️ PostgreSQL Password:
docs_password_2025

⚠️ pgAdmin Password:
admin_2025
```

---

## 🎯 ACCIONES INMEDIATAS REQUERIDAS

### PASO 1: Revocar Credenciales de Azure (URGENTE - 15 minutos)

#### 1.1 Azure OpenAI

```bash
# 1. Ir a Azure Portal: https://portal.azure.com
# 2. Navegar a: Azure OpenAI > tu recurso > Keys and Endpoint
# 3. Hacer clic en "Regenerate Key 1" y "Regenerate Key 2"
# 4. Copiar las nuevas keys y actualizar tu .env local
```

#### 1.2 Azure Cognitive Search

```bash
# 1. Ir a Azure Portal: https://portal.azure.com
# 2. Navegar a: Azure Cognitive Search > escriba-search > Keys
# 3. Hacer clic en "Regenerate admin key"
# 4. Copiar la nueva key y actualizar tu .env local
```

#### 1.3 Verificar Logs de Acceso

```bash
# 1. Azure Portal > Azure OpenAI > tu recurso > Monitoring > Metrics
# 2. Revisar accesos entre: 07-Ene-2026 12:00 y ahora
# 3. Buscar IPs desconocidas o patrones inusuales
# 4. Verificar volumen de tokens consumidos
```

---

### PASO 2: Cambiar Contraseñas de Base de Datos (30 minutos)

#### 2.1 PostgreSQL

```sql
-- Conectar como superuser
psql -U postgres

-- Cambiar password del usuario
ALTER USER docs_user WITH PASSWORD 'NUEVA_PASSWORD_SEGURA_AQUI';

-- Actualizar .env local
POSTGRES_PASSWORD=NUEVA_PASSWORD_SEGURA_AQUI
```

#### 2.2 pgAdmin

```bash
# 1. Acceder a pgAdmin: http://localhost:8080
# 2. File > Preferences > Security
# 3. Change Master Password
# 4. Actualizar documentación interna
```

---

### PASO 3: Limpiar Repositorio Git (60 minutos)

#### 3.1 Eliminar Credenciales del Historial

```bash
# OPCIÓN A: BFG Repo-Cleaner (Recomendado)
# Descargar BFG: https://rtyley.github.io/bfg-repo-cleaner/

# 1. Hacer backup
git clone https://github.com/fgn-subtics/Escriba-back.git backup-escriba

# 2. Crear archivo con strings a eliminar
cat > secrets.txt <<EOF
1oSTnxg0CC9O4oIaB2a6POpWSvOIFxXP6qwR5QlgbDW2ve79fE7KJQQJ99BCACHYHv6XJ3w3AAAAACOGNk1S
U2oDwFkJnRw0nDQNr9baaevAYHmBEB7zcC2hEGDts7AzSeDuiZdI
docs_password_2025
admin_2025
EOF

# 3. Ejecutar BFG
java -jar bfg.jar --replace-text secrets.txt Escriba-back.git

# 4. Limpiar y forzar push
cd Escriba-back.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

```bash
# OPCIÓN B: git-filter-repo (Alternativa)
pip install git-filter-repo

# Eliminar archivos sensibles del historial
git filter-repo --path CREDENCIALES_SISTEMA_13AGO2025.md --invert-paths
git filter-repo --path scripts/crear_indice_chunks_mel.py --invert-paths
git filter-repo --path scripts/poblar_3_chunks_mel.py --invert-paths

# Force push
git push origin develop --force
```

#### 3.2 Sanitizar Archivos y Re-subir

```bash
# Los archivos ya han sido sanitizados por Claude
# Hacer commit y push
git add CREDENCIALES_SISTEMA_13AGO2025.md scripts/ src/api/
git commit -m "security: Sanitizar credenciales expuestas"
git push fiscalia main:develop
```

---

### PASO 4: Notificaciones y Monitoreo (Inmediato)

#### 4.1 Notificar al Equipo

```
Enviar email a:
- Equipo de DevOps/Seguridad de Fiscalía
- Administrador de Azure
- Equipo de desarrollo

Asunto: [URGENTE] Credenciales expuestas en repositorio GitHub

Mensaje:
Se detectaron credenciales reales expuestas en el repositorio público
Escriba-back. Las credenciales han sido revocadas y regeneradas.

Acciones tomadas:
- Keys de Azure OpenAI regeneradas
- Keys de Azure Search regeneradas
- Passwords de BD cambiadas
- Repositorio sanitizado

Favor de actualizar sus configuraciones locales.
```

#### 4.2 Configurar Monitoreo

```bash
# Configurar GitHub Secret Scanning
# 1. GitHub repo > Settings > Security > Code security and analysis
# 2. Enable "Secret scanning"
# 3. Enable "Push protection"

# Configurar pre-commit hooks
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

---

## 📋 CHECKLIST DE MITIGACIÓN

### Acciones Críticas (Primera Hora)

- [ ] ✅ Revocar Azure OpenAI API Keys
- [ ] ✅ Revocar Azure Search Admin Keys
- [ ] ✅ Verificar logs de acceso en Azure
- [ ] ✅ Cambiar password PostgreSQL
- [ ] ✅ Cambiar password pgAdmin
- [ ] ✅ Notificar al equipo de seguridad

### Acciones de Limpieza (Siguientes 24 horas)

- [ ] ⏳ Limpiar historial de Git con BFG/git-filter-repo
- [ ] ⏳ Sanitizar archivos y re-subir al repositorio
- [ ] ⏳ Verificar que no queden credenciales en otros archivos
- [ ] ⏳ Actualizar .gitignore con patrones adicionales
- [ ] ⏳ Configurar pre-commit hooks
- [ ] ⏳ Habilitar GitHub Secret Scanning

### Acciones Preventivas (Esta Semana)

- [ ] 🔄 Implementar rotación automática de keys (Azure Key Vault)
- [ ] 🔄 Configurar alertas de uso inusual en Azure
- [ ] 🔄 Implementar autenticación por IP en Azure
- [ ] 🔄 Crear política de gestión de secretos
- [ ] 🔄 Capacitar al equipo en mejores prácticas
- [ ] 🔄 Realizar auditoría completa de seguridad

---

## 🛡️ MEJORES PRÁCTICAS PARA PREVENIR FUTURAS EXPOSICIONES

### 1. Usar Variables de Entorno (SIEMPRE)

```python
# ❌ MAL - Hardcoded
AZURE_KEY = "1oSTnxg0CC9O4oIaB2a6..."

# ✅ BIEN - Variable de entorno
import os
AZURE_KEY = os.getenv('AZURE_OPENAI_API_KEY')
```

### 2. Verificar .gitignore

```bash
# Agregar a .gitignore
.env
.env.*
*.key
*.pem
credentials.*
secrets.*
config/production.yml
```

### 3. Usar Azure Key Vault

```python
# Ejemplo de uso de Azure Key Vault
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://tu-keyvault.vault.azure.net/", credential=credential)

# Obtener secreto
secret = client.get_secret("AZURE-OPENAI-KEY")
api_key = secret.value
```

### 4. Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

### 5. GitHub Secret Scanning

```bash
# Habilitar en:
# Repo > Settings > Security > Code security and analysis
# - Secret scanning: Enabled
# - Push protection: Enabled
```

---

## 📊 EVALUACIÓN DE RIESGO

### Nivel de Exposición

| Componente | Riesgo | Impacto | Probabilidad | Prioridad |
|------------|--------|---------|--------------|-----------|
| Azure OpenAI Key | ALTO | ALTO | MEDIO | P1 |
| Azure Search Key | ALTO | ALTO | MEDIO | P1 |
| PostgreSQL Pass | MEDIO | ALTO | BAJO | P2 |
| pgAdmin Pass | BAJO | MEDIO | BAJO | P3 |

### Tiempo de Exposición

```
Primer commit con credenciales: ~07-Ene-2026 12:28 UTC
Tiempo expuesto: ~2-3 horas
Visibilidad: Repositorio público
Alcance: Cualquier persona con acceso a GitHub
```

### Impacto Potencial

```
✗ Acceso no autorizado a servicios Azure
✗ Consumo fraudulento de tokens OpenAI (~$150 USD potencial)
✗ Acceso a base de datos de producción
✗ Exposición de datos sensibles de víctimas
✗ Modificación/eliminación de datos
```

---

## 🔍 VERIFICACIÓN POST-MITIGACIÓN

### Verificar Keys Revocadas

```bash
# Probar old key (debe fallar)
curl -H "api-key: 1oSTnxg0CC9O4oIaB2a6POpWSvOIFxXP6qwR5QlgbDW2ve79fE7KJQQJ99BCACHYHv6XJ3w3AAAAACOGNk1S" \
  "https://fgnfoundrylabo3874907599.cognitiveservices.azure.com/openai/deployments?api-version=2024-02-15-preview"

# Debe retornar: 401 Unauthorized
```

### Verificar Repositorio Limpio

```bash
# Buscar credenciales en el repo
git grep -E "1oSTnxg0CC9O4oIaB2a6|U2oDwFkJnRw0nDQNr9ba"
# Debe retornar: Sin resultados

# Verificar archivos sanitizados
git show HEAD:CREDENCIALES_SISTEMA_13AGO2025.md | grep "CAMBIAR"
# Debe mostrar: placeholders en lugar de credenciales reales
```

### Monitorear Uso de Azure

```bash
# Durante las próximas 48 horas, monitorear:
# 1. Azure Cost Management
# 2. OpenAI Usage Metrics
# 3. Search Service Request Rate
# 4. PostgreSQL Connection Logs
```

---

## 📞 CONTACTOS DE EMERGENCIA

### Soporte Azure

- **Portal:** https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade
- **Teléfono:** +1-800-642-7676 (24/7)
- **Chat:** Disponible en el portal

### GitHub Support

- **Email:** support@github.com
- **Docs:** https://docs.github.com/en/code-security/secret-scanning

### Equipo Interno

- **DevOps:** devops@fiscalia.gov.co
- **Seguridad:** seguridad@fiscalia.gov.co
- **CTO:** cto@fiscalia.gov.co

---

## 📚 REFERENCIAS

- [Azure Key Vault Best Practices](https://learn.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [Git Filter Repo](https://github.com/newren/git-filter-repo)
- [BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)

---

**Documento generado automáticamente por auditoría de seguridad**
**Fiscalía General de la Nación - Sistema Escriba Legal**
**Fecha: 07 de Enero, 2026**
