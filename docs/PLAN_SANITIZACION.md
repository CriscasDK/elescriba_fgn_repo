# 🧹 PLAN DE SANITIZACIÓN DEL PROYECTO
## Análisis Exhaustivo y Propuesta de Limpieza

---

## 📊 INVENTARIO COMPLETO ACTUAL

### 📁 **ARCHIVOS TOTALES IDENTIFICADOS: 141**

#### 🐍 **ARCHIVOS PYTHON (71 archivos)**
```yaml
Scripts Principales (MANTENER):
  - extractor_definitivo.py              # ETL principal ✅
  - trazabilidad_100_CORREGIDO.py        # Trazabilidad final ✅
  - sistema_rag_completo.py              # RAG sistema ✅
  - api_rag.py                          # API REST ✅
  - streamlit_app.py                    # Dashboard ✅

Scripts de Análisis (MANTENER):
  - analisis_victimas_avanzado.py       # Análisis core ✅
  - frontend_victimas_validacion.py     # Frontend validado ✅
  - gestor_consultas_habilitadas.py     # Router consultas ✅

Scripts de Mantenimiento (MANTENER):
  - poblar_metadatos_completo.py        # Poblado final ✅
  - verificacion_final.py               # Verificación sistema ✅
  - auditoria_integridad_completa.py    # Auditoría ✅

Scripts de Testing (ARCHIVAR):
  - test_*.py (21 archivos)             # Tests desarrollo 📦
  - debug_*.py (5 archivos)             # Debug temporal 📦
  - quick_sample.py                     # Prueba rápida 📦

Scripts Obsoletos (ELIMINAR):
  - extractor_*.py (versiones antiguas) # Duplicados ❌
  - frontend_victimas_*.py (versiones)  # Múltiples versiones ❌
  - consulta_*.py (scripts básicos)     # Reemplazados ❌
  - detective_*.py (experimentales)     # No usados ❌
  - corregir_metadatos_*.py (antiguos)  # Obsoletos ❌

Scripts Duplicados (ELIMINAR):
  - muestra_simple.py vs quick_sample.py     # Duplicado ❌
  - repoblar_*.py (múltiples versiones)      # Consolidar ❌
  - verificar_*.py (versiones antiguas)      # Limpiar ❌
```

#### 📄 **ARCHIVOS SQL (25 archivos)**
```yaml
SQL Validados (MANTENER):
  - consultas_analisis_victimas.sql          # 100% operativo ✅
  - consultas_busqueda_avanzada.sql          # 100% operativo ✅
  - consultas_redes_temporal_geografico.sql  # 100% operativo ✅
  - rag_trazabilidad_sistema.sql             # 100% operativo ✅
  - fix_rag_final_correct.sql                # 100% operativo ✅
  - consultas_busqueda_frecuentes.sql        # 100% operativo ✅
  - consultas_hibridas_frecuentes_rag.sql    # 100% operativo ✅

SQL Pendientes de Validación (REVISAR):
  - consultas_busqueda_palabras.sql          # No validado 🔍
  - consultas_busqueda_lenguaje_natural.sql  # No validado 🔍
  - consultas_macrocaso_up.sql               # No validado 🔍
  - fix_termino_ambiguo.sql                  # No validado 🔍

SQL Obsoletos (ELIMINAR):
  - fix_rag_functions*.sql (múltiples)       # Reemplazados ❌
  - fix_contexto_functions.sql               # Obsoleto ❌
  - consulta_victima_perdida.sql             # Individual ❌
  - consulta_victimas_optimizada.sql         # Reemplazado ❌
  - verificacion_sql_directa.sql             # Debug ❌
```

#### 📋 **ARCHIVOS DOCUMENTACIÓN (17 archivos)**
```yaml
Documentación Principal (MANTENER):
  - README.md                                 # Principal ✅
  - DOCUMENTACION_COMPLETA_FINAL.md          # Arquitectura ✅
  - docs/ARQUITECTURA_TECNICA_DETALLADA.md   # Técnica ✅
  - docs/FLUJOS_TRABAJO.md                   # Procesos ✅
  - DEPLOYMENT_GUIDE.md                      # Deploy ✅
  - TECHNICAL_GUIDE.md                       # Técnica ✅

Documentación Histórica (ARCHIVAR):
  - ESTADO_FINAL_RAG.md                      # Histórico 📦
  - OPTIMIZACION_RAG_RESUMEN.md              # Histórico 📦
  - PROCESO_TRAZABILIDAD_COMPLETADO.md       # Histórico 📦
  - RESUMEN_DIA_25_JULIO.md                  # Histórico 📦

Documentación Obsoleta (ELIMINAR):
  - README_ESTADO_ACTUAL.md                  # Obsoleto ❌
  - ESTRUCTURA_REFERENCIA.md                 # Obsoleto ❌
  - GUIA_REINICIO.md                         # Obsoleto ❌
  - TROUBLESHOOTING.md                       # Redundante ❌
```

