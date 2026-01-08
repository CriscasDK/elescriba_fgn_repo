#!/usr/bin/env python3
"""
🌐 FRONTEND VÍCTIMAS CON VALIDACIÓN - ANÁLISIS Y TEXTO DESPLEGABLES
Enfocado en la validación de víctimas a través de análisis y texto
"""

import streamlit as st
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.gpt41')

st.set_page_config(
    page_title="🔍 Validación de Víctimas",
    page_icon="📋",
    layout="wide"
)

def get_db_connection():
    """Conexión a base de datos"""
    return {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
        'user': os.getenv('POSTGRES_USER', 'docs_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'docs_password_2024')
    }

def obtener_victimas_para_validacion(limit=10, offset=0):
    """Obtener víctimas con análisis y texto para validación"""
    try:
        db_config = get_db_connection()
        
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                # Total víctimas únicas
                cur.execute("""
                    SELECT COUNT(DISTINCT p.nombre)
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    WHERE p.tipo ILIKE %s AND p.tipo NOT ILIKE %s
                      AND p.nombre IS NOT NULL AND p.nombre != ''
                """, ('%victima%', '%victimario%'))
                
                total_victimas = cur.fetchone()[0]
                
                # Víctimas con sus datos completos para validación
                cur.execute("""
                    SELECT 
                        p.nombre,
                        p.tipo,
                        d.id,
                        COALESCE(d.nuc, 'N/A') as nuc,
                        COALESCE(d.ruta, 'N/A') as ruta,
                        d.created_at,
                        COALESCE(d.serie, 'N/A') as serie,
                        COALESCE(d.analisis, '') as analisis,
                        COALESCE(d.texto_extraido, '') as texto_extraido,
                        LENGTH(COALESCE(d.analisis, '')) as len_analisis,
                        LENGTH(COALESCE(d.texto_extraido, '')) as len_texto
                    FROM personas p
                    JOIN documentos d ON p.documento_id = d.id
                    WHERE p.tipo ILIKE %s AND p.tipo NOT ILIKE %s
                      AND p.nombre IS NOT NULL AND p.nombre != ''
                    ORDER BY p.nombre
                    LIMIT %s OFFSET %s
                """, ('%victima%', '%victimario%', limit, offset))
                
                resultados = cur.fetchall()
                
                victimas_validacion = []
                for row in resultados:
                    victimas_validacion.append({
                        'nombre': row[0],
                        'tipo': row[1],
                        'doc_id': row[2],
                        'nuc': row[3],
                        'ruta': row[4],
                        'fecha': row[5],
                        'serie': row[6],
                        'analisis': row[7],
                        'texto': row[8],
                        'len_analisis': row[9],
                        'len_texto': row[10],
                        'tiene_analisis': bool(row[7] and row[7].strip()),
                        'tiene_texto': bool(row[8] and row[8].strip())
                    })
                
                return {
                    'total_victimas': total_victimas,
                    'victimas': victimas_validacion,
                    'error': None
                }
                
    except Exception as e:
        return {'error': str(e)}

def mostrar_victima_validacion(victima, indice, offset):
    """Mostrar víctima con opciones de validación claras"""
    
    # Encabezado con información básica
    st.markdown(f"### 👤 {offset + indice}. {victima['nombre']}")
    
    # Información básica en columnas
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"**🏷️ Tipo:** {victima['tipo']}")
        st.write(f"**📄 Documento ID:** {victima['doc_id']}")
        st.write(f"**📁 NUC:** {victima['nuc']}")
    
    with col2:
        st.write(f"**📅 Fecha:** {victima['fecha']}")
        st.write(f"**📋 Serie:** {victima['serie']}")
    
    with col3:
        # Indicadores de contenido disponible
        if victima['tiene_analisis']:
            st.success(f"📋 Análisis: {victima['len_analisis']:,} chars")
        else:
            st.error("📋 Sin análisis")
            
        if victima['tiene_texto']:
            st.success(f"📝 Texto: {victima['len_texto']:,} chars")
        else:
            st.error("📝 Sin texto")
    
    # Pestañas para análisis y texto
    tab1, tab2, tab3 = st.tabs(["📋 Análisis", "📝 Texto Extraído", "📁 Archivo"])
    
    with tab1:
        if victima['tiene_analisis']:
            st.markdown("#### 📋 Análisis del Documento")
            # Mostrar análisis en markdown
            st.markdown(victima['analisis'])
            
            # Botón para copiar análisis
            if st.button(f"📋 Copiar Análisis", key=f"copy_analisis_{victima['doc_id']}_{indice}"):
                st.code(victima['analisis'], language="markdown")
        else:
            st.warning("⚠️ Este documento no tiene análisis disponible")
            st.info("💡 **Recomendación:** Este registro podría necesitar revisión manual")
    
    with tab2:
        if victima['tiene_texto']:
            st.markdown("#### 📝 Texto Extraído del Documento")
            # Mostrar texto en área expandible
            st.text_area(
                "Contenido completo:",
                victima['texto'],
                height=400,
                key=f"texto_area_{victima['doc_id']}_{indice}",
                help="Texto extraído directamente del documento PDF"
            )
            
            # Botón para copiar texto
            if st.button(f"📝 Copiar Texto", key=f"copy_texto_{victima['doc_id']}_{indice}"):
                st.code(victima['texto'], language="text")
        else:
            st.warning("⚠️ Este documento no tiene texto extraído disponible")
            st.info("💡 **Recomendación:** Verificar el archivo PDF original")
    
    with tab3:
        st.markdown("#### 📁 Información del Archivo Original")
        st.write(f"**📂 Ruta:** `{victima['ruta']}`")
        
        if victima['ruta'] and victima['ruta'] != 'N/A':
            if os.path.exists(victima['ruta']):
                st.success("✅ Archivo disponible en el sistema")
                try:
                    stat = os.stat(victima['ruta'])
                    size_mb = stat.st_size / (1024 * 1024)
                    st.write(f"**📊 Tamaño:** {size_mb:.1f} MB")
                except:
                    pass
            else:
                st.error("❌ Archivo no encontrado en la ruta especificada")
        else:
            st.warning("⚠️ Sin ruta de archivo disponible")
    
    # Separador
    st.divider()

