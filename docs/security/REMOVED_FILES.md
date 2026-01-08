# 🔐 Archivos Removidos por Seguridad

**Fecha:** 07 de Enero, 2026
**Razón:** Credenciales hardcodeadas detectadas

---

## Archivos Eliminados

Los siguientes archivos fueron removidos del repositorio debido a que contenían credenciales reales hardcodeadas:

### 1. `src/api/api_rag_simple.py`
- **Razón:** Contenía Azure OpenAI API Key hardcoded
- **Líneas problemáticas:** 75-77, 90
- **Reemplazo:** Ver `src/api/rag_api.py` (versión segura con variables de entorno)

### 2. `scripts/crear_indice_chunks_mel.py`
- **Razón:** Contenía Azure OpenAI y Search Keys hardcoded
- **Reemplazo:** Funcionalidad integrada en sistema principal

### 3. `scripts/poblar_3_chunks_mel.py`
- **Razón:** Contenía Azure OpenAI y Search Keys hardcoded
- **Reemplazo:** Funcionalidad integrada en sistema principal

### 4. `CREDENCIALES_SISTEMA_13AGO2025.md`
- **Razón:** Documentaba credenciales reales en texto plano
- **Reemplazo:** `CREDENCIALES_TEMPLATE.md` (template sin credenciales)

---

## ✅ Alternativas Seguras

### Para API RAG

Usar el archivo principal que YA usa variables de entorno:

```bash
# Ver implementación segura en:
src/api/rag_api.py
```

Este archivo correctamente usa:
```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('AZURE_OPENAI_API_KEY')
search_key = os.getenv('AZURE_SEARCH_KEY')
```

### Para Scripts de Población

La funcionalidad de estos scripts ya está integrada en:

```bash
# ETL Principal
python procesar_masivo.py json_files/

# Extractor Definitivo
python src/core/extractor_definitivo.py
```

---

## 📋 Si Necesitas Estos Scripts

Si realmente necesitas la funcionalidad de los scripts removidos:

1. **Recuperar de backup local** (si tienes)
2. **Sanitizar manualmente:**
   ```python
   # Reemplazar credenciales hardcoded:
   api_key = "1oSTnxg0CC..."  # ❌ MAL

   # Por variables de entorno:
   import os
   api_key = os.getenv('AZURE_OPENAI_API_KEY')  # ✅ BIEN
   ```
3. **NO volver a commitear sin sanitizar**

---

## 🔒 Mejores Prácticas

Para prevenir exposición futura:

### 1. Pre-commit Hook

```bash
# Instalar detect-secrets
pip install detect-secrets

# Escanear antes de commit
detect-secrets scan --baseline .secrets.baseline

# Agregar a pre-commit
echo 'detect-secrets-hook --baseline .secrets.baseline $(git diff --staged --name-only)' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 2. GitHub Secret Scanning

Habilitar en: Settings > Security > Code security > Secret scanning

### 3. Revisar Antes de Push

```bash
# Buscar patrones sospechosos antes de push:
git diff main | grep -E "api_key.*=|password.*=|sk-|ghp_"
```

---

## ⚠️ Acción Requerida

Si eras usuario de estos archivos:

1. **Actualizar tu flujo de trabajo** para usar los scripts principales
2. **Verificar que tu `.env` local** tiene todas las credenciales necesarias
3. **Seguir la guía:** `GUIA_POBLAMIENTO_BASE_DATOS.md`

---

**Documentación de seguridad - Sistema Escriba Legal**
