import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os
import re

# Agregar directorio padre al path para importar el sistema RAG
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sistema_rag_completo import SistemaRAGTrazable, ConsultaRAG, FeedbackRAG

# Configuración de página
st.set_page_config(
    page_title="📚 RAG Documentos Judiciales",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-header {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 10px;
        backdrop-filter: blur(10px);
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        backdrop-filter: blur(5px);
    }
    .user-message {
        background: rgba(255,255,255,0.2);
        border-left: 4px solid #4CAF50;
    }
    .assistant-message {
        background: rgba(255,255,255,0.1);
        border-left: 4px solid #2196F3;
    }
    .metric-card {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        backdrop-filter: blur(5px);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_rag_system():
    """Inicializar sistema RAG con cache"""
    return SistemaRAGTrazable()

@st.cache_data(ttl=300)  # Cache por 5 minutos
def extraer_citas_de_texto(texto: str):
    """Extraer números de citas del texto usando regex"""
    patron = r'\[CITA-(\d+)\]'
    citas = re.findall(patron, texto)
    return [int(cita) for cita in citas]

def get_system_stats():
    """Obtener estadísticas del sistema"""
    import psycopg2
    
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'documentos_juridicos_gpt4'),
        'user': os.getenv('POSTGRES_USER', 'docs_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'docs_password_2024')
    }
    
    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                # Estadísticas básicas
                cur.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM documentos) as total_documentos,
                        (SELECT COUNT(*) FROM personas) as total_personas,
                        (SELECT COUNT(*) FROM organizaciones) as total_organizaciones,
                        (SELECT COUNT(*) FROM rag_consultas WHERE DATE(timestamp_consulta) = CURRENT_DATE) as consultas_hoy,
                        (SELECT AVG(tiempo_respuesta_ms) FROM rag_consultas WHERE DATE(timestamp_consulta) = CURRENT_DATE) as tiempo_promedio_hoy
                """)
                stats = cur.fetchone()
                
                return {
                    'total_documentos': int(stats[0]) if stats[0] else 0,
                    'total_personas': int(stats[1]) if stats[1] else 0,
                    'total_organizaciones': int(stats[2]) if stats[2] else 0,
                    'consultas_hoy': int(stats[3]) if stats[3] else 0,
                    'tiempo_promedio_hoy': round(float(stats[4]) if stats[4] else 0, 2)
                }
    except Exception as e:
        st.error(f"Error obteniendo estadísticas: {e}")
        return {
            'total_documentos': 0,
            'total_personas': 0,
            'total_organizaciones': 0,
            'consultas_hoy': 0,
            'tiempo_promedio_hoy': 0
        }

def main():
    """Función principal de la aplicación"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>📚 Sistema RAG - Documentos Judiciales</h1>
        <p>Consulta inteligente sobre documentos del caso Unión Patriótica</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con estadísticas
    with st.sidebar:
        st.header("📊 Estado del Sistema")
        
        # Obtener estadísticas
        stats = get_system_stats()
        
        # Métricas principales
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 Documentos", f"{stats['total_documentos']:,}")
            st.metric("🏛️ Organizaciones", f"{stats['total_organizaciones']:,}")
        with col2:
            st.metric("👥 Personas", f"{stats['total_personas']:,}")
            st.metric("⏱️ Tiempo Prom.", f"{stats['tiempo_promedio_hoy']}ms")
        
        st.metric("🔍 Consultas Hoy", stats['consultas_hoy'])
        
        # Información del sistema
        st.markdown("---")
        st.subheader("🔧 Configuración")
        st.info(f"""
        **Base de Datos:** {os.getenv('POSTGRES_DB', 'N/A')}
        **Modelo IA:** {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'N/A')}
        **Versión:** 2.0
        """)
        
        # Links útiles
        st.markdown("---")
        st.subheader("📚 Documentación")
        st.markdown("""
        - [Guía Técnica](./TECHNICAL_GUIDE.md)
        - [Troubleshooting](./TROUBLESHOOTING.md) 
        - [Query Router](./QUERY_ROUTER_GUIDE.md)
        """)

    # Layout principal con tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat RAG", "📊 Dashboard", "🔍 Análisis"])
    
    with tab1:
        chat_interface()
    
    with tab2:
        dashboard_interface()
    
    with tab3:
        analysis_interface()

