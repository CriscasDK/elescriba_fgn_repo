-- BUSQUEDA POR PALABRA(S) CON SIMILITUD Y SCORE
-- Requiere: pg_trgm, fuzzystrmatch
-- Ejemplo: Buscar personas por nombre (exacto, similar, fonético, texto completo)

-- 1. Exacta
SELECT nombre_persona, documento_id
FROM analisis_personas_general
WHERE nombre_persona = 'Rodrigo Lopez';

-- 2. Similitud léxica (trigramas)
SELECT nombre_persona, documento_id, similarity(nombre_persona, 'Rodriguo Lopez') AS score
FROM analisis_personas_general
WHERE nombre_persona % 'Rodriguo Lopez'
ORDER BY score DESC, nombre_persona
LIMIT 20;

-- 3. Similitud fonética (soundex)
SELECT nombre_persona, documento_id, (soundex(nombre_persona) = soundex('Rodriguo Lopez'))::int AS score
FROM analisis_personas_general
WHERE soundex(nombre_persona) = soundex('Rodriguo Lopez');

-- 4. Texto completo (varias palabras, ranking)
SELECT nombre_persona, documento_id, ts_rank_cd(to_tsvector('spanish', nombre_persona), plainto_tsquery('spanish', 'Rodrigo Lopez')) AS score
FROM analisis_personas_general
WHERE to_tsvector('spanish', nombre_persona) @@ plainto_tsquery('spanish', 'Rodrigo Lopez')
ORDER BY score DESC, nombre_persona
LIMIT 20;

-- Puedes adaptar para organizaciones, lugares, etc. cambiando tabla y columna.
