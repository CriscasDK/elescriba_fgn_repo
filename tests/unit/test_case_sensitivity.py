#!/usr/bin/env python3
"""
Test de sensibilidad a mayúsculas/minúsculas en búsqueda de personas
"""

import sys
sys.path.append('/home/lab4/scripts/documentos_judiciales')

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("consultas", "/home/lab4/scripts/documentos_judiciales/core/consultas.py")
    consultas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consultas)

    print("🔤 TEST SENSIBILIDAD A MAYÚSCULAS/MINÚSCULAS")
    print("=" * 50)

    # Test diferentes variaciones del mismo nombre
    nombres_variaciones = [
        "Oswaldo Olivo",           # Original con mayúsculas
        "oswaldo olivo",           # Todo minúsculas
        "OSWALDO OLIVO",           # Todo mayúsculas
        "Oswaldo olivo",           # Solo primera mayúscula
        "oswaldo Olivo"            # Mixto irregular
    ]

    for nombre in nombres_variaciones:
        print(f"\n📝 Probando: '{nombre}'")
        try:
            resultado = consultas.ejecutar_consulta_persona(nombre)
            print(f"   ✅ Menciones: {resultado.get('total_menciones', 0)}")
            print(f"   ✅ Documentos: {len(resultado.get('documentos', []))}")

            if resultado.get('error'):
                print(f"   ❌ Error: {resultado['error']}")

        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")

except Exception as e:
    print(f"❌ Error importando módulos: {str(e)}")
    import traceback
    traceback.print_exc()