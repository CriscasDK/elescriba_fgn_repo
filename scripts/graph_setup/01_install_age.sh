#!/usr/bin/env bash
#
# Script de instalación de Apache AGE en PostgreSQL 15
#
# Apache AGE es una extensión de PostgreSQL que agrega capacidades de grafo
# usando el lenguaje de consultas Cypher.
#
# Requisitos:
# - PostgreSQL 15 ya instalado y corriendo
# - Usuario con permisos sudo
# - Conexión a internet

set -e  # Salir si hay errores

echo "🚀 Instalación de Apache AGE para PostgreSQL 15"
echo "================================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar que PostgreSQL está corriendo
echo "📊 Verificando PostgreSQL..."
if ! systemctl is-active --quiet postgresql; then
    echo -e "${YELLOW}⚠️  PostgreSQL no está corriendo. Intentando iniciar...${NC}"
    sudo systemctl start postgresql
    sleep 2
fi

if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL está corriendo${NC}"
else
    echo -e "${RED}❌ PostgreSQL no está disponible${NC}"
    exit 1
fi

# Verificar versión de PostgreSQL
PG_VERSION=$(psql --version | grep -oP '\d+' | head -1)
echo "📌 Versión de PostgreSQL detectada: $PG_VERSION"

if [ "$PG_VERSION" != "15" ]; then
    echo -e "${YELLOW}⚠️  Apache AGE está optimizado para PostgreSQL 15${NC}"
    echo "   Tu versión: $PG_VERSION"
    read -p "¿Continuar de todas formas? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    libreadline-dev \
    zlib1g-dev \
    flex \
    bison \
    libssl-dev \
    libpq-dev \
    postgresql-server-dev-$PG_VERSION \
    git

echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# Clonar repositorio de Apache AGE
echo ""
echo "📥 Descargando Apache AGE..."
AGE_DIR="/tmp/age"
if [ -d "$AGE_DIR" ]; then
    echo "   Limpiando directorio anterior..."
    rm -rf "$AGE_DIR"
fi

git clone https://github.com/apache/age.git "$AGE_DIR"
cd "$AGE_DIR"

# Checkout de la última versión estable
echo "   Obteniendo última versión estable..."
LATEST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1))
git checkout "$LATEST_TAG"
echo "   Versión: $LATEST_TAG"

# Compilar e instalar
echo ""
echo "🔨 Compilando Apache AGE..."
echo "   (Esto puede tomar varios minutos...)"

make clean 2>/dev/null || true
make PG_CONFIG=/usr/bin/pg_config

echo ""
echo "📦 Instalando Apache AGE..."
sudo make PG_CONFIG=/usr/bin/pg_config install

echo -e "${GREEN}✅ Apache AGE compilado e instalado${NC}"

# Configurar PostgreSQL para cargar AGE
echo ""
echo "⚙️  Configurando PostgreSQL..."

PG_CONF="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
if [ -f "$PG_CONF" ]; then
    # Backup de configuración
    sudo cp "$PG_CONF" "$PG_CONF.backup_$(date +%Y%m%d_%H%M%S)"

    # Agregar AGE a shared_preload_libraries si no existe
    if ! grep -q "shared_preload_libraries.*age" "$PG_CONF"; then
        echo "   Agregando AGE a shared_preload_libraries..."
        sudo sed -i "s/#shared_preload_libraries = ''/shared_preload_libraries = 'age'/" "$PG_CONF"
        sudo sed -i "s/shared_preload_libraries = ''/shared_preload_libraries = 'age'/" "$PG_CONF"
        echo -e "${GREEN}✅ Configuración actualizada${NC}"
        NEEDS_RESTART=true
    else
        echo "   AGE ya está en shared_preload_libraries"
    fi
else
    echo -e "${YELLOW}⚠️  No se encontró $PG_CONF${NC}"
    echo "   Deberás configurar manualmente shared_preload_libraries = 'age'"
fi

# Reiniciar PostgreSQL si es necesario
if [ "$NEEDS_RESTART" = true ]; then
    echo ""
    echo "🔄 Reiniciando PostgreSQL..."
    sudo systemctl restart postgresql
    sleep 3

    if systemctl is-active --quiet postgresql; then
        echo -e "${GREEN}✅ PostgreSQL reiniciado correctamente${NC}"
    else
        echo -e "${RED}❌ Error al reiniciar PostgreSQL${NC}"
        exit 1
    fi
fi

# Crear extensión en la base de datos
echo ""
echo "🗄️  Creando extensión AGE en base de datos..."

# Leer credenciales del .env
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DB_NAME=${DB_NAME:-"documentos_juridicos_gpt4"}
DB_USER=${DB_USER:-"docs_user"}
DB_PASSWORD=${DB_PASSWORD:-"docs_password_2025"}
DB_HOST=${DB_HOST:-"localhost"}
DB_PORT=${DB_PORT:-"5432"}

# Crear extensión
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS age;" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  No se pudo crear la extensión automáticamente${NC}"
    echo "   Ejecuta manualmente:"
    echo "   psql -U $DB_USER -d $DB_NAME"
    echo "   CREATE EXTENSION age;"
}

# Verificar instalación
echo ""
echo "🧪 Verificando instalación..."

PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "LOAD 'age';" 2>/dev/null && {
    echo -e "${GREEN}✅ Apache AGE cargado correctamente${NC}"
} || {
    echo -e "${RED}❌ Error al cargar Apache AGE${NC}"
    exit 1
}

# Test básico
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT * FROM ag_catalog.ag_graph;" 2>/dev/null && {
    echo -e "${GREEN}✅ Catálogo de grafos accesible${NC}"
} || {
    echo -e "${YELLOW}⚠️  El catálogo de grafos no es accesible aún${NC}"
}

# Limpieza
echo ""
echo "🧹 Limpiando archivos temporales..."
cd /
rm -rf "$AGE_DIR"

# Resumen final
echo ""
echo "================================================"
echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA${NC}"
echo "================================================"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Ejecutar test de conexión:"
echo "      python3 scripts/graph_setup/02_test_age.py"
echo ""
echo "   2. Crear tu primer grafo:"
echo "      python3 scripts/graph_setup/04_populate_prototype.py"
echo ""
echo "📚 Documentación de Apache AGE:"
echo "   https://age.apache.org/docs/"
echo ""
echo "🔧 Comandos útiles:"
echo "   # Listar grafos:"
echo "   SELECT * FROM ag_catalog.ag_graph;"
echo ""
echo "   # Cargar extensión (en sesión psql):"
echo "   LOAD 'age';"
echo "   SET search_path = ag_catalog, \"\$user\", public;"
echo ""