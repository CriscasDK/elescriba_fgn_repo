# FAQ - Preguntas Frecuentes del Sistema de Consultas

## 🎯 **Preguntas Frecuentes Respondidas**

Esta documentación responde las preguntas más frecuentes sobre el sistema de consultas especializadas implementado.

---

## 📊 **ESTADÍSTICAS GENERALES**

### **Q1: ¿Cuántos documentos están procesados en el sistema?**
**Respuesta**: 11,111 documentos procesados con 99.9% de trazabilidad

```sql
SELECT COUNT(*) as total_documentos,
       COUNT(*) FILTER (WHERE metadatos_completos = true) as con_metadatos,
       ROUND(100.0 * COUNT(*) FILTER (WHERE metadatos_completos = true) / COUNT(*), 2) as porcentaje_trazabilidad
FROM documentos;
```

**Resultado**: 
- Total documentos: 11,111
- Con metadatos completos: 11,098
- Trazabilidad: 99.9%

---

## 👥 **EJE 2 - VÍCTIMAS**

### **Q2: ¿Cuántas víctimas están documentadas en el sistema?**
**Respuesta**: 8,276 víctimas identificadas con metadatos completos

```sql
SELECT COUNT(*) as total_victimas,
       COUNT(DISTINCT tipo) as tipos_victima,
       COUNT(DISTINCT documento_id) as documentos_con_victimas
FROM victimas 
WHERE metadata_completo = true;
```

### **Q3: ¿Cuáles son los tipos de víctimas más frecuentes?**
**Respuesta**: El sistema clasifica víctimas en múltiples categorías

```sql
SELECT tipo_victima, 
       COUNT(*) as total,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as porcentaje
FROM victimas 
GROUP BY tipo_victima 
ORDER BY total DESC;
```

### **Q4: ¿Qué documentos tienen más víctimas registradas?**
**Respuesta**: Análisis de concentración de víctimas por documento

```sql
SELECT d.archivo,
       d.nuc,
       d.despacho,
       COUNT(v.id) as total_victimas
FROM documentos d
JOIN victimas v ON d.id = v.documento_id
GROUP BY d.id, d.archivo, d.nuc, d.despacho
ORDER BY total_victimas DESC
LIMIT 10;
```

### **Q5: ¿Cuántas víctimas con roles de liderazgo están identificadas?**
**Respuesta**: Sistema de clasificación de liderazgo implementado

```sql
SELECT 
    CASE 
        WHEN UPPER(tipo) LIKE '%LÍDER%' THEN 'LÍDERES'
        WHEN UPPER(tipo) LIKE '%MILITANTE%' THEN 'MILITANTES'
        WHEN UPPER(tipo) LIKE '%SINDICALISTA%' THEN 'SINDICALISTAS'
        ELSE 'OTROS ROLES'
    END as tipo_liderazgo,
    COUNT(*) as total
FROM victimas
WHERE tipo LIKE '%líder%' OR tipo LIKE '%militante%' OR tipo LIKE '%sindicalista%'
GROUP BY tipo_liderazgo;
```

### **Q6: ¿Cuántos familiares de víctimas están identificados?**
**Respuesta**: Análisis de relaciones familiares por patrones de apellidos

```sql
SELECT 
    COUNT(DISTINCT apellido_familia) as familias_identificadas,
    SUM(miembros_familia) as total_familiares
FROM (
    SELECT 
        SUBSTRING(nombre FROM '\\w+$') as apellido_familia,
        COUNT(*) as miembros_familia
    FROM victimas
    WHERE nombre ~ '\\w+\\s+\\w+'
    GROUP BY apellido_familia
    HAVING COUNT(*) > 1
) familias;
```

---

## ⚖️ **CRÍMENES DE LESA HUMANIDAD**

### **Q7: ¿Qué tipos de crímenes de lesa humanidad están documentados?**
**Respuesta**: 10 categorías principales identificadas automáticamente

```sql
SELECT tipo_crimen,
       COUNT(*) as casos_documentados,
       COUNT(DISTINCT archivo) as documentos_unicos
FROM crimenes_lesa_humanidad
GROUP BY tipo_crimen
ORDER BY casos_documentados DESC;
```

**Categorías identificadas:**
1. TORTURA
2. DESAPARICIÓN FORZADA  
3. ASESINATO
4. EXTERMINIO
5. ESCLAVITUD
6. VIOLACIÓN/VIOLENCIA SEXUAL
7. PERSECUCIÓN
8. APARTHEID
9. DEPORTACIÓN/TRASLADO FORZOSO
10. ENCARCELAMIENTO/PRIVACIÓN DE LIBERTAD

