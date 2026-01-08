#!/usr/bin/env python3
"""
Script de test para Apache AGE

Verifica que la instalación de AGE funciona correctamente y prueba
operaciones básicas del conector.
"""

import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph.age_connector import AGEConnector
from core.graph.config import GraphConfig


def test_connection():
    """Test 1: Conexión a PostgreSQL"""
    print("\n" + "="*60)
    print("TEST 1: Conexión a PostgreSQL")
    print("="*60)

    connector = AGEConnector()
    if connector.test_connection():
        print("✅ Test de conexión EXITOSO\n")
        return True
    else:
        print("❌ Test de conexión FALLIDO\n")
        return False


def test_graph_creation():
    """Test 2: Creación de grafo"""
    print("="*60)
    print("TEST 2: Creación de Grafo de Prueba")
    print("="*60)

    connector = AGEConnector()
    test_graph_name = "test_graph"

    # Limpiar grafo anterior si existe
    if connector.graph_exists(test_graph_name):
        print(f"   Limpiando grafo anterior '{test_graph_name}'...")
        connector.drop_graph(test_graph_name)

    # Crear nuevo grafo
    if connector.create_graph(test_graph_name):
        print("✅ Test de creación de grafo EXITOSO\n")
        return True, test_graph_name
    else:
        print("❌ Test de creación de grafo FALLIDO\n")
        return False, None


def test_node_creation(graph_name):
    """Test 3: Creación de nodos"""
    print("="*60)
    print("TEST 3: Creación de Nodos")
    print("="*60)

    connector = AGEConnector()

    # Crear nodo de persona
    person_props = {
        "nombre": "Juan Pérez",
        "tipo": "victima",
        "documento_id": "test_doc_001"
    }

    print(f"   Creando nodo Persona: {person_props['nombre']}")
    if connector.create_node("Persona", person_props, graph_name):
        print("   ✅ Nodo Persona creado")
    else:
        print("   ❌ Error creando nodo Persona")
        return False

    # Crear nodo de organización
    org_props = {
        "nombre": "DAS",
        "tipo": "fuerza_legitima"
    }

    print(f"   Creando nodo Organizacion: {org_props['nombre']}")
    if connector.create_node("Organizacion", org_props, graph_name):
        print("   ✅ Nodo Organizacion creado")
    else:
        print("   ❌ Error creando nodo Organizacion")
        return False

    print("\n✅ Test de creación de nodos EXITOSO\n")
    return True


def test_relationship_creation(graph_name):
    """Test 4: Creación de relaciones"""
    print("="*60)
    print("TEST 4: Creación de Relaciones")
    print("="*60)

    connector = AGEConnector()

    # Crear relación entre persona y organización
    print("   Creando relación: (Juan Pérez)-[VINCULADO_CON]->(DAS)")
    rel_props = {
        "fuerza": 0.8,
        "tipo_relacion": "co_ocurrencia"
    }

    if connector.create_relationship(
        from_label="Persona",
        from_property="nombre",
        from_value="Juan Pérez",
        to_label="Organizacion",
        to_property="nombre",
        to_value="DAS",
        rel_type="VINCULADO_CON",
        rel_properties=rel_props,
        graph_name=graph_name
    ):
        print("   ✅ Relación creada")
        print("\n✅ Test de creación de relaciones EXITOSO\n")
        return True
    else:
        print("   ❌ Error creando relación")
        print("\n❌ Test de creación de relaciones FALLIDO\n")
        return False


def test_cypher_queries(graph_name):
    """Test 5: Consultas Cypher"""
    print("="*60)
    print("TEST 5: Consultas Cypher")
    print("="*60)

    connector = AGEConnector()

    # Consulta 1: Obtener todos los nodos
    print("   Consulta 1: MATCH (n) RETURN n")
    cypher = "MATCH (n) RETURN n"
    results = connector.execute_cypher(cypher, graph_name=graph_name)
    print(f"   → Resultados: {len(results)} nodos encontrados")

    # Consulta 2: Obtener relaciones
    print("\n   Consulta 2: MATCH ()-[r]->() RETURN r")
    cypher = "MATCH ()-[r]->() RETURN r"
    results = connector.execute_cypher(cypher, graph_name=graph_name)
    print(f"   → Resultados: {len(results)} relaciones encontradas")

    # Consulta 3: Buscar caminos
    print("\n   Consulta 3: MATCH path = (a)-[r]->(b) RETURN path")
    cypher = "MATCH path = (a)-[r]->(b) RETURN path"
    results = connector.execute_cypher(cypher, graph_name=graph_name)
    print(f"   → Resultados: {len(results)} caminos encontrados")

    print("\n✅ Test de consultas Cypher EXITOSO\n")
    return True


def test_graph_stats(graph_name):
    """Test 6: Estadísticas del grafo"""
    print("="*60)
    print("TEST 6: Estadísticas del Grafo")
    print("="*60)

    connector = AGEConnector()
    stats = connector.get_graph_stats(graph_name)

    print("   Estadísticas:")
    print(f"   - Total nodos: {stats.get('total_nodes', 0)}")
    print(f"   - Total relaciones: {stats.get('total_relationships', 0)}")

    print("\n✅ Test de estadísticas EXITOSO\n")
    return True


def cleanup(graph_name):
    """Limpieza: Eliminar grafo de prueba"""
    print("="*60)
    print("LIMPIEZA: Eliminando Grafo de Prueba")
    print("="*60)

    connector = AGEConnector()
    if connector.drop_graph(graph_name):
        print("✅ Grafo de prueba eliminado\n")
    else:
        print("⚠️  No se pudo eliminar el grafo de prueba\n")


def main():
    """Ejecuta todos los tests"""
    print("\n" + "🧪 SUITE DE TESTS PARA APACHE AGE ".center(60, "="))
    print()

    test_results = []

    # Test 1: Conexión
    result = test_connection()
    test_results.append(("Conexión", result))
    if not result:
        print("❌ Tests abortados: no hay conexión a PostgreSQL")
        return

    # Test 2: Creación de grafo
    result, graph_name = test_graph_creation()
    test_results.append(("Creación de grafo", result))
    if not result:
        print("❌ Tests abortados: no se pudo crear grafo")
        return

    # Test 3: Creación de nodos
    result = test_node_creation(graph_name)
    test_results.append(("Creación de nodos", result))

    # Test 4: Creación de relaciones
    result = test_relationship_creation(graph_name)
    test_results.append(("Creación de relaciones", result))

    # Test 5: Consultas Cypher
    result = test_cypher_queries(graph_name)
    test_results.append(("Consultas Cypher", result))

    # Test 6: Estadísticas
    result = test_graph_stats(graph_name)
    test_results.append(("Estadísticas", result))

    # Limpieza
    cleanup(graph_name)

    # Resumen de resultados
    print("="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:.<40} {status}")

    print(f"\n   Total: {passed}/{total} tests exitosos")

    if passed == total:
        print("\n🎉 ¡Todos los tests pasaron! Apache AGE está listo para usar.\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests fallaron. Revisa los errores arriba.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())