def chat_interface():
    """Interfaz de chat principal"""
    st.header("💬 Consulta Inteligente")
    
    # Inicializar sistema RAG
    if 'rag_system' not in st.session_state:
        with st.spinner("🔄 Inicializando sistema RAG..."):
            st.session_state.rag_system = init_rag_system()
    
    # Inicializar historial de chat
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Ejemplos de consultas
    st.subheader("💡 Ejemplos de Consultas")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Estadísticas Generales", key="stats"):
            process_query("¿Cuáles son las estadísticas principales del sistema?")
    
    with col2:
        if st.button("👥 Personas Más Mencionadas", key="people"):
            process_query("¿Cuáles son las 10 personas más mencionadas?")
    
    with col3:
        if st.button("🏛️ Análisis de Organizaciones", key="orgs"):
            process_query("¿Qué organizaciones tienen más documentos relacionados?")
    
    with col4:
        if st.button("🕊️ Unión Patriótica", key="up_genocide"):
            process_query("¿Por qué lo que ocurrió con la Unión Patriótica es un genocidio?")
    
    # Área de entrada de consulta
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_query = st.text_input(
            "🔍 **Escribe tu consulta:**",
            placeholder="Ejemplo: ¿Cómo impactó la violencia a las víctimas en Antioquia?",
            key="user_input"
        )
    
    with col2:
        if st.button("📤 Enviar", type="primary", key="send"):
            if user_query.strip():
                process_query(user_query)
            else:
                st.error("Por favor escribe una consulta")
    
    # Mostrar historial de chat
    st.markdown("---")
    st.subheader("💬 Conversación")
    
    for i, message in enumerate(st.session_state.chat_history):
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>🧑‍💼 Usuario:</strong><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Asistente RAG:</strong><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar texto completo de las citas si están disponibles
            if 'fuentes_detalle' in message and message['fuentes_detalle']:
                citas_en_texto = extraer_citas_de_texto(message['content'])
                
                if citas_en_texto:
                    st.markdown("**📚 Texto completo de las citas:**")
                    
                    for cita_num in citas_en_texto:
                        # Buscar la fuente correspondiente (cita_num - 1 porque las listas empiezan en 0)
                        if cita_num - 1 < len(message['fuentes_detalle']):
                            fuente = message['fuentes_detalle'][cita_num - 1]
                            
                            # Título del expander con información resumida
                            titulo_cita = f"[CITA-{cita_num}] {fuente.get('nombre_archivo', 'N/A')} - Pág. {fuente.get('pagina', 'N/A')}"
                            
                            with st.expander(titulo_cita, expanded=False):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.markdown("**Texto completo:**")
                                    texto_completo = fuente.get('texto_fuente', 'Texto no disponible')
                                    st.markdown(f"*{texto_completo}*")
                                
                                with col2:
                                    st.markdown("**Metadatos:**")
                                    st.markdown(f"**Archivo:** {fuente.get('nombre_archivo', 'N/A')}")
                                    st.markdown(f"**Página:** {fuente.get('pagina', 'N/A')}")
                                    st.markdown(f"**Párrafo:** {fuente.get('parrafo', 'N/A')}")
                                    st.markdown(f"**Tipo:** {fuente.get('tipo_documento', 'N/A')}")
                                    if fuente.get('relevancia'):
                                        st.markdown(f"**Relevancia:** {fuente.get('relevancia', 0):.2f}")
            
            # Botones de feedback
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button("👍", key=f"like_{i}"):
                    st.success("¡Gracias por tu feedback positivo!")
            with col2:
                if st.button("👎", key=f"dislike_{i}"):
                    st.info("Gracias por tu feedback. Trabajaremos en mejorar.")

def process_query(query: str):
    """Procesar consulta del usuario"""
    
    # Agregar consulta del usuario al historial
    st.session_state.chat_history.append({
        'role': 'user',
        'content': query
    })
    
    # Mostrar spinner mientras procesa
    with st.spinner("🧠 Procesando consulta..."):
        try:
            # Crear consulta RAG
            consulta_rag = ConsultaRAG(
                usuario_id="streamlit_user",
                pregunta=query,
                ip_cliente="127.0.0.1"
            )
            
            # Procesar de forma asíncrona
            respuesta, consulta_id = asyncio.run(
                st.session_state.rag_system.procesar_consulta(consulta_rag)
            )
            
            # Agregar respuesta al historial
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': respuesta.texto,
                'tiempo': int(respuesta.tiempo_respuesta) if respuesta.tiempo_respuesta else 0,
                'confianza': round(float(respuesta.confianza) * 100, 1) if respuesta.confianza else 0,
                'metodo': respuesta.metodo.value if hasattr(respuesta.metodo, 'value') else str(respuesta.metodo),
                'fuentes': len(respuesta.fuentes) if respuesta.fuentes else 0,
                'fuentes_detalle': respuesta.fuentes if respuesta.fuentes else []
            })
            
            # Rerun para mostrar la respuesta
            st.rerun()
            
        except Exception as e:
            error_msg = f"Lo siento, hubo un error procesando tu consulta: {str(e)}"
            st.error(error_msg)
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': error_msg,
                'tiempo': 0,
                'confianza': 0,
                'metodo': 'error'
            })
            st.rerun()

