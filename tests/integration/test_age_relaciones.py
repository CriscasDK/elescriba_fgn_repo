#!/usr/bin/env python3
"""
Test completo del grafo AGE con relaciones semánticas
"""

import sys
from pathlib import Path

root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from core.graph.visualizers.age_adapter import AGEGraphAdapter


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_search_strategies():
    """Testea las 3 estrategias de búsqueda"""
    print_section("🔍 TEST 1: ESTRATEGIAS DE BÚSQUEDA")

    adapter = AGEGraphAdapter()

    test_cases = [
        ("Dr. Ramón de J. Henao Henao", "Búsqueda exacta"),
        ("dr. ramón de j. henao henao", "Case-insensitive"),
        ("DR. RAMÓN DE J. HENAO HENAO", "Mayúsculas"),
        ("Ramón Henao", "Búsqueda parcial"),
    ]

    for nombre, tipo in test_cases:
        print(f"\n🔎 Test: {tipo}")
        print(f"   Buscando: '{nombre}'")

        nodes = adapter.search_nodes_by_name(nombre, limit=3)

        if nodes:
            print(f"   ✅ Encontrados: {len(nodes)} nodos")
            for node in nodes[:2]:
                print(f"      - {node['name']} (tipo: {node.get('type', 'N/A')})")
        else:
            print(f"   ❌ No encontrado")


def test_query_with_relations():
    """Testea query completa con relaciones"""
    print_section("🔗 TEST 2: QUERY CON RELACIONES SEMÁNTICAS")

    adapter = AGEGraphAdapter()

    # Test con persona que sabemos que existe
    print("\n🔎 Test: Oswaldo Olivo")
    data = adapter.query_by_entity_names(
        nombres=["Oswaldo Olivo"],
        include_neighborhood=True,
        depth=1
    )

    print(f"\n📊 Resultados:")
    print(f"   Nodos: {len(data['nodes'])}")
    print(f"   Relaciones: {len(data['edges'])}")

    if data['edges']:
        print(f"\n   Tipos de relaciones encontradas:")
        rel_types = set(e.get('type', 'UNKNOWN') for e in data['edges'])
        for rel_type in rel_types:
            count = sum(1 for e in data['edges'] if e.get('type') == rel_type)
            print(f"      - {rel_type}: {count}")

        print(f"\n   Muestra de relaciones:")
        for edge in data['edges'][:5]:
            source = edge.get('source_name', edge.get('source', '?'))
            target = edge.get('target_name', edge.get('target', '?'))
            rel_type = edge.get('type', '?')
            print(f"      {source} --[{rel_type}]--> {target}")
    else:
        print(f"   ⚠️  No se encontraron relaciones")


def test_multiple_entities():
    """Testea búsqueda de múltiples entidades"""
    print_section("👥 TEST 3: MÚLTIPLES ENTIDADES")

    adapter = AGEGraphAdapter()

    nombres = ["Oswaldo Olivo", "Rosa Edith Sierra"]
    print(f"\n🔎 Buscando relaciones entre:")
    for n in nombres:
        print(f"   - {n}")

    data = adapter.query_by_entity_names(
        nombres=nombres,
        include_neighborhood=True,
        depth=1
    )

    print(f"\n📊 Resultados:")
    print(f"   Nodos: {len(data['nodes'])}")
    print(f"   Relaciones: {len(data['edges'])}")

    if data['nodes']:
        print(f"\n   Personas encontradas:")
        for node in data['nodes'][:10]:
            print(f"      - {node['name']}")


def test_case_variations():
    """Testea variaciones de mayúsculas/minúsculas"""
    print_section("🔤 TEST 4: VARIACIONES DE CASE")

    adapter = AGEGraphAdapter()

    # Obtener un nombre real del grafo primero
    print("\n📋 Obteniendo nombres de muestra...")
    sample_data = adapter.query_by_entity_names(
        nombres=["Dr. Ramón de J. Henao Henao"],
        include_neighborhood=False,
        depth=0
    )

    if sample_data['nodes']:
        original_name = sample_data['nodes'][0]['name']
        print(f"   Nombre original en AGE: '{original_name}'")

        variations = [
            original_name,  # Exacto
            original_name.lower(),  # Minúsculas
            original_name.upper(),  # Mayúsculas
        ]

        print(f"\n🔎 Testeando variaciones:")
        for var in variations:
            nodes = adapter.search_nodes_by_name(var, limit=1)
            status = "✅" if nodes else "❌"
            print(f"   {status} '{var[:50]}...' -> {len(nodes)} resultados")


def test_relation_types_diversity():
    """Verifica diversidad de tipos de relaciones"""
    print_section("🎨 TEST 5: DIVERSIDAD DE RELACIONES")

    adapter = AGEGraphAdapter()

    # Obtener muestra grande
    print("\n📊 Analizando tipos de relaciones en el grafo...")

    # Buscar varias personas
    test_names = [
        "Dr. Ramón de J. Henao Henao",
        "Dr. Víctor Hugo Moreno",
        "Luis Arcesio Leyton González"
    ]

    all_rel_types = set()
    total_edges = 0

    for name in test_names:
        try:
            data = adapter.query_by_entity_names(
                nombres=[name],
                include_neighborhood=True,
                depth=1
            )
            total_edges += len(data['edges'])
            for edge in data['edges']:
                all_rel_types.add(edge.get('type', 'UNKNOWN'))
        except:
            pass

    print(f"\n✅ Tipos de relaciones encontrados: {len(all_rel_types)}")
    for rel_type in sorted(all_rel_types):
        print(f"   - {rel_type}")

    print(f"\n📊 Total de relaciones analizadas: {total_edges}")

    if len(all_rel_types) <= 1:
        print("\n⚠️  ADVERTENCIA: Solo hay 1 tipo de relación")
        print("   Esperado: ORGANIZACION, MIEMBRO_DE, VICTIMA_DE, etc.")
    else:
        print("\n✅ Diversidad de relaciones confirmada")


def main():
    print_section("🧪 TEST COMPLETO DEL GRAFO AGE")

    try:
        test_search_strategies()
        test_query_with_relations()
        test_multiple_entities()
        test_case_variations()
        test_relation_types_diversity()

        print_section("✅ TESTS COMPLETADOS")
        print("\n🎉 Todos los tests ejecutados")
        print("\n🔧 PRÓXIMO PASO:")
        print("   - Reiniciar Dash y probar desde UI")
        print("   - Hacer clic en botón 🌐 de cualquier víctima")
        print("   - Verificar que se muestren relaciones variadas")

    except Exception as e:
        print(f"\n❌ Error en tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
