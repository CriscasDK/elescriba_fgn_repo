#!/usr/bin/env python3
"""
Test específico para diagnosticar consulta de personas: Oswaldo Olivo y Rosa Edith Sierra
"""

import sys
sys.path.append('/home/lab4/scripts/documentos_judiciales')

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("consultas", "/home/lab4/scripts/documentos_judiciales/core/consultas.py")
    consultas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consultas)

    print("🔍 DIAGNÓSTICO: Consulta de personas específicas")
    print("=" * 60)

    consulta = "dime quién es Oswaldo Olivo y su relación con Rosa Edith Sierra"

    # Test 1: Clasificador
    print("\n1️⃣ CLASIFICADOR:")
    tipo = consultas.clasificar_consulta(consulta)
    print(f"   Tipo: {tipo}")

    # Test 2: División si es híbrida
    if tipo == 'hibrida':
        print("\n2️⃣ DIVISIÓN HÍBRIDA:")
        parte_bd, parte_rag = consultas.dividir_consulta_hibrida(consulta)
        print(f"   BD: '{parte_bd}'")
        print(f"   RAG: '{parte_rag}'")

        # Test 3: Ejecutar parte BD directamente
        print("\n3️⃣ EJECUTAR PARTE BD DIRECTAMENTE:")
        try:
            if "menciones de" in parte_bd:
                # Extraer nombres de la parte BD
                nombres = parte_bd.replace("menciones de", "").strip()
                print(f"   Extrayendo nombres: '{nombres}'")

                # Test función directa de persona
                resultado_bd = consultas.ejecutar_consulta_persona(nombres)
                print(f"   Keys resultado: {list(resultado_bd.keys())}")
                print(f"   Menciones: {resultado_bd.get('total_menciones', 0)}")
                print(f"   Documentos: {len(resultado_bd.get('documentos', []))}")

                if resultado_bd.get('documentos'):
                    print(f"   Primeros 3 documentos:")
                    for i, doc in enumerate(resultado_bd['documentos'][:3]):
                        print(f"     {i+1}. {doc.get('archivo', 'N/A')}")
                        print(f"        NUC: {doc.get('nuc', 'N/A')}")

        except Exception as e:
            print(f"❌ Error ejecutando BD: {str(e)}")
            import traceback
            traceback.print_exc()

    # Test 4: Ejecutar consulta completa
    print("\n4️⃣ EJECUTAR CONSULTA COMPLETA:")
    try:
        if tipo == 'hibrida':
            resultado = consultas.ejecutar_consulta_hibrida(consulta)
        elif tipo == 'bd':
            resultado = consultas.ejecutar_consulta(consulta)
        else:
            resultado = consultas.ejecutar_consulta(consulta)

        print(f"   Keys resultado: {list(resultado.keys())}")

        # Analizar BD
        bd_info = resultado.get('bd', {})
        if bd_info:
            print(f"   BD - Menciones: {bd_info.get('total_menciones', 0)}")
            print(f"   BD - Documentos: {len(bd_info.get('documentos', []))}")
            print(f"   BD - Keys: {list(bd_info.keys())}")

        # Analizar RAG
        rag_info = resultado.get('rag', {})
        if rag_info:
            print(f"   RAG - Respuesta: {'Sí' if rag_info.get('respuesta') else 'No'}")
            print(f"   RAG - Keys: {list(rag_info.keys())}")

        # Buscar fuentes específicamente
        if 'fuentes' in resultado:
            print(f"   Fuentes directas: {len(resultado['fuentes'])}")
        elif bd_info and 'fuentes' in bd_info:
            print(f"   Fuentes en BD: {len(bd_info['fuentes'])}")
        elif bd_info and 'documentos' in bd_info:
            print(f"   Documentos como fuentes: {len(bd_info['documentos'])}")
        else:
            print("   ❌ NO SE ENCONTRARON FUENTES")

    except Exception as e:
        print(f"❌ Error ejecutando consulta completa: {str(e)}")
        import traceback
        traceback.print_exc()

    # Test 5: Verificar función específica de persona individual
    print("\n5️⃣ TEST FUNCIONES INDIVIDUALES:")
    for nombre in ["Oswaldo Olivo", "Rosa Edith Sierra"]:
        try:
            resultado = consultas.ejecutar_consulta_persona(nombre)
            print(f"   {nombre}: {resultado.get('total_menciones', 0)} menciones, {len(resultado.get('documentos', []))} docs")
        except Exception as e:
            print(f"   {nombre}: ❌ Error - {str(e)}")

except Exception as e:
    print(f"❌ Error importando módulos: {str(e)}")
    import traceback
    traceback.print_exc()