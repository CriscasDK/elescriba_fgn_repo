import os
import psycopg2
import psycopg2.extras

# --- Función auxiliar para aplicar filtro universal ---
def aplicar_filtro_universal(entidades, externos):
    # Combina entidades detectadas y filtros externos
    filtros = {}
    filtros.update({k: v for k, v in externos.items() if v})
    filtros.update({k: v for k, v in entidades.items() if v})
    return filtros

# Función mejorada con análisis IA detallado y metadatos completos
def obtener_detalle_victima_completo(nombre):
    """Versión mejorada con todas las características de Streamlit"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Menciones: contar en personas
    cur.execute("""
        SELECT COUNT(*) FROM personas WHERE nombre = %s
    """, (nombre,))
    menciones = cur.fetchone()[0] if cur.rowcount else 0
    
    # Documentos relacionados con TODA la información necesaria
    cur.execute("""
        SELECT d.id, d.archivo, d.nuc, d.despacho, d.created_at, d.fecha,
               d.serie, d.codigo, d.tipo_documental, d.texto_extraido, d.analisis_ia,
               m.departamento, m.municipio, m.longitud_texto, m.numero_paginas
        FROM documentos d
        LEFT JOIN metadatos m ON m.documento_id = d.id
        JOIN personas p ON p.documento_id = d.id
        WHERE p.nombre = %s
        ORDER BY d.created_at DESC
        LIMIT 10
    """, (nombre,))
    
    documentos = []
    for row in cur.fetchall():
        doc = {
            "id": row[0], "archivo": row[1], "nuc": row[2], "despacho": row[3], 
            "created_at": row[4], "fecha": row[5], "serie": row[6], "codigo": row[7],
            "tipo_documental": row[8], "texto_extraido": row[9], "analisis_ia": row[10],
            "departamento": row[11], "municipio": row[12], "longitud_texto": row[13],
            "numero_paginas": row[14]
        }
        documentos.append(doc)
    
    # Análisis IA mejorado para la víctima
    analisis_ia = f"""**Análisis IA para {nombre}:**
    
📊 **Presencia en documentos:** {menciones} menciones encontradas
📁 **Contexto documental:** Aparece en {len(documentos)} documentos judiciales
⚖️ **Relevancia jurídica:** Víctima documentada en procedimientos judiciales
📅 **Rango temporal:** Documentos procesados del sistema judicial

💡 **Interpretación:** Esta persona ha sido identificada como víctima en múltiples expedientes, 
lo que indica su relevancia en casos de violaciones a derechos humanos o conflicto armado."""
    
    cur.close()
    conn.close()
    return {
        "nombre": nombre,
        "menciones": menciones,
        "documentos": documentos,
        "analisis_ia": analisis_ia
    }

def obtener_metadatos_documento(archivo):
    """Obtiene todos los metadatos de un documento específico (como en Streamlit)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Obtener todos los campos de metadatos
        cur.execute("""
            SELECT m.*, d.archivo, d.nuc, d.despacho, d.fecha, d.serie, d.codigo,
                   d.tipo_documental, d.texto_extraido, d.analisis_ia
            FROM metadatos m
            JOIN documentos d ON m.documento_id = d.id
            WHERE d.archivo = %s
        """, (archivo,))
        
        resultado = cur.fetchone()
        
        if resultado:
            # Convertir a diccionario
            metadatos = dict(resultado)
            
            # Convertir valores None a texto legible
            for key, value in metadatos.items():
                if value is None:
                    metadatos[key] = "No disponible"
                else:
                    metadatos[key] = str(value)
            
            return metadatos
        else:
            return {}
            
    except Exception as e:
        print(f"Error obteniendo metadatos: {str(e)}")
        return {}
    finally:
        cur.close()
        conn.close()

# Versión mejorada de obtener_detalle_victima que usa la función completa
def obtener_detalle_victima(nombre):
    return obtener_detalle_victima_completo(nombre)

# Configuración de conexión
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
        user=os.getenv('POSTGRES_USER', 'docs_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'docs_password_2025')
    )
    return conn

