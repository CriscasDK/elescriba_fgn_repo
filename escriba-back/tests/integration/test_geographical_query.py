#!/usr/bin/env python3
"""
Test de la función ejecutar_consulta_geografica_directa para Antioquia
"""

import sys
sys.path.append('/home/lab4/scripts/documentos_judiciales')

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("consultas", "/home/lab4/scripts/documentos_judiciales/core/consultas.py")
    consultas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consultas)

    print("🌍 TEST CONSULTA GEOGRÁFICA DIRECTA - ANTIOQUIA")
    print("=" * 70)

    # Test 1: Función directa con departamento Antioquia sin límite
    print("\n1️⃣ TEST: ejecutar_consulta_geografica_directa('lista de víctimas', departamento='Antioquia')")
    try:
        resultado = consultas.ejecutar_consulta_geografica_directa(
            "lista de víctimas",
            departamento="Antioquia",
            limit_victimas=None  # Sin límite para ver el total
        )

        print(f"✅ Resultado: {list(resultado.keys())}")
        print(f"   Total víctimas: {len(resultado.get('victimas', []))}")
        if resultado.get('victimas'):
            print(f"   Primeras 5 víctimas:")
            for i, victima in enumerate(resultado['victimas'][:5]):
                print(f"     {i+1}. {victima.get('nombre', 'N/A')} - {victima.get('menciones', 0)} menciones")

        print(f"   Total fuentes: {len(resultado.get('fuentes', []))}")

        if resultado.get('error'):
            print(f"❌ Error: {resultado['error']}")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 2: Con límite de 10 para comparar
    print("\n2️⃣ TEST: Con límite de 10 víctimas")
    try:
        resultado = consultas.ejecutar_consulta_geografica_directa(
            "lista de víctimas",
            departamento="Antioquia",
            limit_victimas=10
        )

        print(f"✅ Resultado con límite: {len(resultado.get('victimas', []))} víctimas")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 3: Ver cómo el clasificador categoriza la consulta "dame la lista de victimas en Antioquia"
    print("\n3️⃣ TEST: Clasificador para 'dame la lista de victimas en Antioquia y los patrones criminales'")
    try:
        consulta = "dame la lista de victimas en Antioquia y los patrones criminales que observes"
        tipo = consultas.clasificar_consulta(consulta)
        print(f"   Consulta: '{consulta}'")
        print(f"   Clasificación: {tipo}")

        # Test híbrida completa
        if tipo == 'hibrida':
            parte_bd, parte_rag = consultas.dividir_consulta_hibrida(consulta)
            print(f"   Parte BD: '{parte_bd}'")
            print(f"   Parte RAG: '{parte_rag}'")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Error importando módulos: {str(e)}")
    import traceback
    traceback.print_exc()