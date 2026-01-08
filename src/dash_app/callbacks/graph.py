"""Callbacks para visualización del grafo 3D."""

from dash import Input, Output, State, html, callback_context, MATCH
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from core.graph.context_graph_builder import (
    load_age_graph,
    query_graph_age,
    build_3d_graph_from_age
)
import traceback


def register_callbacks(app):
    """Registra todos los callbacks relacionados con el grafo 3D."""
    
@    app.callback(
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
@    app.callback(
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


@    app.callback(
        Output("collapse-graph-config", "is_open"),
        Input("toggle-graph-config", "n_clicks"),
        State("collapse-graph-config", "is_open"),
)
    def toggle_graph_config(n_clicks, is_open):
        """Toggle configuración del grafo"""
        if n_clicks:
            return not is_open
        return is_open


@    app.callback(
        [Output('graph-viewer', 'figure'),
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
        """Genera la visualización del grafo 3D (predefinida, manual, contextual o víctima individual)"""

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
                        max_nodes=50
                    )
                    print(f"✅ GRAPH CALLBACK - Relaciones semánticas retornaron {len(data['nodes'])} nodos, {len(data['edges'])} relaciones")
                except Exception as e:
                    print(f"❌ GRAPH CALLBACK - Relaciones semánticas fallaron: {e}")
                    import traceback
                    traceback.print_exc()
                    error_msg = html.Div([
                        dbc.Alert(f"❌ Error al buscar datos: {str(e)}", color="danger")
                    ])
                    return {}, error_msg

                if len(data['nodes']) == 0:
                    error_msg = html.Div([
                        dbc.Alert(f"⚠️ No se encontraron conexiones para {victima_nombre}", color="warning")
                    ])
                    return {}, error_msg

                title = f"Red Semántica de {victima_nombre}"
                description = f"Relaciones víctima-victimario, familiares, organizaciones"

            # MODO 1: Búsqueda contextual automática (desde consulta)
            elif 'btn-ver-red-contextual' in triggered:
                if not graph_context_json:
                    error_msg = html.Div([
                        dbc.Alert("⚠️ No hay datos contextuales disponibles", color="warning")
                    ])
                    return "", error_msg

                # Parsear datos del contexto
                graph_context = json.loads(graph_context_json)
                nombres = graph_context['params']['nombres']

                if not nombres:
                    error_msg = html.Div([
                        dbc.Alert("⚠️ No se encontraron entidades para graficar", color="warning")
                    ])
                    return "", error_msg

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
                    return "", error_msg

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
                    return "", error_msg

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
                    return "", error_msg

                title = f"Búsqueda: {', '.join(nombres)}"
                description = f"Consulta contextual con {len(nombres)} entidad(es)"

            else:
                return "", ""

            # Generar estadísticas
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

            # Generar visualización con Plotly
            print(f"🔍 GRAPH CALLBACK - Generando figura Plotly...")
            print(f"   - Nodos: {len(data['nodes'])}, Aristas: {len(data['edges'])}")

            try:
                fig = create_graph_figure(data, title)
                print(f"✅ GRAPH CALLBACK - Figura generada exitosamente")
                print(f"✅ GRAPH CALLBACK - Retornando figura + stats")
                return fig, stats_html
            except Exception as plot_error:
                print(f"❌ GRAPH CALLBACK - Error en create_graph_figure: {plot_error}")
                import traceback
                traceback.print_exc()
                error_msg = html.Div([
                    dbc.Alert(f"❌ Error generando gráfico: {str(plot_error)}", color="danger")
                ])
                return {}, error_msg

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
            return {}, error_msg

