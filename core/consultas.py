import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple, Any, Union

# Importar constantes centralizadas (sanitización v3.3)
from config.constants import ENTIDADES_NO_PERSONAS, PALABRAS_ANALISIS

# --- Función auxiliar para aplicar filtro universal ---
def aplicar_filtro_universal(entidades, externos):
    # Combina entidades detectadas y filtros externos
    # PRIORIDAD: externos > entidades detectadas (los parámetros externos tienen prioridad)
    filtros = {}
    filtros.update({k: v for k, v in entidades.items() if v})  # Primero entidades AI
    filtros.update({k: v for k, v in externos.items() if v})   # Luego externos (sobreescriben)
    return filtros

# Función mejorada con análisis IA detallado y metadatos completos
def obtener_detalle_victima_completo(nombre):
    """Versión mejorada con todas las características de Streamlit"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Menciones: contar en personas (con búsqueda flexible)
    # ✅ USAR unaccent para ignorar tildes: "guzman" matchea con "guzmán"
    cur.execute("""
        SELECT COUNT(*) FROM personas
        WHERE unaccent(LOWER(nombre)) LIKE unaccent(LOWER(%s)) AND tipo ILIKE %s
    """, (f'%{nombre}%', '%victim%'))
    result = cur.fetchone()
    menciones = result[0] if result else 0

    # Documentos relacionados - CON TODOS LOS METADATOS NECESARIOS
    cur.execute("""
        SELECT DISTINCT
            d.archivo,
            m.nuc,
            m.fecha_creacion as fecha,
            m.despacho,
            m.detalle as tipo_documental,
            m.serie,
            m.codigo,
            d.analisis as analisis_ia,
            d.texto_extraido,
            COALESCE(d.texto_extraido, d.analisis, '') as contenido,
            -- Metadatos completos adicionales
            d.hash_sha256,
            m.cuaderno,
            m.folio_inicial,
            m.folio_final,
            m.subserie,
            d.paginas,
            d.tamaño_mb,
            d.estado,
            m.fecha_procesado,
            m.version_sistema,
            d.ruta,
            m.ruta_documento,
            m.paginas_total
        FROM personas p
        JOIN documentos d ON p.documento_id = d.id
        LEFT JOIN metadatos m ON d.id = m.documento_id
        WHERE unaccent(LOWER(p.nombre)) LIKE unaccent(LOWER(%s)) AND p.tipo ILIKE %s
        ORDER BY m.fecha_creacion DESC NULLS LAST
    """, (f'%{nombre}%', '%victim%'))

    documentos = []
    for row in cur.fetchall():
        doc = {
            # Campos básicos
            "archivo": row[0], "nuc": row[1], "fecha": row[2], "despacho": row[3],
            "tipo_documental": row[4], "serie": row[5], "codigo": row[6],
            "analisis_ia": row[7], "texto_extraido": row[8], "contenido": row[9],
            # Metadatos completos adicionales
            "hash_sha256": row[10],
            "cuaderno": row[11],
            "folio_inicial": row[12],
            "folio_final": row[13],
            "subserie": row[14],
            "paginas": row[15],
            "tamano_mb": row[16],  # tamaño_mb
            "estado": row[17],
            "fecha_procesado": row[18],
            "version_sistema": row[19],
            "ruta": row[20] or row[21],  # ruta o ruta_documento
            "fecha_creacion": row[2]  # Alias para consistencia
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
            SELECT m.*, d.archivo, m.nuc, m.despacho, m.fecha_creacion as fecha, m.serie, m.codigo,
                   m.detalle as tipo_documental, d.texto_extraido, d.analisis as analisis_ia
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
    cur = conn.cursor()  # Cursor normal, no DictCursor

    # Validación robusta de parámetros
    try:
        page = int(page) if page is not None else 1
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = int(page_size) if page_size is not None else 20
    except (ValueError, TypeError):
        page_size = 20

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20

    # Inicializar total a 0 para asegurar que siempre esté definido
    total = 0

    # Consulta SOLO VÍCTIMAS - corregida
    try:
        cur.execute("SELECT COUNT(*) FROM personas WHERE tipo ILIKE '%victim%' AND tipo NOT ILIKE '%victimario%';")
        res = cur.fetchone()
        total = res[0] if res and len(res) > 0 else 0
    except Exception as e:
        print(f"Error en count query: {e}")
        cur.close()
        conn.close()
        return [], 0

    if total == 0:
        cur.close()
        conn.close()
        return [], 0

    start = (page - 1) * page_size

    # Ejecutar consulta principal con named parameters (evita error "tuple index out of range")
    try:
        cur.execute("""
            SELECT nombre, COUNT(*) as menciones
            FROM personas
            WHERE tipo ILIKE %(victim_pattern)s AND tipo NOT ILIKE %(victimario_pattern)s
            GROUP BY nombre
            ORDER BY menciones DESC
            OFFSET %(offset)s LIMIT %(limit)s
        """, {
            'victim_pattern': '%victim%',
            'victimario_pattern': '%victimario%',
            'offset': start,
            'limit': page_size
        })
        rows = cur.fetchall()
        victimas = []
        for row in rows:
            if row and len(row) >= 2:
                victimas.append({"nombre": row[0], "menciones": row[1]})
    except Exception as e:
        print(f"Error en main query: {e}")
        import traceback
        traceback.print_exc()
        victimas = []

    cur.close()
    conn.close()
    return victimas, total
# Fuentes simuladas para una víctima
def obtener_fuentes_victima(nombre):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Fuentes BD: usar campos reales
    # ✅ CORRECCIÓN: Usar unaccent y LIKE para búsqueda flexible, remover LIMIT
    cur.execute("""
        SELECT d.archivo, COALESCE(m.nuc, d.nuc) as nuc,
               COALESCE(m.despacho, d.despacho) as despacho, d.estado, d.created_at
        FROM documentos d
        JOIN personas p ON p.documento_id = d.id
        LEFT JOIN metadatos m ON d.id = m.documento_id
        WHERE unaccent(LOWER(p.nombre)) LIKE unaccent(LOWER(%s))
        ORDER BY m.fecha_creacion DESC NULLS LAST
    """, (f'%{nombre}%',))
    fuentes_bd = [
        {
            "archivo": row[0],
            "nuc": row[1],
            "despacho": row[2],
            "estado": row[3],
            "fecha": row[4]
        } for row in cur.fetchall() if len(row) >= 5
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
# Detalle simulado de víctima - ELIMINADA FUNCIÓN DUPLICADA
# Esta función ahora usa la implementación completa
def obtener_detalle_victima(nombre):
    return obtener_detalle_victima_completo(nombre)
# Opciones simuladas para los filtros
# core/consultas.py
"""
Funciones de negocio para consultas, acceso a BD y procesamiento IA.
Todas las funciones aquí deben ser independientes del frontend.
"""

def ejecutar_consulta_geografica_directa(consulta, departamento=None, municipio=None, nuc=None, despacho=None, tipo_documento=None, fecha_inicio=None, fecha_fin=None, limit_victimas=None, limit_fuentes=100):
    """Función directa para consultas geográficas que bypasea el sistema de agentes"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Construir filtros dinámicamente para todos los tipos
        if departamento or municipio or nuc or despacho or tipo_documento or fecha_inicio or fecha_fin:
            # Construir WHERE clause dinámicamente
            where_conditions = ["p.tipo ILIKE %s", "p.tipo NOT ILIKE %s"]
            where_params = ['%victim%', '%victimario%']

            # Filtros geográficos con normalización
            if departamento:
                dept_variants = normalizar_departamento_busqueda(departamento)
                dept_conditions = []
                for variant in dept_variants:
                    dept_conditions.append("al.departamento ILIKE %s")
                    where_params.append(f'%{variant}%')
                where_conditions.append(f"({' OR '.join(dept_conditions)})")

            if municipio:
                mun_variants = normalizar_municipio_busqueda(municipio)
                mun_conditions = []
                for variant in mun_variants:
                    mun_conditions.append("al.municipio ILIKE %s")
                    where_params.append(f'%{variant}%')
                where_conditions.append(f"({' OR '.join(mun_conditions)})")

            # Filtros de metadatos
            if nuc:
                where_conditions.append("COALESCE(m.nuc, d.nuc) ILIKE %s")
                where_params.append(f'%{nuc}%')

            if despacho:
                where_conditions.append("COALESCE(m.despacho, d.despacho) ILIKE %s")
                where_params.append(f'%{despacho}%')

            if tipo_documento:
                where_conditions.append("m.detalle ILIKE %s")
                where_params.append(f'%{tipo_documento}%')

            # Filtros temporales
            if fecha_inicio:
                where_conditions.append("m.fecha_creacion >= %s")
                where_params.append(fecha_inicio)

            if fecha_fin:
                where_conditions.append("m.fecha_creacion <= %s")
                where_params.append(fecha_fin)

            where_clause = " AND ".join(where_conditions)

            # Query de víctimas - sin límite si es None
            if limit_victimas:
                query_victimas = f"""
                    SELECT p.nombre, COUNT(*) as menciones
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    LEFT JOIN analisis_lugares al ON d.id = al.documento_id
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    WHERE {where_clause}
                    GROUP BY p.nombre
                    ORDER BY menciones DESC
                    LIMIT %s
                """
                params = where_params + [limit_victimas]
            else:
                query_victimas = f"""
                    SELECT p.nombre, COUNT(*) as menciones
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    LEFT JOIN analisis_lugares al ON d.id = al.documento_id
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    WHERE {where_clause}
                    GROUP BY p.nombre
                    ORDER BY menciones DESC
                """
                params = where_params

            cur.execute(query_victimas, params)
            rows = cur.fetchall()
            victimas = [{'nombre': row[0], 'menciones': row[1]} for row in rows if len(row) >= 2]
            print(f"🔍 ejecutar_consulta_geografica_directa: Query retornó {len(victimas)} víctimas para departamento='{departamento}')")

            # Query de fuentes con todos los filtros
            fuentes_where_conditions = []
            fuentes_params = []

            # Filtros geográficos con normalización
            if departamento:
                dept_variants = normalizar_departamento_busqueda(departamento)
                dept_conditions = []
                for variant in dept_variants:
                    dept_conditions.append("al.departamento ILIKE %s")
                    fuentes_params.append(f'%{variant}%')
                fuentes_where_conditions.append(f"({' OR '.join(dept_conditions)})")

            if municipio:
                mun_variants = normalizar_municipio_busqueda(municipio)
                mun_conditions = []
                for variant in mun_variants:
                    mun_conditions.append("al.municipio ILIKE %s")
                    fuentes_params.append(f'%{variant}%')
                fuentes_where_conditions.append(f"({' OR '.join(mun_conditions)})")

            # Filtros de metadatos
            if nuc:
                fuentes_where_conditions.append("COALESCE(m.nuc, d.nuc) ILIKE %s")
                fuentes_params.append(f'%{nuc}%')

            if despacho:
                fuentes_where_conditions.append("COALESCE(m.despacho, d.despacho) ILIKE %s")
                fuentes_params.append(f'%{despacho}%')

            if tipo_documento:
                fuentes_where_conditions.append("m.detalle ILIKE %s")
                fuentes_params.append(f'%{tipo_documento}%')

            fuentes_where_clause = " AND ".join(fuentes_where_conditions) if fuentes_where_conditions else "1=1"

            query_fuentes = f"""
                SELECT DISTINCT d.archivo, COALESCE(m.nuc, d.nuc) as nuc,
                       COALESCE(m.despacho, d.despacho) as despacho,
                       d.estado, d.created_at
                FROM documentos d
                LEFT JOIN metadatos m ON d.id = m.documento_id
                LEFT JOIN analisis_lugares al ON d.id = al.documento_id
                WHERE {fuentes_where_clause}
                ORDER BY d.created_at DESC
                LIMIT %s
            """

            cur.execute(query_fuentes, fuentes_params + [limit_fuentes])
            rows = cur.fetchall()
            fuentes = [
                {
                    "archivo": row[0],
                    "nuc": row[1],
                    "despacho": row[2],
                    "estado": row[3],
                    "fecha": row[4]
                } for row in rows if len(row) >= 5
            ]

        else:
            victimas = []
            fuentes = []

        conn.close()

        respuesta = f"Consulta con filtros procesada: {len(victimas)} víctimas encontradas"
        filtros_aplicados = []

        if departamento and municipio:
            filtros_aplicados.append(f"{municipio}, {departamento}")
        elif departamento:
            filtros_aplicados.append(departamento)
        elif municipio:
            filtros_aplicados.append(municipio)

        if nuc:
            filtros_aplicados.append(f"NUC: {nuc}")
        if despacho:
            filtros_aplicados.append(f"Despacho: {despacho}")
        if tipo_documento:
            filtros_aplicados.append(f"Tipo: {tipo_documento}")

        if filtros_aplicados:
            respuesta += f" - Filtros: {', '.join(filtros_aplicados)}"

        return {
            'respuesta_ia': respuesta,
            'victimas': victimas,
            'fuentes': fuentes,
            'tipo_ejecutado': 'BD Filtros Directos'
        }

    except Exception as e:
        return {
            'respuesta_ia': f'Error en consulta geográfica: {str(e)}',
            'victimas': [],
            'fuentes': [],
            'tipo_ejecutado': 'Error'
        }

