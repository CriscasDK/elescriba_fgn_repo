-- 🔍 CONSULTAS DIRECTAS PARA ANÁLISIS DE VÍCTIMAS
-- Ejecutar estas consultas directamente en psql o pgAdmin

-- 1. ESTADÍSTICAS BÁSICAS
SELECT 'Total víctimas' as descripcion, COUNT(*) as cantidad
FROM personas 
WHERE tipo ILIKE '%victima%' 
  AND tipo NOT ILIKE '%victimario%'
UNION ALL
SELECT 'Víctimas con metadatos', COUNT(*)
FROM personas p
JOIN documentos d ON p.documento_id = d.id
JOIN metadatos m ON d.id = m.documento_id
WHERE p.tipo ILIKE '%victima%' 
  AND p.tipo NOT ILIKE '%victimario%'
UNION ALL
SELECT 'Víctimas con análisis', COUNT(*)
FROM personas p
JOIN documentos d ON p.documento_id = d.id
WHERE p.tipo ILIKE '%victima%' 
  AND p.tipo NOT ILIKE '%victimario%'
  AND d.analisis IS NOT NULL 
  AND d.analisis != '';

-- 2. TIPOS DE PERSONAS EN LA BASE DE DATOS
SELECT tipo, COUNT(*) as cantidad
FROM personas 
GROUP BY tipo 
ORDER BY cantidad DESC
LIMIT 15;

-- 3. MUESTRA DE VÍCTIMAS CON METADATOS COMPLETOS
SELECT 
    p.nombre,
    p.tipo,
    d.archivo,
    m.nuc,
    m.serie,
    LEFT(m.detalle, 50) as detalle_corto,
    LENGTH(d.analisis) as len_analisis,
    LENGTH(d.texto_extraido) as len_texto,
    CASE WHEN m.id IS NOT NULL THEN 'CON METADATOS' ELSE 'SIN METADATOS' END as estado
FROM personas p
JOIN documentos d ON p.documento_id = d.id
LEFT JOIN metadatos m ON d.id = m.documento_id
WHERE p.tipo ILIKE '%victima%' 
  AND p.tipo NOT ILIKE '%victimario%'
  AND p.nombre IS NOT NULL 
  AND p.nombre != ''
ORDER BY p.nombre
LIMIT 10;

-- 4. VÍCTIMAS CON NUC ESPECÍFICO (caso conocido)
SELECT 
    p.nombre,
    p.tipo,
    d.archivo,
    m.nuc,
    m.serie,
    m.detalle,
    LENGTH(d.analisis) as chars_analisis,
    CASE 
        WHEN d.analisis IS NOT NULL AND d.analisis != '' THEN 'SÍ'
        ELSE 'NO'
    END as tiene_analisis
FROM personas p
JOIN documentos d ON p.documento_id = d.id
JOIN metadatos m ON d.id = m.documento_id
WHERE p.tipo ILIKE '%victima%' 
  AND p.tipo NOT ILIKE '%victimario%'
  AND m.nuc = '11001606606419900000186'
ORDER BY p.nombre;

-- 5. ANÁLISIS DE COBERTURA DE METADATOS
SELECT 
    'nuc' as campo,
    COUNT(*) as total_registros,
    SUM(CASE WHEN nuc IS NOT NULL AND nuc != '' THEN 1 ELSE 0 END) as poblado,
    ROUND(SUM(CASE WHEN nuc IS NOT NULL AND nuc != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as porcentaje
FROM metadatos
UNION ALL
SELECT 
    'serie',
    COUNT(*),
    SUM(CASE WHEN serie IS NOT NULL AND serie != '' THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN serie IS NOT NULL AND serie != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM metadatos
UNION ALL
SELECT 
    'detalle',
    COUNT(*),
    SUM(CASE WHEN detalle IS NOT NULL AND detalle != '' THEN 1 ELSE 0 END),
    ROUND(SUM(CASE WHEN detalle IS NOT NULL AND detalle != '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
FROM metadatos;

-- 6. VÍCTIMAS CON ANÁLISIS MÁS EXTENSO
SELECT 
    p.nombre,
    d.archivo,
    LENGTH(d.analisis) as chars_analisis,
    LEFT(d.analisis, 100) as preview_analisis
FROM personas p
JOIN documentos d ON p.documento_id = d.id
WHERE p.tipo ILIKE '%victima%' 
  AND p.tipo NOT ILIKE '%victimario%'
  AND d.analisis IS NOT NULL 
  AND LENGTH(d.analisis) > 1000
ORDER BY LENGTH(d.analisis) DESC
LIMIT 5;

-- 7. CONSULTA COMPLETA COMO LA DEL FRONTEND
SELECT 
    p.nombre,
    p.tipo,
    d.id as doc_id,
    d.archivo,
    COALESCE(NULLIF(m.nuc, ''), 'N/A') as nuc,
    COALESCE(NULLIF(m.serie, ''), 'N/A') as serie,
    COALESCE(NULLIF(m.detalle, ''), 'N/A') as detalle,
    LENGTH(COALESCE(d.analisis, '')) as len_analisis,
    LENGTH(COALESCE(d.texto_extraido, '')) as len_texto,
    CASE WHEN d.analisis IS NOT NULL AND d.analisis != '' THEN 'SÍ' ELSE 'NO' END as tiene_analisis,
    CASE WHEN d.texto_extraido IS NOT NULL AND d.texto_extraido != '' THEN 'SÍ' ELSE 'NO' END as tiene_texto,
    CASE WHEN m.id IS NOT NULL THEN 'SÍ' ELSE 'NO' END as tiene_metadatos
FROM personas p
JOIN documentos d ON p.documento_id = d.id
LEFT JOIN metadatos m ON d.id = m.documento_id
WHERE p.tipo ILIKE '%victima%' 
  AND p.tipo NOT ILIKE '%victimario%'
  AND p.nombre IS NOT NULL 
  AND p.nombre != ''
ORDER BY p.nombre
LIMIT 5;
