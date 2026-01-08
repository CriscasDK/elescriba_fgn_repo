#!/usr/bin/env python3
"""
Script de prueba del visualizador 3D

Genera una visualización HTML de ejemplo desde el grafo AGE.
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph.visualizers.age_adapter import AGEGraphAdapter
from core.graph.visualizers.network_3d import Network3DVisualizer, VisualizationConfig


def main():
    """Prueba el adaptador y visualizador"""
    print("\n" + "="*60)
    print("🎨 TEST: Visualizador 3D desde AGE")
    print("="*60)

    # 1. Crear adaptador
    print("\n1️⃣  Creando adaptador AGE...")
    adapter = AGEGraphAdapter()

    # 2. Listar queries disponibles
    print("\n2️⃣  Consultas disponibles:")
    for query_info in adapter.get_available_queries():
        print(f"   • {query_info['key']}: {query_info['name']}")

    # 3. Ejecutar query
    query_key = 'top_connected'
    print(f"\n3️⃣  Ejecutando query: {query_key}")

    try:
        data = adapter.execute_predefined_query(query_key)

        print(f"\n   ✅ Datos obtenidos:")
        print(f"      Nodos: {len(data['nodes'])}")
        print(f"      Aristas: {len(data['edges'])}")

        if data['nodes']:
            tipos = {}
            for node in data['nodes']:
                t = node['type']
                tipos[t] = tipos.get(t, 0) + 1
            print(f"      Tipos de nodos:")
            for tipo, count in tipos.items():
                print(f"        - {tipo}: {count}")

        # 4. Generar visualización
        print(f"\n4️⃣  Generando visualización HTML...")
        visualizer = Network3DVisualizer()

        config = VisualizationConfig(
            title="Grafo AGE - Nodos Más Conectados",
            background_color="#000511",
            level_spacing=60.0,
            node_size_multiplier=2.5,
            enable_labels=True,
            enable_controls=True
        )

        output_file = "test_graph_3d.html"
        visualizer.generate_html(data, output_file, config)

        print(f"\n" + "="*60)
        print(f"✅ Visualización generada: {output_file}")
        print(f"🌐 Abrir en navegador: file://{Path(output_file).absolute()}")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
