-- =====================================================================
-- ARQUITECTURA HÍBRIDA: CONSULTAS FRECUENTES + RAG
-- =====================================================================
-- Estrategia dual:
-- 1. VISTAS MATERIALIZADAS para preguntas frecuentes (performance)
-- 2. FUNCIONES SQL para RAG (flexibilidad)

-- =====================================================================
-- EXTENSIONES NECESARIAS
-- =====================================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- =====================================================================
-- VISTAS MATERIALIZADAS PARA CONSULTAS FRECUENTES
-- =====================================================================

-- VM1: Dashboard principal - Métricas clave del caso
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_principal AS
SELECT 
    json_build_object(
        'total_documentos', (SELECT COUNT(*) FROM documentos),
        'total_personas', (SELECT COUNT(DISTINCT nombre) FROM personas),
        'total_organizaciones', (SELECT COUNT(DISTINCT nombre) FROM organizaciones),
        'total_lugares', (SELECT COUNT(DISTINCT nombre) FROM analisis_lugares),
        'casos_unicos', (SELECT COUNT(DISTINCT nuc) FROM documentos WHERE nuc IS NOT NULL),
        'ultima_actualizacion', NOW(),
        'progreso_procesamiento', ROUND((SELECT COUNT(*) FROM documentos) * 100.0 / 11446, 2),
        'entidades_por_tipo', json_build_object(
            'victimas', (SELECT COUNT(*) FROM personas WHERE tipo LIKE '%victima%'),
            'victimarios', (SELECT COUNT(*) FROM personas WHERE tipo LIKE '%victimario%'),
            'defensa', (SELECT COUNT(*) FROM personas WHERE tipo = 'defensa'),
            'fiscales', (SELECT COUNT(*) FROM personas WHERE tipo LIKE '%fiscal%'),
            'fuerzas_legitimas', (SELECT COUNT(*) FROM organizaciones WHERE tipo = 'fuerzas_legitimas'),
            'fuerzas_ilegales', (SELECT COUNT(*) FROM organizaciones WHERE tipo = 'fuerzas_ilegales')
        )
    ) as metricas_dashboard;

-- VM2: Top entidades más mencionadas (para autocomplete y sugerencias)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_entidades AS
-- Top personas
SELECT 
    'persona' as tipo_entidad,
    p.nombre as entidad,
    p.tipo as subtipo,
    COUNT(*) as frecuencia,
    COUNT(DISTINCT p.documento_id) as documentos,
    'frecuente' as tag
FROM personas p
WHERE p.nombre IS NOT NULL AND trim(p.nombre) != ''
GROUP BY p.nombre, p.tipo
HAVING COUNT(*) >= 5

UNION ALL

-- Top organizaciones
SELECT 
    'organizacion' as tipo_entidad,
    o.nombre as entidad,
    o.tipo as subtipo,
    COUNT(*) as frecuencia,
    COUNT(DISTINCT o.documento_id) as documentos,
    'frecuente' as tag
FROM organizaciones o
WHERE o.nombre IS NOT NULL AND trim(o.nombre) != ''
GROUP BY o.nombre, o.tipo
HAVING COUNT(*) >= 3

UNION ALL

-- Top lugares
SELECT 
    'lugar' as tipo_entidad,
    al.nombre as entidad,
    COALESCE(al.departamento, al.municipio, 'sin_ubicacion') as subtipo,
    COUNT(*) as frecuencia,
    COUNT(DISTINCT al.documento_id) as documentos,
    'frecuente' as tag
FROM analisis_lugares al
WHERE al.nombre IS NOT NULL AND trim(al.nombre) != ''
GROUP BY al.nombre, COALESCE(al.departamento, al.municipio, 'sin_ubicacion')
HAVING COUNT(*) >= 3

ORDER BY frecuencia DESC;

CREATE INDEX IF NOT EXISTS idx_mv_top_entidades_tipo ON mv_top_entidades (tipo_entidad);
CREATE INDEX IF NOT EXISTS idx_mv_top_entidades_frecuencia ON mv_top_entidades (frecuencia DESC);

-- VM3: Análisis geográfico por departamento
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_analisis_geografico AS
SELECT 
    al.departamento,
    COUNT(DISTINCT al.nombre) as lugares_especificos,
    COUNT(DISTINCT al.municipio) as municipios_afectados,
    COUNT(*) as total_menciones,
    COUNT(DISTINCT al.documento_id) as documentos_involucrados,
    COUNT(DISTINCT d.nuc) as casos_involucrados,
    json_agg(DISTINCT al.municipio ORDER BY al.municipio) FILTER (WHERE al.municipio IS NOT NULL) as municipios_lista,
    -- Top 5 lugares más mencionados por departamento
    (
        SELECT json_agg(
            json_build_object('lugar', nombre, 'menciones', cnt) ORDER BY cnt DESC
        )
        FROM (
            SELECT al2.nombre, COUNT(*) as cnt
            FROM analisis_lugares al2
            WHERE al2.departamento = al.departamento
            GROUP BY al2.nombre
            ORDER BY cnt DESC
            LIMIT 5
        ) top_lugares
    ) as top_lugares