# Paginación real para víctimas
def obtener_victimas_paginadas(page=1, page_size=20):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Consulta flexible: permite cambiar el filtro y la tabla si se requiere
    cur.execute("SELECT COUNT(*) FROM personas;")
    res = cur.fetchone()
    total = res[0] if res and len(res) > 0 else 0
    if not isinstance(page, int) or page < 1:
        page = 1
    if not isinstance(page_size, int) or page_size < 1:
        page_size = 20
    if total == 0:
        cur.close()
        conn.close()
        return [], 0
    start = (page - 1) * page_size
    try:
        cur.execute("""
            SELECT nombre, COUNT(*) as menciones
            FROM personas
            GROUP BY nombre
            ORDER BY menciones DESC
            OFFSET %s LIMIT %s
        """, (start, page_size))
        victimas = [dict(row) for row in cur.fetchall()]
    except Exception:
        victimas = []
    cur.close()
    conn.close()
    return victimas, total
# Fuentes simuladas para una víctima
def obtener_fuentes_victima(nombre):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fuentes BD: usar campos reales
    cur.execute("""
        SELECT d.archivo, d.nuc, d.despacho, d.estado, d.created_at
        FROM documentos d
        JOIN personas p ON p.documento_id = d.id
        WHERE p.nombre = %s
        ORDER BY d.created_at DESC
        LIMIT 10
    """, (nombre,))
    fuentes_bd = [
        {
            "archivo": row[0],
            "nuc": row[1],
            "despacho": row[2],
            "estado": row[3],
            "fecha": row[4]
        } for row in cur.fetchall()
    ]
    # Fuentes RAG: usar la pregunta completa para análisis semántico
    try:
        from src.core.sistema_rag_completo import SistemaRAGTrazable
        sistema_rag = SistemaRAGTrazable()
        import asyncio
        # Si el frontend provee la consulta completa, úsala; si no, usa el nombre
        pregunta = nombre if not isinstance(nombre, str) else nombre
        respuesta_rag = asyncio.run(sistema_rag._resolver_consulta_rag(pregunta))
        fuentes_rag = respuesta_rag.fuentes if hasattr(respuesta_rag, 'fuentes') else []
    except Exception as e:
        fuentes_rag = [{"error": f"No se pudo obtener fuentes RAG: {e}"}]
    cur.close()
    conn.close()
    return fuentes_bd, fuentes_rag
# Detalle simulado de víctima
def obtener_detalle_victima(nombre):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Menciones: contar en personas
    cur.execute("""
        SELECT COUNT(*) FROM personas WHERE nombre = %s
    """, (nombre,))
    menciones = cur.fetchone()[0] if cur.rowcount else 0
    
    # Documentos relacionados con TODA la información necesaria
    cur.execute("""
        SELECT d.id, d.archivo, d.nuc, d.despacho, d.created_at, d.fecha,
               d.serie, d.codigo, d.tipo_documental, d.texto_extraido, d.analisis_ia,
               m.departamento, m.municipio, m.longitud_texto, m.numero_paginas
        FROM documentos d
        LEFT JOIN metadatos m ON m.documento_id = d.id
        JOIN personas p ON p.documento_id = d.id
        WHERE p.nombre = %s
        ORDER BY d.created_at DESC
        LIMIT 10
    """, (nombre,))
    
    documentos = []
    for row in cur.fetchall():
        doc = {
            "id": row[0], "archivo": row[1], "nuc": row[2], "despacho": row[3], 
            "created_at": row[4], "fecha": row[5], "serie": row[6], "codigo": row[7],
            "tipo_documental": row[8], "texto_extraido": row[9], "analisis_ia": row[10],
            "departamento": row[11], "municipio": row[12], "longitud_texto": row[13],
            "numero_paginas": row[14]
        }
        documentos.append(doc)
    
    # Análisis IA mejorado para la víctima
    analisis_ia = f"""**Análisis IA para {nombre}:**
    
📊 **Presencia en documentos:** {menciones} menciones encontradas
📁 **Contexto documental:** Aparece en {len(documentos)} documentos judiciales
⚖️ **Relevancia jurídica:** Víctima documentada en procedimientos judiciales
📅 **Rango temporal:** Documentos procesados del sistema judicial

💡 **Interpretación:** Esta persona ha sido identificada como víctima en múltiples expedientes, 
lo que indica su relevancia en casos de violaciones a derechos humanos o conflicto armado."""
    
    cur.close()
    conn.close()
    return {
        "nombre": nombre,
        "menciones": menciones,
        "documentos": documentos,
        "analisis_ia": analisis_ia
    }
