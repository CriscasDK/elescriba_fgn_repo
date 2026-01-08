
import dash
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash import html, dcc, Input, Output, State, callback_context
from dash.dependencies import MATCH, ALL
import os
from flask import send_file, abort, send_from_directory
import hashlib
import time
from pathlib import Path

ctx = callback_context
from core.consultas import (
    ejecutar_consulta,
    ejecutar_consulta_geografica_directa,
    obtener_detalle_victima,
    obtener_fuentes_victima,
    obtener_victimas_paginadas,
    obtener_opciones_nuc,
    obtener_opciones_departamento,
    obtener_opciones_municipio,
    obtener_opciones_tipo_documento,
    obtener_opciones_despacho,
    obtener_rango_fechas,
    clasificar_consulta,
    ejecutar_consulta_rag_inteligente,
    ejecutar_consulta_hibrida,
    dividir_consulta_hibrida
)
from config.constants import ENTIDADES_NO_PERSONAS
from core.graph.context_graph_builder import extract_entities_from_query_result
from core.graph.visualizers.g6_adapter import G6Adapter
import re
import json

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# ============================================================================
# CONFIGURACIÓN FLASK PARA SERVIR ARCHIVOS ESTÁTICOS (G6)
# ============================================================================

@app.server.route('/static/grafos/<path:filename>')
def serve_graph(filename):
    """Sirve visualizaciones G6 desde directorio static/grafos/"""
    return send_from_directory('static/grafos', filename)

# Cache de visualizaciones G6 generadas
_grafo_g6_cache = {}


# ============================================================================
# FUNCIONES HELPER PARA VISUALIZACIÓN G6
# ============================================================================

def generar_grafo_g6_cached(nodos, aristas, titulo="Grafo de Relaciones"):
    """
    Genera visualización G6 con cache para evitar regenerar grafos idénticos.
    
    Args:
        nodos: Lista de nodos del grafo
        aristas: Lista de aristas del grafo
        titulo: Título de la visualización
    
    Returns:
        str: URL del archivo HTML generado
    """
    # Crear hash único de los datos para cache
    data_str = json.dumps({'n': nodos, 'e': aristas}, sort_keys=True)
    data_hash = hashlib.md5(data_str.encode()).hexdigest()
    
    # Verificar si ya está en cache
    if data_hash in _grafo_g6_cache:
        print(f"✅ Grafo G6 {data_hash[:8]} recuperado de cache")
        return _grafo_g6_cache[data_hash]
    
    # Generar nuevo grafo
    print(f"🔨 Generando grafo G6 {data_hash[:8]}... ({len(nodos)} nodos, {len(aristas)} aristas)")
    start_time = time.time()
    
    try:
        adapter = G6Adapter()
        static_dir = Path("static/grafos")
        static_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"grafo_{data_hash}.html"
        output_path = static_dir / filename
        
        adapter.save_html(
            nodes=nodos,
            edges=aristas,
            output_path=str(output_path),
            title=titulo,
            subtitle=f"Sistema Judicial • {len(nodos)} nodos, {len(aristas)} relaciones"
        )
        
        url = f"/static/grafos/{filename}"
        _grafo_g6_cache[data_hash] = url
        
        elapsed = time.time() - start_time
        print(f"✅ Grafo G6 generado en {elapsed:.2f}s: {url}")
        
        return url
        
    except Exception as e:
        print(f"❌ Error generando grafo G6: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# FUNCIONES HELPER PARA EXTRACCIÓN DE ENTIDADES Y GEOGRAFÍA
# ============================================================================

def cargar_municipios_desde_db():
    """
    Carga lista de municipios únicos desde vista materializada.
    Cache en memoria para evitar múltiples queries.

    Returns:
        dict: {municipio_normalizado: municipio_original}
    """
    import psycopg2
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="documentos_juridicos_gpt4",
            user="docs_user",
            password="docs_password_2025"
        )
        cur = conn.cursor()

        # Query para obtener todos los municipios únicos
        cur.execute("""
            SELECT DISTINCT municipio
            FROM analisis_lugares
            WHERE municipio IS NOT NULL
              AND municipio <> ''
              AND LENGTH(municipio) > 2
            ORDER BY municipio;
        """)

        municipios = {}
        for row in cur.fetchall():
            municipio = row[0].strip()
            # Normalizar para búsqueda (lowercase, sin acentos)
            municipio_norm = municipio.lower()
            # Almacenar original para usar en filtros
            municipios[municipio_norm] = municipio

        cur.close()
        conn.close()

        print(f"✅ Cargados {len(municipios)} municipios desde BD")
        return municipios

    except Exception as e:
        print(f"❌ Error cargando municipios: {e}")
        return {}

# Cache global de municipios (se carga una vez al inicio)
_MUNICIPIOS_CACHE = None

def obtener_municipios():
    """Retorna cache de municipios, cargándolo si es necesario"""
    global _MUNICIPIOS_CACHE
    if _MUNICIPIOS_CACHE is None:
        _MUNICIPIOS_CACHE = cargar_municipios_desde_db()
    return _MUNICIPIOS_CACHE


def reescribir_query_con_contexto(consulta_actual: str, history_data: dict) -> tuple:
    """
    Reescribe una query contextual agregando entidades del historial.

    Esta función soluciona la limitación del RAG con preguntas secuenciales:
    - Pregunta 1: "Oswaldo Olivo" → RAG busca chunks sobre Oswaldo
    - Pregunta 2: "su relación con Rosa Edith Sierra" → RAG NO encuentra la conexión

    Con reescritura:
    - Pregunta 2 se convierte en: "Oswaldo Olivo y su relación con Rosa Edith Sierra"

    LÍMITE DE SECUENCIA:
    - Después de 3 reescrituras consecutivas, toma SOLO la última entidad
    - Esto evita acumulación de entidades y drift semántico
    - Ejemplo: "Juan y María y Pedro" → Después de 3, solo "Pedro"

    Args:
        consulta_actual: La consulta del usuario que puede tener referencias contextuales
        history_data: Diccionario con historial de conversaciones

    Returns:
        tuple: (query_reescrita, fue_reescrita, entidades_agregadas, consecutive_rewrites)
    """
    # Detectar si la consulta tiene referencias contextuales
    referencias_contextuales = [
        'su ', 'sus ', 'él', 'ella', 'ellos', 'ellas',
        'esa persona', 'ese caso', 'esa organización',
        'la anterior', 'el anterior', 'lo anterior',
        'mencionado', 'mencionada', 'de esa', 'de ese'
    ]

    consulta_lower = consulta_actual.lower()
    tiene_referencia = any(ref in consulta_lower for ref in referencias_contextuales)

    if not tiene_referencia:
        # No es una pregunta contextual, retornar sin cambios
        return (consulta_actual, False, [], 0)

    # ✅ NUEVO: Contar reescrituras consecutivas para evitar drift
    consecutive_rewrites = 0
    if history_data and history_data.get('history'):
        for conv in reversed(history_data['history'][-5:]):  # Revisar últimas 5
            if conv.get('query_rewritten', False):
                consecutive_rewrites += 1
            else:
                break  # Se encontró una consulta NO reescrita, detener conteo

    # Extraer entidades de las últimas 2 conversaciones
    entidades_contexto = []
    if history_data and history_data.get('history'):
        ultimas_conversaciones = history_data['history'][-2:]  # Últimas 2

        for conv in ultimas_conversaciones:
            user_query = conv.get('user_query', '')
            # Extraer nombres propios de la consulta previa
            nombres = re.findall(
                r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)+\b',
                user_query
            )
            for nombre in nombres:
                if nombre not in entidades_contexto:
                    entidades_contexto.append(nombre)

    if not entidades_contexto:
        # No hay entidades en el contexto, retornar sin cambios
        return (consulta_actual, False, [], consecutive_rewrites)

    # ✅ LÍMITE: Después de 3 reescrituras, tomar SOLO la última entidad
    if consecutive_rewrites >= 3:
        print(f"⚠️  LÍMITE DE SECUENCIA ALCANZADO ({consecutive_rewrites} reescrituras consecutivas)")
        print(f"   Tomando SOLO última entidad para evitar drift semántico")
        entidades_contexto = entidades_contexto[-1:]  # Solo la última

    # Reescribir query agregando entidades del contexto
    # Estrategia: agregar entidades al inicio
    entidades_str = " y ".join(entidades_contexto)
    query_reescrita = f"{entidades_str}: {consulta_actual}"

    print(f"🔄 REESCRITURA DE QUERY (secuencia #{consecutive_rewrites + 1}):")
    print(f"   Original: '{consulta_actual}'")
    print(f"   Reescrita: '{query_reescrita}'")
    print(f"   Entidades agregadas: {entidades_contexto}")

    return (query_reescrita, True, entidades_contexto, consecutive_rewrites + 1)


# ❌ DESACTIVADA: Secuenciación SQL
# Razón: Demasiado compleja, casos ambiguos causan resultados incorrectos
# Ejemplo: "víctimas en Antioquia" → "de esos en Medellín" → 0 resultados
# Se mantiene solo reescritura RAG que cubre el 80% de casos
#
# def detectar_referencia_sql(consulta: str, history_data: dict) -> tuple:
#     """
#     Detecta referencias a resultados SQL previos en la consulta actual.
#     DESACTIVADA - Ver razones arriba
#     """
#     return (False, [], None)


def extraer_entidades_de_consulta(consulta: str) -> list:
    """
    Extrae nombres de entidades (personas, organizaciones) de una consulta.
    Reutiliza la lógica de clasificar_consulta() en core/consultas.py línea 830.

    Args:
        consulta: Texto de la consulta del usuario

    Returns:
        Lista de nombres de entidades encontradas
    """
    # Mismo regex que en clasificar_consulta() línea 830
    nombres_propios = re.findall(
        r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b',
        consulta
    )

    # Filtrar nombres que NO son entidades geográficas/conceptuales
    nombres_entidades = []
    for nombre in nombres_propios:
        if nombre.lower() not in ENTIDADES_NO_PERSONAS:
            nombres_entidades.append(nombre)

    return nombres_entidades


# ============================================================================
# CALLBACKS
# ============================================================================

# Callback para mostrar/ocultar texto de chunk RAG
@app.callback(
    Output({'type': 'chunk-text', 'index': MATCH}, 'style'),
    Input({'type': 'chunk-btn', 'index': MATCH}, 'n_clicks'),
    State({'type': 'chunk-text', 'index': MATCH}, 'style')
)
def mostrar_texto_chunk(n_clicks, current_style):
    try:
        if n_clicks and n_clicks % 2 == 1:
            style = current_style.copy() if current_style else {}
            style['display'] = 'block'
            return style
        else:
            style = current_style.copy() if current_style else {}
            style['display'] = 'none'
            return style
    except Exception as e:
        import logging
        logging.error(f"Error en mostrar_texto_chunk: {e}")
        return {'display': 'none'}

