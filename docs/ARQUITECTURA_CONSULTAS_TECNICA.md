# Documentación Técnica - Sistema de Consultas Especializadas

## 🎯 **Arquitectura del Sistema de Consultas**

Esta documentación describe la implementación técnica del sistema de consultas especializadas con estrategia híbrida BD + RAG.

---

## 🏗️ **Arquitectura Híbrida BD + RAG**

### **Principio de Diseño**
El sistema implementa una estrategia híbrida que selecciona automáticamente entre Base de Datos (BD) y RAG según el tipo de consulta:

```python
def detectar_consulta_especifica(query):
    """
    Router inteligente que decide el motor de consulta apropiado
    """
    query_lower = query.lower()
    
    # Patrones para consultas de BD (estadísticas)
    bd_patterns = ['cuántos', 'cuántas', 'total', 'ranking', 'listado', 'menciones']
    
    # Patrones para consultas RAG (análisis contextual)
    rag_patterns = ['patrones', 'estructuras', 'cadenas', 'análisis', 'contexto']
    
    if any(pattern in query_lower for pattern in rag_patterns):
        return seleccionar_consulta_rag(query_lower)
    else:
        return seleccionar_consulta_bd(query_lower)
```

---

## 📊 **EJE 2 - VÍCTIMAS (6 Consultas Implementadas)**

### **1. Listado Total de Víctimas (BD)**

**Funcionalidad**: `mostrar_interfaz_victimas_avanzada()`

```python
def ejecutar_consulta_victimas_basica():
    """
    Consulta SQL optimizada para listado de víctimas
    """
    query = """
    SELECT DISTINCT
        p.nombre,
        CASE 
            WHEN UPPER(p.tipo) LIKE '%VICTIM%' THEN 
                CASE 
                    WHEN UPPER(p.tipo) LIKE '%LÍDER%' THEN 'Víctima - Líder'
                    WHEN UPPER(p.tipo) LIKE '%CIVIL%' THEN 'Víctima - Civil'
                    ELSE 'Víctima'
                END
            ELSE p.tipo
        END as tipo,
        COUNT(pd.documento_id) as veces_mencionada,
        string_agg(DISTINCT d.archivo, ', ') as documentos
    FROM personas p
    JOIN personas_documentos pd ON p.id = pd.persona_id
    JOIN documentos d ON pd.documento_id = d.id
    WHERE UPPER(p.tipo) LIKE '%VICTIM%'
    GROUP BY p.nombre, p.tipo
    ORDER BY veces_mencionada DESC;
    """
    return ejecutar_query_con_paginacion(query)
```

### **2. Documentos con Más Víctimas (BD)**

```python
def ejecutar_consulta_documentos_victimas():
    """
    Análisis de concentración de víctimas por documento
    """
    query = """
    SELECT 
        d.archivo,
        d.nuc,
        d.despacho,
        d.cuaderno,
        COUNT(DISTINCT p.id) as total_victimas,
        string_agg(DISTINCT p.nombre, ' | ') as lista_victimas
    FROM documentos d
    JOIN personas_documentos pd ON d.id = pd.documento_id
    JOIN personas p ON pd.persona_id = p.id
    WHERE UPPER(p.tipo) LIKE '%VICTIM%'
    GROUP BY d.id, d.archivo, d.nuc, d.despacho, d.cuaderno
    HAVING COUNT(DISTINCT p.id) > 0
    ORDER BY total_victimas DESC;
    """
    return ejecutar_query_con_paginacion(query)
```

### **3. Víctimas con Roles de Liderazgo (BD)**

