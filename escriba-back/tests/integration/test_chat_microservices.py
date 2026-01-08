#!/usr/bin/env python3
"""
Test de Microservicios de Chat
Valida Session Manager y Query Decomposer
"""

import sys
from datetime import datetime
from core.chat.session_manager import (
    InvestigationSession,
    QueryResult,
    QueryType,
    session_store
)
from core.chat.query_decomposer import QueryDecomposer


def test_session_manager():
    """Prueba el Session Manager con contexto y navegación"""
    print("=" * 70)
    print("TEST 1: SESSION MANAGER")
    print("=" * 70)

    # Crear sesión
    session = InvestigationSession(user_id="abogado_test_001")
    print(f"\n✅ Sesión creada: {session.session_id}")
    print(f"   User ID: {session.user_id}")

    # Simular Query 1: Buscar persona
    result1 = QueryResult(
        query_id="q1",
        query_text="Buscar Jorge Caicedo",
        query_type=QueryType.BUSCAR_PERSONA,
        cypher_query="MATCH (p:Persona {nombre: 'Jorge Caicedo'}) RETURN p",
        results=[{"nombre": "Jorge Caicedo", "tipo": "Persona"}],
        result_count=1,
        timestamp=datetime.now(),
        execution_time_ms=45.2,
        entities_found=["Jorge Caicedo"]
    )
    session.add_query_result(result1)
    print(f"\n📊 Query 1 ejecutada:")
    print(f"   Texto: {result1.query_text}")
    print(f"   Tipo: {result1.query_type.value}")
    print(f"   Resultados: {result1.result_count}")
    print(f"   Entidades encontradas: {result1.entities_found}")

    # Simular Query 2: Ver relaciones (contextual)
    result2 = QueryResult(
        query_id="q2",
        query_text="Ver sus relaciones",
        query_type=QueryType.RELACIONES,
        cypher_query="MATCH (p:Persona {nombre: 'Jorge Caicedo'})-[r]->(p2) RETURN r, p2",
        results=[
            {"tipo_rel": "MIEMBRO_DE", "destino": "Unión Patriótica"},
            {"tipo_rel": "HIJO", "destino": "María Caicedo"},
            {"tipo_rel": "VICTIMA_DE", "destino": "Masacre 1985"}
        ],
        result_count=3,
        timestamp=datetime.now(),
        execution_time_ms=123.8,
        entities_found=["Unión Patriótica", "María Caicedo", "Masacre 1985"]
    )
    session.add_query_result(result2)
    print(f"\n📊 Query 2 ejecutada (contextual):")
    print(f"   Texto: {result2.query_text}")
    print(f"   Tipo: {result2.query_type.value}")
    print(f"   Resultados: {result2.result_count}")

    # Verificar contexto actual
    print(f"\n🎯 Contexto actual:")
    print(f"   Entidades en foco: {session.focused_entities}")
    print(f"   Última query: {session.current_context.query_text}")

    # Verificar breadcrumbs
    breadcrumbs = session.get_breadcrumb_trail()
    print(f"\n🍞 Breadcrumb trail: {' → '.join(breadcrumbs)}")

    # Simular Query 3: Ver documentos
    result3 = QueryResult(
        query_id="q3",
        query_text="Mostrar documentos de 1985",
        query_type=QueryType.DOCUMENTOS,
        cypher_query="MATCH (d:Documento) WHERE d.anio = 1985 RETURN d",
        results=[{"id": "doc_001"}, {"id": "doc_002"}],
        result_count=2,
        timestamp=datetime.now(),
        execution_time_ms=89.3,
        entities_found=[]
    )
    session.add_query_result(result3)

    # Navegación: Volver a Query 1
    print(f"\n⬅️  Navegando hacia atrás a Query 1...")
    previous_result = session.go_to_breadcrumb("q1")
    if previous_result:
        print(f"   ✅ Navegación exitosa")
        print(f"   Contexto restaurado: {previous_result.query_text}")
        print(f"   Entidades en foco: {session.focused_entities}")

    # Resumen de sesión
    print(f"\n📈 Resumen de sesión:")
    summary = session.get_session_summary()
    print(f"   Total queries: {summary['total_queries']}")
    print(f"   Breadcrumbs: {summary['breadcrumbs']}")
    print(f"   Entidades enfocadas: {summary['focused_entities']}")

    return session


