#!/bin/bash

# Script para configurar la base de datos inicial
# Uso: ./scripts/setup_database.sh

set -e

echo "🗄️ Configurando base de datos PostgreSQL..."

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a que PostgreSQL esté disponible..."
until docker exec docs_postgres pg_isready -U docs_user -d documentos_juridicos_gpt4; do
  sleep 2
done

echo "✅ PostgreSQL está listo"

# Ejecutar schema inicial
echo "📋 Creando esquema de base de datos..."
docker exec -i docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 < scripts/schema.sql

echo "✅ Base de datos configurada exitosamente"

# Mostrar estadísticas
echo "📊 Estadísticas iniciales:"
docker exec -it docs_postgres psql -U docs_user -d documentos_juridicos_gpt4 -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

echo "🎉 ¡Setup completado!"
