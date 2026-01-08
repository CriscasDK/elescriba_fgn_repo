# 🛡️ Sistema de Backup y Restauración - RAG Jurídico

Este documento describe el sistema completo de backup y restauración implementado el 28 de Agosto de 2025.

## 📦 Archivos de Backup Disponibles

### Backup Principal: `backup_sistema_rag_28ago2025_1055.tar.gz` (360K)
- **Fecha**: 28 de Agosto de 2025 - 10:55 AM
- **Contenido**: Sistema completo unificado RAG + Base de Datos
- **Estado**: ✅ Funcionalidades completamente integradas

**Incluye:**
- ✅ Interfaz principal unificada (`interfaz_principal.py`)
- ✅ Sistema RAG completo (`src/core/sistema_rag_completo.py`)
- ✅ Cliente Azure Search dual-índice (`src/core/azure_search_vectorizado.py`)
- ✅ Clasificador inteligente LLM (`clasificador_inteligente_llm.py`)
- ✅ Scripts de prueba y configuración
- ✅ Documentación técnica completa

## 🔧 Scripts de Gestión

### 1. `restaurar_sistema.sh` - Restauración Automática
Restaura el sistema completo desde el backup más reciente.

```bash
./restaurar_sistema.sh
```

**Funciones:**
- ✅ Verifica existencia del backup
- ✅ Crea respaldo del estado actual antes de restaurar
- ✅ Extrae todos los archivos del backup
- ✅ Verifica integridad de archivos críticos
- ✅ Proporciona comandos para iniciar el sistema

### 2. `verificar_sistema.sh` - Verificación Completa
Verifica el estado completo del sistema tras la restauración.

```bash
./verificar_sistema.sh
```

**Verifica:**
- 📁 Estructura completa de archivos
- 🐍 Ambiente Python y paquetes críticos
- ⚙️ Configuración y variables de entorno
- 🗄️ Conectividad de base de datos
- 🌐 Disponibilidad de puertos
- 🔄 Procesos activos del sistema

## 🚀 Procedimiento de Restauración Completa

### Paso 1: Ejecutar Restauración
```bash
# Navegar al directorio del proyecto
cd /home/lab4/scripts/documentos_judiciales

# Ejecutar restauración
./restaurar_sistema.sh
```

### Paso 2: Verificar Sistema
```bash
# Verificar integridad completa
./verificar_sistema.sh
```

### Paso 3: Iniciar Sistema
```bash
# Activar ambiente virtual
source venv_docs/bin/activate

# Iniciar interfaz principal
streamlit run interfaz_principal.py --server.port 8508 --server.address 0.0.0.0
```

### Paso 4: Acceder a la Aplicación
- **Local**: http://localhost:8508
- **Red**: http://10.1.180.13:8508

## 📊 Estado del Sistema Restaurado

### Funcionalidades Integradas
- ✅ **Sistema RAG Unificado**: Búsqueda vectorial + Base de datos
- ✅ **Interfaz Dinámica**: Adaptación inteligente según contexto de consulta
- ✅ **Búsqueda Cruzada**: Entre índices `exhaustive-legal-chunks-v2` y `exhaustive-legal-index`
- ✅ **Panel de Filtros**: 8 opciones de filtrado inteligente
- ✅ **Clasificación Automática**: LLM determina tipo de consulta (RAG vs BD)
- ✅ **Metadatos Completos**: Trazabilidad y contexto legal completo

### Datos Disponibles
- **Azure Search**: 100,025+ chunks vectorizados
- **PostgreSQL**: 11,111 documentos únicos, 12,248 víctimas
- **Índices**: Dual sistema para chunks específicos y documentos completos

### Tecnologías
- **Frontend**: Streamlit (Puerto 8508)
- **Backend**: Flask + FastAPI
- **IA**: Azure OpenAI GPT-4 + Embeddings
- **Búsqueda**: Azure Cognitive Search
- **Base de Datos**: PostgreSQL

## 🐛 Resolución de Problemas

### Problema: Puerto 8508 en uso
```bash
# Encontrar proceso
ps aux | grep streamlit

# Terminar proceso
kill -9 <PID>

# Reiniciar
streamlit run interfaz_principal.py --server.port 8508 --server.address 0.0.0.0
```

### Problema: Base de datos no conecta
```bash
# Verificar PostgreSQL
sudo systemctl status postgresql

# Conectar manualmente
psql -h localhost -p 5432 -d documentos_juridicos_gpt4 -U docs_user
```

### Problema: Ambiente virtual corrupto
```bash
# Recrear ambiente
rm -rf venv_docs
python -m venv venv_docs
source venv_docs/bin/activate
pip install -r api_requirements.txt
```

## 📋 Checklist de Verificación Post-Restauración

- [ ] ✅ Archivos críticos restaurados
- [ ] ✅ Ambiente Python activado
- [ ] ✅ Paquetes instalados
- [ ] ✅ Variables de entorno configuradas
- [ ] ✅ Base de datos accesible
- [ ] ✅ Puerto 8508 disponible
- [ ] ✅ Streamlit ejecutándose
- [ ] ✅ Interfaz accesible vía web
- [ ] ✅ Búsqueda RAG funcional
- [ ] ✅ Consultas BD funcionales
- [ ] ✅ Filtros operativos

## 📞 Información de Contacto y Documentación

### Documentación Técnica Completa
- `DOCUMENTACION_BACKUP_28AGO2025.md` - Estado técnico completo
- `DOCUMENTACION_SISTEMA_RAG_TRAZABILIDAD_LEGAL.md` - Arquitectura general
- `API_REFERENCE.md` - Referencia de API

### Archivos de Configuración
- `config/.env` - Variables de entorno
- `api_requirements.txt` - Dependencias Python
- `docker-compose.yml` - Configuración Docker

---

**Última Actualización**: 28 de Agosto de 2025 - 11:00 AM  
**Responsable**: Sistema automatizado de backup RAG Jurídico  
**Estado**: ✅ Sistema completo y operativo