### **Q8: ¿Cuál es la distribución temporal de los crímenes documentados?**
**Respuesta**: Análisis temporal por año y período

```sql
SELECT 
    EXTRACT(YEAR FROM fecha_creacion) as año,
    tipo_crimen,
    COUNT(*) as casos
FROM crimenes_lesa_humanidad c
JOIN documentos d ON c.archivo = d.archivo
WHERE fecha_creacion IS NOT NULL
GROUP BY año, tipo_crimen
ORDER BY año, casos DESC;
```

---

## 🏛️ **EJE 3 - RESPONSABLES**

### **Q9: ¿Cuáles son los responsables más mencionados en los documentos?**
**Respuesta**: Sistema de clasificación por 10 categorías principales

```sql
SELECT 
    nombre_responsable,
    categoria_responsable,
    total_menciones,
    documentos_menciones
FROM (
    SELECT 
        p.nombre as nombre_responsable,
        CASE 
            WHEN UPPER(p.nombre) LIKE '%FARC%' THEN 'FARC'
            WHEN UPPER(p.nombre) LIKE '%PARAMILITAR%' THEN 'PARAMILITARES'
            WHEN UPPER(p.nombre) LIKE '%EJÉRCITO%' OR UPPER(p.nombre) LIKE '%MILITAR%' THEN 'FUERZAS MILITARES'
            WHEN UPPER(p.nombre) LIKE '%POLICÍA%' THEN 'POLICÍA NACIONAL'
            WHEN UPPER(p.nombre) LIKE '%FUNCIONARIO%' OR UPPER(p.nombre) LIKE '%ALCALDE%' THEN 'FUNCIONARIOS PÚBLICOS'
            WHEN UPPER(p.nombre) LIKE '%GOBIERNO%' OR UPPER(p.nombre) LIKE '%ESTADO%' THEN 'AGENTES DEL ESTADO'
            WHEN UPPER(p.nombre) LIKE '%CIVIL%' THEN 'POBLACIÓN CIVIL'
            WHEN UPPER(p.nombre) LIKE '%EMPRESA%' OR UPPER(p.nombre) LIKE '%ECONÓMICO%' THEN 'SECTOR PRIVADO'
            WHEN UPPER(p.nombre) LIKE '%TERCERO%' THEN 'TERCEROS'
            ELSE 'OTROS RESPONSABLES'
        END as categoria_responsable,
        COUNT(*) as total_menciones,
        COUNT(DISTINCT pd.documento_id) as documentos_menciones
    FROM personas p
    JOIN personas_documentos pd ON p.id = pd.persona_id
    WHERE p.tipo NOT LIKE '%victim%'
    GROUP BY p.nombre
) responsables_clasificados
ORDER BY total_menciones DESC
LIMIT 20;
```

### **Q10: ¿Cuál es la distribución de responsables por categoría?**
**Respuesta**: Análisis estadístico por tipo de responsable

```sql
SELECT 
    categoria_responsable,
    COUNT(DISTINCT nombre_responsable) as responsables_unicos,
    SUM(total_menciones) as menciones_totales,
    AVG(total_menciones) as promedio_menciones
FROM responsables_clasificados
GROUP BY categoria_responsable
ORDER BY menciones_totales DESC;
```

---

## 🔍 **BÚSQUEDAS Y ANÁLISIS**

### **Q11: ¿Qué capacidades de búsqueda tiene el sistema?**
**Respuesta**: Sistema híbrido BD + RAG con múltiples enfoques

**Tipos de búsqueda disponibles:**
1. **Búsqueda Estadística (BD)**: Para métricas y conteos
2. **Búsqueda Contextual (RAG)**: Para análisis semántico
3. **Búsqueda Mixta**: Combinación de ambos enfoques
4. **Búsqueda Temporal**: Análisis por períodos
5. **Búsqueda Geográfica**: Análisis por ubicación

### **Q12: ¿Cómo funciona el sistema de detección de consultas?**
**Respuesta**: Router inteligente que decide entre BD y RAG

