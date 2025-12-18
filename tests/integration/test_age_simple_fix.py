#!/usr/bin/env python3
"""Test simple del fix de AGE"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def test_age_simple():
    """Prueba simple de AGE con consulta básica"""
    print("=" * 80)
    print("TEST SIMPLE: AGE con max_locks_per_transaction = 256")
    print("=" * 80)

    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5432),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

    try:
        cursor = conn.cursor()

        # Verificar configuración
        print("\n1. Verificando configuración...")
        cursor.execute("SHOW max_locks_per_transaction;")
        locks = cursor.fetchone()[0]
        print(f"   ✅ max_locks_per_transaction = {locks}")

        if int(locks) < 256:
            print(f"   ❌ ERROR: Valor esperado 256, actual {locks}")
            return False

        # Verificar extensión AGE
        print("\n2. Verificando extensión AGE...")
        cursor.execute("SELECT * FROM ag_catalog.ag_graph;")
        graphs = cursor.fetchall()
        print(f"   ✅ Grafos disponibles: {len(graphs)}")
        for g in graphs:
            print(f"      - {g[1]}")

        # Hacer una query simple sin LIMIT
        print("\n3. Ejecutando query AGE simple (sin LIMIT)...")
        query = """
        SELECT * FROM cypher('legal_graph', $$
            MATCH (n:Persona)
            RETURN n
            LIMIT 3
        $$) as (n agtype);
        """

        cursor.execute("LOAD 'age';")
        cursor.execute("SET search_path = ag_catalog, '$user', public;")

        cursor.execute(query)
        results = cursor.fetchall()
        print(f"   ✅ Query ejecutada, {len(results)} resultados")

        print("\n" + "=" * 80)
        print("✅ TEST EXITOSO - AGE funcionando con max_locks = 256")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_age_simple()
    exit(0 if success else 1)
