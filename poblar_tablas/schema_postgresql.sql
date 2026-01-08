-- Schema PostgreSQL generado automáticamente
-- Tabla principal para documentos judiciales

CREATE TABLE IF NOT EXISTS documentos_judiciales (
    id SERIAL PRIMARY KEY,
    archivo_json VARCHAR(255) NOT NULL,
    fecha_insercion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archivo VARCHAR(255) NOT NULL,
    ruta VARCHAR(255) NOT NULL,
    procesado VARCHAR(255) NOT NULL,
    estado VARCHAR(255) NOT NULL,
    texto_extraido TEXT NOT NULL,
    analisis TEXT NOT NULL,
    paginas INTEGER NOT NULL,
    tamaño_mb NUMERIC NOT NULL,
    costo_estimado NUMERIC NOT NULL,
    procesamiento_batch BOOLEAN NOT NULL,
    equipo_id VARCHAR(255) NOT NULL,
    usuario VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    pdf_buscable_original VARCHAR(255) NOT NULL,
    pdf_buscable_batch VARCHAR(255) NOT NULL
);

-- Índices recomendados
CREATE INDEX IF NOT EXISTS idx_documentos_archivo ON documentos_judiciales(archivo);
CREATE INDEX IF NOT EXISTS idx_documentos_nuc ON documentos_judiciales(nuc);
CREATE INDEX IF NOT EXISTS idx_documentos_procesado ON documentos_judiciales(procesado);