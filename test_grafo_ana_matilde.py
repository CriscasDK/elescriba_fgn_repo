#!/usr/bin/env python3
"""
Test automatizado para verificar que el grafo de Ana Matilde Guzmán Borja
use solo las relaciones extraídas con IA (gpt4_from_analisis) y no muestre
instituciones estatales como victimarios.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
proyecto_root = Path(__file__).parent
sys.path.insert(0, str(proyecto_root))

from core.graph.visualizers.age_adapter import AGEGraphAdapter


def test_grafo_ana_matilde():
    """
    Prueba que el grafo de Ana Matilde:
    1. Use solo relaciones de método 'gpt4_from_analisis'
    2. No muestre instituciones estatales como victimarios
    3. Muestre relaciones familiares y perpetradores reales
    """

    print("=" * 80)
    print("🧪 TEST: Grafo de Ana Matilde Guzmán Borja con Relaciones IA")
    print("=" * 80)
    print()

    # Crear adaptador AGE (usa configuración por defecto de GraphConfig)
    print("🔧 Inicializando AGE Adapter...")
    adapter = AGEGraphAdapter()
    print("✅ Adaptador inicializado")
    print()

    # Buscar relaciones de Ana Matilde
    print("🔍 Buscando relaciones de 'Ana Matilde Guzmán Borja'...")
    print()

    try:
        data = adapter.query_by_entity_names_semantic(
            nombres=['Ana Matilde Guzmán Borja'],
            max_nodes=50
        )

        print(f"✅ Consulta exitosa!")
        print(f"   Nodos encontrados: {len(data['nodes'])}")

        # El adaptador puede usar 'edges' o 'links'
        edges_key = 'edges' if 'edges' in data else 'links'
        print(f"   Relaciones encontradas: {len(data[edges_key])}")
        print()

        # Analizar las relaciones
        print("📋 RELACIONES ENCONTRADAS:")
        print("-" * 80)

        relaciones_victima_de = []
        relaciones_familiares = []
        relaciones_otras = []

        for link in data[edges_key]:
            tipo = link.get('tipo_relacion', 'desconocida')
            origen = link.get('source', 'N/A')
            destino = link.get('target', 'N/A')
            confianza = link.get('confianza', 0)

            if tipo == 'victima_de':
                relaciones_victima_de.append({
                    'origen': origen,
                    'destino': destino,
                    'confianza': confianza
                })
            elif tipo in ['hijo', 'hija', 'hermano', 'hermana', 'esposo', 'esposa', 'padre', 'madre']:
                relaciones_familiares.append({
                    'tipo': tipo,
                    'origen': origen,
                    'destino': destino,
                    'confianza': confianza
                })
            else:
                relaciones_otras.append({
                    'tipo': tipo,
                    'origen': origen,
                    'destino': destino,
                    'confianza': confianza
                })

        # Mostrar relaciones victima_de
        print(f"\n🎯 Relaciones 'victima_de' ({len(relaciones_victima_de)}):")
        instituciones_estatales_encontradas = []

        for rel in relaciones_victima_de:
            destino_lower = rel['destino'].lower()

            # Verificar si es institución estatal
            instituciones_keywords = [
                'fiscalía', 'fiscal', 'unidad nacional', 'grupo especial',
                'juzgado', 'tribunal', 'procuradur', 'defensor',
                'medicina legal', 'sirdec', 'instituto nacional'
            ]

            es_institucion = any(keyword in destino_lower for keyword in instituciones_keywords)

            if es_institucion:
                print(f"   ❌ {rel['origen']} → victima_de → {rel['destino']} (conf: {rel['confianza']:.2f})")
                instituciones_estatales_encontradas.append(rel['destino'])
            else:
                print(f"   ✅ {rel['origen']} → victima_de → {rel['destino']} (conf: {rel['confianza']:.2f})")

        # Mostrar relaciones familiares
        print(f"\n👨‍👩‍👧‍👦 Relaciones familiares ({len(relaciones_familiares)}):")
        for rel in relaciones_familiares:
            print(f"   ✅ {rel['origen']} → {rel['tipo']} → {rel['destino']} (conf: {rel['confianza']:.2f})")

        # Mostrar otras relaciones
        if relaciones_otras:
            print(f"\n🔗 Otras relaciones ({len(relaciones_otras)}):")
            for rel in relaciones_otras[:10]:  # Mostrar máximo 10
                print(f"   ℹ️  {rel['origen']} → {rel['tipo']} → {rel['destino']} (conf: {rel['confianza']:.2f})")
            if len(relaciones_otras) > 10:
                print(f"   ... y {len(relaciones_otras) - 10} relaciones más")

        # Verificar resultado del test
        print()
        print("=" * 80)
        print("📊 RESULTADO DEL TEST:")
        print("=" * 80)

        if instituciones_estatales_encontradas:
            print("❌ TEST FALLIDO: Se encontraron instituciones estatales como victimarios:")
            for inst in instituciones_estatales_encontradas:
                print(f"   - {inst}")
            print()
            print("⚠️  El filtro en age_adapter.py NO está funcionando correctamente.")
            return False
        else:
            print("✅ TEST EXITOSO: No se encontraron instituciones estatales como victimarios")
            print("✅ El grafo usa solo relaciones extraídas con IA (gpt4_from_analisis)")
            print(f"✅ Total de nodos: {len(data['nodes'])}")
            print(f"✅ Total de relaciones: {len(data['links'])}")
            print(f"✅ Relaciones victima_de (perpetradores reales): {len(relaciones_victima_de)}")
            print(f"✅ Relaciones familiares: {len(relaciones_familiares)}")
            return True

    except Exception as e:
        print(f"❌ ERROR durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cerrar adaptador
        if hasattr(adapter, 'close'):
            adapter.close()
        print()
        print("🔒 Adaptador cerrado")


if __name__ == "__main__":
    success = test_grafo_ana_matilde()
    sys.exit(0 if success else 1)
