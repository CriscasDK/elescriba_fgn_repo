#!/usr/bin/env python3
"""
Script de consultas al grafo

Permite explorar el grafo con consultas Cypher especializadas.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph.age_connector import AGEConnector
from core.graph.config import GraphConfig


def imprimir_resultados(resultados: List[Dict], titulo: str):
    """Imprime resultados de forma legible"""
    print("\n" + "="*60)
    print(f"📊 {titulo}")
    print("="*60)

    if not resultados:
        print("   (Sin resultados)")
        return

    for i, row in enumerate(resultados, 1):
        print(f"\n{i}. {row}")


def query_estadisticas(connector: AGEConnector, graph_name: str):
    """Consulta: Estadísticas generales del grafo"""
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DEL GRAFO")
    print("="*60)

    # Contar nodos por tipo
    queries = {
        "Total de nodos": "MATCH (n) RETURN count(n) as total",
        "Total de relaciones": "MATCH ()-[r]->() RETURN count(r) as total",
        "Personas": "MATCH (n:Persona) RETURN count(n) as total",
        "Organizaciones": "MATCH (n:Organizacion) RETURN count(n) as total",
        "Lugares": "MATCH (n:Lugar) RETURN count(n) as total",
        "Documentos": "MATCH (n:Documento) RETURN count(n) as total",
    }

    for descripcion, cypher in queries.items():
        resultado = connector.execute_cypher(
            cypher,
            graph_name=graph_name,
            column_definitions=["total agtype"]
        )
        if resultado:
            total = resultado[0].get('total', 0)
            print(f"   {descripcion:.<40} {total}")

    # Desglose de relaciones por tipo
    print("\n   Desglose de relaciones:")
    # Consultar cada tipo de relación individualmente
    tipos_relaciones = [
        "co_ocurrencia_persona",
        "co_ocurrencia_persona_org",
        "co_ocurrencia_org",
        "MENCIONADO_EN",
        "UBICADO_EN",
        "OPERA_EN",
        "PERTENECE_A"
    ]

    for tipo in tipos_relaciones:
        cypher = f"MATCH ()-[r:VINCULADO {{tipo_relacion: '{tipo}'}}]->() RETURN count(r) as total"
        resultado = connector.execute_cypher(
            cypher,
            graph_name=graph_name,
            column_definitions=["total agtype"]
        )
        if resultado:
            total = resultado[0].get('total', 0)
            if total > 0:
                print(f"     - {tipo:.<35} {total}")


def query_personas_mas_conectadas(connector: AGEConnector, graph_name: str, limit: int = 10):
    """Consulta: Personas con más conexiones"""
    # AGE requiere ORDER BY en el resultado de count(), no en el alias
    cypher = f"""
    MATCH (p:Persona)-[r]-()
    WITH p.nombre as nombre, count(r) as conexiones
    RETURN nombre, conexiones
    ORDER BY conexiones DESC
    LIMIT {limit}
    """

    # Especificar columnas de salida
    resultados = connector.execute_cypher(
        cypher,
        graph_name=graph_name,
        column_definitions=["nombre agtype", "conexiones agtype"]
    )
    imprimir_resultados(resultados, f"TOP {limit} PERSONAS MÁS CONECTADAS")


def query_organizaciones_mas_mencionadas(connector: AGEConnector, graph_name: str, limit: int = 10):
    """Consulta: Organizaciones con más conexiones"""
    cypher = f"""
    MATCH (o:Organizacion)-[r]-()
    WITH o.nombre as nombre, o.subtipo as tipo, count(r) as conexiones
    RETURN nombre, tipo, conexiones
    ORDER BY conexiones DESC
    LIMIT {limit}
    """

    resultados = connector.execute_cypher(
        cypher,
        graph_name=graph_name,
        column_definitions=["nombre agtype", "tipo agtype", "conexiones agtype"]
    )
    imprimir_resultados(resultados, f"TOP {limit} ORGANIZACIONES MÁS MENCIONADAS")


def query_lugares_mas_mencionados(connector: AGEConnector, graph_name: str, limit: int = 10):
    """Consulta: Lugares con más conexiones"""
    cypher = f"""
    MATCH (l:Lugar)-[r]-()
    WITH l.nombre as nombre, l.subtipo as tipo, count(r) as conexiones
    RETURN nombre, tipo, conexiones
    ORDER BY conexiones DESC
    LIMIT {limit}
    """

    resultados = connector.execute_cypher(
        cypher,
        graph_name=graph_name,
        column_definitions=["nombre agtype", "tipo agtype", "conexiones agtype"]
    )
    imprimir_resultados(resultados, f"TOP {limit} LUGARES MÁS MENCIONADOS")


def query_buscar_entidad(connector: AGEConnector, graph_name: str, nombre: str):
    """Consulta: Buscar una entidad específica y sus conexiones"""
    cypher = f"""
    MATCH (n)
    WHERE toLower(n.nombre) CONTAINS toLower('{nombre}')
    RETURN n.nombre as nombre, labels(n) as tipo
    LIMIT 10
    """

    resultados = connector.execute_cypher(
        cypher,
        graph_name=graph_name,
        column_definitions=["nombre agtype", "tipo agtype"]
    )
    imprimir_resultados(resultados, f"BÚSQUEDA: '{nombre}'")

    # Si hay resultados, mostrar conexiones del primero
    if resultados:
        nombre_exacto = resultados[0].get('nombre')
        # Remover comillas si las tiene AGE
        if isinstance(nombre_exacto, str) and nombre_exacto.startswith('"'):
            nombre_exacto = nombre_exacto.strip('"')

        cypher_conexiones = f"""
        MATCH (n {{nombre: '{nombre_exacto}'}})-[r]-(m)
        WITH m.nombre as conectado_con, labels(m) as tipo, count(r) as fuerza
        RETURN conectado_con, tipo, fuerza
        ORDER BY fuerza DESC
        LIMIT 20
        """

        conexiones = connector.execute_cypher(
            cypher_conexiones,
            graph_name=graph_name,
            column_definitions=["conectado_con agtype", "tipo agtype", "fuerza agtype"]
        )
        imprimir_resultados(conexiones, f"CONEXIONES DE '{nombre_exacto}'")


def query_camino_entre_entidades(connector: AGEConnector, graph_name: str, origen: str, destino: str):
    """Consulta: Encontrar camino más corto entre dos entidades"""
    cypher = f"""
    MATCH path = shortestPath((a)-[*..5]-(b))
    WHERE toLower(a.nombre) CONTAINS toLower('{origen}')
      AND toLower(b.nombre) CONTAINS toLower('{destino}')
    RETURN
        a.nombre as origen,
        b.nombre as destino,
        length(path) as distancia
    LIMIT 1
    """

    resultados = connector.execute_cypher(
        cypher,
        graph_name=graph_name,
        column_definitions=["origen agtype", "destino agtype", "distancia agtype"]
    )
    imprimir_resultados(resultados, f"CAMINO MÁS CORTO: '{origen}' → '{destino}'")


def main():
    """Ejecuta consultas al grafo"""
    parser = argparse.ArgumentParser(
        description="Consultas al grafo de documentos jurídicos"
    )
    parser.add_argument(
        "--query",
        type=str,
        choices=["stats", "personas", "organizaciones", "lugares", "buscar", "camino", "all"],
        default="stats",
        help="Tipo de consulta a ejecutar"
    )
    parser.add_argument(
        "--buscar",
        type=str,
        help="Nombre de entidad a buscar (para --query buscar)"
    )
    parser.add_argument(
        "--origen",
        type=str,
        help="Entidad origen (para --query camino)"
    )
    parser.add_argument(
        "--destino",
        type=str,
        help="Entidad destino (para --query camino)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Límite de resultados (default: 10)"
    )
    parser.add_argument(
        "--graph-name",
        type=str,
        default=None,
        help="Nombre del grafo"
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "="*60)
    print("🔍 CONSULTAS AL GRAFO DE DOCUMENTOS JURÍDICOS")
    print("="*60)

    # Crear conector
    config = GraphConfig()
    if args.graph_name:
        config.graph_name = args.graph_name

    connector = AGEConnector(config)

    # Verificar que el grafo existe
    if not connector.graph_exists(config.graph_name):
        print(f"\n❌ Error: El grafo '{config.graph_name}' no existe")
        print("   Ejecuta primero: python3 scripts/graph_setup/04_populate_prototype.py")
        return 1

    print(f"\n✅ Grafo: {config.graph_name}")

    # Ejecutar consultas según el tipo
    try:
        if args.query == "stats" or args.query == "all":
            query_estadisticas(connector, config.graph_name)

        if args.query == "personas" or args.query == "all":
            query_personas_mas_conectadas(connector, config.graph_name, args.limit)

        if args.query == "organizaciones" or args.query == "all":
            query_organizaciones_mas_mencionadas(connector, config.graph_name, args.limit)

        if args.query == "lugares" or args.query == "all":
            query_lugares_mas_mencionados(connector, config.graph_name, args.limit)

        if args.query == "buscar":
            if not args.buscar:
                print("\n❌ Error: Debes especificar --buscar <nombre>")
                return 1
            query_buscar_entidad(connector, config.graph_name, args.buscar)

        if args.query == "camino":
            if not args.origen or not args.destino:
                print("\n❌ Error: Debes especificar --origen y --destino")
                return 1
            query_camino_entre_entidades(connector, config.graph_name, args.origen, args.destino)

        print("\n" + "="*60)
        print("✅ Consultas completadas")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error ejecutando consultas: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())