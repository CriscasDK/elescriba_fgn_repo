#!/usr/bin/env python3
"""
Test para verificar que la búsqueda "Quien es Ana Matilde Guzman" funciona correctamente
"""
import sys
from pathlib import Path

proyecto_root = Path(__file__).parent
sys.path.insert(0, str(proyecto_root))

from core.consultas import ejecutar_consulta

print("=" * 80)
print("🧪 TEST: Búsqueda 'Quien es Ana Matilde Guzman'")
print("=" * 80)
print()

consulta = "Quien es Ana Matilde Guzman"
print(f"📝 Consulta: {consulta}")
print()

print("🔍 Ejecutando búsqueda...")
try:
    resultado = ejecutar_consulta(consulta)

    print("\n" + "=" * 80)
    print("📊 RESULTADOS:")
    print("=" * 80)

    if 'victimas' in resultado:
        victimas = resultado['victimas']
        print(f"\n✅ Víctimas encontradas: {len(victimas)}")

        if len(victimas) > 0:
            print("\n📋 Top 10 víctimas:")
            for i, victima in enumerate(victimas[:10], 1):
                nombre = victima.get('nombre', 'N/A')
                menciones = victima.get('menciones', 0)
                print(f"   {i}. {nombre:<50} | {menciones:>3} menciones")

            # Verificar si Ana Matilde está en los resultados
            ana_matilde_encontrada = False
            for victima in victimas:
                nombre_lower = victima.get('nombre', '').lower()
                if 'ana matilde' in nombre_lower and 'guzm' in nombre_lower:
                    ana_matilde_encontrada = True
                    print(f"\n✅ Ana Matilde encontrada: {victima['nombre']} con {victima['menciones']} menciones")
                    break

            if not ana_matilde_encontrada:
                print("\n⚠️  Ana Matilde NO está en los primeros resultados")
        else:
            print("\n❌ No se encontraron víctimas (lista vacía)")
    else:
        print("\n❌ El resultado no contiene 'victimas'")

    if 'fuentes' in resultado:
        fuentes = resultado['fuentes']
        print(f"\n✅ Fuentes encontradas: {len(fuentes)}")
        if len(fuentes) > 0:
            print("\n📄 Primeras 5 fuentes:")
            for i, fuente in enumerate(fuentes[:5], 1):
                archivo = fuente.get('archivo', 'N/A')
                nuc = fuente.get('nuc', 'N/A')
                print(f"   {i}. {archivo}")
                print(f"      NUC: {nuc}")
    else:
        print("\n⚠️  El resultado no contiene 'fuentes'")

    print("\n" + "=" * 80)
    print("🎯 CONCLUSIÓN:")
    print("=" * 80)

    victimas_count = len(resultado.get('victimas', []))
    fuentes_count = len(resultado.get('fuentes', []))

    if victimas_count > 0 and fuentes_count > 0:
        print("✅ TEST EXITOSO: La búsqueda retornó resultados")
        print(f"   Víctimas: {victimas_count}")
        print(f"   Fuentes: {fuentes_count}")
    else:
        print("❌ TEST FALLIDO: La búsqueda retornó 0 resultados")
        print(f"   Víctimas: {victimas_count}")
        print(f"   Fuentes: {fuentes_count}")

except Exception as e:
    print(f"\n❌ ERROR durante la búsqueda: {str(e)}")
    import traceback
    traceback.print_exc()