#### 📁 **OTROS ARCHIVOS (28 archivos)**
```yaml
Configuración (MANTENER):
  - .env*, docker-compose.yml, requirements*.txt  # Config ✅
  - .gitignore, LICENSE                           # Git ✅
  - setup_docs.sh, start.sh, reiniciar_sistema.sh # Scripts ✅

Logs y Temporales (LIMPIAR):
  - *.log (6 archivos)                           # Logs antiguos 🧹
  - respuesta_llm_error_*.txt (5 archivos)       # Errores debug 🧹
  - traceback                                     # Error temporal 🧹
  - poblado_log.txt                              # Log antiguo 🧹

Office y Temporales (ELIMINAR):
  - 24072025_estado_proyecto.docx                # Word obsoleto ❌
  - preguntas_resolver_bd.docx                   # Word obsoleto ❌
  - .~lock.*.docx#                               # Lock file ❌
  - reporte_victimas_*.txt                       # Reportes viejos ❌
```

---

## 🎯 ESTRATEGIA DE SANITIZACIÓN

### 📋 **FASE 1: CATEGORIZACIÓN**
```yaml
MANTENER (39 archivos):
  Core System: 15 archivos
  SQL Validados: 7 archivos  
  Documentación: 10 archivos
  Configuración: 7 archivos

ARCHIVAR (28 archivos):
  Tests: 21 archivos
  Docs Históricas: 4 archivos
  Debug Scripts: 3 archivos

ELIMINAR (74 archivos):
  Scripts Obsoletos: 45 archivos
  SQL Obsoletos: 11 archivos
  Logs/Temporales: 12 archivos
  Docs Obsoletas: 6 archivos
```

### 🗂️ **FASE 2: NUEVA ESTRUCTURA**
```
documentos_judiciales/
├── 📁 src/                          # CÓDIGO PRINCIPAL
│   ├── core/
│   │   ├── extractor_definitivo.py
│   │   ├── trazabilidad_100_CORREGIDO.py
│   │   └── sistema_rag_completo.py
│   ├── api/
│   │   ├── api_rag.py
│   │   └── streamlit_app.py
│   ├── analysis/
│   │   ├── analisis_victimas_avanzado.py
│   │   └── gestor_consultas_habilitadas.py
│   └── maintenance/
│       ├── poblar_metadatos_completo.py
│       ├── verificacion_final.py
│       └── auditoria_integridad_completa.py
│
├── 📁 sql/                          # CONSULTAS SQL
│   ├── validated/                   # 7 archivos validados
│   └── pending/                     # 11 archivos por validar
│
├── 📁 docs/                         # DOCUMENTACIÓN
│   ├── architecture/
│   ├── guides/
│   └── historical/
│
├── 📁 config/                       # CONFIGURACIÓN
│   ├── .env*
│   ├── requirements*.txt
│   └── docker-compose.yml
│
├── 📁 scripts/                      # SCRIPTS SISTEMA
│   ├── setup_docs.sh
│   ├── start.sh
│   └── reiniciar_sistema.sh
│
├── 📁 archive/                      # ARCHIVOS HISTÓRICOS
│   ├── tests/                       # 21 tests archivados
│   ├── docs_historical/             # 4 docs históricas
│   └── debug/                       # 3 scripts debug
│
└── 📁 data/                         # DATOS
    ├── json_files/
    ├── logs/
    └── postgres/
```

---

## ⚡ **PLAN DE EJECUCIÓN SANITIZACIÓN**

### 🎯 **ETAPA 1: PREPARACIÓN SEGURA**
```bash
# 1. Backup completo sistema
tar -czf backup_pre_sanitizacion_$(date +%Y%m%d).tar.gz \
    /home/lab4/scripts/documentos_judiciales/

# 2. Verificar estado sistema actual
python verificacion_final.py

# 3. Validar SQL críticos
SELECT COUNT(*) FROM documentos;    # Debe ser 11,111
SELECT COUNT(*) FROM metadatos;     # Verificar integridad
```

### 🗂️ **ETAPA 2: CREACIÓN ESTRUCTURA**
```bash
# Crear nueva estructura
mkdir -p src/{core,api,analysis,maintenance}
mkdir -p sql/{validated,pending}
mkdir -p docs/{architecture,guides,historical}
mkdir -p config scripts archive/{tests,docs_historical,debug}
```

