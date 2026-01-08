"""Callbacks para manejo del historial conversacional."""

from dash import Input, Output, State, html
import dash_bootstrap_components as dbc


def register_callbacks(app):
    """Registra todos los callbacks relacionados con el historial."""
    
    # Callback para toggle del historial
    @app.callback(
        Output("collapse-history", "is_open"),
        Input("btn-toggle-history", "n_clicks"),
        State("collapse-history", "is_open")
    )
    def toggle_history(n_clicks, is_open):
    def toggle_history(n_clicks, is_open):
        """Toggle la visibilidad del historial de conversación"""
        if n_clicks:
            return not is_open
        return is_open
    

    # Callback para limpiar historial
    @app.callback(
        Output("conversation-history", "data", allow_duplicate=True),
        Input("btn-clear-history", "n_clicks"),
        prevent_initial_call=True
    )
    def clear_history(n_clicks):
    def clear_history(n_clicks):
        """Limpia el historial de conversación"""
        if n_clicks:
            print("🗑️ Historial limpiado por el usuario")
            return {'history': [], 'max_turns': 10}
        return dash.no_update

    # Callback para actualizar display del slider
    @app.callback(
        Output("max-turns-display", "children"),
        Input("max-turns-slider", "value")
    )
    def update_slider_display(value):
    def update_slider_display(value):
        """Muestra el valor actual del slider"""
        return f"Recordar últimas {value} conversaciones"

    # Callback para actualizar límite de turnos
    @app.callback(
        Output("conversation-history", "data", allow_duplicate=True),
        Input("max-turns-slider", "value"),
        State("conversation-history", "data"),
        prevent_initial_call=True
    )
    def update_max_turns(new_max_turns, history_data):
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

    # Callback para actualizar visualización del historial
    @app.callback(
        Output("history-display", "children"),
        Input("conversation-history", "data")
    )
    def update_history_display(history_data):
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