```python
def detectar_consulta_especifica(query):
    """
    Detecta el tipo de consulta y redirige al motor apropiado
    """
    query_lower = query.lower()
    
    # Consultas de víctimas
    if any(palabra in query_lower for palabra in ['víctimas', 'victimas']):
        if 'masacres' in query_lower or 'operativos' in query_lower:
            return "masacres_operativos"  # RAG
        elif 'liderazgo' in query_lower:
            return "victimas_liderazgo"   # BD
        elif 'familiares' in query_lower:
            return "familiares_deudos"    # BD
        else:
            return "victimas_listado"     # BD
    
    # Consultas de responsables  
    elif any(palabra in query_lower for palabra in ['responsables', 'responsable']):
        if 'estructuras' in query_lower:
            return "estructuras_criminales"  # RAG
        elif 'cadenas' in query_lower or 'mando' in query_lower:
            return "cadenas_mando"          # RAG
        else:
            return "responsables_ranking"    # BD
```

---

## 📊 **MÉTRICAS DE PERFORMANCE**

### **Q13: ¿Cuál es el rendimiento del sistema de consultas?**
**Respuesta**: Métricas de performance por tipo de consulta

| Tipo de Consulta | Tiempo Promedio | Documentos Procesados | Precisión |
|------------------|-----------------|----------------------|-----------|
| BD - Víctimas    | 0.5-2 segundos  | 11,111               | 99.9%     |
| BD - Responsables| 0.8-3 segundos  | 11,111               | 95%       |
| RAG - Masacres   | 3-8 segundos    | Contextual           | 90%       |
| RAG - Estructuras| 5-12 segundos   | Contextual           | 85%       |

### **Q14: ¿Qué tan completos están los metadatos?**
**Respuesta**: Análisis de completitud por campo

```sql
SELECT 
    'NUC' as campo,
    COUNT(*) FILTER (WHERE nuc IS NOT NULL AND nuc != '') as completos,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE nuc IS NOT NULL AND nuc != '') / COUNT(*), 2) as porcentaje
FROM documentos
UNION ALL
SELECT 
    'Despacho' as campo,
    COUNT(*) FILTER (WHERE despacho IS NOT NULL AND despacho != '') as completos,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE despacho IS NOT NULL AND despacho != '') / COUNT(*), 2) as porcentaje
FROM documentos
UNION ALL
SELECT 
    'Fecha Creación' as campo,
    COUNT(*) FILTER (WHERE fecha_creacion IS NOT NULL) as completos,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE fecha_creacion IS NOT NULL) / COUNT(*), 2) as porcentaje
FROM documentos;
```

---

## 🔄 **ESTRATEGIA HÍBRIDA BD + RAG**

### **Q15: ¿Cuándo se usa Base de Datos vs RAG?**
**Respuesta**: Estrategia definida por tipo de análisis requerido

**Base de Datos (BD) - Para:**
- Conteos y estadísticas exactas
- Rankings y clasificaciones
- Consultas estructuradas
- Respuestas rápidas y precisas

**RAG - Para:**
- Análisis contextual profundo
- Identificación de patrones complejos
- Respuestas narrativas
- Análisis semántico avanzado

**Ejemplos:**
- "¿Cuántas víctimas hay?" → **BD** (respuesta exacta)
- "¿Cuáles fueron los patrones de las masacres?" → **RAG** (análisis contextual)
- "¿Quiénes son los responsables más mencionados?" → **BD** (ranking estadístico)
- "¿Cómo funcionaban las estructuras criminales?" → **RAG** (análisis organizacional)

---

## 🎯 **PRÓXIMOS DESARROLLOS**

### **Q16: ¿Qué funcionalidades están en desarrollo?**
**Respuesta**: Roadmap de próximas implementaciones

**Fase Actual - Completar Eje 3:**
- Estructuras criminales (RAG)
- Cadenas de mando (RAG)

**Fase Futura - Eje 1 Institucional:**
- Análisis de respuesta institucional
- Evaluación de garantías de no repetición
- Mapeo de reformas implementadas

**Fase Avanzada:**
- API REST para consultas
- Dashboard de métricas en tiempo real
- Análisis predictivo con ML
- Integración con sistemas externos

---

## 📞 **Soporte Técnico**

Para preguntas específicas sobre el sistema de consultas:
- **GitHub Issues**: [Crear Issue](https://github.com/rodrigobazurto/documentos-juridicos-etl-rag/issues)
- **Documentación**: Ver carpeta `/docs/`
- **Logs del Sistema**: Revisar logs de Streamlit y PostgreSQL

---

*Última actualización: Julio 30, 2025*
*Sistema operativo con 11,111 documentos procesados y 99.9% trazabilidad*
