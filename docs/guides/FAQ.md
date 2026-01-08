# 📚 DOCUMENTACIÓN TÉCNICA - CONSULTAS FRECUENTES
## Sistema de Consultas Jurídicas FGN - Estado al 29/07/2025

---

## 🎯 **CONSULTAS SQL IMPLEMENTADAS**

### **1. DIRIGENTES/LÍDERES VICTIMIZADOS**
```sql
-- Triggers: "dirigentes victimizados", "líderes asesinados", "militantes", "sindicalistas"
-- Función: Identifica casos de victimización de líderes sociales y políticos

SELECT DISTINCT 
    d.numero_unico_caso,
    d.numero_interno,
    m.nombre_archivo,
    m.cuaderno,
    m.despacho,
    COALESCE(m.fecha_creacion, m.fecha_procesado) as fecha_documento,
    COUNT(p.id) as num_personas
FROM documentos d
JOIN metadatos m ON d.id = m.documento_id
LEFT JOIN personas p ON d.id = p.documento_id
WHERE (
    d.contenido ~* '(dirigent|líder|president|coordinador|represent).*UP'
    OR d.contenido ~* 'Unión Patriótica.*(dirigent|líder|militante)'
    OR d.contenido ~* '(asesinato|homicidio|muerte).*(dirigent|líder).*UP'
    OR d.contenido ~* 'militante.*(UP|Unión Patriótica)'
)
GROUP BY d.numero_unico_caso, d.numero_interno, m.nombre_archivo, m.cuaderno, m.despacho, fecha_documento
ORDER BY fecha_documento DESC
LIMIT 20;

-- RESULTADO ACTUAL: 8 militantes UP victimizados identificados
```

### **2. DESPLAZAMIENTO FORZADO**
```sql
-- Triggers: "desplazamiento forzado", "exilio", "refugio", "migración forzada"
-- Función: Identifica casos de movilización populacional por violencia

SELECT DISTINCT 
    d.numero_unico_caso,
    d.numero_interno,
    m.nombre_archivo,
    m.despacho,
    COALESCE(m.fecha_creacion, m.fecha_procesado) as fecha_documento
FROM documentos d
JOIN metadatos m ON d.id = m.documento_id
WHERE (
    d.contenido ~* '(desplazamiento|desplazado|desplazar).*forz'
    OR d.contenido ~* '(exilio|exiliad|migr).*(forz|violen)'
    OR d.contenido ~* '(refugio|refugiad).*(violen|amenaz)'
    OR d.contenido ~* '(abandon|desaloj).*(forz|violen)'
    OR d.contenido ~* 'población.*(desplaz|migr).*violen'
)
ORDER BY fecha_documento DESC
LIMIT 20;
```

### **3. CASOS ANTIGUOS (SIN AVANCES)**
```sql
-- Triggers: "casos antiguos", "sin avances", "estancados", "históricos"
-- Función: Muestra documentos más antiguos del corpus

SELECT DISTINCT 
    d.numero_unico_caso,
    d.numero_interno,
    m.nombre_archivo,
    m.cuaderno,
    m.despacho,
    COALESCE(m.fecha_creacion, m.fecha_procesado) as fecha_documento,
    EXTRACT(YEAR FROM COALESCE(m.fecha_creacion, m.fecha_procesado)) as año
FROM documentos d
JOIN metadatos m ON d.id = m.documento_id
WHERE COALESCE(m.fecha_creacion, m.fecha_procesado) IS NOT NULL
ORDER BY fecha_documento ASC
LIMIT 20;

-- RESULTADO ACTUAL: Documentos desde 1990
```

### **4. DISTRIBUCIÓN POR DESPACHOS**
```sql
-- Triggers: "distribución por despachos", "casos por despacho", "despacho"
-- Función: Análisis de carga de trabajo por despacho judicial

SELECT 
    m.despacho,
    COUNT(*) as total_documentos,
    COUNT(DISTINCT d.numero_unico_caso) as casos_unicos,
    MIN(COALESCE(m.fecha_creacion, m.fecha_procesado)) as fecha_mas_antigua,
    MAX(COALESCE(m.fecha_creacion, m.fecha_procesado)) as fecha_mas_reciente
FROM metadatos m
JOIN documentos d ON d.id = m.documento_id
WHERE m.despacho IS NOT NULL AND m.despacho != ''
GROUP BY m.despacho
ORDER BY total_documentos DESC;

-- RESULTADO ACTUAL: Despacho 59 con 11,034 documentos (99% del corpus)
```

