"""
Visualizador 3D de Grafos usando Plotly
Más ligero y compatible con Dash
"""

import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Any, Optional


class PlotlyGraphVisualizer:
    """
    Visualizador de grafos 3D usando Plotly.
    Optimizado para integración con Dash.
    """

    def __init__(self):
        # ✅ COLORES ESPECÍFICOS POR TIPO DE ENTIDAD
        self.default_colors = {
            # Tipos de nodos en grafos semánticos
            'victima': '#4A90E2',         # Azul - víctimas
            'victimario': '#E74C3C',      # Rojo intenso - perpetradores
            'familiar': '#F39C12',        # Naranja/amarillo - familiares
            'entidad_ilegal': '#8B0000',  # Rojo oscuro - grupos armados
            'entidad_estatal': '#7F8C8D', # Gris - instituciones estatales
            'persona': '#00D9E0',         # Turquesa - personas sin clasificar
            # Tipos legacy (para compatibilidad)
            'Documento': '#FF3B3B',
            'Persona': '#00D9E0',
            'Organizacion': '#2E86DE',
            'Lugar': '#10AC84',
            'default': '#95A5A6'
        }

        # ✅ SÍMBOLOS POR TIPO DE ENTIDAD
        self.entity_symbols = {
            'victima': 'circle',          # Círculo - víctimas
            'victimario': 'diamond',      # Diamante - perpetradores
            'familiar': 'square',         # Cuadrado - familiares
            'entidad_ilegal': 'x',        # X - grupos ilegales
            'entidad_estatal': 'square',  # Cuadrado - entidades estatales
            'persona': 'circle',          # Círculo - personas
            'default': 'circle'
        }

        # Colores para tipos de relaciones
        self.edge_colors = {
            'MENCIONADO_EN': '#4CAF50',           # Verde - menciones
            'VICTIMA_DE': '#F44336',              # Rojo - víctimas
            'PERPETRADOR': '#9C27B0',             # Morado - perpetradores
            'CO_OCURRE_CON': '#2196F3',           # Azul - co-ocurrencias
            'RELACIONADO_CON': '#FF9800',         # Naranja - relaciones genéricas
            'ORGANIZACION': '#FFC107',            # Amarillo - organizaciones
            'MIEMBRO_DE': '#00BCD4',              # Cyan - membresía
            'DOCUMENTO': '#795548',               # Marrón - documentos
            'default': '#555555'                  # Gris oscuro - default
        }

    def create_3d_graph(self, data: Dict[str, Any], title: str = "Red de Relaciones") -> go.Figure:
        """
        Crea visualización 3D del grafo usando Plotly.

        Args:
            data: Dict con nodes y edges
            title: Título del grafo

        Returns:
            go.Figure de Plotly
        """
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])

        if not nodes:
            # Grafo vacío
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para visualizar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="gray")
            )
            return fig

        # Crear layout de nodos (circular en 3D por niveles)
        node_positions = self._calculate_node_positions(nodes)

        # Crear trazas de aristas (ahora retorna lista)
        edge_traces = self._create_edge_trace(edges, node_positions)

        # Crear trazas de etiquetas de aristas (nombres de relaciones)
        edge_label_trace = self._create_edge_label_trace(edges, node_positions)

        # Crear trazas de nodos
        node_trace = self._create_node_trace(nodes, node_positions, data.get('config', {}))

        # Crear figura combinando todas las trazas
        # IMPORTANTE: Nodos al final para que se dibujen encima de las aristas
        all_traces = edge_traces + [edge_label_trace, node_trace]
        fig = go.Figure(data=all_traces)

        # Layout
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=18, color='#333')
            ),
            showlegend=True,  # Mostrar leyenda para tipos de relaciones
            legend=dict(
                x=1.02,
                y=0.5,
                xanchor='left',
                yanchor='middle',
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#ccc',
                borderwidth=1,
                font=dict(size=10)
            ),
            hovermode='closest',
            margin=dict(b=20, l=0, r=0, t=50),
            scene=dict(
                xaxis=dict(
                    showgrid=True,
                    gridcolor='#e0e0e0',
                    showticklabels=False,
                    title='',
                    showbackground=True,
                    backgroundcolor='#f8f9fa'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#e0e0e0',
                    showticklabels=False,
                    title='',
                    showbackground=True,
                    backgroundcolor='#f8f9fa'
                ),
                zaxis=dict(
                    showgrid=True,
                    gridcolor='#e0e0e0',
                    showticklabels=False,
                    title='',
                    showbackground=True,
                    backgroundcolor='#f8f9fa'
                ),
                bgcolor='#ffffff',
                camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.2)  # Vista más alejada y ligeramente superior
                )
            ),
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff',
            height=900
        )

        return fig

    def _calculate_node_positions(self, nodes: List[Dict]) -> Dict[str, tuple]:
        """Calcula posiciones 3D para los nodos"""
        positions = {}

        # Agrupar por nivel
        nodes_by_level = {}
        for node in nodes:
            level = node.get('level', 0)
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # Posicionar cada nivel en un círculo
        for level, level_nodes in nodes_by_level.items():
            count = len(level_nodes)
            radius = max(10, count * 1.5)  # ✅ MODO ESPACIADO: Radio aumentado para más aire
            z = level * 15  # ✅ MODO ESPACIADO: Separación vertical aumentada (8→15)

            for i, node in enumerate(level_nodes):
                angle = (2 * np.pi * i) / count
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                positions[node['id']] = (x, y, z)

        return positions

    def _create_edge_trace(self, edges: List[Dict], positions: Dict[str, tuple]) -> List[go.Scatter3d]:
        """Crea trazas de aristas (una por cada tipo de relación para colores distintos)"""

        # Agrupar edges por tipo
        edges_by_type = {}
        for edge in edges:
            rel_type = edge.get('type', edge.get('relation', 'default')).upper()
            if rel_type not in edges_by_type:
                edges_by_type[rel_type] = []
            edges_by_type[rel_type].append(edge)

        # Crear una traza por tipo de relación
        edge_traces = []

        for rel_type, type_edges in edges_by_type.items():
            edge_x = []
            edge_y = []
            edge_z = []

            for edge in type_edges:
                source_id = edge['source']
                target_id = edge['target']

                if source_id in positions and target_id in positions:
                    x0, y0, z0 = positions[source_id]
                    x1, y1, z1 = positions[target_id]

                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    edge_z.extend([z0, z1, None])

            # Color según tipo de relación
            edge_color = self.edge_colors.get(rel_type, self.edge_colors['default'])

            edge_trace = go.Scatter3d(
                x=edge_x, y=edge_y, z=edge_z,
                mode='lines',
                line=dict(color=edge_color, width=1, dash='solid'),  # ✅ MODO MINIMALISTA: width 2→1
                name=rel_type,  # Para leyenda
                hoverinfo='name',
                showlegend=True,
                legendgroup=rel_type,
                opacity=0.35  # ✅ MODO MINIMALISTA: opacity 0.6→0.35 (más transparentes)
            )

            edge_traces.append(edge_trace)

        return edge_traces if edge_traces else [go.Scatter3d(x=[], y=[], z=[])]

    def _create_edge_label_trace(self, edges: List[Dict], positions: Dict[str, tuple]) -> go.Scatter3d:
        """Crea traza de etiquetas de aristas (nombres de relaciones)"""
        edge_label_x = []
        edge_label_y = []
        edge_label_z = []
        edge_label_text = []
        edge_hover_text = []

        for edge in edges:
            source_id = edge['source']
            target_id = edge['target']

            if source_id in positions and target_id in positions:
                x0, y0, z0 = positions[source_id]
                x1, y1, z1 = positions[target_id]

                # Posición del label en el punto medio de la arista
                mid_x = (x0 + x1) / 2
                mid_y = (y0 + y1) / 2
                mid_z = (z0 + z1) / 2

                edge_label_x.append(mid_x)
                edge_label_y.append(mid_y)
                edge_label_z.append(mid_z)

                # Texto del label (tipo de relación)
                relation_type = edge.get('type', edge.get('relation', 'RELACIONADO'))
                edge_label_text.append(relation_type)

                # Hover text con más detalles
                hover = f"<b>{relation_type}</b><br>"
                hover += f"De: {edge.get('source_name', source_id)}<br>"
                hover += f"A: {edge.get('target_name', target_id)}"
                if 'weight' in edge:
                    hover += f"<br>Peso: {edge['weight']}"
                edge_hover_text.append(hover)

        edge_label_trace = go.Scatter3d(
            x=edge_label_x, y=edge_label_y, z=edge_label_z,
            mode='markers',  # ✅ MODO MINIMALISTA: Cambiar a markers invisibles para mantener hover
            marker=dict(size=0.1, color='rgba(0,0,0,0)'),  # ✅ Markers invisibles
            text=edge_label_text,
            textposition='middle center',
            textfont=dict(size=7, color='#666', family='Arial'),
            hovertext=edge_hover_text,
            hoverinfo='text',  # ✅ Hover sigue funcionando
            showlegend=False,
            opacity=0  # ✅ MODO MINIMALISTA: Oculto por defecto (info solo en hover)
        )

        return edge_label_trace

    def _create_node_trace(self, nodes: List[Dict], positions: Dict[str, tuple],
                          config: Dict) -> go.Scatter3d:
        """Crea traza de nodos"""
        node_x = []
        node_y = []
        node_z = []
        node_text = []  # Hover text
        node_labels = []  # ✅ MODO MINIMALISTA: Labels visibles (solo importantes)
        node_colors = []
        node_sizes = []
        node_symbols = []

        node_color_map = config.get('node_colors', self.default_colors)

        for node in nodes:
            if node['id'] not in positions:
                continue

            x, y, z = positions[node['id']]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)

            # Texto hover con tipo de entidad traducido
            tipo_labels = {
                'victima': '🔵 Víctima',
                'victimario': '🔴 Victimario',
                'familiar': '🟡 Familiar',
                'entidad_ilegal': '❌ Entidad Ilegal',
                'entidad_estatal': '🏛️ Entidad Estatal',
                'persona': '👤 Persona'
            }
            tipo_display = tipo_labels.get(node.get('type', 'persona'), node.get('type', 'N/A'))

            hover_text = f"<b>{node['name']}</b><br>"
            hover_text += f"Tipo: {tipo_display}<br>"
            hover_text += f"Nivel: {node.get('level', 0)}<br>"

            if 'metadata' in node and node['metadata']:
                metadata = node['metadata']
                if 'documentos' in metadata:
                    docs = metadata['documentos']
                    if isinstance(docs, list):
                        hover_text += f"Documentos: {len(docs)}"

            node_text.append(hover_text)

            # ✅ MODO MINIMALISTA: Solo mostrar nombre si es importante
            # Importante = nivel 0 (víctima principal) O peso > 3 O victimario/entidad ilegal
            node_weight = node.get('weight', 1)
            node_level = node.get('level', 0)
            node_type = node.get('type', 'default')

            is_important = (
                node_level == 0 or  # Víctima principal
                node_weight > 3 or  # Mencionado en 3+ documentos
                node_type in ['victimario', 'entidad_ilegal']  # Tipos importantes siempre
            )

            node_labels.append(node['name'] if is_important else '')  # Nombre o vacío

            # Color y símbolo según tipo
            color = node_color_map.get(node_type, node_color_map.get('default', '#888888'))
            node_colors.append(color)

            # ✅ SÍMBOLO según tipo de entidad
            symbol = self.entity_symbols.get(node_type, self.entity_symbols.get('default', 'circle'))
            node_symbols.append(symbol)

            # Tamaño basado en importancia (peso)
            base_size = node.get('size', 20)
            # ✅ Tamaño proporcional a peso (más menciones = más grande)
            size = max(base_size * 2.5 + (node_weight * 3), 25)  # Mínimo 25
            node_sizes.append(size)

        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                symbol=node_symbols,  # ✅ Símbolos por tipo de entidad
                line=dict(color='rgba(255,255,255,0.8)', width=2),  # Borde blanco semi-transparente
                opacity=0.95  # Opacidad alta para visibilidad
            ),
            text=node_labels,  # ✅ MODO MINIMALISTA: Solo nombres importantes
            textposition='top center',
            textfont=dict(size=10, color='#000', family='Arial Black'),  # ✅ Tamaño reducido 11→10
            hovertext=node_text,
            hoverinfo='text',
            showlegend=False  # Evitar duplicados en leyenda
        )

        return node_trace


