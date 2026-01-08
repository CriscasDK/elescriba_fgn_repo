-- BUSQUEDAS FRECUENTES Y TEMATICAS (ESTADISTICAS, PATRONES)
-- Arquitectura para preguntas frecuentes optimizadas con vistas materializadas

-- =====================================================================
-- VISTAS MATERIALIZADAS PARA CONSULTAS FRECUENTES DE ALTA PERFORMANCE
-- =====================================================================

-- Vista materializada: Top personas por tipo y frecuencia
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_personas_frecuentes AS
SELECT 
    p.tipo,
    p.nombre,
    COUNT(*) as veces_mencionada,
    COUNT(DISTINCT p.documento_id) as documentos_mencionada,
    array_agg(DISTINCT d.nuc) as casos_relacionados,
    array_agg(DISTINCT p.documento_id ORDER BY p.documento_id) as documento_ids
FROM personas p
JOIN documentos d ON p.documento_id = d.id
WHERE p.nombre IS NOT NULL AND trim(p.nombre) != ''
GROUP BY p.tipo, p.nombre
HAVING COUNT(*) > 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_personas_frecuentes 
ON mv_personas_frecuentes (tipo, nombre);

-- Vista materializada: Top organizaciones por tipo
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_organizaciones_frecuentes AS
SELECT 
    o.tipo,
    o.nombre,
    COUNT(*) as veces_mencionada,
    COUNT(DISTINCT o.documento_id) as documentos_mencionada,
    array_agg(DISTINCT d.nuc) as casos_relacionados,
    string_agg(DISTINCT o.descripcion, ' | ') as descripciones
FROM organizaciones o
JOIN documentos d ON o.documento_id = d.id
WHERE o.nombre IS NOT NULL AND trim(o.nombre) != ''
GROUP BY o.tipo, o.nombre
HAVING COUNT(*) > 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_organizaciones_frecuentes 
ON mv_organizaciones_frecuentes (tipo, nombre);

-- Vista materializada: Análisis geográfico
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lugares_frecuentes AS
SELECT 
    al.departamento,
    al.municipio,
    al.nombre,
    al.tipo,
    COUNT(*) as veces_mencionado,
    COUNT(DISTINCT al.documento_id) as documentos_mencionado,
    array_agg(DISTINCT d.nuc) as casos_relacionados
FROM analisis_lugares al
JOIN documentos d ON al.documento_id = d.id
WHERE al.nombre IS NOT NULL AND trim(al.nombre) != ''
GROUP BY al.departamento, al.municipio, al.nombre, al.tipo
HAVING COUNT(*) > 1;

CREATE INDEX IF NOT EXISTS idx_mv_lugares_departamento 
ON mv_lugares_frecuentes (departamento);
CREATE INDEX IF NOT EXISTS idx_mv_lugares_municipio 
ON mv_lugares_frecuentes (municipio);

-- Vista materializada: Estadísticas generales del caso
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_estadisticas_caso AS
SELECT 
    'resumen_general' as categoria,
    json_build_object(
        'total_documentos', (SELECT COUNT(*) FROM documentos),
        'total_personas', (SELECT COUNT(*) FROM personas),
        'total_organizaciones', (SELECT COUNT(*) FROM organizaciones),
        'total_lugares', (SELECT COUNT(*) FROM analisis_lugares),
        'personas_por_tipo', (
            SELECT json_object_agg(tipo, cantidad)
            FROM (
                SELECT COALESCE(tipo, 'sin_clasificar') as tipo, COUNT(*) as cantidad
                FROM personas 
                GROUP BY tipo
            ) t
        ),
        'organizaciones_por_tipo', (
            SELECT json_object_agg(tipo, cantidad)
            FROM (
                SELECT COALESCE(tipo, 'sin_clasificar') as tipo, COUNT(*) as cantidad
                FROM organizaciones 
                GROUP BY tipo
            ) t
        ),
        'departamentos_involucrados', (
            SELECT COUNT(DISTINCT departamento) 
            FROM analisis_lugares 
            WHERE departamento IS NOT NULL
        ),
        'municipios_involucrados', (
            SELECT COUNT(DISTINCT municipio) 
            FROM analisis_lugares 
            WHERE municipio IS NOT NULL
        )
    ) as estadisticas;

-- =====================================================================
-- CONSULTAS FRECUENTES OPTIMIZADAS (Usan las vistas materializadas)
-- =====================================================================