def dashboard_interface():
    """Dashboard con métricas y visualizaciones"""
    st.header("📊 Dashboard Ejecutivo")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    stats = get_system_stats()
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📄 Documentos</h3>
            <h2>{stats['total_documentos']:,}</h2>
            <small>Procesados exitosamente</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Personas</h3>
            <h2>{stats['total_personas']:,}</h2>
            <small>Entidades identificadas</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏛️ Organizaciones</h3>
            <h2>{stats['total_organizaciones']:,}</h2>
            <small>Grupos clasificados</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ Performance</h3>
            <h2>{stats['tiempo_promedio_hoy']}ms</h2>
            <small>Tiempo promedio hoy</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráficos de ejemplo (datos simulados para demo)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Consultas por Método")
        # Datos de ejemplo
        data = {
            'Método': ['Cache', 'Vista Materializada', 'RAG Simple', 'RAG Complejo'],
            'Cantidad': [150, 300, 200, 100],
            'Tiempo Promedio (ms)': [5, 80, 1500, 3500]
        }
        df = pd.DataFrame(data)
        
        fig = px.pie(df, values='Cantidad', names='Método', 
                    title="Distribución por Método de Resolución")
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⏱️ Performance por Método")
        fig = px.bar(df, x='Método', y='Tiempo Promedio (ms)',
                    title="Tiempo de Respuesta por Método")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

def analysis_interface():
    """Interfaz de análisis avanzado"""
    st.header("🔍 Análisis Avanzado")
    
    # Selector de tipo de análisis
    analysis_type = st.selectbox(
        "Selecciona el tipo de análisis:",
        ["Análisis de Entidades", "Análisis Geográfico", "Análisis Temporal", "Redes de Relaciones"]
    )
    
    if analysis_type == "Análisis de Entidades":
        entity_analysis()
    elif analysis_type == "Análisis Geográfico":
        geographic_analysis()
    elif analysis_type == "Análisis Temporal":
        temporal_analysis()
    else:
        network_analysis()

def entity_analysis():
    """Análisis de entidades"""
    st.subheader("👥 Análisis de Entidades")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        entity_type = st.selectbox("Tipo de Entidad:", ["Personas", "Organizaciones"])
    
    with col2:
        min_mentions = st.slider("Mínimo de menciones:", 1, 100, 5)
    
    if st.button("🔍 Analizar"):
        with st.spinner("Analizando entidades..."):
            # Aquí iría la lógica real de análisis
            st.success("Análisis completado")
            
            # Datos de ejemplo
            if entity_type == "Personas":
                data = {
                    'Nombre': ['María García', 'Carlos López', 'Ana Rodríguez'],
                    'Tipo': ['Víctima', 'Defensa', 'Testigo'],
                    'Menciones': [45, 32, 28],
                    'Documentos': [15, 12, 18]
                }
            else:
                data = {
                    'Nombre': ['FARC', 'Ejército Nacional', 'Policía Nacional'],
                    'Tipo': ['Fuerza Ilegal', 'Fuerza Legítima', 'Fuerza Legítima'],
                    'Menciones': [234, 189, 145],
                    'Documentos': [89, 67, 54]
                }
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

def geographic_analysis():
    """Análisis geográfico"""
    st.subheader("🗺️ Análisis Geográfico")
    st.info("Esta sección mostraría un mapa interactivo con la distribución geográfica de eventos")
    
    # Placeholder para mapa
    st.markdown("```python\n# Aquí iría un mapa interactivo con Folium o Plotly\n```")

def temporal_analysis():
    """Análisis temporal"""
    st.subheader("📅 Análisis Temporal")
    st.info("Esta sección mostraría la evolución temporal de los eventos")

def network_analysis():
    """Análisis de redes"""
    st.subheader("🕸️ Análisis de Redes")
    st.info("Esta sección mostraría las relaciones entre entidades")

if __name__ == "__main__":
    main()