```python
def ejecutar_consulta_victimas_liderazgo():
    """
    Clasificación de víctimas por tipo de liderazgo
    """
    query = """
    SELECT DISTINCT
        p.nombre,
        CASE 
            WHEN UPPER(p.tipo) LIKE '%LÍDER%' THEN 'Líder Social/Político'
            WHEN UPPER(p.tipo) LIKE '%MILITANTE%' THEN 'Militante/Activista'
            WHEN UPPER(p.tipo) LIKE '%SINDICALISTA%' THEN 'Sindicalista'
            WHEN UPPER(p.tipo) LIKE '%DIRIGENTE%' THEN 'Dirigente'
            ELSE 'Otro Tipo de Liderazgo'
        END as tipo_liderazgo,
        COUNT(pd.documento_id) as veces_mencionada,
        string_agg(DISTINCT d.archivo, ', ') as documentos
    FROM personas p
    JOIN personas_documentos pd ON p.id = pd.persona_id
    JOIN documentos d ON pd.documento_id = d.id
    WHERE UPPER(p.tipo) LIKE '%VICTIM%' 
      AND (UPPER(p.tipo) LIKE '%LÍDER%' 
           OR UPPER(p.tipo) LIKE '%MILITANTE%' 
           OR UPPER(p.tipo) LIKE '%SINDICALISTA%'
           OR UPPER(p.tipo) LIKE '%DIRIGENTE%')
    GROUP BY p.nombre, p.tipo
    ORDER BY veces_mencionada DESC;
    """
    return ejecutar_query_con_paginacion(query)
```

### **4. Familiares y Deudos (BD)**

```python
def ejecutar_consulta_familiares():
    """
    Identificación de familiares por patrones de apellidos
    """
    query = """
    WITH apellidos_frecuentes AS (
        SELECT 
            SUBSTRING(nombre FROM '\\w+$') as apellido,
            COUNT(*) as frecuencia
        FROM personas
        WHERE UPPER(tipo) LIKE '%VICTIM%' 
          AND nombre ~ '\\w+\\s+\\w+'
        GROUP BY apellido
        HAVING COUNT(*) > 1
    )
    SELECT DISTINCT
        p.nombre,
        af.apellido as apellido_familia,
        af.frecuencia as miembros_familia,
        COUNT(pd.documento_id) as veces_mencionada,
        string_agg(DISTINCT d.archivo, ', ') as documentos
    FROM personas p
    JOIN apellidos_frecuentes af ON SUBSTRING(p.nombre FROM '\\w+$') = af.apellido
    JOIN personas_documentos pd ON p.id = pd.persona_id
    JOIN documentos d ON pd.documento_id = d.id
    WHERE UPPER(p.tipo) LIKE '%VICTIM%'
    GROUP BY p.nombre, af.apellido, af.frecuencia
    ORDER BY af.frecuencia DESC, veces_mencionada DESC;
    """
    return ejecutar_query_con_paginacion(query)
```

### **5. Crímenes de Lesa Humanidad (BD + RAG Híbrido)**