# Opciones simuladas para los filtros
def obtener_opciones_nuc():
    return [f"NUC-{i:04d}" for i in range(1, 51)]

def obtener_opciones_departamento():
    return [
        "Antioquia", "Atlántico", "Bogotá D.C.", "Bolívar", "Boyacá",
        "Caldas", "Caquetá", "Cauca", "Cesar", "Córdoba", "Cundinamarca",
        "Chocó", "Huila", "La Guajira", "Magdalena", "Meta", "Nariño",
        "Norte de Santander", "Putumayo", "Quindío", "Risaralda",
        "Santander", "Sucre", "Tolima", "Valle del Cauca", "Arauca",
        "Casanare", "Guainía", "Guaviare", "Vaupés", "Vichada"
    ]

def obtener_opciones_municipio():
    return [
        "Medellín", "Bogotá", "Cali", "Barranquilla", "Cartagena",
        "Bucaramanga", "Pereira", "Ibagué", "Cúcuta", "Villavicencio",
        "Manizales", "Neiva", "Pasto", "Santa Marta", "Valledupar"
    ]

def obtener_opciones_tipo_documento():
    return [
        "Sentencia", "Auto", "Informe", "Resolución", "Oficio", "Acta"
    ]

def obtener_opciones_despacho():
    return [
        "Juzgado 1", "Juzgado 2", "Juzgado 3", "Fiscalía 1", "Fiscalía 2"
    ]
# core/consultas.py
"""
Funciones de negocio para consultas, acceso a BD y procesamiento IA.
Todas las funciones aquí deben ser independientes del frontend.
"""

