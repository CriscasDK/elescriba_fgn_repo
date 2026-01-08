"""Layout principal de la aplicación Dash."""

import dash_bootstrap_components as dbc
from dash import html, dcc

def create_layout():
    """
    Crea y retorna el layout completo de la aplicación Dash.
    
    Returns:
        dbc.Container: Layout principal de la aplicación
    """
    return dbc.Container([
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

            # Visualización con Plotly
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