def ejecutar_consulta(consulta, nucs=None, departamento=None, municipio=None, tipo_documento=None, despacho=None, fecha_inicio=None, fecha_fin=None):
    # --- Integración del selector inteligente y análisis de oraciones ---
    from src.core.agente_oraciones_simple import crear_agente_oraciones_simple
    agente = crear_agente_oraciones_simple()
    plan = agente.analizar_consulta_completa(consulta, filtros_externos={
        "nucs": nucs,
        "departamento": departamento,
        "municipio": municipio,
        "tipo_documento": tipo_documento,
        "despacho": despacho,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    })

    # ✅ DETECTAR CONSULTAS SOBRE PERSONAS ESPECÍFICAS
    # Si el agente detectó un nombre de persona, usar ejecutar_consulta_persona
    for oracion in plan.oraciones_analizadas:
        if 'nombre_persona' in oracion.entidades_detectadas:
            nombre_persona = oracion.entidades_detectadas['nombre_persona']
            print(f"🔍 Detectado consulta sobre persona: {nombre_persona}")
            print(f"🔀 Redirigiendo a ejecutar_consulta_persona...")
            return ejecutar_consulta_persona(
                nombre_persona=nombre_persona,
                departamento=departamento,
                municipio=municipio,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )

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
    cur = conn.cursor()  # Use regular cursor to avoid parameter issues
    for oracion in plan.oraciones_analizadas:
        try:
            # Aplicar filtro universal modularmente
            filtros_universales = aplicar_filtro_universal(oracion.entidades_detectadas, {
                "nucs": nucs,
                "departamento": departamento,
                "municipio": municipio,
                "tipo_documento": tipo_documento,
                "despacho": despacho,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
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
                    filtros.append("al.departamento = %s")
                    params.append(departamento_)
                if municipio_:
                    filtros.append("al.municipio = %s")
                    params.append(municipio_)
                if tipo_documento_:
                    filtros.append("m.detalle = %s")
                    params.append(tipo_documento_)
                if despacho_:
                    filtros.append("m.despacho = %s")
                    params.append(despacho_)
                fecha_inicio_ = filtros_universales.get("fecha_inicio")
                fecha_fin_ = filtros_universales.get("fecha_fin")
                if fecha_inicio_:
                    filtros.append("m.fecha_creacion >= %s")
                    params.append(fecha_inicio_)
                if fecha_fin_:
                    filtros.append("m.fecha_creacion <= %s")
                    params.append(fecha_fin_)
                where = " AND ".join(filtros) if filtros else "1=1"


                # Consulta de víctimas con filtro correcto y JOIN a metadatos y analisis_lugares
                where_victimas = f"(p.tipo ILIKE '%victim%' AND p.tipo NOT ILIKE '%victimario%')"
                if where != "1=1":
                    where_victimas += f" AND {where}"
                cur.execute(f"""
                    SELECT p.nombre, COUNT(*) as menciones
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    LEFT JOIN analisis_lugares al ON d.id = al.documento_id
                    WHERE {where_victimas}
                    GROUP BY p.nombre
                    ORDER BY menciones DESC
                """, tuple(params))
                rows = cur.fetchall()
                print(f"🔍 ejecutar_consulta BD: Query retornó {len(rows)} víctimas")
                victimas += [{'nombre': row[0], 'menciones': row[1]} for row in rows if len(row) >= 2]
                # Consulta de fuentes con JOIN a metadatos y analisis_lugares
                cur.execute(f"""
                    SELECT d.archivo, COALESCE(m.nuc, d.nuc) as nuc,
                           COALESCE(m.despacho, d.despacho) as despacho,
                           d.estado, d.created_at
                    FROM documentos d
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    LEFT JOIN analisis_lugares al ON d.id = al.documento_id
                    WHERE {where}
                    ORDER BY m.fecha_creacion DESC NULLS LAST
                    LIMIT 10
                """, tuple(params))
                rows_fuentes = cur.fetchall()
                fuentes += [
                    {
                        "archivo": row[0],
                        "nuc": row[1],
                        "despacho": row[2],
                        "estado": row[3],
                        "fecha": row[4]
                    } for row in rows_fuentes if len(row) >= 5
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

# === FUNCIONES RAG Y CONSULTAS INTELIGENTES ===

def ejecutar_consulta_rag_inteligente(consulta, contexto_conversacional=None):
    """Motor RAG inteligente con Azure Search y trazabilidad completa"""
    try:
        # Usar función síncrona más simple
        from src.core.sistema_rag_completo import consulta_hibrida_sincrona

        # Enriquecer consulta con contexto si está disponible
        consulta_enriquecida = consulta
        if contexto_conversacional:
            consulta_enriquecida = f"""{contexto_conversacional}

CONSULTA ACTUAL: {consulta}"""
            print(f"🔍 RAG: Consulta enriquecida con contexto conversacional ({len(contexto_conversacional)} caracteres)")

        # Ejecutar consulta
        resultado = consulta_hibrida_sincrona(consulta_enriquecida)

        if resultado and 'respuesta' in resultado:
            # Estructurar respuesta
            respuesta_estructurada = {
                'respuesta': resultado.get('respuesta', 'Sin respuesta'),
                'fuentes': resultado.get('fuentes', []),
                'chunks': resultado.get('chunks', []),
                'confianza': resultado.get('confianza', 0.0),
                'consulta_id': resultado.get('consulta_id', 0)
            }

            return respuesta_estructurada
        else:
            return {'respuesta': 'No se pudo procesar la consulta RAG', 'fuentes': [], 'chunks': [], 'confianza': 0.0}

    except Exception as e:
        return {'respuesta': f'Error en consulta RAG: {str(e)}', 'fuentes': [], 'chunks': [], 'confianza': 0.0}

def ejecutar_consulta_hibrida(
    consulta: str,
    nucs: Optional[List[str]] = None,
    departamento: Optional[str] = None,
    municipio: Optional[str] = None,
    tipo_documento: Optional[str] = None,
    despacho: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    contexto_conversacional: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta consulta híbrida combinando BD + RAG con división automática.

    Args:
        consulta: Texto de la consulta del usuario
        nucs: Lista opcional de NUCs para filtrar
        departamento: Departamento opcional para filtrar
        municipio: Municipio opcional para filtrar
        tipo_documento: Tipo de documento opcional para filtrar
        despacho: Despacho opcional para filtrar
        fecha_inicio: Fecha de inicio opcional para filtrar (YYYY-MM-DD)
        fecha_fin: Fecha de fin opcional para filtrar (YYYY-MM-DD)
        contexto_conversacional: Contexto de conversaciones previas para enriquecer la consulta RAG

    Returns:
        Dict[str, Any]: Diccionario con 'bd' y 'rag' conteniendo los resultados combinados
    """
    try:
        # 1. Dividir consulta automáticamente
        consulta_bd, consulta_rag = dividir_consulta_hibrida(consulta)

        # 2. Extraer entidades geográficas del texto si no se especifican en UI
        if not departamento:
            consulta_lower = consulta_bd.lower()
            # Lista de departamentos comunes en el dataset
            departamentos_conocidos = ['antioquia', 'bogotá', 'valle del cauca', 'cundinamarca', 'atlántico',
                                     'santander', 'bolívar', 'nariño', 'tolima', 'huila', 'caldas', 'cauca',
                                     'córdoba', 'sucre', 'magdalena', 'cesar', 'arauca', 'amazonas']

            for dept in departamentos_conocidos:
                if dept in consulta_lower:
                    departamento = dept.title()  # Capitalizar primera letra
                    print(f"🔍 HIBRIDA: Detectado departamento '{departamento}' en consulta_bd: '{consulta_bd}'")
                    break

            if not departamento:
                print(f"⚠️ HIBRIDA: NO se detectó departamento en consulta_bd: '{consulta_bd}'")

        # ✅ NUEVO: Detectar municipio en el texto si no se especifica en UI
        if not municipio:
            consulta_lower = consulta_bd.lower()
            try:
                # Cargar municipios desde BD
                import psycopg2
                conn = psycopg2.connect(
                    host="localhost",
                    database="documentos_juridicos_gpt4",
                    user="docs_user",
                    password="docs_password_2025"
                )
                cur = conn.cursor()
                cur.execute("""
                    SELECT DISTINCT municipio
                    FROM analisis_lugares
                    WHERE municipio IS NOT NULL
                      AND municipio <> ''
                      AND LENGTH(municipio) > 2
                    ORDER BY LENGTH(municipio) DESC;
                """)

                # Buscar en orden de longitud (más largos primero)
                for row in cur.fetchall():
                    mun = row[0].strip()
                    if mun.lower() in consulta_lower:
                        municipio = mun
                        print(f"🔍 HIBRIDA: Detectado municipio '{municipio}' en consulta_bd: '{consulta_bd}'")
                        break

                cur.close()
                conn.close()
            except Exception as e:
                print(f"⚠️ Error al detectar municipio: {e}")

        # 3. Ejecutar parte BD (cuantitativa) - MEJORADO PARA PERSONAS
        try:
            # Detectar si es consulta de persona específica
            import re
            nombres_propios = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', consulta_bd)

            if 'menciones de' in consulta_bd.lower():
                # Es una consulta de persona específica - MEJORAR EXTRACCIÓN
                texto_personas = consulta_bd.split('menciones de')[-1].strip()
                print(f"🔍 DETECTADO consulta de persona: '{texto_personas}'")  # Debug

                # NUEVO: Extraer nombres propios reales de la consulta (case insensitive)
                import re
                # Patrón que acepta tanto mayúsculas como minúsculas para nombres
                nombres_reales = re.findall(r'\b[a-zA-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[a-zA-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[a-zA-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', texto_personas)

                if nombres_reales:
                    # Si hay nombres propios identificables, usar el primero (consulta principal)
                    nombre_principal = nombres_reales[0]
                    print(f"🔍 USANDO nombre principal: '{nombre_principal}'")
                    resultados_bd = ejecutar_consulta_persona(
                        nombre_principal,
                        departamento=departamento,
                        municipio=municipio,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin
                    )
                else:
                    # Fallback: usar el texto completo si no se pueden extraer nombres
                    resultados_bd = ejecutar_consulta_persona(
                        texto_personas,
                        departamento=departamento,
                        municipio=municipio,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin
                    )
            elif departamento or municipio or nucs or tipo_documento or despacho or fecha_inicio or fecha_fin:
                # Usar función directa si hay cualquier tipo de filtro
                print(f"🔍 HIBRIDA: Ejecutando ejecutar_consulta_geografica_directa con departamento='{departamento}'")
                resultados_bd = ejecutar_consulta_geografica_directa(
                    consulta_bd,
                    departamento=departamento,
                    municipio=municipio,
                    nuc=nucs[0] if nucs and len(nucs) > 0 else None,
                    despacho=despacho,
                    tipo_documento=tipo_documento,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                    # Sin limit_victimas - devuelve todas las víctimas encontradas
                )
            else:
                print(f"⚠️ HIBRIDA: Ejecutando ejecutar_consulta SIN filtros (departamento='{departamento}')")
                resultados_bd = ejecutar_consulta(
                    consulta_bd,
                    nucs=nucs,
                    departamento=departamento,
                    municipio=municipio,
                    tipo_documento=tipo_documento,
                    despacho=despacho,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )
        except Exception as e:
            resultados_bd = {'respuesta_ia': f'ERROR {consulta_bd}: {str(e)}', 'victimas': [], 'fuentes': []}

        # 4. Ejecutar parte RAG (cualitativa) con contexto conversacional si está disponible
        resultados_rag = ejecutar_consulta_rag_inteligente(consulta_rag, contexto_conversacional=contexto_conversacional)

        # 5. Combinar resultados con información de división
        respuesta_combinada = {
            'bd': {
                'consulta_original': consulta_bd,
                'respuesta_ia': resultados_bd.get('respuesta_ia', ''),
                'victimas': resultados_bd.get('victimas', []),
                'fuentes': resultados_bd.get('fuentes', []),
                # AGREGAR CAMPOS FALTANTES PARA COMPATIBILIDAD CON DASH
                'total_menciones': resultados_bd.get('total_menciones', 0),
                'documentos': resultados_bd.get('documentos', [])
            },
            'rag': {
                'consulta_original': consulta_rag,
                'respuesta': resultados_rag.get('respuesta', ''),
                'fuentes': resultados_rag.get('fuentes', []),
                'chunks': resultados_rag.get('chunks', []),
                'confianza': resultados_rag.get('confianza', 0.0)
            },
            'tipo_consulta': 'hibrida',
            'division_aplicada': consulta_bd != consulta_rag
        }

        return respuesta_combinada

    except Exception as e:
        return {'error': f'Error en consulta híbrida: {str(e)}', 'tipo_consulta': 'error'}

def clasificar_consulta(consulta: str) -> str:
    """
    Clasifica si la consulta necesita BD, RAG o ambas con lógica inteligente mejorada.

    Args:
        consulta: Texto de la consulta del usuario

    Returns:
        str: 'bd', 'rag', o 'hibrida'
    """
    import re
    consulta_lower = consulta.lower()

    # Palabras que indican consultas cuantitativas (BD)
    palabras_bd = ['cuántos', 'cuantos', 'cantidad', 'número', 'numero', 'total', 'lista', 'listado']

    # Palabras que indican consultas cualitativas (RAG)
    palabras_rag = ['por qué', 'porque', 'qué significa', 'analizar', 'explicar', 'contexto', 'patrones', 'observar', 'observes']

    # Detectar consultas sobre personas específicas (NUEVA FUNCIONALIDAD MEJORADA)
    patrones_personas = [
        r'quién es \w+',           # "¿quién es Oswaldo?"
        r'quien es \w+',           # "quien es Oswaldo"
        r'qué sabes de \w+',       # "qué sabes de Oswaldo"
        r'que sabes de \w+',       # "que sabes de Oswaldo"
        r'cuéntame de \w+',        # "cuéntame de Oswaldo"
        r'cuentame de \w+',        # "cuentame de Oswaldo"
        r'información de \w+',     # "información de Oswaldo"
        r'informacion de \w+',     # "informacion de Oswaldo"
        r'sobre \w+ \w+',          # "sobre Oswaldo Olivo"
    ]

    # Entidades geográficas y conceptuales que NO son personas (importadas de config.constants)
    entidades_no_personas = ENTIDADES_NO_PERSONAS

    # Detectar nombres propios (palabras con mayúscula inicial)
    nombres_propios = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', consulta)

    # Verificar si es consulta sobre persona específica
    es_consulta_persona = any(re.search(patron, consulta_lower) for patron in patrones_personas)

    # NUEVA LÓGICA: Filtrar nombres propios que NO son personas
    nombres_posibles_personas = []
    for nombre in nombres_propios:
        if nombre.lower() not in entidades_no_personas:
            nombres_posibles_personas.append(nombre)

    tiene_nombres_personas = len(nombres_posibles_personas) >= 1

    # Detectar consultas híbridas (contienen palabras de ambos tipos + conectores)
    tiene_bd = any(palabra in consulta_lower for palabra in palabras_bd)
    tiene_rag = any(palabra in consulta_lower for palabra in palabras_rag)
    conectores = [' y ', ' and ', ' además ', ' también ', ' junto ', ' más ', ' sumado ']
    tiene_conector = any(conector in consulta_lower for conector in conectores)

    # Patrones específicos para híbridas VÁLIDAS (datos + análisis genuinos)
    patrones_hibrida = [
        'víctimas con contexto', 'victimas con contexto', 'masacres y contexto',
        'datos.*y.*analiz', 'estadísticas.*y.*context', 'estadisticas.*y.*context',
        'números.*y.*explicar', 'numeros.*y.*explicar', 'cantidad.*y.*anális',
        'cuántos.*y.*por qué', 'cuantos.*y.*por que'
    ]

    # Patrones que parecen híbridas pero son RAG (consultas analíticas complejas)
    patrones_rag_complejos = [
        'lista.*y.*patron', 'lista.*y.*observ', 'listado.*pattern', 'listado.*observ',
        'lista.*criminal', 'patrones.*observ', 'patron.*observ'
    ]

    # CLASIFICACIÓN INTELIGENTE MEJORADA
    if es_consulta_persona or tiene_nombres_personas:
        # Solo híbrida si realmente es sobre personas específicas
        return 'hibrida'
    elif any(patron in consulta_lower for patron in patrones_rag_complejos):
        # Consultas que parecen híbridas pero son análisis complejos → RAG
        return 'rag'
    elif any(patron in consulta_lower for patron in patrones_hibrida):
        # Híbridas genuinas: datos cuantitativos + análisis cualitativo
        return 'hibrida'
    elif tiene_bd and tiene_rag and tiene_conector:
        # Solo híbrida si hay conectores genuinos de combinación
        return 'hibrida'
    elif tiene_rag:
        return 'rag'
    elif tiene_bd:
        return 'bd'
    else:
        return 'rag'  # Por defecto usar RAG para consultas complejas

def dividir_consulta_hibrida(consulta: str) -> Tuple[str, str]:
    """
    Divide una consulta híbrida en parte BD y parte RAG.

    Args:
        consulta: Texto de la consulta híbrida del usuario

    Returns:
        Tuple[str, str]: (consulta_bd, consulta_rag)
    """
    import re
    consulta_lower = consulta.lower()

    # NUEVO: Detectar consultas sobre personas específicas
    patrones_personas = [
        r'quién es (\w+(?:\s+\w+)*)',      # "¿quién es Oswaldo Olivo?"
        r'quien es (\w+(?:\s+\w+)*)',      # "quien es Oswaldo Olivo"
        r'qué sabes de (\w+(?:\s+\w+)*)',  # "qué sabes de Oswaldo Olivo"
        r'que sabes de (\w+(?:\s+\w+)*)',  # "que sabes de Oswaldo Olivo"
    ]

    for patron in patrones_personas:
        match = re.search(patron, consulta_lower, re.IGNORECASE)
        if match:
            nombre_persona = match.group(1)
            # Crear consultas específicas para BD y RAG
            parte_bd = f"menciones de {nombre_persona}"
            parte_rag = f"¿quién es {nombre_persona} y cuál es su relevancia en el contexto judicial?"
            return parte_bd, parte_rag

    # Detectar nombres propios para otras consultas híbridas con nombres
    nombres_propios = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b', consulta)
    if nombres_propios:
        # FILTRAR entidades geográficas y conceptuales que NO son personas (importadas de config.constants)
        entidades_no_personas = ENTIDADES_NO_PERSONAS

        # NUEVA LÓGICA: Filtrar nombres propios que NO son entidades geográficas/conceptuales
        nombres_posibles_personas = []
        for nombre in nombres_propios:
            if nombre.lower() not in entidades_no_personas:
                nombres_posibles_personas.append(nombre)

        # Solo crear búsqueda de personas si hay nombres que NO sean entidades conocidas
        if nombres_posibles_personas:
            nombre_completo = ' '.join(nombres_posibles_personas)
            parte_bd = f"menciones de {nombre_completo}"
            parte_rag = consulta  # Usar la consulta original para RAG
            return parte_bd, parte_rag

    # Patrones para identificar y dividir consultas híbridas
    if 'lista' in consulta_lower and ('patron' in consulta_lower or 'observ' in consulta_lower):
        # Ejemplo: "dame la lista de victimas en Antioquia y los patrones criminales que observes"
        partes = consulta.split(' y ')
        if len(partes) >= 2:
            parte_bd = partes[0].strip()  # "dame la lista de victimas en Antioquia"
            parte_rag = ' '.join(partes[1:]).strip()  # "los patrones criminales que observes"

            # Asegurar que la parte BD sea una consulta válida
            if not any(palabra in parte_bd.lower() for palabra in ['dame', 'lista', 'muestra', 'busca']):
                parte_bd = f"Dame {parte_bd}"

            # Asegurar que la parte RAG sea una pregunta válida
            if not any(palabra in parte_rag.lower() for palabra in ['qué', 'que', 'cuál', 'cual', 'cómo', 'como', 'por qué', 'analiz']):
                parte_rag = f"¿Qué {parte_rag}?"

            return parte_bd, parte_rag

    # Otros patrones de división
    if ' y ' in consulta_lower:
        partes = consulta.split(' y ')
        if len(partes) >= 2:
            # Evaluar cada parte para determinar BD vs RAG
            parte1 = partes[0].strip()
            parte2 = ' '.join(partes[1:]).strip()

            palabras_bd = ['lista', 'listado', 'cuántos', 'total', 'número', 'cantidad']
            palabras_rag = ['patrones', 'contexto', 'análisis', 'por qué', 'explicar']

            es_bd_1 = any(palabra in parte1.lower() for palabra in palabras_bd)
            es_rag_2 = any(palabra in parte2.lower() for palabra in palabras_rag)

            if es_bd_1 and es_rag_2:
                return parte1, parte2
            elif es_rag_2 and not es_bd_1:
                return parte2, parte1  # Intercambiar orden

    # Si no se puede dividir, devolver consulta original para ambas
    return consulta, consulta

# === FUNCIONES PARA CONSULTAS DE PERSONAS ESPECÍFICAS ===

def normalizar_nombre_busqueda(nombre):
    """
    Normaliza nombre para búsqueda ignorando tildes y caracteres especiales.
    'Ana Matilde Guzman' -> 'ana matilde guzman' (lowercase, sin tildes)
    """
    import unicodedata
    # Convertir a minúsculas
    nombre = nombre.lower()
    # Remover tildes: 'á' -> 'a', 'é' -> 'e', etc.
    nombre = ''.join(
        c for c in unicodedata.normalize('NFD', nombre)
        if unicodedata.category(c) != 'Mn'
    )
    return nombre

def ejecutar_consulta_persona(nombre_persona, limit=10, departamento=None, municipio=None, fecha_inicio=None, fecha_fin=None):
    """Ejecuta consulta específica para obtener información de una persona"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Configurar si necesitamos JOINs geográficos/temporales
        necesita_joins = departamento or municipio or fecha_inicio or fecha_fin

        if necesita_joins:
            # Con filtros: usar JOINs y COUNT(DISTINCT) y solo nombre completo
            # ✅ USAR unaccent para ignorar tildes: "guzman" matchea con "guzmán"
            where_conditions = ["unaccent(LOWER(p.nombre)) LIKE unaccent(LOWER(%s))", "p.tipo ILIKE %s"]
            params = [f'%{nombre_persona}%', '%victim%']

            # Filtros geográficos
            if departamento:
                dept_variants = normalizar_departamento_busqueda(departamento)
                dept_conditions = []
                for variant in dept_variants:
                    dept_conditions.append("al.departamento ILIKE %s")
                    params.append(f'%{variant}%')
                where_conditions.append(f"({' OR '.join(dept_conditions)})")

            if municipio:
                mun_variants = normalizar_municipio_busqueda(municipio)
                mun_conditions = []
                for variant in mun_variants:
                    mun_conditions.append("al.municipio ILIKE %s")
                    params.append(f'%{variant}%')
                where_conditions.append(f"({' OR '.join(mun_conditions)})")

            # Filtros temporales
            if fecha_inicio:
                where_conditions.append("m.fecha_creacion >= %s")
                params.append(fecha_inicio)

            if fecha_fin:
                where_conditions.append("m.fecha_creacion <= %s")
                params.append(fecha_fin)

            where_clause = " AND ".join(where_conditions)

            # Contar menciones sin duplicar por lugares (usar subquery para filtro geográfico)
            if departamento or municipio:
                # Si hay filtro geográfico, usar EXISTS para evitar duplicados
                geo_subquery = ""
                if departamento and municipio:
                    geo_subquery = "AND EXISTS (SELECT 1 FROM analisis_lugares al2 WHERE al2.documento_id = d.id AND al2.departamento ILIKE %s AND al2.municipio ILIKE %s)"
                elif departamento:
                    geo_subquery = f"AND EXISTS (SELECT 1 FROM analisis_lugares al2 WHERE al2.documento_id = d.id AND ({' OR '.join(['al2.departamento ILIKE %s' for _ in normalizar_departamento_busqueda(departamento)])}))"
                elif municipio:
                    geo_subquery = f"AND EXISTS (SELECT 1 FROM analisis_lugares al2 WHERE al2.documento_id = d.id AND ({' OR '.join(['al2.municipio ILIKE %s' for _ in normalizar_municipio_busqueda(municipio)])}))"

                # Crear query de conteo sin JOIN a analisis_lugares
                where_simple = ["unaccent(LOWER(p.nombre)) LIKE unaccent(LOWER(%s))", "p.tipo ILIKE %s"]
                params_simple = [f'%{nombre_persona}%', '%victim%']

                if fecha_inicio:
                    where_simple.append("m.fecha_creacion >= %s")
                    params_simple.append(fecha_inicio)
                if fecha_fin:
                    where_simple.append("m.fecha_creacion <= %s")
                    params_simple.append(fecha_fin)

                # Agregar parámetros de geografía después
                if departamento:
                    for variant in normalizar_departamento_busqueda(departamento):
                        params_simple.append(f'%{variant}%')
                if municipio:
                    for variant in normalizar_municipio_busqueda(municipio):
                        params_simple.append(f'%{variant}%')

                where_clause_simple = " AND ".join(where_simple) + " " + geo_subquery

                cur.execute(f"""
                    SELECT COUNT(*) FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    WHERE {where_clause_simple}
                """, params_simple)
            else:
                # Sin filtro geográfico, contar normalmente
                cur.execute(f"""
                    SELECT COUNT(*) FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    LEFT JOIN metadatos m ON d.id = m.documento_id
                    WHERE unaccent(LOWER(p.nombre)) LIKE unaccent(LOWER(%s)) AND p.tipo ILIKE %s
                        {f"AND m.fecha_creacion >= '{fecha_inicio}'" if fecha_inicio else ""}
                        {f"AND m.fecha_creacion <= '{fecha_fin}'" if fecha_fin else ""}
                """, [f'%{nombre_persona}%', '%victim%'])

            result = cur.fetchone()
            total_menciones = result[0] if result else 0

            # Obtener documentos relacionados con filtros
            params_docs = params + [limit]
            cur.execute(f"""
                SELECT DISTINCT
                    d.archivo,
                    m.nuc,
                    m.fecha_creacion as fecha,
                    m.despacho,
                    m.detalle as tipo_documental,
                    p.nombre,
                    p.tipo,
                    COALESCE(d.analisis, '') as analisis_ia
                FROM personas p
                JOIN documentos d ON p.documento_id = d.id
                LEFT JOIN metadatos m ON d.id = m.documento_id
                LEFT JOIN analisis_lugares al ON d.id = al.documento_id
                WHERE {where_clause}
                ORDER BY m.fecha_creacion DESC NULLS LAST
                LIMIT %s
            """, params_docs)

            documentos_relacionados = []
            for row in cur.fetchall():
                if len(row) >= 8:
                    doc = {
                        "archivo": row[0],
                        "nuc": row[1],
                        "fecha": row[2],
                        "despacho": row[3],
                        "tipo_documental": row[4],
                        "nombre_encontrado": row[5],
                        "tipo_persona": row[6],
                        "analisis_ia": row[7]
                    }
                    documentos_relacionados.append(doc)

        else:
            # Sin filtros: buscar SOLO por nombre completo (sin variantes para evitar duplicados)
            # ✅ CORRECCIÓN: Eliminar lógica de variantes que causaba conteo duplicado
            cur.execute("""
                SELECT COUNT(*) FROM personas
                WHERE unaccent(LOWER(nombre)) LIKE unaccent(LOWER(%s)) AND tipo ILIKE %s
            """, (f'%{nombre_persona}%', '%victim%'))
            result = cur.fetchone()
            total_menciones = result[0] if result else 0

            # ✅ CORRECCIÓN: Remover LIMIT para obtener TODOS los documentos relacionados
            cur.execute("""
                SELECT DISTINCT
                    d.archivo,
                    m.nuc,
                    m.fecha_creacion as fecha,
                    m.despacho,
                    m.detalle as tipo_documental,
                    p.nombre,
                    p.tipo,
                    COALESCE(d.analisis, '') as analisis_ia
                FROM personas p
                JOIN documentos d ON p.documento_id = d.id
                LEFT JOIN metadatos m ON d.id = m.documento_id
                WHERE unaccent(LOWER(p.nombre)) LIKE unaccent(LOWER(%s)) AND p.tipo ILIKE %s
                ORDER BY m.fecha_creacion DESC NULLS LAST
            """, (f'%{nombre_persona}%', '%victim%'))

            documentos_relacionados = []
            for row in cur.fetchall():
                if len(row) >= 8:
                    doc = {
                        "archivo": row[0],
                        "nuc": row[1],
                        "fecha": row[2],
                        "despacho": row[3],
                        "tipo_documental": row[4],
                        "nombre_encontrado": row[5],
                        "tipo_persona": row[6],
                        "analisis_ia": row[7]
                    }
                    documentos_relacionados.append(doc)

        # Crear respuesta estructurada
        respuesta_bd = f"""**📊 Información de Base de Datos para {nombre_persona}:**

**Total menciones encontradas:** {total_menciones}
**Documentos relacionados:** {len(documentos_relacionados)}

**📁 Documentos más relevantes:**"""

        for i, doc in enumerate(documentos_relacionados[:5], 1):
            respuesta_bd += f"""
{i}. **{doc['nombre_encontrado']}**
   - Archivo: {doc['archivo']}
   - NUC: {doc['nuc'] or 'No disponible'}
   - Fecha: {doc['fecha'] or 'No disponible'}
   - Despacho: {doc['despacho'] or 'No disponible'}
   - Tipo: {doc['tipo_persona']}"""

        cur.close()
        conn.close()

        return {
            'respuesta': respuesta_bd,
            'respuesta_ia': respuesta_bd,  # Compatibilidad con interfaz Dash
            'total_menciones': total_menciones,
            'documentos': documentos_relacionados,
            'victimas': [{'nombre': nombre_persona, 'menciones': total_menciones}],
            'fuentes': documentos_relacionados[:5],
            'tipo_ejecutado': 'Consulta Persona Específica'
        }

    except Exception as e:
        return {
            'error': f'Error consultando persona {nombre_persona}: {str(e)}',
            'respuesta': f'No se pudo obtener información de {nombre_persona}',
            'respuesta_ia': f'No se pudo obtener información de {nombre_persona}',
            'victimas': [],
            'fuentes': [],
            'tipo_ejecutado': 'Error'
        }

# === FUNCIONES DE NORMALIZACIÓN ===

def normalizar_departamento_busqueda(departamento_norm: str) -> str:
    """Convierte departamento normalizado a patrones de búsqueda"""
    if departamento_norm == 'Antioquia':
        return ['Antioquia', 'Antioquía']
    elif departamento_norm == 'Bogotá D.C.':
        return ['Bogotá D.C.', 'Bogotá', 'Bogotá, D.C.', 'D.C.', 'Distrito Capital']
    elif departamento_norm == 'Cesar':
        return ['Cesar', 'César']
    elif departamento_norm == 'Valle del Cauca':
        return ['Valle del Cauca', 'Valle']
    elif departamento_norm == 'La Guajira':
        return ['La Guajira', 'Guajira']
    else:
        return [departamento_norm]

def normalizar_municipio_busqueda(municipio_norm: str) -> str:
    """Convierte municipio normalizado a patrones de búsqueda"""
    if municipio_norm == 'Bogotá':
        return ['Bogotá', 'Santa Fe de Bogotá', 'Santafé de Bogotá', 'Santa Fé de Bogotá',
                'Bogotá D.C.', 'Bogotá, D.C.', 'Santa Fe de Bogotá D.C.', 'Santafé de Bogotá D.C.']
    elif municipio_norm == 'Cali':
        return ['Cali', 'Santiago de Cali']
    elif municipio_norm == 'Medellín':
        return ['Medellín', 'Medellin']
    else:
        return [municipio_norm]

# === FUNCIONES DE OPCIONES PARA FILTROS ===

def obtener_opciones_nuc() -> List[str]:
    """Obtiene lista de NUCs disponibles con filtrado de calidad"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT COALESCE(m.nuc, d.nuc) as nuc, COUNT(*) as docs
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.nuc, d.nuc) IS NOT NULL
              AND LENGTH(COALESCE(m.nuc, d.nuc)) BETWEEN 21 AND 23
              AND COALESCE(m.nuc, d.nuc) ~ '^[0-9]+$'
            GROUP BY COALESCE(m.nuc, d.nuc)
            ORDER BY docs DESC, nuc
            LIMIT 50
        """)
        nucs = [row[0] for row in cur.fetchall() if len(row) > 0]
        cur.close()
        conn.close()
        return nucs
    except:
        return []

def obtener_opciones_departamento() -> List[str]:
    """Obtiene lista de departamentos disponibles con normalización mejorada"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT departamento_norm, SUM(docs) as total_docs
            FROM (
                SELECT
                    CASE
                        -- Normalizar Antioquia
                        WHEN departamento ILIKE '%Antioqu%' THEN 'Antioquia'

                        -- Normalizar Bogotá (todas las variantes)
                        WHEN departamento ILIKE '%Bogot%'
                          OR departamento ILIKE '%D.C%'
                          OR departamento = 'D.E.'
                          OR departamento = 'Distrito Capital'
                          OR departamento = 'Distrito de Columbia' THEN 'Bogotá D.C.'

                        -- Normalizar Cesar
                        WHEN departamento ILIKE '%Ces%r%' THEN 'Cesar'

                        -- Normalizar Valle del Cauca
                        WHEN departamento ILIKE '%Valle del Cauca%'
                          OR departamento = 'Valle' THEN 'Valle del Cauca'

                        -- Normalizar La Guajira
                        WHEN departamento = 'Guajira'
                          OR departamento = 'La Guajira' THEN 'La Guajira'

                        -- Normalizar Norte de Santander
                        WHEN departamento = 'Norte de Santander' THEN 'Norte de Santander'

                        -- EXCLUIR datos inválidos
                        -- Códigos y no disponibles
                        WHEN departamento IN ('00', '00 - TODOS', 'No disponible', 'No especificado', 'CES', 'TCO008', 'S') THEN NULL

                        -- Países/estados extranjeros
                        WHEN departamento IN ('A Coruña', 'Columbia', 'Maryland', 'Nueva York', 'Jalisco', 'La Libertad') THEN NULL

                        -- Regiones inventadas o composiciones
                        WHEN departamento ILIKE '%Orinoquía%' THEN NULL
                        WHEN departamento ILIKE '%Santander del Sur%' THEN NULL
                        WHEN departamento ILIKE '%Santander-Cauca%' THEN NULL
                        WHEN departamento ILIKE '%Valle de Aburrá%' THEN NULL

                        -- Múltiples departamentos (contienen comas o "y")
                        WHEN departamento LIKE '%,%' OR departamento LIKE '% y %' THEN NULL

                        -- Ciudades específicas (no son departamentos)
                        WHEN departamento IN ('San Gil', 'Cali', 'Bucaramanga', 'Medellín', 'Mampuján', 'Cartagena') THEN NULL

                        -- Mantener departamentos válidos
                        ELSE departamento
                    END as departamento_norm,
                    COUNT(*) as docs
                FROM analisis_lugares
                WHERE departamento IS NOT NULL AND departamento != ''
                GROUP BY departamento, departamento_norm
            ) subq
            WHERE departamento_norm IS NOT NULL
            GROUP BY departamento_norm
            HAVING SUM(docs) >= 2  -- Solo departamentos con al menos 2 documentos
            ORDER BY departamento_norm
        """)
        departamentos = [row[0] for row in cur.fetchall() if len(row) > 0]
        cur.close()
        conn.close()
        return departamentos
    except:
        return []

def obtener_opciones_municipio() -> List[str]:
    """Obtiene lista de municipios disponibles con normalización"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT municipio_norm, SUM(docs) as total_docs
            FROM (
                SELECT
                    CASE
                        WHEN municipio ILIKE '%santa%f%bogot%' OR municipio ILIKE '%bogot%' THEN 'Bogotá'
                        WHEN municipio ILIKE '%santiago%cali%' OR municipio ILIKE '%cali%' THEN 'Cali'
                        WHEN municipio ILIKE '%medellin%' OR municipio ILIKE '%medell%n%' THEN 'Medellín'
                        WHEN municipio ILIKE '%cartagena%' THEN 'Cartagena'
                        WHEN municipio ILIKE '%barranquilla%' THEN 'Barranquilla'
                        WHEN municipio IN ('000 - TODOS', '00 - TODOS') THEN NULL
                        ELSE municipio
                    END as municipio_norm,
                    COUNT(*) as docs
                FROM analisis_lugares
                WHERE municipio IS NOT NULL AND municipio != ''
                GROUP BY municipio, municipio_norm
            ) subq
            WHERE municipio_norm IS NOT NULL
            GROUP BY municipio_norm
            ORDER BY municipio_norm
            LIMIT 100
        """)
        municipios = [row[0] for row in cur.fetchall() if len(row) > 0]
        cur.close()
        conn.close()
        return municipios
    except:
        return []

def obtener_opciones_tipo_documento() -> List[str]:
    """Obtiene lista de tipos de documento disponibles"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT detalle FROM metadatos WHERE detalle IS NOT NULL ORDER BY detalle")
        tipos = [row[0] for row in cur.fetchall() if len(row) > 0]
        cur.close()
        conn.close()
        return tipos
    except:
        return []

def obtener_opciones_despacho() -> List[str]:
    """Obtiene lista de despachos disponibles"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT COALESCE(m.despacho, d.despacho) as despacho
            FROM documentos d
            LEFT JOIN metadatos m ON d.id = m.documento_id
            WHERE COALESCE(m.despacho, d.despacho) IS NOT NULL
              AND LENGTH(COALESCE(m.despacho, d.despacho)) < 15
              AND COALESCE(m.despacho, d.despacho) NOT LIKE '110016%'
            ORDER BY despacho
            LIMIT 20
        """)
        despachos = [row[0] for row in cur.fetchall() if len(row) > 0]
        cur.close()
        conn.close()
        return despachos
    except:
        return []

def obtener_rango_fechas() -> Tuple[Optional[str], Optional[str]]:
    """
    Obtiene el rango de fechas disponible en los documentos.

    Returns:
        Tuple[Optional[str], Optional[str]]: (fecha_minima, fecha_maxima) en formato 'YYYY-MM-DD'
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                MIN(fecha_creacion) as fecha_minima,
                MAX(fecha_creacion) as fecha_maxima
            FROM metadatos
            WHERE fecha_creacion IS NOT NULL
        """)
        resultado = cur.fetchone()
        cur.close()
        conn.close()

        if resultado and resultado[0] and resultado[1]:
            # Convertir a string formato YYYY-MM-DD
            fecha_min = resultado[0].strftime('%Y-%m-%d') if hasattr(resultado[0], 'strftime') else str(resultado[0])[:10]
            fecha_max = resultado[1].strftime('%Y-%m-%d') if hasattr(resultado[1], 'strftime') else str(resultado[1])[:10]
            return (fecha_min, fecha_max)
        return (None, None)
    except Exception as e:
        print(f"Error obteniendo rango de fechas: {e}")
        return (None, None)

# Función duplicada eliminada - usar la implementación de línea 161