app.layout = dbc.Container([
    # Botón flotante para abrir grafo 3D
    html.Button(
        "🌐 Grafo 3D",
        id="btn-open-graph",
        n_clicks=0,
        style={
            'position': 'fixed',
            'top': '20px',
            'right': '20px',
            'zIndex': '1000',
            'padding': '12px 24px',
            'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'color': 'white',
            'border': 'none',
            'borderRadius': '25px',
            'fontSize': '16px',
            'fontWeight': 'bold',
            'cursor': 'pointer',
            'boxShadow': '0 4px 15px rgba(0,0,0,0.2)',
            'transition': 'all 0.3s'
        }
    ),

    # SECCIÓN INLINE para el grafo 3D (reemplaza modal problemático)
    html.Div([
        html.Div([
            html.H4("🌐 Visualización del Grafo de Conocimiento", style={"display": "inline-block"}),
            html.Button("❌ Cerrar", id="btn-close-graph-inline", className="btn btn-sm btn-danger float-end")
        ], style={"marginBottom": "10px"}),
        html.Div([
            # Botón para colapsar/expandir configuración
            html.Button(
                "⚙️ Configuración",
                id="toggle-graph-config",
                className="btn btn-sm btn-outline-secondary mb-2"
            ),

            # Panel de configuración colapsable
            dbc.Collapse([
                # Tabs para diferentes modos de consulta
                dbc.Tabs([
                # Tab 1: Consultas predefinidas
                dbc.Tab(label="📊 Consultas Predefinidas", tab_id="tab-predefined", children=[
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(
                                id='graph-query-selector',
                                options=[
                                    {'label': '⭐ Nodos Más Conectados (100 rel.)', 'value': 'top_connected'},
                                    {'label': '👥 Personas y Organizaciones', 'value': 'personas_y_organizaciones'},
                                    {'label': '📄 Documentos Recientes (100)', 'value': 'documentos_recientes'},
                                    {'label': '📍 Red Geográfica', 'value': 'geografia'},
                                    {'label': '🌍 Grafo Completo (cuidado: puede ser lento)', 'value': 'full_graph'},
                                ],
                                value='top_connected',
                                clearable=False,
                                placeholder="Selecciona una consulta..."
                            )
                        ], width=8),
                        dbc.Col([
                            html.Button(
                                '🔄 Generar',
                                id='graph-generate-btn',
                                n_clicks=0,
                                className='btn btn-success w-100'
                            )
                        ], width=4)
                    ], className="mb-3 mt-3"),
                ]),

                # Tab 2: Consulta contextual (búsqueda por entidades)
                dbc.Tab(label="🔍 Búsqueda Contextual", tab_id="tab-contextual", children=[
                    dbc.Row([
                        dbc.Col([
                            dcc.Input(
                                id='graph-entity-search',
                                type='text',
                                placeholder='Ej: Oswaldo Olivo, Rosa Edith Sierra',
                                className='form-control',
                                style={'width': '100%'}
                            ),
                            html.Small(
                                "Ingresa nombres de personas u organizaciones separados por coma",
                                className="text-muted"
                            )
                        ], width=12)
                    ], className="mb-2 mt-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Checklist(
                                id='graph-context-options',
                                options=[
                                    {'label': ' Incluir vecindarios (1 salto)', 'value': 'neighborhood'},
                                    {'label': ' Mostrar co-ocurrencias', 'value': 'cooccurrence'},
                                    {'label': ' Incluir documentos fuente', 'value': 'documents'},
                                ],
                                value=['documents'],
                                inline=True
                            )
                        ], width=8),
                        dbc.Col([
                            html.Button(
                                '🔍 Buscar',
                                id='graph-search-btn',
                                n_clicks=0,
                                className='btn btn-primary w-100'
                            )
                        ], width=4)
                    ], className="mb-3"),
                ]),
                ], id="graph-tabs", active_tab="tab-predefined", className="mb-3"),
            ], id="collapse-graph-config", is_open=False),  # Cerrado por defecto

            # Estadísticas
            html.Div(id='graph-stats', className='mb-3'),

            # ✅ FILTROS POR TIPO DE NODO
            dbc.Card([
                dbc.CardHeader("🎯 Filtrar por Tipo de Nodo", className="bg-primary text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Checklist(
                                id="graph-node-filters",
                                options=[
                                    {"label": "🔵 Víctimas", "value": "victima"},
                                    {"label": "🔴 Victimarios", "value": "victimario"},
                                    {"label": "🟡 Familiares", "value": "familiar"},
                                    {"label": "❌ Entidades Ilegales", "value": "entidad_ilegal"},
                                    {"label": "🏛️ Entidades Estatales", "value": "entidad_estatal"},
                                    {"label": "👤 Otras Personas", "value": "persona"},
                                ],
                                value=["victima", "victimario", "familiar", "entidad_ilegal", "entidad_estatal", "persona"],  # Default: MOSTRAR TODO
                                inline=True,
                                switch=True
                            )
                        ], width=12)
                    ])
                ])
            ], className="mb-3"),

            # ✅ FILTROS POR TIPO DE RELACIÓN
            dbc.Card([
                dbc.CardHeader("🔗 Filtrar por Tipo de Relación", className="bg-info text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Checklist(
                                id="graph-relation-filters",
                                options=[
                                    {"label": "🔴 Víctima De", "value": "VICTIMA_DE"},
                                    {"label": "🟣 Perpetrador", "value": "PERPETRADOR"},
                                    {"label": "🟢 Mencionado En", "value": "MENCIONADO_EN"},
                                    {"label": "🔵 Co-ocurre Con", "value": "CO_OCURRE_CON"},
                                    {"label": "🟠 Relacionado Con", "value": "RELACIONADO_CON"},
                                    {"label": "🟡 Organización", "value": "ORGANIZACION"},
                                    {"label": "🔷 Miembro De", "value": "MIEMBRO_DE"},
                                    {"label": "📄 Documento", "value": "DOCUMENTO"},
                                ],
                                value=["VICTIMA_DE", "PERPETRADOR", "MENCIONADO_EN", "CO_OCURRE_CON",
                                       "RELACIONADO_CON", "ORGANIZACION", "MIEMBRO_DE", "DOCUMENTO"],  # Default: MOSTRAR TODO
                                inline=True,
                                switch=True
                            )
                        ], width=12)
                    ])
                ])
            ], className="mb-3"),

            # ✅ TOGGLE PARA CAMBIAR ENTRE VISUALIZACIONES
            dbc.Card([
                dbc.CardHeader("🎨 Modo de Visualización", className="bg-success text-white"),
                dbc.CardBody([
                    dbc.RadioItems(
                        id="graph-viz-mode",
                        options=[
                            {"label": "📊 Plotly 3D (Clásico)", "value": "plotly"},
                            {"label": "✨ G6 Modern (Nuevo)", "value": "g6"}
                        ],
                        value="g6",  # Por defecto G6
                        inline=True,
                        className="mb-2"
                    ),
                    html.Small("G6 ofrece mejor performance y estética moderna", className="text-muted")
                ])
            ], className="mb-3"),

            # Visualización con Plotly (se oculta cuando G6 está activo)
            html.Div(
                id="plotly-graph-container",
                children=[
                    dcc.Loading(
                        id="loading-graph",
                        type="default",
                        children=[
                            dcc.Graph(
                                id='graph-viewer',
                                figure={},
                                style={'height': '700px'},
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False,
                                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
                                }
                            )
                        ]
                    )
                ],
                style={'display': 'none'}  # Oculto por defecto
            ),

            # Visualización con G6 (iframe)
            html.Div(
                id="g6-graph-container",
                children=[
                    dcc.Loading(
                        id="loading-g6-graph",
                        type="default",
                        children=[
                            html.Iframe(
                                id='graph-g6-iframe',
                                src='',
                                style={
                                    'width': '100%',
                                    'height': '800px',
                                    'border': 'none',
                                    'border-radius': '10px',
                                    'box-shadow': '0 4px 20px rgba(0,0,0,0.1)'
                                }
                            )
                        ]
                    )
                ],
                style={'display': 'block'}  # Visible por defecto
            )
        ], style={'minHeight': '700px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'border': '2px solid #2196F3'})
    ],
    id="graph-inline-container",
    # ✅ FIX: Eliminado className="d-none" que impedía visualización
    # El callback controla visibilidad solo con style={'display': 'none'}
    style={'marginTop': '20px', 'marginBottom': '20px', 'display': 'none'}
    ),

    # Panel de filtros superior
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="dropdown-nuc",
                options=[{"label": "Todos los NUCs", "value": "__ALL__"}] + [{"label": nuc, "value": nuc} for nuc in obtener_opciones_nuc()],
                multi=True,
                placeholder="Selecciona NUCs"
            )
        ], width=2),
        dbc.Col([
            dcc.Dropdown(
                id="dropdown-departamento",
                options=[{"label": dep, "value": dep} for dep in obtener_opciones_departamento()],
                placeholder="Departamento"
            )
        ], width=2),
        dbc.Col([
            dcc.Dropdown(
                id="dropdown-municipio",
                options=[{"label": mun, "value": mun} for mun in obtener_opciones_municipio()],
                placeholder="Municipio"
            )
        ], width=2),
        dbc.Col([
            dcc.Dropdown(
                id="dropdown-tipo-documento",
                options=[{"label": tipo, "value": tipo} for tipo in obtener_opciones_tipo_documento()],
                placeholder="Tipo documento"
            )
        ], width=2),
        dbc.Col([
            dcc.Dropdown(
                id="dropdown-despacho",
                options=[{"label": desp, "value": desp} for desp in obtener_opciones_despacho()],
                placeholder="Despacho"
            )
        ], width=2),
        dbc.Col([
            dcc.DatePickerRange(
                id="date-picker-range",
                start_date=obtener_rango_fechas()[0],
                end_date=obtener_rango_fechas()[1],
                display_format='YYYY-MM-DD',
                style={'width': '100%'}
            )
        ], width=2),
    ], className="mb-3"),

    # Stores ocultos para datos del grafo contextual
    dcc.Store(id='graph-context-data', data=None, storage_type='memory'),
    dcc.Store(id='victima-seleccionada-red', data=None, storage_type='memory'),  # Para grafo individual de víctima
    dcc.Store(id='graph-raw-data', data=None, storage_type='memory'),  # ✅ Datos RAW del grafo (sin filtros aplicados) para filtrado reactivo

    # Store para historial conversacional
    # storage_type='session': Persiste durante la sesión del navegador (sobrevive a recargas)
    dcc.Store(id='conversation-history', data={'history': [], 'max_turns': 10}, storage_type='session'),

    # Paneles principales en horizontal
    dbc.Row([
        dbc.Col([
            html.H4("Análisis IA"),
            # Botón Ver Red (inicialmente oculto)
            html.Div(
                id="container-btn-ver-red",
                children=[
                    html.Button(
                        "🌐 Ver Red de Relaciones",
                        id="btn-ver-red-contextual",
                        n_clicks=0,
                        style={"display": "none"}  # Oculto por defecto
                    )
                ],
                style={"marginBottom": "10px"}
            ),
            dcc.Loading(
                id="loading-ia",
                type="default",
                children=[
                    html.Div(id="panel-ia", style={"height": "400px", "overflowY": "auto", "background": "#f8fff8", "borderRadius": "8px", "border": "1px solid #4CAF50", "padding": "12px"})
                ]
            )
        ], width=4),
        dbc.Col([
            html.H4("Datos BD"),
            dcc.Loading(
                id="loading-bd",
                type="default",
                children=[
                    html.Div([
                        html.H5("Lista de víctimas (Página 1):"),
                        html.Div("No hay víctimas para mostrar."),
                        html.Div([
                            html.Button("Anterior", id="btn-pag-prev", n_clicks=0, style={"margin": "4px"}),
                            dcc.Input(id="input-pag", type="number", value=1, min=1, max=1, style={"width": "60px"}),
                            html.Button("Siguiente", id="btn-pag-next", n_clicks=0, style={"margin": "4px"}),
                            html.Span("Total: 0")
                        ], style={"marginTop": "12px"})
                    ], id="panel-bd", style={"height": "400px", "overflowY": "auto", "background": "#f8fbff", "borderRadius": "8px", "border": "1px solid #2196F3", "padding": "12px"})
                ]
            )
        ], width=4),
        dbc.Col([
            html.H4("Documentos y Fuentes"),
            dcc.Loading(
                id="loading-fuentes",
                type="default",
                children=[
                    html.Div(id="panel-fuentes", style={"height": "400px", "overflowY": "auto", "background": "#f3eaff", "borderRadius": "8px", "border": "1px solid #6a1b9a", "padding": "12px"})
                ]
            )
        ], width=4),
    ], className="gy-3"),

    # Historial conversacional (colapsable)
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "📜 Ver Historial de Conversación",
                id="btn-toggle-history",
                color="info",
                outline=True,
                size="sm",
                className="mb-2"
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        id="history-content",
                        children=[html.P("No hay conversaciones previas", className="text-muted")]
                    ),
                    style={"maxHeight": "300px", "overflowY": "auto"}
                ),
                id="collapse-history",
                is_open=False,
            ),
        ], width=12)
    ], className="mt-3"),

    # Input de consulta abajo
    dbc.Row([
        dbc.Col([
            dcc.Input(id="input-consulta", type="text", placeholder="Escribe tu consulta...", style={"width": "100%"}),
            html.Div([
                html.Div([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                dbc.Checklist(
                                    id="use-context-checkbox",
                                    options=[{"label": " 🔗 Usar contexto de consultas anteriores", "value": "use_context"}],
                                    value=[],  # Desactivado por defecto
                                    inline=True,
                                    switch=True,
                                ),
                                html.Small(
                                    id="context-indicator",
                                    children="",
                                    className="text-muted ms-2"
                                )
                            ], style={"display": "flex", "alignItems": "center"}),
                            # Slider para configurar historial
                            html.Div([
                                html.Label("📊 Conversaciones a recordar:", style={"fontSize": "0.85em", "marginBottom": "5px"}),
                                dcc.Slider(
                                    id="history-max-turns-slider",
                                    min=5,
                                    max=50,
                                    step=5,
                                    value=10,  # Default
                                    marks={
                                        5: '5',
                                        10: '10',
                                        20: '20',
                                        30: '30',
                                        50: '50'
                                    },
                                    tooltip={"placement": "bottom", "always_visible": False}
                                ),
                                html.Small(id="history-max-display", className="text-muted", style={"fontSize": "0.75em"})
                            ], className="mt-2")
                        ], style={"padding": "8px 12px"})
                    ], color="light", outline=True, className="mt-2")
                ], style={"display": "inline-block", "marginRight": "15px", "width": "100%", "maxWidth": "500px"}),
                html.Div([
                    html.Button("Enviar", id="btn-enviar", n_clicks=0, className="mt-2 me-2"),
                    html.Button("🗑️ Limpiar Historial", id="btn-clear-history", n_clicks=0, className="mt-2 btn btn-outline-secondary btn-sm")
                ], style={"display": "inline-block"})
            ])
        ], width=12)
    ], className="mt-4"),
], fluid=True)

