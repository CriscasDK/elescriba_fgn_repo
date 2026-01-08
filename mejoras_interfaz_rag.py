#!/usr/bin/env python3
"""
Mejoras para interfaz_fiscales.py - Integración del Clasificador Inteligente
Agregar selector automático mejorado con LLM
"""

# CÓDIGO PARA AGREGAR AL INICIO DE interfaz_fiscales.py (después de los imports existentes)

# Importar el clasificador inteligente
sys.path.append(os.path.dirname(__file__))
from clasificador_inteligente_llm import clasificar_consulta_auto_llm, ClasificadorInteligenteLLM

# Función para mostrar el widget de clasificación automática mejorado
def mostrar_selector_inteligente(consulta_texto):
    """Muestra el selector inteligente mejorado con predicción LLM"""
    
    if not consulta_texto:
        return st.radio(
            "🤖 Método de Consulta",
            ["Base de Datos", "Libro Digital (RAG)", "Ambas"],
            help="Selecciona el método de consulta"
        )
    
    try:
        # Usar clasificador inteligente
        clasificador = ClasificadorInteligenteLLM()
        recomendacion = clasificador.obtener_recomendacion_ui(consulta_texto)
        
        # Mostrar predicción del sistema
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"""
                {recomendacion['icono']} **Recomendación IA:** {recomendacion['tipo']}
                
                📊 **Confianza:** {recomendacion['confianza']:.0%} | ⏱️ **Tiempo estimado:** {recomendacion['tiempo_estimado']}
                
                💡 **Motivo:** {recomendacion['justificacion']}
            """)
        
        with col2:
            usar_recomendacion = st.button(
                "✨ Usar IA", 
                help=f"Usar recomendación: {recomendacion['tipo']}",
                type="secondary"
            )
        
        # Selector manual (siempre disponible)
        opciones = ["Base de Datos", "Libro Digital (RAG)", "Ambas"]
        
        # Si usa recomendación, preseleccionar
        if usar_recomendacion:
            indice_recomendado = opciones.index(recomendacion['tipo']) if recomendacion['tipo'] in opciones else 0
        else:
            indice_recomendado = 0
            
        tipo_respuesta = st.radio(
            "🎯 Método Final",
            opciones,
            index=indice_recomendado,
            help="Puedes cambiar la recomendación manualmente"
        )
        
        return tipo_respuesta
        
    except Exception as e:
        st.warning(f"⚠️ Clasificador IA no disponible: {e}")
        return st.radio(
            "🤖 Método de Consulta",
            ["Base de Datos", "Libro Digital (RAG)", "Ambas"],
            help="Selecciona el método de consulta (clasificador manual)"
        )

# CÓDIGO PARA REEMPLAZAR EN LA SECCIÓN DE CONSULTA PRINCIPAL

def seccion_consulta_mejorada():
    """Sección de consulta principal mejorada con clasificador inteligente"""
    
    st.subheader("🔍 Consulta Inteligente")
    st.markdown("""
    <div class="info-box">
    <h4>🤖 Sistema Híbrido Base de Datos + RAG</h4>
    <p><strong>Base de Datos:</strong> Búsquedas rápidas, conteos, listados, filtros específicos</p>
    <p><strong>RAG + IA:</strong> Análisis conceptual, interpretación, explicaciones complejas</p>
    <p><strong>Automático:</strong> El sistema decide el mejor método usando IA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input de consulta
    col1, col2 = st.columns([3, 1])
    
    with col1:
        consulta_texto = st.text_area(
            "Escribe tu consulta:",
            placeholder="Ej: ¿Qué significa desplazamiento forzado? / ¿Cuántas víctimas hay? / Analizar estructuras criminales...",
            height=100,
            key="consulta_texto_mejorada"
        )
    
    with col2:
        st.markdown("### 💡 Ejemplos")
        st.markdown("""
        **Base de Datos:**
        - ¿Cuántas víctimas hay?
        - Buscar Juan Pérez
        - Listado de organizaciones
        
        **RAG + IA:**
        - ¿Qué significa X?
        - Analizar estructuras
        - ¿Por qué ocurrió Y?
        """)
    
    if consulta_texto:
        # Mostrar selector inteligente
        tipo_respuesta = mostrar_selector_inteligente(consulta_texto)
        
        # Botón de ejecutar
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            ejecutar_consulta = st.button(
                f"🚀 Ejecutar con {tipo_respuesta}", 
                type="primary",
                use_container_width=True
            )
        
        if ejecutar_consulta:
            return consulta_texto, tipo_respuesta
    
    return None, None

# CÓDIGO CSS ADICIONAL PARA MEJORAR LA UI

css_mejorado = """
<style>
.info-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}

.info-box h4 {
    margin-top: 0;
    color: white;
}

.prediction-box {
    background: #f0f2f6;
    border-left: 4px solid #4CAF50;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 5px;
}

.confidence-high { border-left-color: #4CAF50; }
.confidence-medium { border-left-color: #FF9800; }
.confidence-low { border-left-color: #f44336; }

.method-card {
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    transition: all 0.3s ease;
}

.method-card:hover {
    border-color: #1976d2;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.recommended {
    border-color: #4CAF50 !important;
    background: #f8fff8 !important;
}
</style>
"""

# FUNCIÓN PARA INTEGRAR EN LA LÓGICA PRINCIPAL

def procesar_consulta_inteligente(consulta_texto, tipo_respuesta, filtros):
    """Procesa la consulta usando el método seleccionado"""
    
    resultados = None
    tiempo_inicio = time.time()
    
    if tipo_respuesta == "Base de Datos":
        st.subheader("📊 Resultados de Base de Datos")
        with st.spinner("Consultando base de datos..."):
            resultados, total = consulta_base_datos(filtros, consulta_texto)
            
    elif tipo_respuesta == "Libro Digital (RAG)":
        st.subheader("🤖 Análisis RAG + IA")
        with st.spinner("Analizando con inteligencia artificial..."):
            resultado_rag = consulta_rag(consulta_texto)
            if resultado_rag:
                st.markdown(f"""
                <div class="rag-response">
                <h4>🎯 Respuesta del Sistema RAG</h4>
                <p>{resultado_rag.respuesta}</p>
                
                <h5>📚 Fuentes consultadas:</h5>
                <ul>
                """)
                for fuente in resultado_rag.fuentes[:3]:
                    st.markdown(f"<li>{fuente.get('fuente', 'N/A')}</li>")
                st.markdown("</ul></div>", unsafe_allow_html=True)
                
    elif tipo_respuesta == "Ambas":
        st.subheader("🔄 Consulta Híbrida: BD + RAG")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Base de Datos")
            with st.spinner("Consultando BD..."):
                resultados, total = consulta_base_datos(filtros, consulta_texto)
                if resultados:
                    st.success(f"Encontrados {total:,} resultados estructurados")
                    
        with col2:
            st.markdown("### 🤖 Análisis IA")
            with st.spinner("Analizando con IA..."):
                resultado_rag = consulta_rag(consulta_texto)
                if resultado_rag:
                    st.success("Análisis contextual completado")
                    with st.expander("Ver análisis completo"):
                        st.write(resultado_rag.respuesta)
    
    tiempo_respuesta = time.time() - tiempo_inicio
    st.success(f"⚡ Consulta completada en {tiempo_respuesta:.2f} segundos")
    
    return resultados

print("✅ Código de mejoras para interfaz_fiscales.py generado")
print("📝 Para integrar: copiar las funciones a interfaz_fiscales.py")
print("🔧 Reemplazar la sección de consulta actual con seccion_consulta_mejorada()")
