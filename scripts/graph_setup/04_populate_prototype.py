#!/usr/bin/env python3
"""
Script de poblado del grafo - Prototipo

Puebla el grafo con un subset de documentos para validar la arquitectura.
Permite especificar límite de documentos a procesar.
"""

import sys
import argparse
from pathlib import Path

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph.graph_builder import GraphBuilder
from core.graph.config import GraphConfig


def main():
    """
    Ejecuta el poblado del grafo con subset de documentos.
    """
    parser = argparse.ArgumentParser(
        description="Poblar grafo de documentos jurídicos (prototipo)"
    )
    parser.add_argument(
        "--docs",
        type=int,
        default=100,
        help="Número de documentos a procesar (default: 100)"
    )
    parser.add_argument(
        "--recrear",
        action="store_true",
        help="Eliminar y recrear el grafo desde cero"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="No pedir confirmación (útil para scripts)"
    )
    parser.add_argument(
        "--json-dir",
        type=str,
        default="json_files",
        help="Directorio con archivos JSON (default: json_files)"
    )
    parser.add_argument(
        "--graph-name",
        type=str,
        default=None,
        help="Nombre del grafo (default: documentos_juridicos_graph)"
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "="*60)
    print("🚀 POBLADO DE GRAFO - PROTOTIPO")
    print("="*60)
    print(f"\n📋 Configuración:")
    print(f"   Documentos a procesar: {args.docs}")
    print(f"   Directorio JSON: {args.json_dir}")
    print(f"   Recrear grafo: {'Sí' if args.recrear else 'No'}")
    if args.graph_name:
        print(f"   Nombre del grafo: {args.graph_name}")
    print()

    # Confirmación si es recrear
    if args.recrear and not args.yes:
        respuesta = input("⚠️  ¿Estás seguro de eliminar el grafo existente? (s/n): ")
        if respuesta.lower() != 's':
            print("❌ Operación cancelada")
            return 1

    # Crear builder
    config = GraphConfig()
    if args.graph_name:
        config.graph_name = args.graph_name

    builder = GraphBuilder(config)

    # Verificar directorio
    json_dir = Path(args.json_dir)
    if not json_dir.exists():
        print(f"❌ Error: Directorio no existe: {json_dir}")
        return 1

    # Verificar que hay JSONs
    json_count = len(list(json_dir.glob("*.json")))
    if json_count == 0:
        print(f"❌ Error: No hay archivos JSON en {json_dir}")
        return 1

    print(f"✅ Encontrados {json_count} archivos JSON en {json_dir}")

    if args.docs > json_count:
        print(f"⚠️  Límite ({args.docs}) mayor que archivos disponibles ({json_count})")
        print(f"   Se procesarán todos los {json_count} documentos")

    # Ejecutar construcción
    try:
        resultados = builder.construir_desde_directorio(
            json_dir=json_dir,
            limit=args.docs,
            recrear_grafo=args.recrear
        )

        # Éxito
        print("✅ Poblado completado exitosamente")

        # Sugerencias
        print("\n💡 Próximos pasos:")
        print("   1. Explorar el grafo:")
        print("      python3 scripts/graph_setup/05_query_graph.py")
        print()
        print("   2. Ver estadísticas:")
        print("      docker exec -it docs_postgres psql -U docs_user -d documentos_juridicos_gpt4")
        print("      LOAD 'age';")
        print("      SET search_path = ag_catalog, \"$user\", public;")
        print(f"      SELECT * FROM cypher('{config.graph_name}', $$ MATCH (n) RETURN count(n) $$) as (count agtype);")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Error durante el poblado: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())