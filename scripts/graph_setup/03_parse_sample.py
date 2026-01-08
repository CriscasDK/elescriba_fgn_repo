#!/usr/bin/env python3
"""
Script de prueba del parser de entidades

Procesa una muestra de documentos JSON para validar la extracción de entidades.
"""

import sys
import json
from pathlib import Path
from pprint import pprint

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph.parser import AnalisisParser


def test_parser_sample(num_docs: int = 10):
    """
    Prueba el parser con una muestra de documentos.

    Args:
        num_docs: Número de documentos a procesar
    """
    print(f"🧪 Testeando parser con {num_docs} documentos...\n")

    parser = AnalisisParser()
    json_dir = Path("json_files")

    if not json_dir.exists():
        print(f"❌ Directorio {json_dir} no encontrado")
        return

    # Obtener archivos JSON
    json_files = list(json_dir.glob("*.json"))[:num_docs]

    if not json_files:
        print(f"❌ No se encontraron archivos JSON en {json_dir}")
        return

    print(f"📂 Encontrados {len(json_files)} archivos JSON\n")

    resultados = []

    for i, json_file in enumerate(json_files, 1):
        print(f"[{i}/{len(json_files)}] Procesando: {json_file.name}")

        resultado = parser.parse_documento(str(json_file))

        if resultado:
            print(f"  ✅ Extraído:")
            print(f"     - {len(resultado['personas'])} personas")
            print(f"     - {len(resultado['organizaciones'])} organizaciones")
            print(f"     - {len(resultado['lugares'])} lugares")
            print(f"     - {len(resultado['relaciones'])} relaciones\n")

            resultados.append(resultado)
        else:
            print(f"  ⚠️  Sin análisis en documento\n")

    # Mostrar estadísticas finales
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS FINALES")
    print("="*60)
    stats = parser.get_stats()
    for key, value in stats.items():
        print(f"{key:.<40} {value}")

    # Mostrar ejemplo detallado del primer documento con datos
    if resultados:
        print("\n" + "="*60)
        print("📄 EJEMPLO DETALLADO - Primer Documento")
        print("="*60)
        ejemplo = resultados[0]

        print(f"\n🆔 Documento: {ejemplo['documento_id']}")

        if ejemplo['personas']:
            print(f"\n👤 PERSONAS ({len(ejemplo['personas'])}):")
            for persona in ejemplo['personas'][:5]:  # Mostrar máximo 5
                print(f"  - {persona['nombre']}")
                if persona.get('clasificacion'):
                    print(f"    Clasificación: {persona['clasificacion']}")
                if persona.get('contexto'):
                    print(f"    Contexto: {persona['contexto'][:80]}...")

        if ejemplo['organizaciones']:
            print(f"\n🏢 ORGANIZACIONES ({len(ejemplo['organizaciones'])}):")
            for org in ejemplo['organizaciones'][:5]:
                print(f"  - {org['nombre']}")
                if org.get('tipo'):
                    print(f"    Tipo: {org['tipo']}")

        if ejemplo['lugares']:
            print(f"\n📍 LUGARES ({len(ejemplo['lugares'])}):")
            for lugar in ejemplo['lugares'][:5]:
                print(f"  - {lugar['nombre']} ({lugar.get('tipo', 'sin tipo')})")

        if ejemplo['relaciones']:
            print(f"\n🔗 RELACIONES ({len(ejemplo['relaciones'])}):")
            for rel in ejemplo['relaciones'][:5]:
                print(f"  - {rel['origen']} --[{rel['tipo']}]--> {rel['destino']}")

    # Guardar resultados para inspección
    output_file = Path("tests/graph/parser_sample_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "stats": stats,
            "resultados": resultados
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Resultados guardados en: {output_file}")
    print("\n✅ Test completado!")


if __name__ == "__main__":
    import argparse

    parser_args = argparse.ArgumentParser(
        description="Test del parser de entidades"
    )
    parser_args.add_argument(
        "--docs",
        type=int,
        default=10,
        help="Número de documentos a procesar (default: 10)"
    )

    args = parser_args.parse_args()
    test_parser_sample(args.docs)