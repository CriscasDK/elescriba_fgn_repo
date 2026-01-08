#!/bin/bash
# Script de Limpieza Física Post-Sanitización
# Fecha: Julio 28, 2025
# EJECUTAR CON EXTREMO CUIDADO

echo "🧹 INICIANDO LIMPIEZA FÍSICA DEL PROYECTO"
echo "========================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "verificacion_final.py" ]; then
    echo "❌ ERROR: No se encuentra verificacion_final.py"
    echo "   Ejecute desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar que existen las nuevas estructuras
if [ ! -d "src/core" ] || [ ! -d "sql/validated" ]; then
    echo "❌ ERROR: Estructura sanitizada no encontrada"
    echo "   Las carpetas src/core y sql/validated deben existir"
    exit 1
fi

echo "✅ Estructura sanitizada encontrada"

# PASO 1: Validar sistema antes de limpiar
echo ""
echo "🔍 PASO 1: Validando sistema actual..."
python3 verificacion_final.py > validacion_pre_limpieza.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Sistema validado - Procediendo con limpieza"
else
    echo "❌ Sistema con errores - ABORTANDO limpieza"
    echo "   Revise validacion_pre_limpieza.log"
    exit 1
fi

# PASO 2: Backup de seguridad
echo ""
echo "💾 PASO 2: Creando backup de seguridad..."
tar -czf "backup_pre_limpieza_$(date +%Y%m%d_%H%M%S).tar.gz" \
    --exclude="venv_docs" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".git" \
    . 

if [ $? -eq 0 ]; then
    echo "✅ Backup creado exitosamente"
else
    echo "❌ Error creando backup - ABORTANDO"
    exit 1
fi

echo ""
echo "🗑️ PASO 3: Limpieza de archivos obsoletos..."

# Lista de archivos a eliminar (según el plan de sanitización)
ARCHIVOS_ELIMINAR=(
    # Scripts obsoletos
    "extractor_definitivo_backup.py"
    "extractor_gpt_mini.py"
    "frontend_victimas.py"
    "frontend_victimas_agrupadas.py"
    "frontend_victimas_mejorado.py"
    "frontend_victimas_robusto.py"
    "frontend_victimas_simple.py"
    "frontend_victimas_tabla.py"
    "consulta_basica_victimas.py"
    "consulta_directa_victimas.py"
    "consulta_rapida_victimas.py"
    "detective_simple.py"
    "detective_victima_perdida.py"
    "corregir_metadatos_FIXED.py"
    "corregir_metadatos_urgente.py"
    "repoblar_metadatos.py"
    "repoblar_todo.py"
    "repoblar_todo_limpio.py"
    "verificacion_esencial.py"
    "verificacion_extraccion_completa.py"
    "verificacion_simple_final.py"
    "verificar_consulta_original.py"
    "verificar_sistema.py"
    "verificar_sistema_rag.py"
    "muestra_simple.py"
    "quick_sample.py"
    
    # SQL obsoletos
    "consulta_victima_perdida.sql"
    "consulta_victimas_optimizada.sql"
    "verificacion_sql_directa.sql"
    "fix_contexto_functions.sql"
    "fix_rag_functions.sql"
    "fix_rag_functions_complete.sql"
    "fix_rag_functions_final.sql"
    "fix_rag_organizaciones.sql"
    "fix_rag_sistema_final.sql"
    "fix_termino_ambiguo.sql"
    
    # Documentación obsoleta
    "README_ESTADO_ACTUAL.md"
    "ESTRUCTURA_REFERENCIA.md"
    "GUIA_REINICIO.md"
    "TROUBLESHOOTING.md"
    
    # Logs y temporales
    "analisis.log"
    "poblado_log.txt"
    "procesamiento_masivo.log"
    "traceback"
    "respuesta_llm_error_doc_1.txt"
    "respuesta_llm_error_doc_11295.txt"
    "respuesta_llm_error_doc_118.txt"
    "respuesta_llm_error_doc_2.txt"
    "respuesta_llm_error_doc_2513.txt"
    "reporte_victimas_20250728_145942.txt"
    "24072025_estado_proyecto.docx"
    "preguntas_resolver_bd.docx"
    ".~lock.preguntas_resolver_bd.docx#"
    
    # Otros obsoletos
    "ejemplo_semantic_kernel_gpt41.py"
    "analisis_victimas_random.py"
    "comparacion_consultas_victimas.py"
    "consultor_victimas_optimizado.py"
    "diagnostico_cambio_victimas.py"
    "frontend_debug_simple.py"
    "generar_reporte_victimas.py"
    "habilitar_listado.py"
    "procesar_masivo_fijo.py"
    "reporte_victimas_simple.py"
    "actualizar_metadatos_seguro.py"
)

