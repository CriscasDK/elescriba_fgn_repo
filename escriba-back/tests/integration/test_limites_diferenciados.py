#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import ejecutar_consulta_geografica_directa

def test_limites_diferenciados():
    """Test los nuevos límites diferenciados"""

    print("=== TEST LÍMITES DIFERENCIADOS ===")

    resultado = ejecutar_consulta_geografica_directa(
        "victimas y documentos en Antioquia",
        departamento="Antioquia"
    )

    print(f"✅ Víctimas encontradas: {len(resultado['victimas'])}")
    print(f"✅ Fuentes encontradas: {len(resultado['fuentes'])}")

    print(f"\nPrimeras 5 víctimas:")
    for i, v in enumerate(resultado['victimas'][:5]):
        print(f"  {i+1}. {v['nombre']} ({v['menciones']} menciones)")

    print(f"\nPrimeras 5 fuentes:")
    for i, f in enumerate(resultado['fuentes'][:5]):
        print(f"  {i+1}. {f['archivo'][:50]}... | NUC: {f['nuc']}")

    print(f"\n📊 TOTALES REALES EN BD:")
    print(f"   - Víctimas: 997 (mostrando {len(resultado['victimas'])})")
    print(f"   - Documentos: 2,481 (mostrando {len(resultado['fuentes'])})")

if __name__ == "__main__":
    test_limites_diferenciados()