def test_query_decomposer():
    """Prueba el Query Decomposer con diferentes patrones"""
    print("\n\n" + "=" * 70)
    print("TEST 2: QUERY DECOMPOSER")
    print("=" * 70)

    decomposer = QueryDecomposer()

    # Caso 1: Query simple (no requiere descomposición)
    query1 = "Buscar Jorge Caicedo"
    print(f"\n🔍 Query 1: '{query1}'")
    print(f"   ¿Requiere descomposición? {decomposer.should_decompose(query1)}")
    steps1 = decomposer.decompose(query1)
    print(f"   Pasos generados: {len(steps1)}")
    for step in steps1:
        print(f"     {step.step_number}. {step.description} ({step.query_type.value})")

    # Caso 2: Query compleja (requiere descomposición)
    query2 = "Buscar Jorge Caicedo y ver sus relaciones con la Unión Patriótica"
    print(f"\n🔍 Query 2: '{query2}'")
    print(f"   ¿Requiere descomposición? {decomposer.should_decompose(query2)}")
    steps2 = decomposer.decompose(query2)
    print(f"   Pasos generados: {len(steps2)}")
    for step in steps2:
        print(f"     {step.step_number}. {step.description} ({step.query_type.value})")
        if step.cypher_template:
            print(f"        Template: {step.cypher_template[:60]}...")
        print(f"        Depende del anterior: {step.depends_on_previous}")

    # Caso 3: Query contextual (usa entidades del contexto)
    query3 = "Ver sus relaciones"
    context_entities = ["Jorge Caicedo"]
    print(f"\n🔍 Query 3: '{query3}' (contextual)")
    print(f"   Contexto: {context_entities}")
    steps3 = decomposer.decompose(query3, context_entities)
    print(f"   Pasos generados: {len(steps3)}")
    for step in steps3:
        print(f"     {step.step_number}. {step.description} ({step.query_type.value})")

    # Caso 4: Query de organización y red
    query4 = "Buscar miembros de la Unión Patriótica y su red de relaciones"
    print(f"\n🔍 Query 4: '{query4}'")
    print(f"   ¿Requiere descomposición? {decomposer.should_decompose(query4)}")
    steps4 = decomposer.decompose(query4)
    print(f"   Pasos generados: {len(steps4)}")
    for step in steps4:
        print(f"     {step.step_number}. {step.description} ({step.query_type.value})")
        print(f"        Depende del anterior: {step.depends_on_previous}")

    # Caso 5: Query de período y estadísticas
    query5 = "Cuántos documentos hay de 1985 y estadísticas del período"
    print(f"\n🔍 Query 5: '{query5}'")
    print(f"   ¿Requiere descomposición? {decomposer.should_decompose(query5)}")
    steps5 = decomposer.decompose(query5)
    print(f"   Pasos generados: {len(steps5)}")
    for step in steps5:
        print(f"     {step.step_number}. {step.description} ({step.query_type.value})")

    # Verificar dependencias
    print(f"\n🔗 Dependencias de Query 2:")
    dependencies = decomposer.get_step_dependencies(steps2)
    for step_num, deps in dependencies.items():
        deps_str = ', '.join(map(str, deps)) if deps else "Ninguna"
        print(f"   Paso {step_num} depende de: {deps_str}")


def test_session_store():
    """Prueba el Session Store global"""
    print("\n\n" + "=" * 70)
    print("TEST 3: SESSION STORE (Singleton)")
    print("=" * 70)

    # Crear sesión 1
    session1 = session_store.get_or_create_session(user_id="abogado_001")
    print(f"\n✅ Sesión 1 creada: {session1.session_id}")

    # Crear sesión 2
    session2 = session_store.get_or_create_session(user_id="abogado_002")
    print(f"✅ Sesión 2 creada: {session2.session_id}")

    # Recuperar sesión 1
    recovered_session = session_store.get_session(session1.session_id)
    print(f"\n🔍 Recuperando sesión 1: {recovered_session.session_id}")
    print(f"   ¿Es la misma? {recovered_session is session1}")

    # Verificar sesiones activas
    active_count = session_store.get_active_sessions_count()
    print(f"\n📊 Sesiones activas: {active_count}")

    # Eliminar sesión 2
    session_store.delete_session(session2.session_id)
    print(f"\n❌ Sesión 2 eliminada")
    print(f"   Sesiones activas: {session_store.get_active_sessions_count()}")


def test_integration():
    """Prueba integración entre Session Manager y Query Decomposer"""
    print("\n\n" + "=" * 70)
    print("TEST 4: INTEGRACIÓN (SessionManager + QueryDecomposer)")
    print("=" * 70)

    # Crear sesión y decomposer
    session = InvestigationSession(user_id="abogado_int_001")
    decomposer = QueryDecomposer()

    # Simular flujo completo de investigación
    print("\n🔬 Simulando flujo de investigación completo:")

    # Query 1: Buscar persona
    query1_text = "Buscar Jorge Caicedo y ver sus relaciones"
    print(f"\n1️⃣  Usuario pregunta: '{query1_text}'")

    steps = decomposer.decompose(query1_text)
    print(f"   Descompuesta en {len(steps)} pasos:")
    for step in steps:
        print(f"     - Paso {step.step_number}: {step.description}")

    # Simular ejecución del primer paso
    result1 = QueryResult(
        query_id="int_q1",
        query_text=steps[0].description,
        query_type=steps[0].query_type,
        cypher_query=steps[0].cypher_template,
        results=[{"nombre": "Jorge Caicedo"}],
        result_count=1,
        timestamp=datetime.now(),
        execution_time_ms=32.1,
        entities_found=["Jorge Caicedo"]
    )
    session.add_query_result(result1)
    print(f"   ✅ Paso 1 ejecutado: Encontrado 'Jorge Caicedo'")

    # Query 2: Pregunta contextual
    query2_text = "Mostrar sus documentos"
    print(f"\n2️⃣  Usuario pregunta: '{query2_text}'")

    # Usar contexto de la sesión
    context_entities = session.get_context_entities()
    print(f"   Contexto detectado: {context_entities}")

    steps2 = decomposer.decompose(query2_text, context_entities)
    print(f"   Descompuesta en {len(steps2)} pasos:")
    for step in steps2:
        print(f"     - Paso {step.step_number}: {step.description}")

    # Verificar breadcrumbs finales
    print(f"\n🍞 Breadcrumb trail final: {' → '.join(session.get_breadcrumb_trail())}")
    print(f"📊 Total queries en sesión: {len(session.query_history)}")


def main():
    """Ejecuta todos los tests"""
    print("\n" + "🧪 " * 35)
    print("PRUEBAS DE MICROSERVICIOS DE CHAT")
    print("🧪 " * 35 + "\n")

    try:
        # Test 1: Session Manager
        session = test_session_manager()

        # Test 2: Query Decomposer
        test_query_decomposer()

        # Test 3: Session Store
        test_session_store()

        # Test 4: Integración
        test_integration()

        print("\n\n" + "✅ " * 35)
        print("TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("✅ " * 35 + "\n")

    except Exception as e:
        print(f"\n\n❌ ERROR en tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
