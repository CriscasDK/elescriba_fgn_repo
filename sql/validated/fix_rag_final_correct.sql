-- Corregir función rag_buscar_contexto_personas con GROUP BY correcto

DROP FUNCTION IF EXISTS rag_buscar_contexto_personas(TEXT[], INTEGER) CASCADE;

CREATE OR REPLACE FUNCTION rag_buscar_contexto_personas(
    terminos_busqueda TEXT[],
    limite INTEGER DEFAULT 10
) RETURNS TABLE (
    persona TEXT,
    tipo VARCHAR(50),
    contexto TEXT,
    documentos_relacionados INTEGER[],
    casos_relacionados TEXT[],
    score_relevancia NUMERIC
) AS $$
DECLARE
    query_text TEXT := array_to_string(terminos_busqueda, ' ');
BEGIN
    RETURN QUERY
    SELECT 
        p.nombre::TEXT as persona,
        p.tipo::VARCHAR(50),
        string_agg(DISTINCT 
            CASE 
                WHEN p.observaciones IS NOT NULL THEN p.observaciones
                WHEN p.descripcion IS NOT NULL THEN p.descripcion
                ELSE 'Mencionado en documento ' || d.archivo
            END, 
            ' | '
        )::TEXT as contexto,
        array_agg(DISTINCT p.documento_id) as documentos_relacionados,
        array_agg(DISTINCT d.nuc::TEXT) FILTER (WHERE d.nuc IS NOT NULL) as casos_relacionados,
        MAX(
            COALESCE(similarity(p.nombre, query_text)::NUMERIC, 0) + 
            COALESCE(ts_rank_cd(to_tsvector('spanish', COALESCE(p.observaciones, '')), plainto_tsquery('spanish', query_text))::NUMERIC, 0)
        ) as score_relevancia
    FROM personas p
    JOIN documentos d ON p.documento_id = d.id
    WHERE EXISTS (
        SELECT 1 FROM unnest(terminos_busqueda) AS termino_tabla(termino_busqueda)
        WHERE p.nombre ILIKE '%' || termino_tabla.termino_busqueda || '%'
           OR to_tsvector('spanish', p.nombre) @@ plainto_tsquery('spanish', termino_tabla.termino_busqueda)
           OR (p.observaciones IS NOT NULL AND to_tsvector('spanish', p.observaciones) @@ plainto_tsquery('spanish', termino_tabla.termino_busqueda))
    )
    GROUP BY p.nombre, p.tipo
    ORDER BY score_relevancia DESC, persona
    LIMIT limite;
END;
$$ LANGUAGE plpgsql;

-- Test de la función corregida
\echo '--- Probando función rag_buscar_contexto_personas corregida ---'
SELECT * FROM rag_buscar_contexto_personas(ARRAY['Juan'], 3);

\echo '--- Función RAG corregida exitosamente ---'
