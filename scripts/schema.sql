-- 17. ESTADÍSTICAS DEL DOCUMENTO
CREATE TABLE IF NOT EXISTS estadisticas (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    normal INTEGER DEFAULT 0,
    ilegible INTEGER DEFAULT 0,
    posiblemente INTEGER DEFAULT 0,
    total_palabras INTEGER DEFAULT 0,
    porcentaje_inferencias NUMERIC(5,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_estadisticas_documento_id ON estadisticas(documento_id);
COMMENT ON TABLE estadisticas IS 'Estadísticas de procesamiento y calidad del documento.';
-- 16. METADATOS DEL DOCUMENTO
CREATE TABLE IF NOT EXISTS metadatos (
    id SERIAL PRIMARY KEY,
    documento_id INTEGER REFERENCES documentos(id) ON DELETE CASCADE,
    nuc VARCHAR(50),
    cuaderno VARCHAR(50),
    codigo VARCHAR(20),
    despacho VARCHAR(50),
    detalle TEXT,
    entidad_productora TEXT,
    serie VARCHAR(20),
    subserie VARCHAR(20),
    folio_inicial INTEGER,
    folio_final INTEGER,
    fecha_creacion TIMESTAMP,
    observaciones TEXT,
    hash_sha256 VARCHAR(64),
    firma_digital VARCHAR(255),
    timestamp_auth TIMESTAMP,
    equipo_id_auth VARCHAR(255),
    producer VARCHAR(255),
    anexos TEXT,
    authentication_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metadatos_documento_id ON metadatos(documento_id);
COMMENT ON TABLE metadatos IS 'Metadatos estructurados de cada documento, extraídos y enriquecidos por IA.';
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
    tipo_persona VARCHAR(50),
    tipo VARCHAR(50),
    descripcion TEXT,
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
    tipo VARCHAR(50),
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices importantes
CREATE INDEX idx_documentos_nuc ON documentos(nuc);
CREATE INDEX idx_documentos_archivo ON documentos(archivo);
CREATE INDEX idx_personas_nombre ON personas(nombre);
CREATE INDEX idx_personas_tipo ON personas(tipo_persona);

-- Datos de prueba
INSERT INTO documentos (archivo, nuc, estado, cuaderno, paginas, tamaño_mb) 
VALUES ('test_document.pdf', 'TEST001', 'procesado', 'Cuaderno 1', 2, 1.5);
