#!/bin/bash

# Script para crear backup de la base de datos
# Uso: ./scripts/backup.sh [nombre_backup]

set -e

# Configuración
BACKUP_DIR="backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME=${1:-"backup_${DATE}"}
DB_NAME="documentos_juridicos_gpt4"
DB_USER="docs_user"

# Crear directorio de backups si no existe
mkdir -p $BACKUP_DIR

echo "💾 Creando backup de la base de datos..."
echo "📁 Archivo: ${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"

# Crear backup comprimido
docker exec docs_postgres pg_dump -U $DB_USER -d $DB_NAME | gzip > "${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"

# Verificar que el backup se creó correctamente
if [ -f "${BACKUP_DIR}/${BACKUP_NAME}.sql.gz" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.sql.gz" | cut -f1)
    echo "✅ Backup creado exitosamente"
    echo "📊 Tamaño: $BACKUP_SIZE"
    
    # Listar backups existentes
    echo ""
    echo "📋 Backups disponibles:"
    ls -lah $BACKUP_DIR/*.sql.gz 2>/dev/null || echo "No hay backups previos"
    
    # Limpiar backups antiguos (mantener solo los últimos 10)
    if [ $(ls $BACKUP_DIR/*.sql.gz 2>/dev/null | wc -l) -gt 10 ]; then
        echo "🧹 Limpiando backups antiguos..."
        ls -t $BACKUP_DIR/*.sql.gz | tail -n +11 | xargs rm -f
        echo "✅ Backups antiguos eliminados"
    fi
    
else
    echo "❌ Error al crear el backup"
    exit 1
fi

echo "🎉 ¡Backup completado!"
