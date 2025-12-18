#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import ejecutar_consulta_hibrida, clasificar_consulta, ejecutar_consulta_geografica_directa

def test_antioquia_query():
    """Test the Antioquia query to verify BD panel filtering works"""

    consulta_test = "dame la lista de victimas en Antioquia y los patrones criminales que observes"

    print("=== TEST ANTIOQUIA QUERY ===")
    print(f"Consulta: {consulta_test}")
    print()

    # 1. Test query classification
    tipo_detectado = clasificar_consulta(consulta_test)
    print(f"Tipo detectado: {tipo_detectado}")

    # 2. Test new direct geographical query
    print("\n=== TESTING DIRECT GEOGRAPHICAL QUERY ===")
    try:
        resultado_geo = ejecutar_consulta_geografica_directa(
            "dame la lista de victimas en Antioquia",
            departamento="Antioquia"
        )
        print(f"Geo Directo - Víctimas: {len(resultado_geo.get('victimas', []))}")
        if resultado_geo.get('victimas'):
            for v in resultado_geo['victimas'][:5]:
                print(f"  - {v['nombre']}: {v['menciones']}")
    except Exception as e:
        print(f"❌ Error Geo directo: {e}")
        import traceback
        traceback.print_exc()

    # 3. Test direct BD query with departamento filter
    print("\n=== TESTING DIRECT BD QUERY ===")
    from core.consultas import ejecutar_consulta
    try:
        resultado_bd_directo = ejecutar_consulta(
            "dame la lista de victimas en Antioquia",
            departamento="Antioquia"
        )
        print(f"BD Directo - Víctimas: {len(resultado_bd_directo.get('victimas', []))}")
        if resultado_bd_directo.get('victimas'):
            for v in resultado_bd_directo['victimas'][:3]:
                print(f"  - {v['nombre']}: {v['menciones']}")

    except Exception as e:
        print(f"❌ Error BD directo: {e}")
        import traceback
        traceback.print_exc()

    # 3. Execute hybrid query
    print("\n=== TESTING HYBRID QUERY ===")
    try:
        resultados = ejecutar_consulta_hibrida(consulta_test)

        if 'error' not in resultados:
            print(f"División aplicada: {resultados.get('division_aplicada', False)}")
            print(f"Consulta BD: {resultados['bd'].get('consulta_original', 'N/A')}")
            print(f"Consulta RAG: {resultados['rag'].get('consulta_original', 'N/A')}")

            bd_victimas = resultados['bd'].get('victimas', [])
            print(f"✅ Víctimas BD encontradas: {len(bd_victimas)}")

            if bd_victimas:
                print("Primeras 5 víctimas:")
                for i, victima in enumerate(bd_victimas[:5]):
                    print(f"  {i+1}. {victima['nombre']} ({victima['menciones']} menciones)")
            else:
                print("❌ No se encontraron víctimas en BD")

            bd_fuentes = resultados['bd'].get('fuentes', [])
            print(f"✅ Fuentes BD encontradas: {len(bd_fuentes)}")

            rag_respuesta = resultados['rag'].get('respuesta', '')
            print(f"✅ Respuesta RAG: {'Sí' if rag_respuesta else 'No'}")

        else:
            print(f"❌ Error en consulta: {resultados.get('error', 'Error desconocido')}")

    except Exception as e:
        print(f"❌ Excepción durante ejecución: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_antioquia_query()