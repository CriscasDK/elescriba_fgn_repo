-- BUSQUEDA POR LENGUAJE NATURAL (TEXTO COMPLETO Y SIMILITUD)
-- Requiere: pg_trgm, texto completo
-- Ejemplo: Buscar documentos relevantes a una pregunta o frase

-- 1. Texto completo (websearch, varias palabras, ranking)
SELECT id, archivo, ts_rank_cd(to_tsvector('spanish', texto), websearch_to_tsquery('spanish', 'desplazamiento forzado violencia')) AS score
FROM documentos
WHERE to_tsvector('spanish', texto) @@ websearch_to_tsquery('spanish', 'desplazamiento forzado violencia')
ORDER BY score DESC, archivo
LIMIT 20;

-- 2. Similitud léxica (trigramas) sobre texto completo
SELECT id, archivo, similarity(texto, 'desplazamiento forzado violencia') AS score
FROM documentos
WHERE similarity(texto, 'desplazamiento forzado violencia') > 0.2
ORDER BY score DESC, archivo
LIMIT 20;

-- 3. Combinada: texto completo y trigramas
SELECT id, archivo,
  ts_rank_cd(to_tsvector('spanish', texto), websearch_to_tsquery('spanish', 'desplazamiento forzado violencia')) AS score_texto,
  similarity(texto, 'desplazamiento forzado violencia') AS score_lexico
FROM documentos
WHERE to_tsvector('spanish', texto) @@ websearch_to_tsquery('spanish', 'desplazamiento forzado violencia')
   OR similarity(texto, 'desplazamiento forzado violencia') > 0.2
ORDER BY score_texto DESC, score_lexico DESC, archivo
LIMIT 20;

-- Puedes adaptar la consulta a cualquier campo o tabla relevante.
