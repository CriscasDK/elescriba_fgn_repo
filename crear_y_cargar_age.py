#!/usr/bin/env python3
"""
Script para crear el grafo AGE y cargar datos desde PostgreSQL
"""

import sys
from pathlib import Path

root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from core.graph.age_connector import AGEConnector
import time


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_graph(connector):
    """Crea el grafo legal_graph en AGE"""
    print_section("📦 CREANDO GRAFO 'legal_graph'")

    with connector.get_connection() as conn:
        cursor = conn.cursor()

        try:
            # Verificar si ya existe
            cursor.execute("SELECT name FROM ag_catalog.ag_graph WHERE name = 'legal_graph';")
            if cursor.fetchone():
                print("⚠️  El grafo 'legal_graph' ya existe")
                return True

            # Crear grafo
            print("Creando grafo...")
            cursor.execute("SELECT create_graph('legal_graph');")
            conn.commit()
            print("✅ Grafo 'legal_graph' creado exitosamente")
            return True

        except Exception as e:
            conn.rollback()
            print(f"❌ Error creando grafo: {e}")
            return False


def load_victims_as_personas(connector, limit=100):
    """Carga víctimas de PostgreSQL como nodos Persona en AGE"""
    print_section(f"👤 CARGANDO VÍCTIMAS COMO PERSONAS (limit={limit})")

    with connector.get_connection() as conn:
        cursor = conn.cursor()

        try:
            # Obtener víctimas de PostgreSQL
            print("Obteniendo víctimas desde PostgreSQL...")
            cursor.execute(f"""
                SELECT DISTINCT
                    nombre_victima,
                    COUNT(DISTINCT id_documento) as doc_count
                FROM victimas
                WHERE nombre_victima IS NOT NULL
                  AND nombre_victima != ''
                  AND LENGTH(nombre_victima) > 3
                GROUP BY nombre_victima
                ORDER BY doc_count DESC
                LIMIT {limit};
            """)
            victimas = cursor.fetchall()
            print(f"✅ Encontradas {len(victimas)} víctimas únicas")

            # Insertar como nodos Persona en AGE
            print("\nInsertando nodos en AGE...")
            inserted = 0
            errors = 0

            for nombre, doc_count in victimas:
                try:
                    # Escapar comillas simples
                    nombre_escaped = nombre.replace("'", "\\'")

                    # Insertar nodo
                    cypher_query = f"""
                        SELECT *
                        FROM cypher('legal_graph', $$
                            CREATE (p:Persona {{
                                nombre: '{nombre_escaped}',
                                doc_count: {doc_count},
                                tipo: 'victima'
                            }})
                            RETURN p
                        $$) as (persona agtype);
                    """

                    cursor.execute(cypher_query)
                    inserted += 1

                    if inserted % 10 == 0:
                        print(f"   Insertados: {inserted}/{len(victimas)}")

                except Exception as e:
                    errors += 1
                    if errors < 5:  # Solo mostrar primeros 5 errores
                        print(f"   ⚠️  Error con '{nombre}': {str(e)[:100]}")

            conn.commit()
            print(f"\n✅ Insertados: {inserted} personas")
            print(f"⚠️  Errores: {errors}")

            return inserted > 0

        except Exception as e:
            conn.rollback()
            print(f"❌ Error cargando víctimas: {e}")
            return False


def create_cooccurrence_relations(connector, limit=500):
    """Crea relaciones de co-ocurrencia entre personas basadas en documentos compartidos"""
    print_section(f"🔗 CREANDO RELACIONES DE CO-OCURRENCIA (limit={limit})")

    with connector.get_connection() as conn:
        cursor = conn.cursor()

        try:
            # Obtener co-ocurrencias desde vista materializada PostgreSQL
            print("Obteniendo co-ocurrencias desde PostgreSQL...")
            cursor.execute(f"""
                SELECT
                    entidad1,
                    entidad2,
                    frecuencia,
                    documentos_compartidos
                FROM mv_red_conexiones
                WHERE frecuencia >= 2  -- Mínimo 2 documentos compartidos
                ORDER BY frecuencia DESC
                LIMIT {limit};
            """)
            cooccurrences = cursor.fetchall()
            print(f"✅ Encontradas {len(cooccurrences)} co-ocurrencias")

            # Crear relaciones en AGE
            print("\nCreando relaciones en AGE...")
            created = 0
            errors = 0

            for entidad1, entidad2, frecuencia, docs in cooccurrences:
                try:
                    # Escapar comillas
                    e1_escaped = entidad1.replace("'", "\\'")
                    e2_escaped = entidad2.replace("'", "\\'")

                    cypher_query = f"""
                        SELECT *
                        FROM cypher('legal_graph', $$
                            MATCH (p1:Persona {{nombre: '{e1_escaped}'}})
                            MATCH (p2:Persona {{nombre: '{e2_escaped}'}})
                            CREATE (p1)-[r:CO_OCURRE_CON {{
                                frecuencia: {frecuencia},
                                documentos: {docs}
                            }}]->(p2)
                            RETURN r
                        $$) as (relacion agtype);
                    """

                    cursor.execute(cypher_query)
                    created += 1

                    if created % 50 == 0:
                        print(f"   Creadas: {created}/{len(cooccurrences)}")

                except Exception as e:
                    errors += 1
                    if errors < 5:
                        print(f"   ⚠️  Error: {str(e)[:100]}")

            conn.commit()
            print(f"\n✅ Creadas: {created} relaciones")
            print(f"⚠️  Errores: {errors}")

            return created > 0

        except Exception as e:
            conn.rollback()
            print(f"❌ Error creando relaciones: {e}")
            return False