```python
def ejecutar_consulta_crimenes_lesa_humanidad():
    """
    Clasificación automática de crímenes por IA
    """
    query = """
    SELECT 
        d.archivo,
        CASE 
            WHEN UPPER(d.texto_extraido) LIKE '%TORTURA%' THEN 'TORTURA'
            WHEN UPPER(d.texto_extraido) LIKE '%DESAPARICIÓN%' THEN 'DESAPARICIÓN FORZADA'
            WHEN UPPER(d.texto_extraido) LIKE '%ASESINATO%' OR UPPER(d.texto_extraido) LIKE '%HOMICIDIO%' THEN 'ASESINATO'
            WHEN UPPER(d.texto_extraido) LIKE '%EXTERMINIO%' THEN 'EXTERMINIO'
            WHEN UPPER(d.texto_extraido) LIKE '%ESCLAVITUD%' THEN 'ESCLAVITUD'
            WHEN UPPER(d.texto_extraido) LIKE '%VIOLACIÓN%' OR UPPER(d.texto_extraido) LIKE '%VIOLENCIA SEXUAL%' THEN 'VIOLACIÓN/VIOLENCIA SEXUAL'
            WHEN UPPER(d.texto_extraido) LIKE '%PERSECUCIÓN%' THEN 'PERSECUCIÓN'
            WHEN UPPER(d.texto_extraido) LIKE '%APARTHEID%' THEN 'APARTHEID'
            WHEN UPPER(d.texto_extraido) LIKE '%DEPORTACIÓN%' OR UPPER(d.texto_extraido) LIKE '%TRASLADO FORZOSO%' THEN 'DEPORTACIÓN/TRASLADO FORZOSO'
            WHEN UPPER(d.texto_extraido) LIKE '%ENCARCELAMIENTO%' OR UPPER(d.texto_extraido) LIKE '%PRIVACIÓN DE LIBERTAD%' THEN 'ENCARCELAMIENTO/PRIVACIÓN DE LIBERTAD'
            ELSE 'OTROS CRÍMENES'
        END as tipo_crimen,
        SUBSTRING(d.texto_extraido FROM 1 FOR 500) as extracto_relevante,
        d.nuc,
        d.despacho,
        d.fecha_creacion
    FROM documentos d
    WHERE d.texto_extraido IS NOT NULL 
      AND LENGTH(d.texto_extraido) > 100
      AND (
        UPPER(d.texto_extraido) LIKE '%TORTURA%' OR
        UPPER(d.texto_extraido) LIKE '%DESAPARICIÓN%' OR
        UPPER(d.texto_extraido) LIKE '%ASESINATO%' OR
        UPPER(d.texto_extraido) LIKE '%EXTERMINIO%' OR
        UPPER(d.texto_extraido) LIKE '%ESCLAVITUD%' OR
        UPPER(d.texto_extraido) LIKE '%VIOLACIÓN%' OR
        UPPER(d.texto_extraido) LIKE '%PERSECUCIÓN%' OR
        UPPER(d.texto_extraido) LIKE '%APARTHEID%' OR
        UPPER(d.texto_extraido) LIKE '%DEPORTACIÓN%' OR
        UPPER(d.texto_extraido) LIKE '%ENCARCELAMIENTO%'
      )
    ORDER BY d.fecha_creacion DESC;
    """
    return ejecutar_query_con_paginacion(query)
```

### **6. Masacres y Operativos (RAG)**

```python
async def analizar_masacres_operativos(query):
    """
    Análisis contextual de masacres usando RAG
    """
    prompt = f"""
    Analiza los documentos judiciales para identificar patrones relacionados con masacres y operativos militares.
    
    Consulta específica: {query}
    
    Proporciona:
    1. Eventos identificados como masacres o operativos
    2. Patrones temporales y geográficos
    3. Actores involucrados
    4. Métodos utilizados
    5. Contexto histórico relevante
    
    Utiliza únicamente información de los documentos procesados.
    """
    
    return await rag_system.query(prompt, scope="masacres_operativos")
```

---

## 🏛️ **EJE 3 - RESPONSABLES (1 de 3 Implementado)**

### **1. Responsables Más Mencionados (BD) ✅**

```python
def ejecutar_consulta_responsables():
    """
    Clasificación automática de responsables en 10 categorías
    """
    query = """
    SELECT 
        p.nombre as nombre_responsable,
        CASE 
            WHEN UPPER(p.nombre) LIKE '%FARC%' THEN 'FARC'
            WHEN UPPER(p.nombre) LIKE '%PARAMILITAR%' OR UPPER(p.nombre) LIKE '%AUC%' THEN 'PARAMILITARES'
            WHEN UPPER(p.nombre) LIKE '%EJÉRCITO%' OR UPPER(p.nombre) LIKE '%MILITAR%' THEN 'FUERZAS MILITARES'
            WHEN UPPER(p.nombre) LIKE '%POLICÍA%' THEN 'POLICÍA NACIONAL'
            WHEN UPPER(p.nombre) LIKE '%FUNCIONARIO%' OR UPPER(p.nombre) LIKE '%ALCALDE%' OR UPPER(p.nombre) LIKE '%GOBERNADOR%' THEN 'FUNCIONARIOS PÚBLICOS'
            WHEN UPPER(p.nombre) LIKE '%GOBIERNO%' OR UPPER(p.nombre) LIKE '%ESTADO%' THEN 'AGENTES DEL ESTADO'
            WHEN UPPER(p.nombre) LIKE '%CIVIL%' THEN 'POBLACIÓN CIVIL'
            WHEN UPPER(p.nombre) LIKE '%EMPRESA%' OR UPPER(p.nombre) LIKE '%ECONÓMICO%' THEN 'SECTOR PRIVADO'
            WHEN UPPER(p.nombre) LIKE '%TERCERO%' THEN 'TERCEROS'
            ELSE 'OTROS RESPONSABLES'
        END as categoria_responsable,
        COUNT(pd.documento_id) as total_menciones,
        COUNT(DISTINCT pd.documento_id) as documentos_menciones,
        string_agg(DISTINCT d.archivo, ', ') as documentos_lista
    FROM personas p
    JOIN personas_documentos pd ON p.id = pd.persona_id
    JOIN documentos d ON pd.documento_id = d.id
    WHERE UPPER(p.tipo) NOT LIKE '%VICTIM%'
    GROUP BY p.nombre
    HAVING COUNT(pd.documento_id) >= 3  -- Mínimo 3 menciones
    ORDER BY total_menciones DESC;
    """
    return ejecutar_query_con_paginacion(query)
```

