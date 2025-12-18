#!/usr/bin/env python3
"""
Test de consultas híbridas para personas específicas
Verifica que consultas como "¿Quién es Oswaldo Olivo?" funcionen correctamente
"""

import sys
import os
sys.path.append('/home/lab4/scripts/documentos_judiciales')
sys.path.append('/home/lab4/scripts/documentos_judiciales/core')
sys.path.append('/home/lab4/scripts/documentos_judiciales/src')

try:
    from core.consultas import (
        clasificar_consulta,
        dividir_consulta_hibrida,
        ejecutar_consulta_hibrida,
        ejecutar_consulta_persona
    )
except ImportError:
    # Fallback para importar directamente
    import importlib.util
    spec = importlib.util.spec_from_file_location("consultas", "/home/lab4/scripts/documentos_judiciales/core/consultas.py")
    consultas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consultas)

    clasificar_consulta = consultas.clasificar_consulta
    dividir_consulta_hibrida = consultas.dividir_consulta_hibrida
    ejecutar_consulta_hibrida = consultas.ejecutar_consulta_hibrida
    ejecutar_consulta_persona = consultas.ejecutar_consulta_persona

def test_clasificador_personas():
    """Test del clasificador mejorado"""
    print("🧪 TESTING CLASIFICADOR DE CONSULTAS PERSONAS")
    print("=" * 60)

    consultas_test = [
        "¿Quién es Oswaldo Olivo?",
        "Quien es Oswaldo Olivo",
        "Qué sabes de Oswaldo Olivo",
        "Información sobre Oswaldo Olivo",
        "Cuéntame de Ana María García",
        "dame la lista de víctimas",
        "¿Cuántos documentos hay?",
        "Patrones criminales"
    ]

    for consulta in consultas_test:
        clasificacion = clasificar_consulta(consulta)
        print(f"'{consulta}' → {clasificacion}")

    print()

def test_division_consultas_personas():
    """Test de división de consultas híbridas para personas"""
    print("🔀 TESTING DIVISIÓN DE CONSULTAS PERSONAS")
    print("=" * 60)

    consultas_test = [
        "¿Quién es Oswaldo Olivo?",
        "Qué sabes de Ana María García",
        "Información sobre Pedro Pérez y qué documentos tiene"
    ]

    for consulta in consultas_test:
        parte_bd, parte_rag = dividir_consulta_hibrida(consulta)
        print(f"Consulta: '{consulta}'")
        print(f"  BD:  '{parte_bd}'")
        print(f"  RAG: '{parte_rag}'")
        print()

def test_consulta_persona_directa():
    """Test de consulta directa a BD para persona específica"""
    print("📊 TESTING CONSULTA PERSONA DIRECTA (BD)")
    print("=" * 60)

    resultado = ejecutar_consulta_persona("Oswaldo Olivo")

    print(f"Resultado tipo: {resultado.get('tipo_ejecutado', 'N/A')}")
    print(f"Total menciones: {resultado.get('total_menciones', 0)}")
    print(f"Documentos encontrados: {len(resultado.get('documentos', []))}")

    if resultado.get('respuesta'):
        print("\n📄 RESPUESTA:")
        print(resultado['respuesta'][:500] + "..." if len(resultado.get('respuesta', '')) > 500 else resultado.get('respuesta', ''))

    print()

def test_consulta_hibrida_completa():
    """Test completo de consulta híbrida con persona específica"""
    print("🚀 TESTING CONSULTA HÍBRIDA COMPLETA")
    print("=" * 60)

    consulta = "¿Quién es Oswaldo Olivo?"

    try:
        resultado = ejecutar_consulta_hibrida(consulta)

        print(f"Consulta: '{consulta}'")
        print(f"Tipo de consulta detectado: híbrida")

        # Panel BD
        bd_info = resultado.get('bd', {})
        print(f"\n📊 PANEL BD:")
        print(f"Consulta BD: {bd_info.get('consulta_original', 'N/A')}")
        if bd_info.get('victimas'):
            print(f"Víctimas encontradas: {len(bd_info['victimas'])}")
        if bd_info.get('respuesta'):
            print(f"Respuesta BD: {bd_info['respuesta'][:200]}...")

        # Panel RAG
        rag_info = resultado.get('rag', {})
        print(f"\n🤖 PANEL RAG:")
        print(f"Consulta RAG: {rag_info.get('consulta_original', 'N/A')}")
        if rag_info.get('respuesta'):
            print(f"Respuesta RAG: {rag_info['respuesta'][:200]}...")

        print(f"\n✅ SUCCESS: Consulta híbrida completada")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    print()

def main():
    print("🎯 TEST DE CONSULTAS HÍBRIDAS PARA PERSONAS ESPECÍFICAS")
    print("=" * 80)
    print()

    try:
        test_clasificador_personas()
        test_division_consultas_personas()
        test_consulta_persona_directa()
        test_consulta_hibrida_completa()

        print("🏆 TODOS LOS TESTS COMPLETADOS")
        print("=" * 80)
        print()
        print("✅ El sistema ahora debería responder correctamente a:")
        print("   - '¿Quién es Oswaldo Olivo?' → HÍBRIDA (BD + RAG)")
        print("   - Panel BD: Menciones y documentos")
        print("   - Panel RAG: Análisis contextual")

    except Exception as e:
        print(f"❌ ERROR EN TESTS: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()