#!/usr/bin/env python3
"""
Test del flujo completo de consulta híbrida
"""

import sys
sys.path.append('/home/lab4/scripts/documentos_judiciales')

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("consultas", "/home/lab4/scripts/documentos_judiciales/core/consultas.py")
    consultas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consultas)

    print("🎯 TEST FLUJO COMPLETO: ¿Quién es Oswaldo Olivo?")
    print("=" * 80)

    consulta = "¿Quién es Oswaldo Olivo?"

    # 1. Test clasificador
    print("\n1️⃣ TEST CLASIFICADOR")
    tipo_detectado = consultas.clasificar_consulta(consulta)
    print(f"Consulta: '{consulta}'")
    print(f"Tipo detectado: {tipo_detectado}")

    # 2. Test división
    print("\n2️⃣ TEST DIVISIÓN HÍBRIDA")
    parte_bd, parte_rag = consultas.dividir_consulta_hibrida(consulta)
    print(f"Parte BD: '{parte_bd}'")
    print(f"Parte RAG: '{parte_rag}'")

    # 3. Test consulta híbrida completa
    print("\n3️⃣ TEST CONSULTA HÍBRIDA COMPLETA")
    try:
        resultado = consultas.ejecutar_consulta_hibrida(consulta)

        print(f"Resultado keys: {list(resultado.keys())}")

        if 'error' in resultado:
            print(f"❌ Error: {resultado['error']}")
        else:
            print(f"✅ Éxito!")

            # BD
            bd_info = resultado.get('bd', {})
            print(f"\n📊 BD Info:")
            print(f"  Keys: {list(bd_info.keys())}")
            if 'respuesta_ia' in bd_info:
                print(f"  Respuesta BD: {bd_info['respuesta_ia'][:200]}...")
            if 'victimas' in bd_info:
                print(f"  Víctimas: {len(bd_info['victimas'])}")

            # RAG
            rag_info = resultado.get('rag', {})
            print(f"\n🧠 RAG Info:")
            print(f"  Keys: {list(rag_info.keys())}")
            if 'respuesta' in rag_info:
                print(f"  Respuesta RAG: {rag_info['respuesta'][:200]}...")

    except Exception as e:
        print(f"❌ Error en consulta híbrida: {str(e)}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f"❌ Error general: {str(e)}")
    import traceback
    traceback.print_exc()