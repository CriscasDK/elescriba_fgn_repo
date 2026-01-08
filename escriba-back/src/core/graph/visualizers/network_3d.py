#!/usr/bin/env python3
"""
Graficador 3D de Redes - Módulo Independiente
Visualiza cualquier red usando el método "3D por niveles"

Acepta datos en formato estándar y genera visualización HTML independiente
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import time

@dataclass
class VisualizationConfig:
    """Configuración para la visualización"""
    title: str = "Red 3D"
    background_color: str = "#000511"
    level_spacing: float = 50.0
    node_size_multiplier: float = 2.0
    edge_opacity_base: float = 0.6
    enable_labels: bool = True
    enable_controls: bool = True

class Network3DVisualizer:
    """Graficador 3D independiente para cualquier tipo de red"""

    def __init__(self):
        self.default_colors = {
            # Colores por tipo de nodo (customizable)
            'default': '#888888',
            'primary': '#4ECDC4',
            'secondary': '#45B7D1',
            'accent': '#96CEB4',
            'warning': '#FF6B6B',
            'info': '#FFEAA7'
        }

        self.default_edge_colors = {
            # Colores por tipo de arista (customizable)
            'default': '#666666',
            'strong': '#4ECDC4',
            'medium': '#96CEB4',
            'weak': '#CCCCCC'
        }

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validar que los datos tengan el formato correcto"""
        required_keys = ['nodes', 'edges']

        if not all(key in data for key in required_keys):
            raise ValueError(f"Datos deben contener: {required_keys}")

        # Validar nodos
        for node in data['nodes']:
            if not all(key in node for key in ['id', 'name']):
                raise ValueError("Cada nodo debe tener 'id' y 'name'")

        # Validar aristas
        for edge in data['edges']:
            if not all(key in edge for key in ['source', 'target']):
                raise ValueError("Cada arista debe tener 'source' y 'target'")

        return True

    def prepare_layout(self, nodes: List[Dict], config: VisualizationConfig) -> List[Dict]:
        """Preparar layout 3D por niveles"""
        # Agrupar nodos por nivel/tipo
        nodes_by_level = {}

        for node in nodes:
            level = node.get('level', 0)
            if isinstance(level, str):
                # Si level es string (como tipo), convertir a número
                level = hash(level) % 10  # Máximo 10 niveles

            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)

        # Calcular posiciones
        positioned_nodes = []

        for level_num, level_nodes in nodes_by_level.items():
            z = level_num * config.level_spacing

            # Layout circular para cada nivel
            node_count = len(level_nodes)
            radius = max(30, node_count * 4)
            angle_step = (2 * 3.14159) / max(node_count, 1)

            for i, node in enumerate(level_nodes):
                angle = i * angle_step
                x = radius * (angle / 6.28)  # cos aproximado
                y = radius * ((angle + 1.57) / 6.28)  # sin aproximado

                # Calcular tamaño del nodo
                size = node.get('size', 5)
                if 'weight' in node:
                    size = max(3, min(15, node['weight'] * config.node_size_multiplier))

                positioned_node = {
                    **node,
                    'x': x,
                    'y': y,
                    'z': z,
                    'size': size,
                    'level': level_num
                }
                positioned_nodes.append(positioned_node)

        return positioned_nodes

    def generate_html(self, data: Dict[str, Any], output_file: str = "network_3d.html",
                     config: Optional[VisualizationConfig] = None) -> str:
        """Generar archivo HTML con visualización 3D embebida"""

        if config is None:
            config = VisualizationConfig()

        # Validar datos
        self.validate_data(data)

        # Preparar datos
        nodes = self.prepare_layout(data['nodes'], config)
        edges = data['edges']

        # Obtener colores personalizados o usar defaults
        node_colors = data.get('config', {}).get('node_colors', self.default_colors)
        edge_colors = data.get('config', {}).get('edge_colors', self.default_edge_colors)

        # Generar estadísticas
        stats = {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'levels': len(set(node.get('level', 0) for node in nodes)),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        html_content = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: {config.background_color};
            color: white;
        }}

        #container {{
            position: relative;
            width: 100vw;
            height: 100vh;
        }}

        #controls {{
            position: absolute;
            top: 15px;
            left: 15px;
            z-index: 100;
            background: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 20px;
            border-radius: 10px;
            min-width: 280px;
            max-height: 80vh;
            overflow-y: auto;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        #info {{
            position: absolute;
            bottom: 15px;
            left: 15px;
            z-index: 100;
            background: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 15px;
            border-radius: 10px;
            max-width: 350px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #4ECDC4;
            border-bottom: 2px solid #4ECDC4;
            padding-bottom: 8px;
        }}

        .section {{
            margin: 15px 0;
        }}

        .section h4 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #fff;
        }}

        .level-control {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            padding: 6px;
            border-radius: 6px;
            transition: background 0.3s;
        }}

        .level-control:hover {{
            background: rgba(255,255,255,0.1);
        }}

        .level-control input[type="checkbox"] {{
            margin-right: 10px;
        }}

        .level-indicator {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            margin-right: 10px;
        }}

        .control-button {{
            background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            margin: 3px;
            font-size: 12px;
            transition: all 0.3s;
        }}

        .control-button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(78, 205, 196, 0.3);
        }}

        .slider-control {{
            margin: 10px 0;
        }}

        .slider-control input[type="range"] {{
            width: 100%;
            margin: 8px 0;
        }}

        .slider-value {{
            font-size: 12px;
            color: #ccc;
        }}

        .stats {{
            font-size: 12px;
            color: #aaa;
            line-height: 1.4;
        }}

        .node-details {{
            background: rgba(78, 205, 196, 0.1);
            border-left: 3px solid #4ECDC4;
            padding: 12px;
            margin-top: 10px;
            border-radius: 6px;
        }}

        .edge-details {{
            background: rgba(255, 107, 107, 0.1);
            border-left: 3px solid #FF6B6B;
            padding: 12px;
            margin-top: 10px;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div id="container">
        {"" if not config.enable_controls else f'''
        <div id="controls">
            <div class="title">🎛️ {config.title}</div>

            <div class="section">
                <h4>📊 Estadísticas:</h4>
                <div class="stats">
                    Nodos: {stats['total_nodes']}<br>
                    Aristas: {stats['total_edges']}<br>
                    Niveles: {stats['levels']}
                </div>
            </div>

            <div class="section">
                <h4>🎯 Vista:</h4>
                <button class="control-button" onclick="resetCamera()">🎯 Centrar</button>
                <button class="control-button" onclick="toggleRotation()">🔄 Rotar</button>
                <button class="control-button" onclick="toggleLabels()">🏷️ Etiquetas</button>
                <button class="control-button" onclick="exportView()">💾 Exportar</button>
            </div>

            <div class="section">
                <h4>🔍 Filtros:</h4>
                <div class="slider-control">
                    <label>Tamaño mínimo:</label>
                    <input type="range" id="sizeFilter" min="0" max="15" value="0">
                    <div class="slider-value">Mínimo: <span id="sizeValue">0</span></div>
                </div>

                <div class="slider-control">
                    <label>Peso de aristas:</label>
                    <input type="range" id="weightFilter" min="0" max="1" step="0.1" value="0">
                    <div class="slider-value">Mínimo: <span id="weightValue">0%</span></div>
                </div>
            </div>

            <div class="section">
                <h4>📑 Niveles:</h4>
                <div id="level-controls"></div>
            </div>
        </div>
        '''}

        <div id="info">
            <div id="node-info">
                <strong>💡 Navegación:</strong><br>
                • Click en nodos/aristas para detalles<br>
                • Rueda del mouse para zoom<br>
                • Arrastra para rotar la vista
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/three@0.147.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.147.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        // DATOS EMBEBIDOS
        const networkData = {{
            nodes: {json.dumps(nodes, ensure_ascii=False)},
            edges: {json.dumps(edges, ensure_ascii=False)},
            config: {json.dumps({'node_colors': node_colors, 'edge_colors': edge_colors}, ensure_ascii=False)},
            stats: {json.dumps(stats, ensure_ascii=False)}
        }};

        console.log('Network3DVisualizer cargado:', networkData);

        // Variables globales
        let scene, camera, renderer, controls;
        let nodeObjects = new Map();
        let edgeObjects = [];
        let autoRotate = false;
        let showLabels = {str(config.enable_labels).lower()};
        let visibleLevels = new Set();

        // Configuración
        const CONFIG = {{
            levelSpacing: {config.level_spacing},
            nodeSizeMultiplier: {config.node_size_multiplier},
            edgeOpacityBase: {config.edge_opacity_base}
        }};

        function init() {{
            console.log('Iniciando visualizador 3D...');

            // Crear escena
            scene = new THREE.Scene();
            scene.background = new THREE.Color('{config.background_color}');

            // Cámara
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 2000);
            camera.position.set(100, 100, 100);

            // Renderizador
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.getElementById('container').appendChild(renderer.domElement);

            // Controles
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // Iluminación
            const ambientLight = new THREE.AmbientLight(0x404040, 0.7);
            scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
            directionalLight.position.set(100, 100, 100);
            scene.add(directionalLight);

            // Event listeners
            window.addEventListener('resize', onWindowResize, false);
            renderer.domElement.addEventListener('click', onMouseClick, false);

            // Construir red
            buildNetwork();
            if ({str(config.enable_controls).lower()}) {{
                setupControls();
            }}
            animate();

            console.log('Visualizador iniciado exitosamente');
        }}

        function buildNetwork() {{
            console.log('Construyendo red 3D...');

            // Crear nodos
            networkData.nodes.forEach(nodeData => {{
                const geometry = new THREE.SphereGeometry(nodeData.size, 16, 16);
                const color = getNodeColor(nodeData);
                const material = new THREE.MeshLambertMaterial({{
                    color: color,
                    transparent: true,
                    opacity: 0.9
                }});

                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(nodeData.x, nodeData.y, nodeData.z);
                mesh.userData = nodeData;
                mesh.castShadow = true;
                mesh.receiveShadow = true;

                scene.add(mesh);
                nodeObjects.set(nodeData.id, {{
                    mesh: mesh,
                    data: nodeData
                }});

                // Agregar nivel a set de niveles visibles
                visibleLevels.add(nodeData.level);
            }});

            // Crear aristas
            networkData.edges.forEach(edgeData => {{
                const sourceObj = nodeObjects.get(edgeData.source);
                const targetObj = nodeObjects.get(edgeData.target);

                if (sourceObj && targetObj) {{
                    const points = [
                        sourceObj.mesh.position.clone(),
                        targetObj.mesh.position.clone()
                    ];

                    const geometry = new THREE.BufferGeometry().setFromPoints(points);
                    const color = getEdgeColor(edgeData);
                    const material = new THREE.LineBasicMaterial({{
                        color: color,
                        transparent: true,
                        opacity: CONFIG.edgeOpacityBase
                    }});

                    const line = new THREE.Line(geometry, material);
                    line.userData = edgeData;
                    scene.add(line);
                    edgeObjects.push(line);
                }}
            }});

            console.log(`Red construida: ${{nodeObjects.size}} nodos, ${{edgeObjects.length}} aristas`);
        }}

        function getNodeColor(nodeData) {{
            const colors = networkData.config.node_colors;
            return colors[nodeData.type] || colors[nodeData.category] || colors.default || '#888888';
        }}

        function getEdgeColor(edgeData) {{
            const colors = networkData.config.edge_colors;
            return colors[edgeData.type] || colors[edgeData.category] || colors.default || '#666666';
        }}

        function setupControls() {{
            // Configurar controles de nivel
            const levelControlsDiv = document.getElementById('level-controls');
            if (!levelControlsDiv) return;

            const levels = [...visibleLevels].sort((a, b) => a - b);

            levels.forEach(level => {{
                const nodesInLevel = networkData.nodes.filter(n => n.level === level);
                const levelType = nodesInLevel[0]?.type || nodesInLevel[0]?.category || `Nivel ${{level}}`;
                const color = getNodeColor(nodesInLevel[0] || {{}});

                const div = document.createElement('div');
                div.className = 'level-control';
                div.innerHTML = `
                    <input type="checkbox" id="level-${{level}}" checked>
                    <div class="level-indicator" style="background-color: ${{color}}"></div>
                    <label for="level-${{level}}">${{levelType}} (${{nodesInLevel.length}})</label>
                `;

                const checkbox = div.querySelector('input');
                checkbox.addEventListener('change', () => {{
                    toggleLevel(level, checkbox.checked);
                }});

                levelControlsDiv.appendChild(div);
            }});

            // Configurar filtros
            const sizeFilter = document.getElementById('sizeFilter');
            const sizeValue = document.getElementById('sizeValue');
            if (sizeFilter && sizeValue) {{
                sizeFilter.addEventListener('input', () => {{
                    const minSize = parseFloat(sizeFilter.value);
                    sizeValue.textContent = minSize;
                    filterBySize(minSize);
                }});
            }}

            const weightFilter = document.getElementById('weightFilter');
            const weightValue = document.getElementById('weightValue');
            if (weightFilter && weightValue) {{
                weightFilter.addEventListener('input', () => {{
                    const minWeight = parseFloat(weightFilter.value);
                    weightValue.textContent = Math.round(minWeight * 100) + '%';
                    filterByWeight(minWeight);
                }});
            }}
        }}

        function toggleLevel(level, visible) {{
            nodeObjects.forEach((obj, nodeId) => {{
                if (obj.data.level === level) {{
                    obj.mesh.visible = visible;
                }}
            }});

            edgeObjects.forEach(edge => {{
                const sourceObj = nodeObjects.get(edge.userData.source);
                const targetObj = nodeObjects.get(edge.userData.target);

                if (sourceObj && targetObj) {{
                    const sourceVisible = sourceObj.mesh.visible;
                    const targetVisible = targetObj.mesh.visible;
                    edge.visible = sourceVisible && targetVisible;
                }}
            }});
        }}

        function filterBySize(minSize) {{
            nodeObjects.forEach((obj, nodeId) => {{
                obj.mesh.visible = obj.data.size >= minSize;
            }});
        }}

        function filterByWeight(minWeight) {{
            edgeObjects.forEach(edge => {{
                const weight = edge.userData.weight || edge.userData.strength || 0.5;
                edge.visible = weight >= minWeight;
            }});
        }}

        function onMouseClick(event) {{
            const mouse = new THREE.Vector2();
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

            const raycaster = new THREE.Raycaster();
            raycaster.setFromCamera(mouse, camera);

            // Verificar intersección con nodos
            const meshes = Array.from(nodeObjects.values()).map(obj => obj.mesh);
            const intersects = raycaster.intersectObjects(meshes);

            if (intersects.length > 0) {{
                const nodeData = intersects[0].object.userData;
                showNodeDetails(nodeData);
                return;
            }}

            // Verificar intersección con aristas
            const edgeIntersects = raycaster.intersectObjects(edgeObjects);
            if (edgeIntersects.length > 0) {{
                const edgeData = edgeIntersects[0].object.userData;
                showEdgeDetails(edgeData);
            }}
        }}

        function showNodeDetails(nodeData) {{
            const infoDiv = document.getElementById('node-info');
            infoDiv.innerHTML = `
                <div class="node-details">
                    <h4>📍 ${{nodeData.name}}</h4>
                    <p><strong>Tipo:</strong> ${{nodeData.type || nodeData.category || 'N/A'}}</p>
                    <p><strong>Nivel:</strong> ${{nodeData.level}}</p>
                    <p><strong>Tamaño:</strong> ${{nodeData.size}}</p>
                    ${{nodeData.description ? `<p><strong>Descripción:</strong> ${{nodeData.description}}</p>` : ''}}
                    ${{nodeData.metadata ? `<p><strong>Datos:</strong> ${{JSON.stringify(nodeData.metadata)}}</p>` : ''}}
                </div>
            `;
        }}

        function showEdgeDetails(edgeData) {{
            const sourceNode = nodeObjects.get(edgeData.source);
            const targetNode = nodeObjects.get(edgeData.target);

            const infoDiv = document.getElementById('node-info');
            infoDiv.innerHTML = `
                <div class="edge-details">
                    <h4>🔗 Conexión</h4>
                    <p><strong>Desde:</strong> ${{sourceNode.data.name}}</p>
                    <p><strong>Hacia:</strong> ${{targetNode.data.name}}</p>
                    <p><strong>Tipo:</strong> ${{edgeData.type || edgeData.category || 'N/A'}}</p>
                    <p><strong>Peso:</strong> ${{edgeData.weight || edgeData.strength || 'N/A'}}</p>
                    ${{edgeData.description ? `<p><strong>Descripción:</strong> ${{edgeData.description}}</p>` : ''}}
                </div>
            `;
        }}

        function animate() {{
            requestAnimationFrame(animate);

            if (autoRotate) {{
                scene.rotation.y += 0.005;
            }}

            controls.update();
            renderer.render(scene, camera);
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        // Funciones de control globales
        function resetCamera() {{
            camera.position.set(100, 100, 100);
            controls.reset();
        }}

        function toggleRotation() {{
            autoRotate = !autoRotate;
        }}

        function toggleLabels() {{
            showLabels = !showLabels;
            // Implementar toggle de etiquetas si es necesario
        }}

        function exportView() {{
            const imgData = renderer.domElement.toDataURL('image/png');
            const link = document.createElement('a');
            link.download = 'network_3d_view.png';
            link.href = imgData;
            link.click();
        }}

        // Inicializar cuando se carga la página
        window.addEventListener('load', init);
    </script>
</body>
</html>'''

        # Escribir archivo
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Visualización 3D generada: {output_file}")
        print(f"📊 Datos: {len(nodes)} nodos, {len(edges)} aristas")
        print(f"🔗 URL: file://{os.path.abspath(output_file)}")

        return output_file

def create_network_visualization(data: Dict[str, Any], title: str = "Red 3D",
                                output_file: str = "network_3d.html") -> str:
    """Función de conveniencia para crear visualización"""
    visualizer = Network3DVisualizer()
    config = VisualizationConfig(title=title)
    return visualizer.generate_html(data, output_file, config)

def main():
    """Función de prueba del módulo"""
    # Datos de ejemplo para demostrar el módulo independiente
    sample_data = {
        "nodes": [
            {"id": "1", "name": "Nodo Central", "type": "primary", "level": 0, "size": 10},
            {"id": "2", "name": "Nodo A", "type": "secondary", "level": 1, "size": 7},
            {"id": "3", "name": "Nodo B", "type": "secondary", "level": 1, "size": 8},
            {"id": "4", "name": "Nodo C", "type": "accent", "level": 2, "size": 6},
            {"id": "5", "name": "Nodo D", "type": "accent", "level": 2, "size": 5}
        ],
        "edges": [
            {"source": "1", "target": "2", "weight": 0.8, "type": "strong"},
            {"source": "1", "target": "3", "weight": 0.7, "type": "medium"},
            {"source": "2", "target": "4", "weight": 0.6, "type": "medium"},
            {"source": "3", "target": "5", "weight": 0.5, "type": "weak"}
        ]
    }

    print("🎨 Network3DVisualizer - Módulo Independiente")
    print("=" * 50)

    output_file = create_network_visualization(
        data=sample_data,
        title="Red de Ejemplo",
        output_file="modulo_example.html"
    )

    print(f"\n✅ Ejemplo generado: {output_file}")
    print("📝 Este módulo puede visualizar cualquier red que tenga el formato estándar")

if __name__ == "__main__":
    main()