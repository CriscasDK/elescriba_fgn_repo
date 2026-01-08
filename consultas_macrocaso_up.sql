-- RECOMENDACIÓN: Para búsquedas avanzadas (similitud léxica, fonética, tolerancia a errores y varias palabras), consulta el archivo:
-- consultas_busqueda_avanzada.sql
-- Incluye ejemplos con pg_trgm, fuzzystrmatch y texto completo para personas, organizaciones y lugares.
-- Puedes combinar estos métodos con las consultas temáticas de este archivo para análisis más flexibles.

SELECT d.id, d.archivo, pc.nombre_persona
FROM documentos d
JOIN analisis_personas_clasificacion pc ON d.id = pc.documento_id
WHERE pc.tipo_clasificacion = 'victimas';

-- 2. Todas las personas clasificadas como víctimas y su frecuencia
SELECT nombre_persona, COUNT(*) AS veces_mencionada
FROM analisis_personas_clasificacion
WHERE tipo_clasificacion = 'victimas'
GROUP BY nombre_persona
ORDER BY veces_mencionada DESC;

-- 3. Documentos con palabras clave de violencia
SELECT id, archivo
FROM documentos
WHERE texto_extraido ILIKE ANY (ARRAY[
    '%desaparecido%', '%asesinado%', '%torturado%', '%amenazado%', '%secuestrado%', '%ejecutado%'
])
   OR analisis ILIKE ANY (ARRAY[
    '%desaparecido%', '%asesinado%', '%torturado%', '%amenazado%', '%secuestrado%', '%ejecutado%'
]);

-- 4. Dirigentes/líderes atacados
SELECT cr.persona, cr.cargo, d.archivo
FROM analisis_cargos_roles cr
JOIN documentos d ON cr.documento_id = d.id
WHERE cr.cargo ILIKE ANY (ARRAY[
    '%militante%', '%dirigente%', '%líder%'
])
AND (d.texto_extraido ILIKE '%atacado%' OR d.analisis ILIKE '%atacado%' OR d.texto_extraido ILIKE '%agredido%' OR d.analisis ILIKE '%agredido%');

-- 6. Documentos con mención a exilio/desplazamiento/refugio
SELECT id, archivo
FROM documentos
WHERE texto_extraido ILIKE ANY (ARRAY[
    '%exilio%', '%desplazamiento forzado%', '%refugio%', '%huyó%', '%obligado a salir%'
])
   OR analisis ILIKE ANY (ARRAY[
    '%exilio%', '%desplazamiento forzado%', '%refugio%', '%huyó%', '%obligado a salir%'
]);

-- 9. Personas como dirigentes sindicales, líderes estudiantiles, militantes políticos
SELECT cr.persona, cr.cargo, d.archivo
FROM analisis_cargos_roles cr
JOIN documentos d ON cr.documento_id = d.id
WHERE cr.cargo ILIKE ANY (ARRAY[
    '%dirigente sindical%', '%líder estudiantil%', '%militante político%', '%activista%'
]);

-- 12. Casos (NUC) más antiguos sin avances (por fecha de creación)
SELECT nuc, MIN(fecha_creacion) AS fecha_mas_antigua, COUNT(*) AS documentos
FROM metadatos
GROUP BY nuc
ORDER BY fecha_mas_antigua ASC
LIMIT 20;

-- 18. Tipos de documentos con mayor valor probatorio (por cantidad de firmas digitales)
SELECT tipo_especifico, COUNT(*) AS cantidad, COUNT(firma_digital) AS con_firma
FROM analisis_tipo_documento td
JOIN metadatos m ON td.documento_id = m.documento_id
GROUP BY tipo_especifico
ORDER BY con_firma DESC, cantidad DESC;

-- 21. Calidad de extracción de texto por documento
SELECT d.id, d.archivo, e.normal, e.ilegible, e.posiblemente, e.total_palabras, e.porcentaje_inferencias
FROM documentos d
JOIN estadisticas e ON d.id = e.documento_id
ORDER BY e.normal DESC;

-- 25. Ubicaciones más mencionadas en los casos
SELECT l.nombre, COUNT(*) AS veces_mencionada
FROM analisis_lugares l
GROUP BY l.nombre
ORDER BY veces_mencionada DESC
LIMIT 20;

-- 27. Despachos judiciales con más casos
SELECT despacho, COUNT(*) AS cantidad
FROM metadatos
GROUP BY despacho
ORDER BY cantidad DESC
LIMIT 20;

-- CONSULTAS AVANZADAS Y SUGERIDAS

