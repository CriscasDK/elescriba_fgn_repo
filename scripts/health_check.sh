#!/bin/bash

# Script de verificación de salud del sistema
# Uso: ./scripts/health_check.sh

set -e

echo "🏥 Verificación de salud del sistema ETL + RAG"
echo "============================================="

# Verificar servicios Docker
echo "🐳 Verificando servicios Docker..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Servicios Docker activos"
    docker-compose ps
else
    echo "❌ Servicios Docker no están corriendo"
    echo "💡 Ejecuta: docker-compose up -d"
    exit 1
fi

echo ""

# Verificar PostgreSQL
echo "🗄️ Verificando PostgreSQL..."
if docker exec docs_postgres pg_isready -U docs_user -d documentos_juridicos_gpt4 >/dev/null 2>&1; then
    echo "✅ PostgreSQL está activo"
    
    # Estadísticas de la base de datos
    echo "📊 Estadísticas de entidades:"
    docker exec -it docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "
    SELECT 
        'personas' as tabla, 
        COUNT(*) as total,
        COUNT(CASE WHEN tipo IS NOT NULL THEN 1 END) as clasificadas
    FROM personas
    UNION ALL
    SELECT 
        'organizaciones' as tabla, 
        COUNT(*) as total,
        COUNT(CASE WHEN tipo IS NOT NULL THEN 1 END) as clasificadas
    FROM organizaciones
    UNION ALL
    SELECT 'lugares' as tabla, COUNT(*) as total, COUNT(*) as clasificadas FROM lugares
    UNION ALL
    SELECT 'cargos_roles' as tabla, COUNT(*) as total, COUNT(*) as clasificadas FROM cargos_roles;
    "
else
    echo "❌ PostgreSQL no está disponible"
    exit 1
fi

echo ""

# Verificar ambiente Python
echo "🐍 Verificando ambiente Python..."
if [ -d "venv_docs" ]; then
    echo "✅ Ambiente virtual existe"
    source venv_docs/bin/activate
    
    echo "📦 Paquetes instalados:"
    pip list | grep -E "(openai|psycopg2|pandas)"
    
    deactivate
else
    echo "❌ Ambiente virtual no encontrado"
    echo "💡 Ejecuta: python3.12 -m venv venv_docs && source venv_docs/bin/activate && pip install -r requirements.txt"
fi

echo ""

# Verificar archivos de configuración
echo "⚙️ Verificando configuración..."
if [ -f ".env.gpt41" ]; then
    echo "✅ Archivo de configuración encontrado"
    echo "🔑 Variables configuradas:"
    grep -E "^[A-Z]" .env.gpt41 | cut -d'=' -f1 | sed 's/^/  - /'
else
    echo "❌ Archivo .env.gpt41 no encontrado"
    echo "💡 Copia .env.example a .env.gpt41 y configura tus credenciales"
fi

echo ""

# Verificar logs recientes
echo "📝 Verificando logs recientes..."
if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
    echo "✅ Logs encontrados"
    echo "📄 Archivos de log recientes:"
    ls -la logs/ | tail -5
    
    # Mostrar últimas líneas del log más reciente
    LATEST_LOG=$(ls -t logs/*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "🔍 Últimas 5 líneas del log más reciente:"
        tail -5 "$LATEST_LOG"
    fi
else
    echo "⚠️ No se encontraron logs recientes"
fi

echo ""

# Resumen final
echo "🎯 RESUMEN DE SALUD:"
echo "==================="

# Verificar si todo está OK
HEALTH_SCORE=0

if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker Services: OK"
    ((HEALTH_SCORE++))
else
    echo "❌ Docker Services: FAIL"
fi

if docker exec docs_postgres pg_isready -U docs_user -d documentos_juridicos_gpt4 >/dev/null 2>&1; then
    echo "✅ PostgreSQL: OK"
    ((HEALTH_SCORE++))
else
    echo "❌ PostgreSQL: FAIL"
fi

if [ -d "venv_docs" ]; then
    echo "✅ Python Environment: OK"
    ((HEALTH_SCORE++))
else
    echo "❌ Python Environment: FAIL"
fi

if [ -f ".env.gpt41" ]; then
    echo "✅ Configuration: OK"
    ((HEALTH_SCORE++))
else
    echo "❌ Configuration: FAIL"
fi

echo ""
if [ $HEALTH_SCORE -eq 4 ]; then
    echo "🎉 ¡Sistema completamente saludable! Listo para procesar."
    exit 0
elif [ $HEALTH_SCORE -ge 2 ]; then
    echo "⚠️ Sistema parcialmente funcional. Revisa los elementos marcados como FAIL."
    exit 1
else
    echo "🚨 Sistema requiere configuración. Muchos componentes fallan."
    exit 2
fi