### **2. Estructuras Criminales (RAG) 🔄**

```python
async def analizar_estructuras_criminales(query):
    """
    Análisis de organizaciones criminales usando RAG
    """
    prompt = f"""
    Analiza la estructura organizacional de los grupos armados y criminales mencionados en los documentos.
    
    Consulta: {query}
    
    Identifica:
    1. Jerarquías organizacionales
    2. Roles y responsabilidades
    3. Métodos de operación
    4. Territorios de influencia
    5. Conexiones entre diferentes estructuras
    
    Enfócate en la información disponible en los documentos procesados.
    """
    
    return await rag_system.query(prompt, scope="estructuras_criminales")
```

### **3. Cadenas de Mando (RAG) 🔄**

```python
async def analizar_cadenas_mando(query):
    """
    Análisis de cadenas de responsabilidad usando RAG
    """
    prompt = f"""
    Analiza las cadenas de mando y responsabilidad documentadas en el caso.
    
    Consulta: {query}
    
    Examina:
    1. Líneas de autoridad y comando
    2. Responsabilidad por órdenes emitidas
    3. Conocimiento de actividades subordinadas
    4. Omisiones en el deber de supervisión
    5. Patrones de responsabilidad vertical
    
    Utiliza únicamente evidencia documentada en los archivos procesados.
    """
    
    return await rag_system.query(prompt, scope="cadenas_mando")
```

---

## 🔧 **Componentes Técnicos**

### **Sistema de Paginación**

```python
def aplicar_paginacion(df, elementos_por_pagina=25):
    """
    Sistema de paginación uniforme para todas las consultas
    """
    if df.empty:
        return df, 1, 1, 0
    
    total_elementos = len(df)
    total_paginas = (total_elementos + elementos_por_pagina - 1) // elementos_por_pagina
    
    # Selector de página
    pagina_actual = st.selectbox(
        f"📄 Página (Total: {total_paginas})",
        range(1, total_paginas + 1),
        index=0,
        key="paginacion_selector"
    )
    
    inicio = (pagina_actual - 1) * elementos_por_pagina
    fin = inicio + elementos_por_pagina
    
    return df.iloc[inicio:fin], pagina_actual, total_paginas, total_elementos
```

### **Interface Unificada**