FROM analisis_lugares al
JOIN documentos d ON al.documento_id = d.id
WHERE al.departamento IS NOT NULL
GROUP BY al.departamento
ORDER BY total_menciones DESC;

-- VM4: Red de conexiones frecuentes (para visualizaciones)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_red_conexiones AS
-- Conexiones persona-persona
SELECT 
    'persona-persona' as tipo_conexion,
    p1.nombre as entidad_1,
    p2.nombre as entidad_2,
    p1.tipo as tipo_1,
    p2.tipo as tipo_2,
    COUNT(DISTINCT p1.documento_id) as fuerza_conexion,
    'co-ocurrencia' as naturaleza_conexion
FROM personas p1
JOIN personas p2 ON p1.documento_id = p2.documento_id AND p1.id < p2.id
WHERE p1.nombre != p2.nombre
GROUP BY p1.nombre, p2.nombre, p1.tipo, p2.tipo
HAVING COUNT(DISTINCT p1.documento_id) >= 3

UNION ALL

-- Conexiones persona-organizacion
SELECT 
    'persona-organizacion' as tipo_conexion,
    p.nombre as entidad_1,
    o.nombre as entidad_2,
    p.tipo as tipo_1,
    o.tipo as tipo_2,
    COUNT(DISTINCT p.documento_id) as fuerza_conexion,
    'asociacion' as naturaleza_conexion
FROM personas p
JOIN organizaciones o ON p.documento_id = o.documento_id
GROUP BY p.nombre, o.nombre, p.tipo, o.tipo
HAVING COUNT(DISTINCT p.documento_id) >= 2

UNION ALL

-- Conexiones organizacion-lugar
SELECT 
    'organizacion-lugar' as tipo_conexion,
    o.nombre as entidad_1,
    al.nombre as entidad_2,
    o.tipo as tipo_1,
    COALESCE(al.departamento, 'sin_departamento') as tipo_2,
    COUNT(DISTINCT o.documento_id) as fuerza_conexion,
    'presencia_territorial' as naturaleza_conexion
FROM organizaciones o
JOIN analisis_lugares al ON o.documento_id = al.documento_id
WHERE o.tipo = 'fuerzas_ilegales'
GROUP BY o.nombre, al.nombre, o.tipo, COALESCE(al.departamento, 'sin_departamento')
HAVING COUNT(DISTINCT o.documento_id) >= 2

ORDER BY fuerza_conexion DESC;

-- =====================================================================
-- FUNCIONES PARA CONSULTAS FRECUENTES OPTIMIZADAS
-- =====================================================================

-- Función: Obtener dashboard principal
CREATE OR REPLACE FUNCTION get_dashboard_metricas()
RETURNS JSON AS $$
BEGIN
    RETURN (SELECT metricas_dashboard FROM mv_dashboard_principal);
END;
$$ LANGUAGE plpgsql;

