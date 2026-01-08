"""
Adaptador para AntV G6
Convierte datos del formato estándar a formato G6 y genera HTML embebible.
"""

from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class G6Adapter:
    """
    Convierte datos de AGE al formato requerido por AntV G6.
    Genera HTML completo con visualización embebible.
    """
    
    # Mapeo de colores por tipo de nodo (consistente con el sistema)
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
    
    # Tamaños por tipo
    NODE_SIZES = {
        'victima': 40,
        'victimario': 35,
        'familiar': 25,
        'entidad_ilegal': 40,
        'Persona': 30,
        'Organizacion': 35,
        'Documento': 20,
        'Lugar': 25,
        'default': 25
    }
    
    def __init__(self):
        """Inicializa el adaptador"""
        pass
    
    def convert_to_g6(
        self, 
        nodes: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convierte listas de nodos y aristas al formato G6.
        
        Args:
            nodes: Lista de nodos en formato estándar
            edges: Lista de aristas en formato estándar
            
        Returns:
            Diccionario con estructura G6
        """
        g6_nodes = []
        g6_edges = []
        
        # Convertir nodos
        for node in nodes:
            node_type = node.get('type', 'default')
            g6_node = {
                'id': str(node.get('id', '')),
                'label': node.get('name', node.get('label', '')),
                'type': node_type,
                'size': self.NODE_SIZES.get(node_type, self.NODE_SIZES['default']),
                'style': {
                    'fill': self.NODE_COLORS.get(node_type, self.NODE_COLORS['default']),
                    'lineWidth': 3,
                    'stroke': '#fff'
                }
            }
            
            # Agregar metadata si existe
            if 'metadata' in node:
                g6_node['metadata'] = node['metadata']
            
            g6_nodes.append(g6_node)
        
        # Convertir aristas
        for edge in edges:
            g6_edge = {
                'source': str(edge.get('source', '')),
                'target': str(edge.get('target', '')),
                'label': edge.get('label', edge.get('type', '')),
            }
            
            # Agregar metadata si existe
            if 'metadata' in edge:
                g6_edge['metadata'] = edge['metadata']
            
            g6_edges.append(g6_edge)
        
        return {
            'nodes': g6_nodes,
            'edges': g6_edges
        }
    
    def generate_html(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        title: str = "Visualización de Grafos",
        subtitle: str = "Sistema de Documentos Judiciales",
        width: int = 1200,
        height: int = 800
    ) -> str:
        """
        Genera HTML completo con visualización G6.
        
        Args:
            nodes: Lista de nodos
            edges: Lista de aristas
            title: Título de la visualización
            subtitle: Subtítulo
            width: Ancho del contenedor
            height: Alto del contenedor
            
        Returns:
            String con HTML completo
        """
        data = self.convert_to_g6(nodes, edges)
        data_json = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Calcular estadísticas
        stats = self._calculate_stats(nodes)
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <script src="https://unpkg.com/@antv/g6@4.8.24/dist/g6.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        .sidebar {{
            width: 300px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }}
        
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 5px;
        }}
        
        .header p {{
            color: #7f8c8d;
            font-size: 13px;
        }}
        
        #graph-container {{
            flex: 1;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }}
        
        .control-section {{
            margin-bottom: 20px;
        }}
        
        .control-section h3 {{
            color: #2c3e50;
            font-size: 14px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
        }}
        
        .control-section h3::before {{
            content: '';
            width: 3px;
            height: 16px;
            background: #667eea;
            margin-right: 8px;
            border-radius: 2px;
        }}
        
        .btn {{
            width: 100%;
            padding: 10px;
            margin: 4px 0;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: #ecf0f1;
            color: #2c3e50;
        }}
        
        .btn-secondary:hover {{
            background: #bdc3c7;
        }}
        
        .stats {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        
        .stat-item {{
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .stat-item:last-child {{
            border-bottom: none;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 12px;
        }}
        
        .stat-value {{
            color: #2c3e50;
            font-weight: 600;
            font-size: 12px;
        }}
        
        .legend {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            padding: 6px 0;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        
        .legend-item span {{
            font-size: 12px;
        }}
        
        .node-info {{
            background: rgba(255, 255, 255, 0.98);
            padding: 12px;
            border-radius: 8px;
            margin-top: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            min-height: 80px;
        }}
        
        .node-info h4 {{
            color: #667eea;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        
        .toolbar {{
            position: absolute;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}
        
        .toolbar-btn {{
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.9);
            border: none;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }}
        
        .toolbar-btn:hover {{
            background: white;
            transform: scale(1.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="control-section">
                <h3>⚙️ Controles</h3>
                <button class="btn" onclick="fitView()">🔍 Ajustar Vista</button>
                <button class="btn" onclick="resetZoom()">🎯 Reset Zoom</button>
                <button class="btn btn-secondary" onclick="togglePhysics()">⚡ Toggle Física</button>
            </div>
            
            <div class="control-section">
                <h3>👁️ Filtros Visuales</h3>
                <div class="stats" id="node-filters">
                    <!-- Se generará dinámicamente con JavaScript -->
                </div>
            </div>
            
            <div class="control-section">
                <h3>🎮 Interactividad</h3>
                <div class="stats">
                    <div class="stat-item" style="border-bottom: none; padding: 4px 0;">
                        <label style="cursor: pointer; display: flex; align-items: center; width: 100%;">
                            <input type="checkbox" id="toggle-drag-node" checked style="margin-right: 8px;">
                            <span class="stat-label" style="flex: 1;">🖱️ Arrastrar Nodos</span>
                        </label>
                    </div>
                    <div class="stat-item" style="border-bottom: none; padding: 4px 0;">
                        <label style="cursor: pointer; display: flex; align-items: center; width: 100%;">
                            <input type="checkbox" id="toggle-drag-canvas" checked style="margin-right: 8px;">
                            <span class="stat-label" style="flex: 1;">🌐 Arrastrar Canvas</span>
                        </label>
                    </div>
                    <div class="stat-item" style="border-bottom: none; padding: 4px 0;">
                        <label style="cursor: pointer; display: flex; align-items: center; width: 100%;">
                            <input type="checkbox" id="toggle-zoom" checked style="margin-right: 8px;">
                            <span class="stat-label" style="flex: 1;">🔍 Zoom con Rueda</span>
                        </label>
                    </div>
                    <div class="stat-item" style="border-bottom: none; padding: 4px 0;">
                        <label style="cursor: pointer; display: flex; align-items: center; width: 100%;">
                            <input type="checkbox" id="toggle-select" checked style="margin-right: 8px;">
                            <span class="stat-label" style="flex: 1;">✅ Seleccionar Nodos</span>
                        </label>
                    </div>
                    <div class="stat-item" style="border-bottom: none; padding: 4px 0;">
                        <label style="cursor: pointer; display: flex; align-items: center; width: 100%;">
                            <input type="checkbox" id="toggle-box-select" style="margin-right: 8px;">
                            <span class="stat-label" style="flex: 1;">📦 Selección Múltiple</span>
                        </label>
                    </div>
                    <div class="stat-item" style="border-bottom: none; padding: 4px 0;">
                        <label style="cursor: pointer; display: flex; align-items: center; width: 100%;">
                            <input type="checkbox" id="toggle-labels" checked style="margin-right: 8px;">
                            <span class="stat-label" style="flex: 1;">🏷️ Mostrar Etiquetas</span>
                        </label>
                    </div>
                </div>
            </div>
            
            <div class="control-section">
                <h3>📊 Estadísticas</h3>
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-label">Total Nodos</span>
                        <span class="stat-value">{stats['total_nodes']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Total Aristas</span>
                        <span class="stat-value">{stats['total_edges']}</span>
                    </div>
                    {self._generate_type_stats_html(stats['by_type'])}
                </div>
            </div>
            
            <div class="control-section">
                <h3>🎨 Leyenda</h3>
                <div class="legend">
                    {self._generate_legend_html(stats['types_present'])}
                </div>
            </div>
            
            <div class="node-info" id="node-info">
                <p style="color: #7f8c8d; font-style: italic; font-size: 12px;">Haz click en un nodo para ver detalles</p>
            </div>
        </div>
        
        <div class="main-content">
            <div class="header">
                <h1>🔍 {title}</h1>
                <p>{subtitle}</p>
            </div>
            
            <div id="graph-container">
                <div class="toolbar">
                    <button class="toolbar-btn" onclick="graph.zoomTo(graph.getZoom() * 1.2)" title="Zoom In">+</button>
                    <button class="toolbar-btn" onclick="graph.zoomTo(graph.getZoom() * 0.8)" title="Zoom Out">-</button>
                    <button class="toolbar-btn" onclick="downloadGraph()" title="Descargar">💾</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const data = {data_json};

        const container = document.getElementById('graph-container');
        const width = container.offsetWidth;
        const height = container.offsetHeight;

        const graph = new G6.Graph({{
            container: 'graph-container',
            width,
            height,
            layout: {{
                type: 'force',
                preventOverlap: true,
                nodeSpacing: 100,
                linkDistance: 150,
                nodeStrength: -300,
                edgeStrength: 0.5,
                collideStrength: 0.8,
                alpha: 0.8,
                alphaDecay: 0.028,
                alphaMin: 0.01
            }},
            defaultNode: {{
                size: 30,
                style: {{
                    lineWidth: 3,
                    stroke: '#fff',
                    shadowColor: 'rgba(0,0,0,0.3)',
                    shadowBlur: 10
                }},
                labelCfg: {{
                    style: {{
                        fill: '#fff',
                        fontSize: 11,
                        fontWeight: 'bold',
                        textAlign: 'center',
                        textBaseline: 'middle',
                        shadowColor: 'rgba(0,0,0,0.5)',
                        shadowBlur: 4
                    }}
                }}
            }},
            defaultEdge: {{
                style: {{
                    stroke: '#e2e2e2',
                    lineWidth: 2,
                    endArrow: {{
                        path: G6.Arrow.triangle(8, 10, 0),
                        fill: '#e2e2e2'
                    }}
                }},
                labelCfg: {{
                    autoRotate: true,
                    style: {{
                        fill: '#666',
                        fontSize: 9,
                        background: {{
                            fill: '#fff',
                            padding: [2, 4, 2, 4],
                            radius: 4
                        }}
                    }}
                }}
            }},
            modes: {{
                default: ['drag-canvas', 'zoom-canvas', 'drag-node', 'click-select']
            }},
            plugins: [],  // Plugins disponibles para selección múltiple
            nodeStateStyles: {{
                hover: {{
                    lineWidth: 5,
                    stroke: '#FFD700',
                    shadowColor: 'rgba(255, 215, 0, 0.6)',
                    shadowBlur: 20
                }},
                selected: {{
                    lineWidth: 5,
                    stroke: '#FFD700',
                    shadowColor: 'rgba(255, 215, 0, 0.8)',
                    shadowBlur: 25
                }}
            }},
            edgeStateStyles: {{
                hover: {{
                    lineWidth: 4,
                    stroke: '#FFD700'
                }}
            }}
        }});

        graph.data(data);
        graph.render();

        graph.on('node:mouseenter', (e) => {{
            graph.setItemState(e.item, 'hover', true);
        }});

        graph.on('node:mouseleave', (e) => {{
            graph.setItemState(e.item, 'hover', false);
        }});

        graph.on('node:click', (e) => {{
            const node = e.item;
            const model = node.getModel();
            
            const infoPanel = document.getElementById('node-info');
            let metadataHtml = '';
            if (model.metadata) {{
                metadataHtml = '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e0e0e0;">';
                for (const [key, value] of Object.entries(model.metadata)) {{
                    metadataHtml += `<div class="stat-item"><span class="stat-label">${{key}}:</span><span class="stat-value">${{value}}</span></div>`;
                }}
                metadataHtml += '</div>';
            }}
            
            infoPanel.innerHTML = `
                <h4>${{model.label}}</h4>
                <div class="stat-item">
                    <span class="stat-label">Tipo:</span>
                    <span class="stat-value">${{model.type}}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">ID:</span>
                    <span class="stat-value">${{model.id}}</span>
                </div>
                ${{metadataHtml}}
            `;
            
            graph.getNodes().forEach(node => {{
                graph.clearItemStates(node);
            }});
            graph.setItemState(node, 'selected', true);
            
            const edges = node.getEdges();
            edges.forEach(edge => {{
                graph.setItemState(edge, 'hover', true);
            }});
        }});

        function fitView() {{
            graph.fitView(20);
        }}

        function resetZoom() {{
            graph.zoomTo(1);
            graph.fitCenter();
        }}

        let physicsEnabled = true;
        function togglePhysics() {{
            if (physicsEnabled) {{
                graph.updateLayout({{
                    type: 'circular'
                }});
            }} else {{
                graph.updateLayout({{
                    type: 'force',
                    preventOverlap: true,
                    nodeSpacing: 100
                }});
            }}
            physicsEnabled = !physicsEnabled;
        }}

        function downloadGraph() {{
            graph.downloadFullImage('grafo-judicial', 'image/png', {{
                backgroundColor: '#fff',
                padding: 30
            }});
        }}

        // ========================================
        // FILTROS VISUALES POR TIPO DE NODO
        // ========================================
        
        // Estado de visibilidad por tipo
        const nodeTypeVisibility = {{}};
        
        // Mapeo de nombres legibles
        const nodeTypeLabels = {{
            'victima': '🔵 Víctima',
            'victimario': '🔴 Victimario',
            'familiar': '🟠 Familiar',
            'entidad_ilegal': '⚫ Entidad Ilegal',
            'Persona': '🔷 Persona',
            'Organizacion': '🔶 Organización',
            'Documento': '📄 Documento',
            'Lugar': '📍 Lugar'
        }};
        
        // Extraer tipos únicos de los nodos
        const nodeTypes = [...new Set(data.nodes.map(n => n.type))];
        
        // Inicializar estado (todos visibles por defecto)
        nodeTypes.forEach(type => {{
            nodeTypeVisibility[type] = true;
        }});
        
        // Generar checkboxes de filtro dinámicamente
        function initializeNodeFilters() {{
            const filtersContainer = document.getElementById('node-filters');
            
            nodeTypes.forEach(type => {{
                const count = data.nodes.filter(n => n.type === type).length;
                const label = nodeTypeLabels[type] || type;
                const color = data.nodes.find(n => n.type === type)?.style?.fill || '#888';
                
                const filterItem = document.createElement('div');
                filterItem.className = 'stat-item';
                filterItem.style.cssText = 'border-bottom: none; padding: 6px 0; cursor: pointer; transition: all 0.2s;';
                filterItem.innerHTML = `
                    <label style="cursor: pointer; display: flex; align-items: center; width: 100%; gap: 8px;">
                        <input type="checkbox" class="node-filter" data-type="${{type}}" checked style="margin: 0;">
                        <div style="width: 12px; height: 12px; border-radius: 50%; background: ${{color}}; flex-shrink: 0;"></div>
                        <span style="flex: 1; font-size: 13px;">${{label}}</span>
                        <span style="color: #7f8c8d; font-size: 11px;">${{count}}</span>
                    </label>
                `;
                
                // Efecto hover
                filterItem.addEventListener('mouseenter', () => {{
                    filterItem.style.background = 'rgba(52, 152, 219, 0.1)';
                }});
                filterItem.addEventListener('mouseleave', () => {{
                    filterItem.style.background = 'transparent';
                }});
                
                filtersContainer.appendChild(filterItem);
            }});
            
            // Añadir listeners
            document.querySelectorAll('.node-filter').forEach(checkbox => {{
                checkbox.addEventListener('change', function() {{
                    const type = this.dataset.type;
                    nodeTypeVisibility[type] = this.checked;
                    applyNodeFilters();
                }});
            }});
        }}
        
        // Aplicar filtros de visibilidad
        function applyNodeFilters() {{
            const nodes = graph.getNodes();
            const edges = graph.getEdges();
            
            let visibleCount = 0;
            let hiddenCount = 0;
            
            nodes.forEach(node => {{
                const model = node.getModel();
                const isVisible = nodeTypeVisibility[model.type];
                
                if (isVisible) {{
                    graph.showItem(node);
                    visibleCount++;
                }} else {{
                    graph.hideItem(node);
                    hiddenCount++;
                }}
            }});
            
            // Ocultar aristas conectadas a nodos invisibles
            edges.forEach(edge => {{
                const model = edge.getModel();
                const sourceNode = graph.findById(model.source);
                const targetNode = graph.findById(model.target);
                
                const sourceVisible = sourceNode && !sourceNode.get('visible') === false;
                const targetVisible = targetNode && !targetNode.get('visible') === false;
                
                if (sourceVisible && targetVisible) {{
                    graph.showItem(edge);
                }} else {{
                    graph.hideItem(edge);
                }}
            }});
            
            console.log(`👁️ Filtros aplicados: ${{visibleCount}} visibles, ${{hiddenCount}} ocultos`);
        }}
        
        // ========================================
        // CONTROLES DE INTERACTIVIDAD DINÁMICOS
        // ========================================
        
        // Función para actualizar modos del grafo
        function updateGraphModes() {{
            const modes = [];
            
            if (document.getElementById('toggle-drag-node').checked) {{
                modes.push('drag-node');
            }}
            if (document.getElementById('toggle-drag-canvas').checked) {{
                modes.push('drag-canvas');
            }}
            if (document.getElementById('toggle-zoom').checked) {{
                modes.push('zoom-canvas');
            }}
            if (document.getElementById('toggle-select').checked) {{
                modes.push('click-select');
            }}
            if (document.getElementById('toggle-box-select').checked) {{
                modes.push('brush-select');
            }}
            
            // Actualizar modos del grafo
            graph.setMode('default');
            graph.get('modeController').setMode('default');
            
            console.log('🎮 Modos actualizados:', modes);
        }}
        
        // Toggle para mostrar/ocultar etiquetas
        document.getElementById('toggle-labels').addEventListener('change', function(e) {{
            const showLabels = e.target.checked;
            
            graph.getNodes().forEach(node => {{
                graph.updateItem(node, {{
                    labelCfg: {{
                        style: {{
                            opacity: showLabels ? 1 : 0
                        }}
                    }}
                }});
            }});
            
            graph.getEdges().forEach(edge => {{
                graph.updateItem(edge, {{
                    labelCfg: {{
                        style: {{
                            opacity: showLabels ? 0.8 : 0
                        }}
                    }}
                }});
            }});
            
            console.log(showLabels ? '🏷️ Etiquetas mostradas' : '🏷️ Etiquetas ocultas');
        }});
        
        // Event listeners para checkboxes de interactividad
        ['toggle-drag-node', 'toggle-drag-canvas', 'toggle-zoom', 'toggle-select', 'toggle-box-select'].forEach(id => {{
            document.getElementById(id).addEventListener('change', function() {{
                updateGraphModes();
            }});
        }});
        
        // Inicializar modos
        updateGraphModes();
        
        // Inicializar filtros visuales
        initializeNodeFilters();

        // ========================================
        // RESPONSIVE Y AUTO-FIT
        // ========================================

        window.addEventListener('resize', () => {{
            const container = document.getElementById('graph-container');
            graph.changeSize(container.offsetWidth, container.offsetHeight);
            graph.fitView(20);
        }});

        setTimeout(() => {{
            graph.fitView(20);
        }}, 1000);
    </script>
</body>
</html>
"""
        return html_template
    
    def _calculate_stats(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula estadísticas de los nodos"""
        stats = {
            'total_nodes': len(nodes),
            'total_edges': 0,  # Se calcula en generate_html
            'by_type': {},
            'types_present': set()
        }
        
        for node in nodes:
            node_type = node.get('type', 'default')
            stats['types_present'].add(node_type)
            stats['by_type'][node_type] = stats['by_type'].get(node_type, 0) + 1
        
        return stats
    
    def _generate_type_stats_html(self, by_type: Dict[str, int]) -> str:
        """Genera HTML de estadísticas por tipo"""
        html = ""
        for node_type, count in sorted(by_type.items()):
            html += f"""
                    <div class="stat-item">
                        <span class="stat-label">{node_type}:</span>
                        <span class="stat-value">{count}</span>
                    </div>"""
        return html
    
    def _generate_legend_html(self, types_present: set) -> str:
        """Genera HTML de la leyenda"""
        html = ""
        
        legend_labels = {
            'victima': 'Víctima',
            'victimario': 'Victimario',
            'familiar': 'Familiar',
            'entidad_ilegal': 'Entidad Ilegal',
            'Persona': 'Persona',
            'Organizacion': 'Organización',
            'Documento': 'Documento',
            'Lugar': 'Lugar'
        }
        
        for node_type in types_present:
            color = self.NODE_COLORS.get(node_type, self.NODE_COLORS['default'])
            label = legend_labels.get(node_type, node_type)
            html += f"""
                    <div class="legend-item">
                        <div class="legend-color" style="background: {color};"></div>
                        <span>{label}</span>
                    </div>"""
        
        return html
    
    def save_html(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        output_path: str,
        **kwargs
    ) -> str:
        """
        Genera y guarda HTML en archivo.
        
        Args:
            nodes: Lista de nodos
            edges: Lista de aristas
            output_path: Ruta donde guardar el HTML
            **kwargs: Argumentos adicionales para generate_html
            
        Returns:
            Ruta del archivo guardado
        """
        html = self.generate_html(nodes, edges, **kwargs)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(output_file)