### **5. ESPECIALIZACIÓN TERRITORIAL**
```sql
-- Triggers: "especialización territorial", "delitos por región", "territorial"
-- Función: Análisis de tipos de delitos por región/despacho

SELECT 
    m.despacho,
    CASE 
        WHEN d.contenido ~* '(homicidio|asesinato|muerte)' THEN 'Homicidios'
        WHEN d.contenido ~* '(desaparición|desaparecid)' THEN 'Desapariciones'
        WHEN d.contenido ~* '(secuestro|plagio)' THEN 'Secuestros'
        WHEN d.contenido ~* '(tortura|maltrato)' THEN 'Torturas'
        WHEN d.contenido ~* '(amenaza|intimidación)' THEN 'Amenazas'
        ELSE 'Otros delitos'
    END as tipo_delito,
    COUNT(*) as total_casos
FROM documentos d
JOIN metadatos m ON d.id = m.documento_id
WHERE m.despacho IS NOT NULL
GROUP BY m.despacho, tipo_delito
ORDER BY m.despacho, total_casos DESC;
```

### **6. TIPOS DOCUMENTALES**
```sql
-- Triggers: "tipos de documentos", "series documentales", "documentales"
-- Función: Análisis de completitud y tipos de series/subseries

SELECT 
    m.serie,
    m.subserie,
    COUNT(*) as total_documentos,
    COUNT(CASE WHEN m.cuaderno IS NOT NULL AND m.cuaderno != '' THEN 1 END) as con_cuaderno,
    COUNT(CASE WHEN m.folio_inicial IS NOT NULL THEN 1 END) as con_folio,
    ROUND(
        COUNT(CASE WHEN m.cuaderno IS NOT NULL AND m.cuaderno != '' THEN 1 END) * 100.0 / COUNT(*), 
        1
    ) as porcentaje_completitud
FROM metadatos m
WHERE m.serie IS NOT NULL AND m.serie != ''
GROUP BY m.serie, m.subserie
ORDER BY total_documentos DESC;
```

### **7. RUTAS DE DINERO Y BIENES**
```sql
-- Triggers: "dinero en los casos", "bienes y propiedades", "rutas financieras"
-- Función: Casos con componente económico/patrimonial

SELECT DISTINCT 
    d.numero_unico_caso,
    d.numero_interno,
    m.nombre_archivo,
    m.despacho,
    COALESCE(m.fecha_creacion, m.fecha_procesado) as fecha_documento
FROM documentos d
JOIN metadatos m ON d.id = m.documento_id
WHERE (
    d.contenido ~* '(dinero|peso|dólar|efectivo)'
    OR d.contenido ~* '(propiedad|bien|tierra|finca|lote)'
    OR d.contenido ~* '(patrimonio|riqueza|activo)'
    OR d.contenido ~* '(transferencia|transacción|pago)'
    OR d.contenido ~* '(cuenta|banco|financier)'
    OR d.contenido ~* '(despoj|apropiación|usurpación).*tierra'
)
ORDER BY fecha_documento DESC
LIMIT 20;
```

---

## 🔧 **FUNCIÓN DE DETECCIÓN AUTOMÁTICA**

### **`detectar_consulta_especifica()`** en `interfaz_fiscales.py`
```python
def detectar_consulta_especifica(consulta):
    """
    Detecta y ejecuta consultas especializadas basadas en palabras clave
    
    Parámetros:
    - consulta (str): Texto de la consulta del usuario
    
    Retorna:
    - tuple: (sql_query, titulo_reporte) si hay coincidencia
    - None: Si no se detecta consulta especializada
    """
    
    consulta_lower = consulta.lower()
    
    # Mapa de consultas especializadas
    consultas_especiales = {
        'dirigentes': {
            'keywords': ['dirigent', 'líder', 'militante', 'sindicalista'],
            'title': "🎯 Dirigentes y Líderes Victimizados",
            'sql': SQL_DIRIGENTES_VICTIMIZADOS
        },
        'desplazamiento': {
            'keywords': ['desplazamiento', 'exilio', 'refugio', 'migración forzada'],
            'title': "📍 Casos de Desplazamiento Forzado",
            'sql': SQL_DESPLAZAMIENTO_FORZADO
        },
        # ... resto de consultas
    }
    
    # Lógica de detección y ejecución
    for categoria, config in consultas_especiales.items():
        if any(keyword in consulta_lower for keyword in config['keywords']):
            return config['sql'], config['title']
    
    return None
```