-- 1. Top 30 víctimas más mencionadas
SELECT nombre, veces_mencionada, documentos_mencionada, casos_relacionados
FROM mv_personas_frecuentes 
WHERE tipo LIKE '%victima%' OR tipo LIKE '%víctima%'
ORDER BY veces_mencionada DESC, nombre
LIMIT 30;

-- 2. Top 30 victimarios identificados
SELECT nombre, veces_mencionada, documentos_mencionada, casos_relacionados
FROM mv_personas_frecuentes 
WHERE tipo LIKE '%victimario%' OR tipo LIKE '%responsable%'
ORDER BY veces_mencionada DESC, nombre
LIMIT 30;

-- 3. Fuerzas legítimas más mencionadas
SELECT nombre, veces_mencionada, documentos_mencionada, descripciones
FROM mv_organizaciones_frecuentes 
WHERE tipo = 'fuerzas_legitimas'
ORDER BY veces_mencionada DESC, nombre
LIMIT 20;

-- 4. Fuerzas ilegales más mencionadas
SELECT nombre, veces_mencionada, documentos_mencionada, descripciones
FROM mv_organizaciones_frecuentes 
WHERE tipo = 'fuerzas_ilegales'
ORDER BY veces_mencionada DESC, nombre
LIMIT 20;

-- 5. Departamentos más afectados
SELECT departamento, 
       COUNT(*) as lugares_mencionados,
       SUM(veces_mencionado) as total_menciones,
       COUNT(DISTINCT municipio) as municipios_afectados
FROM mv_lugares_frecuentes
WHERE departamento IS NOT NULL
GROUP BY departamento
ORDER BY total_menciones DESC
LIMIT 15;

-- 6. Municipios más afectados por departamento
SELECT departamento, municipio, 
       COUNT(*) as lugares_especificos,
       SUM(veces_mencionado) as total_menciones
FROM mv_lugares_frecuentes
WHERE departamento IS NOT NULL AND municipio IS NOT NULL
GROUP BY departamento, municipio
ORDER BY total_menciones DESC
LIMIT 30;

-- 7. Personas de la defensa más activas
SELECT nombre, veces_mencionada, documentos_mencionada, casos_relacionados
FROM mv_personas_frecuentes 
WHERE tipo = 'defensa'
ORDER BY veces_mencionada DESC, nombre
LIMIT 20;

-- 8. Funcionarios judiciales más mencionados
SELECT nombre, veces_mencionada, documentos_mencionada, casos_relacionados
FROM mv_personas_frecuentes 
WHERE tipo LIKE '%fiscal%' OR tipo LIKE '%juez%' OR tipo LIKE '%funcionario%'
ORDER BY veces_mencionada DESC, nombre
LIMIT 25;

-- 9. Organizaciones civiles más mencionadas
SELECT nombre, veces_mencionada, documentos_mencionada, descripciones
FROM mv_organizaciones_frecuentes 
WHERE tipo = 'organizaciones_civiles' OR tipo = 'organizacion_no_gubernamental'
ORDER BY veces_mencionada DESC, nombre
LIMIT 15;

-- 10. Estadísticas generales del caso
SELECT estadisticas FROM mv_estadisticas_caso;

-- =====================================================================
-- FUNCIONES PARA REFRESCAR VISTAS MATERIALIZADAS
-- =====================================================================

-- Función para refrescar todas las vistas materializadas
CREATE OR REPLACE FUNCTION refresh_all_mv() 
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_personas_frecuentes;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_organizaciones_frecuentes;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_lugares_frecuentes;
    REFRESH MATERIALIZED VIEW mv_estadisticas_caso;
    
    -- Log del refresh
    INSERT INTO mv_refresh_log (refresh_time, status) 
    VALUES (NOW(), 'success');
EXCEPTION
    WHEN OTHERS THEN
        INSERT INTO mv_refresh_log (refresh_time, status, error_message) 
        VALUES (NOW(), 'error', SQLERRM);
        RAISE;
END;
$$ LANGUAGE plpgsql;

-- Tabla de log para refrescos
CREATE TABLE IF NOT EXISTS mv_refresh_log (
    id SERIAL PRIMARY KEY,
    refresh_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20),
    error_message TEXT
);

-- =====================================================================
-- SCHEDULER AUTOMÁTICO PARA REFRESCAR VISTAS (Ejecutar manualmente cuando sea necesario)
-- =====================================================================

-- Para refrescar manualmente durante desarrollo:
-- SELECT refresh_all_mv();