```python
def mostrar_documento_detalle(archivo, entidad_nombre, unique_key):
    """
    Formato estándar para mostrar detalles de documentos
    Usado tanto en víctimas como responsables
    """
    metadatos = obtener_metadatos_documento(archivo)
    
    with st.container():
        st.markdown(f"**📄 {archivo}**")
        
        # 5 columnas estándar de metadatos
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            fecha_display = formatear_fecha(metadatos.get('fecha_creacion'))
            st.caption(f"📅 **Fecha:** {fecha_display}")
            st.caption(f"📋 **Tipo:** {metadatos.get('tipo', 'N/A')}")
            st.caption(f"📄 **Páginas:** {metadatos.get('paginas_total', 'N/A')}")
        
        # ... columnas 2-5 con formato estándar
        
        # Menú de acciones estándar
        with st.expander("🔧 Acciones"):
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                if st.button("🔍 Análisis", key=f"analisis_{unique_key}"):
                    mostrar_modal_analisis(archivo)
            
            with col_b:
                if st.button("📄 Texto", key=f"texto_{unique_key}"):
                    mostrar_modal_texto(archivo, entidad_nombre)
            
            with col_c:
                if st.button("📊 Metadatos", key=f"metadatos_{unique_key}"):
                    mostrar_modal_metadatos(metadatos)
            
            with col_d:
                if st.button("📑 PDF", key=f"pdf_{unique_key}"):
                    st.info("🚧 Visualización PDF en desarrollo")
```

### **Gestión de Estado**

```python
def gestionar_estado_consulta():
    """
    Gestión centralizada del estado de la aplicación
    """
    if 'consulta_actual' not in st.session_state:
        st.session_state.consulta_actual = None
    
    if 'filtros_activos' not in st.session_state:
        st.session_state.filtros_activos = {}
    
    if 'resultados_cache' not in st.session_state:
        st.session_state.resultados_cache = {}
    
    if 'modales_abiertos' not in st.session_state:
        st.session_state.modales_abiertos = set()
```

---

## 📊 **Optimizaciones de Performance**

### **Cache de Consultas**

```python
@st.cache_data(ttl=3600)  # Cache por 1 hora
def ejecutar_consulta_con_cache(query, params=None):
    """
    Sistema de cache para consultas frecuentes
    """
    hash_query = hashlib.md5(f"{query}{params}".encode()).hexdigest()
    
    if hash_query in st.session_state.get('cache_consultas', {}):
        return st.session_state.cache_consultas[hash_query]
    
    resultado = ejecutar_query_directa(query, params)
    
    # Almacenar en cache
    if 'cache_consultas' not in st.session_state:
        st.session_state.cache_consultas = {}
    
    st.session_state.cache_consultas[hash_query] = resultado
    return resultado
```

### **Lazy Loading de Documentos**

```python
def cargar_documentos_lazy(lista_documentos, batch_size=5):
    """
    Carga perezosa de documentos para mejorar rendimiento
    """
    if len(lista_documentos) <= batch_size:
        return lista_documentos
    
    # Mostrar primeros documentos
    documentos_iniciales = lista_documentos[:batch_size]
    
    # Botón para cargar más
    if st.button(f"📄 Mostrar más documentos ({len(lista_documentos) - batch_size} restantes)"):
        return lista_documentos
    
    return documentos_iniciales
```

---

## 🔍 **Sistema de Logging y Monitoreo**

```python
import logging

def configurar_logging():
    """
    Configuración del sistema de logging
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/consultas_sistema.log'),
            logging.StreamHandler()
        ]
    )

def log_consulta(tipo_consulta, parametros, tiempo_ejecucion, resultados_count):
    """
    Logging de consultas para análisis de uso
    """
    logger = logging.getLogger('sistema_consultas')
    logger.info(f"Consulta: {tipo_consulta} | Params: {parametros} | "
                f"Tiempo: {tiempo_ejecucion:.2f}s | Resultados: {resultados_count}")
```

---

## 🚀 **Próximas Implementaciones**

### **Eje 3 - Responsables (Completar)**
1. **Estructuras Criminales (RAG)**
2. **Cadenas de Mando (RAG)**

### **Eje 1 - Institucional (Nuevo)**
1. **Respuesta Institucional (RAG)**
2. **Garantías de No Repetición (BD + RAG)**
3. **Reformas Implementadas (BD)**

### **Optimizaciones Avanzadas**
1. **API REST** para consultas externas
2. **Dashboard de métricas** en tiempo real
3. **Análisis predictivo** con Machine Learning
4. **Integración** con sistemas externos

---

*Documentación técnica actualizada: Julio 30, 2025*
*Sistema operativo con arquitectura híbrida BD + RAG implementada*
