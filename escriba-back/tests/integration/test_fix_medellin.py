#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import ejecutar_consulta_geografica_directa

def test_fix_medellin():
    """Test que el filtro de Medellín ya funciona correctamente"""

    print("=== TEST FIX MEDELLÍN VS ANTIOQUIA ===")

    # Test 1: Solo Antioquia
    resultado_antioquia = ejecutar_consulta_geografica_directa(
        "victimas en Antioquia",
        departamento="Antioquia"
    )

    print(f"✅ Antioquia: {len(resultado_antioquia['victimas'])} víctimas")
    if resultado_antioquia['victimas']:
        print(f"   Top: {resultado_antioquia['victimas'][0]['nombre']} ({resultado_antioquia['victimas'][0]['menciones']})")

    # Test 2: Medellín, Antioquia
    resultado_medellin = ejecutar_consulta_geografica_directa(
        "victimas en Medellin",
        departamento="Antioquia",
        municipio="Medellín"
    )

    print(f"✅ Medellín, Antioquia: {len(resultado_medellin['victimas'])} víctimas")
    if resultado_medellin['victimas']:
        print(f"   Top: {resultado_medellin['victimas'][0]['nombre']} ({resultado_medellin['victimas'][0]['menciones']})")

    # Test 3: Verificar diferencia
    print(f"\n📊 COMPARACIÓN:")
    print(f"   Antioquia total: {len(resultado_antioquia['victimas'])}")
    print(f"   Medellín solamente: {len(resultado_medellin['victimas'])}")

    if len(resultado_medellin['victimas']) < len(resultado_antioquia['victimas']):
        print("   ✅ ¡ARREGLADO! Medellín muestra menos víctimas que Antioquia completo")
    else:
        print("   ❌ Aún hay problema: Medellín muestra el mismo número")

    # Test 4: Solo municipio sin departamento
    resultado_solo_medellin = ejecutar_consulta_geografica_directa(
        "victimas en Medellin",
        municipio="Medellín"
    )

    print(f"✅ Solo municipio Medellín: {len(resultado_solo_medellin['victimas'])} víctimas")

if __name__ == "__main__":
    test_fix_medellin()