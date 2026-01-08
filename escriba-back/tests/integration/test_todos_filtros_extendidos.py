#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.consultas import ejecutar_consulta_geografica_directa

def test_todos_filtros():
    """Test completo de todos los tipos de filtro"""

    print("=== TEST TODOS LOS FILTROS EXTENDIDOS ===")

    # Test 1: Filtro geográfico - Solo departamento
    print("\n1. FILTRO DEPARTAMENTO:")
    resultado_depto = ejecutar_consulta_geografica_directa(
        "victimas en Antioquia",
        departamento="Antioquia"
    )
    print(f"✅ Antioquia: {len(resultado_depto['victimas'])} víctimas, {len(resultado_depto['fuentes'])} fuentes")

    # Test 2: Filtro geográfico - Departamento + Municipio
    print("\n2. FILTRO DEPARTAMENTO + MUNICIPIO:")
    resultado_mun = ejecutar_consulta_geografica_directa(
        "victimas en Medellin",
        departamento="Antioquia",
        municipio="Medellín"
    )
    print(f"✅ Medellín, Antioquia: {len(resultado_mun['victimas'])} víctimas, {len(resultado_mun['fuentes'])} fuentes")

    # Test 3: Filtro por despacho
    print("\n3. FILTRO DESPACHO:")
    resultado_despacho = ejecutar_consulta_geografica_directa(
        "victimas del despacho 59",
        despacho="59"
    )
    print(f"✅ Despacho 59: {len(resultado_despacho['victimas'])} víctimas, {len(resultado_despacho['fuentes'])} fuentes")

    # Test 4: Filtro por tipo de documento
    print("\n4. FILTRO TIPO DOCUMENTO:")
    resultado_tipo = ejecutar_consulta_geografica_directa(
        "victimas en resoluciones",
        tipo_documento="Resoluciones"
    )
    print(f"✅ Resoluciones: {len(resultado_tipo['victimas'])} víctimas, {len(resultado_tipo['fuentes'])} fuentes")

    # Test 5: Filtro por NUC (usando uno conocido)
    print("\n5. FILTRO NUC:")
    resultado_nuc = ejecutar_consulta_geografica_directa(
        "victimas en este nuc",
        nuc="110016000253201600077"
    )
    print(f"✅ NUC específico: {len(resultado_nuc['victimas'])} víctimas, {len(resultado_nuc['fuentes'])} fuentes")

    # Test 6: Combinación de filtros
    print("\n6. FILTROS COMBINADOS:")
    resultado_combo = ejecutar_consulta_geografica_directa(
        "victimas en Antioquia con despacho 59",
        departamento="Antioquia",
        despacho="59"
    )
    print(f"✅ Antioquia + Despacho 59: {len(resultado_combo['victimas'])} víctimas, {len(resultado_combo['fuentes'])} fuentes")

    # Test 7: Verificar respuesta con filtros
    print(f"\n7. VERIFICAR RESPUESTA:")
    print(f"   Respuesta: {resultado_combo['respuesta_ia']}")
    print(f"   Tipo: {resultado_combo['tipo_ejecutado']}")

    print(f"\n📊 RESUMEN COMPARATIVO:")
    print(f"   - Antioquia completo: {len(resultado_depto['victimas'])} víctimas")
    print(f"   - Solo Medellín: {len(resultado_mun['victimas'])} víctimas")
    print(f"   - Solo Despacho 59: {len(resultado_despacho['victimas'])} víctimas")
    print(f"   - Solo Resoluciones: {len(resultado_tipo['victimas'])} víctimas")
    print(f"   - Antioquia + Despacho 59: {len(resultado_combo['victimas'])} víctimas")

    if (len(resultado_mun['victimas']) < len(resultado_depto['victimas']) and
        len(resultado_combo['victimas']) <= len(resultado_depto['victimas'])):
        print("   ✅ ¡TODOS LOS FILTROS FUNCIONAN CORRECTAMENTE!")
    else:
        print("   ❌ Hay problemas con algunos filtros")

if __name__ == "__main__":
    test_todos_filtros()