from dash.dependencies import ALL

# Callback para mostrar paneles y manejar selección de víctima
from dash.dependencies import ALL

# Callback para mostrar paneles y manejar selección de víctima y paginación
from dash import ctx

# ============================================================================
# CALLBACKS DEL HISTORIAL CONVERSACIONAL
# ============================================================================

# Callback para toggle del historial
@app.callback(
    Output("collapse-history", "is_open"),
    Input("btn-toggle-history", "n_clicks"),
    State("collapse-history", "is_open"),
    prevent_initial_call=True
)
def toggle_history(n_clicks, is_open):
    """Toggle la visibilidad del historial de conversación"""
    if n_clicks:
        return not is_open
    return is_open

# Callback para limpiar el historial
@app.callback(
    Output("conversation-history", "data", allow_duplicate=True),
    Input("btn-clear-history", "n_clicks"),
    prevent_initial_call=True
)
def clear_history(n_clicks):
    """Limpia el historial de conversación"""
    if n_clicks:
        print("🗑️ Historial limpiado por el usuario")
        return {'history': [], 'max_turns': 10}
    return dash.no_update

# Callback para actualizar display del slider de max_turns
@app.callback(
    Output("history-max-display", "children"),
    Input("history-max-turns-slider", "value")
)
def update_slider_display(value):
    """Muestra el valor actual del slider"""
    return f"Recordar últimas {value} conversaciones"

# Callback para aplicar cambio de max_turns al Store
@app.callback(
    Output("conversation-history", "data", allow_duplicate=True),
    Input("history-max-turns-slider", "value"),
    State("conversation-history", "data"),
    prevent_initial_call=True
)
def update_max_turns(new_max_turns, history_data):
    """Actualiza el max_turns del historial y recorta si es necesario"""
    if history_data:
        history_data['max_turns'] = new_max_turns
        # Recortar historial si el nuevo límite es menor
        if len(history_data['history']) > new_max_turns:
            history_data['history'] = history_data['history'][-new_max_turns:]
            print(f"📊 Historial recortado a {new_max_turns} conversaciones")
        else:
            print(f"📊 Max turns actualizado a {new_max_turns}")
        return history_data
    return dash.no_update

# Callback para actualizar la visualización del historial
@app.callback(
    Output("history-content", "children"),
    Input("conversation-history", "data")
)
def update_history_display(history_data):
    """Actualiza la visualización del historial cuando cambia el Store"""
    if not history_data or not history_data.get('history'):
        return [html.P("No hay conversaciones previas", className="text-muted")]

    history_items = []
    for i, item in enumerate(reversed(history_data['history'])):
        # Mostrar cada intercambio de conversación
        history_items.append(
            dbc.Card(
                dbc.CardBody([
                    html.Small(item.get('timestamp', ''), className="text-muted"),
                    html.P([
                        html.Strong("👤 Usuario: "),
                        item.get('user_query', '')
                    ], className="mb-1 mt-2"),
                    html.P([
                        html.Strong("🤖 Sistema: "),
                        item.get('system_response_preview', '')[:200] + "..." if len(item.get('system_response_preview', '')) > 200 else item.get('system_response_preview', '')
                    ], className="mb-1", style={"fontSize": "0.9em"}),
                    html.Small(f"Tipo: {item.get('query_type', 'N/A')}", className="text-info")
                ]),
                className="mb-2",
                color="light"
            )
        )

    return history_items

# ============================================================================
# CALLBACK PRINCIPAL DE CONSULTAS (modificado para usar historial)
# ============================================================================