---

## 📊 **MÉTRICAS DE COBERTURA**

### **Estado Actual de Implementación:**
| **Categoría** | **Consultas Implementadas** | **Cobertura** | **Estado** |
|---------------|------------------------------|---------------|-------------|
| **Víctimas** | 7/8 consultas principales | 87.5% | ✅ |
| **Procedimientos** | 3/7 consultas identificadas | 42.9% | 🔄 |
| **Temporal** | 2/5 consultas históricas | 40.0% | 🔄 |
| **Geográfico** | 2/4 análisis territoriales | 50.0% | 🔄 |
| **Redes** | 1/9 análisis de conexiones | 11.1% | 🆕 |

### **Consultas Pendientes para Mañana:**
1. **Procedimientos Específicos:**
   - Investigaciones preliminares vs indagaciones
   - Estado procesal de casos por NUC
   - Decisiones de archivo y sus causas

2. **Análisis Temporal Avanzado:**
   - Duración promedio de casos
   - Casos por año/mes de inicio
   - Patrones estacionales en victimización

3. **Análisis de Redes:**
   - Víctimas recurrentes por caso
   - Organizaciones más afectadas
   - Conexiones entre casos por NUC

---

## 🗂️ **ESTRUCTURA DE ARCHIVOS**

```
/documentos_judiciales/
│
├── RESUMEN_EJECUTIVO_29JUL2025.md          # Este documento
├── DOCUMENTACION_CONSULTAS_FRECUENTES.md  # Consultas implementadas
├── test_nuevas_consultas.md               # Casos de prueba
│
├── interfaz_fiscales.py                   # ✅ Interface principal
├── corregir_cuadernos_folios.py          # ✅ Migración cuadernos
├── actualizar_fechas_creacion.py         # ✅ Migración fechas
├── migracion_campos_pendientes.py        # ✅ Migración 12 campos
├── analisis_mapeo_json_bd.py            # ✅ Análisis previo
│
└── json_files/                          # Archivos fuente JSON
    ├── 2015005.204_24M_6215C3_...json
    ├── 201500520.4_27AJ_6215C3_...json
    └── ... (400+ archivos)
```

---

## 🚀 **GUÍA DE USO MAÑANA**

### **1. Activar Entorno:**
```bash
cd /home/lab4/scripts/documentos_judiciales
source venv_docs/bin/activate
streamlit run interfaz_fiscales.py --server.port=8503
```

### **2. Probar Consultas Sistemáticamente:**
```
URL: http://localhost:8503

Queries de Prueba:
- "dirigentes victimizados"         → Debe mostrar 8 militantes UP
- "casos antiguos"                  → Documentos desde 1990
- "distribución por despachos"      → Despacho 59 con 11k docs
- "desplazamiento forzado"          → Casos de migración forzada
- "especialización territorial"     → Delitos por región
- "tipos de documentos"             → Series y completitud
- "dinero en los casos"             → Componente económico
```

### **3. Documentar Resultados:**
- Tiempo de respuesta de cada consulta
- Relevancia de resultados mostrados
- Casos donde se necesita ajuste fino
- Ideas para consultas adicionales

---

## 📝 **NOTAS PARA DESARROLLO FUTURO**

### **Optimizaciones Identificadas:**
1. **Índices de Texto**: Considerar índices GIN para búsquedas ~*
2. **Cache de Consultas**: Implementar cache para consultas frecuentes
3. **Paginación**: Para consultas que retornen >100 resultados
4. **Exportación**: Función para exportar resultados a Excel/CSV

### **Funcionalidades Sugeridas:**
1. **Dashboard Ejecutivo**: Métricas globales del corpus
2. **Alertas Automáticas**: Nuevos casos que coincidan con patrones
3. **Análisis Temporal**: Líneas de tiempo interactivas
4. **Mapas Geográficos**: Visualización territorial de casos

---

**📅 Estado:** LISTO PARA REVISIÓN MAÑANA 30/07/2025  
**⏰ Próxima sesión:** Revisión sistemática consultas frecuentes  
**🎯 Objetivo:** Completar las 33 consultas del análisis original  

**✅ SISTEMA COMPLETAMENTE OPERATIVO Y DOCUMENTADO** 📚