### 📦 **ETAPA 3: MOVIMIENTO DE ARCHIVOS**
```yaml
FASE 3A - Archivos Core:
  - Mover 15 archivos principales a src/
  - Mover 7 SQL validados a sql/validated/
  - Mover configuración a config/

FASE 3B - Archivado Seguro:
  - Mover tests a archive/tests/
  - Mover docs históricas a docs/historical/
  - Mover debug scripts a archive/debug/

FASE 3C - Limpieza Final:
  - Eliminar 74 archivos obsoletos
  - Limpiar logs temporales
  - Remover duplicados confirmados
```

### ✅ **ETAPA 4: VALIDACIÓN POST-SANITIZACIÓN**
```bash
# Verificar sistema funcional
python src/maintenance/verificacion_final.py

# Test SQL críticos
python -c "import subprocess; subprocess.run(['psql', '-c', 'SELECT version()'])"

# Verificar API
python src/api/api_rag.py --test

# Validar dashboard
python src/api/streamlit_app.py --check
```

---

## 📊 **MÉTRICAS DE SANITIZACIÓN**

### 🎯 **OBJETIVOS CUANTITATIVOS**
```yaml
Reducción Archivos:
  Antes: 141 archivos
  Después: 67 archivos (52% reducción)
  Eliminados: 74 archivos
  
Organización:
  Directorios: 3 → 8 (mejor organización)
  Profundidad: 2 → 3 niveles máximo
  Archivos/directorio: 47 → 8 promedio

Limpieza Espacio:
  Logs antiguos: ~50MB liberados
  Scripts duplicados: ~15MB liberados
  Docs obsoletas: ~5MB liberados
  Total estimado: ~70MB liberados
```

### 🔍 **CRITERIOS DE ÉXITO**
```yaml
Funcionalidad:
  ✅ Sistema RAG operativo al 100%
  ✅ Base de datos intacta (11,111 docs)
  ✅ Trazabilidad 99.9% preservada
  ✅ API y dashboard funcionales

Organización:
  ✅ Estructura lógica clara
  ✅ Archivos categorizados correctamente
  ✅ Sin duplicados en producción
  ✅ Documentación consolidada

Mantenibilidad:
  ✅ Código core identificable
  ✅ Tests archivados pero accesibles
  ✅ Configuración centralizada
  ✅ Scripts de inicio simplificados
```

---

## ⚠️ **PRECAUCIONES CRÍTICAS**

### 🛡️ **SALVAGUARDAS OBLIGATORIAS**
```yaml
Antes de Eliminar CUALQUIER Archivo:
  1. Verificar no está en uso por sistema productivo
  2. Confirmar no contiene configuración única
  3. Buscar referencias en otros archivos
  4. Backup individual del archivo crítico

Archivos NUNCA Eliminar Sin Validación:
  - Cualquier .py que contenga "CORREGIDO" o "FINAL"
  - Archivos SQL con "rag_" en el nombre
  - Cualquier archivo .env o config
  - Scripts con "start" o "setup" en el nombre

Validación Obligatoria Post-Cambio:
  - Test conexión base de datos
  - Verificar conteo documentos/víctimas
  - Probar consulta RAG básica
  - Validar dashboard carga correctamente
```

### 🔒 **PUNTO DE NO RETORNO**
```yaml
Crear Checkpoint Antes de:
  - Eliminar archivos SQL
  - Mover scripts de inicio
  - Cambiar estructura directorios principales
  - Modificar archivos de configuración

Procedimiento Rollback:
  1. Restaurar desde backup_pre_sanitizacion
  2. Verificar estado base datos
  3. Ejecutar verificacion_final.py
  4. Confirmar sistema operativo 100%
```

---

## 🚀 **ROADMAP EJECUCIÓN**

### ⏰ **TIMELINE ESTIMADO**
```yaml
Preparación (30 min):
  - Backup completo sistema
  - Verificación estado actual
  - Creación estructura directorios

Ejecución (45 min):
  - Movimiento archivos core (15 min)
  - Archivado tests y debug (15 min)
  - Eliminación archivos obsoletos (15 min)

Validación (30 min):
  - Test funcionalidad sistema
  - Verificación integridad datos
  - Pruebas API y dashboard

Total Estimado: 1h 45min
```

### 🎯 **DECISIÓN USUARIO**
¿Proceder con la sanitización según este plan?

**Opciones:**
1. 🟢 **PROCEDER** - Ejecutar sanitización completa
2. 🟡 **MODIFICAR** - Ajustar plan antes de proceder  
3. 🟠 **PARCIAL** - Solo eliminar archivos más obvios
4. 🔴 **CANCELAR** - Mantener estructura actual

---

**📅 Fecha análisis:** Julio 28, 2025  
**🎯 Estado:** Plan Detallado Listo para Ejecución  
**⚠️ Criticidad:** Extremo Cuidado - Sistema Productivo**