# Eliminar archivos
eliminados=0
for archivo in "${ARCHIVOS_ELIMINAR[@]}"; do
    if [ -f "$archivo" ]; then
        echo "🗑️  Eliminando: $archivo"
        rm "$archivo"
        eliminados=$((eliminados + 1))
    fi
done

echo "✅ Archivos eliminados: $eliminados"

# PASO 4: Mover tests y debug a archive
echo ""
echo "📦 PASO 4: Archivando tests y debug..."

# Crear directorios de archivo si no existen
mkdir -p archive/tests
mkdir -p archive/debug
mkdir -p archive/docs_historical

# Mover tests
moved_tests=0
for test_file in test_*.py; do
    if [ -f "$test_file" ]; then
        echo "📦 Archivando: $test_file"
        mv "$test_file" archive/tests/
        moved_tests=$((moved_tests + 1))
    fi
done

# Mover debug
for debug_file in debug_*.py; do
    if [ -f "$debug_file" ]; then
        echo "📦 Archivando: $debug_file"
        mv "$debug_file" archive/debug/
    fi
done

# Mover documentación histórica
DOCS_HISTORICOS=(
    "ESTADO_FINAL_RAG.md"
    "OPTIMIZACION_RAG_RESUMEN.md"
    "PROCESO_TRAZABILIDAD_COMPLETADO.md"
    "RESUMEN_DIA_25_JULIO.md"
)

for doc in "${DOCS_HISTORICOS[@]}"; do
    if [ -f "$doc" ]; then
        echo "📦 Archivando doc: $doc"
        mv "$doc" archive/docs_historical/
    fi
done

echo "✅ Tests archivados: $moved_tests"

# PASO 5: Mover archivos de configuración
echo ""
echo "⚙️ PASO 5: Organizando configuración..."

# Mover archivos de configuración a config/ (solo si no existen ya)
CONFIG_FILES=(
    ".env"
    ".env.example"
    ".env.gpt41"
    "docker-compose.yml"
    "requirements.txt"
    "requirements-frontend.txt"
    "requirements_api.txt"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$config_file" ] && [ ! -f "config/$config_file" ]; then
        echo "⚙️ Moviendo config: $config_file"
        mv "$config_file" config/
    fi
done

# PASO 6: Validación post-limpieza
echo ""
echo "🔍 PASO 6: Validación post-limpieza..."
python3 verificacion_final.py > validacion_post_limpieza.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Sistema validado después de limpieza"
else
    echo "❌ Sistema con errores después de limpieza"
    echo "   Revise validacion_post_limpieza.log"
    echo "   Considere restaurar desde backup"
fi

# PASO 7: Reporte final
echo ""
echo "📊 REPORTE FINAL:"
echo "================"

# Contar archivos restantes
archivos_restantes=$(find . -maxdepth 1 -type f -name "*.py" -o -name "*.sql" -o -name "*.md" | wc -l)
echo "📄 Archivos principales restantes: $archivos_restantes"

# Mostrar estructura
echo ""
echo "📁 Nueva estructura:"
echo "├── src/ ($(find src -type f | wc -l) archivos)"
echo "├── sql/ ($(find sql -type f | wc -l) archivos)"
echo "├── docs/ ($(find docs -type f | wc -l) archivos)"
echo "├── config/ ($(find config -type f | wc -l) archivos)"
echo "├── archive/ ($(find archive -type f | wc -l) archivos)"
echo "└── scripts/ ($(find scripts -type f | wc -l) archivos)"

echo ""
echo "🎉 LIMPIEZA COMPLETADA"
echo "📝 Logs: validacion_pre_limpieza.log, validacion_post_limpieza.log"
echo "💾 Backup: backup_pre_limpieza_*.tar.gz"
