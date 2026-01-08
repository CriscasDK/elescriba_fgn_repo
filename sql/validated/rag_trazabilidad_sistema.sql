-- =====================================================================
-- SISTEMA RAG CON TRAZABILIDAD Y MEJORA CONTINUA
-- =====================================================================
-- Tablas para historial, feedback y análisis de performance

-- Tabla para historial de consultas RAG
CREATE TABLE IF NOT EXISTS rag_consultas (
    id SERIAL PRIMARY KEY,
    sesion_id UUID DEFAULT gen_random_uuid(),
    usuario_id VARCHAR(100),
    pregunta_original TEXT NOT NULL,
    pregunta_normalizada TEXT,
    tipo_consulta VARCHAR(50), -- 'frecuente', 'rag', 'hibrida'
    metodo_resolucion VARCHAR(50), -- 'vista_materializada', 'busqueda_sql', 'llm_generacion'
    contexto_utilizado JSONB,
    tokens_prompt INTEGER,
    tokens_respuesta INTEGER,
    costo_estimado NUMERIC(10,4),
    tiempo_respuesta_ms INTEGER,
    timestamp_consulta TIMESTAMP DEFAULT NOW(),
    ip_cliente INET,
    user_agent TEXT
);

-- Tabla para respuestas generadas
CREATE TABLE IF NOT EXISTS rag_respuestas (
    id SERIAL PRIMARY KEY,
    consulta_id INTEGER REFERENCES rag_consultas(id) ON DELETE CASCADE,
    respuesta_texto TEXT NOT NULL,
    fuentes_utilizadas JSONB, -- Array de documentos/entidades consultadas
    confianza_score REAL, -- 0.0 - 1.0
    metodo_generacion VARCHAR(50), -- 'template', 'llm_completion', 'hibrido'
    datos_estructurados JSONB, -- Para respuestas que incluyen tablas/graficos
    metadatos_llm JSONB, -- model, temperature, etc
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla para feedback y calificaciones
CREATE TABLE IF NOT EXISTS rag_feedback (
    id SERIAL PRIMARY KEY,
    consulta_id INTEGER REFERENCES rag_consultas(id) ON DELETE CASCADE,
    respuesta_id INTEGER REFERENCES rag_respuestas(id) ON DELETE CASCADE,
    calificacion INTEGER CHECK (calificacion BETWEEN 1 AND 5),
    feedback_texto TEXT,
    aspectos_evaluados JSONB, -- {precision: 4, relevancia: 5, completitud: 3}
    respuesta_esperada TEXT, -- Si el usuario proporciona la respuesta correcta
    timestamp_feedback TIMESTAMP DEFAULT NOW(),
    ip_cliente INET
);

-- Tabla para analítica y mejora continua
CREATE TABLE IF NOT EXISTS rag_analytics (
    id SERIAL PRIMARY KEY,
    fecha DATE DEFAULT CURRENT_DATE,
    total_consultas INTEGER DEFAULT 0,
    consultas_exitosas INTEGER DEFAULT 0,
    consultas_fallidas INTEGER DEFAULT 0,
    tiempo_promedio_ms INTEGER DEFAULT 0,
    costo_total_tokens NUMERIC(10,4) DEFAULT 0,
    calificacion_promedio REAL DEFAULT 0,
    temas_frecuentes JSONB,
    errores_comunes JSONB,
    sugerencias_mejora JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla para cache de respuestas frecuentes
CREATE TABLE IF NOT EXISTS rag_cache (
    id SERIAL PRIMARY KEY,
    pregunta_hash VARCHAR(64) UNIQUE, -- MD5/SHA256 de la pregunta normalizada
    pregunta_normalizada TEXT NOT NULL,
    respuesta_cacheada TEXT NOT NULL,
    fuentes_cache JSONB,
    veces_utilizada INTEGER DEFAULT 1,
    calificacion_promedio REAL,
    ultima_utilizacion TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 days',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_rag_consultas_timestamp ON rag_consultas (timestamp_consulta);
CREATE INDEX IF NOT EXISTS idx_rag_consultas_usuario ON rag_consultas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_rag_consultas_tipo ON rag_consultas (tipo_consulta);
CREATE INDEX IF NOT EXISTS idx_rag_feedback_calificacion ON rag_feedback (calificacion);
CREATE INDEX IF NOT EXISTS idx_rag_cache_hash ON rag_cache (pregunta_hash);
CREATE INDEX IF NOT EXISTS idx_rag_cache_utilizacion ON rag_cache (veces_utilizada DESC);

-- Índices GIN para búsquedas en JSONB
CREATE INDEX IF NOT EXISTS idx_rag_consultas_contexto ON rag_consultas USING GIN (contexto_utilizado);
CREATE INDEX IF NOT EXISTS idx_rag_respuestas_fuentes ON rag_respuestas USING GIN (fuentes_utilizadas);
CREATE INDEX IF NOT EXISTS idx_rag_feedback_aspectos ON rag_feedback USING GIN (aspectos_evaluados);

-- =====================================================================
-- FUNCIONES PARA EL SISTEMA RAG
-- =====================================================================

-- Función para normalizar preguntas (eliminar acentos, minúsculas, etc.)
CREATE OR REPLACE FUNCTION normalizar_pregunta(pregunta TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            translate(
                trim(pregunta),
                'áéíóúñÁÉÍÓÚÑ',
                'aeiounAEIOUN'
            ),
            '[^\w\s]', ' ', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Función para generar hash de pregunta
CREATE OR REPLACE FUNCTION generar_hash_pregunta(pregunta TEXT)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN md5(normalizar_pregunta(pregunta));
END;
$$ LANGUAGE plpgsql;

-- Función para clasificar tipo de consulta
CREATE OR REPLACE FUNCTION clasificar_tipo_consulta(pregunta TEXT)
RETURNS VARCHAR(50) AS $$
DECLARE
    pregunta_norm TEXT;
    palabras_frecuentes TEXT[] := ARRAY[
        'cuantos', 'cuantas', 'total', 'estadisticas', 'dashboard',
        'top', 'listado', 'mayores', 'principales', 'mas mencionados'
    ];
    palabras_rag TEXT[] := ARRAY[
        'como', 'porque', 'que paso', 'explicar', 'analizar', 'describir',
        'impacto', 'relacion', 'conexion', 'influencia'
    ];
BEGIN
    pregunta_norm := normalizar_pregunta(pregunta);
    
    -- Detectar consultas frecuentes
    IF EXISTS (
        SELECT 1 FROM unnest(palabras_frecuentes) AS palabra
        WHERE pregunta_norm LIKE '%' || palabra || '%'
    ) THEN
        RETURN 'frecuente';
    END IF;
    
    -- Detectar consultas que requieren RAG
    IF EXISTS (
        SELECT 1 FROM unnest(palabras_rag) AS palabra
        WHERE pregunta_norm LIKE '%' || palabra || '%'
    ) THEN
        RETURN 'rag';
    END IF;
    
    RETURN 'hibrida';
END;
$$ LANGUAGE plpgsql;

-- Función para registrar consulta
CREATE OR REPLACE FUNCTION registrar_consulta_rag(
    p_usuario_id VARCHAR(100),
    p_pregunta TEXT,
    p_ip_cliente INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    consulta_id INTEGER;
    pregunta_norm TEXT;
    tipo_consulta VARCHAR(50);
BEGIN
    pregunta_norm := normalizar_pregunta(p_pregunta);
    tipo_consulta := clasificar_tipo_consulta(p_pregunta);
    
    INSERT INTO rag_consultas (
        usuario_id, pregunta_original, pregunta_normalizada, 
        tipo_consulta, ip_cliente, user_agent
    ) VALUES (
        p_usuario_id, p_pregunta, pregunta_norm, 
        tipo_consulta, p_ip_cliente, p_user_agent
    ) RETURNING id INTO consulta_id;
    
    RETURN consulta_id;
END;
$$ LANGUAGE plpgsql;

-- Función para buscar en cache
CREATE OR REPLACE FUNCTION buscar_respuesta_cache(pregunta TEXT)
RETURNS TABLE(
    respuesta TEXT,
    fuentes JSONB,
    veces_utilizada INTEGER,
    calificacion_promedio REAL
) AS $$
DECLARE
    hash_pregunta VARCHAR(64);
BEGIN
    hash_pregunta := generar_hash_pregunta(pregunta);
    
    RETURN QUERY
    SELECT 
        rc.respuesta_cacheada,
        rc.fuentes_cache,
        rc.veces_utilizada,
        rc.calificacion_promedio
    FROM rag_cache rc
    WHERE rc.pregunta_hash = hash_pregunta
      AND rc.expires_at > NOW()
    LIMIT 1;
    
    -- Actualizar contador de uso
    UPDATE rag_cache 
    SET veces_utilizada = veces_utilizada + 1,
        ultima_utilizacion = NOW()
    WHERE pregunta_hash = hash_pregunta;
END;
$$ LANGUAGE plpgsql;

-- Función para guardar respuesta en cache
CREATE OR REPLACE FUNCTION guardar_respuesta_cache(
    pregunta TEXT,
    respuesta TEXT,
    fuentes JSONB
)
RETURNS VOID AS $$
DECLARE
    hash_pregunta VARCHAR(64);
BEGIN
    hash_pregunta := generar_hash_pregunta(pregunta);
    
    INSERT INTO rag_cache (
        pregunta_hash, pregunta_normalizada, respuesta_cacheada, fuentes_cache
    ) VALUES (
        hash_pregunta, normalizar_pregunta(pregunta), respuesta, fuentes
    )
    ON CONFLICT (pregunta_hash) DO UPDATE SET
        respuesta_cacheada = EXCLUDED.respuesta_cacheada,
        fuentes_cache = EXCLUDED.fuentes_cache,
        veces_utilizada = rag_cache.veces_utilizada + 1,
        ultima_utilizacion = NOW();
END;
$$ LANGUAGE plpgsql;

-- Función para registrar respuesta
CREATE OR REPLACE FUNCTION registrar_respuesta_rag(
    p_consulta_id INTEGER,
    p_respuesta TEXT,
    p_fuentes JSONB,
    p_confianza REAL DEFAULT NULL,
    p_metodo VARCHAR(50) DEFAULT 'llm_completion',
    p_datos_estructurados JSONB DEFAULT NULL,
    p_metadatos_llm JSONB DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    respuesta_id INTEGER;
BEGIN
    INSERT INTO rag_respuestas (
        consulta_id, respuesta_texto, fuentes_utilizadas,
        confianza_score, metodo_generacion, datos_estructurados, metadatos_llm
    ) VALUES (
        p_consulta_id, p_respuesta, p_fuentes,
        p_confianza, p_metodo, p_datos_estructurados, p_metadatos_llm
    ) RETURNING id INTO respuesta_id;
    
    RETURN respuesta_id;
END;
$$ LANGUAGE plpgsql;

-- Función para registrar feedback
CREATE OR REPLACE FUNCTION registrar_feedback_rag(
    p_consulta_id INTEGER,
    p_respuesta_id INTEGER,
    p_calificacion INTEGER,
    p_feedback_texto TEXT DEFAULT NULL,
    p_aspectos JSONB DEFAULT NULL,
    p_respuesta_esperada TEXT DEFAULT NULL,
    p_ip_cliente INET DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    feedback_id INTEGER;
BEGIN
    INSERT INTO rag_feedback (
        consulta_id, respuesta_id, calificacion, feedback_texto,
        aspectos_evaluados, respuesta_esperada, ip_cliente
    ) VALUES (
        p_consulta_id, p_respuesta_id, p_calificacion, p_feedback_texto,
        p_aspectos, p_respuesta_esperada, p_ip_cliente
    ) RETURNING id INTO feedback_id;
    
    -- Actualizar calificación promedio en cache si existe
    UPDATE rag_cache 
    SET calificacion_promedio = (
        SELECT AVG(rf.calificacion)
        FROM rag_feedback rf
        JOIN rag_consultas rc ON rf.consulta_id = rc.id
        WHERE generar_hash_pregunta(rc.pregunta_original) = rag_cache.pregunta_hash
    )
    WHERE pregunta_hash = (
        SELECT generar_hash_pregunta(rc.pregunta_original)
        FROM rag_consultas rc
        WHERE rc.id = p_consulta_id
    );
    
    RETURN feedback_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- VISTAS PARA ANALÍTICA Y MONITOREO
-- =====================================================================

-- Vista para estadísticas en tiempo real
CREATE OR REPLACE VIEW v_rag_estadisticas_tiempo_real AS
SELECT 
    DATE(timestamp_consulta) as fecha,
    COUNT(*) as total_consultas,
    COUNT(*) FILTER (WHERE tipo_consulta = 'frecuente') as consultas_frecuentes,
    COUNT(*) FILTER (WHERE tipo_consulta = 'rag') as consultas_rag,
    COUNT(*) FILTER (WHERE tipo_consulta = 'hibrida') as consultas_hibridas,
    AVG(tiempo_respuesta_ms) as tiempo_promedio_ms,
    SUM(COALESCE(costo_estimado, 0)) as costo_total,
    COUNT(DISTINCT usuario_id) as usuarios_unicos,
    (
        SELECT AVG(calificacion)
        FROM rag_feedback rf
        JOIN rag_consultas rc ON rf.consulta_id = rc.id
        WHERE DATE(rc.timestamp_consulta) = DATE(rag_consultas.timestamp_consulta)
    ) as calificacion_promedio
FROM rag_consultas
GROUP BY DATE(timestamp_consulta)
ORDER BY fecha DESC;

-- Vista para preguntas frecuentes sin respuesta satisfactoria
CREATE OR REPLACE VIEW v_rag_preguntas_mejorar AS
SELECT 
    rc.pregunta_normalizada,
    COUNT(*) as veces_preguntada,
    AVG(rf.calificacion) as calificacion_promedio,
    COUNT(rf.id) as veces_calificada,
    STRING_AGG(DISTINCT rf.feedback_texto, ' | ') as comentarios_usuarios,
    STRING_AGG(DISTINCT rf.respuesta_esperada, ' | ') as respuestas_esperadas
FROM rag_consultas rc
LEFT JOIN rag_feedback rf ON rc.id = rf.consulta_id
GROUP BY rc.pregunta_normalizada
HAVING COUNT(*) >= 3 AND (AVG(rf.calificacion) IS NULL OR AVG(rf.calificacion) < 3.5)
ORDER BY veces_preguntada DESC, calificacion_promedio ASC NULLS FIRST;

-- Vista para patrones de uso por usuario
CREATE OR REPLACE VIEW v_rag_patrones_usuario AS
SELECT 
    usuario_id,
    COUNT(*) as total_consultas,
    COUNT(DISTINCT DATE(timestamp_consulta)) as dias_activos,
    AVG(tiempo_respuesta_ms) as tiempo_promedio_respuesta,
    STRING_AGG(DISTINCT tipo_consulta, ', ') as tipos_consultas_usadas,
    (
        SELECT AVG(calificacion)
        FROM rag_feedback rf
        WHERE rf.consulta_id IN (
            SELECT id FROM rag_consultas WHERE usuario_id = rc.usuario_id
        )
    ) as satisfaccion_promedio,
    MIN(timestamp_consulta) as primera_consulta,
    MAX(timestamp_consulta) as ultima_consulta
FROM rag_consultas rc
WHERE usuario_id IS NOT NULL
GROUP BY usuario_id
ORDER BY total_consultas DESC;

-- =====================================================================
-- FUNCIONES DE ANALÍTICA AVANZADA
-- =====================================================================

-- Función para generar reporte de mejora continua
CREATE OR REPLACE FUNCTION generar_reporte_mejora_continua(dias_atras INTEGER DEFAULT 30)
RETURNS TABLE(
    categoria TEXT,
    metrica TEXT,
    valor TEXT,
    tendencia TEXT,
    recomendacion TEXT
) AS $$
BEGIN
    RETURN QUERY
    -- Métricas de volumen
    SELECT 
        'Volumen'::TEXT,
        'Total consultas'::TEXT,
        COUNT(*)::TEXT,
        CASE 
            WHEN COUNT(*) > (
                SELECT COUNT(*) FROM rag_consultas 
                WHERE timestamp_consulta >= NOW() - INTERVAL '60 days'
                AND timestamp_consulta < NOW() - INTERVAL '30 days'
            ) THEN 'Creciente'
            ELSE 'Estable'
        END::TEXT,
        'Monitorear capacidad del sistema'::TEXT
    FROM rag_consultas
    WHERE timestamp_consulta >= NOW() - INTERVAL '30 days'
    
    UNION ALL
    
    -- Métricas de satisfacción
    SELECT 
        'Satisfacción'::TEXT,
        'Calificación promedio'::TEXT,
        ROUND(AVG(rf.calificacion), 2)::TEXT,
        CASE 
            WHEN AVG(rf.calificacion) >= 4.0 THEN 'Excelente'
            WHEN AVG(rf.calificacion) >= 3.0 THEN 'Buena'
            ELSE 'Requiere mejora'
        END::TEXT,
        CASE 
            WHEN AVG(rf.calificacion) < 3.0 THEN 'Revisar preguntas con baja calificación'
            ELSE 'Mantener calidad actual'
        END::TEXT
    FROM rag_feedback rf
    JOIN rag_consultas rc ON rf.consulta_id = rc.id
    WHERE rc.timestamp_consulta >= NOW() - INTERVAL '30 days'
    
    UNION ALL
    
    -- Métricas de performance
    SELECT 
        'Performance'::TEXT,
        'Tiempo promedio respuesta (ms)'::TEXT,
        ROUND(AVG(tiempo_respuesta_ms))::TEXT,
        CASE 
            WHEN AVG(tiempo_respuesta_ms) <= 1000 THEN 'Rápido'
            WHEN AVG(tiempo_respuesta_ms) <= 3000 THEN 'Aceptable'
            ELSE 'Lento'
        END::TEXT,
        CASE 
            WHEN AVG(tiempo_respuesta_ms) > 3000 THEN 'Optimizar consultas o agregar cache'
            ELSE 'Performance adecuada'
        END::TEXT
    FROM rag_consultas
    WHERE timestamp_consulta >= NOW() - INTERVAL '30 days'
    AND tiempo_respuesta_ms IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Función para detectar preguntas similares no optimizadas
CREATE OR REPLACE FUNCTION detectar_preguntas_optimizar()
RETURNS TABLE(
    grupo_similar TEXT,
    preguntas_ejemplo TEXT[],
    frecuencia_total INTEGER,
    calificacion_promedio REAL,
    recomendacion TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH preguntas_frecuentes AS (
        SELECT 
            pregunta_normalizada,
            COUNT(*) as frecuencia,
            ARRAY_AGG(DISTINCT pregunta_original ORDER BY pregunta_original) as ejemplos,
            AVG(rf.calificacion) as cal_promedio
        FROM rag_consultas rc
        LEFT JOIN rag_feedback rf ON rc.id = rf.consulta_id
        GROUP BY pregunta_normalizada
        HAVING COUNT(*) >= 3
    )
    SELECT 
        pf.pregunta_normalizada as grupo_similar,
        pf.ejemplos[1:3] as preguntas_ejemplo,
        pf.frecuencia::INTEGER,
        pf.cal_promedio,
        CASE 
            WHEN pf.frecuencia >= 10 AND (pf.cal_promedio IS NULL OR pf.cal_promedio >= 4.0) 
            THEN 'Crear vista materializada para esta consulta'
            WHEN pf.cal_promedio < 3.0 
            THEN 'Mejorar la respuesta para esta pregunta'
            WHEN pf.frecuencia >= 5 
            THEN 'Considerar agregar al cache permanente'
            ELSE 'Monitorear evolución'
        END::TEXT
    FROM preguntas_frecuentes pf
    ORDER BY pf.frecuencia DESC, pf.cal_promedio ASC NULLS FIRST;
END;
$$ LANGUAGE plpgsql;