def create_graph_figure(data: Dict[str, Any], title: str = "Red de Relaciones") -> go.Figure:
    """
    Función de conveniencia para crear figura de grafo.

    Args:
        data: Datos del grafo (nodes, edges, config)
        title: Título

    Returns:
        Figura de Plotly lista para Dash
    """
    visualizer = PlotlyGraphVisualizer()
    return visualizer.create_3d_graph(data, title)


if __name__ == "__main__":
    # Test básico
    print("🎨 Plotly Graph Visualizer - Test")
    print("=" * 60)

    # Datos de ejemplo
    test_data = {
        "nodes": [
            {"id": "1", "name": "Nodo A", "type": "Persona", "level": 0, "size": 10},
            {"id": "2", "name": "Nodo B", "type": "Persona", "level": 0, "size": 8},
            {"id": "3", "name": "Doc 1", "type": "Documento", "level": 1, "size": 6},
        ],
        "edges": [
            {"source": "1", "target": "3", "type": "MENCIONADO_EN"},
            {"source": "2", "target": "3", "type": "MENCIONADO_EN"},
        ],
        "config": {
            "node_colors": {
                "Persona": "#4ECDC4",
                "Documento": "#FF6B6B"
            }
        }
    }

    fig = create_graph_figure(test_data, "Grafo de Prueba")
    print(f"✅ Figura creada: {type(fig)}")
    print(f"📊 Nodos: {len(test_data['nodes'])}, Aristas: {len(test_data['edges'])}")
