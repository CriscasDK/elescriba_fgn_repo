#!/bin/bash

# Script de Sanitización Conservador - 21 Agosto 2025
# Elimina SOLO archivos claramente temporales/obsoletos
# Mantiene todo lo que pueda ser funcional

echo "🧹 Iniciando sanitización conservadora del proyecto..."
echo "=================================================="

# Crear backup antes de la limpieza
echo "📦 Creando backup de seguridad..."
tar -czf "backup_pre_sanitizacion_conservadora_$(date +%Y%m%d_%H%M%S).tar.gz" \
    --exclude='venv_docs' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='data' \
    --exclude='json_files' \
    --exclude='logs' \
    --exclude='cache' \
    --exclude='backups' \
    --exclude='archive' \
    --exclude='.git' \
    .

echo "✅ Backup creado"

# Contar archivos antes
archivos_antes=$(find . -maxdepth 1 -type f -name "*.py" | wc -l)
echo "📊 Scripts Python antes: $archivos_antes"

echo ""
echo "🗑️ Eliminando archivos claramente temporales..."

# 1. Tests RAG (claramente temporales)
echo "   📝 Eliminando tests RAG temporales..."
rm -f test_rag_azure_configurado.py
rm -f test_rag_azure_search.py
rm -f test_rag_directo.py
rm -f test_rag_progreso.py
rm -f test_rag_puro.py
rm -f test_rag_simple.py
rm -f test_rag_ultra_simple.py
rm -f test_rag_union_patriotica.py
rm -f test_up_rag.py
rm -f test_azure_funcionando.py

# 2. Diagnósticos temporales
echo "   🔍 Eliminando diagnósticos temporales..."
rm -f diagnostico_azure_search.py
rm -f diagnostico_busqueda_semantica.py
rm -f diagnostico_cambio_victimas.py
rm -f diagnostico_upload.py
rm -f diagnostico_vectores_final.py
rm -f diagnostico_vectorizacion.py
rm -f diagnostico_vectorizacion_optimizado.py

# 3. Interfaces de backup (claramente obsoletas)
echo "   💾 Eliminando interfaces de backup obsoletas..."
rm -f interfaz_fiscales_backup.py
rm -f interfaz_fiscales_backup_20250801_065515.py
rm -f interfaz_fiscales_backup_20250813_153346.py
rm -f interfaz_fiscales_backup_antes_mejoras.py
rm -f interfaz_fiscales_d4f47c2.py
rm -f interfaz_fiscales_ffcf89f.py
rm -f interfaz_fiscales_original.py
rm -f interfaz_fiscales_restored.py
rm -f interfaz_fiscalia.py

# 4. Frontends temporales
echo "   🖥️ Eliminando frontends temporales..."
rm -f frontend_debug_simple.py
rm -f frontend_victimas.py
rm -f frontend_victimas_agrupadas.py
rm -f frontend_victimas_mejorado.py
rm -f frontend_victimas_robusto.py
rm -f frontend_victimas_simple.py
rm -f frontend_victimas_tabla.py

# 5. APIs obsoletas
echo "   🚀 Eliminando APIs obsoletas..."
rm -f api_rag_endpoint.py
rm -f api_rag_mejorada.py
rm -f api_rag_vectorizada.py
rm -f interfaz_rag_vectorizada.py
rm -f interfaz_simple_api.py
rm -f rag_vectorizado.py

# 6. Archivos de output temporales
echo "   📄 Eliminando archivos de output temporales..."
rm -f vectorizacion_completa.out
rm -f resultados_optimizacion_chunks.json
rm -f test_metadatos_completos_20250819_*.json

# 7. Interfaces de chatbot temporales
echo "   💬 Eliminando interfaces de chatbot temporales..."
rm -f interfaz_chatbot_avanzada.py
rm -f interfaz_chatbot_legal.py
rm -f mejoras_interfaz_rag.py

# 8. Scripts de ejemplo/tutorial
echo "   📚 Eliminando ejemplos y tutoriales temporales..."
rm -f ejemplo_semantic_kernel_gpt41.py
rm -f tutorial_consultas_didactico.py

# 9. Archivos de investigación temporal
echo "   🔬 Eliminando archivos de investigación temporal..."
rm -f investigar_diversidad.py
rm -f comparacion_consultas_victimas.py

# 10. Reportes temporales
echo "   📊 Eliminando reportes temporales..."
rm -f reporte_victimas_simple.py
rm -f reporte_victimas_validacion.ipynb

# 11. Limpiar archivos de script temporal
echo "   🛠️ Eliminando scripts temporales..."
rm -f estado_sistema.sh
rm -f generar_reporte.sh
rm -f limpiar_proyecto.sh
rm -f run_sadtalker.sh

# Contar archivos después
archivos_despues=$(find . -maxdepth 1 -type f -name "*.py" | wc -l)
archivos_eliminados=$((archivos_antes - archivos_despues))

echo ""
echo "✅ Sanitización conservadora completada"
echo "📊 Scripts Python eliminados: $archivos_eliminados"
echo "📊 Scripts Python restantes: $archivos_despues"

echo ""
echo "📁 Scripts importantes CONSERVADOS:"
echo "   ✅ interfaz_principal.py - Interfaz principal de víctimas"
echo "   ✅ clasificador_inteligente_llm.py - Clasificador usado por interfaz"
echo "   ✅ procesar_masivo.py - Procesamiento masivo"
echo "   ✅ src/ - Todo el sistema RAG reorganizado"
echo "   ✅ start_all_services.sh - Script de inicio unificado"
echo "   ✅ test_api.py - Test principal de API"

echo ""
echo "🗑️ Limpieza adicional..."

# Limpiar __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "   ✅ __pycache__ limpiado"

# Limpiar cache si existe
if [ -d "cache" ]; then
    rm -rf cache/* 2>/dev/null
    echo "   ✅ Cache limpiado"
fi

# Limpiar logs antiguos (mantener solo los últimos 3)
if [ -d "logs" ]; then
    cd logs
    ls -t *.log 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null
    cd ..
    echo "   ✅ Logs antiguos limpiados"
fi

echo ""
echo "📋 Estructura final del proyecto:"
ls -la | grep -E "^d|interfaz_principal.py|clasificador|src|start_all|test_api.py|requirements"

echo ""
echo "🎉 Proyecto sanitizado CONSERVADORAMENTE!"
echo "   💾 Backup: backup_pre_sanitizacion_conservadora_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "   🚀 Sistema listo: ./start_all_services.sh"
echo "   ⚠️ Todo lo funcional se mantiene intacto"
