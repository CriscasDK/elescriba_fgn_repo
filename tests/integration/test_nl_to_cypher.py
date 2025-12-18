#!/usr/bin/env python3
"""
Test del convertidor Natural Language → Cypher
"""

import sys
from core.chat.nl_to_cypher import NLToCypherConverter
from core.chat.session_manager import QueryType


def test_basic_conversions():
    """Prueba conversiones básicas sin llamar al LLM"""
    print("=" * 70)
    print("TEST 1: CONVERSIONES BÁSICAS (Mock - sin LLM)")
    print("=" * 70)

    converter = NLToCypherConverter(initialize_llm=False)

    # Test 1: Validación de Cypher
    print("\n🔍 Test de validación de sintaxis:")

    valid_queries = [
        "MATCH (p:Persona) RETURN p LIMIT 10",
        "MATCH (p:Persona {nombre: 'Jorge'})-[r]->(p2) RETURN p, r, p2",
        "MATCH (d:Documento) WHERE d.anio = 1985 RETURN d"
    ]

    invalid_queries = [
        "",  # Vacío
        "MATCH (p:Persona",  # Paréntesis sin cerrar
        "SELECT * FROM personas",  # SQL, no Cypher
    ]

    for query in valid_queries:
        is_valid, error = converter.validate_cypher(query)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {query[:50]}...")

    for query in invalid_queries:
        is_valid, error = converter.validate_cypher(query)
        status = "✅" if not is_valid else "❌"
        desc = query[:30] if query else "(vacío)"
        print(f"  {status} RECHAZADO: {desc}... → {error}")

    # Test 2: Inferencia de query type
    print("\n🔍 Test de inferencia de tipo de query:")

    test_queries = [
        ("MATCH (p:Persona) RETURN p", "buscar_persona"),
        ("MATCH (p)-[r]->(p2) RETURN r", "relaciones"),
        ("MATCH (d:Documento) RETURN d", "documentos"),
        ("MATCH (d:Documento) RETURN count(d)", "estadisticas"),
    ]

    for cypher, expected_type in test_queries:
        inferred = converter._infer_query_type(cypher)
        status = "✅" if inferred.value == expected_type else "❌"
        print(f"  {status} {cypher[:40]}... → {inferred.value}")

    # Test 3: Resolución de referencias contextuales
    print("\n🔍 Test de resolución contextual:")

    contextual_queries = [
        ("sus relaciones", ["Jorge Caicedo"], "relaciones de jorge caicedo"),
        ("ver sus documentos", ["María López"], "ver documentos de maría lópez"),
        ("esa persona", ["Pedro Ruiz"], "pedro ruiz"),
    ]

    for query, entities, expected in contextual_queries:
        resolved = converter._resolve_contextual_references(query, entities)
        status = "✅" if resolved == expected else "❌"
        print(f"  {status} '{query}' + {entities[0]} → '{resolved}'")

    # Test 4: Schema del grafo
    print("\n📊 Schema del grafo cargado:")
    print(f"  Tipos de nodos: {len(converter.graph_schema['node_types'])}")
    for node_type in converter.graph_schema['node_types']:
        print(f"    - {node_type['label']}: {node_type['description']}")

    print(f"\n  Tipos de relaciones: {len(converter.graph_schema['relationship_types'])}")
    print(f"    {', '.join(converter.graph_schema['relationship_types'][:10])}...")

    print(f"\n  Ejemplos cargados: {len(converter.examples)}")


def test_llm_conversion():
    """
    Prueba conversión real con Azure OpenAI.

    NOTA: Esto requiere credenciales válidas de Azure OpenAI.
    Si no están configuradas, el test fallará (esperado).
    """
    print("\n\n" + "=" * 70)
    print("TEST 2: CONVERSIÓN CON LLM (Azure OpenAI)")
    print("=" * 70)

    try:
        converter = NLToCypherConverter()

        test_queries = [
            "Buscar Jorge Caicedo",
            "Ver relaciones de la Unión Patriótica",
            "Documentos de 1985",
        ]

        print("\n🤖 Convirtiendo queries con Azure OpenAI GPT-4...")
        print("(Esto puede tomar unos segundos...)\n")

        for nl_query in test_queries:
            print(f"📝 Query: '{nl_query}'")
            try:
                result = converter.convert(nl_query)

                print(f"   ✅ Cypher generado:")
                print(f"      {result.cypher}")
                print(f"   📖 Explicación: {result.explanation}")
                print(f"   🎯 Confianza: {result.confidence:.2f}")
                print(f"   📂 Tipo: {result.query_type.value}")

                # Validar el Cypher generado
                is_valid, error = converter.validate_cypher(result.cypher)
                if is_valid:
                    print(f"   ✅ Sintaxis válida")
                else:
                    print(f"   ⚠️  Posible error: {error}")

                print()

            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()

    except Exception as e:
        print(f"\n⚠️  No se pudo conectar a Azure OpenAI:")
        print(f"   {e}")
        print(f"\n   Para probar este test, configura las variables de entorno:")
        print(f"   - AZURE_OPENAI_API_KEY")
        print(f"   - AZURE_OPENAI_ENDPOINT")


def test_contextual_conversion():
    """Prueba conversión con contexto"""
    print("\n\n" + "=" * 70)
    print("TEST 3: CONVERSIÓN CONTEXTUAL")
    print("=" * 70)

    try:
        converter = NLToCypherConverter()

        # Simular flujo contextual
        context_entities = ["Jorge Caicedo"]

        print(f"\n🎯 Contexto: {context_entities}")
        print(f"\n📝 Query contextual: 'Ver sus relaciones'")

        result = converter.convert(
            "Ver sus relaciones",
            context_entities=context_entities
        )

        print(f"\n   Cypher generado:")
        print(f"   {result.cypher}")
        print(f"   Explicación: {result.explanation}")

    except Exception as e:
        print(f"\n⚠️  Error: {e}")


def main():
    print("\n" + "🧪 " * 35)
    print("PRUEBAS DE CONVERTIDOR NL → CYPHER")
    print("🧪 " * 35 + "\n")

    try:
        # Test 1: Conversiones básicas (sin LLM)
        test_basic_conversions()

        # Test 2: Conversión con LLM (requiere Azure OpenAI)
        test_llm_conversion()

        # Test 3: Conversión contextual
        test_contextual_conversion()

        print("\n\n" + "✅ " * 35)
        print("TESTS COMPLETADOS")
        print("✅ " * 35 + "\n")

    except Exception as e:
        print(f"\n\n❌ ERROR en tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