-- Función: Buscar entidades para autocomplete
CREATE OR REPLACE FUNCTION buscar_entidades_autocomplete(termino TEXT, limite INTEGER DEFAULT 10)
RETURNS TABLE(
    tipo_entidad TEXT,
    nombre TEXT,
    subtipo TEXT,
    relevancia INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mte.tipo_entidad,
        mte.entidad as nombre,
        mte.subtipo,
        mte.frecuencia as relevancia
    FROM mv_top_entidades mte
    WHERE mte.entidad ILIKE '%' || termino || '%'
       OR mte.entidad % termino
    ORDER BY 
        CASE WHEN mte.entidad ILIKE termino || '%' THEN 1 ELSE 2 END,
        mte.frecuencia DESC
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- Función: Análisis geográfico rápido
CREATE OR REPLACE FUNCTION get_analisis_geografico(departamento_filtro TEXT DEFAULT NULL)
RETURNS TABLE(
    departamento VARCHAR(100),
    lugares_especificos BIGINT,
    municipios_afectados BIGINT,
    total_menciones BIGINT,
    casos_involucrados BIGINT,
    top_lugares JSON
) AS $$
BEGIN
    IF departamento_filtro IS NULL THEN
        RETURN QUERY
        SELECT 
            mag.departamento,
            mag.lugares_especificos,
            mag.municipios_afectados,
            mag.total_menciones,
            mag.casos_involucrados,
            mag.top_lugares
        FROM mv_analisis_geografico mag
        ORDER BY mag.total_menciones DESC;
    ELSE
        RETURN QUERY
        SELECT 
            mag.departamento,
            mag.lugares_especificos,
            mag.municipios_afectados,
            mag.total_menciones,
            mag.casos_involucrados,
            mag.top_lugares
        FROM mv_analisis_geografico mag
        WHERE mag.departamento ILIKE '%' || departamento_filtro || '%'
        ORDER BY mag.total_menciones DESC;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- FUNCIONES PARA RAG - CONSULTAS DINÁMICAS
-- =====================================================================

-- Función RAG: Buscar contexto para pregunta sobre personas
CREATE OR REPLACE FUNCTION rag_buscar_contexto_personas(terminos_busqueda TEXT[], limite INTEGER DEFAULT 20)
RETURNS TABLE(
    persona VARCHAR(255),
    tipo VARCHAR(50),
    contexto TEXT,
    documentos_relacionados INTEGER[],
    casos_relacionados TEXT[],
    score_relevancia REAL
) AS $$
DECLARE
    termino TEXT;
    query_text TEXT := '';
BEGIN
    -- Construir query de búsqueda
    FOREACH termino IN ARRAY terminos_busqueda LOOP
        IF query_text != '' THEN
            query_text := query_text || ' | ';
        END IF;
        query_text := query_text || termino;
    END LOOP;
    
    RETURN QUERY
    SELECT 
        p.nombre as persona,
        p.tipo,
        string_agg(DISTINCT 
            CASE 
                WHEN p.observaciones IS NOT NULL THEN p.observaciones
                WHEN p.descripcion IS NOT NULL THEN p.descripcion
                ELSE 'Mencionado en documento ' || d.archivo
            END, 
            ' | '
        ) as contexto,
        array_agg(DISTINCT p.documento_id) as documentos_relacionados,
        array_agg(DISTINCT d.nuc::TEXT) FILTER (WHERE d.nuc IS NOT NULL) as casos_relacionados,
        MAX(
            similarity(p.nombre, query_text) + 
            COALESCE(ts_rank_cd(to_tsvector('spanish', p.observaciones), plainto_tsquery('spanish', query_text)), 0)
        ) as score_relevancia
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE p.nombre % ANY(terminos_busqueda)
       OR to_tsvector('spanish', p.nombre) @@ plainto_tsquery('spanish', query_text)
       OR (p.observaciones IS NOT NULL AND to_tsvector('spanish', p.observaciones) @@ plainto_tsquery('spanish', query_text))
    GROUP BY p.nombre, p.tipo
    ORDER BY score_relevancia DESC, p.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- Función RAG: Buscar contexto para pregunta sobre organizaciones
CREATE OR REPLACE FUNCTION rag_buscar_contexto_organizaciones(terminos_busqueda TEXT[], limite INTEGER DEFAULT 20)
RETURNS TABLE(
    organizacion VARCHAR(255),
    tipo VARCHAR(50),
    contexto TEXT,
    documentos_relacionados INTEGER[],
    casos_relacionados TEXT[],
    lugares_asociados TEXT[],
    score_relevancia REAL
) AS $$
DECLARE
    termino TEXT;
    query_text TEXT := '';
BEGIN
    -- Construir query de búsqueda
    FOREACH termino IN ARRAY terminos_busqueda LOOP
        IF query_text != '' THEN
            query_text := query_text || ' | ';
        END IF;
        query_text := query_text || termino;
    END LOOP;
    
    RETURN QUERY
    SELECT 
        o.nombre as organizacion,
        o.tipo,
        string_agg(DISTINCT 
            CASE 
                WHEN o.descripcion IS NOT NULL THEN o.descripcion
                ELSE 'Mencionado en documento ' || d.archivo
            END, 
            ' | '
        ) as contexto,
        array_agg(DISTINCT o.documento_id) as documentos_relacionados,
        array_agg(DISTINCT d.nuc::TEXT) FILTER (WHERE d.nuc IS NOT NULL) as casos_relacionados,
        array_agg(DISTINCT al.nombre::TEXT) FILTER (WHERE al.nombre IS NOT NULL) as lugares_asociados,
        MAX(
            similarity(o.nombre, query_text) + 
            COALESCE(ts_rank_cd(to_tsvector('spanish', o.descripcion), plainto_tsquery('spanish', query_text)), 0)
        ) as score_relevancia
    FROM organizaciones o
    JOIN documentos d ON o.documento_id = d.id
    LEFT JOIN analisis_lugares al ON o.documento_id = al.documento_id
    WHERE o.nombre % ANY(terminos_busqueda)
       OR to_tsvector('spanish', o.nombre) @@ plainto_tsquery('spanish', query_text)
       OR (o.descripcion IS NOT NULL AND to_tsvector('spanish', o.descripcion) @@ plainto_tsquery('spanish', query_text))
    GROUP BY o.nombre, o.tipo
    ORDER BY score_relevancia DESC, o.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- Función RAG: Buscar contexto para pregunta sobre lugares/geografía
CREATE OR REPLACE FUNCTION rag_buscar_contexto_geografico(terminos_busqueda TEXT[], limite INTEGER DEFAULT 20)
RETURNS TABLE(
    lugar VARCHAR(500),
    municipio VARCHAR(100),
    departamento VARCHAR(100),
    contexto TEXT,
    entidades_asociadas JSON,
    documentos_relacionados INTEGER[],
    casos_relacionados TEXT[],
    score_relevancia REAL
) AS $$
DECLARE
    termino TEXT;
    query_text TEXT := '';
BEGIN
    -- Construir query de búsqueda
    FOREACH termino IN ARRAY terminos_busqueda LOOP
        IF query_text != '' THEN
            query_text := query_text || ' | ';
        END IF;
        query_text := query_text || termino;
    END LOOP;
    
    RETURN QUERY
    SELECT 
        al.nombre as lugar,
        al.municipio,
        al.departamento,
        'Lugar mencionado en contexto de: ' || string_agg(DISTINCT al.tipo, ', ') as contexto,
        json_build_object(
            'personas', (
                SELECT array_agg(DISTINCT p.nombre) 
                FROM personas p 
                WHERE p.documento_id = ANY(array_agg(DISTINCT al.documento_id))
                LIMIT 10
            ),
            'organizaciones', (
                SELECT array_agg(DISTINCT o.nombre) 
                FROM organizaciones o 
                WHERE o.documento_id = ANY(array_agg(DISTINCT al.documento_id))
                LIMIT 10
            )
        ) as entidades_asociadas,
        array_agg(DISTINCT al.documento_id) as documentos_relacionados,
        array_agg(DISTINCT d.nuc) FILTER (WHERE d.nuc IS NOT NULL) as casos_relacionados,
        MAX(
            similarity(al.nombre, query_text) + 
            similarity(COALESCE(al.municipio, ''), query_text) +
            similarity(COALESCE(al.departamento, ''), query_text)
        ) as score_relevancia
    FROM analisis_lugares al
    JOIN documentos d ON al.documento_id = d.id
    WHERE al.nombre % ANY(terminos_busqueda)
       OR COALESCE(al.municipio, '') % ANY(terminos_busqueda)
       OR COALESCE(al.departamento, '') % ANY(terminos_busqueda)
       OR to_tsvector('spanish', al.nombre) @@ plainto_tsquery('spanish', query_text)
    GROUP BY al.nombre, al.municipio, al.departamento
    ORDER BY score_relevancia DESC, al.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- FUNCIONES DE MANTENIMIENTO DE VISTAS MATERIALIZADAS
-- =====================================================================

-- Función para refrescar todas las vistas materializadas
CREATE OR REPLACE FUNCTION refresh_vistas_materializadas() 
RETURNS TABLE(vista TEXT, status TEXT, tiempo_ms INTEGER) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    -- Dashboard principal
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW mv_dashboard_principal;
    end_time := clock_timestamp();
    vista := 'mv_dashboard_principal';
    status := 'success';
    tiempo_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    RETURN NEXT;
    
    -- Top entidades
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_entidades;
    end_time := clock_timestamp();
    vista := 'mv_top_entidades';
    status := 'success';
    tiempo_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    RETURN NEXT;
    
    -- Análisis geográfico
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW mv_analisis_geografico;
    end_time := clock_timestamp();
    vista := 'mv_analisis_geografico';
    status := 'success';
    tiempo_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    RETURN NEXT;
    
    -- Red de conexiones
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW mv_red_conexiones;
    end_time := clock_timestamp();
    vista := 'mv_red_conexiones';
    status := 'success';
    tiempo_ms := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    RETURN NEXT;
    
EXCEPTION
    WHEN OTHERS THEN
        vista := 'error_general';
        status := SQLERRM;
        tiempo_ms := -1;
        RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- EJEMPLOS DE USO
-- =====================================================================

/*
-- CONSULTAS FRECUENTES (usan vistas materializadas):
SELECT * FROM get_dashboard_metricas();
SELECT * FROM buscar_entidades_autocomplete('FARC');
SELECT * FROM get_analisis_geografico('Meta');

-- CONSULTAS RAG (dinámicas):
SELECT * FROM rag_buscar_contexto_personas(ARRAY['Juan', 'Carlos']);
SELECT * FROM rag_buscar_contexto_organizaciones(ARRAY['FARC', 'ejercito']);
SELECT * FROM rag_buscar_contexto_geografico(ARRAY['Villavicencio', 'Meta']);

-- MANTENIMIENTO:
SELECT * FROM refresh_vistas_materializadas();
*/
