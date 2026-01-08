#!/usr/bin/env bash
#
# Script de instalación de Apache AGE en PostgreSQL 15 (Docker)
#
# Apache AGE es una extensión de PostgreSQL que agrega capacidades de grafo
# usando el lenguaje de consultas Cypher.
#
# Este script instala AGE en el contenedor Docker existente de PostgreSQL
#
# Requisitos:
# - Docker corriendo con contenedor docs_postgres
# - Usuario con permisos para ejecutar docker

set -e  # Salir si hay errores

echo "🚀 Instalación de Apache AGE en PostgreSQL 15 (Docker)"
echo "======================================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

CONTAINER_NAME="docs_postgres"

# Verificar que Docker está corriendo
echo "🐳 Verificando Docker..."
if ! docker ps >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está corriendo o no tienes permisos${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker está disponible${NC}"

# Verificar que el contenedor de PostgreSQL existe y está corriendo
echo ""
echo "📦 Verificando contenedor PostgreSQL..."
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ Contenedor ${CONTAINER_NAME} no está corriendo${NC}"
    echo "   Intenta: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ Contenedor ${CONTAINER_NAME} está corriendo${NC}"

# Verificar versión de PostgreSQL en el contenedor
PG_VERSION=$(docker exec $CONTAINER_NAME psql --version | grep -oP '\d+' | head -1)
echo "📌 Versión de PostgreSQL en contenedor: $PG_VERSION"

# Instalar dependencias en el contenedor
echo ""
echo "📦 Instalando dependencias en contenedor..."
docker exec $CONTAINER_NAME bash -c "apt-get update && apt-get install -y \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    libssl-dev \
    libpq-dev \
    postgresql-server-dev-$PG_VERSION \
    git \
    ca-certificates \
    wget \
    > /dev/null 2>&1"

echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# Clonar y compilar Apache AGE dentro del contenedor
echo ""
echo "📥 Descargando y compilando Apache AGE en contenedor..."
echo "   (Esto puede tomar 5-10 minutos...)"

docker exec $CONTAINER_NAME bash -c '
    set -e
    cd /tmp

    # Limpiar directorio anterior si existe
    rm -rf age

    # Clonar repositorio
    git clone https://github.com/apache/age.git age
    cd age

    # Usar versión estable para PostgreSQL 15
    # release/PG15/1.5.0 es la última versión estable para PG15
    git checkout release/PG15/1.5.0
    echo "Compilando versión: release/PG15/1.5.0 (compatible con PostgreSQL 15)"

    # Compilar
    make clean 2>/dev/null || true
    make PG_CONFIG=/usr/bin/pg_config

    # Instalar
    make PG_CONFIG=/usr/bin/pg_config install

    # Limpiar
    cd /
    rm -rf /tmp/age

    echo "✅ AGE compilado e instalado"
'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Apache AGE instalado en contenedor${NC}"
else
    echo -e "${RED}❌ Error al instalar Apache AGE${NC}"
    exit 1
fi

# No necesitamos modificar postgresql.conf para cargar AGE en cada sesión
# AGE se carga con LOAD 'age'; en cada sesión

# Leer credenciales del .env
echo ""
echo "🗄️  Configurando extensión en base de datos..."

if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DB_NAME=${DB_NAME:-"documentos_juridicos_gpt4"}
DB_USER=${DB_USER:-"docs_user"}
DB_PASSWORD=${DB_PASSWORD:-"docs_password_2025"}

# Crear extensión AGE en la base de datos
echo "   Creando extensión age en base de datos ${DB_NAME}..."

docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME \
    psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS age;" 2>&1 | grep -v "NOTICE" || {
    echo -e "${YELLOW}⚠️  La extensión age puede no haberse creado correctamente${NC}"
}

# Verificar instalación
echo ""
echo "🧪 Verificando instalación..."

# Test 1: Cargar extensión
docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME \
    psql -U $DB_USER -d $DB_NAME -c "LOAD 'age'; SET search_path = ag_catalog, \"\$user\", public;" 2>&1 | grep -v "SET" && {
    echo -e "${GREEN}✅ Apache AGE se carga correctamente${NC}"
} || {
    echo -e "${RED}❌ Error al cargar Apache AGE${NC}"
    exit 1
}

# Test 2: Verificar catálogo
echo "   Verificando catálogo de grafos..."
docker exec -e PGPASSWORD=$DB_PASSWORD $CONTAINER_NAME \
    psql -U $DB_USER -d $DB_NAME -c "LOAD 'age'; SET search_path = ag_catalog, \"\$user\", public; SELECT COUNT(*) FROM ag_catalog.ag_graph;" >/dev/null 2>&1 && {
    echo -e "${GREEN}✅ Catálogo de grafos accesible${NC}"
} || {
    echo -e "${YELLOW}⚠️  Catálogo no accesible (puede ser normal en primera instalación)${NC}"
}

# Resumen final
echo ""
echo "======================================================"
echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA${NC}"
echo "======================================================"
echo ""
echo "📋 Información importante:"
echo "   - Apache AGE instalado en contenedor: ${CONTAINER_NAME}"
echo "   - Base de datos: ${DB_NAME}"
echo "   - Usuario: ${DB_USER}"
echo ""
echo "📝 Para usar AGE en tus sesiones de psql:"
echo "   LOAD 'age';"
echo "   SET search_path = ag_catalog, \"\$user\", public;"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Ejecutar test de conexión:"
echo "      python3 scripts/graph_setup/02_test_age.py"
echo ""
echo "   2. Crear tu primer grafo:"
echo "      python3 scripts/graph_setup/04_populate_prototype.py"
echo ""
echo "🔧 Comandos útiles:"
echo ""
echo "   # Conectar a PostgreSQL en Docker:"
echo "   docker exec -it ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}"
echo ""
echo "   # Listar grafos (en psql):"
echo "   LOAD 'age';"
echo "   SET search_path = ag_catalog, \"\$user\", public;"
echo "   SELECT * FROM ag_catalog.ag_graph;"
echo ""
echo "📚 Documentación:"
echo "   https://age.apache.org/docs/"
echo ""