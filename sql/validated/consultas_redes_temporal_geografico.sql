-- CONSULTAS AVANZADAS: REDES, PATRONES TEMPORALES Y GEOGRÁFICOS
-- Análisis de conexiones entre entidades para el esquema actual

-- =====================================================================
-- ANÁLISIS DE REDES DE PERSONAS
-- =====================================================================

-- 1. Personas que aparecen juntas en el mismo documento (co-ocurrencia)
CREATE OR REPLACE FUNCTION analizar_red_personas(limite INTEGER DEFAULT 50)
RETURNS TABLE(
    persona_1 VARCHAR(255),
    persona_2 VARCHAR(255),
    tipo_1 VARCHAR(50),
    tipo_2 VARCHAR(50),
    documentos_compartidos BIGINT,
    casos_compartidos TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p1.nombre AS persona_1,
        p2.nombre AS persona_2,
        p1.tipo AS tipo_1,
        p2.tipo AS tipo_2,
        COUNT(DISTINCT p1.documento_id) AS documentos_compartidos,
        array_agg(DISTINCT d.nuc) AS casos_compartidos
    FROM personas p1
    JOIN personas p2 ON p1.documento_id = p2.documento_id AND p1.nombre < p2.nombre
    JOIN documentos d ON p1.documento_id = d.id
    WHERE p1.nombre != p2.nombre
    GROUP BY p1.nombre, p2.nombre, p1.tipo, p2.tipo
    HAVING COUNT(DISTINCT p1.documento_id) > 1
    ORDER BY documentos_compartidos DESC, persona_1
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- 2. Red específica: Víctimas y victimarios en el mismo documento
CREATE OR REPLACE FUNCTION analizar_victimas_victimarios()
RETURNS TABLE(
    victima VARCHAR(255),
    victimario VARCHAR(255),
    documentos_compartidos BIGINT,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p1.nombre AS victima,
        p2.nombre AS victimario,
        COUNT(DISTINCT p1.documento_id) AS documentos_compartidos,
        array_agg(DISTINCT d.nuc) AS casos_relacionados
    FROM personas p1
    JOIN personas p2 ON p1.documento_id = p2.documento_id
    JOIN documentos d ON p1.documento_id = d.id
    WHERE (p1.tipo LIKE '%victima%' OR p1.tipo LIKE '%víctima%')
      AND (p2.tipo LIKE '%victimario%' OR p2.tipo LIKE '%responsable%')
      AND p1.nombre != p2.nombre
    GROUP BY p1.nombre, p2.nombre
    ORDER BY documentos_compartidos DESC, victima;
END;
$$ LANGUAGE plpgsql;

-- 3. Personas con múltiples roles (aparecen en diferentes clasificaciones)
CREATE OR REPLACE FUNCTION analizar_personas_multiples_roles()
RETURNS TABLE(
    nombre VARCHAR(255),
    tipos_diferentes TEXT[],
    total_documentos BIGINT,
    casos_involucrados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre,
        array_agg(DISTINCT p.tipo) AS tipos_diferentes,
        COUNT(DISTINCT p.documento_id) AS total_documentos,
        array_agg(DISTINCT d.nuc) AS casos_involucrados
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE p.tipo IS NOT NULL
    GROUP BY p.nombre
    HAVING COUNT(DISTINCT p.tipo) > 1
    ORDER BY total_documentos DESC, nombre;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- ANÁLISIS DE REDES DE ORGANIZACIONES
-- =====================================================================

-- 4. Red de organizaciones y personas (conexiones entre entidades)
CREATE OR REPLACE FUNCTION analizar_red_organizaciones_personas(limite INTEGER DEFAULT 50)
RETURNS TABLE(
    organizacion VARCHAR(255),
    tipo_organizacion VARCHAR(50),
    persona VARCHAR(255),
    tipo_persona VARCHAR(50),
    documentos_compartidos BIGINT,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.nombre AS organizacion,
        o.tipo AS tipo_organizacion,
        p.nombre AS persona,
        p.tipo AS tipo_persona,
        COUNT(DISTINCT o.documento_id) AS documentos_compartidos,
        array_agg(DISTINCT d.nuc) AS casos_relacionados
    FROM organizaciones o
    JOIN personas p ON o.documento_id = p.documento_id
    JOIN documentos d ON o.documento_id = d.id
    GROUP BY o.nombre, o.tipo, p.nombre, p.tipo
    HAVING COUNT(DISTINCT o.documento_id) > 1
    ORDER BY documentos_compartidos DESC, organizacion
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- 5. Organizaciones ilegales y su presencia territorial
CREATE OR REPLACE FUNCTION analizar_organizaciones_territorio()
RETURNS TABLE(
    organizacion VARCHAR(255),
    lugar VARCHAR(500),
    municipio VARCHAR(100),
    departamento VARCHAR(100),
    documentos_compartidos BIGINT,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.nombre AS organizacion,
        al.nombre AS lugar,
        al.municipio,
        al.departamento,
        COUNT(DISTINCT o.documento_id) AS documentos_compartidos,
        array_agg(DISTINCT d.nuc) AS casos_relacionados
    FROM organizaciones o
    JOIN analisis_lugares al ON o.documento_id = al.documento_id
    JOIN documentos d ON o.documento_id = d.id
    WHERE o.tipo = 'fuerzas_ilegales'
    GROUP BY o.nombre, al.nombre, al.municipio, al.departamento
    ORDER BY documentos_compartidos DESC, organizacion;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- ANÁLISIS GEOGRÁFICO Y TERRITORIAL
-- =====================================================================

-- 6. Lugares que conectan múltiples casos
CREATE OR REPLACE FUNCTION analizar_lugares_conectores()
RETURNS TABLE(
    lugar VARCHAR(500),
    municipio VARCHAR(100),
    departamento VARCHAR(100),
    casos_distintos BIGINT,
    total_apariciones BIGINT,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.nombre AS lugar,
        al.municipio,
        al.departamento,
        COUNT(DISTINCT d.nuc) AS casos_distintos,
        COUNT(*) AS total_apariciones,
        array_agg(DISTINCT d.nuc) AS casos_relacionados
    FROM analisis_lugares al
    JOIN documentos d ON al.documento_id = d.id
    WHERE d.nuc IS NOT NULL
    GROUP BY al.nombre, al.municipio, al.departamento
    HAVING COUNT(DISTINCT d.nuc) > 1
    ORDER BY casos_distintos DESC, total_apariciones DESC;
END;
$$ LANGUAGE plpgsql;

-- 7. Co-ocurrencia de lugares (lugares que aparecen en el mismo documento)
CREATE OR REPLACE FUNCTION analizar_coocurrencia_lugares(limite INTEGER DEFAULT 50)
RETURNS TABLE(
    lugar_1 VARCHAR(500),
    lugar_2 VARCHAR(500),
    departamento_1 VARCHAR(100),
    departamento_2 VARCHAR(100),
    documentos_compartidos BIGINT,
    casos_relacionados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l1.nombre AS lugar_1,
        l2.nombre AS lugar_2,
        l1.departamento AS departamento_1,
        l2.departamento AS departamento_2,
        COUNT(DISTINCT l1.documento_id) AS documentos_compartidos,
        array_agg(DISTINCT d.nuc) AS casos_relacionados
    FROM analisis_lugares l1
    JOIN analisis_lugares l2 ON l1.documento_id = l2.documento_id AND l1.nombre < l2.nombre
    JOIN documentos d ON l1.documento_id = d.id
    GROUP BY l1.nombre, l2.nombre, l1.departamento, l2.departamento
    HAVING COUNT(DISTINCT l1.documento_id) > 1
    ORDER BY documentos_compartidos DESC, lugar_1
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- ANÁLISIS TEMPORAL
-- =====================================================================

-- 8. Evolución temporal del caso por fechas de procesamiento
CREATE OR REPLACE FUNCTION analizar_evolucion_temporal()
RETURNS TABLE(
    fecha_procesamiento DATE,
    documentos_procesados BIGINT,
    personas_nuevas BIGINT,
    organizaciones_nuevas BIGINT,
    lugares_nuevos BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.created_at::DATE AS fecha_procesamiento,
        COUNT(DISTINCT d.id) AS documentos_procesados,
        COUNT(DISTINCT p.id) AS personas_nuevas,
        COUNT(DISTINCT o.id) AS organizaciones_nuevas,
        COUNT(DISTINCT al.id) AS lugares_nuevos
    FROM documentos d
    LEFT JOIN personas p ON d.id = p.documento_id
    LEFT JOIN organizaciones o ON d.id = o.documento_id
    LEFT JOIN analisis_lugares al ON d.id = al.documento_id
    GROUP BY d.created_at::DATE
    ORDER BY fecha_procesamiento;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- ANÁLISIS DE MOVILIDAD Y DISPERSIÓN
-- =====================================================================

-- 9. Casos con múltiples departamentos (movilidad geográfica)
CREATE OR REPLACE FUNCTION analizar_casos_multiples_departamentos()
RETURNS TABLE(
    caso VARCHAR(50),
    departamentos_involucrados BIGINT,
    lista_departamentos TEXT,
    total_lugares BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.nuc AS caso,
        COUNT(DISTINCT al.departamento) AS departamentos_involucrados,
        string_agg(DISTINCT al.departamento, ', ' ORDER BY al.departamento) AS lista_departamentos,
        COUNT(DISTINCT al.nombre) AS total_lugares
    FROM documentos d
    JOIN analisis_lugares al ON d.id = al.documento_id
    WHERE al.departamento IS NOT NULL AND d.nuc IS NOT NULL
    GROUP BY d.nuc
    HAVING COUNT(DISTINCT al.departamento) > 1
    ORDER BY departamentos_involucrados DESC, total_lugares DESC;
END;
$$ LANGUAGE plpgsql;

-- 10. Personas con presencia en múltiples departamentos
CREATE OR REPLACE FUNCTION analizar_personas_movilidad()
RETURNS TABLE(
    persona VARCHAR(255),
    tipo_persona VARCHAR(50),
    departamentos_presencia BIGINT,
    lista_departamentos TEXT,
    casos_involucrados TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre AS persona,
        p.tipo AS tipo_persona,
        COUNT(DISTINCT al.departamento) AS departamentos_presencia,
        string_agg(DISTINCT al.departamento, ', ' ORDER BY al.departamento) AS lista_departamentos,
        array_agg(DISTINCT d.nuc) AS casos_involucrados
    FROM personas p
    JOIN analisis_lugares al ON p.documento_id = al.documento_id
    JOIN documentos d ON p.documento_id = d.id
    WHERE al.departamento IS NOT NULL
    GROUP BY p.nombre, p.tipo
    HAVING COUNT(DISTINCT al.departamento) > 1
    ORDER BY departamentos_presencia DESC, persona;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- ANÁLISIS ESTADÍSTICO DE REDES
-- =====================================================================

-- 11. Estadísticas generales de la red
CREATE OR REPLACE FUNCTION estadisticas_red_general()
RETURNS TABLE(
    metrica TEXT,
    valor BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'total_personas'::TEXT, COUNT(DISTINCT nombre)::BIGINT FROM personas
    UNION ALL
    SELECT 'total_organizaciones'::TEXT, COUNT(DISTINCT nombre)::BIGINT FROM organizaciones
    UNION ALL
    SELECT 'total_lugares'::TEXT, COUNT(DISTINCT nombre)::BIGINT FROM analisis_lugares
    UNION ALL
    SELECT 'personas_multiples_documentos'::TEXT, COUNT(*)::BIGINT FROM (
        SELECT nombre FROM personas GROUP BY nombre HAVING COUNT(DISTINCT documento_id) > 1
    ) t
    UNION ALL
    SELECT 'organizaciones_multiples_documentos'::TEXT, COUNT(*)::BIGINT FROM (
        SELECT nombre FROM organizaciones GROUP BY nombre HAVING COUNT(DISTINCT documento_id) > 1
    ) t
    UNION ALL
    SELECT 'lugares_multiples_documentos'::TEXT, COUNT(*)::BIGINT FROM (
        SELECT nombre FROM analisis_lugares GROUP BY nombre HAVING COUNT(DISTINCT documento_id) > 1
    ) t;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- EJEMPLOS DE USO
-- =====================================================================

-- Analizar red de personas:
-- SELECT * FROM analizar_red_personas(30);

-- Analizar víctimas y victimarios:
-- SELECT * FROM analizar_victimas_victimarios();

-- Analizar movilidad geográfica:
-- SELECT * FROM analizar_casos_multiples_departamentos();

-- Estadísticas generales:
-- SELECT * FROM estadisticas_red_general();

-- FIN CONSULTAS AVANZADAS