def ejecutar_consulta(consulta, nucs=None, departamento=None, municipio=None, tipo_documento=None, despacho=None):
    # --- Integración del selector inteligente y análisis de oraciones ---
    from src.core.agente_oraciones_simple import crear_agente_oraciones_simple
    agente = crear_agente_oraciones_simple()
    plan = agente.analizar_consulta_completa(consulta, filtros_externos={
        "nucs": nucs,
        "departamento": departamento,
        "municipio": municipio,
        "tipo_documento": tipo_documento,
        "despacho": despacho
    })

    # Inicializar resultados
    respuesta_ia = ""
    victimas = []
    fuentes = []
    trazabilidad = []

    # Procesar cada oración según estrategia
    import asyncio
    from src.core.sistema_rag_completo import SistemaRAGTrazable
    sistema_rag = SistemaRAGTrazable()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    for oracion in plan.oraciones_analizadas:
        try:
            # Aplicar filtro universal modularmente
            filtros_universales = aplicar_filtro_universal(oracion.entidades_detectadas, {
                "nucs": nucs,
                "departamento": departamento,
                "municipio": municipio,
                "tipo_documento": tipo_documento,
                "despacho": despacho
            })
            if oracion.estrategia.value in ["bd_directa", "filtro_aplicado"]:
                filtros = []
                params = []
                nucs_ = filtros_universales.get("nucs")
                departamento_ = filtros_universales.get("departamento")
                municipio_ = filtros_universales.get("municipio")
                tipo_documento_ = filtros_universales.get("tipo_documento")
                despacho_ = filtros_universales.get("despacho")
                if nucs_ and '__ALL__' not in nucs_:
                    filtros.append("d.nuc = ANY(%s)")
                    params.append(nucs_)
                if departamento_:
                    filtros.append("departamento = %s")
                    params.append(departamento_)
                if municipio_:
                    filtros.append("municipio = %s")
                    params.append(municipio_)
                if tipo_documento_:
                    filtros.append("tipo = %s")
                    params.append(tipo_documento_)
                if despacho_:
                    filtros.append("despacho = %s")
                    params.append(despacho_)
                where = " AND ".join(filtros) if filtros else "1=1"
                # Consulta de víctimas
                cur.execute(f"""
                    SELECT nombre, COUNT(*) as menciones
                    FROM personas
                    WHERE {where}
                    GROUP BY nombre
                    ORDER BY menciones DESC
                    LIMIT 10
                """, params)
                victimas += [dict(row) for row in cur.fetchall()]
                # Consulta de fuentes
                cur.execute(f"""
                    SELECT archivo, nuc, despacho, estado, created_at
                    FROM documentos
                    WHERE {where}
                    ORDER BY created_at DESC
                    LIMIT 10
                """, params)
                fuentes += [
                    {
                        "archivo": row[0],
                        "nuc": row[1],
                        "despacho": row[2],
                        "estado": row[3],
                        "fecha": row[4]
                    } for row in cur.fetchall()
                ]
            elif oracion.estrategia.value == "rag_semantico":
                # Consulta semántica RAG con template/contexto y filtros universales
                try:
                    if hasattr(sistema_rag, 'templates') and 'pregunta_compleja' in sistema_rag.templates:
                        template = sistema_rag.templates['pregunta_compleja']
                        contexto_sql = f"Filtros aplicados: " + ", ".join([f"{k}={v}" for k, v in filtros_universales.items() if v])
                        instrucciones = (
                            "Responde de forma extensa y estructurada, usando subtítulos, listas, ejemplos y referencias documentales. "
                            "Incluye contexto relevante, patrones, explicaciones y citas. Usa formato Markdown. Si no hay suficiente información, explica por qué."
                        )
                        prompt = (
                            f"{instrucciones}\n\n" +
                            template.format(
                                contexto_sql=contexto_sql,
                                respuesta_llm=oracion.texto_original,
                                fuentes_detalle=""
                            )
                        )
                        respuesta_rag = asyncio.run(sistema_rag._resolver_consulta_rag(prompt))
                    else:
                        respuesta_rag = asyncio.run(sistema_rag._resolver_consulta_rag(oracion.texto_original))
                    
                    # Validación robusta de respuesta_rag
                    if respuesta_rag is not None:
                        texto_rag = respuesta_rag.texto if hasattr(respuesta_rag, 'texto') else "Sin respuesta RAG"
                        respuesta_ia += f"[RAG] {oracion.texto_original}: {texto_rag}\n"
                        
                        # Trazabilidad y chunks completos - con validaciones
                        if hasattr(respuesta_rag, 'fuentes') and respuesta_rag.fuentes is not None:
                            for fuente in respuesta_rag.fuentes:
                                if fuente is not None:
                                    trazabilidad.append(fuente)
                        
                        if hasattr(respuesta_rag, 'chunks') and respuesta_rag.chunks is not None:
                            respuesta_ia += "\n[CHUNKS]\n"
                            for chunk in respuesta_rag.chunks:
                                if chunk is not None and isinstance(chunk, dict):
                                    respuesta_ia += f"Fuente: {chunk.get('fuente', chunk.get('nombre_archivo', 'N/A'))} | Página: {chunk.get('pagina', 'N/A')} | Párrafo: {chunk.get('parrafo', 'N/A')} | Texto: {chunk.get('texto', '')[:500]}...\n"
                    else:
                        respuesta_ia += f"[RAG] {oracion.texto_original}: Respuesta RAG vacía\n"
                except Exception as e:
                    respuesta_ia += f"[RAG ERROR] {oracion.texto_original}: {e}\n"
            else:
                respuesta_ia += f"[SKIP] {oracion.texto_original}: Estrategia no reconocida\n"
        except Exception as e:
            respuesta_ia += f"[ERROR] {oracion.texto_original}: {e}\n"
    cur.close()
    conn.close()
    # Eliminar duplicados
    victimas = [dict(t) for t in {tuple(d.items()) for d in victimas}]
    fuentes = [dict(t) for t in {tuple(d.items()) for d in fuentes}]
    return {
        "respuesta_ia": respuesta_ia.strip(),
        "victimas": victimas,
        "fuentes": fuentes,
        "trazabilidad": trazabilidad,
        "plan": {
            "estrategia_principal": plan.estrategia_principal,
            "oraciones_analizadas": [o.__dict__ for o in plan.oraciones_analizadas],
            "filtros_combinados": plan.filtros_combinados,
            "confianza_total": plan.confianza_total
        }
    }

# Puedes agregar aquí más funciones de negocio, por ejemplo:
# - obtener_opciones_nuc
# - obtener_opciones_departamento
# - obtener_opciones_municipio
# - obtener_opciones_tipo_documento
# - obtener_opciones_despacho
