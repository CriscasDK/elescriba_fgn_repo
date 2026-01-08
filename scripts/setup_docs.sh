#!/bin/bash

# Script de setup completo para el proyecto de documentos judiciales
# Ubicación: /home/lab4/scripts/documentos_judiciales

echo "🚀 Configurando proyecto de documentos judiciales..."

# Variables de configuración
PROJECT_DIR="/home/lab4/scripts/documentos_judiciales"
DB_NAME="documentos_juridicos"
DB_USER="docs_user"
DB_PASSWORD="docs_password_2025"
PGADMIN_EMAIL="admin@docs.local"
PGADMIN_PASSWORD="admin_2025"

# Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

mkdir -p {data/postgres,data/pgadmin,json_files,logs,scripts}

echo "✅ Directorios creados en: $PROJECT_DIR"

# Crear docker-compose.yml
echo "🐳 Creando docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    container_name: docs_postgres
    environment:
      POSTGRES_DB: documentos_juridicos
      POSTGRES_USER: docs_user
      POSTGRES_PASSWORD: docs_password_2025
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/01-init.sql
      - ./scripts/schema.sql:/docker-entrypoint-initdb.d/02-schema.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U docs_user -d documentos_juridicos"]
      interval: 10s
      timeout: 5s
      retries: 5

  # PgAdmin para administrar la BD
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: docs_pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@docs.local
      PGADMIN_DEFAULT_PASSWORD: admin_2025
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    volumes:
      - ./data/pgadmin:/var/lib/pgadmin
    ports:
      - "8080:80"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

networks:
  default:
    name: docs_network
EOF

# Crear script de inicialización de BD
echo "📋 Creando script de inicialización..."
cat > scripts/init.sql << 'EOF'
-- Script de inicialización de base de datos
-- Se ejecuta automáticamente al crear el contenedor

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Configurar timezone
SET timezone = 'America/Bogota';

-- Log de inicialización
DO $$
BEGIN
    RAISE NOTICE 'Base de datos documentos_juridicos inicializada correctamente';
    RAISE NOTICE 'Usuario: docs_user';
    RAISE NOTICE 'Timezone configurado: America/Bogota';
END $$;
EOF

# Crear schema completo
echo "🗄️ Creando schema de base de datos..."
cat > scripts/schema.sql << 'EOF'
-- Esquema para base de datos de documentos jurídicos
-- Basado en los JSONs procesados por GPT-4

