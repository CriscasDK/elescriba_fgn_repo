"""
Adaptador para dash-cytoscape
Convierte datos del formato estándar a formato Cytoscape.js
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class CytoscapeNode:
    """Nodo en formato Cytoscape"""
    id: str
    label: str
    node_type: str
    size: float = 20.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CytoscapeEdge:
    """Arista en formato Cytoscape"""
    source: str
    target: str
    edge_type: str
    weight: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class CytoscapeAdapter:
    """
    Convierte datos de AGE al formato requerido por dash-cytoscape.
    
    Formato Cytoscape esperado:
    {
        "nodes": [
            {
                "data": {
                    "id": "node1",
                    "label": "Nombre",
                    "type": "persona"
                },
                "classes": "persona"
            }
        ],
        "edges": [
            {
                "data": {
                    "source": "node1",
                    "target": "node2",
                    "label": "relacion"
                }
            }
        ]
    }
    """
    
    # Mapeo de colores por tipo de nodo (igual que Plotly 3D)
    NODE_COLORS = {
        'victima': '#4A90E2',        # Azul
        'victimario': '#E74C3C',     # Rojo
        'familiar': '#F39C12',       # Naranja
        'entidad_ilegal': '#8B0000', # Rojo oscuro
        'Persona': '#4ECDC4',        # Turquesa
        'Organizacion': '#45B7D1',   # Azul
        'Documento': '#FF6B6B',      # Rojo claro
        'Lugar': '#96CEB4',          # Verde
        'default': '#888888'         # Gris
    }
    
    # Tamaños por tipo (proporcional a importancia)
    NODE_SIZES = {
        'victima': 30,
        'victimario': 35,
        'familiar': 25,
        'entidad_ilegal': 40,
        'Persona': 25,
        'Organizacion': 30,
        'Documento': 20,
        'Lugar': 25,
        'default': 20
    }
    
    def __init__(self):
        """Inicializa el adaptador"""
        pass
    
    def convert_to_cytoscape(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convierte listas de nodos y aristas al formato Cytoscape.
        
        Args:
            nodes: Lista de nodos en formato estándar
            edges: Lista de aristas en formato estándar
            
        Returns:
            Lista de elementos Cytoscape (nodos + aristas)
        """
        elements = []
        
        # Convertir nodos
        for node in nodes:
            node_type = node.get('type', 'default')
            cyto_node = {
                'data': {
                    'id': str(node.get('id', '')),
                    'label': node.get('name', node.get('label', '')),
                    'type': node_type,
                    'color': self.NODE_COLORS.get(node_type, self.NODE_COLORS['default']),
                    'size': self.NODE_SIZES.get(node_type, self.NODE_SIZES['default']),
                    'weight': node.get('weight', 1.0),
                },
                'classes': node_type
            }
            
            # Agregar metadata si existe
            if 'metadata' in node:
                cyto_node['data']['metadata'] = node['metadata']
            
            elements.append(cyto_node)
        
        # Convertir aristas
        for edge in edges:
            edge_type = edge.get('type', 'default')
            cyto_edge = {
                'data': {
                    'source': str(edge.get('source', '')),
                    'target': str(edge.get('target', '')),
                    'label': edge.get('label', edge_type),
                    'type': edge_type,
                    'weight': edge.get('weight', 1.0),
                }
            }
            
            # Agregar metadata si existe
            if 'metadata' in edge:
                cyto_edge['data']['metadata'] = edge['metadata']
            
            elements.append(cyto_edge)
        
        return elements
    
    def get_stylesheet(self) -> List[Dict[str, Any]]:
        """
        Retorna el stylesheet CSS para Cytoscape.
        Define estilos visuales para nodos y aristas.
        
        Returns:
            Lista de reglas de estilo Cytoscape
        """
        stylesheet = [
            # Estilo base para todos los nodos
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'background-color': 'data(color)',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    'font-size': '10px',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'text-outline-color': '#fff',
                    'text-outline-width': '2px',
                    'overlay-padding': '4px'
                }
            },
            # Estilo base para todas las aristas
            {
                'selector': 'edge',
                'style': {
                    'width': 2,
                    'line-color': '#999',
                    'target-arrow-color': '#999',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 0.6
                }
            },
            # Nodos seleccionados
            {
                'selector': 'node:selected',
                'style': {
                    'border-width': '3px',
                    'border-color': '#FFD700',
                    'overlay-color': '#FFD700',
                    'overlay-opacity': 0.3
                }
            },
            # Aristas conectadas al nodo seleccionado
            {
                'selector': 'edge:selected',
                'style': {
                    'width': 4,
                    'line-color': '#FFD700',
                    'target-arrow-color': '#FFD700',
                    'opacity': 1.0
                }
            },
            # Estilos específicos por tipo de nodo
            {
                'selector': '.victima',
                'style': {
                    'shape': 'ellipse',
                    'background-color': self.NODE_COLORS['victima']
                }
            },
            {
                'selector': '.victimario',
                'style': {
                    'shape': 'triangle',
                    'background-color': self.NODE_COLORS['victimario']
                }
            },
            {
                'selector': '.familiar',
                'style': {
                    'shape': 'diamond',
                    'background-color': self.NODE_COLORS['familiar']
                }
            },
            {
                'selector': '.entidad_ilegal',
                'style': {
                    'shape': 'octagon',
                    'background-color': self.NODE_COLORS['entidad_ilegal']
                }
            },
            {
                'selector': '.Organizacion',
                'style': {
                    'shape': 'rectangle',
                    'background-color': self.NODE_COLORS['Organizacion']
                }
            },
            {
                'selector': '.Documento',
                'style': {
                    'shape': 'round-rectangle',
                    'background-color': self.NODE_COLORS['Documento']
                }
            },
            {
                'selector': '.Lugar',
                'style': {
                    'shape': 'round-pentagon',
                    'background-color': self.NODE_COLORS['Lugar']
                }
            }
        ]
        
        return stylesheet
    
    def get_layout_config(self, layout_type: str = 'cose') -> Dict[str, Any]:
        """
        Retorna configuración para diferentes tipos de layout.
        
        Args:
            layout_type: Tipo de layout ('cose', 'circle', 'grid', 'breadthfirst', 'concentric')
            
        Returns:
            Diccionario de configuración del layout
        """
        layouts = {
            'cose': {
                'name': 'cose',
                'idealEdgeLength': 100,
                'nodeOverlap': 20,
                'refresh': 20,
                'fit': True,
                'padding': 30,
                'randomize': False,
                'componentSpacing': 100,
                'nodeRepulsion': 400000,
                'edgeElasticity': 100,
                'nestingFactor': 5,
                'gravity': 80,
                'numIter': 1000,
                'initialTemp': 200,
                'coolingFactor': 0.95,
                'minTemp': 1.0
            },
            'circle': {
                'name': 'circle',
                'fit': True,
                'padding': 30,
                'avoidOverlap': True,
                'radius': 200
            },
            'grid': {
                'name': 'grid',
                'fit': True,
                'padding': 30,
                'avoidOverlap': True,
                'rows': None,
                'cols': None
            },
            'breadthfirst': {
                'name': 'breadthfirst',
                'fit': True,
                'directed': True,
                'padding': 30,
                'circle': False,
                'spacingFactor': 1.5
            },
            'concentric': {
                'name': 'concentric',
                'fit': True,
                'padding': 30,
                'startAngle': 3.14159 / 2,
                'sweep': None,
                'clockwise': True,
                'equidistant': False,
                'minNodeSpacing': 10,
                'concentric': 'function(node) { return node.degree(); }',
                'levelWidth': 'function(nodes) { return 2; }'
            }
        }
        
        return layouts.get(layout_type, layouts['cose'])