def main():
    st.title("🔍 Validación de Víctimas - Análisis y Texto")
    st.markdown("### 📋 Sistema de validación con análisis detallado")
    
    # Alerta informativa
    st.info("""
    🎯 **Objetivo de Validación:**
    - **📋 Revisar análisis** para verificar si realmente son víctimas
    - **📝 Examinar texto original** para confirmar el contexto
    - **🔍 Validar clasificación** correcta de cada persona
    - **⚠️ Identificar posibles errores** de categorización
    """)
    
    # Controles
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        limite = st.selectbox("Registros por página", [5, 10, 15, 25], index=1)
    
    with col2:
        pagina = st.number_input("Página", min_value=1, value=1)
    
    offset = (pagina - 1) * limite
    
    # Botón principal
    if st.button("🔍 Cargar Víctimas para Validación", type="primary"):
        with st.spinner("Cargando víctimas con análisis y texto..."):
            resultado = obtener_victimas_para_validacion(limit=limite, offset=offset)
            
            if resultado.get('error'):
                st.error(f"❌ Error: {resultado['error']}")
            else:
                total = resultado['total_victimas']
                victimas = resultado['victimas']
                
                st.success(f"✅ {len(victimas)} víctimas cargadas de {total:,} totales")
                st.info(f"📄 Página {pagina} de {(total + limite - 1) // limite}")
                
                # Estadísticas de contenido
                con_analisis = sum(1 for v in victimas if v['tiene_analisis'])
                con_texto = sum(1 for v in victimas if v['tiene_texto'])
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    st.metric("📋 Con Análisis", f"{con_analisis}/{len(victimas)}")
                with col_stat2:
                    st.metric("📝 Con Texto", f"{con_texto}/{len(victimas)}")
                with col_stat3:
                    completitud = ((con_analisis + con_texto) / (len(victimas) * 2)) * 100
                    st.metric("📊 Completitud", f"{completitud:.1f}%")
                
                st.markdown("---")
                
                # Mostrar víctimas para validación
                for i, victima in enumerate(victimas, 1):
                    mostrar_victima_validacion(victima, i, offset)
    
    # Sidebar con guía de validación
    with st.sidebar:
        st.header("📖 Guía de Validación")
        
        st.markdown("""
        ### ✅ **Cómo Validar:**
        
        **1. 📋 Revisar Análisis:**
        - ¿Describe realmente a una víctima?
        - ¿El contexto es de violencia/conflicto?
        - ¿La clasificación es correcta?
        
        **2. 📝 Examinar Texto:**
        - ¿Confirma lo del análisis?
        - ¿Hay información adicional relevante?
        - ¿El contexto es claro?
        
        **3. ⚠️ Señales de Alerta:**
        - Nombres genéricos o grupos
        - Falta de contexto específico
        - Clasificación ambigua
        - Sin análisis o texto
        """)
        
        st.header("📊 Estadísticas")
        if st.button("🔄 Actualizar"):
            stats = obtener_victimas_para_validacion(limit=1)
            if not stats.get('error'):
                st.metric("👥 Total Víctimas", f"{stats['total_victimas']:,}")
        
        st.header("ℹ️ Información")
        st.write("**Puerto:** 8507")
        st.write("**Modo:** Validación")
        st.write("**Objetivo:** Control de calidad")

if __name__ == "__main__":
    main()
