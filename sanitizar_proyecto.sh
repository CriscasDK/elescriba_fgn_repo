#!/bin/bash

# Script de Sanitización del Proyecto - 21 Agosto 2025
# Elimina archivos de prueba, temporales y duplicados
# Mantiene solo los archivos esenciales y de documentación actual

echo "🧹 Iniciando sanitización del proyecto..."
echo "======================================"

# Crear backup antes de la limpieza
echo "📦 Creando backup de seguridad..."
tar -czf "backup_pre_sanitizacion_$(date +%Y%m%d_%H%M%S).tar.gz" \
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
archivos_antes=$(find . -maxdepth 1 -type f | wc -l)
echo "📊 Archivos antes: $archivos_antes"

echo ""
echo "🗑️ Eliminando archivos de prueba y temporales..."

# 1. Scripts de prueba RAG
echo "   Eliminando scripts de prueba RAG..."
rm -f test_rag_*.py
rm -f test_azure_*.py
rm -f test_up_rag.py
rm -f diagnostico_*.py
rm -f verificacion_*.py
rm -f prueba_*.py

# 2. Scripts de vectorización temporales
echo "   Eliminando scripts de vectorización temporales..."
rm -f vectorizacion_*.py
rm -f fase1_vectorizacion*.py
rm -f migracion_*.py
rm -f poblar_metadatos*.py
rm -f continuar_migracion*.py

# 3. Scripts de análisis temporales
echo "   Eliminando scripts de análisis temporales..."
rm -f analisis_*.py
rm -f analizar_*.py
rm -f mapear_*.py
rm -f investigar_*.py
rm -f inspeccionar_*.py

# 4. Scripts de corrección puntuales
echo "   Eliminando scripts de corrección puntuales..."
rm -f corregir_*.py
rm -f actualizar_*.py
rm -f fix_*.sql
rm -f crear_*.py
rm -f optimizar_*.py

# 5. Monitores temporales
echo "   Eliminando monitores temporales..."
rm -f monitor_*.py
rm -f check_*.py

# 6. APIs y frontends de prueba
echo "   Eliminando APIs y frontends de prueba..."
rm -f api_rag_*.py
rm -f frontend_*.py
rm -f interfaz_rag_*.py
rm -f interfaz_chatbot_*.py
rm -f interfaz_simple_*.py
rm -f mejoras_interfaz_*.py

# 7. Backups de interfaces
echo "   Eliminando backups de interfaces..."
rm -f interfaz_fiscales_backup*.py
rm -f interfaz_fiscales_*.py
rm -f interfaz_fiscalia.py

# 8. Archivos de tutorial y ejemplo
echo "   Eliminando tutoriales y ejemplos temporales..."
rm -f tutorial_*.py
rm -f ejemplo_*.py
rm -f generar_*.py
rm -f reporte_*.py

# 9. Archivos de configuración duplicados
echo "   Eliminando configuraciones duplicadas..."
rm -f requirements-*.txt
rm -f requirements_*.txt

# 10. Archivos SQL temporales
echo "   Eliminando SQL temporales..."
rm -f consulta_*.sql
rm -f consultas_*.sql
rm -f migracion_*.sql

# 11. Archivos de respaldo específicos
echo "   Eliminando archivos de respaldo específicos..."
rm -f backup_*.py
rm -f *_backup.py
rm -f *_restored.py
rm -f *_original.py

# 12. Archivos de resultado temporales
echo "   Eliminando resultados temporales..."
rm -f resultados_*.json
rm -f test_metadatos_*.json
rm -f *.out

# 13. Scripts de procesamiento masivo temporales
echo "   Eliminando scripts de procesamiento temporales..."
rm -f procesar_masivo.py
rm -f buscar_vectorizados.py
rm -f habilitar_listado.py
rm -f trazabilidad_100_DEFINITIVO.py

# 14. Scripts de sistema temporales
echo "   Eliminando scripts de sistema temporales..."
rm -f estado_sistema.sh
rm -f generar_reporte.sh
rm -f limpiar_proyecto.sh

# 15. Archivos de test específicos
echo "   Eliminando archivos de test específicos..."
rm -f test_nuevas_consultas.md

# Contar archivos después
archivos_despues=$(find . -maxdepth 1 -type f | wc -l)
archivos_eliminados=$((archivos_antes - archivos_despues))

echo ""
echo "✅ Sanitización completada"
echo "📊 Archivos eliminados: $archivos_eliminados"
echo "📊 Archivos restantes: $archivos_despues"

echo ""
echo "📁 Archivos principales conservados:"
echo "   ✅ interfaz_principal.py - Interfaz principal"
echo "   ✅ src/ - Sistema RAG completo"
echo "   ✅ config/ - Configuraciones"
echo "   ✅ templates/ - Templates HTML"
echo "   ✅ scripts/ - Scripts SQL esenciales"
echo "   ✅ docs/ - Documentación técnica"
echo "   ✅ start_all_services.sh - Script de inicio"
echo "   ✅ test_api.py - Test principal de API"
echo "   ✅ Documentación actual (DOCUMENTACION_*, GUIA_*, RESUMEN_*)"

echo ""
echo "🗑️ Limpiando directorios temporales..."

# Limpiar cache si existe
if [ -d "cache" ]; then
    rm -rf cache/*
    echo "   ✅ Cache limpiado"
fi

# Limpiar __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
echo "   ✅ __pycache__ limpiado"

# Limpiar logs antiguos (mantener solo los últimos 5)
if [ -d "logs" ]; then
    cd logs
    ls -t *.log 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
    cd ..
    echo "   ✅ Logs antiguos limpiados"
fi

echo ""
echo "📋 Estructura final del proyecto:"
echo "   📁 src/ - Sistema RAG y APIs"
echo "   📁 config/ - Configuraciones"
echo "   📁 templates/ - Templates web"
echo "   📁 scripts/ - Scripts SQL"
echo "   📁 docs/ - Documentación"
echo "   📁 data/ - Datos PostgreSQL"
echo "   📁 venv_docs/ - Ambiente virtual"
echo "   📄 interfaz_principal.py - Interfaz principal"
echo "   📄 *.md - Documentación actual"
echo "   📄 requirements.txt - Dependencias"
echo "   📄 start_all_services.sh - Inicio de servicios"

echo ""
echo "🎉 Proyecto sanitizado exitosamente!"
echo "   💾 Backup: backup_pre_sanitizacion_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "   🚀 Listo para usar: ./start_all_services.sh"