-- Tabla principal de documentos
CREATE TABLE documentos (
    id SERIAL PRIMARY KEY,
    archivo VARCHAR(255) NOT NULL,
    ruta TEXT,
    nuc VARCHAR(50),
    procesado TIMESTAMP,
    estado VARCHAR(100),
    cuaderno VARCHAR(50),
    codigo VARCHAR(20),
    despacho VARCHAR(10),
    entidad_productora VARCHAR(255),
    serie VARCHAR(10),
    subserie VARCHAR(10),
    folio_inicial INTEGER,
    folio_final INTEGER,
    paginas INTEGER,
    tamaño_mb DECIMAL(10,2),
    costo_estimado DECIMAL(10,4),
    hash_sha256 VARCHAR(64) UNIQUE,
    texto_extraido TEXT,
    analisis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de personas extraídas
CREATE TABLE personas (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    tipo_persona VARCHAR(50), -- victima, victimario, testigo, funcionario, etc.
    cedula VARCHAR(20),
    alias VARCHAR(255),
    lugar_nacimiento VARCHAR(255),
    fecha_nacimiento DATE,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de organizaciones
CREATE TABLE organizaciones (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50), -- legal, ilegal, estatal, etc.
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de lugares mencionados
CREATE TABLE lugares (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(50), -- municipio, corregimiento, direccion, etc.
    departamento VARCHAR(100),
    coordenadas POINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de fechas importantes
CREATE TABLE fechas_relevantes (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    tipo_evento VARCHAR(100), -- hecho, informe, resolucion, etc.
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de datos de contacto
CREATE TABLE contactos (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    tipo VARCHAR(50), -- telefono, email, direccion
    valor VARCHAR(255),
    entidad VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de números de identificación/referencia
CREATE TABLE referencias (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    tipo VARCHAR(50), -- expediente, oficio, resolucion, etc.
    numero VARCHAR(100),
    año INTEGER,
    entidad VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de delitos mencionados
CREATE TABLE delitos (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    tipo_delito VARCHAR(100),
    fecha_hecho DATE,
    lugar_hecho VARCHAR(255),
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar performance
CREATE INDEX idx_documentos_nuc ON documentos(nuc);
CREATE INDEX idx_documentos_archivo ON documentos(archivo);
CREATE INDEX idx_documentos_hash ON documentos(hash_sha256);
CREATE INDEX idx_personas_nombre ON personas(nombre);
CREATE INDEX idx_personas_tipo ON personas(tipo_persona);
CREATE INDEX idx_personas_cedula ON personas(cedula);
CREATE INDEX idx_organizaciones_nombre ON organizaciones(nombre);
CREATE INDEX idx_lugares_nombre ON lugares(nombre);
CREATE INDEX idx_fechas_fecha ON fechas_relevantes(fecha);
CREATE INDEX idx_referencias_numero ON referencias(numero);

-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar timestamp en documentos
CREATE TRIGGER update_documentos_updated_at 
    BEFORE UPDATE ON documentos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insertar datos de prueba
INSERT INTO documentos (archivo, nuc, estado, cuaderno, paginas, tamaño_mb) 
VALUES ('test_document.pdf', 'TEST001', 'procesado', 'Cuaderno 1', 2, 1.5);

-- Log de creación del schema
DO $$
BEGIN
    RAISE NOTICE 'Schema creado correctamente con % tablas', 
        (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public');
END $$;
EOF

# Crear script de control
echo "⚙️ Creando scripts de control..."
cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 Iniciando servicios de documentos judiciales..."
docker-compose up -d

echo "⏳ Esperando que PostgreSQL esté listo..."
sleep 10

echo "✅ Servicios iniciados:"
echo "📊 PostgreSQL: localhost:5432"
echo "🖥️ PgAdmin: http://localhost:8080"
echo ""
echo "Credenciales PgAdmin:"
echo "  Email: admin@docs.local"
echo "  Password: admin_2025"
echo ""
echo "Credenciales PostgreSQL:"
echo "  Host: localhost"
echo "  Puerto: 5432"
echo "  Base de datos: documentos_juridicos"
echo "  Usuario: docs_user"
echo "  Password: docs_password_2025"
EOF

cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Deteniendo servicios..."
docker-compose down
echo "✅ Servicios detenidos"
EOF

cat > logs.sh << 'EOF'
#!/bin/bash
echo "📋 Logs de PostgreSQL:"
docker-compose logs postgres
echo ""
echo "📋 Logs de PgAdmin:"
docker-compose logs pgadmin
EOF

cat > status.sh << 'EOF'
#!/bin/bash
echo "📊 Estado de servicios:"
docker-compose ps
echo ""
echo "💾 Uso de espacio:"
du -sh data/
echo ""
echo "🔗 URLs:"
echo "  PgAdmin: http://localhost:8080"
echo "  PostgreSQL: localhost:5432"
EOF

# Hacer scripts ejecutables
chmod +x *.sh

# Crear archivo de conexión para Python
echo "🐍 Creando configuración Python..."
cat > db_config.py << 'EOF'
# Configuración de base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'documentos_juridicos',
    'user': 'docs_user',
    'password': 'docs_password_2025',
    'port': '5432'
}

# URL de conexión para SQLAlchemy
DATABASE_URL = "postgresql://docs_user:docs_password_2025@localhost:5432/documentos_juridicos"

# Configuración de Ollama
OLLAMA_CONFIG = {
    'host': 'http://localhost:11434',
    'model': 'deepseek-r1:14b'
}
EOF

# Crear requirements.txt
cat > requirements.txt << 'EOF'
psycopg2-binary==2.9.9
ollama==0.1.9
sqlalchemy==2.0.23
pandas==2.1.4
python-dotenv==1.0.0
tqdm==4.66.1
jsonschema==4.20.0
EOF

echo ""
echo "🎉 ¡Setup completado!"
echo "📁 Proyecto creado en: $PROJECT_DIR"
echo ""
echo "🚀 Para iniciar los servicios:"
echo "   cd $PROJECT_DIR"
echo "   ./start.sh"
echo ""
echo "🔗 Accesos:"
echo "   PgAdmin: http://localhost:8080"
echo "   PostgreSQL: localhost:5432"
echo ""
echo "📦 Para instalar dependencias Python:"
echo "   pip3 install -r requirements.txt"
