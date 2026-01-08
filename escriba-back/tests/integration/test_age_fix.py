#!/usr/bin/env python3
"""
Test para verificar que el fix de AGE (max_locks_per_transaction = 256) funciona
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_age_query():
    """Prueba una consulta AGE que antes fallaba con 'out of shared memory'"""
    from core.graph.visualizers.age_adapter import AGEGraphAdapter

    print("=" * 80)
    print("TEST: Verificando fix de AGE (max_locks_per_transaction = 256)")
    print("=" * 80)

    try:
        adapter = AGEGraphAdapter()
        print("\n✅ AGEGraphAdapter creado exitosamente")

        # Probar búsqueda de nodo (query que antes fallaba)
        print("\n🔍 Buscando nodos por nombre: 'Oswaldo Olivo'...")

        result = adapter.query_by_entity_names(
            nombres=["Oswaldo Olivo"],
            include_neighborhood=True,
            depth=1
        )

        print(f"\n✅ Query ejecutada exitosamente!")
        print(f"   - Nodos encontrados: {len(result.get('nodes', []))}")
        print(f"   - Relaciones encontradas: {len(result.get('edges', []))}")

        if len(result.get('nodes', [])) > 0:
            print(f"\n📊 Primeros nodos encontrados:")
            for i, node in enumerate(result['nodes'][:3]):
                print(f"   {i+1}. {node.get('label', 'N/A')}: {node.get('properties', {}).get('nombre', 'N/A')}")

        if len(result.get('edges', [])) > 0:
            print(f"\n🔗 Primeras relaciones encontradas:")
            for i, edge in enumerate(result['edges'][:3]):
                print(f"   {i+1}. {edge.get('label', 'N/A')} (confianza: {edge.get('properties', {}).get('confianza', 'N/A')})")

        print("\n" + "=" * 80)
        print("✅ TEST EXITOSO - AGE funcionando correctamente con max_locks_per_transaction = 256")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\n" + "=" * 80)
        print("❌ TEST FALLIDO - AGE aún tiene problemas")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_age_query()
    exit(0 if success else 1)
