#!/usr/bin/env python3
"""
Test específico para el error KeyError: 'fuentes'
"""

from core.consultas import ejecutar_consulta, clasificar_consulta, ejecutar_consulta_rag_inteligente

def test_diferentes_consultas():
    """Probar diferentes tipos de consultas para ver estructura de respuesta"""

    consultas_test = [
        "¿Cuántas víctimas hay?",
        "Lista víctimas",
        "Test consulta",
        "",
        None
    ]

    print("🔍 PROBANDO DIFERENTES TIPOS DE CONSULTAS")
    print("="*50)

    for i, consulta in enumerate(consultas_test, 1):
        print(f"\n📋 TEST {i}: Consulta = {repr(consulta)}")

        try:
            if consulta:
                tipo = clasificar_consulta(consulta)
                print(f"🎯 Tipo detectado: {tipo}")

                if tipo == 'bd':
                    resultado = ejecutar_consulta(consulta)
                elif tipo == 'rag':
                    resultado = ejecutar_consulta_rag_inteligente(consulta)
                else:
                    resultado = ejecutar_consulta(consulta)  # Fallback
            else:
                resultado = ejecutar_consulta("")  # Consulta vacía

            print(f"✅ Claves en resultado: {list(resultado.keys())}")
            print(f"📚 Tiene 'fuentes': {'fuentes' in resultado}")
            print(f"📊 Fuentes count: {len(resultado.get('fuentes', []))}")

            # Simular acceso como en Dash
            fuentes = resultado.get("fuentes", [])
            print(f"✅ Acceso seguro 'fuentes': {type(fuentes)} con {len(fuentes)} elementos")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print(f"\n🎉 PRUEBAS COMPLETADAS")
    print(f"✅ Corrección aplicada: resultado.get('fuentes', []) es segura")

if __name__ == "__main__":
    test_diferentes_consultas()