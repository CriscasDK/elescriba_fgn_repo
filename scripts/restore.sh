#!/bin/bash

# Script para restaurar backup de la base de datos
# Uso: ./scripts/restore.sh <nombre_backup>

set -e

# Verificar que se proporcionó el nombre del backup
if [ -z "$1" ]; then
    echo "❌ Error: Debes proporcionar el nombre del backup"
    echo "💡 Uso: ./scripts/restore.sh <nombre_backup>"
    echo ""
    echo "📋 Backups disponibles:"
    ls -la backups/*.sql.gz 2>/dev/null || echo "No hay backups disponibles"
    exit 1
fi

# Configuración
BACKUP_FILE="backups/$1.sql.gz"
DB_NAME="documentos_juridicos_gpt4"
DB_USER="docs_user"

# Verificar que el archivo de backup existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: El archivo de backup no existe: $BACKUP_FILE"
    echo ""
    echo "📋 Backups disponibles:"
    ls -la backups/*.sql.gz 2>/dev/null || echo "No hay backups disponibles"
    exit 1
fi

echo "🔄 Restaurando backup desde: $BACKUP_FILE"

# Confirmar la operación
read -p "⚠️ Esto eliminará todos los datos actuales. ¿Continuar? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operación cancelada"
    exit 1
fi

echo "💾 Iniciando restauración..."

# Eliminar todas las tablas existentes
echo "🗑️ Eliminando datos existentes..."
docker exec docs_postgres psql -U $DB_USER -d $DB_NAME -c "
DO \$\$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END \$\$;
"

# Restaurar el backup
echo "📥 Restaurando datos desde backup..."
gunzip -c "$BACKUP_FILE" | docker exec -i docs_postgres psql -U $DB_USER -d $DB_NAME

# Verificar la restauración
echo "✅ Verificando restauración..."
TOTAL_ROWS=$(docker exec docs_postgres psql -U $DB_USER -d $DB_NAME -t -c "
SELECT SUM(n_tup_ins) FROM pg_stat_user_tables;
" | tr -d ' ')

if [ "$TOTAL_ROWS" -gt 0 ]; then
    echo "✅ Restauración completada exitosamente"
    echo "📊 Total de registros restaurados: $TOTAL_ROWS"
    
    # Mostrar estadísticas por tabla
    echo ""
    echo "📋 Estadísticas por tabla:"
    docker exec docs_postgres psql -U $DB_USER -d $DB_NAME -c "
    SELECT 
        schemaname,
        tablename,
        n_tup_ins as registros,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamaño
    FROM pg_stat_user_tables 
    WHERE n_tup_ins > 0
    ORDER BY n_tup_ins DESC;
    "
else
    echo "❌ Error: No se restauraron datos"
    exit 1
fi

echo "🎉 ¡Restauración completada!"
