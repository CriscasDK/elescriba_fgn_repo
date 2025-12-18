#!/usr/bin/env python3
"""
Test detallado del flujo híbrido paso a paso
"""

import sys
sys.path.append('/home/lab4/scripts/documentos_judiciales')

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("consultas", "/home/lab4/scripts/documentos_judiciales/core/consultas.py")
    consultas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consultas)

    print("🔍 ANÁLISIS DETALLADO DEL FLUJO HÍBRIDO")
    print("=" * 60)

    consulta = "dime quién es Oswaldo Olivo y su relación con Rosa Edith Sierra"

    # 1. Ejecutar la función individual de persona directamente
    print("\n1️⃣ FUNCIÓN INDIVIDUAL DIRECTA:")
    resultado_individual = consultas.ejecutar_consulta_persona("oswaldo olivo")
    print(f"   Keys: {list(resultado_individual.keys())}")
    print(f"   Menciones: {resultado_individual.get('total_menciones', 0)}")
    print(f"   Documentos: {len(resultado_individual.get('documentos', []))}")
    print(f"   Fuentes: {len(resultado_individual.get('fuentes', []))}")
    print(f"   Víctimas: {len(resultado_individual.get('victimas', []))}")

    # 2. Ejecutar consulta híbrida y capturar resultado BD completo
    print("\n2️⃣ CONSULTA HÍBRIDA - ANÁLISIS BD:")
    resultado_hibrido = consultas.ejecutar_consulta_hibrida(consulta)
    bd_info = resultado_hibrido.get('bd', {})

    print(f"   BD Keys completas: {list(bd_info.keys())}")

    # Analizar cada key detalladamente
    for key, valor in bd_info.items():
        if isinstance(valor, list):
            print(f"   BD['{key}']: {len(valor)} elementos")
            if valor and len(valor) > 0:
                print(f"      Primer elemento: {type(valor[0])} - {str(valor[0])[:100]}...")
        elif isinstance(valor, dict):
            print(f"   BD['{key}']: {len(valor)} keys - {list(valor.keys())}")
        else:
            print(f"   BD['{key}']: {type(valor)} - {str(valor)[:100]}...")

    # 3. Comparar estructura de datos
    print("\n3️⃣ COMPARACIÓN DE ESTRUCTURAS:")
    print("   INDIVIDUAL:")
    for key in ['total_menciones', 'documentos', 'fuentes', 'victimas']:
        if key in resultado_individual:
            valor = resultado_individual[key]
            if isinstance(valor, list):
                print(f"      {key}: {len(valor)} elementos")
            else:
                print(f"      {key}: {valor}")

    print("   HÍBRIDA BD:")
    for key in ['total_menciones', 'documentos', 'fuentes', 'victimas']:
        if key in bd_info:
            valor = bd_info[key]
            if isinstance(valor, list):
                print(f"      {key}: {len(valor)} elementos")
            else:
                print(f"      {key}: {valor}")
        else:
            print(f"      {key}: ❌ NO EXISTE")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()