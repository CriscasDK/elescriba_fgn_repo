#!/usr/bin/env python3
"""
Test completo de consulta híbrida corregida para Antioquia
"""

import sys
sys.path.append('/home/lab4/scripts/documentos_judiciales')

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("consultas", "/home/lab4/scripts/documentos_judiciales/core/consultas.py")
    consultas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consultas)

    print("🚀 TEST COMPLETO: CONSULTA HÍBRIDA CORREGIDA")
    print("=" * 60)

    consulta = "dame la lista de victimas en Antioquia y los patrones criminales que observes"

    # Test 1: Clasificador
    print("\n1️⃣ CLASIFICADOR:")
    tipo = consultas.clasificar_consulta(consulta)
    print(f"   Tipo: {tipo}")

    # Test 2: División
    print("\n2️⃣ DIVISIÓN:")
    parte_bd, parte_rag = consultas.dividir_consulta_hibrida(consulta)
    print(f"   BD: '{parte_bd}'")
    print(f"   RAG: '{parte_rag}'")

    # Test 3: Ejecutar consulta híbrida completa
    print("\n3️⃣ EJECUCIÓN HÍBRIDA COMPLETA:")
    try:
        resultado = consultas.ejecutar_consulta_hibrida(consulta)
        print(f"   Keys resultado: {list(resultado.keys())}")

        # Resultados BD
        bd_info = resultado.get('bd', {})
        if bd_info:
            print(f"   BD - Víctimas encontradas: {len(bd_info.get('victimas', []))}")
            if bd_info.get('victimas'):
                print(f"   BD - Primeras 3 víctimas:")
                for i, v in enumerate(bd_info['victimas'][:3]):
                    print(f"     {i+1}. {v.get('nombre', 'N/A')} - {v.get('menciones', 0)} menciones")

        # Resultados RAG
        rag_info = resultado.get('rag', {})
        if rag_info:
            print(f"   RAG - Respuesta disponible: {'Sí' if rag_info.get('respuesta') else 'No'}")
            if rag_info.get('respuesta'):
                print(f"   RAG - Primeras 100 chars: {rag_info['respuesta'][:100]}...")

        # Errores
        if resultado.get('error'):
            print(f"   ❌ Error: {resultado['error']}")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Error importando módulos: {str(e)}")
    import traceback
    traceback.print_exc()