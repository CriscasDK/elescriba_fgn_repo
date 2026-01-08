-- Script de migración para metadatos completos
-- Generado automáticamente desde archivos JSON

ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS archivo_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS ruta_completa VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS fecha_creacion_original TIMESTAMP;
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS nuc_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS cuaderno_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS codigo_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS despacho_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS detalle_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS entidad_productora_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS serie_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS subserie_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS observaciones_original VARCHAR(500);
ALTER TABLE metadatos ADD COLUMN IF NOT EXISTS version_procesamiento VARCHAR(500);

-- Indices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_metadatos_fecha_original ON metadatos(fecha_creacion_original);
CREATE INDEX IF NOT EXISTS idx_metadatos_nuc_original ON metadatos(nuc_original);
CREATE INDEX IF NOT EXISTS idx_metadatos_despacho_original ON metadatos(despacho_original);