def verify_graph(connector):
    """Verifica el estado final del grafo"""
    print_section("✅ VERIFICACIÓN FINAL")

    with connector.get_connection() as conn:
        cursor = conn.cursor()

        try:
            # Contar nodos
            cursor.execute("""
                SELECT COUNT(*)
                FROM cypher('legal_graph', $$
                    MATCH (n:Persona)
                    RETURN n
                $$) as (node agtype);
            """)
            node_count = cursor.fetchone()[0]
            print(f"📊 Total nodos (Persona): {node_count}")

            # Contar relaciones
            cursor.execute("""
                SELECT COUNT(*)
                FROM cypher('legal_graph', $$
                    MATCH ()-[r:CO_OCURRE_CON]->()
                    RETURN r
                $$) as (rel agtype);
            """)
            edge_count = cursor.fetchone()[0]
            print(f"📊 Total relaciones (CO_OCURRE_CON): {edge_count}")

            # Sample de personas
            cursor.execute("""
                SELECT *
                FROM cypher('legal_graph', $$
                    MATCH (p:Persona)
                    RETURN p.nombre
                    LIMIT 5
                $$) as (nombre agtype);
            """)
            print("\n📋 Muestra de personas:")
            for row in cursor.fetchall():
                print(f"   - {str(row[0]).strip('\"')}")

            # Test específico
            cursor.execute("""
                SELECT COUNT(*)
                FROM cypher('legal_graph', $$
                    MATCH (p:Persona {nombre: 'Omar de Jesus Correa Isaza'})
                    RETURN p
                $$) as (node agtype);
            """)
            omar_exists = cursor.fetchone()[0]
            if omar_exists:
                print(f"\n✅ Test: 'Omar de Jesus Correa Isaza' encontrado en AGE")
            else:
                print(f"\n⚠️  Test: 'Omar de Jesus Correa Isaza' NO encontrado")

        except Exception as e:
            print(f"❌ Error en verificación: {e}")


def main():
    print_section("🚀 CREACIÓN Y CARGA DEL GRAFO AGE")

    connector = AGEConnector()

    # 1. Crear grafo
    if not create_graph(connector):
        print("\n❌ No se pudo crear el grafo. Abortando.")
        return

    time.sleep(1)

    # 2. Cargar personas (víctimas)
    print("\n¿Cuántas víctimas cargar? (100, 500, 1000, o 'all')")
    print("Recomendado: 500 para empezar")
    limit_input = input("Límite (default=500): ").strip() or "500"

    if limit_input.lower() == 'all':
        limit = 999999
    else:
        try:
            limit = int(limit_input)
        except:
            limit = 500

    if not load_victims_as_personas(connector, limit=limit):
        print("\n❌ Error cargando víctimas. Abortando.")
        return

    time.sleep(1)

    # 3. Crear relaciones
    print("\n¿Cuántas relaciones crear? (500, 1000, 5000, o 'all')")
    print("Recomendado: 1000 para empezar")
    rel_input = input("Límite (default=1000): ").strip() or "1000"

    if rel_input.lower() == 'all':
        rel_limit = 999999
    else:
        try:
            rel_limit = int(rel_input)
        except:
            rel_limit = 1000

    if not create_cooccurrence_relations(connector, limit=rel_limit):
        print("\n⚠️  Error creando relaciones (esto es opcional)")

    time.sleep(1)

    # 4. Verificar
    verify_graph(connector)

    print_section("🎉 PROCESO COMPLETADO")
    print("✅ El grafo AGE está listo para usar")
    print("\n🔧 PRÓXIMOS PASOS:")
    print("   1. Ejecutar: python diagnostico_age_simple.py")
    print("   2. Probar visualización en Dash: http://localhost:8050")


if __name__ == "__main__":
    main()
