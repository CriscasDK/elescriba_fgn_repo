-- MODULO DE BUSQUEDA AVANZADA: SQL PARA SIMILITUD LEXICA, FONETICA Y TEXTO COMPLETO
-- Asegúrate de tener instaladas las extensiones necesarias:
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- =====================================================================
-- FUNCIONES DE BÚSQUEDA AVANZADA PARA EL ESQUEMA ACTUAL
-- =====================================================================

-- 1. Búsqueda léxica tolerante a errores en PERSONAS (trigramas)
-- Busca nombres similares con tolerancia a errores de escritura
CREATE OR REPLACE FUNCTION buscar_personas_fuzzy(termino_busqueda TEXT, limite INTEGER DEFAULT 20)
RETURNS TABLE(
    nombre VARCHAR(255),
    tipo VARCHAR(50),
    documento_id INTEGER,
    similitud REAL,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre,
        p.tipo,
        p.documento_id,
        similarity(p.nombre, termino_busqueda) AS similitud,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE p.nombre % termino_busqueda
    GROUP BY p.nombre, p.tipo, p.documento_id, similitud
    ORDER BY similitud DESC, p.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- 2. Búsqueda fonética en PERSONAS (soundex)
CREATE OR REPLACE FUNCTION buscar_personas_soundex(termino_busqueda TEXT)
RETURNS TABLE(
    nombre VARCHAR(255),
    tipo VARCHAR(50),
    documento_id INTEGER,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre,
        p.tipo,
        p.documento_id,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE soundex(p.nombre) = soundex(termino_busqueda)
    GROUP BY p.nombre, p.tipo, p.documento_id
    ORDER BY p.nombre;
END;
$$ LANGUAGE plpgsql;

-- 3. Búsqueda fonética avanzada (dmetaphone)
CREATE OR REPLACE FUNCTION buscar_personas_metaphone(termino_busqueda TEXT)
RETURNS TABLE(
    nombre VARCHAR(255),
    tipo VARCHAR(50),
    documento_id INTEGER,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre,
        p.tipo,
        p.documento_id,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE dmetaphone(p.nombre) = dmetaphone(termino_busqueda)
    GROUP BY p.nombre, p.tipo, p.documento_id
    ORDER BY p.nombre;
END;
$$ LANGUAGE plpgsql;

-- 4. Búsqueda de texto completo en PERSONAS con ranking
CREATE OR REPLACE FUNCTION buscar_personas_fulltext(termino_busqueda TEXT, limite INTEGER DEFAULT 20)
RETURNS TABLE(
    nombre VARCHAR(255),
    tipo VARCHAR(50),
    documento_id INTEGER,
    ranking REAL,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre,
        p.tipo,
        p.documento_id,
        ts_rank_cd(to_tsvector('spanish', p.nombre), plainto_tsquery('spanish', termino_busqueda)) AS ranking,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE to_tsvector('spanish', p.nombre) @@ plainto_tsquery('spanish', termino_busqueda)
    GROUP BY p.nombre, p.tipo, p.documento_id, ranking
    ORDER BY ranking DESC, p.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- 5. Búsqueda híbrida en PERSONAS (combina todos los métodos)
CREATE OR REPLACE FUNCTION buscar_personas_hibrida(termino_busqueda TEXT, limite INTEGER DEFAULT 30)
RETURNS TABLE(
    nombre VARCHAR(255),
    tipo VARCHAR(50),
    documento_id INTEGER,
    similitud_lexica REAL,
    coincidencia_fonetica BOOLEAN,
    ranking_texto REAL,
    metodo_encontrado TEXT,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre,
        p.tipo,
        p.documento_id,
        similarity(p.nombre, termino_busqueda) AS similitud_lexica,
        (soundex(p.nombre) = soundex(termino_busqueda)) AS coincidencia_fonetica,
        ts_rank_cd(to_tsvector('spanish', p.nombre), plainto_tsquery('spanish', termino_busqueda)) AS ranking_texto,
        CASE 
            WHEN p.nombre % termino_busqueda THEN 'trigrama'
            WHEN soundex(p.nombre) = soundex(termino_busqueda) THEN 'soundex'
            WHEN to_tsvector('spanish', p.nombre) @@ plainto_tsquery('spanish', termino_busqueda) THEN 'fulltext'
            ELSE 'otro'
        END AS metodo_encontrado,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE p.nombre % termino_busqueda
       OR soundex(p.nombre) = soundex(termino_busqueda)
       OR to_tsvector('spanish', p.nombre) @@ plainto_tsquery('spanish', termino_busqueda)
    GROUP BY p.nombre, p.tipo, p.documento_id, similitud_lexica, coincidencia_fonetica, ranking_texto, metodo_encontrado
    ORDER BY coincidencia_fonetica DESC, similitud_lexica DESC, ranking_texto DESC, p.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- FUNCIONES DE BÚSQUEDA PARA ORGANIZACIONES
-- =====================================================================

-- 6. Búsqueda fuzzy en ORGANIZACIONES
CREATE OR REPLACE FUNCTION buscar_organizaciones_fuzzy(termino_busqueda TEXT, limite INTEGER DEFAULT 20)
RETURNS TABLE(
    nombre VARCHAR(255),
    tipo VARCHAR(50),
    descripcion TEXT,
    documento_id INTEGER,
    similitud REAL,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.nombre,
        o.tipo,
        o.descripcion,
        o.documento_id,
        similarity(o.nombre, termino_busqueda) AS similitud,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM organizaciones o
    JOIN documentos d ON o.documento_id = d.id
    WHERE o.nombre % termino_busqueda
    GROUP BY o.nombre, o.tipo, o.descripcion, o.documento_id, similitud
    ORDER BY similitud DESC, o.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- FUNCIONES DE BÚSQUEDA PARA LUGARES
-- =====================================================================

-- 7. Búsqueda geográfica avanzada
CREATE OR REPLACE FUNCTION buscar_lugares_geografica(termino_busqueda TEXT, limite INTEGER DEFAULT 20)
RETURNS TABLE(
    nombre VARCHAR(500),
    tipo VARCHAR(100),
    municipio VARCHAR(100),
    departamento VARCHAR(100),
    documento_id INTEGER,
    similitud REAL,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.nombre,
        al.tipo,
        al.municipio,
        al.departamento,
        al.documento_id,
        GREATEST(
            similarity(al.nombre, termino_busqueda),
            similarity(COALESCE(al.municipio, ''), termino_busqueda),
            similarity(COALESCE(al.departamento, ''), termino_busqueda)
        ) AS similitud,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM analisis_lugares al
    JOIN documentos d ON al.documento_id = d.id
    WHERE al.nombre % termino_busqueda
       OR COALESCE(al.municipio, '') % termino_busqueda
       OR COALESCE(al.departamento, '') % termino_busqueda
    GROUP BY al.nombre, al.tipo, al.municipio, al.departamento, al.documento_id, similitud
    ORDER BY similitud DESC, al.nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- BÚSQUEDAS COMBINADAS Y GLOBALES
-- =====================================================================

-- 8. Búsqueda global en todas las entidades
CREATE OR REPLACE FUNCTION buscar_global(termino_busqueda TEXT, limite INTEGER DEFAULT 50)
RETURNS TABLE(
    tipo_entidad TEXT,
    nombre TEXT,
    detalles TEXT,
    documento_id INTEGER,
    similitud REAL,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    -- Personas
    SELECT 
        'persona'::TEXT as tipo_entidad,
        p.nombre::TEXT as nombre,
        COALESCE(p.tipo, 'sin_clasificar')::TEXT as detalles,
        p.documento_id,
        similarity(p.nombre, termino_busqueda) AS similitud,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE p.nombre % termino_busqueda
    GROUP BY p.nombre, p.tipo, p.documento_id, similitud
    
    UNION ALL
    
    -- Organizaciones
    SELECT 
        'organizacion'::TEXT as tipo_entidad,
        o.nombre::TEXT as nombre,
        COALESCE(o.tipo, 'sin_clasificar')::TEXT as detalles,
        o.documento_id,
        similarity(o.nombre, termino_busqueda) AS similitud,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM organizaciones o
    JOIN documentos d ON o.documento_id = d.id
    WHERE o.nombre % termino_busqueda
    GROUP BY o.nombre, o.tipo, o.documento_id, similitud
    
    UNION ALL
    
    -- Lugares
    SELECT 
        'lugar'::TEXT as tipo_entidad,
        al.nombre::TEXT as nombre,
        (COALESCE(al.municipio, '') || ', ' || COALESCE(al.departamento, ''))::TEXT as detalles,
        al.documento_id,
        similarity(al.nombre, termino_busqueda) AS similitud,
        array_agg(DISTINCT d.nuc) as casos_relacionados
    FROM analisis_lugares al
    JOIN documentos d ON al.documento_id = d.id
    WHERE al.nombre % termino_busqueda
    GROUP BY al.nombre, al.municipio, al.departamento, al.documento_id, similitud
    
    ORDER BY similitud DESC, nombre
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- EJEMPLOS DE USO DE LAS FUNCIONES
-- =====================================================================

-- Buscar persona con tolerancia a errores:
-- SELECT * FROM buscar_personas_fuzzy('Rodriguo');

-- Buscar por similitud fonética:
-- SELECT * FROM buscar_personas_soundex('Rodriguez');

-- Búsqueda híbrida (recomendado):
-- SELECT * FROM buscar_personas_hibrida('Juan Carlos');

-- Buscar organizaciones:
-- SELECT * FROM buscar_organizaciones_fuzzy('Union Patriotica');

-- Búsqueda geográfica:
-- SELECT * FROM buscar_lugares_geografica('Villavicencio');

-- Búsqueda global:
-- SELECT * FROM buscar_global('FARC');

-- FIN MODULO DE BUSQUEDA AVANZADA
