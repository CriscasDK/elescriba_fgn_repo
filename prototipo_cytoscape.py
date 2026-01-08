"""
Prototipo de visualización con dash-cytoscape
Prueba básica de funcionalidad y performance
"""

import dash
from dash import html, dcc, Input, Output, State
import dash_cytoscape as cyto
from datetime import datetime
import sys
from pathlib import Path

# Agregar path para imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.graph.visualizers.cytoscape_adapter import CytoscapeAdapter


def create_sample_data():
    """
    Crea datos de prueba simulando el caso Oswaldo Olivo
    """
    nodes = [
        # Víctima central
        {
            'id': 'victima_1',
            'name': 'Oswaldo Olivo',
            'type': 'victima',
            'weight': 3.0,
            'metadata': {
                'edad': 45,
                'fecha': '2002-03-15',
                'lugar': 'Antioquia'
            }
        },
        # Victimarios
        {
            'id': 'victimario_1',
            'name': 'Grupo Armado X',
            'type': 'victimario',
            'weight': 2.5,
            'metadata': {
                'tipo': 'Organización ilegal'
            }
        },
        {
            'id': 'victimario_2',
            'name': 'Comandante Y',
            'type': 'victimario',
            'weight': 2.0
        },
        # Familiares
        {
            'id': 'familiar_1',
            'name': 'María Olivo',
            'type': 'familiar',
            'weight': 1.5,
            'metadata': {
                'parentesco': 'Esposa'
            }
        },
        {
            'id': 'familiar_2',
            'name': 'Pedro Olivo',
            'type': 'familiar',
            'weight': 1.5,
            'metadata': {
                'parentesco': 'Hijo'
            }
        },
        # Entidades ilegales
        {
            'id': 'entidad_1',
            'name': 'Frente Norte',
            'type': 'entidad_ilegal',
            'weight': 2.0
        },
        # Documentos
        {
            'id': 'doc_1',
            'name': 'Testimonio 2002-034',
            'type': 'Documento',
            'weight': 1.0
        },
        {
            'id': 'doc_2',
            'name': 'Acta Defunción',
            'type': 'Documento',
            'weight': 1.0
        },
        # Lugares
        {
            'id': 'lugar_1',
            'name': 'Antioquia',
            'type': 'Lugar',
            'weight': 1.5
        },
        {
            'id': 'lugar_2',
            'name': 'Vereda El Carmen',
            'type': 'Lugar',
            'weight': 1.0
        }
    ]
    
    edges = [
        # Relaciones víctima
        {'source': 'victimario_1', 'target': 'victima_1', 'type': 'victimizacion', 'weight': 3.0},
        {'source': 'victimario_2', 'target': 'victima_1', 'type': 'victimizacion', 'weight': 2.5},
        
        # Relaciones familiares
        {'source': 'victima_1', 'target': 'familiar_1', 'type': 'familiar', 'weight': 2.0},
        {'source': 'victima_1', 'target': 'familiar_2', 'type': 'familiar', 'weight': 2.0},
        
        # Relaciones victimarios
        {'source': 'victimario_2', 'target': 'victimario_1', 'type': 'pertenece', 'weight': 1.5},
        {'source': 'victimario_1', 'target': 'entidad_1', 'type': 'opera_en', 'weight': 2.0},
        
        # Relaciones documentos
        {'source': 'victima_1', 'target': 'doc_1', 'type': 'mencionado_en', 'weight': 1.0},
        {'source': 'victima_1', 'target': 'doc_2', 'type': 'mencionado_en', 'weight': 1.0},
        {'source': 'familiar_1', 'target': 'doc_1', 'type': 'mencionado_en', 'weight': 1.0},
        
        # Relaciones lugares
        {'source': 'victima_1', 'target': 'lugar_1', 'type': 'ubicado_en', 'weight': 1.5},
        {'source': 'victima_1', 'target': 'lugar_2', 'type': 'ubicado_en', 'weight': 1.0},
        {'source': 'entidad_1', 'target': 'lugar_1', 'type': 'opera_en', 'weight': 1.5}
    ]
    
    return nodes, edges