@app.callback(
    Output("panel-ia", "children"),
    Output("panel-bd", "children"),
    Output("panel-fuentes", "children"),
    Output("btn-ver-red-contextual", "style"),
    Output("btn-ver-red-contextual", "children"),
    Output("graph-context-data", "data"),
    Output("conversation-history", "data"),  # Nueva salida para actualizar historial
    Input("btn-enviar", "n_clicks"),
    State("input-consulta", "value"),
    State("dropdown-nuc", "value"),
    State("dropdown-departamento", "value"),
    State("dropdown-municipio", "value"),
    State("dropdown-tipo-documento", "value"),
    State("dropdown-despacho", "value"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
    Input({'type': 'victima-btn', 'index': ALL}, 'n_clicks'),
    Input('btn-pag-next', 'n_clicks'),
    Input('btn-pag-prev', 'n_clicks'),
    State('input-pag', 'value'),
    State("conversation-history", "data"),  # Nueva entrada para leer historial actual
    State("use-context-checkbox", "value")  # Checkbox para activar contexto
)
def actualizar_paneles(n_clicks, consulta, nucs, departamento, municipio, tipo_documento, despacho, fecha_inicio, fecha_fin, victima_clicks, pag_next, pag_prev, pag_input, history_data, use_context):
    # Paginación
    page = int(pag_input) if pag_input else 1
    if ctx.triggered_id == 'btn-pag-next':
        page += 1
    elif ctx.triggered_id == 'btn-pag-prev' and page > 1:
        page -= 1

    # === SISTEMA INTELIGENTE DE CONSULTAS ===
    resultados = None
    tipo_detectado = None
    victimas_filtradas = None
    total_victimas_filtradas = None

    if n_clicks and consulta:
        # 1. Construir contexto conversacional desde historial (SOLO SI EL USUARIO LO ACTIVA)
        contexto_conversacional = ""
        use_context_enabled = use_context and 'use_context' in use_context

        if use_context_enabled and history_data and history_data.get('history'):
            print(f"📚 Construyendo contexto desde {len(history_data['history'])} conversaciones previas")
            contexto_items = []
            for item in history_data['history'][-5:]:  # Últimas 5 conversaciones
                contexto_items.append(f"Usuario: {item['user_query']}")
                # Usar respuesta completa para GPT (1500 chars) o fallback a preview (300 chars)
                response_text = item.get('system_response_full', item.get('system_response_preview', ''))
                contexto_items.append(f"Sistema: {response_text}")
            contexto_conversacional = "\n".join(contexto_items)
            print(f"✅ Contexto activado por usuario: {len(contexto_conversacional)} caracteres")
        else:
            if history_data and history_data.get('history'):
                print(f"ℹ️ Contexto disponible ({len(history_data['history'])} entradas) pero NO activado por usuario")

        # 2. Clasificar consulta automáticamente
        tipo_detectado = clasificar_consulta(consulta)
        print(f"🔍 DASH DEBUG: Consulta='{consulta}', Tipo={tipo_detectado}, Contexto={'ACTIVO' if use_context_enabled else 'DESACTIVADO'}")

        # 3. Ejecutar según clasificación
        if tipo_detectado == 'bd':
            # Consulta cuantitativa (Base de Datos)
            # Detectar departamento en el texto si no viene de UI
            if not departamento:
                consulta_lower = consulta.lower()
                departamentos_conocidos = ['antioquia', 'bogotá', 'valle del cauca', 'cundinamarca', 'santander',
                                          'atlántico', 'bolívar', 'magdalena', 'tolima', 'huila', 'nariño',
                                          'cauca', 'meta', 'cesar', 'córdoba', 'norte de santander', 'boyacá',
                                          'caldas', 'risaralda', 'quindío', 'caquetá', 'putumayo', 'casanare',
                                          'sucre', 'la guajira', 'chocó', 'arauca', 'amazonas', 'guainía',
                                          'guaviare', 'vaupés', 'vichada', 'san andrés']

                for dept in departamentos_conocidos:
                    if dept in consulta_lower:
                        departamento = dept.title()
                        print(f"🔍 BD: Detectado departamento '{departamento}' en consulta: '{consulta}'")
                        break

            # ✅ NUEVO: Detectar municipio en el texto si no viene de UI
            if not municipio:
                consulta_lower = consulta.lower()
                municipios_db = obtener_municipios()

                # Buscar municipios en orden de longitud (más largos primero para evitar falsos positivos)
                # Ejemplo: "San José de Apartadó" debe matchear antes que "Apartadó" o "San José"
                municipios_ordenados = sorted(municipios_db.keys(), key=len, reverse=True)

                for mun_norm in municipios_ordenados:
                    if mun_norm in consulta_lower:
                        municipio = municipios_db[mun_norm]  # Usar nombre original de BD
                        print(f"🔍 BD: Detectado municipio '{municipio}' en consulta: '{consulta}'")
                        break

            # Si hay filtros geográficos/temporales, usar función directa
            if departamento or municipio or (nucs and len(nucs) > 0) or despacho or tipo_documento or fecha_inicio or fecha_fin:
                resultados = ejecutar_consulta_geografica_directa(
                    consulta,
                    departamento=departamento,
                    municipio=municipio,
                    nuc=nucs[0] if nucs and len(nucs) > 0 else None,
                    despacho=despacho,
                    tipo_documento=tipo_documento,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                    # Sin limit_victimas - devuelve todas las víctimas encontradas (consistente con híbrida)
                )
            else:
                resultados = ejecutar_consulta(
                    consulta,
                    nucs=nucs,
                    departamento=departamento,
                    municipio=municipio,
                    tipo_documento=tipo_documento,
                    despacho=despacho,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )
            resultados['tipo_ejecutado'] = 'Base de Datos (Cuantitativa)'
            # Usar víctimas filtradas de la consulta si están disponibles
            if 'victimas' in resultados:
                victimas_filtradas = resultados['victimas']
                total_victimas_filtradas = len(victimas_filtradas)

        elif tipo_detectado == 'rag':
            # Consulta cualitativa (RAG)
            # ✅ MEJORA: Reescribir query con contexto ANTES de enviar al RAG
            consulta_para_rag = consulta
            query_fue_reescrita = False
            consecutive_rewrites = 0

            if use_context_enabled and history_data and history_data.get('history'):
                # Intentar reescribir la query agregando entidades del contexto
                consulta_para_rag, query_fue_reescrita, entidades_agregadas, consecutive_rewrites = reescribir_query_con_contexto(
                    consulta, history_data
                )

            # Enriquecer consulta con contexto si está disponible (mantener compatibilidad)
            consulta_enriquecida = consulta_para_rag
            if contexto_conversacional and not query_fue_reescrita:
                # Solo agregar prompt de contexto si NO se reescribió la query
                consulta_enriquecida = f"""IMPORTANTE: Esta consulta hace referencia a información previa.

Conversación anterior:
{contexto_conversacional}

Consulta nueva que debes responder: {consulta_para_rag}

INSTRUCCIÓN: Interpreta pronombres (su, él, ella, etc.) y referencias usando la conversación anterior. Si la consulta menciona "su relación con X", identifica quién es el sujeto desde el contexto previo y busca la relación específica entre ambas personas."""
                print(f"🔍 Consulta enriquecida con contexto conversacional (método legacy)")

            resultados_rag = ejecutar_consulta_rag_inteligente(consulta_enriquecida)
            resultados = {
                'respuesta_ia': resultados_rag.get('respuesta', 'Sin respuesta RAG'),
                'trazabilidad': resultados_rag.get('fuentes', []),
                'chunks': resultados_rag.get('chunks', []),
                'confianza': resultados_rag.get('confianza', 0.0),
                'tipo_ejecutado': 'RAG Semántico (Cualitativa)'
            }

        elif tipo_detectado == 'hibrida':
            # Consulta híbrida (BD + RAG) con división automática
            print(f"🔄 DASH DEBUG: Ejecutando consulta híbrida...")  # Debug

            # ✅ MEJORA: Reescribir query con contexto ANTES de enviar
            consulta_hibrida = consulta
            query_fue_reescrita = False
            consecutive_rewrites = 0
            prompt_contexto = ""

            if use_context_enabled and history_data and history_data.get('history'):
                # Intentar reescribir la query agregando entidades del contexto
                consulta_hibrida, query_fue_reescrita, entidades_agregadas, consecutive_rewrites = reescribir_query_con_contexto(
                    consulta, history_data
                )

            # Mantener compatibilidad con método legacy de contexto
            if contexto_conversacional and not query_fue_reescrita:
                # Solo usar método legacy si NO se reescribió la query
                ultima_consulta = history_data['history'][-1]['user_query'] if history_data and history_data.get('history') else ""

                # Crear un prompt con contexto que se agregará DESPUÉS de obtener resultados
                prompt_contexto = f"""
CONTEXTO de consulta anterior: {ultima_consulta}

INSTRUCCIÓN: La consulta actual hace referencia a información de la consulta anterior.
Interpreta pronombres (su, él, ella) usando ese contexto. Si menciona "su relación con X",
busca la relación entre la persona mencionada en la consulta anterior y X."""
                print(f"🔍 Consulta híbrida con contexto (método legacy) - Consulta original sin modificar: {consulta}")
                print(f"   Contexto previo que se usará: {ultima_consulta}")

            resultados_hibrida = ejecutar_consulta_hibrida(
                consulta_hibrida,  # Usar consulta reescrita si fue modificada
                nucs=nucs,
                departamento=departamento,
                municipio=municipio,
                tipo_documento=tipo_documento,
                despacho=despacho,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                contexto_conversacional=prompt_contexto if prompt_contexto else None
            )
            print(f"✅ DASH DEBUG: Híbrida completada, keys: {list(resultados_hibrida.keys())}")  # Debug
            if 'error' not in resultados_hibrida:
                # Mostrar división de consultas si se aplicó
                division_info = ""
                if resultados_hibrida.get('division_aplicada', False):
                    division_info = f"""**🔄 División Automática Aplicada:**
📊 Consulta BD: "{resultados_hibrida['bd'].get('consulta_original', '')}"
🧠 Consulta RAG: "{resultados_hibrida['rag'].get('consulta_original', '')}"

"""

                resultados = {
                    'respuesta_ia': f"""{division_info}**📊 Datos Estructurados (Base de Datos):**
{resultados_hibrida['bd'].get('respuesta_ia', 'Sin datos estructurados')}

**🧠 Análisis Contextual (RAG Semántico):**
{resultados_hibrida['rag'].get('respuesta', 'Sin análisis contextual')}""",
                    'trazabilidad': resultados_hibrida['rag'].get('fuentes', []),
                    'chunks': resultados_hibrida['rag'].get('chunks', []),
                    'confianza': resultados_hibrida['rag'].get('confianza', 0.0),
                    'tipo_ejecutado': 'Híbrida (BD + RAG)',
                    'victimas': resultados_hibrida['bd'].get('victimas', []),
                    'fuentes': resultados_hibrida['bd'].get('fuentes', [])
                }
                # Usar víctimas filtradas de la consulta híbrida si están disponibles
                if 'victimas' in resultados and resultados['victimas']:
                    victimas_filtradas = resultados['victimas']
                    total_victimas_filtradas = len(victimas_filtradas)
            else:
                resultados = {'respuesta_ia': resultados_hibrida.get('error', 'Error en consulta híbrida'), 'tipo_ejecutado': 'Error'}

    ia_parts = []
    entidades_graficables = []  # Para almacenar entidades del contexto

    # Valores por defecto para el botón y store
    btn_style = {"display": "none"}
    btn_content = "🌐 Ver Red de Relaciones"
    graph_context_data = None

    if resultados:
        # Mostrar tipo de consulta detectada con Badge más visible
        badge_config = {
            'bd': {"text": "📊 Base de Datos", "color": "primary"},
            'rag': {"text": "🧠 RAG Semántico", "color": "success"},
            'hibrida': {"text": "🔄 Consulta Híbrida", "color": "info"}
        }
        badge_info = badge_config.get(tipo_detectado, {"text": "❓ Desconocido", "color": "secondary"})

        ia_parts.append(html.Div([
            dbc.Badge(
                badge_info["text"],
                color=badge_info["color"],
                className="fs-5 mb-3",
                style={"padding": "10px 20px", "fontSize": "16px"}
            ),
            html.Span(
                f" → {resultados.get('tipo_ejecutado', 'Desconocido')}",
                style={"marginLeft": "10px", "color": "#666", "fontSize": "14px"}
            )
        ], style={"marginBottom": "20px"}))

        # Mostrar confianza si es RAG
        if 'confianza' in resultados and resultados['confianza'] > 0:
            confianza_color = "#4CAF50" if resultados['confianza'] > 0.7 else "#FF9800" if resultados['confianza'] > 0.4 else "#f44336"
            ia_parts.append(html.Div([
                html.Strong("🔍 Confianza de respuesta: "),
                html.Span(f"{resultados['confianza']:.1%}", style={"color": confianza_color, "fontWeight": "bold"})
            ], style={"marginBottom": "10px"}))

        # === NUEVO: EXTRACCIÓN DE ENTIDADES PARA GRAFO ===
        try:
            graph_context = extract_entities_from_query_result(resultados)

            # Decidir si mostrar botón basado en la consulta y tipo
            from core.graph.context_graph_builder import ContextGraphBuilder
            builder = ContextGraphBuilder()
            should_show = builder.should_auto_generate_graph(
                tipo_consulta=tipo_detectado,
                entity_count=graph_context['entity_count'],
                consulta_texto=consulta or ""
            )

            if should_show and graph_context['ready'] and graph_context['entity_count'] >= 2:
                entidades_graficables = graph_context['top_entities']

                # Actualizar estilo y contenido del botón
                btn_style = {
                    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "color": "white",
                    "border": "none",
                    "padding": "10px 20px",
                    "borderRadius": "8px",
                    "cursor": "pointer",
                    "marginBottom": "15px",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                    "transition": "all 0.3s",
                    "display": "block",
                    "width": "100%"
                }

                btn_content = [
                    html.Span("🌐 Ver Red de Relaciones ", style={"fontWeight": "bold"}),
                    html.Span(f"({graph_context['entity_count']} entidades)",
                             style={"fontSize": "11px", "opacity": "0.8"})
                ]

                # Guardar datos en store
                graph_context_data = json.dumps(graph_context)

                # Agregar info de entidades al panel IA
                ia_parts.append(html.Div(
                    f"📊 Entidades detectadas: {', '.join(entidades_graficables[:5])}{'...' if len(entidades_graficables) > 5 else ''}",
                    style={"fontSize": "11px", "color": "#666", "marginTop": "10px", "marginBottom": "10px",
                           "padding": "8px", "background": "#f0f0f0", "borderRadius": "4px"}
                ))
        except Exception as e:
            print(f"Error extrayendo entidades para grafo: {e}")

        ia_parts.append(dcc.Markdown(resultados.get("respuesta_ia", "Sin respuesta IA"), dangerously_allow_html=True))
        trazabilidad = resultados.get("trazabilidad", [])
        if trazabilidad:
            ia_parts.append(html.Hr())
            ia_parts.append(html.H6("Trazabilidad y Citas RAG:"))
            ia_parts.append(html.Ul([
                html.Li([
                    html.Span(
                        f"Fuente: {f.get('archivo', f.get('nombre_archivo', 'N/A'))} | NUC: {f.get('expediente_nuc', f.get('nuc', 'N/A'))} | Página: {f.get('pagina', 'N/A')} | Párrafo: {f.get('parrafo', 'N/A')} | Tipo: {f.get('tipo_documental', f.get('tipo_documento', 'N/A'))}",
                        style={"fontWeight": "bold"}
                    ),
                    html.Button("Ver texto completo", id={"type": "chunk-btn", "index": i}, n_clicks=0, style={"marginLeft": "8px", "fontSize": "12px"}),
                    html.Div(
                        (lambda t: t if len(t) <= 2000 else t[:2000] + "...")(
                            f.get('contenido') or f.get('texto_chunk') or f.get('resumen_chunk') or f.get('texto', '')
                        ),
                        id={"type": "chunk-text", "index": i},
                        style={"display": "none", "marginTop": "6px", "background": "#f3f3f3", "padding": "8px", "borderRadius": "6px"}
                    )
                ]) for i, f in enumerate(trazabilidad) if isinstance(f, dict)
            ]))
        ia = html.Div(ia_parts)
    else:
        ia = "Esperando consulta..."

    # Usar víctimas filtradas si están disponibles, de lo contrario usar paginación por defecto
    if victimas_filtradas is not None:
        victimas = victimas_filtradas
        total_victimas = total_victimas_filtradas
        # Para consultas filtradas, mostrar todos los resultados sin paginación
        # pero aplicar paginación manual si hay muchos resultados
        if len(victimas) > 20:
            start_idx = (page - 1) * 20
            end_idx = start_idx + 20
            victimas_pagina = victimas[start_idx:end_idx]
        else:
            victimas_pagina = victimas
    else:
        # Usar paginación por defecto cuando no hay filtros específicos
        victimas_pagina, total_victimas = obtener_victimas_paginadas(page=page)
        victimas = victimas_pagina

    # Renderiza la lista de víctimas como botones con mini-botón de red
    bd = html.Div([
        html.H5(f"Lista de víctimas (Página {page}):"),
        html.Div([
            html.Div([
                html.Button(
                    f"{v['nombre']} ({v['menciones']} menciones)",
                    id={"type": "victima-btn", "index": i},
                    n_clicks=0,
                    style={"margin": "4px", "width": "85%", "display": "inline-block"}
                ),
                html.Button(
                    "🌐",
                    id={"type": "victima-red-btn", "nombre": v['nombre']},
                    n_clicks=0,
                    title=f"Ver red de conexiones de {v['nombre']}",
                    style={
                        "margin": "4px",
                        "width": "12%",
                        "display": "inline-block",
                        "background": "#667eea",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "4px",
                        "cursor": "pointer",
                        "fontSize": "14px"
                    }
                )
            ], style={"marginBottom": "2px"}) for i, v in enumerate(victimas_pagina)
        ]) if victimas_pagina else html.Div([
            dbc.Alert([
                html.H4("ℹ️ Sin resultados", className="alert-heading text-info"),
                html.P("No se encontraron víctimas con los filtros aplicados."),
                html.Hr(),
                html.P("Sugerencias:", className="fw-bold mb-2"),
                html.Ul([
                    html.Li("Intenta con términos más generales"),
                    html.Li("Verifica los filtros de fecha, ubicación y tipo de documento"),
                    html.Li("Prueba una consulta híbrida o RAG para búsquedas semánticas"),
                    html.Li("Revisa la ortografía de nombres propios")
                ], className="mb-0")
            ], color="light", className="border-info")
        ]),
        dbc.ButtonGroup([
            dbc.Button("← Anterior", id="btn-pag-prev", color="secondary", size="lg", n_clicks=0),
            dbc.Input(
                id="input-pag",
                type="number",
                value=page,
                min=1,
                max=max((total_victimas//20)+1, 1),
                className="text-center fw-bold",
                style={'width': '100px', 'fontSize': '16px'}
            ),
            dbc.Button("Siguiente →", id="btn-pag-next", color="secondary", size="lg", n_clicks=0),
        ], className="mt-3 mb-2"),
        html.Div([
            html.Span(f"Total de víctimas: ", className="fw-bold"),
            html.Span(f"{total_victimas}", className="badge bg-primary", style={'fontSize': '14px'})
        ], className="mt-2")
    ])

    # Detecta si se hizo clic en alguna víctima
    victima_seleccionada = None
    if victima_clicks and any(victima_clicks):
        idx = [i for i, c in enumerate(victima_clicks) if c]
        if idx and len(victimas_pagina) > idx[0]:
            victima_seleccionada = victimas_pagina[idx[0]]["nombre"]

    # Muestra el detalle en el panel de fuentes
    if victima_seleccionada:
        from core.consultas import obtener_detalle_victima_completo, obtener_metadatos_documento
        detalle = obtener_detalle_victima_completo(victima_seleccionada)
        fuentes_bd, fuentes_rag = obtener_fuentes_victima(victima_seleccionada)
        
        # Crear tabs para cada documento como en Streamlit
        document_tabs = []
        for i, doc in enumerate(detalle["documentos"]):
            # Tab para cada documento individual
            doc_content = html.Div([
                # Análisis IA del documento
                html.H6("🤖 Análisis IA", style={"color": "#2E7D32", "marginTop": "15px"}),
                html.Div([
                    dcc.Markdown(doc.get('analisis_ia', 'Análisis IA no disponible para este documento'))
                ], style={"background": "#f8fff8", "padding": "10px", "borderRadius": "5px", "border": "1px solid #4CAF50"}),
                
                # Información Clave
                html.H6("📋 Información Clave", style={"color": "#1976D2", "marginTop": "15px"}),
                html.Div([
                    html.Div([
                        html.Strong("Tipo Documental: "), doc.get('tipo_documental', 'No especificado'),
                        html.Br(),
                        html.Strong("Fecha de Creación: "), doc.get('fecha', 'Sin fecha'),
                        html.Br(),
                        html.Strong("NUC: "), doc.get('nuc', 'N/A'),
                        html.Br(),
                        html.Strong("Serie: "), doc.get('serie', 'N/A'),
                        html.Br(),
                        html.Strong("Despacho: "), doc.get('despacho', 'N/A'),
                        html.Br(),
                        html.Strong("Código: "), doc.get('codigo', 'N/A')
                    ], style={"background": "#f0f8ff", "padding": "10px", "borderRadius": "5px"})
                ]),
                
                # Botones de acción como en Streamlit - versión simplificada
                html.H6("⚡ Información Adicional", style={"color": "#FF5722", "marginTop": "15px"}),
                
                # Texto completo expandible
                html.Details([
                    html.Summary("📄 Texto Completo (OCR)", 
                                style={"cursor": "pointer", "color": "#2196F3", "fontWeight": "bold"}),
                    html.Div([
                        html.Pre(doc.get('texto_extraido', 'Texto OCR no disponible'), 
                                style={
                                    "whiteSpace": "pre-wrap", 
                                    "maxHeight": "300px", 
                                    "overflow": "auto",
                                    "background": "#f5f5f5",
                                    "padding": "10px",
                                    "borderRadius": "5px",
                                    "fontSize": "12px",
                                    "marginTop": "10px"
                                })
                    ])
                ], style={"marginBottom": "10px"}),
                
                # Metadatos expandibles
                html.Details([
                    html.Summary("🔍 Metadatos Completos",
                                style={"cursor": "pointer", "color": "#4CAF50", "fontWeight": "bold"}),
                    html.Div([
                        html.Table([
                            # Información básica del archivo
                            html.Tr([
                                html.Td(html.Strong("Archivo: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('archivo', 'N/A'), style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Código: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('codigo', 'N/A'), style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Ruta: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('ruta', doc.get('ruta_documento', 'N/A')),
                                        style={"padding": "5px", "wordBreak": "break-all", "fontSize": "11px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Tamaño: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(f"{doc.get('tamano_mb', doc.get('tamaño_mb', 0))} MB", style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Hash SHA256: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('hash_sha256', 'N/A'),
                                        style={"padding": "5px", "wordBreak": "break-all", "fontSize": "11px"})
                            ]),
                            # Información documental
                            html.Tr([
                                html.Td(html.Strong("Fecha Creación: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(str(doc.get('fecha_creacion', 'N/A')), style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Cuaderno: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('cuaderno', 'N/A'), style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Folios: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(f"{doc.get('folio_inicial', 'N/A')} - {doc.get('folio_final', 'N/A')}", style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Serie: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('serie', 'N/A'), style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Subserie: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('subserie', 'N/A') if doc.get('subserie') else 'N/A', style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Páginas: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('paginas', doc.get('paginas_total', 'N/A')), style={"padding": "5px"})
                            ]),
                            # Información de procesamiento
                            html.Tr([
                                html.Td(html.Strong("Estado: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('estado', 'N/A'), style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Fecha Procesado: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(str(doc.get('fecha_procesado', 'N/A')), style={"padding": "5px"})
                            ]),
                            html.Tr([
                                html.Td(html.Strong("Versión Sistema: "), style={"padding": "5px", "verticalAlign": "top"}),
                                html.Td(doc.get('version_sistema', 'N/A'),
                                        style={"padding": "5px", "fontSize": "11px"})
                            ])
                        ], style={"width": "100%", "borderCollapse": "collapse", "border": "1px solid #ddd"})
                    ], style={
                        "background": "#f0fff0",
                        "padding": "10px",
                        "borderRadius": "5px",
                        "marginTop": "10px",
                        "maxHeight": "400px",
                        "overflow": "auto"
                    })
                ], style={"marginBottom": "10px"}),
                
                # Información del PDF
                html.Details([
                    html.Summary("📁 Información del PDF",
                                style={"cursor": "pointer", "color": "#FF9800", "fontWeight": "bold"}),
                    html.Div([
                        html.P(f"📂 Ruta: {doc.get('ruta', doc.get('ruta_documento', 'No disponible'))}"),
                        html.P(f"🆔 Código: {doc.get('codigo', 'N/A')}"),
                        html.P(f"📏 Tamaño: {doc.get('tamano_mb', 'No especificado')} MB"),
                        html.P(f"📄 Archivo: {doc.get('archivo', 'N/A')}"),

                        # Enlace de descarga
                        html.Div([
                            html.A([
                                html.Button([
                                    "📥 Descargar PDF",
                                    html.Br(),
                                    html.Small("(Archivo original)", style={"fontSize": "10px"})
                                ],
                                style={
                                    "backgroundColor": "#4CAF50",
                                    "color": "white",
                                    "border": "none",
                                    "padding": "10px 20px",
                                    "borderRadius": "5px",
                                    "cursor": "pointer",
                                    "fontSize": "14px",
                                    "fontWeight": "bold",
                                    "marginTop": "10px",
                                    "display": "block",
                                    "textAlign": "center"
                                })
                            ],
                            href=f"/download_pdf/{doc.get('archivo', '')}" if doc.get('archivo') else "#",
                            target="_blank",
                            style={"textDecoration": "none"}
                            )
                        ] if doc.get('archivo') else [
                            html.P("❌ Archivo no disponible para descarga",
                                  style={"color": "red", "fontStyle": "italic"})
                        ]),

                        html.P("📌 Nota: El archivo se descargará desde el servidor local",
                              style={"fontSize": "12px", "color": "#666", "marginTop": "10px"})
                    ], style={
                        "background": "#fff3e0",
                        "padding": "15px",
                        "borderRadius": "5px",
                        "marginTop": "10px"
                    })
                ])
            ])
            
            # Crear tab para este documento
            document_tabs.append(
                dcc.Tab(
                    label=f"📄 {doc.get('archivo', f'Doc {i+1}')}",
                    children=[doc_content],
                    value=f"doc_{i}"
                )
            )
        
        fuentes = html.Div([
            html.H5(f"🎯 Detalle de {detalle['nombre']}", style={"color": "#1976D2"}),
            html.P(f"📊 Menciones totales: {detalle['menciones']}", style={"fontSize": "16px", "fontWeight": "bold"}),
            
            # Análisis IA general de la víctima
            html.H6("🧠 Análisis IA General", style={"color": "#2E7D32", "marginTop": "15px"}),
            html.Div([
                dcc.Markdown(detalle["analisis_ia"])
            ], style={"background": "#f8fff8", "padding": "12px", "borderRadius": "8px", "border": "2px solid #4CAF50"}),
            
            html.Hr(),
            
            # Tabs para documentos individuales
            html.H6(f"📚 Documentos ({len(detalle['documentos'])} encontrados)", style={"color": "#1976D2", "marginTop": "15px"}),
            dcc.Tabs(
                children=document_tabs,
                value="doc_0" if document_tabs else None,
                style={"marginTop": "10px"}
            )
        ])
    else:
        fuentes = html.Ul([
            html.Li(f"Archivo: {f.get('archivo', 'N/A')} | NUC: {f.get('nuc', 'N/A')} | Despacho: {f.get('despacho', 'N/A')} | Tipo: {f.get('tipo_documental', 'N/A')} | Fecha: {f.get('fecha', 'N/A')}")
            for f in resultados.get("fuentes", [])
        ]) if resultados and resultados.get("fuentes") else "Fuentes/documentos aquí..."

    # === ACTUALIZAR HISTORIAL CONVERSACIONAL ===
    # Inicializar history_data si es None
    if history_data is None:
        history_data = {'history': [], 'max_turns': 10}

    # Si se ejecutó una consulta, agregar al historial
    if n_clicks and consulta and resultados:
        from datetime import datetime

        # Construir preview de la respuesta (dos versiones)
        response_preview_short = ""  # Para UI (300 chars)
        response_preview_full = ""   # Para GPT (1500 chars)

        if 'respuesta_ia' in resultados:
            response_preview_short = resultados['respuesta_ia'][:300]
            response_preview_full = resultados['respuesta_ia'][:1500]
        elif 'respuesta' in resultados:
            response_preview_short = str(resultados['respuesta'])[:300]
            response_preview_full = str(resultados['respuesta'])[:1500]
        elif 'total' in resultados:
            summary = f"Se encontraron {resultados['total']} resultados"
            response_preview_short = summary
            response_preview_full = summary

        # Crear entrada del historial
        history_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_query': consulta,
            'system_response_preview': response_preview_short,  # Para visualización en UI
            'system_response_full': response_preview_full,       # Para contexto GPT
            'query_type': tipo_detectado or 'desconocido',
            'results_summary': {
                'total': resultados.get('total', 0) if isinstance(resultados, dict) else 0,
                'tipo_ejecutado': resultados.get('tipo_ejecutado', 'N/A') if isinstance(resultados, dict) else 'N/A'
            },
            # ✅ Para tracking de reescrituras consecutivas RAG (evita drift semántico)
            'query_rewritten': locals().get('query_fue_reescrita', False)
        }

        # Agregar al historial (mantener solo max_turns)
        history_data['history'].append(history_entry)
        if len(history_data['history']) > history_data['max_turns']:
            history_data['history'] = history_data['history'][-history_data['max_turns']:]

        print(f"📝 Historial actualizado: {len(history_data['history'])} entradas")

    # Callback para mostrar texto completo al hacer clic en chunk
    # (Dash requiere un callback extra para esto, pero aquí se deja el markup listo)
    return ia, bd, fuentes, btn_style, btn_content, graph_context_data, history_data

# === FUNCIONES HELPER PARA DESCARGA DE PDFs ===

def convertir_ruta_bd_a_real(ruta_bd):
    """Convierte ruta de BD (/mnt/UP/...) a ruta real del sistema (/home/lab4/caso_UP/UP/...)"""
    if not ruta_bd or ruta_bd == 'N/A':
        return None

    # Reemplazar /mnt/UP/ por /home/lab4/caso_UP/UP/
    ruta_real = ruta_bd.replace('/mnt/UP/', '/home/lab4/caso_UP/UP/')

    # Verificar que el archivo existe
    if os.path.exists(ruta_real):
        return ruta_real

    return None

def obtener_ruta_pdf_real(doc):
    """Obtiene la ruta real del PDF desde los metadatos del documento"""
    # Intentar diferentes campos de ruta
    rutas_candidatas = [
        doc.get('ruta'),
        doc.get('ruta_documento'),
        doc.get('ruta_completa')
    ]

    for ruta in rutas_candidatas:
        if ruta and ruta != 'N/A':
            ruta_real = convertir_ruta_bd_a_real(ruta)
            if ruta_real:
                return ruta_real

    return None

# === ENDPOINT FLASK PARA DESCARGA DE PDFs ===

@app.server.route('/download_pdf/<path:archivo>')
def download_pdf(archivo):
    """Endpoint para descargar archivos PDF"""
    try:
        # Buscar el archivo en el sistema
        import glob

        # Buscar el archivo específico
        patron_busqueda = f"/home/lab4/caso_UP/**/{archivo}"
        archivos_encontrados = glob.glob(patron_busqueda, recursive=True)

        if archivos_encontrados:
            ruta_archivo = archivos_encontrados[0]  # Tomar el primero encontrado
            if os.path.exists(ruta_archivo):
                return send_file(ruta_archivo, as_attachment=True, download_name=archivo)

        # Si no se encuentra, error 404
        abort(404)

    except Exception as e:
        print(f"Error al descargar PDF {archivo}: {str(e)}")
        abort(500)

# === CALLBACKS PARA GRAFO 3D ===

# Callback 1: Los botones pattern-matching solo actualizan el Store
@app.callback(
    Output("victima-seleccionada-red", "data"),
    Input({"type": "victima-red-btn", "nombre": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def update_victima_store(n_clicks_list):
    """Actualiza el Store cuando se hace click en botón de víctima"""
    print(f"🔍🔍🔍 UPDATE STORE CALLED!")
    print(f"   n_clicks_list: {n_clicks_list}")

    triggered = callback_context.triggered[0]['prop_id']
    print(f"   Triggered: {triggered}")

    if not triggered or triggered == '.' or triggered == '':
        print(f"❌ UPDATE STORE - No trigger válido")
        raise PreventUpdate

    if 'victima-red-btn' in triggered:
        import json
        try:
            prop_dict = json.loads(triggered.split('.')[0])
            # Extraer el nombre directamente del ID del botón
            victima_nombre = prop_dict.get('nombre')

            if victima_nombre:
                print(f"✅ UPDATE STORE - Retornando nombre desde ID: {victima_nombre}")
                return victima_nombre
            else:
                print(f"❌ UPDATE STORE - No hay nombre en el ID del botón")
        except Exception as e:
            print(f"❌ UPDATE STORE - Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"❌ UPDATE STORE - No se pudo actualizar")
    raise PreventUpdate

# Callback 2: El Store controla la visibilidad del grafo
@app.callback(
    Output("graph-inline-container", "style"),
    [Input("btn-open-graph", "n_clicks"),
     Input("btn-ver-red-contextual", "n_clicks"),
     Input("btn-close-graph-inline", "n_clicks"),
     Input("victima-seleccionada-red", "data")],
    [State("graph-inline-container", "style")],
    prevent_initial_call=True
)
def toggle_modal_graph(n_clicks_manual, n_clicks_contextual, n_clicks_close, victima_nombre, current_style):
    """Abre/cierra la visualización inline del grafo"""
    triggered = callback_context.triggered[0]['prop_id']

    # Styles base (siempre incluir estos)
    base_style = {'marginTop': '20px', 'marginBottom': '20px'}

    # Styles para mostrar/ocultar
    style_visible = {**base_style}  # Sin display:none = visible
    style_hidden = {**base_style, 'display': 'none'}  # display:none = oculto

    # Determinar si está visible actualmente
    is_visible = current_style and current_style.get('display') != 'none'

    print(f"🔍 GRAPH INLINE TOGGLE - Triggered: {triggered}")
    print(f"   is_visible: {is_visible}")
    print(f"   victima_nombre: {victima_nombre}")
    print(f"   n_clicks_manual: {n_clicks_manual}")
    print(f"   n_clicks_contextual: {n_clicks_contextual}")
    print(f"   n_clicks_close: {n_clicks_close}")

    # Seguridad: Si no hay trigger válido, mantener oculto
    if not triggered or triggered == '.' or triggered == '':
        print(f"❌ GRAPH INLINE TOGGLE - No trigger válido, manteniendo oculto")
        raise PreventUpdate

    # Si el botón de cerrar fue clickeado, cerrar Y limpiar Store
    if 'btn-close-graph-inline' in triggered:
        print(f"✅ GRAPH INLINE TOGGLE - Cerrando grafo")
        # Nota: También deberíamos limpiar el Store, pero ese es otro Output
        return style_hidden

    # Si el Store cambió con un nombre de víctima, abrir el grafo
    if 'victima-seleccionada-red' in triggered:
        if victima_nombre:
            # Si hay nombre válido, abrir el grafo (incluso si ya está visible)
            # Esto permite actualizar el grafo cuando se hace clic en otra persona
            if not is_visible:
                print(f"✅ GRAPH INLINE TOGGLE - Abriendo grafo para {victima_nombre}")
            else:
                print(f"✅ GRAPH INLINE TOGGLE - Actualizando grafo para {victima_nombre}")
            return style_visible
        else:
            # Store cambió pero no hay nombre válido
            print(f"❌ GRAPH INLINE TOGGLE - Store cambió sin nombre")
            raise PreventUpdate

    # Si es el botón contextual, siempre abrir
    if 'btn-ver-red-contextual' in triggered:
        print(f"✅ GRAPH INLINE TOGGLE - Abriendo grafo contextual")
        return style_visible

    # Si es el botón manual, toggle
    if 'btn-open-graph' in triggered:
        if is_visible:
            print(f"✅ GRAPH INLINE TOGGLE - Cerrando grafo (manual)")
            return style_hidden
        else:
            print(f"✅ GRAPH INLINE TOGGLE - Abriendo grafo (manual)")
            return style_visible

    # Por defecto, no cambiar nada
    raise PreventUpdate


@app.callback(
    Output("collapse-graph-config", "is_open"),
    Input("toggle-graph-config", "n_clicks"),
    State("collapse-graph-config", "is_open"),
)
def toggle_graph_config(n_clicks, is_open):
    """Toggle configuración del grafo"""
    if n_clicks:
        return not is_open
    return is_open


@app.callback(
    [Output('graph-raw-data', 'data'),  # ✅ NUEVO: Guardar datos RAW (sin filtros) para filtrado reactivo
     Output('graph-stats', 'children')],
    [Input('graph-generate-btn', 'n_clicks'),
     Input('graph-search-btn', 'n_clicks'),
     Input('btn-ver-red-contextual', 'n_clicks'),
     Input('victima-seleccionada-red', 'data')],
    [State('graph-query-selector', 'value'),
     State('graph-entity-search', 'value'),
     State('graph-context-options', 'value'),
     State('graph-context-data', 'data')],
    prevent_initial_call=True
)
def generate_graph_visualization(n_clicks_predefined, n_clicks_search, n_clicks_contextual,
                                victima_nombre, query_key, entity_search, context_options, graph_context_json):
    """Genera datos RAW del grafo 3D (sin filtros). Los filtros se aplican en callback reactivo separado."""

    # Verificar que hay un trigger real
    triggered = callback_context.triggered[0]['prop_id']

    print(f"🔍 GRAPH CALLBACK - Triggered: {triggered}")
    print(f"   n_clicks_predefined: {n_clicks_predefined}")
    print(f"   n_clicks_search: {n_clicks_search}")
    print(f"   n_clicks_contextual: {n_clicks_contextual}")
    print(f"   victima_nombre: {victima_nombre}")

    # Si no hay trigger o es un trigger vacío, no hacer nada
    if not triggered or triggered == '.' or triggered == '':
        print(f"❌ GRAPH CALLBACK - No trigger válido")
        raise PreventUpdate

    # Si el trigger es el Store, validar que tenga un nombre válido
    if 'victima-seleccionada-red.data' in triggered:
        if not victima_nombre:
            print(f"❌ GRAPH CALLBACK - Store changed but no victima name")
            raise PreventUpdate
        # Si hay nombre válido, continuar para generar el grafo
        print(f"✅ GRAPH CALLBACK - Store changed with valid name: {victima_nombre}")

    # Si no hay clicks ni victima nombre, no hacer nada
    if not n_clicks_predefined and not n_clicks_search and not n_clicks_contextual and not victima_nombre:
        print(f"❌ GRAPH CALLBACK - No clicks and no victima")
        raise PreventUpdate

    try:
        from core.graph.visualizers.age_adapter import AGEGraphAdapter
        from core.graph.visualizers.plotly_3d import create_graph_figure

        # Crear adaptador
        adapter = AGEGraphAdapter()

        # MODO 2: Grafo individual de víctima (desde botón 🌐)
        if 'victima-seleccionada-red' in triggered and victima_nombre:
            print(f"🔍 GRAPH CALLBACK - Iniciando búsqueda de grafo para: {victima_nombre}")

            # ✅ USAR RELACIONES SEMÁNTICAS (victima-victimario, familiares, organizaciones, etc.)
            print(f"🔍 GRAPH CALLBACK - Usando relaciones semánticas desde tabla relaciones_extraidas...")
            try:
                data = adapter.query_by_entity_names_semantic(
                    nombres=[victima_nombre],
                    max_nodes=200  # ✅ Aumentado de 50 a 200 para capturar más relaciones
                )
                print(f"✅ GRAPH CALLBACK - Relaciones semánticas retornaron {len(data['nodes'])} nodos, {len(data['edges'])} relaciones")
            except Exception as e:
                print(f"❌ GRAPH CALLBACK - Relaciones semánticas fallaron: {e}")
                import traceback
                traceback.print_exc()
                error_msg = html.Div([
                    dbc.Alert(f"❌ Error al buscar datos: {str(e)}", color="danger")
                ])
                return None, error_msg

            if len(data['nodes']) == 0:
                error_msg = html.Div([
                    dbc.Alert(f"⚠️ No se encontraron conexiones para {victima_nombre}", color="warning")
                ])
                return None, error_msg

            title = f"Red Semántica de {victima_nombre}"
            description = f"Relaciones víctima-victimario, familiares, organizaciones"

        # MODO 1: Búsqueda contextual automática (desde consulta)
        elif 'btn-ver-red-contextual' in triggered:
            if not graph_context_json:
                error_msg = html.Div([
                    dbc.Alert("⚠️ No hay datos contextuales disponibles", color="warning")
                ])
                return None, error_msg

            # Parsear datos del contexto
            graph_context = json.loads(graph_context_json)
            nombres = graph_context['params']['nombres']

            if not nombres:
                error_msg = html.Div([
                    dbc.Alert("⚠️ No se encontraron entidades para graficar", color="warning")
                ])
                return None, error_msg

            # Intentar AGE primero, fallback a PostgreSQL
            try:
                data = adapter.query_by_entity_names(
                    nombres=nombres[:10],
                    include_neighborhood=True,
                    depth=1
                )
                # Si AGE no devuelve datos, usar fast query
                if len(data['nodes']) == 0:
                    data = adapter.query_by_entity_names_fast(
                        nombres=nombres[:15],
                        max_nodes=100
                    )
            except Exception:
                # Fallback a fast query
                data = adapter.query_by_entity_names_fast(
                    nombres=nombres[:15],
                    max_nodes=100
                )

            if len(data['nodes']) == 0:
                error_msg = html.Div([
                    dbc.Alert(f"⚠️ No se encontraron conexiones para: {', '.join(nombres[:3])}...", color="warning")
                ])
                return None, error_msg

            title = f"Red Contextual: {', '.join(nombres[:3])}{'...' if len(nombres) > 3 else ''}"
            description = f"Generada automáticamente desde la consulta ({graph_context['entity_count']} entidades detectadas)"

        # MODO 2: Consulta predefinida
        elif triggered == 'graph-generate-btn':
            # Obtener info de la query
            queries_info = {q['key']: q for q in adapter.get_available_queries()}
            query_info = queries_info.get(query_key, {})

            # Ejecutar consulta
            data = adapter.execute_predefined_query(query_key)

            title = query_info.get('name', 'Grafo AGE')
            description = query_info.get('description', '')

        # MODO 3: Búsqueda manual
        elif triggered == 'graph-search-btn':
            if not entity_search or not entity_search.strip():
                error_msg = html.Div([
                    dbc.Alert("⚠️ Por favor ingresa al menos un nombre de entidad", color="warning")
                ])
                return None, error_msg

            # Extraer nombres de la búsqueda (separados por coma)
            nombres = [n.strip() for n in entity_search.split(',') if n.strip()]

            # Determinar parámetros de búsqueda
            include_neighborhood = 'neighborhood' in (context_options or [])

            # Intentar AGE primero, fallback a PostgreSQL
            try:
                data = adapter.query_by_entity_names(
                    nombres=nombres[:10],
                    include_neighborhood=include_neighborhood,
                    depth=1 if include_neighborhood else 0
                )
                # Si AGE no devuelve datos, usar fast query
                if len(data['nodes']) == 0:
                    data = adapter.query_by_entity_names_fast(
                        nombres=nombres,
                        max_nodes=50
                    )
            except Exception:
                # Fallback a fast query
                data = adapter.query_by_entity_names_fast(
                    nombres=nombres,
                    max_nodes=50
                )

            if len(data['nodes']) == 0:
                error_msg = html.Div([
                    dbc.Alert(f"⚠️ No se encontraron entidades para: {', '.join(nombres)}", color="warning")
                ])
                return None, error_msg

            title = f"Búsqueda: {', '.join(nombres)}"
            description = f"Consulta contextual con {len(nombres)} entidad(es)"

        else:
            return None, None

        # ✅ Guardar metadata del grafo para el callback reactivo
        data['metadata'] = {
            'title': title,
            'description': description
        }

        # Generar estadísticas (se actualizarán en el callback reactivo después de filtrar)
        stats_html = html.Div([
            dbc.Alert([
                html.H5(f"📊 {title}", className="alert-heading"),
                html.P(description),
                html.Hr(),
                html.P([
                    html.Strong(f"Nodos: "),
                    html.Span(f"{len(data['nodes'])} "),
                    html.Strong(f"| Aristas: "),
                    html.Span(f"{len(data['edges'])}")
                ], className="mb-0")
            ], color="info")
        ])

        # ✅ RETORNAR DATOS RAW sin filtros (los filtros se aplicarán en callback reactivo)
        print(f"✅ GRAPH CALLBACK - Guardando datos RAW en Store")
        print(f"   - Nodos: {len(data['nodes'])}, Aristas: {len(data['edges'])}")
        return data, stats_html

    except Exception as e:
        print(f"❌ GRAPH CALLBACK - Error general: {e}")
        import traceback
        traceback.print_exc()
        error_msg = html.Div([
            dbc.Alert([
                html.H5("❌ Error generando visualización", className="alert-heading"),
                html.P(str(e)),
                html.Hr(),
                html.Pre(traceback.format_exc(), style={'fontSize': '10px'})
            ], color="danger")
        ])
        return None, error_msg


# ========================================
# ✅ CALLBACK PARA TOGGLE ENTRE PLOTLY Y G6
# ========================================
@app.callback(
    [Output('plotly-graph-container', 'style'),
     Output('g6-graph-container', 'style')],
    [Input('graph-viz-mode', 'value')],
    prevent_initial_call=False
)
def toggle_graph_visualization(viz_mode):
    """
    Controla qué visualización mostrar: Plotly 3D o G6.
    """
    if viz_mode == 'plotly':
        return {'display': 'block'}, {'display': 'none'}
    else:  # g6
        return {'display': 'none'}, {'display': 'block'}


# ========================================
# ✅ CALLBACK PARA GENERAR VISUALIZACIÓN G6
# ========================================
@app.callback(
    Output('graph-g6-iframe', 'src'),
    [Input('graph-raw-data', 'data'),
     Input('graph-node-filters', 'value'),
     Input('graph-relation-filters', 'value'),
     Input('graph-viz-mode', 'value')],
    prevent_initial_call=True
)
def generate_g6_visualization(raw_data, node_filters, relation_filters, viz_mode):
    """
    Genera visualización G6 cuando:
    - Se cargan nuevos datos RAW
    - Se cambian los filtros
    - Se selecciona modo G6
    """
    
    # Solo generar si está en modo G6
    if viz_mode != 'g6':
        raise PreventUpdate
    
    # Si no hay datos RAW, no hacer nada
    if not raw_data:
        print(f"⚠️ G6 CALLBACK - No hay datos RAW")
        raise PreventUpdate

    # Hacer una copia profunda de los datos
    import copy
    data = copy.deepcopy(raw_data)

    print(f"🔄 G6 CALLBACK - Iniciando generación G6")
    print(f"   - Datos originales: {len(data['nodes'])} nodos, {len(data['edges'])} aristas")

    # ✅ APLICAR FILTROS POR TIPO DE NODO (igual que Plotly)
    if node_filters is not None and len(node_filters) > 0:
        filtered_nodes = [node for node in data['nodes'] if node.get('type', 'persona') in node_filters]
        filtered_node_ids = {node['id'] for node in filtered_nodes}
        filtered_edges = [
            edge for edge in data['edges']
            if edge['source'] in filtered_node_ids and edge['target'] in filtered_node_ids
        ]
        data['nodes'] = filtered_nodes
        data['edges'] = filtered_edges

    # ✅ APLICAR FILTROS POR TIPO DE RELACIÓN (igual que Plotly)
    if relation_filters is not None and len(relation_filters) > 0:
        filtered_edges = [
            edge for edge in data['edges']
            if edge.get('type', edge.get('relation', '')).upper() in relation_filters
        ]
        # Eliminar nodos huérfanos
        connected_node_ids = set()
        for edge in filtered_edges:
            connected_node_ids.add(edge['source'])
            connected_node_ids.add(edge['target'])
        filtered_nodes = [
            node for node in data['nodes']
            if node['id'] in connected_node_ids
        ]
        data['nodes'] = filtered_nodes
        data['edges'] = filtered_edges

    # Si no quedan datos después de filtrar
    if len(data['nodes']) == 0 or len(data['edges']) == 0:
        print(f"⚠️ G6 CALLBACK - No hay datos después de filtrar")
        raise PreventUpdate

    print(f"🎨 G6 CALLBACK - Generando visualización G6...")
    print(f"   - Nodos filtrados: {len(data['nodes'])}, Aristas filtradas: {len(data['edges'])}")

    try:
        # Recuperar título desde metadata
        title = data.get('metadata', {}).get('title', 'Grafo de Conocimiento')
        
        # Generar visualización G6
        url = generar_grafo_g6_cached(data['nodes'], data['edges'], title)
        
        if url:
            print(f"✅ G6 CALLBACK - Visualización generada: {url}")
            return url
        else:
            print(f"❌ G6 CALLBACK - Error generando visualización")
            raise PreventUpdate

    except Exception as e:
        print(f"❌ G6 CALLBACK - Error: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate


# ========================================
# ✅ CALLBACK REACTIVO PARA FILTROS DE GRAFOS 3D (PLOTLY)
# ========================================
@app.callback(
    Output('graph-viewer', 'figure'),
    [Input('graph-raw-data', 'data'),
     Input('graph-node-filters', 'value'),
     Input('graph-relation-filters', 'value')],
    prevent_initial_call=True
)
def apply_graph_filters_reactive(raw_data, node_filters, relation_filters):
    """
    Aplica filtros de forma REACTIVA sobre los datos RAW del grafo.
    Este callback se ejecuta automáticamente cuando:
    - Se cargan nuevos datos RAW en el Store
    - El usuario cambia los filtros de nodos
    - El usuario cambia los filtros de relaciones

    NO requiere hacer clic en botones de búsqueda - es completamente reactivo.
    """

    # Si no hay datos RAW, no hacer nada
    if not raw_data:
        print(f"⚠️ REACTIVE FILTER CALLBACK - No hay datos RAW")
        raise PreventUpdate

    # Hacer una copia profunda de los datos para no mutar el original
    import copy
    data = copy.deepcopy(raw_data)

    print(f"🔄 REACTIVE FILTER CALLBACK - Iniciando filtrado reactivo")
    print(f"   - Datos originales: {len(data['nodes'])} nodos, {len(data['edges'])} aristas")
    print(f"   - Filtros de nodos: {node_filters}")
    print(f"   - Filtros de relaciones: {relation_filters}")

    # ✅ APLICAR FILTROS POR TIPO DE NODO
    if node_filters is not None and len(node_filters) > 0:
        print(f"🎯 REACTIVE FILTER - Aplicando filtros de nodos: {node_filters}")
        original_nodes = len(data['nodes'])
        original_edges = len(data['edges'])

        # Filtrar nodos según tipos seleccionados
        filtered_nodes = [node for node in data['nodes'] if node.get('type', 'persona') in node_filters]
        filtered_node_ids = {node['id'] for node in filtered_nodes}

        # Filtrar edges: solo mantener edges donde ambos nodos están en el filtro
        filtered_edges = [
            edge for edge in data['edges']
            if edge['source'] in filtered_node_ids and edge['target'] in filtered_node_ids
        ]

        data['nodes'] = filtered_nodes
        data['edges'] = filtered_edges

        print(f"   - Nodos: {original_nodes} → {len(filtered_nodes)}")
        print(f"   - Aristas: {original_edges} → {len(filtered_edges)}")

    # ✅ APLICAR FILTROS POR TIPO DE RELACIÓN
    if relation_filters is not None and len(relation_filters) > 0:
        print(f"🔗 REACTIVE FILTER - Aplicando filtros de relaciones: {relation_filters}")
        original_nodes = len(data['nodes'])
        original_edges = len(data['edges'])

        # Filtrar edges según tipos de relación seleccionados
        filtered_edges = [
            edge for edge in data['edges']
            if edge.get('type', edge.get('relation', '')).upper() in relation_filters
        ]

        # ✅ ELIMINAR NODOS HUÉRFANOS (que no tienen ninguna conexión)
        # Crear conjunto de nodos que tienen al menos una conexión
        connected_node_ids = set()
        for edge in filtered_edges:
            connected_node_ids.add(edge['source'])
            connected_node_ids.add(edge['target'])

        # Filtrar nodos: solo mantener los que tienen al menos una conexión
        filtered_nodes = [
            node for node in data['nodes']
            if node['id'] in connected_node_ids
        ]

        data['nodes'] = filtered_nodes
        data['edges'] = filtered_edges

        print(f"   - Nodos: {original_nodes} → {len(filtered_nodes)} (eliminados {original_nodes - len(filtered_nodes)} huérfanos)")
        print(f"   - Aristas: {original_edges} → {len(filtered_edges)}")

    # Si no quedan nodos o edges después de filtrar, retornar figura vacía con mensaje
    if len(data['nodes']) == 0 or len(data['edges']) == 0:
        print(f"⚠️ REACTIVE FILTER - No quedan datos después de filtrar")
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.update_layout(
            title="⚠️ No hay datos que mostrar con los filtros seleccionados",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template='plotly_white',
            height=600
        )
        return fig

    # Generar visualización con Plotly
    print(f"🔍 REACTIVE FILTER - Generando figura Plotly...")
    print(f"   - Nodos: {len(data['nodes'])}, Aristas: {len(data['edges'])}")

    try:
        from core.graph.visualizers.plotly_3d import create_graph_figure

        # Recuperar título desde metadata (si existe)
        title = data.get('metadata', {}).get('title', 'Grafo de Conocimiento')

        fig = create_graph_figure(data, title)
        print(f"✅ REACTIVE FILTER - Figura generada exitosamente")
        return fig

    except Exception as plot_error:
        print(f"❌ REACTIVE FILTER - Error en create_graph_figure: {plot_error}")
        import traceback
        traceback.print_exc()

        # Retornar figura vacía con mensaje de error
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.update_layout(
            title=f"❌ Error generando gráfico: {str(plot_error)}",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template='plotly_white',
            height=600
        )
        return fig


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8050)