-- A. Nombres de víctimas que aparecen como victimarios en otros documentos (alerta de contradicción)
SELECT v1.nombre_persona AS posible_victima, v2.nombre_persona AS posible_victimario, v1.documento_id AS doc_victima, v2.documento_id AS doc_victimario
FROM analisis_personas_clasificacion v1
JOIN analisis_personas_clasificacion v2 ON v1.nombre_persona = v2.nombre_persona AND v1.tipo_clasificacion = 'victimas' AND v2.tipo_clasificacion = 'victimarios';

-- B. Fechas incompatibles: documentos con fechas fuera de rango esperado (ejemplo: antes de 1980 o después de 2025)
SELECT documento_id, fecha
FROM analisis_fechas
WHERE fecha < '1980-01-01' OR fecha > '2025-12-31';

-- C. Lugares que aparecen en contextos contradictorios (ejemplo: mismo lugar como sitio de víctima y victimario)
SELECT l1.nombre, l1.documento_id AS doc_victima, l2.documento_id AS doc_victimario
FROM analisis_lugares l1
JOIN analisis_lugares l2 ON l1.nombre = l2.nombre AND l1.documento_id <> l2.documento_id;

-- D. Personas o lugares que aparecen en más de 10 documentos (relevancia alta)
SELECT nombre_persona, COUNT(*) AS apariciones
FROM analisis_personas_general
GROUP BY nombre_persona
HAVING COUNT(*) > 10
ORDER BY apariciones DESC;

SELECT nombre, COUNT(*) AS apariciones
FROM analisis_lugares
GROUP BY nombre
HAVING COUNT(*) > 10
ORDER BY apariciones DESC;

-- E. Documentos con múltiples delitos registrados
SELECT documento_id, COUNT(*) AS cantidad_delitos
FROM analisis_delitos
GROUP BY documento_id
HAVING COUNT(*) > 1
ORDER BY cantidad_delitos DESC;

-- F. Documentos con mayor cantidad de palabras extraídas (posible mayor valor probatorio)
SELECT d.id, d.archivo, e.total_palabras
FROM documentos d
JOIN estadisticas e ON d.id = e.documento_id
ORDER BY e.total_palabras DESC
LIMIT 20;

-- G. Casos con fechas de creación y fechas de hechos muy distantes (posible retardo procesal)
SELECT m.nuc, m.fecha_creacion, f.fecha, f.tipo
FROM metadatos m
JOIN analisis_fechas f ON m.documento_id = f.documento_id
WHERE ABS(EXTRACT(YEAR FROM m.fecha_creacion) - EXTRACT(YEAR FROM f.fecha)) > 10;

-- H. Organizaciones criminales más mencionadas
SELECT nombre, COUNT(*) AS veces_mencionada
FROM analisis_organizaciones_clasificacion
WHERE tipo_clasificacion = 'fuerzas_ilegales'
GROUP BY nombre
ORDER BY veces_mencionada DESC
LIMIT 20;

-- I. Documentos con palabras clave de rutas de dinero o bienes
SELECT id, archivo
FROM documentos
WHERE texto_extraido ILIKE ANY (ARRAY['%dinero%', '%transferencia%', '%cuenta%', '%bienes%', '%propiedades%'])
   OR analisis ILIKE ANY (ARRAY['%dinero%', '%transferencia%', '%cuenta%', '%bienes%', '%propiedades%']);

-- J. Documentos con posibles familias completas afectadas
SELECT d.id, d.archivo
FROM documentos d
WHERE texto_extraido ILIKE '%familia completa%' OR texto_extraido ILIKE '%toda la familia%' OR texto_extraido ILIKE '%exterminio familiar%' OR texto_extraido ILIKE '%clan familiar%';

-- K. Documentos con fechas de hechos y lugares asociados (para análisis temporal-geográfico)
SELECT f.fecha, l.nombre, d.archivo
FROM analisis_fechas f
JOIN analisis_lugares l ON f.documento_id = l.documento_id
JOIN documentos d ON d.id = f.documento_id
ORDER BY f.fecha;

-- L. Documentos con mayor cantidad de víctimas identificadas
SELECT documento_id, COUNT(*) AS victimas
FROM analisis_personas_clasificacion
WHERE tipo_clasificacion = 'victimas'
GROUP BY documento_id
ORDER BY victimas DESC
LIMIT 20;

-- M. Documentos con palabras clave de alerta de calidad (ejemplo: "verificar", "duda", "inconsistente")
SELECT id, archivo
FROM documentos
WHERE texto_extraido ILIKE ANY (ARRAY['%verificar%', '%duda%', '%inconsistente%', '%contradictorio%', '%requiere verificación%'])
   OR analisis ILIKE ANY (ARRAY['%verificar%', '%duda%', '%inconsistente%', '%contradictorio%', '%requiere verificación%']);

-- FIN DEL SCRIPT