def create_app():
    """
    Crea la aplicación Dash con visualización Cytoscape
    """
    app = dash.Dash(__name__)
    adapter = CytoscapeAdapter()
    
    # Obtener datos de prueba
    nodes, edges = create_sample_data()
    elements = adapter.convert_to_cytoscape(nodes, edges)
    stylesheet = adapter.get_stylesheet()
    
    app.layout = html.Div([
        html.Div([
            html.H1('🔍 Prototipo Visualización Cytoscape', 
                   style={'textAlign': 'center', 'color': '#2c3e50'}),
            html.H3(f'Caso: Oswaldo Olivo - {len(nodes)} nodos, {len(edges)} relaciones',
                   style={'textAlign': 'center', 'color': '#7f8c8d'}),
        ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),
        
        html.Div([
            # Panel de control
            html.Div([
                html.H4('⚙️ Controles', style={'color': '#2c3e50'}),
                
                html.Label('Layout:', style={'fontWeight': 'bold', 'marginTop': '10px'}),
                dcc.Dropdown(
                    id='layout-dropdown',
                    options=[
                        {'label': '🌀 Force-Directed (COSE)', 'value': 'cose'},
                        {'label': '⭕ Circular', 'value': 'circle'},
                        {'label': '📊 Grid', 'value': 'grid'},
                        {'label': '🌳 Breadth-First', 'value': 'breadthfirst'},
                        {'label': '🎯 Concentric', 'value': 'concentric'}
                    ],
                    value='cose',
                    style={'marginBottom': '15px'}
                ),
                
                html.Button('🔄 Re-aplicar Layout', 
                           id='reset-layout-btn', 
                           n_clicks=0,
                           style={
                               'width': '100%',
                               'padding': '10px',
                               'backgroundColor': '#3498db',
                               'color': 'white',
                               'border': 'none',
                               'borderRadius': '5px',
                               'cursor': 'pointer',
                               'marginBottom': '15px'
                           }),
                
                html.Hr(),
                
                html.H5('📊 Estadísticas', style={'color': '#2c3e50'}),
                html.Div(id='stats-display', style={
                    'padding': '10px',
                    'backgroundColor': '#fff',
                    'borderRadius': '5px',
                    'border': '1px solid #ddd'
                }),
                
                html.Hr(),
                
                html.H5('🔍 Nodo Seleccionado', style={'color': '#2c3e50'}),
                html.Div(id='node-info', style={
                    'padding': '10px',
                    'backgroundColor': '#fff',
                    'borderRadius': '5px',
                    'border': '1px solid #ddd',
                    'minHeight': '100px'
                }),
                
                html.Hr(),
                
                html.H5('ℹ️ Leyenda', style={'color': '#2c3e50'}),
                html.Div([
                    html.Div([
                        html.Span('⭕', style={'color': '#4A90E2', 'fontSize': '20px'}),
                        html.Span(' Víctima', style={'marginLeft': '10px'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span('▲', style={'color': '#E74C3C', 'fontSize': '20px'}),
                        html.Span(' Victimario', style={'marginLeft': '10px'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span('◆', style={'color': '#F39C12', 'fontSize': '20px'}),
                        html.Span(' Familiar', style={'marginLeft': '10px'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span('⬢', style={'color': '#8B0000', 'fontSize': '20px'}),
                        html.Span(' Entidad Ilegal', style={'marginLeft': '10px'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span('▭', style={'color': '#FF6B6B', 'fontSize': '20px'}),
                        html.Span(' Documento', style={'marginLeft': '10px'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span('⬟', style={'color': '#96CEB4', 'fontSize': '20px'}),
                        html.Span(' Lugar', style={'marginLeft': '10px'})
                    ])
                ], style={
                    'padding': '10px',
                    'backgroundColor': '#fff',
                    'borderRadius': '5px',
                    'border': '1px solid #ddd'
                })
                
            ], style={
                'width': '25%',
                'padding': '20px',
                'backgroundColor': '#f8f9fa',
                'borderRight': '2px solid #dee2e6',
                'height': '800px',
                'overflowY': 'auto'
            }),
            
            # Visualización principal
            html.Div([
                cyto.Cytoscape(
                    id='cytoscape-graph',
                    elements=elements,
                    stylesheet=stylesheet,
                    layout=adapter.get_layout_config('cose'),
                    style={
                        'width': '100%',
                        'height': '800px',
                        'backgroundColor': '#ffffff',
                        'border': '1px solid #ddd'
                    },
                    # Opciones de interactividad
                    zoom=1.5,
                    pan={'x': 0, 'y': 0},
                    minZoom=0.5,
                    maxZoom=3,
                    boxSelectionEnabled=True,
                    autoungrabify=False
                )
            ], style={'width': '75%'})
            
        ], style={'display': 'flex'}),
        
        # Información de performance
        html.Div([
            html.Div(id='performance-info', style={
                'padding': '15px',
                'backgroundColor': '#d1ecf1',
                'borderRadius': '5px',
                'marginTop': '20px',
                'textAlign': 'center',
                'color': '#0c5460'
            })
        ], style={'padding': '20px'})
    ])
    
    # Callbacks
    @app.callback(
        Output('stats-display', 'children'),
        Input('cytoscape-graph', 'elements')
    )
    def update_stats(elements):
        """Actualiza las estadísticas del grafo"""
        if not elements:
            return "Sin datos"
        
        nodes = [e for e in elements if 'source' not in e['data']]
        edges = [e for e in elements if 'source' in e['data']]
        
        node_types = {}
        for node in nodes:
            node_type = node['data'].get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        stats_html = [
            html.P(f"📍 Total Nodos: {len(nodes)}", style={'marginBottom': '5px'}),
            html.P(f"🔗 Total Aristas: {len(edges)}", style={'marginBottom': '10px'}),
            html.Hr(style={'margin': '10px 0'}),
            html.P("Por Tipo:", style={'fontWeight': 'bold', 'marginBottom': '5px'})
        ]
        
        for node_type, count in sorted(node_types.items()):
            stats_html.append(
                html.P(f"• {node_type}: {count}", style={'marginBottom': '3px'})
            )
        
        return stats_html
    
    @app.callback(
        Output('node-info', 'children'),
        Input('cytoscape-graph', 'tapNodeData')
    )
    def display_node_info(data):
        """Muestra información del nodo seleccionado"""
        if not data:
            return html.P("Haz click en un nodo para ver detalles", 
                         style={'color': '#7f8c8d', 'fontStyle': 'italic'})
        
        info_html = [
            html.H6(data.get('label', 'Sin nombre'), 
                   style={'color': '#2c3e50', 'marginBottom': '10px'}),
            html.P([
                html.Strong("Tipo: "),
                html.Span(data.get('type', 'Desconocido'))
            ], style={'marginBottom': '5px'}),
            html.P([
                html.Strong("ID: "),
                html.Span(data.get('id', 'N/A'))
            ], style={'marginBottom': '5px'}),
            html.P([
                html.Strong("Peso: "),
                html.Span(f"{data.get('weight', 0):.2f}")
            ], style={'marginBottom': '10px'})
        ]
        
        # Agregar metadata si existe
        if 'metadata' in data:
            info_html.append(html.Hr())
            info_html.append(html.P("Metadata:", style={'fontWeight': 'bold', 'marginBottom': '5px'}))
            for key, value in data['metadata'].items():
                info_html.append(
                    html.P(f"• {key}: {value}", style={'marginBottom': '3px', 'fontSize': '12px'})
                )
        
        return info_html
    
    @app.callback(
        [Output('cytoscape-graph', 'layout'),
         Output('performance-info', 'children')],
        [Input('layout-dropdown', 'value'),
         Input('reset-layout-btn', 'n_clicks')],
        prevent_initial_call=False
    )
    def update_layout(layout_type, n_clicks):
        """Actualiza el layout del grafo"""
        layout_config = adapter.get_layout_config(layout_type)
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        layout_names = {
            'cose': 'Force-Directed (COSE)',
            'circle': 'Circular',
            'grid': 'Grid',
            'breadthfirst': 'Breadth-First',
            'concentric': 'Concentric'
        }
        
        perf_info = f"⚡ Layout '{layout_names.get(layout_type, layout_type)}' aplicado a las {timestamp}"
        
        return layout_config, perf_info
    
    return app


if __name__ == '__main__':
    print("="*70)
    print("🚀 INICIANDO PROTOTIPO DASH-CYTOSCAPE")
    print("="*70)
    print(f"⏰ Hora de inicio: {datetime.now().strftime('%H:%M:%S')}")
    print(f"🌐 URL: http://localhost:8051")
    print(f"📊 Datos de prueba: Caso Oswaldo Olivo")
    print("="*70)
    
    app = create_app()
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8051,
        dev_tools_hot_reload=True
    )
